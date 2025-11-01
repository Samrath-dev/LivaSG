"""
Migration script to add planning_area column to street_locations table
and populate it for all existing records.
"""
import sqlite3
import asyncio
import json
import os
import sys
from typing import Optional

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.integrations.onemap_client import OneMapClientHardcoded


def point_in_polygon(lon, lat, polygon):
    """Ray casting algorithm for point-in-polygon check"""
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


async def find_area_by_point(lat: float, lon: float, polygons_cache: dict) -> Optional[str]:
    """Check if point is inside any planning area polygon"""
    for area_name, geojson in polygons_cache.items():
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


async def load_planning_area_polygons():
    """Load planning area polygons from cache or API"""
    polygons = {}
    
    # Try to load from planning_cache.db first
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        cache_db_path = os.path.join(base_dir, 'planning_cache.db')
        
        if os.path.exists(cache_db_path):
            conn = sqlite3.connect(cache_db_path)
            try:
                rows = conn.execute(
                    "SELECT area_name, geojson FROM planning_area_polygons WHERE year = 2019"
                ).fetchall()
                
                if rows:
                    for area_name, geojson_str in rows:
                        polygons[area_name] = json.loads(geojson_str)
                    print(f"Loaded {len(polygons)} planning areas from cache")
                    return polygons
            finally:
                conn.close()
    except Exception as e:
        print(f"Could not load from cache: {e}")
    
    # Fallback: fetch from API
    print("Fetching planning areas from OneMap API...")
    client = OneMapClientHardcoded()
    try:
        pa_data = await client.planning_areas(2019)
        for area in pa_data.get('SearchResults', []):
            area_name = area['pln_area_n'].title()
            geojson_str = area.get('geojson', '{}')
            geojson = json.loads(geojson_str)
            polygons[area_name] = geojson
        print(f"Loaded {len(polygons)} planning areas from API")
    except Exception as e:
        print(f"Error fetching from API: {e}")
    
    return polygons


async def determine_planning_area(lat: float, lon: float, polygons_cache: dict, client: OneMapClientHardcoded) -> Optional[str]:
    """Determine planning area for given coordinates"""
    # Try API first (more accurate)
    try:
        pa_result = await client.planning_area_at(lat, lon)
        if pa_result and len(pa_result) > 0 and 'pln_area_n' in pa_result[0]:
            return pa_result[0]['pln_area_n'].title()
    except Exception as e:
        print(f"  API lookup failed for ({lat}, {lon}): {e}")
    
    # Fallback to polygon containment
    try:
        area = await find_area_by_point(lat, lon, polygons_cache)
        if area:
            return area
    except Exception as e:
        print(f"  Polygon check failed for ({lat}, {lon}): {e}")
    
    return None


async def main():
    """Main migration function"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, 'street_geocode.db')
    
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return
    
    print("Starting migration: Adding planning_area column to street_locations")
    print("=" * 70)
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Step 1: Add column if it doesn't exist
    print("\n1. Adding planning_area column...")
    try:
        cursor.execute("ALTER TABLE street_locations ADD COLUMN planning_area TEXT")
        conn.commit()
        print("   ✓ Column added successfully")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print("   ✓ Column already exists")
        else:
            print(f"   ✗ Error adding column: {e}")
            conn.close()
            return
    
    # Step 2: Load planning area polygons
    print("\n2. Loading planning area polygons...")
    polygons_cache = await load_planning_area_polygons()
    
    if not polygons_cache:
        print("   ✗ Failed to load planning areas. Cannot proceed.")
        conn.close()
        return
    
    # Step 3: Get all streets that need updating
    print("\n3. Finding streets without planning_area...")
    cursor.execute("""
        SELECT street_name, latitude, longitude 
        FROM street_locations 
        WHERE status = 'found' 
        AND latitude IS NOT NULL 
        AND longitude IS NOT NULL
        AND (planning_area IS NULL OR planning_area = '')
    """)
    streets_to_update = cursor.fetchall()
    
    print(f"   Found {len(streets_to_update)} streets to update")
    
    if len(streets_to_update) == 0:
        print("   ✓ All streets already have planning_area set")
        conn.close()
        return
    
    # Step 4: Update each street with planning area
    print("\n4. Updating planning areas for streets...")
    client = OneMapClientHardcoded()
    updated_count = 0
    failed_count = 0
    
    for idx, (street_name, lat, lon) in enumerate(streets_to_update, 1):
        print(f"   [{idx}/{len(streets_to_update)}] Processing: {street_name}", end="")
        
        try:
            planning_area = await determine_planning_area(lat, lon, polygons_cache, client)
            
            if planning_area:
                cursor.execute(
                    "UPDATE street_locations SET planning_area = ? WHERE street_name = ?",
                    (planning_area, street_name)
                )
                print(f" → {planning_area}")
                updated_count += 1
            else:
                print(" → Not found")
                failed_count += 1
        except Exception as e:
            print(f" → Error: {e}")
            failed_count += 1
        
        # Commit every 10 records
        if idx % 10 == 0:
            conn.commit()
    
    # Final commit
    conn.commit()
    
    # Step 5: Summary
    print("\n" + "=" * 70)
    print("Migration complete!")
    print(f"  ✓ Successfully updated: {updated_count} streets")
    if failed_count > 0:
        print(f"  ✗ Failed to update: {failed_count} streets")
    
    # Show some sample results
    print("\nSample results:")
    cursor.execute("""
        SELECT street_name, planning_area 
        FROM street_locations 
        WHERE planning_area IS NOT NULL 
        LIMIT 5
    """)
    samples = cursor.fetchall()
    for street, area in samples:
        print(f"  - {street} → {area}")
    
    conn.close()
    print("\n✓ Database connection closed")


if __name__ == "__main__":
    asyncio.run(main())
