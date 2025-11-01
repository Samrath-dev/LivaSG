"""
Populate Missing Facilities and Scores Script
==============================================
This script goes through all streets in street_geocode.db and populates:
1. Missing street_facilities records (facility counts)
2. Missing street_scores records (local_score, transit_km)

The script recomputes ALL facility counts and scores to ensure accuracy.
"""

import sqlite3
import os
import sys
import asyncio
import math
from typing import Dict, List, Any

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def haversine(lat1, lon1, lat2, lon2):
    """Calculate haversine distance between two points in kilometers"""
    R = 6371
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2*R*math.atan2(math.sqrt(a), math.sqrt(1-a))

def _load_facility_datasets():
    """Load and cache facility datasets from disk cache for quick radius counts."""
    try:
        from app.cache.disk_cache import load_cache as _dc_load
        from app.cache.paths import cache_file as _cache_file
    except Exception as e:
        print(f"Warning: Could not import cache utilities: {e}")
        return {
            'schools': [], 'sports': [], 'hawkers': [],
            'healthcare': [], 'greenSpaces': [], 'carparks': []
        }

    datasets = {
        'schools': [], 'sports': [], 'hawkers': [],
        'healthcare': [], 'greenSpaces': [], 'carparks': []
    }

    # Schools (from OneMap search cached pages)
    try:
        blob = _dc_load(_cache_file("onemap_search_school", version=1))
        if blob:
            datasets['schools'] = blob.get('payload', [])
            print(f"Loaded {len(datasets['schools'])} schools")
    except Exception as e:
        print(f"Warning: Could not load schools data: {e}")

    # Sports facilities (data.gov.sg GeoJSON)
    try:
        blob = _dc_load(_cache_file("sports_dataset", version=1))
        sports_raw = blob.get('payload', {}) if blob else {}
        sports = []
        for feature in sports_raw.get('features', []):
            geom = feature.get('geometry', {})
            coords = geom.get('coordinates', [])
            if geom.get('type') == 'Polygon' and coords:
                lat = coords[0][0][1] if coords[0] else None
                lon = coords[0][0][0] if coords[0] else None
            elif geom.get('type') == 'MultiPolygon' and coords:
                lat = coords[0][0][0][1] if coords[0][0] else None
                lon = coords[0][0][0][0] if coords[0][0] else None
            else:
                lat, lon = None, None
            if lat is not None and lon is not None:
                sports.append({'latitude': lat, 'longitude': lon})
        datasets['sports'] = sports
        print(f"Loaded {len(datasets['sports'])} sports facilities")
    except Exception as e:
        print(f"Warning: Could not load sports data: {e}")

    # Hawker centres (Point GeoJSON)
    try:
        blob = _dc_load(_cache_file("hawkers_dataset", version=1))
        hawkers_raw = blob.get('payload', {}) if blob else {}
        hawkers = []
        for feature in hawkers_raw.get('features', []):
            geom = feature.get('geometry', {})
            if geom.get('type') == 'Point':
                coords = geom.get('coordinates', [])
                if len(coords) >= 2:
                    hawkers.append({'latitude': coords[1], 'longitude': coords[0]})
        datasets['hawkers'] = hawkers
        print(f"Loaded {len(datasets['hawkers'])} hawker centres")
    except Exception as e:
        print(f"Warning: Could not load hawkers data: {e}")

    # CHAS clinics (Point GeoJSON)
    try:
        blob = _dc_load(_cache_file("chas_dataset", version=1))
        clinics_raw = blob.get('payload', {}) if blob else {}
        clinics = []
        for feature in clinics_raw.get('features', []):
            geom = feature.get('geometry', {})
            if geom.get('type') == 'Point':
                coords = geom.get('coordinates', [])
                if len(coords) >= 2:
                    clinics.append({'latitude': coords[1], 'longitude': coords[0]})
        datasets['healthcare'] = clinics
        print(f"Loaded {len(datasets['healthcare'])} healthcare facilities")
    except Exception as e:
        print(f"Warning: Could not load healthcare data: {e}")

    # Parks (Point GeoJSON)
    try:
        blob = _dc_load(_cache_file("parks_dataset", version=1))
        parks_raw = blob.get('payload', {}) if blob else {}
        parks = []
        for feature in parks_raw.get('features', []):
            geom = feature.get('geometry', {})
            if geom.get('type') == 'Point':
                coords = geom.get('coordinates', [])
                if len(coords) >= 2:
                    parks.append({'latitude': coords[1], 'longitude': coords[0]})
        datasets['greenSpaces'] = parks
        print(f"Loaded {len(datasets['greenSpaces'])} parks")
    except Exception as e:
        print(f"Warning: Could not load parks data: {e}")

    # HDB Carparks (list of records)
    try:
        blob = _dc_load(_cache_file("hdb_carparks_records", version=1))
        carparks_raw = blob.get('payload', []) if blob else []
        carparks = []
        for cp in carparks_raw:
            lat = cp.get('latitude')
            lon = cp.get('longitude')
            if lat and lon:
                carparks.append({'latitude': float(lat), 'longitude': float(lon)})
        datasets['carparks'] = carparks
        print(f"Loaded {len(datasets['carparks'])} carparks")
    except Exception as e:
        print(f"Warning: Could not load carparks data: {e}")

    return datasets

