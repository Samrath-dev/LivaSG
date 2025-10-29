from fastapi import APIRouter, Depends, HTTPException
import time
import traceback

from ..domain.models import ExportData, ImportRequest
from ..services.settings_service import SettingsService
from ..services.shortlist_service import ShortlistService
from ..services.preference_service import PreferenceService

router = APIRouter(prefix="/settings", tags=["settings"])

def get_settings_service():
    from ..main import di_settings_service
    return di_settings_service

def get_shortlist_service():
    from ..main import di_shortlist_service
    return di_shortlist_service

def get_preference_service():
    from ..main import di_preference_service
    return di_preference_service

@router.get("/export", response_model=ExportData)
def export_json(
    settings_service: SettingsService = Depends(get_settings_service),
    shortlist_service: ShortlistService = Depends(get_shortlist_service)
):
    """Export user data as JSON"""
    try:
        saved_locations = shortlist_service.get_saved_locations()
        return settings_service.export_data(saved_locations)
    except Exception as e:
        print(f"Export JSON error: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to export data: {str(e)}"
        )

@router.get("/export/csv")
def export_csv(
    settings_service: SettingsService = Depends(get_settings_service),
    shortlist_service: ShortlistService = Depends(get_shortlist_service)
):
    """Export user data as CSV (default format)"""
    try:
        saved_locations = shortlist_service.get_saved_locations()
        csv_data = settings_service.export_csv(saved_locations)
        return {
            "csv_data": csv_data,
            "filename": f"livasg_export_{time.strftime('%Y%m%d_%H%M%S')}.csv"
        }
    except Exception as e:
        print(f"Export CSV error: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to export CSV: {str(e)}"
        )

@router.get("/export/pdf")
def export_pdf(
    settings_service: SettingsService = Depends(get_settings_service),
    shortlist_service: ShortlistService = Depends(get_shortlist_service)
):
    """Export user data as PDF (base64 encoded)"""
    try:
        saved_locations = shortlist_service.get_saved_locations()
        pdf_data = settings_service.export_pdf(saved_locations)
        return {
            "pdf_data": pdf_data,
            "filename": f"livasg_export_{time.strftime('%Y%m%d_%H%M%S')}.pdf"
        }
    except Exception as e:
        print(f"Export PDF error: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to export PDF: {str(e)}"
        )

@router.post("/import")
def import_data(
    import_request: ImportRequest,
    settings_service: SettingsService = Depends(get_settings_service),
    shortlist_service: ShortlistService = Depends(get_shortlist_service),
    preference_service: PreferenceService = Depends(get_preference_service)
):
    """Import user data from backup (default: CSV)"""
    try:
        from ..main import di_preference_repo
        
        result = settings_service.import_data(
            import_request.data, 
            import_request.import_type,
            di_preference_repo,
            shortlist_service
        )
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["message"])
    except Exception as e:
        print(f"Import error: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500, 
            detail=f"Import failed: {str(e)}"
        )