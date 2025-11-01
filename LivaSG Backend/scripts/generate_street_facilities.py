"""
Generate facility counts for all 653 streets in street_geocode.db

This script:
1. Loads facility data from disk cache
2. For each street with coordinates in street_geocode.db:
   - Counts facilities within a radius (e.g., 1km)
   - Saves counts to a new table: street_facilities
3. Uses caching to avoid reloading large datasets
"""

import json
import math
import os
import sqlite3
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.cache.disk_cache import load_cache
from app.cache.paths import cache_file

# Constants
BACKEND_DIR = Path(__file__).parent.parent
STREET_DB_PATH = BACKEND_DIR / "street_geocode.db"
SEARCH_RADIUS_KM = 1.0  # Search within 1km radius


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth (in kilometers).
    """
    R = 6371  # Radius of Earth in kilometers

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def load_cached_facilities() -> Dict[str, List[Dict[str, Any]]]:
    """
    Load all facility datasets from disk cache.
    """
    print("📦 Loading facility data from cache...")
    
    facilities = {}
    
    # Load schools (from OneMap search)
    schools_cache = cache_file("onemap_search_school", version=1)
    blob = load_cache(schools_cache)
    if blob:
        schools_data = blob.get('payload', [])
        facilities['schools'] = schools_data
        print(f"  ✓ Schools: {len(schools_data)}")
    else:
        facilities['schools'] = []
        print(f"  ⚠️  Schools: No cache found")
    
    # Load sports facilities
    sports_cache = cache_file("sports_dataset", version=1)
    blob = load_cache(sports_cache)
    if blob:
        sports_raw = blob.get('payload', {})
        # Extract from GeoJSON features
        sports_data = []
        for feature in sports_raw.get('features', []):
            props = feature.get('properties', {})
            geom = feature.get('geometry', {})
            coords = geom.get('coordinates', [])
            
            # Handle different geometry types
            if geom.get('type') == 'Polygon' and coords:
                lat = coords[0][0][1] if coords[0] else None
                lon = coords[0][0][0] if coords[0] else None
            elif geom.get('type') == 'MultiPolygon' and coords:
                lat = coords[0][0][0][1] if coords[0][0] else None
                lon = coords[0][0][0][0] if coords[0][0] else None
            else:
                lat, lon = None, None
            
            if lat and lon:
                sports_data.append({
                    'latitude': lat,
                    'longitude': lon,
                    'name': props.get('Description', '').split('<td>')[1].split('</td>')[0] if '<td>' in props.get('Description', '') else ''
                })
        facilities['sports'] = sports_data
        print(f"  ✓ Sports: {len(sports_data)}")
    else:
        facilities['sports'] = []
        print(f"  ⚠️  Sports: No cache found")
    
    # Load hawker centres
    hawkers_cache = cache_file("hawkers_dataset", version=1)
    blob = load_cache(hawkers_cache)
    if blob:
        hawkers_raw = blob.get('payload', {})
        hawkers_data = []
        for feature in hawkers_raw.get('features', []):
            props = feature.get('properties', {})
            geom = feature.get('geometry', {})
            if geom.get('type') == 'Point':
                coords = geom.get('coordinates', [])
                if len(coords) >= 2:
                    hawkers_data.append({
                        'latitude': coords[1],
                        'longitude': coords[0],
                        'name': props.get('NAME', '')
                    })
        facilities['hawkers'] = hawkers_data
        print(f"  ✓ Hawkers: {len(hawkers_data)}")
    else:
        facilities['hawkers'] = []
        print(f"  ⚠️  Hawkers: No cache found")
    
    # Load CHAS clinics
    clinics_cache = cache_file("chas_dataset", version=1)
    blob = load_cache(clinics_cache)
    if blob:
        clinics_raw = blob.get('payload', {})
        clinics_data = []
        for feature in clinics_raw.get('features', []):
            props = feature.get('properties', {})
            geom = feature.get('geometry', {})
            if geom.get('type') == 'Point':
                coords = geom.get('coordinates', [])
                if len(coords) >= 2:
                    name = props.get('Description', '')
                    if '<td>' in name:
                        name = name.split('<td>')[2].split('</td>')[0] if len(name.split('<td>')) > 2 else name
                    clinics_data.append({
                        'latitude': coords[1],
                        'longitude': coords[0],
                        'name': name
                    })
        facilities['healthcare'] = clinics_data
        print(f"  ✓ Healthcare: {len(clinics_data)}")
    else:
        facilities['healthcare'] = []
        print(f"  ⚠️  Healthcare: No cache found")
    
    # Load parks
    parks_cache = cache_file("parks_dataset", version=1)
    blob = load_cache(parks_cache)
    if blob:
        parks_raw = blob.get('payload', {})
        parks_data = []
        for feature in parks_raw.get('features', []):
            props = feature.get('properties', {})
            geom = feature.get('geometry', {})
            if geom.get('type') == 'Point':
                coords = geom.get('coordinates', [])
                if len(coords) >= 2:
                    parks_data.append({
                        'latitude': coords[1],
                        'longitude': coords[0],
                        'name': props.get('NAME', '')
                    })
        facilities['greenSpaces'] = parks_data
        print(f"  ✓ Green Spaces: {len(parks_data)}")
    else:
        facilities['greenSpaces'] = []
        print(f"  ⚠️  Green Spaces: No cache found")
    
    # Load carparks
    carparks_cache = cache_file("hdb_carparks_records", version=1)
    blob = load_cache(carparks_cache)
    if blob:
        carparks_raw = blob.get('payload', [])
        carparks_data = []
        for cp in carparks_raw:
            lat = cp.get('latitude')
            lon = cp.get('longitude')
            if lat and lon:
                carparks_data.append({
                    'latitude': float(lat),
                    'longitude': float(lon),
                    'name': cp.get('address', '')
                })
        facilities['carparks'] = carparks_data
        print(f"  ✓ Carparks: {len(carparks_data)}")
    else:
        facilities['carparks'] = []
        print(f"  ⚠️  Carparks: No cache found")
    
    # Load community centres (from MemoryCommunityRepo)
    try:
        from app.repositories.memory_impl import MemoryCommunityRepo
        community_repo = MemoryCommunityRepo()
        community_centres = community_repo._centres or []
        community_data = []
        for cc in community_centres:
            try:
                if cc.latitude and cc.longitude:
                    community_data.append({
                        'latitude': float(cc.latitude),
                        'longitude': float(cc.longitude),
                        'name': cc.name
                    })
            except (AttributeError, ValueError):
                continue
        facilities['community'] = community_data
        print(f"  ✓ Community Centres: {len(community_data)}")
    except Exception as e:
        facilities['community'] = []
        print(f"  ⚠️  Community Centres: {e}")
    
    return facilities


def count_facilities_near_point(lat: float, lon: float, facilities: List[Dict], radius_km: float) -> int:
    """
    Count facilities within radius_km of the given point.
    """
    count = 0
    for facility in facilities:
        try:
            f_lat = float(facility.get('LATITUDE') or facility.get('latitude'))
            f_lon = float(facility.get('LONGITUDE') or facility.get('longitude'))
            
            distance = haversine_distance(lat, lon, f_lat, f_lon)
            if distance <= radius_km:
                count += 1
        except (TypeError, ValueError, KeyError):
            continue
    
    return count


def create_facilities_table(conn: sqlite3.Connection):
    """
    Create the street_facilities table if it doesn't exist.
    """
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS street_facilities (
            street_name TEXT PRIMARY KEY,
            schools INTEGER DEFAULT 0,
            sports INTEGER DEFAULT 0,
            hawkers INTEGER DEFAULT 0,
            healthcare INTEGER DEFAULT 0,
            greenSpaces INTEGER DEFAULT 0,
            carparks INTEGER DEFAULT 0,
            community INTEGER DEFAULT 0,
            radius_km REAL DEFAULT 1.0,
            calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (street_name) REFERENCES street_locations(street_name)
        )
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_street_facilities 
        ON street_facilities(street_name)
    """)
    
    conn.commit()


