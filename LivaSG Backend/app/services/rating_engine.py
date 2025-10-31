# app/services/rating_engine.py
from __future__ import annotations
from math import radians, sin, cos, sqrt, atan2
from typing import Optional, Any
import os
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
        Rank (1 best … 5 worst) -> multiplier applied to category scores BEFORE weights.
        Stronger spread + tunable strength + gamma curve, with light mean-normalization so totals don’t explode.
        Env knobs:
        RANK_STRENGTH  in [0..2.0]  (default 1.5) — how far from 1.0 the multipliers can pull
        RANK_NORMALIZE in [0..1]    (default 0.15) — how much to pull the average back toward 1.0
        RANK_GAMMA     in [1..3+]   (default 2.0)  — ive made it exponential now to pull even more. Exponential curve
        """
        import os, math
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
        r_amen = int(getattr(rp, "rAmen", 3) or 3)
        r_env = int(getattr(rp, "rEnv", 3) or 3)
        r_com = int(getattr(rp, "rCom", 3) or 3)

        # base spread
        LUT = {1: 1.75, 2: 1.30, 3: 1.00, 4: 0.75, 5: 0.45}
        gamma = float(os.getenv("RANK_GAMMA", "2.0"))
        strength = float(os.getenv("RANK_STRENGTH", "1.2"))
        normalize = float(os.getenv("RANK_NORMALIZE", "0.3"))

        # apply exponential curve for contrast
        def curved(v: float) -> float:
            return math.copysign(abs(v) ** gamma, v) if v != 0 else 0.0

        raw = {
            "Affordability": curved(LUT.get(r_aff, 1.0)),
            "Accessibility": curved(LUT.get(r_acc, 1.0)),
            "Amenities":     curved(LUT.get(r_amen, 1.0)),
            "Environment":   curved(LUT.get(r_env, 1.0)),
            "Community":     curved(LUT.get(r_com, 1.0)),
        }

        # scale by strength
        blended = {k: 1.0 + strength * (v - 1.0) for k, v in raw.items()}

        # normalize toward 1.0 to stabilize totals
        mean = sum(blended.values()) / 5.0
        if mean > 0 and normalize > 0:
            norm = mean ** normalize
            return {k: v / norm for k, v in blended.items()}
        return blended
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

    def _apply_rank_to_weights(self, w: WeightsProfile) -> WeightsProfile:
        mult = self._rank_multipliers()
        # scale weights by rank multipliers
        w2 = WeightsProfile(
            id=w.id,
            wAff=w.wAff * mult.get("Affordability", 1.0),
            wAcc=w.wAcc * mult.get("Accessibility", 1.0),
            wAmen=w.wAmen * mult.get("Amenities", 1.0),
            wEnv=w.wEnv * mult.get("Environment", 1.0),
            wCom=w.wCom * mult.get("Community", 1.0),
        )
        # renormalize to sum=1 (keeps score scale stable)
        s = (w2.wAff + w2.wAcc + w2.wAmen + w2.wEnv + w2.wCom) or 1.0
        return WeightsProfile(
            id=w2.id,
            wAff=w2.wAff / s,
            wAcc=w2.wAcc / s,
            wAmen=w2.wAmen / s,
            wEnv=w2.wEnv / s,
            wCom=w2.wCom / s,
        )
    async def aggregate(self, area_id: str, w: WeightsProfile) -> NeighbourhoodScore:
        base = (await self.category_breakdown(area_id)).scores

        # NEW: push rank effect into weights (bigger global impact)
        eff_w = self._apply_rank_to_weights(w)

        # keep base categories un-clamped here; clamp only if you must, at the very end
        total = (
            base["Affordability"] * eff_w.wAff +
            base["Accessibility"] * eff_w.wAcc +
            base["Amenities"]     * eff_w.wAmen +
            base["Environment"]   * eff_w.wEnv +
            base["Community"]     * eff_w.wCom
        )
        total=clamp01(total)

        score = NeighbourhoodScore(areaId=area_id, total=round(total, 3), weightsProfileId=w.id)
        self.scores.save(score)
        return score