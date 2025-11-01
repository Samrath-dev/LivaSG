# app/api/transit_debug.py
from __future__ import annotations
from math import radians, sin, cos, asin, sqrt
from typing import List
from fastapi import APIRouter, Depends, Query

from app.repositories.memory_impl import MemoryTransitRepo
from app.domain.models import Transit  # if you have a Pydantic model; else return dicts

router = APIRouter(prefix="/debug/transit", tags=["debug-transit"])

def get_transit_repo() -> MemoryTransitRepo:
    # will be overridden from main.py to your singleton (di_transit)
    return MemoryTransitRepo()

@router.get("/count")
async def count(repo: MemoryTransitRepo = Depends(get_transit_repo)):
    nodes = repo.all()
    by_type = {}
    for n in nodes:
        by_type[n.type] = by_type.get(n.type, 0) + 1
    return {"total": len(nodes), "byType": by_type}

@router.get("/area/{area_id}")
async def by_area(area_id: str, repo: MemoryTransitRepo = Depends(get_transit_repo)):
    nodes = repo.list_near_area(area_id)
    # return a compact payload
    return {"areaId": area_id, "count": len(nodes), "nodes": [
        {"id": n.id, "type": n.type, "name": n.name, "lat": n.latitude, "lon": n.longitude}
        for n in nodes
    ]}

def _haversine(lat1, lon1, lat2, lon2):
    # km
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return 2 * R * asin(sqrt(a))

@router.get("/nearest")
async def nearest(
    lat: float = Query(...),
    lon: float = Query(...),
    k: int = Query(10, ge=1, le=100),
    repo: MemoryTransitRepo = Depends(get_transit_repo),
):
    nodes = repo.all()
    ranked = sorted(
        nodes,
        key=lambda n: _haversine(lat, lon, n.latitude, n.longitude)
    )[:k]
    return [
        {
            "id": n.id,
            "type": n.type,
            "name": n.name,
            "areaId": n.areaId,
            "lat": n.latitude,
            "lon": n.longitude
        } for n in ranked
    ]