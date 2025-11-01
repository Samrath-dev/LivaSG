# app/api/ranks_controller.py
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict

from ..domain.models import RankProfile

router = APIRouter(prefix="/ranks", tags=["ranks"])

def get_rank_service():
    from ..main import di_ranks
    return di_ranks

@router.get("", response_model=RankProfile)
def get_ranks(rank_svc = Depends(get_rank_service)):
    """Get current rank preferences"""
    active_ranks = rank_svc.get_active()
    if active_ranks is None:
        return RankProfile(rAff=3, rAcc=3, rAmen=3, rEnv=3, rCom=3)
    return active_ranks

@router.post("", response_model=RankProfile)
def set_ranks(rank_profile: RankProfile, rank_svc = Depends(get_rank_service)):
    """Set ranks using direct RankProfile model"""
    rank_svc.set(rank_profile)
    return rank_svc.get_active() or RankProfile(rAff=3, rAcc=3, rAmen=3, rEnv=3, rCom=3)


@router.post("/reset")
def reset_ranks(rank_svc = Depends(get_rank_service)):
    """Reset ranks to default (clear custom ranks)"""
    rank_svc.clear()
    return {"ok": True, "ranks": RankProfile(rAff=3, rAcc=3, rAmen=3, rEnv=3, rCom=3)}
