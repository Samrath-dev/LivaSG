<<<<<<< Updated upstream
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict

from ..domain.models import UserPreference
from ..services.preference_service import PreferenceService

router = APIRouter(prefix="/preferences", tags=["preferences"])

def get_preference_service():
    from ..main import di_preference_service
    return di_preference_service

@router.get("/", response_model=UserPreference)
def get_preferences(service: PreferenceService = Depends(get_preference_service)):
    """Get user preferences"""
    return service.get_preference()

@router.put("/ranks", response_model=UserPreference)
def update_category_ranks(
    category_ranks: Dict[str, int],
    service: PreferenceService = Depends(get_preference_service)
):
    """Update category ranks"""
    valid_categories = {"Affordability", "Accessibility", "Amenities", "Environment", "Community"}
    if not set(category_ranks.keys()).issubset(valid_categories):
        raise HTTPException(status_code=400, detail="Invalid category names")
    
    for rank in category_ranks.values():
        if not 1 <= rank <= 5:
            raise HTTPException(status_code=400, detail="Ranks must be between 1 and 5")
    
=======
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict

from ..domain.models import UserPreference
from ..services.preference_service import PreferenceService

router = APIRouter(prefix="/preferences", tags=["preferences"])

def get_preference_service():
    from ..main import di_preference_service
    return di_preference_service

@router.get("/", response_model=UserPreference)
def get_preferences(service: PreferenceService = Depends(get_preference_service)):
    """Get user preferences"""
    return service.get_preference()

@router.put("/ranks", response_model=UserPreference)
def update_category_ranks(
    category_ranks: Dict[str, int],
    service: PreferenceService = Depends(get_preference_service)
):
    """Update category ranks"""
    valid_categories = {"Affordability", "Accessibility", "Amenities", "Environment", "Community"}
    if not set(category_ranks.keys()).issubset(valid_categories):
        raise HTTPException(status_code=400, detail="Invalid category names")
    
    for rank in category_ranks.values():
        if not 1 <= rank <= 5:
            raise HTTPException(status_code=400, detail="Ranks must be between 1 and 5")
    
>>>>>>> Stashed changes
    return service.update_preference_ranks(category_ranks)