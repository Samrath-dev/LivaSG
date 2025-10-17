from typing import List
from ..domain.models import NeighbourhoodScore, WeightsProfile, SearchFilters, LocationResult
from .rating_engine import RatingEngine

class SearchService:
    def __init__(self, engine: RatingEngine): 
        self.engine = engine
        self._initialize_location_data()

    def rank(self, areas: List[str], weights: WeightsProfile) -> List[NeighbourhoodScore]:
        scores = [self.engine.aggregate(a, weights) for a in areas]
        return sorted(scores, key=lambda s: s.total, reverse=True)
    
    def _initialize_location_data(self):
        """Initialize mock location data similar to frontend"""
        self.location_data = {
            'orchard': [
                LocationResult(
                    id=1,
                    street='Orchard Boulevard',
                    area='Orchard',
                    district='District 9',
                    price_range=[2800000, 8500000],
                    avg_price=3400,
                    facilities=['Near MRT', 'Shopping Malls', 'Fine Dining', 'Entertainment'],
                    description='Prestigious address along Orchard Road with luxury condominiums and excellent connectivity to shopping malls and entertainment hubs.',
                    growth=5.2,
                    amenities=['ION Orchard', 'Wheelock Place', 'Orchard MRT'],
                    latitude=1.3047,
                    longitude=103.8257
                ),
                LocationResult(
                    id=2,
                    street='Scotts Road',
                    area='Orchard',
                    district='District 9',
                    price_range=[2200000, 6000000],
                    avg_price=2900,
                    facilities=['Near MRT', 'Shopping Malls', 'Healthcare'],
                    description='Prime location with luxury hotels, shopping centers, and high-end residential developments.',
                    growth=4.9,
                    amenities=['Scotts Square', 'Far East Plaza', 'Newton MRT'],
                    latitude=1.3094,
                    longitude=103.8350
                )
            ],
            'bukit panjang': [
                LocationResult(
                    id=3,
                    street='Fajar Road',
                    area='Bukit Panjang',
                    district='District 23',
                    price_range=[450000, 1200000],
                    avg_price=680,
                    facilities=['Near MRT', 'Good Schools', 'Community Facilities'],
                    description='Family-friendly neighborhood with good amenities and convenient LRT connectivity to Bukit Panjang town center.',
                    growth=3.8,
                    amenities=['Fajar LRT', 'Bukit Panjang Plaza', 'West Spring Primary'],
                    latitude=1.3850,
                    longitude=103.7714
                ),
                LocationResult(
                    id=4,
                    street='Segar Road',
                    area='Bukit Panjang',
                    district='District 23',
                    price_range=[480000, 1300000],
                    avg_price=720,
                    facilities=['Parks', 'Shopping Malls', 'Sports Facilities'],
                    description='Well-established residential area with proximity to Bukit Panjang Integrated Transport Hub and recreational facilities.',
                    growth=4.1,
                    amenities=['Bukit Panjang ITH', 'Segar LRT', 'Junction 10'],
                    latitude=1.3792,
                    longitude=103.7703
                )
            ],
            'tampines': [
                LocationResult(
                    id=6,
                    street='Tampines Street 11',
                    area='Tampines',
                    district='District 18',
                    price_range=[380000, 950000],
                    avg_price=520,
                    facilities=['Near MRT', 'Good Schools', 'Sports Facilities'],
                    description='Central location in Tampines town with easy access to all amenities and excellent family facilities.',
                    growth=3.2,
                    amenities=['Tampines Mall', 'Tampines MRT', 'Our Tampines Hub'],
                    latitude=1.3472,
                    longitude=103.9447
                ),
                LocationResult(
                    id=7,
                    street='Tampines Avenue 7',
                    area='Tampines',
                    district='District 18',
                    price_range=[420000, 1100000],
                    avg_price=580,
                    facilities=['Parks', 'Sports Facilities', 'Hawker Centres'],
                    description='Quieter part of Tampines with proximity to Tampines Eco Green and various sports facilities.',
                    growth=3.6,
                    amenities=['Tampines Eco Green', 'Safra Tampines', 'Tampines North CC'],
                    latitude=1.3569,
                    longitude=103.9550
                )
            ],
            'jurong': [
                LocationResult(
                    id=8,
                    street='Jurong East Street 13',
                    area='Jurong East',
                    district='District 22',
                    price_range=[350000, 900000],
                    avg_price=480,
                    facilities=['Near MRT', 'Shopping Malls', 'Healthcare'],
                    description='Heart of Jurong East regional centre with excellent connectivity and future growth potential from Jurong Lake District development.',
                    growth=7.8,
                    amenities=['Jurong East MRT', 'JEM Mall', 'Westgate'],
                    latitude=1.3364,
                    longitude=103.7422
                ),
                LocationResult(
                    id=9,
                    street='Jurong West Street 65',
                    area='Jurong West',
                    district='District 22',
                    price_range=[320000, 850000],
                    avg_price=450,
                    facilities=['Good Schools', 'Parks', 'Community Facilities'],
                    description='Mature residential area with established community facilities and good educational institutions.',
                    growth=4.2,
                    amenities=['Pioneer Mall', 'Boon Lay MRT', 'Jurong West Sports Centre'],
                    latitude=1.3419,
                    longitude=103.6994
                )
            ],
            'marine parade': [
                LocationResult(
                    id=10,
                    street='Marine Parade Road',
                    area='Marine Parade',
                    district='District 15',
                    price_range=[1300000, 3800000],
                    avg_price=1650,
                    facilities=['Parks', 'Healthcare', 'Community Facilities'],
                    description='Prime seafront location with panoramic sea views and direct access to East Coast Park.',
                    growth=4.3,
                    amenities=['East Coast Park', 'Parkway Parade', 'Katong Mall'],
                    latitude=1.3031,
                    longitude=103.9075
                ),
                LocationResult(
                    id=11,
                    street='East Coast Road',
                    area='Marine Parade',
                    district='District 15',
                    price_range=[1100000, 3200000],
                    avg_price=1450,
                    facilities=['Hawker Centres', 'Shopping Malls', 'Community Facilities'],
                    description='Historic Katong area with rich Peranakan heritage, famous eateries, and charming shophouses.',
                    growth=4.0,
                    amenities=['Katong I12', 'Roxy Square', 'Marine Parade CC'],
                    latitude=1.3064,
                    longitude=103.9128
                )
            ]
        }

    def filter_locations(self, filters: SearchFilters) -> List[LocationResult]:
        """
        Filter locations based on search criteria and filters.
        This function handles the filtering logic that corresponds to SearchView.tsx filters.
        """
        # Get initial set of locations based on search query
        search_term = filters.search_query.lower() if filters.search_query else ""
        results = []
        
        if search_term:
            # Find locations in areas that match the search term
            for area_key, locations in self.location_data.items():
                if search_term in area_key.lower():
                    results.extend(locations)
        else:
            # If no search query, include all locations for filtering
            for locations in self.location_data.values():
                results.extend(locations)
        
        # Apply price range filter
        filtered_results = []
        for location in results:
            # Check if location's price range overlaps with filter's price range
            if (location.price_range[1] >= filters.price_range[0] and 
                location.price_range[0] <= filters.price_range[1]):
                
                # Apply facilities filter
                if not filters.facilities:
                    # No facility filters applied, include this location
                    filtered_results.append(location)
                else:
                    # Check if location has any of the required facilities (currently OR logic)
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