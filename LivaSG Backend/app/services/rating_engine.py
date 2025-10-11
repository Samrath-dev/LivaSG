from ..domain.models import CategoryBreakdown, NeighbourhoodScore, WeightsProfile
from ..repositories.interfaces import IPriceRepo, IAmenityRepo, IScoreRepo, ICommunityRepo

def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))

class RatingEngine:
    """Very light placeholder scoring: affordability derived from latest median price;
    others from amenity counts; simple weighted sum."""
    def __init__(self, price: IPriceRepo, amen: IAmenityRepo, scores: IScoreRepo, community: ICommunityRepo | None = None):
        self.price = price
        self.amen  = amen
        self.scores = scores
        self.community = community

    def category_breakdown(self, area_id: str) -> CategoryBreakdown:
        series = self.price.series(area_id, months=1)
        median = series[-1].medianResale if series else 500_000
        # Normalize: 300k→1.0, 900k→0.0 (linear)
        aff = clamp01(1.0 - (median - 300_000) / (900_000 - 300_000))
        fac = self.amen.facilities_summary(area_id)
        amen_score = clamp01((fac.schools + fac.sports + fac.hawkers + fac.healthcare + fac.greenSpaces) / 20.0)
        acc  = 0.75  # placeholder
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
        