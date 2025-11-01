"""
Add Transit Column and Populate Data
=====================================
This script:
1. Adds a 'transit' column to the street_facilities table
2. Populates transit counts for all streets based on proximity to MRT/LRT stations
3. Uses the transit repository to get all transit nodes
"""

import sqlite3
import os
import sys
import asyncio
import math

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

async def load_transit_nodes():
    """Load transit nodes from the rating engine"""
    try:
        # Try to import and use the rating engine's transit data
        from app.repositories.memory_impl import MemoryTransitRepo
        
        # Initialize the transit repository (ensures MRT/LRT + bus stops via BUS_STOPS_CSV_PATH)
        try:
            await MemoryTransitRepo.initialize()
        except Exception:
            pass
        transit_repo = MemoryTransitRepo()
        nodes = transit_repo.all()
        
        print(f"Loaded {len(nodes)} transit nodes from MemoryTransitRepo")
        
        # Convert to simple dict format
        transit_list = []
        for n in nodes:
            if n.latitude is not None and n.longitude is not None:
                transit_list.append({
                    'id': n.id,
                    'name': n.name,
                    'type': n.type,
                    'latitude': float(n.latitude),
                    'longitude': float(n.longitude)
                })
        
        print(f"Valid transit nodes with coordinates: {len(transit_list)}")
        return transit_list
    except Exception as e:
        print(f"Error loading transit nodes: {e}")
        return []

def count_transit_near(lat: float, lon: float, transit_nodes: list, radius_km: float = 1.0) -> int:
    """Count transit stations within radius_km of the given point"""
    count = 0
    for node in transit_nodes:
        try:
            distance = haversine(lat, lon, node['latitude'], node['longitude'])
            if distance <= radius_km:
                count += 1
        except Exception:
            continue
    return count

async def add_transit_column_and_populate():
    """Main function to add transit column and populate data"""
    print("=" * 80)
    print("Adding Transit Column and Populating Data")
    print("=" * 80)
    print()
    
    # Connect to database
    db_path = 'street_geocode.db'
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if transit column already exists
    schema = cursor.execute('PRAGMA table_info(street_facilities)').fetchall()
    column_names = [col[1] for col in schema]
    
    if 'transit' in column_names:
        # Avoid Unicode checkmarks for Windows consoles
        print("Transit column already exists in street_facilities table")
    else:
        print("Adding transit column to street_facilities table...")
        try:
            cursor.execute('ALTER TABLE street_facilities ADD COLUMN transit INTEGER DEFAULT 0')
            conn.commit()
            print("Transit column added successfully")
        except Exception as e:
            print(f"Error adding transit column: {e}")
            conn.close()
            return
    
    print()
    
    # Load transit nodes
    print("Loading transit nodes...")
    transit_nodes = await load_transit_nodes()
    
    if not transit_nodes:
        print("Warning: No transit nodes loaded. Transit counts will be 0.")
    
    print()
    
    # Get all streets with coordinates
    all_streets = cursor.execute(
        "SELECT street_name, latitude, longitude FROM street_locations WHERE status = 'found' AND latitude IS NOT NULL AND longitude IS NOT NULL"
    ).fetchall()
    
    print(f"Found {len(all_streets)} streets in database")
    print()
    
    # Update transit counts for all streets
    print("Updating transit counts...")
    print("-" * 80)
    
    updated = 0
    errors = 0
    
    for idx, (street_name, lat, lon) in enumerate(all_streets, start=1):
        try:
            # Count transit stations within 1km
            transit_count = count_transit_near(float(lat), float(lon), transit_nodes, radius_km=1.0)
            
            # Update the transit column
            cursor.execute(
                "UPDATE street_facilities SET transit = ? WHERE street_name = ?",
                (transit_count, street_name)
            )
            updated += 1
            
            # Progress indicator
            if idx % 50 == 0 or idx == len(all_streets):
                print(f"Progress: {idx}/{len(all_streets)} streets processed")
                
        except Exception as e:
            errors += 1
            print(f"Error processing {street_name}: {e}")
    
    # Commit changes
    conn.commit()
    
    # Verify the changes
    print()
    print("Verifying changes...")
    stats = cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN transit > 0 THEN 1 ELSE 0 END) as with_transit,
            AVG(transit) as avg_transit,
            MAX(transit) as max_transit
        FROM street_facilities
    """).fetchone()
    
    conn.close()
    
    print("-" * 80)
    print()
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"Total streets processed: {len(all_streets)}")
    print(f"Records updated: {updated}")
    print(f"Errors encountered: {errors}")
    print()
    print(f"Statistics:")
    print(f"  - Total facility records: {stats[0]}")
    print(f"  - Streets with transit nearby: {stats[1]}")
    print(f"  - Average transit count: {stats[2]:.2f}")
    print(f"  - Max transit count: {stats[3]}")
    print()
    print("Transit column addition and population complete!")
    print()

if __name__ == "__main__":
    asyncio.run(add_transit_column_and_populate())
