
from fastapi import APIRouter, Depends, Query
from typing import Annotated, Any, Dict


async def get_planning_repo():
    raise RuntimeError("Planning repo not initialized")

router = APIRouter(prefix="/onemap", tags=["onemap"])

@router.get("/planning-areas")
async def get_planning_areas(
    year: int = Query(2020, ge=2000, le=2100),
    repo = Depends(get_planning_repo)
):
    return await repo.geojson(year)

@router.get("/planning-area-names")
async def get_planning_area_names(
    year: int = Query(2020, ge=2000, le=2100),
    repo = Depends(get_planning_repo)
):
    return await repo.names(year)