def process_streets(conn: sqlite3.Connection, facilities: Dict[str, List[Dict]]):
    """
    Process all streets and calculate facility counts.
    """
    cursor = conn.cursor()
    
    # Get all streets with coordinates
    cursor.execute("""
        SELECT street_name, latitude, longitude 
        FROM street_locations 
        WHERE status = 'found' AND latitude IS NOT NULL AND longitude IS NOT NULL
        ORDER BY street_name
    """)
    
    streets = cursor.fetchall()
    total = len(streets)
    
    print(f"\n🔍 Processing {total} streets with coordinates...")
    print(f"📏 Search radius: {SEARCH_RADIUS_KM} km")
    print()
    
    start_time = time.time()
    
    for idx, (street_name, lat, lon) in enumerate(streets, 1):
        # Count facilities near this street
        counts = {
            'schools': count_facilities_near_point(lat, lon, facilities['schools'], SEARCH_RADIUS_KM),
            'sports': count_facilities_near_point(lat, lon, facilities['sports'], SEARCH_RADIUS_KM),
            'hawkers': count_facilities_near_point(lat, lon, facilities['hawkers'], SEARCH_RADIUS_KM),
            'healthcare': count_facilities_near_point(lat, lon, facilities['healthcare'], SEARCH_RADIUS_KM),
            'greenSpaces': count_facilities_near_point(lat, lon, facilities['greenSpaces'], SEARCH_RADIUS_KM),
            'carparks': count_facilities_near_point(lat, lon, facilities['carparks'], SEARCH_RADIUS_KM),
            'community': count_facilities_near_point(lat, lon, facilities['community'], SEARCH_RADIUS_KM),
        }
        
        # Insert or update
        cursor.execute("""
            INSERT OR REPLACE INTO street_facilities 
            (street_name, schools, sports, hawkers, healthcare, greenSpaces, carparks, community, radius_km, calculated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            street_name,
            counts['schools'],
            counts['sports'],
            counts['hawkers'],
            counts['healthcare'],
            counts['greenSpaces'],
            counts['carparks'],
            counts['community'],
            SEARCH_RADIUS_KM
        ))
        
        # Progress update
        if idx % 50 == 0 or idx == total:
            elapsed = time.time() - start_time
            rate = idx / elapsed if elapsed > 0 else 0
            eta = (total - idx) / rate if rate > 0 else 0
            
            print(f"  [{idx:>3}/{total}] {street_name[:40]:<40} | "
                  f"Schools:{counts['schools']:>3} Sports:{counts['sports']:>3} Hawkers:{counts['hawkers']:>3} "
                  f"Healthcare:{counts['healthcare']:>3} Parks:{counts['greenSpaces']:>3} Carparks:{counts['carparks']:>4} "
                  f"Community:{counts['community']:>3} | ETA: {eta:.0f}s")
            
            # Commit in batches
            conn.commit()
    
    conn.commit()
    
    elapsed = time.time() - start_time
    print(f"\n✅ Completed in {elapsed:.1f}s ({total/elapsed:.1f} streets/sec)")


def show_summary(conn: sqlite3.Connection):
    """
    Show summary statistics.
    """
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            AVG(schools) as avg_schools,
            AVG(sports) as avg_sports,
            AVG(hawkers) as avg_hawkers,
            AVG(healthcare) as avg_healthcare,
            AVG(greenSpaces) as avg_parks,
            AVG(carparks) as avg_carparks
        FROM street_facilities
    """)
    
    row = cursor.fetchone()
    
    print(f"\n📊 Summary Statistics")
    print("━" * 80)
    print(f"Total streets processed: {row[0]}")
    print(f"Average facilities per street (within {SEARCH_RADIUS_KM}km):")
    print(f"  Schools:     {row[1]:.1f}")
    print(f"  Sports:      {row[2]:.1f}")
    print(f"  Hawkers:     {row[3]:.1f}")
    print(f"  Healthcare:  {row[4]:.1f}")
    print(f"  Parks:       {row[5]:.1f}")
    print(f"  Carparks:    {row[6]:.1f}")
    
    # Top 5 streets by total facilities
    cursor.execute("""
        SELECT 
            street_name,
            (schools + sports + hawkers + healthcare + greenSpaces + carparks) as total
        FROM street_facilities
        ORDER BY total DESC
        LIMIT 5
    """)
    
    print(f"\n🏆 Top 5 Streets by Total Facilities:")
    print("━" * 80)
    for street, total in cursor.fetchall():
        print(f"  {street:<50} {total:>4} facilities")


def main():
    print("🏗️  Street Facilities Generator")
    print("━" * 80)
    
    if not STREET_DB_PATH.exists():
        print(f"❌ Database not found: {STREET_DB_PATH}")
        return
    
    # Load facilities from cache
    facilities = load_cached_facilities()
    
    # Check if we have any data
    total_facilities = sum(len(f) for f in facilities.values())
    if total_facilities == 0:
        print("\n❌ No facility data found in cache!")
        print("Run the backend server first to populate the cache.")
        return
    
    print(f"\n✓ Loaded {total_facilities} total facility records")
    
    # Connect to database
    conn = sqlite3.connect(STREET_DB_PATH)
    
    try:
        # Create table
        create_facilities_table(conn)
        print("\n✓ Created street_facilities table")
        
        # Process streets
        process_streets(conn, facilities)
        
        # Show summary
        show_summary(conn)
        
        print(f"\n💾 Data saved to: {STREET_DB_PATH}")
        print(f"📋 Table: street_facilities")
        
    finally:
        conn.close()


if __name__ == "__main__":
    main()