def _count_facilities_near(lat: float, lon: float, datasets, radius_km: float = 1.0) -> dict:
    """Count facilities near a point.
    Tweaks:
    - Use a smaller radius for healthcare (0.5 km) to avoid inflated counts.
    - Deduplicate very close healthcare points (~100m) to avoid multiple clinics in the same building inflating counts.
    """
    out = {k: 0 for k in ['schools', 'sports', 'hawkers', 'healthcare', 'greenSpaces', 'carparks']}
    # category-specific radius override
    category_radius = {'healthcare': 0.5}
    # approx degrees per ~100m (lat ~ 0.0009, lon depends on latitude)
    lat_cell = 0.0009
    lon_cell = 0.0009 / max(math.cos(math.radians(lat)), 0.3)
    healthcare_cells = set()
    
    for key, items in datasets.items():
        try:
            eff_r = float(category_radius.get(key, radius_km))
            for it in items:
                f_lat = float(it.get('LATITUDE') or it.get('latitude'))
                f_lon = float(it.get('LONGITUDE') or it.get('longitude'))
                if haversine(lat, lon, f_lat, f_lon) <= eff_r:
                    if key == 'healthcare':
                        # dedup nearby clinics by 100m grid
                        cell = (int(f_lat / lat_cell), int(f_lon / lon_cell))
                        if cell in healthcare_cells:
                            continue
                        healthcare_cells.add(cell)
                    out[key] += 1
        except Exception as e:
            continue
    return out

def _clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x

def _compute_local_street_score(lat: float, lon: float, counts: dict, transit_nodes: list) -> float:
    """Compute a local street-level score using nearby facilities and transit proximity.
    Uses only Amenities, Accessibility, Environment and normalizes weights accordingly.
    """
    # Local amenities score
    amen = _clamp01((counts.get('schools', 0) + counts.get('sports', 0) + counts.get('hawkers', 0)
                    + counts.get('healthcare', 0) + counts.get('greenSpaces', 0)) / 22.0)
    # Environment: based on parks
    env = _clamp01((counts.get('greenSpaces', 0)) / 11.0)

    # Accessibility: distance to nearest transit + carparks
    transit_score = 0.35
    dmin = None
    
    if transit_nodes:
        dists = []
        for n in transit_nodes:
            try:
                if n.get('latitude') is None or n.get('longitude') is None:
                    continue
                d = haversine(lat, lon, float(n['latitude']), float(n['longitude']))
                dists.append(d)
            except Exception:
                continue
        dmin = min(dists) if dists else None
    
    # Transit scoring
    if dmin is None:
        transit_score = 0.35
    elif dmin <= 0.2:
        transit_score = 1.0
    elif dmin <= 1.0:
        transit_score = _clamp01(1.0 - (dmin - 0.2) / 0.8)
    else:
        transit_score = 0.12

    carpark_score = _clamp01((counts.get('carparks', 0)) / 22.0)
    acc = _clamp01(0.7 * transit_score + 0.3 * carpark_score)

    # Normalize weights across available categories (Amen, Acc, Env)
    wA, wAcc, wEnv = 0.2, 0.2, 0.2
    denom = (wA + wAcc + wEnv) or 1.0
    local = (amen * wA + acc * wAcc + env * wEnv) / denom
    return float(round(local, 4)), dmin

