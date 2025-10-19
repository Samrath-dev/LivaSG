from fastapi import APIRouter, Query
from ..domain.models import FacilitiesSummary, PriceRecord, CategoryBreakdown
router = APIRouter()

@router.get("/{area_id}/breakdown", response_model=CategoryBreakdown)
def breakdown(area_id: str):
    from ..main import di_engine
    return di_engine.category_breakdown(area_id)

@router.get("/{area_id}/facilities", response_model=FacilitiesSummary)
async def facilities(area_id: str):
    from ..main import di_amenity
    return await di_amenity.facilities_summary(area_id)

@router.get("/{area_id}/price-trend", response_model=list[PriceRecord])
def price_trend(area_id: str, months: int = Query(24, ge=1, le=120)):
    from ..main import di_trend
    return di_trend.series(area_id, months)