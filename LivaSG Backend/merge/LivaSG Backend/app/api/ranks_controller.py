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

@router.put("/preferences", response_model=RankProfile)
def update_preference_ranks(
    category_ranks: Dict[str, int],
    rank_svc = Depends(get_rank_service)
):
    """Update category ranks from preference-style dictionary"""
    valid_categories = {"Affordability", "Accessibility", "Amenities", "Environment", "Community"}
    
    if not set(category_ranks.keys()).issubset(valid_categories):
        raise HTTPException(status_code=400, detail="Invalid category names")
    
    for rank in category_ranks.values():
        if not 1 <= rank <= 5:
            raise HTTPException(status_code=400, detail="Ranks must be between 1 and 5")
    
    rank_profile = RankProfile(
        rAff=category_ranks.get("Affordability", 3),
        rAcc=category_ranks.get("Accessibility", 3),
        rAmen=category_ranks.get("Amenities", 3),
        rEnv=category_ranks.get("Environment", 3),
        rCom=category_ranks.get("Community", 3),
    )
    
    rank_svc.set(rank_profile)
    return rank_svc.get_active() or RankProfile(rAff=3, rAcc=3, rAmen=3, rEnv=3, rCom=3)

@router.post("/reset")
def reset_ranks(rank_svc = Depends(get_rank_service)):
    """Reset ranks to default (clear custom ranks)"""
    rank_svc.clear()
    return {"ok": True, "ranks": RankProfile(rAff=3, rAcc=3, rAmen=3, rEnv=3, rCom=3)}

@router.get("/preferences", response_model=RankProfile)
def get_preferences(rank_svc = Depends(get_rank_service)):
    """Get preferences (legacy endpoint - same as get_ranks)"""
    return get_ranks(rank_svc)