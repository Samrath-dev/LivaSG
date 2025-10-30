# app/services/rating_engine.py
from __future__ import annotations
from math import radians, sin, cos, sqrt, atan2
from typing import Optional, Any

from ..domain.models import CategoryBreakdown, NeighbourhoodScore, WeightsProfile
from ..repositories.interfaces import (
    IPriceRepo, IAmenityRepo, IScoreRepo, ICommunityRepo, ITransitRepo, ICarparkRepo, IAreaRepo
)

def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))

class RatingEngine:
    """
    Weights = dev-controlled.
    User ranks (via IRankRepo) scale category scores BEFORE weights.
    Accepts either rank=... or ranks=... (alias).
    """
    def __init__(
        self,
        price: IPriceRepo,
        amen: IAmenityRepo,
        scores: IScoreRepo,
        community: Optional[ICommunityRepo] = None,
        transit: Optional[ITransitRepo] = None,
        carparks: Optional[ICarparkRepo] = None,
        areas: Optional[IAreaRepo] = None,
        rank: Optional[Any] = None,     # preferred (IRankRepo)
        ranks: Optional[Any] = None,    # alias for backward/forward compat
        **_: Any,                       # ignore stray kwargs safely
    ):
        self.price = price
        self.amen  = amen
        self.scores = scores
        self.community = community
        self.transit = transit
        self.carparks = carparks
        self.areas = areas
        # coalesce alias
        self.rank = rank if rank is not None else ranks

    def _haversine_km(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        # Correct haversine
        R = 6371.0
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat/2.0)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2.0)**2
        c = 2.0 * atan2(sqrt(a), sqrt(1.0 - a))
        return R * c

    def _compute_transit_score_from_distance(self, dist_km: Optional[float]) -> float:
        if dist_km is None: return 0.35
        if dist_km <= 0.2:  return 1.0
        if dist_km <= 1.0:  return clamp01(1.0 - (dist_km - 0.2) / 0.8)
        return 0.12

    def _carpark_capacity_score(self, area_id: str) -> float:
        if self.carparks:
            try:
                parks = self.carparks.list_near_area(area_id)
            except Exception:
                parks = []
            if parks:
                avg_cap = sum((p.capacity or 0) for p in parks) / max(1, len(parks))
                return clamp01(avg_cap / 450.0)
        # fallback: use facilities_summary carparks (handled later when we have fac)
        return 0.0

    def _rank_multipliers(self) -> dict[str, float]:
        """
        Map rank (1=highest priority … 5=lowest) to a multiplier.
        Mean-normalize to keep overall scale stable so weights remain meaningful.
        """
        neutral = {"Affordability": 1.0, "Accessibility": 1.0, "Amenities": 1.0, "Environment": 1.0, "Community": 1.0}
        rp = None
        if self.rank:
            try:
                rp = self.rank.get_active()
            except Exception:
                rp = None
        if not rp:
            return neutral

        r_aff = int(getattr(rp, "rAff", 3) or 3)
        r_acc = int(getattr(rp, "rAcc", 3) or 3)
        r_amen= int(getattr(rp, "rAmen",3) or 3)
        r_env = int(getattr(rp, "rEnv", 3) or 3)
        r_com = int(getattr(rp, "rCom", 3) or 3)

        # Strong but bounded effect; rank 1 boosts, rank 5 dampens
        LUT = {1: 1.40, 2: 1.18, 3: 1.00, 4: 0.85, 5: 0.65}
        raw = {
            "Affordability": LUT.get(r_aff, 1.0),
            "Accessibility": LUT.get(r_acc, 1.0),
            "Amenities":     LUT.get(r_amen,1.0),
            "Environment":   LUT.get(r_env, 1.0),
            "Community":     LUT.get(r_com, 1.0),
        }
        mean = sum(raw.values()) / 5.0
        return {k: v / mean for k, v in raw.items()} if mean > 0 else neutral

    async def category_breakdown(self, area_id: str) -> CategoryBreakdown:
        # Affordability from price series (sync repo)
        series = self.price.series(area_id, months=1)
        median = series[-1].medianResale if series else 500_000
        # 300k→1.0 … 900k→0.0
        aff = clamp01(1.0 - (median - 300_000) / 600_000)

        # Facilities (async)
        fac = await self.amen.facilities_summary(area_id)
        amen_score = clamp01((fac.schools + fac.sports + fac.hawkers + fac.healthcare + fac.greenSpaces) / 22.0)

        # Accessibility — transit + carparks
        transit_dist = None
        centroid = None
        if self.areas:
            try:
                centroid = self.areas.centroid(area_id) if hasattr(self.areas, "centroid") else None
            except Exception:
                centroid = None

        if centroid is not None and self.transit:
            nodes = self.transit.list_near_area(area_id) or self.transit.all()
            dists = [
                self._haversine_km(centroid.latitude, centroid.longitude, n.latitude, n.longitude)
                for n in nodes if n.latitude is not None and n.longitude is not None
            ]
            transit_dist = min(dists) if dists else None

        transit_score = self._compute_transit_score_from_distance(transit_dist)

        carpark_score = self._carpark_capacity_score(area_id)
        if carpark_score == 0.0 and hasattr(fac, "carparks"):
            carpark_score = clamp01((fac.carparks or 0) / 22.0)

        acc  = clamp01(0.7 * transit_score + 0.3 * carpark_score)
        env  = clamp01(fac.greenSpaces / 11.0)

        # Community: 0 (none), 0.5 (1 CC), 0.75 (2 CCs), 1.0 (>=3 CCs)
        try:
            cc_count = len(self.community.list_near_area(area_id)) if self.community else 0
        except Exception:
            cc_count = 0
        comm = 1.0 if cc_count >= 3 else 0.75 if cc_count == 2 else 0.5 if cc_count == 1 else 0.0

        return CategoryBreakdown(scores={
            "Affordability": round(aff, 3),
            "Accessibility": acc,
            "Amenities":     round(amen_score, 3),
            "Environment":   round(env, 3),
            "Community":     round(comm, 3),
        })

    async def aggregate(self, area_id: str, w: WeightsProfile) -> NeighbourhoodScore:
        base = (await self.category_breakdown(area_id)).scores
        mult = self._rank_multipliers()
        # Apply rank multipliers BEFORE weights
        adj = {k: clamp01(base[k] * mult.get(k, 1.0)) for k in base.keys()}

        total = (
            adj["Affordability"] * w.wAff +
            adj["Accessibility"] * w.wAcc +
            adj["Amenities"]     * w.wAmen +
            adj["Environment"]   * w.wEnv +
            adj["Community"]     * w.wCom
        )
        score = NeighbourhoodScore(areaId=area_id, total=round(total, 3), weightsProfileId=w.id)
        self.scores.save(score)
        return score