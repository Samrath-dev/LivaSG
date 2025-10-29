from fastapi import APIRouter, Depends, HTTPException
import time

from ..domain.models import ExportData, ImportRequest
from ..services.preference_service import PreferenceService

router = APIRouter(prefix="/settings", tags=["settings"])

def get_preference_service():
    from ..main import di_preference_service
    return di_preference_service

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