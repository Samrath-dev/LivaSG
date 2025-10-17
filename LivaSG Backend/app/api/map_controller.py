# app/api/map_controller.py

from fastapi import APIRouter, HTTPException, Depends, Query
from ..domain.models import NeighbourhoodScore

router = APIRouter(prefix="/map", tags=["map"])

# Dependency hooks 
def get_engine():
    raise RuntimeError("Rating engine not initialized")

def get_weights_service():
    raise RuntimeError("Weights service not initialized")

def get_planning_repo():
    raise RuntimeError("Planning repo not initialized")


@router.get("/choropleth", response_model=list[NeighbourhoodScore])
async def choropleth(
    weightsId: str = Query("default"),
    engine = Depends(get_engine),
    weights_svc = Depends(get_weights_service),
    planning_repo = Depends(get_planning_repo),
):
    """
    Return neighbourhood scores for *all real* planning areas from OneMap.
    """
    try:
        areas = await planning_repo.names(year=2019)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load planning areas: {e}")

    weights = weights_svc.get_active()
    results: list[NeighbourhoodScore] = []

    for area_name in areas:
        try:
            score = engine.aggregate(area_name, weights)
            results.append(score)
        except Exception:
            continue

    return results