from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from ..domain.models import NeighbourhoodScore, SearchFilters, LocationResult

router = APIRouter()

@router.post("", response_model=List[NeighbourhoodScore])
def search_areas(filters: SearchFilters, weightsId: str = "default"):
    """
    Original search function for area ranking only.
    """
    from ..main import di_search, di_weights
    areas = ["Bedok", "Tampines", "ToaPayoh", "BukitMerah"]
    w = di_weights.get_active()
    return di_search.rank(areas, w)

@router.post("/filter", response_model=List[LocationResult])
def filter_locations(filters: SearchFilters):
    """
    Filter locations based on search query, facilities, and price range.
    Corresponds to the filtering functionality in SearchView.tsx.
    """
    try:
        from ..main import di_search
        return di_search.filter_locations(filters)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error filtering locations: {str(e)}")

@router.post("/search-and-rank", response_model=List[Dict[str, Any]])
def search_and_rank_locations(filters: SearchFilters, weightsId: str = "default"):
    """
    Combined search, filter, and ranking function.
    Returns locations with their ranking scores for comprehensive results.
    """
    try:
        from ..main import di_search, di_weights
        w = di_weights.get_active()
        return di_search.search_and_rank(filters, w)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in search and rank: {str(e)}")

@router.get("/facilities", response_model=List[str])
def get_available_facilities():
    """
    Get list of available facility filters.
    """
    return [
        'Near MRT',
        'Good Schools',
        'Shopping Malls',
        'Parks',
        'Hawker Centres',
        'Healthcare',
        'Sports Facilities',
        'Community Facilities'
    ]