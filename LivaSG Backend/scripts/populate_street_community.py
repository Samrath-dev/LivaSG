"""
Populate the community column in street_geocode.db's street_facilities table.
Counts community centres within 1km radius of each street.
"""

import os
import sys
import sqlite3
import math

# Add parent directory to path to import app modules
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..'))
sys.path.insert(0, PROJECT_ROOT)

from app.repositories.memory_impl import MemoryCommunityRepo


def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in kilometers."""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2*R*math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


def main():
    print("=" * 60)
    print("POPULATING COMMUNITY CENTRES FOR STREETS")
    print("=" * 60)
    
    # Initialize community repository
    print("\n[1/4] Loading community centres data...")
    community_repo = MemoryCommunityRepo()
    community_centres = community_repo._centres or []
    print(f"  Loaded {len(community_centres)} community centres")
    
    # Connect to street database
    street_db_path = os.path.join(PROJECT_ROOT, 'street_geocode.db')
    print(f"\n[2/4] Connecting to database: {street_db_path}")
    
    if not os.path.exists(street_db_path):
        print(f"  ERROR: Database not found at {street_db_path}")
        return
    
    conn = sqlite3.connect(street_db_path)
    cur = conn.cursor()
    
    # Check if street_facilities table exists
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='street_facilities'")
    if not cur.fetchone():
        print("  ERROR: street_facilities table does not exist!")
        conn.close()
        return
    
    # Check if community column exists, add if not
    cur.execute("PRAGMA table_info(street_facilities)")
    columns = [row[1] for row in cur.fetchall()]
    
    if 'community' not in columns:
        print("  Adding community column to street_facilities table...")
        cur.execute("ALTER TABLE street_facilities ADD COLUMN community INTEGER DEFAULT 0")
        conn.commit()
    else:
        print("  Community column already exists")
    
    # Get all streets with coordinates
    print("\n[3/4] Fetching streets from database...")
    cur.execute("""
        SELECT street_name, latitude, longitude 
        FROM street_locations 
        WHERE status = 'found' AND latitude IS NOT NULL AND longitude IS NOT NULL
    """)
    streets = cur.fetchall()
    print(f"  Found {len(streets)} streets to process")
    
    if len(streets) == 0:
        print("  No streets found to process!")
        conn.close()
        return
    
    # Process each street
    print("\n[4/4] Counting community centres for each street...")
    updated_count = 0
    skipped_count = 0
    
    for idx, (street_name, street_lat, street_lon) in enumerate(streets, 1):
        try:
            # Count community centres within 1km
            community_count = 0
            for cc in community_centres:
                try:
                    cc_lat = float(cc.latitude) if cc.latitude else 0
                    cc_lon = float(cc.longitude) if cc.longitude else 0
                    
                    if cc_lat and cc_lon:
                        distance = haversine(street_lat, street_lon, cc_lat, cc_lon)
                        if distance <= 1.0:  # Within 1km
                            community_count += 1
                except (ValueError, TypeError, AttributeError):
                    continue
            
            # Update or insert into street_facilities
            cur.execute("""
                INSERT INTO street_facilities (street_name, community, schools, sports, hawkers, healthcare, greenSpaces, carparks, transit)
                VALUES (?, ?, 0, 0, 0, 0, 0, 0, 0)
                ON CONFLICT(street_name) DO UPDATE SET community = excluded.community
            """, (street_name, community_count))
            
            updated_count += 1
            
            # Progress indicator
            if idx % 50 == 0 or idx == len(streets):
                print(f"  Progress: {idx}/{len(streets)} streets processed ({updated_count} updated)")
                
        except Exception as e:
            print(f"  ERROR processing {street_name}: {e}")
            skipped_count += 1
            continue
    
    # Commit changes
    conn.commit()
    
    # Show statistics
    print("\n" + "=" * 60)
    print("POPULATION COMPLETE")
    print("=" * 60)
    print(f"Total streets processed: {len(streets)}")
    print(f"Successfully updated: {updated_count}")
    print(f"Skipped (errors): {skipped_count}")
    
    # Show sample results
    print("\n" + "-" * 60)
    print("SAMPLE RESULTS (Top 10 streets by community centres)")
    print("-" * 60)
    cur.execute("""
        SELECT sl.street_name, sl.latitude, sl.longitude, sf.community
        FROM street_locations sl
        JOIN street_facilities sf ON sl.street_name = sf.street_name
        WHERE sf.community > 0
        ORDER BY sf.community DESC
        LIMIT 10
    """)
    
    results = cur.fetchall()
    if results:
        for street_name, lat, lon, count in results:
            print(f"  {street_name}: {count} community centres")
    else:
        print("  No streets with community centres found")
    
    # Show distribution
    print("\n" + "-" * 60)
    print("DISTRIBUTION OF COMMUNITY CENTRES")
    print("-" * 60)
    cur.execute("""
        SELECT 
            CASE 
                WHEN community = 0 THEN '0'
                WHEN community = 1 THEN '1'
                WHEN community = 2 THEN '2'
                WHEN community = 3 THEN '3'
                WHEN community >= 4 THEN '4+'
            END as range,
            COUNT(*) as count
        FROM street_facilities
        GROUP BY range
        ORDER BY range
    """)
    
    distribution = cur.fetchall()
    for range_label, count in distribution:
        print(f"  {range_label} community centres: {count} streets")
    
    conn.close()
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == '__main__':
    main()
