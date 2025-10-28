# app/api/ranks_controller.py
from fastapi import APIRouter, Depends
from ..domain.models import RankProfile

router = APIRouter(prefix="/ranks", tags=["ranks"])

def get_rank_service():
    raise RuntimeError("Rank service not initialized")

@router.get("")
def get_ranks(rank_svc = Depends(get_rank_service)):
    return {"ranks": rank_svc.get_active()}

@router.post("")
def set_ranks(r: RankProfile, rank_svc = Depends(get_rank_service)):
    rank_svc.set(r)
    return {"ok": True, "ranks": rank_svc.get_active()}

@router.post("/reset")
def reset_ranks(rank_svc = Depends(get_rank_service)):
    rank_svc.clear()
    return {"ok": True, "ranks": rank_svc.get_active()}