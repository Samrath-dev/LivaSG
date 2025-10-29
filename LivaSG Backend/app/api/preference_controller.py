from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
import time

from ..domain.models import UserPreference, SavedLocation, ExportData, ImportRequest
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

   
    valid_categories = {"Affordability", "Accessibility", "Amenities", "Environment", "Community"}
    if not set(category_ranks.keys()).issubset(valid_categories):
        raise HTTPException(status_code=400, detail="Invalid category names")
    
    for rank in category_ranks.values():
        if not 1 <= rank <= 5:
            raise HTTPException(status_code=400, detail="Ranks must be between 1 and 5")
    
    return service.update_preference_ranks(category_ranks)

@router.get("/saved-locations", response_model=List[SavedLocation])
def get_saved_locations(service: PreferenceService = Depends(get_preference_service)):
    """Get saved locations"""
    return service.get_saved_locations()

@router.post("/saved-locations", response_model=SavedLocation)
def saved_location(
    location_data: Dict[str, Any],
    service: PreferenceService = Depends(get_preference_service)
):
    """Save a location to shortlist by postal code"""
    required_fields = ["postal_code", "address", "area"]
    for field in required_fields:
        if field not in location_data:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
    
    return service.saved_location(location_data)

@router.delete("/saved-locations/{postal_code}")
def delete_saved_location(
    postal_code: str,
    service: PreferenceService = Depends(get_preference_service)
):
    """Remove a location from shortlist by postal code"""
    service.delete_saved_location(postal_code)
    return {"success": True, "message": "Location removed from shortlist"}

@router.get("/export", response_model=ExportData)
def export_json(service: PreferenceService = Depends(get_preference_service)):
    """Export user data as JSON"""
    return service.export_data()

@router.get("/export/csv")
def export_csv(service: PreferenceService = Depends(get_preference_service)):
    """Export user data as CSV (default format)"""
    csv_data = service.export_csv()
    return {
        "csv_data": csv_data,
        "filename": f"livasg_export_{time.strftime('%Y%m%d_%H%M%S')}.csv"
    }

@router.get("/export/pdf")
def export_pdf(service: PreferenceService = Depends(get_preference_service)):
    """Export user data as PDF (base64 encoded)"""
    pdf_data = service.export_pdf()
    return {
        "pdf_data": pdf_data,
        "filename": f"livasg_export_{time.strftime('%Y%m%d_%H%M%S')}.pdf"
    }

@router.post("/import")
def import_data(
    import_request: ImportRequest,
    service: PreferenceService = Depends(get_preference_service)
):
    """Import user data from backup (default: CSV)"""
    result = service.import_data(import_request.data, import_request.import_type)
    
    if result["success"]:
        return result
    else:
        raise HTTPException(status_code=400, detail=result["message"])