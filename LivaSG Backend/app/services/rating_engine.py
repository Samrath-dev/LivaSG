from ..domain.models import CategoryBreakdown, NeighbourhoodScore, WeightsProfile
from ..repositories.interfaces import IPriceRepo, IAmenityRepo, IScoreRepo

def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))

class RatingEngine:
    """Very light placeholder scoring: affordability derived from latest median price;
    others from amenity counts; simple weighted sum."""
    def __init__(self, price: IPriceRepo, amen: IAmenityRepo, scores: IScoreRepo):
        self.price = price
        self.amen  = amen
        self.scores = scores

    def category_breakdown(self, area_id: str) -> CategoryBreakdown:
        series = self.price.series(area_id, months=1)
        median = series[-1].medianResale if series else 500_000
        # Normalize: 300k→1.0, 900k→0.0 (linear)
        aff = clamp01(1.0 - (median - 300_000) / (900_000 - 300_000))
        fac = self.amen.facilities_summary(area_id)
        amen_score = clamp01((fac.schools + fac.sports + fac.hawkers + fac.healthcare + fac.greenSpaces) / 20.0)
        acc  = 0.75  # placeholder
        env  = clamp01(fac.greenSpaces / 10.0)
        comm = 0.8   # placeholder
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