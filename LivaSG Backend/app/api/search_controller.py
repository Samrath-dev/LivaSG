from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
from ..domain.models import NeighbourhoodScore, SearchFilters, LocationResult, OneMapSearchResponse

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
async def filter_locations(filters: SearchFilters):
    """
    Filter locations based on search query, facilities, and price range.
    Corresponds to the filtering functionality in SearchView.tsx.
    """
    try:
        from ..main import di_search
        return await di_search.filter_locations(filters)
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

@router.get("/onemap", response_model=OneMapSearchResponse)
async def search_onemap(
    query: str = Query(..., description="Search query for location"),
    page: int = Query(1, ge=1, description="Page number")
):
    """
    Search for locations using OneMap API.
    Returns results in OneMap's native format.
    
    Example response:
    {
      "found": 1,
      "totalNumPages": 1,
      "pageNum": 1,
      "results": [
        {
          "SEARCHVAL": "640 ROWELL ROAD SINGAPORE 200640",
          "BLK_NO": "640",
          "ROAD_NAME": "ROWELL ROAD",
          "BUILDING": "NIL",
          "ADDRESS": "640 ROWELL ROAD SINGAPORE 200640",
          "POSTAL": "200640",
          "X": "30381.1007417506",
          "Y": "32195.1006872542",
          "LATITUDE": "1.30743547948389",
          "LONGITUDE": "103.854713903431",
          "LONGTITUDE": "103.854713903431"
        }
      ]
    }
    """
    try:
        from ..main import di_search
        return await di_search.search_onemap(query, page)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching OneMap: {str(e)}")