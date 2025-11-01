"""
Test the filter_locations method with facility filtering using street_facilities data.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.search_service import SearchService
from app.services.rating_engine import RatingEngine
from app.domain.models import SearchFilters
from app.repositories.memory_impl import (
    MemoryPriceRepo, MemoryAmenityRepo, MemoryWeightsRepo,
    MemoryScoreRepo, MemoryCommunityRepo, MemoryTransitRepo,
    MemoryCarparkRepo, MemoryAreaRepo
)


async def test_search_with_facilities():
    """Test searching with facility filters."""
    
    # Initialize repositories
    price_repo = MemoryPriceRepo()
    amenity_repo = MemoryAmenityRepo()
    weights_repo = MemoryWeightsRepo()
    score_repo = MemoryScoreRepo()
    community_repo = MemoryCommunityRepo()
    transit_repo = MemoryTransitRepo()
    carpark_repo = MemoryCarparkRepo()
    area_repo = MemoryAreaRepo()
    
    # Initialize amenity data (loads from cache)
    await MemoryAmenityRepo.initialize()
    
    # Create rating engine
    engine = RatingEngine(
        price_repo, amenity_repo, weights_repo, score_repo,
        community_repo, transit_repo, carpark_repo, area_repo
    )
    
    # Create search service
    service = SearchService(engine)
    
    print("🧪 Testing Filter Locations with Facility Data")
    print("=" * 80)
    
    # Test 1: Search for "TAMPINES" (should return multiple streets)
    print("\n1️⃣  Test: Search 'TAMPINES' (no filters)")
    print("-" * 80)
    filters = SearchFilters(
        search_query="TAMPINES",
        price_range=[0, 10000000],
        facilities=[]
    )
    results = await service.filter_locations(filters)
    print(f"Found {len(results)} results")
    
    if results:
        for i, r in enumerate(results[:3], 1):
            print(f"\n  {i}. {r.street}")
            print(f"     Area: {r.area}")
            print(f"     Facilities: {', '.join(r.facilities) if r.facilities else 'None listed'}")
            print(f"     Location: {r.latitude:.6f}, {r.longitude:.6f}")
    
    # Test 2: Search with "Good Schools" filter
    print("\n\n2️⃣  Test: Search 'TAMPINES' with 'Good Schools' filter")
    print("-" * 80)
    filters = SearchFilters(
        search_query="TAMPINES",
        price_range=[0, 10000000],
        facilities=["Good Schools"]
    )
    results = await service.filter_locations(filters)
    print(f"Found {len(results)} results with schools")
    
    if results:
        for i, r in enumerate(results[:5], 1):
            print(f"\n  {i}. {r.street}")
            facilities_str = ', '.join(r.facilities) if r.facilities else 'None'
            print(f"     Facilities: {facilities_str}")
    
    # Test 3: Search with "Healthcare" filter
    print("\n\n3️⃣  Test: Search 'ANG MO KIO' with 'Healthcare' filter")
    print("-" * 80)
    filters = SearchFilters(
        search_query="ANG MO KIO",
        price_range=[0, 10000000],
        facilities=["Healthcare"]
    )
    results = await service.filter_locations(filters)
    print(f"Found {len(results)} results with healthcare")
    
    if results:
        for i, r in enumerate(results[:5], 1):
            print(f"\n  {i}. {r.street}")
            facilities_str = ', '.join(r.facilities) if r.facilities else 'None'
            print(f"     Facilities: {facilities_str}")
    
    # Test 4: Search with multiple facility filters
    print("\n\n4️⃣  Test: Search 'BUKIT' with 'Schools' and 'Parks' filters")
    print("-" * 80)
    filters = SearchFilters(
        search_query="BUKIT",
        price_range=[0, 10000000],
        facilities=["Schools", "Parks"]
    )
    results = await service.filter_locations(filters)
    print(f"Found {len(results)} results with schools OR parks")
    
    if results:
        for i, r in enumerate(results[:5], 1):
            print(f"\n  {i}. {r.street}")
            facilities_str = ', '.join(r.facilities) if r.facilities else 'None'
            print(f"     Facilities: {facilities_str}")
    
    # Test 5: Search specific street
    print("\n\n5️⃣  Test: Search 'SAGO LANE' (top street by facilities)")
    print("-" * 80)
    filters = SearchFilters(
        search_query="SAGO LANE",
        price_range=[0, 10000000],
        facilities=[]
    )
    results = await service.filter_locations(filters)
    print(f"Found {len(results)} result(s)")
    
    if results:
        r = results[0]
        print(f"\n  Street: {r.street}")
        print(f"  Area: {r.area}")
        print(f"  Description: {r.description}")
        print(f"  Facilities:")
        for fac in r.facilities:
            print(f"    • {fac}")
    
    print("\n" + "=" * 80)
    print("✅ Tests completed!")


if __name__ == "__main__":
    asyncio.run(test_search_with_facilities())
