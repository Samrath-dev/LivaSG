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
        - If search_query exists: Only search by planning area name, or resolve postal code to planning area.
        - If no search_query: Return all locations matching filters.
        - If no planning area match: Return closest planning area to searched place.
        """
        import os, json, re, math
        from app.domain.models import LocationResult, OneMapSearchResult, AreaCentroid
        results: List[LocationResult] = []

        def is_postal_code(query):
            return bool(re.fullmatch(r"\d{6}", query.strip()))

        async def load_planning_areas_from_popapi():
            # Get planning areas from PopAPI
            try:
                pa_names = await self.onemap_client.planning_area_names()
                # Returns: [ { "id": 114, "pln_area_n": "BEDOK" }, ... ]
                return {pa['pln_area_n'].title() for pa in pa_names}
            except Exception:
                return set()

        async def calculate_planning_area_centroids():
            # Get planning area polygons and calculate centroids
            centroids = {}
            try:
                pa_data = await self.onemap_client.planning_areas()
                # Returns: {"SearchResults": [ { "pln_area_n": "...", "geojson": "{...}" }, ... ]}
                for area in pa_data.get('SearchResults', []):
                    area_name = area['pln_area_n'].title()
                    geojson_str = area.get('geojson', '{}')
                    geojson = json.loads(geojson_str)
                    # Calculate centroid from polygon coordinates
                    coords = []
                    if geojson.get('type') == 'MultiPolygon':
                        for polygon in geojson.get('coordinates', []):
                            for ring in polygon:
                                coords.extend(ring)
                    elif geojson.get('type') == 'Polygon':
                        for ring in geojson.get('coordinates', []):
                            coords.extend(ring)
                    if coords:
                        avg_lon = sum(c[0] for c in coords) / len(coords)
                        avg_lat = sum(c[1] for c in coords) / len(coords)
                        centroids[area_name] = (avg_lat, avg_lon)
            except Exception:
                pass
            return centroids

        def haversine(lat1, lon1, lat2, lon2):
            R = 6371
            phi1, phi2 = math.radians(lat1), math.radians(lat2)
            dphi = math.radians(lat2 - lat1)
            dlambda = math.radians(lon2 - lon1)
            a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
            return 2*R*math.atan2(math.sqrt(a), math.sqrt(1-a))

        def point_in_polygon(lon, lat, polygon):
            # Ray casting algorithm for point-in-polygon
            # GeoJSON: [longitude, latitude]
            num = len(polygon)
            j = num - 1
            inside = False
            for i in range(num):
                lon_i, lat_i = polygon[i][0], polygon[i][1]
                lon_j, lat_j = polygon[j][0], polygon[j][1]
                if ((lat_i > lat) != (lat_j > lat)) and (lon < (lon_j - lon_i) * (lat - lat_i) / (lat_j - lat_i + 1e-12) + lon_i):
                    inside = not inside
                j = i
            return inside

        async def find_area_by_point(lat, lon, pa_data):
            # Check if point is inside any planning area polygon
            for area in pa_data.get('SearchResults', []):
                area_name = area['pln_area_n'].title()
                geojson_str = area.get('geojson', '{}')
                geojson = json.loads(geojson_str)
                if geojson.get('type') == 'MultiPolygon':
                    for polygon in geojson.get('coordinates', []):
                        for ring in polygon:
                            if point_in_polygon(lon, lat, ring):
                                return area_name
                elif geojson.get('type') == 'Polygon':
                    for ring in geojson.get('coordinates', []):
                        if point_in_polygon(lon, lat, ring):
                            return area_name
            return None

        # Load all planning area names from PopAPI
        planning_areas = await load_planning_areas_from_popapi()
        centroids = await calculate_planning_area_centroids()

        # Case 1: Search query exists
        if filters.search_query:
            query = filters.search_query.strip()
            matched_area = None
            # 1. Direct planning area name match
            for area in planning_areas:
                if query.lower() == area.lower():
                    matched_area = area
                    break
            pa_data = await self.onemap_client.planning_areas()
            # 2. If postal code, use OneMap /getPlanningarea endpoint
            if not matched_area and is_postal_code(query):
                onemap_response = await self.search_onemap(query)
                if onemap_response.results:
                    om = onemap_response.results[0]
                    lat, lon = float(om.LATITUDE), float(om.LONGITUDE)
                    try:
                        pa_result = await self.onemap_client.planning_area_at(lat, lon)
                        if pa_result and 'pln_area_n' in pa_result[0]:
                            matched_area = pa_result[0]['pln_area_n'].title()
                    except Exception:
                        pass
            # 3. If not matched, check polygon containment
            if not matched_area:
                onemap_response = await self.search_onemap(query)
                if onemap_response.results:
                    om = onemap_response.results[0]
                    lat, lon = float(om.LATITUDE), float(om.LONGITUDE)
                    matched_area = await find_area_by_point(lat, lon, pa_data)
            # 4. If still not matched, fallback to closest centroid
            if not matched_area:
                onemap_response = await self.search_onemap(query)
                if onemap_response.results:
                    om = onemap_response.results[0]
                    lat, lon = float(om.LATITUDE), float(om.LONGITUDE)
                    min_dist, closest_area = float('inf'), None
                    for area, (alat, alon) in centroids.items():
                        dist = haversine(lat, lon, alat, alon)
                        if dist < min_dist:
                            min_dist, closest_area = dist, area
                    matched_area = closest_area
            # Return LocationResult for matched_area
            if matched_area:
                lat, lon = centroids.get(matched_area, (0.0, 0.0))
                results.append(LocationResult(
                    id=1,
                    street=matched_area,
                    area=matched_area,
                    district=matched_area,
                    price_range=[0, 0],
                    avg_price=0,
                    facilities=[],
                    description=f"Planning area: {matched_area}",
                    growth=0.0,
                    amenities=[],
                    latitude=lat if lat != 0.0 else None,
                    longitude=lon if lon != 0.0 else None
                ))
        else:
            # No search query: return all planning areas as LocationResults
            for idx, area_name in enumerate(planning_areas, start=1):
                lat, lon = centroids.get(area_name, (0.0, 0.0))
                results.append(LocationResult(
                    id=idx,
                    street=area_name,
                    area=area_name,
                    district=area_name,
                    price_range=[0, 0],
                    avg_price=0,
                    facilities=[],
                    description=f"Planning area: {area_name}",
                    growth=0.0,
                    amenities=[],
                    latitude=lat if lat != 0.0 else None,
                    longitude=lon if lon != 0.0 else None
                ))

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
        # Area: extract from ROAD_NAME (first word, typical for Singapore)
        area = onemap_result.ROAD_NAME.split()[0] if onemap_result.ROAD_NAME else "Unknown"
        # Street: SEARCHVAL and BLK_NO (block number)
        street = f"{onemap_result.SEARCHVAL} {onemap_result.BLK_NO}".strip()
        return LocationResult(
            id=idx,
            street=street,
            area=area,
            district=onemap_result.POSTAL or "Unknown",
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