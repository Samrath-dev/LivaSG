# app/api/map_controller.py

from fastapi import APIRouter, HTTPException, Depends, Query
from ..domain.models import NeighbourhoodScore
import inspect

router = APIRouter(prefix="/map", tags=["map"])

# Dependency hooks 
def get_engine():
    raise RuntimeError("Rating engine not initialized")

def get_weights_service():
    raise RuntimeError("Weights service not initialized")

def get_planning_repo():
    raise RuntimeError("Planning repo not initialized")


def _coerce_area_names(items) -> list[str]:
    """Accepts either a list[str] or list[dict] from OneMap and returns clean area names."""
    out: list[str] = []
    for it in items or []:
        if isinstance(it, str):
            name = it.strip()
        elif isinstance(it, dict):
            name = (
                it.get("pln_area_n")
                or it.get("name")
                or it.get("area")
                or it.get("areaId")
                or ""
            )
            name = str(name).strip()
        else:
            name = ""
        if not name:
            continue
        name_titled = name.title()
        if name_titled in {"None", "Null", "Undefined"}:
            continue
        out.append(name_titled)

    # Deduplicate while preserving order
    seen = set()
    uniq = []
    for n in out:
        if n not in seen:
            uniq.append(n)
            seen.add(n)
    return uniq


async def _maybe_call(fn, *args, **kwargs):
    """
    Call a function that might be sync or async.
    If it returns an awaitable, await it; else return the value.
    """
    try:
        result = fn(*args, **kwargs)
    except TypeError:
        # Some engines might define aggregate(self, area, weights) vs (weights, area)
        # but we won't guess; just re-raise
        raise
    if inspect.isawaitable(result):
        return await result
    return result


@router.get("/choropleth", response_model=list[NeighbourhoodScore])
async def choropleth(
    weightsId: str = Query("default"),
    engine = Depends(get_engine),
    weights_svc = Depends(get_weights_service),
    planning_repo = Depends(get_planning_repo),
):
    """
    Return neighbourhood scores for *all real* planning areas from OneMap.
    Compatible with sync or async RatingEngine.aggregate().
    """
    try:
        raw = await planning_repo.names(year=2019)  # names() is async in your repo
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load planning areas: {e}")

    areas = _coerce_area_names(raw)
    if not areas:
        raise HTTPException(status_code=500, detail="No planning areas returned by OneMap.")

    weights = weights_svc.get_active()

    results: list[NeighbourhoodScore] = []
    for area_name in areas:
        try:
            score = await _maybe_call(engine.aggregate, area_name, weights)
            # Defensive: some engines might return None on failure
            if score is not None:
                results.append(score)
        except Exception:
            # Uncomment for debug:
            # import traceback; traceback.print_exc()
            continue

    return results