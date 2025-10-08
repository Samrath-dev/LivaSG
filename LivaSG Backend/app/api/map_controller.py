from fastapi import APIRouter
from ..domain.models import NeighbourhoodScore
router = APIRouter()

@router.get("/choropleth", response_model=list[NeighbourhoodScore])
def choropleth(weightsId: str = "default"):
    from ..main import di_weights, di_engine
    areas = ["Bedok", "Tampines", "ToaPayoh", "BukitMerah"]
    w = di_weights.get_active()
    return [di_engine.aggregate(a, w) for a in areas]