# app/services/rating_engine.py
from ..domain.models import CategoryBreakdown, NeighbourhoodScore, WeightsProfile
from ..repositories.interfaces import IPriceRepo, IAmenityRepo, IScoreRepo, ICommunityRepo, ITransitRepo, ICarparkRepo, IAreaRepo
from math import radians, sin, cos, sqrt, atan2

def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))

class RatingEngine:
    """Scoring engine; amenity calls are async, so breakdown/aggregate are async."""
    def __init__(self, price: IPriceRepo, amen: IAmenityRepo, scores: IScoreRepo,
                 community: ICommunityRepo | None = None,
                 transit: ITransitRepo | None = None,
                 carparks: ICarparkRepo | None = None,
                 areas: IAreaRepo | None = None):
        self.price = price
        self.amen  = amen
        self.scores = scores
        self.community = community
        self.transit = transit
        self.carparks = carparks
        self.areas = areas

    def _haversine_km(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371.0
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        return R * c

    def _compute_transit_score_from_distance(self, dist_km: float | None) -> float:
        if dist_km is None:
            return 0.3
        if dist_km <= 0.2:
            return 1.0
        if dist_km <= 1.0:
            return clamp01(1.0 - (dist_km - 0.2) / (1.0 - 0.2))
        return 0.1

    def _carpark_capacity_score(self, area_id: str) -> float:
        if self.carparks:
            try:
                parks = self.carparks.list_near_area(area_id)
            except Exception:
                parks = []
            if parks:
                avg_cap = sum((p.capacity or 0) for p in parks) / len(parks)
                return clamp01(avg_cap / 500.0)
        # fallback: use facilities_summary carparks
        # NOTE: we cannot await here (sync helper), so do not call amenity here.
        return 0.0

    async def category_breakdown(self, area_id: str) -> CategoryBreakdown:
        # Affordability from price series (sync)
        series = self.price.series(area_id, months=1)
        median = series[-1].medianResale if series else 500_000
        aff = clamp01(1.0 - (median - 300_000) / (900_000 - 300_000))

        # Facilities (async)
        fac = await self.amen.facilities_summary(area_id)
        amen_score = clamp01((fac.schools + fac.sports + fac.hawkers + fac.healthcare + fac.greenSpaces) / 20.0)

        # Accessibility — mix of transit and carparks
        transit_dist = None
        centroid = None
        if self.areas:
            try:
                centroid = self.areas.centroid(area_id) if hasattr(self.areas, "centroid") else None
            except Exception:
                centroid = None
        if centroid is not None and self.transit:
            nodes = self.transit.list_near_area(area_id)
            if not nodes:
                nodes = self.transit.all()
            dists = []
            for n in nodes:
                if n.latitude is None or n.longitude is None:
                    continue
                dists.append(self._haversine_km(centroid.latitude, centroid.longitude, n.latitude, n.longitude))
            transit_dist = min(dists) if dists else None
        transit_score = self._compute_transit_score_from_distance(transit_dist)

        carpark_score = self._carpark_capacity_score(area_id)
        # if we didn’t have carparks repo, fallback to fac.carparks
        if carpark_score == 0.0 and hasattr(fac, "carparks"):
            carpark_score = clamp01((fac.carparks or 0) / 20.0)

        acc  = clamp01(0.7 * transit_score + 0.3 * carpark_score)
        env  = clamp01(fac.greenSpaces / 10.0)

        if self.community:
            comm = 1.0 if self.community.exists(area_id) else 0.0
        else:
            comm = 0.0

        return CategoryBreakdown(scores={
            "Affordability": round(aff, 3),
            "Accessibility": acc,
            "Amenities": round(amen_score, 3),
            "Environment": round(env, 3),
            "Community": comm
        })

    async def aggregate(self, area_id: str, w: WeightsProfile) -> NeighbourhoodScore:
        b = (await self.category_breakdown(area_id)).scores
        total = (
            b["Affordability"]*w.wAff +
            b["Accessibility"]*w.wAcc +
            b["Amenities"]*w.wAmen +
            b["Environment"]*w.wEnv +
            b["Community"]*w.wCom
        )
        score = NeighbourhoodScore(areaId=area_id, total=round(total, 3), weightsProfileId=w.id)
        self.scores.save(score)
        return score