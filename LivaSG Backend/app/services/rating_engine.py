from __future__ import annotations

import asyncio
import inspect
from math import radians, sin, cos, sqrt, atan2, exp, log1p
from typing import Optional

from ..domain.models import CategoryBreakdown, NeighbourhoodScore, WeightsProfile
from ..repositories.interfaces import (
    IPriceRepo, IAmenityRepo, IScoreRepo, ICommunityRepo, ITransitRepo, ICarparkRepo, IAreaRepo
)

def clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x

def _await_if_needed(val):
    """If repo method returns a coroutine, run it synchronously (safe in thread worker)."""
    if inspect.isawaitable(val):
   
        return asyncio.run(val)
    return val

def _soft_cap_count(x: float, knee: float) -> float:
    """Diminishing returns curve: linear before 'knee', then log squeeze."""
    if x <= 0:
        return 0.0
    if x <= knee:
        return x / knee
  
    return clamp01(0.5 + 0.5 * (log1p(x - knee) / log1p(10.0)))

def _decay_distance_km(d: Optional[float], half_life_km: float = 0.6) -> float:
    """Convert distance to [0,1] using exponential decay; 0 distance→1.0, halves every half_life_km."""
    if d is None:
        return 0.3  
    if d <= 0:
        return 1.0
    # score = 0.5 ** (d / half_life_km)
    return clamp01(pow(0.5, d / max(0.05, half_life_km)))

def _stable_tiebreaker(area_id: str) -> float:
    """Tiny deterministic epsilon in [0,1e-6) to break exact ties across areas."""
 
    h = 2166136261
    for ch in area_id:
        h ^= ord(ch)
        h = (h * 16777619) & 0xFFFFFFFF
    
    return (h / 0xFFFFFFFF) * 1e-6

class RatingEngine:
    """
    Sophisticated scoring using multi-signal features with deterministic tiebreak.
    Public surface remains compatible with existing services/controllers.
    """
    def __init__(
        self,
        price: IPriceRepo,
        amen: IAmenityRepo,
        scores: IScoreRepo,
        community: ICommunityRepo | None = None,
        transit: ITransitRepo | None = None,
        carparks: ICarparkRepo | None = None,
        areas: IAreaRepo | None = None,
    ):
        self.price = price
        self.amen = amen
        self.scores = scores
        self.community = community
        self.transit = transit
        self.carparks = carparks
        self.areas = areas

    # --- geometry helpers ---
    def _haversine_km(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371.0
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c

    def _area_centroid(self, area_id: str):
        if not self.areas:
            return None
        try:
            poly, centroid = self.areas.getAreaGeometry(area_id)
            return centroid
        except Exception:
            return None

    def _nearest_transit_distance_km(self, area_id: str) -> Optional[float]:
        if not self.transit:
            return None
        centroid = self._area_centroid(area_id)
        if centroid is None or centroid.latitude is None or centroid.longitude is None:
            return None
        nodes = self.transit.list_near_area(area_id) or self.transit.all()
        best = None
        for n in nodes:
            if n.latitude is None or n.longitude is None:
                continue
            d = self._haversine_km(centroid.latitude, centroid.longitude, n.latitude, n.longitude)
            if best is None or d < best:
                best = d
        return best

    # --- category feature computations ---
    def _affordability(self, area_id: str) -> float:
        # Use the last value; scale within a robust band to avoid identical scores
        series = self.price.series(area_id, months=1)
        median = series[-1].medianResale if series else 500_000
        # Robust min/max (allows differentiation): 300k–1.2M
        lo, hi = 300_000, 1_200_000
        score = 1.0 - (median - lo) / (hi - lo)
        return clamp01(score)

    def _amenities(self, area_id: str) -> float:
        # FacilitiesSummary via repo (handles loading/caching internally).
        fac = _await_if_needed(self.amen.facilities_summary(area_id))
        # Use soft caps to avoid linear explosion + ensure fine differentiation
        # knee values tuned to typical SG distributions
        schools = _soft_cap_count(fac.schools, knee=6)
        sports  = _soft_cap_count(fac.sports, knee=3)
        hawkers = _soft_cap_count(fac.hawkers, knee=4)
        health  = _soft_cap_count(fac.healthcare, knee=8)
        parks   = _soft_cap_count(fac.greenSpaces, knee=6)
        # Weighted blend emphasizing universal access (health/schools) slightly more
        raw = 0.25*schools + 0.2*health + 0.2*parks + 0.2*hawkers + 0.15*sports
        return clamp01(raw)

    def _accessibility(self, area_id: str) -> float:
        # Transit proximity
        d_km = self._nearest_transit_distance_km(area_id)
        transit_score = _decay_distance_km(d_km, half_life_km=0.6)

        # Carparks (capacity + presence)
        carpark_score = 0.3  # default
        if self.carparks:
            try:
                parks = self.carparks.list_near_area(area_id)
            except Exception:
                parks = []
            if parks:
                avg_cap = sum((p.capacity or 0) for p in parks) / max(1, len(parks))
                # Normalize: 0→0.0, 500→~1.0 (soft)
                cap_norm = clamp01(avg_cap / 500.0)
                cnt_norm = _soft_cap_count(len(parks), knee=8)
                carpark_score = clamp01(0.7 * cap_norm + 0.3 * cnt_norm)
            else:
                # Fallback to facilities_summary carpark count if available (already computed above)
                try:
                    fac = _await_if_needed(self.amen.facilities_summary(area_id))
                    carpark_score = _soft_cap_count(fac.carparks, knee=8)
                except Exception:
                    pass

        # Blend, skew toward transit
        return clamp01(0.75 * transit_score + 0.25 * carpark_score)

    def _environment(self, area_id: str) -> float:
        # Use parks component from facilities summary; add gentle boost for larger green presence
        fac = _await_if_needed(self.amen.facilities_summary(area_id))
        parks = _soft_cap_count(fac.greenSpaces, knee=6)
        # optionally factor “hawker/health” lightly as proxies for daily-walkability greenspace usage
        walkability_proxy = clamp01(0.5 * _soft_cap_count(fac.hawkers, knee=4) + 0.5 * _soft_cap_count(fac.healthcare, knee=8))
        return clamp01(0.8 * parks + 0.2 * walkability_proxy)

    def _community(self, area_id: str) -> float:
        if not self.community:
            return 0.0
        try:
            exists = self.community.exists(area_id)
        except Exception:
            exists = False
     
        base = 1.0 if exists else 0.2
        return clamp01(base)

    # --- public API ---
    def category_breakdown(self, area_id: str) -> CategoryBreakdown:
        aff = round(self._affordability(area_id), 4)
        amen = round(self._amenities(area_id), 4)
        acc = round(self._accessibility(area_id), 4)
        env = round(self._environment(area_id), 4)
        com = round(self._community(area_id), 4)

        return CategoryBreakdown(scores={
            "Affordability": aff,
            "Accessibility": acc,
            "Amenities": amen,
            "Environment": env,
            "Community": com
        })

    def aggregate(self, area_id: str, w: WeightsProfile) -> NeighbourhoodScore:
        b = self.category_breakdown(area_id).scores
        total = (
            b["Affordability"] * w.wAff +
            b["Accessibility"] * w.wAcc +
            b["Amenities"] * w.wAmen +
            b["Environment"] * w.wEnv +
            b["Community"] * w.wCom
        )

        # Deterministic, invisible tie-breaker to ensure strict ordering across areas.
        total = float(total) + _stable_tiebreaker(area_id)

        score = NeighbourhoodScore(areaId=area_id, total=round(total, 6), weightsProfileId=w.id)
        self.scores.save(score)
        return score