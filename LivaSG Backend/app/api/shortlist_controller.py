from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List

from ..domain.models import SavedLocation
from ..services.shortlist_service import ShortlistService

router = APIRouter(prefix="/shortlist", tags=["shortlist"])

def get_shortlist_service():
    from ..main import di_shortlist_service
    return di_shortlist_service

@router.get("/saved-locations", response_model=List[SavedLocation])
def get_saved_locations(service: ShortlistService = Depends(get_shortlist_service)):
    """Get saved locations"""
    return service.get_saved_locations()

@router.post("/saved-locations", response_model=SavedLocation)
def save_location(
    location_data: Dict[str, Any],
    service: ShortlistService = Depends(get_shortlist_service)
):
    """Save a location to shortlist by postal code"""
    required_fields = ["postal_code", "address", "area"]
    for field in required_fields:
        if field not in location_data:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    
    return service.save_location(location_data)

@router.delete("/saved-locations/{postal_code}")
def delete_saved_location(
    postal_code: str,
    service: ShortlistService = Depends(get_shortlist_service)
):
    """Remove a location from shortlist by postal code"""
    service.delete_saved_location(postal_code)
    return {"success": True, "message": "Location removed from shortlist"}