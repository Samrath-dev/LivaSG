# app/api/onemap_controller.py
from fastapi import APIRouter, Depends, Query, HTTPException

router = APIRouter(prefix="/onemap", tags=["onemap"])


async def get_planning_repo():
    raise HTTPException(status_code=500, detail="Planning repo not initialized")

@router.get("/planning-areas")
async def get_planning_areas(
    year: int = Query(2019, ge=1998, le=2100),
    repo = Depends(get_planning_repo),
):
    return await repo.geojson(year)

@router.get("/planning-area-names")
async def get_planning_area_names(
    year: int = Query(2019, ge=1998, le=2100),
    repo = Depends(get_planning_repo),
):
    return await repo.names(year)


@router.get("/planning-area-at")
async def get_planning_area_at(
    latitude: float = Query(...),
    longitude: float = Query(...),
    year: int = Query(2019, ge=1998, le=2100),
    repo = Depends(get_planning_repo),
):
   
    raise HTTPException(status_code=501, detail="Not implemented in repo yet")