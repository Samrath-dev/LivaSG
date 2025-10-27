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


def _coerce_area_names(items) -> list[str]:
    """Normalize names from OneMap (list[str] or list[dict])."""
    out: list[str] = []
    for it in items or []:
        if isinstance(it, str):
            name = it.strip()
        elif isinstance(it, dict):
            name = str(it.get("pln_area_n") or it.get("name") or "").strip()
        else:
            continue
        if not name:
            continue
        name_titled = name.title()
        if name_titled not in {"None", "Null", "Undefined"}:
            out.append(name_titled)

    # Deduplicate while preserving order
    seen, uniq = set(), []
    for n in out:
        if n not in seen:
            uniq.append(n)
            seen.add(n)
    return uniq


@router.get("/choropleth", response_model=list[NeighbourhoodScore])
async def choropleth(
    weightsId: str = Query("default"),
    engine = Depends(get_engine),
    weights_svc = Depends(get_weights_service),
    planning_repo = Depends(get_planning_repo),
):
    """
    Return neighbourhood scores for *all* planning areas from OneMap.
    Uses async RatingEngine and normalized names.
    """
    try:
        raw_areas = await planning_repo.names(year=2019)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load planning areas: {e}")

    areas = _coerce_area_names(raw_areas)
    if not areas:
        raise HTTPException(status_code=500, detail="No planning areas found.")

    weights = weights_svc.get_active()
    results: list[NeighbourhoodScore] = []

    for area_name in areas:
        try:
            score = await engine.aggregate(area_name, weights)  # This is why the empty...
        except Exception as e:
            # Uncomment for debugging: print(f"Failed {area_name}: {e}")
            continue

    return results