from typing import List
from ..domain.models import NeighbourhoodScore, WeightsProfile, SearchFilters, LocationResult, OneMapSearchResponse
from .rating_engine import RatingEngine
from ..integrations.onemap_client import OneMapClientHardcoded

class SearchService:
    def __init__(self, engine: RatingEngine, onemap_client: OneMapClientHardcoded = None): 
        self.engine = engine
        self.onemap_client = onemap_client or OneMapClientHardcoded()
        self._initialize_location_data()

    def rank(self, areas: List[str], weights: WeightsProfile) -> List[NeighbourhoodScore]:
        scores = [self.engine.aggregate(a, weights) for a in areas]
        return sorted(scores, key=lambda s: s.total, reverse=True)
    
    def _initialize_location_data(self):
        """No longer used. All local locations are loaded from onemap_locations.json."""
        pass

    async def filter_locations(self, filters: SearchFilters) -> List[LocationResult]:
        """
        Filter locations based on search query and filters:
        - If search_query exists: Return only OneMap results (no JSON data)
        - If no search_query: Return only JSON data that matches filters
        """
        import os, json
        from app.domain.models import LocationResult, OneMapSearchResult
        results: List[LocationResult] = []

        # Case 1: Search query exists - pull from OneMap API only
        if filters.search_query:
            onemap_response = await self.search_onemap(filters.search_query)
            # Convert OneMap results to LocationResult format
            for idx, om in enumerate(onemap_response.results):
                try:
                    om_obj = OneMapSearchResult(**om) if isinstance(om, dict) else om
                    results.append(self._convert_onemap_to_location_result(om_obj, idx+1))
                except Exception:
                    continue
        
        # Case 2: No search query - load from local JSON file only
        else:
            json_path = os.path.join(os.path.dirname(__file__), '../../onemap_locations.json')
            if os.path.exists(json_path):
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        for loc in data:
                            try:
                                results.append(LocationResult(**loc))
                            except Exception:
                                continue
                except Exception:
                    pass

        # Apply filter logic (price range, facilities)
        filtered_results = []
        for location in results:
            # Check if location's price range overlaps with filter's price range
            # Skip price check for OneMap results without price data
            price_check_passed = False
            if location.price_range == [0, 0]:
                # OneMap results without price data - pass price check
                price_check_passed = True
            elif (location.price_range[1] >= filters.price_range[0] and 
                  location.price_range[0] <= filters.price_range[1]):
                price_check_passed = True
            
            if price_check_passed:
                # Apply facilities filter
                if not filters.facilities:
                    # No facility filters applied, include this location
                    filtered_results.append(location)
                else:
                    # Check if location has any of the required facilities
                    has_matching_facility = any(
                        any(filter_facility.lower() in facility.lower() 
                            for facility in location.facilities)
                        for filter_facility in filters.facilities
                    )
                    if has_matching_facility:
                        filtered_results.append(location)

        return filtered_results

    def search_and_rank(self, filters: SearchFilters, weights: WeightsProfile) -> List[dict]:
        """
        Combined search, filter, and ranking function.
        Returns locations with their scores for comprehensive results.
        """
        # First filter locations based on search criteria
        filtered_locations = self.filter_locations(filters)
        
        # Extract area names for ranking
        area_names = list(set(location.area for location in filtered_locations))
        
        # Get ranking scores for these areas
        area_scores = self.rank(area_names, weights)
        score_map = {score.areaId: score.total for score in area_scores}
        
        # Combine location data with scores
        results = []
        for location in filtered_locations:
            location_dict = location.dict()
            location_dict['score'] = score_map.get(location.area, 0.0)
            results.append(location_dict)
        
        # Sort by score (highest first)
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return results
    
    async def search_onemap(self, query: str, page: int = 1) -> OneMapSearchResponse:
        """
        Search using OneMap API and return results in OneMap format.
        This maintains the exact format as OneMap API for compatibility.
        """
        result = await self.onemap_client.search(query, page)
        return OneMapSearchResponse(**result)
    
    
    def _convert_onemap_to_location_result(self, onemap_result, idx: int) -> LocationResult:
        """
        Helper method to convert OneMap search result to LocationResult format.
        Useful for integrating OneMap results with existing ranking system.
        """
        # Extract area from address or use road name as fallback
        area = onemap_result.ROAD_NAME.split()[0] if onemap_result.ROAD_NAME else "Unknown"
        
        return LocationResult(
            id=idx,
            street=onemap_result.SEARCHVAL or onemap_result.ROAD_NAME,
            area=area,
            district=onemap_result.ROAD_NAME,  # OneMap doesn't provide district directly
            price_range=[0, 0],  # Would need to fetch from your pricing data
            avg_price=0,  # Would need to fetch from your pricing data
            facilities=[],  # Would need to fetch from amenities data
            description=f"Located at {onemap_result.ADDRESS}",
            growth=0.0,  # Would need historical data
            amenities=[],
            latitude=float(onemap_result.LATITUDE) if onemap_result.LATITUDE else None,
            longitude=float(onemap_result.LONGITUDE) if onemap_result.LONGITUDE else None
        )
    
    '''
    Available facility filters:
    'Near MRT',
    'Good Schools',
    'Shopping Malls',
    'Parks',
    'Hawker Centres',
    'Healthcare',
    'Sports Facilities',
    'Community Facilities'
    '''