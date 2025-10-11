from ..domain.models import CategoryBreakdown, NeighbourhoodScore, WeightsProfile
from ..repositories.interfaces import IPriceRepo, IAmenityRepo, IScoreRepo, ICommunityRepo, ITransitRepo, ICarparkRepo, IAreaRepo
from math import radians, sin, cos, sqrt, atan2

def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))

class RatingEngine:
    """Very light placeholder scoring: affordability derived from latest median price;
    others from amenity counts; simple weighted sum."""
    def __init__(self, price: IPriceRepo, amen: IAmenityRepo, scores: IScoreRepo, community: ICommunityRepo | None = None, transit: ITransitRepo | None = None, carparks: ICarparkRepo | None = None, areas: IAreaRepo | None = None):
        self.price = price
        self.amen  = amen
        self.scores = scores
        self.community = community
        self.transit = transit
        self.carparks = carparks
        self.areas = areas

    def _haversine_km(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        # approximate haversine distance between two lat/lon points in km
        R = 6371.0
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        return R * c

    def _nearest_transit_distance(self, area_id: str) -> float | None:
        # we attempt to find transit nodes for the area; if none, try all nodes and return min dist
        # Need an area centroid: try to use amenity facilities_summary or community centre coords if available
        # For simplicity in this in-memory implementation, we'll look for community centre coords first, else None
        lat = None
        lon = None
        if self.community:
            # try to find a community centre for the area
            try:
                centres = self.community.list_all()
            except Exception:
                centres = []
        # Fallback: no centroid available in generic repo; return None to indicate unknown
        if self.transit is None:
            return None
        nodes = self.transit.list_near_area(area_id)
        if not nodes:
            nodes = self.transit.all()
        # if we can't get an anchor point, return None
        if lat is None or lon is None:
            # No centroid available: cannot compute accurate distance; return small sentinel None
            return None
        # compute min distance
        dists = []
        for n in nodes:
            if n.latitude is None or n.longitude is None:
                continue
            d = self._haversine_km(lat, lon, n.latitude, n.longitude)
            dists.append(d)
        return min(dists) if dists else None

    def _compute_transit_score_from_distance(self, dist_km: float | None) -> float:
        # distance in km: closer => higher score
        if dist_km is None:
            return 0.3  # unknown but pessimistic
        if dist_km <= 0.2:
            return 1.0
        if dist_km <= 1.0:
            return clamp01(1.0 - (dist_km - 0.2) / (1.0 - 0.2))
        # beyond 1km it's low
        return 0.1

    def _carpark_capacity_score(self, area_id: str) -> float:
        # Normalize average capacity (or fallback to facilities carpark count)
        if self.carparks:
            try:
                parks = self.carparks.list_near_area(area_id)
            except Exception:
                parks = []
            if parks:
                avg_cap = sum((p.capacity or 0) for p in parks) / len(parks)
                return clamp01(avg_cap / 500.0)
        # fallback to facilities summary which contains a carparks count
        fac = self.amen.facilities_summary(area_id)
        return clamp01(fac.carparks / 20.0)

    def category_breakdown(self, area_id: str) -> CategoryBreakdown:
        series = self.price.series(area_id, months=1)
        median = series[-1].medianResale if series else 500_000
        # Normalize: 300k→1.0, 900k→0.0 (linear)
        aff = clamp01(1.0 - (median - 300_000) / (900_000 - 300_000))
        fac = self.amen.facilities_summary(area_id)
        amen_score = clamp01((fac.schools + fac.sports + fac.hawkers + fac.healthcare + fac.greenSpaces) / 20.0)
        # Accessibility: combine transit proximity and carpark availability
        # Determine an area centroid if possible using community centre coordinates
        # Use area centroid (preferred) for proximity calculations
        transit_dist = None
        centroid = None
        if self.areas:
            try:
                centroid = self.areas.centroid(area_id)
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
        acc  = clamp01(0.7 * transit_score + 0.3 * carpark_score)
        env  = clamp01(fac.greenSpaces / 10.0)
        # Community score: 1.0 if a community centre exists for the area, else 0.0
        if self.community:
            comm = 1.0 if self.community.exists(area_id) else 0.0
        else:
            comm = 0.0
        return CategoryBreakdown(scores={
            "Affordability": round(aff,3),
            "Accessibility": acc,
            "Amenities": round(amen_score,3),
            "Environment": round(env,3),
            "Community": comm
        })

    def aggregate(self, area_id: str, w: WeightsProfile) -> NeighbourhoodScore:
        b = self.category_breakdown(area_id).scores
        total = (
            b["Affordability"]*w.wAff +
            b["Accessibility"]*w.wAcc +
            b["Amenities"]*w.wAmen +
            b["Environment"]*w.wEnv +
            b["Community"]*w.wCom
        )
        score = NeighbourhoodScore(areaId=area_id, total=round(total,3), weightsProfileId=w.id)
        self.scores.save(score)
        return score

    def temp(self):
        pass
        # FOR comm in category_breakdown():
        # get community centre presence from amenity/communityCentre repo, which gets from models.py
        # from facilities summary, get community centre presence (get id of community centres from cache)
        # in memory_impl.py, MemoryAmenityRepo, add community centre presence - 1.0 if area_id==id else 0.0
        #
        # FOR acc in category_breakdown():
        # proximity to MRT stations, LRT stations, bus stops and carpark availability
        # in memory_impl.py, MemoryAmenityRepo or MemoryTransportRepo, add mrt, lrt, bus stop and carpark counts
        # how to actually calculate the proximity of these transport nodes to the area? (get their coordinates and calculate distance from center of area?)
        # maybe use average distance of all transport nodes to the centre of the area?
        