async def load_transit_nodes():
    """Load transit nodes from the rating engine"""
    try:
        from app.services.rating_engine import RatingEngine
        engine = RatingEngine()
        if hasattr(engine, 'transit') and hasattr(engine.transit, 'all'):
            nodes = engine.transit.all()
            return [{'latitude': n.latitude, 'longitude': n.longitude} for n in nodes 
                   if n.latitude is not None and n.longitude is not None]
    except Exception as e:
        print(f"Warning: Could not load transit nodes: {e}")
    return []

async def populate_missing_data():
    """Main function to populate missing facilities and scores"""
    print("=" * 80)
    print("Populating Missing Facilities and Scores")
    print("=" * 80)
    print()
    
    # Load datasets
    print("Loading facility datasets...")
    datasets = _load_facility_datasets()
    print()
    
    # Load transit nodes
    print("Loading transit nodes...")
    transit_nodes = await load_transit_nodes()
    print(f"Loaded {len(transit_nodes)} transit nodes")
    print()
    
    # Connect to database
    db_path = 'street_geocode.db'
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Ensure tables exist
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS street_facilities (
            street_name TEXT PRIMARY KEY,
            schools INTEGER,
            sports INTEGER,
            hawkers INTEGER,
            healthcare INTEGER,
            greenSpaces INTEGER,
            carparks INTEGER,
            radius_km REAL DEFAULT 1.0,
            calculated_at TEXT DEFAULT (datetime('now'))
        )
        """
    )
    
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS street_scores (
            street_name TEXT PRIMARY KEY,
            local_score REAL NOT NULL,
            transit_km REAL,
            calculated_at TEXT DEFAULT (datetime('now'))
        )
        """
    )
    
    # Get all streets with coordinates
    all_streets = cursor.execute(
        "SELECT street_name, latitude, longitude FROM street_locations WHERE status = 'found' AND latitude IS NOT NULL AND longitude IS NOT NULL"
    ).fetchall()
    
    print(f"Found {len(all_streets)} streets in database")
    print()
    
    # Statistics
    facilities_updated = 0
    scores_updated = 0
    errors = 0
    
    print("Processing streets...")
    print("-" * 80)
    
    for idx, (street_name, lat, lon) in enumerate(all_streets, start=1):
        try:
            # Compute facility counts
            counts = _count_facilities_near(float(lat), float(lon), datasets, radius_km=1.0)
            
            # Insert/update facility counts
            cursor.execute(
                """
                INSERT OR REPLACE INTO street_facilities (
                    street_name, schools, sports, hawkers, healthcare, greenSpaces, carparks, radius_km, calculated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 1.0, datetime('now'))
                """,
                (
                    street_name,
                    counts.get('schools', 0),
                    counts.get('sports', 0),
                    counts.get('hawkers', 0),
                    counts.get('healthcare', 0),
                    counts.get('greenSpaces', 0),
                    counts.get('carparks', 0)
                )
            )
            facilities_updated += 1
            
            # Compute local score
            local_score, transit_dist = _compute_local_street_score(float(lat), float(lon), counts, transit_nodes)
            
            # Insert/update score
            cursor.execute(
                """
                INSERT OR REPLACE INTO street_scores (street_name, local_score, transit_km, calculated_at)
                VALUES (?, ?, ?, datetime('now'))
                """,
                (street_name, float(local_score), float(transit_dist) if transit_dist is not None else None)
            )
            scores_updated += 1
            
            # Progress indicator
            if idx % 50 == 0 or idx == len(all_streets):
                print(f"Progress: {idx}/{len(all_streets)} streets processed")
                
        except Exception as e:
            errors += 1
            print(f"Error processing {street_name}: {e}")
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print("-" * 80)
    print()
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"Total streets processed: {len(all_streets)}")
    print(f"Facilities records updated: {facilities_updated}")
    print(f"Score records updated: {scores_updated}")
    print(f"Errors encountered: {errors}")
    print()
    print("✓ Database population complete!")
    print()

if __name__ == "__main__":
    asyncio.run(populate_missing_data())
