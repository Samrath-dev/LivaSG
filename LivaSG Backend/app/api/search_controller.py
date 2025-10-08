from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from ..domain.models import NeighbourhoodScore

class SearchFilters(BaseModel):
    maxBudget: int | None = None   # placeholder for now

router = APIRouter()

@router.post("", response_model=List[NeighbourhoodScore])
def search(filters: SearchFilters, weightsId: str = "default"):
    from ..main import di_search, di_weights
    areas = ["Bedok", "Tampines", "ToaPayoh", "BukitMerah"]
    w = di_weights.get_active()
    return di_search.rank(areas, w)