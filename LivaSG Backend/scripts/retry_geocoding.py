"""
Retry geocoding for streets that weren't found, trying alternative search terms
"""

import asyncio
import json
import sqlite3
import sys
from pathlib import Path

# Import OneMap client
script_dir = Path(__file__).resolve().parent
backend_dir = script_dir.parent
sys.path.insert(0, str(backend_dir))

from app.integrations.onemap_client import OneMapClientHardcoded


# Alternative search patterns for problematic streets
SEARCH_ALTERNATIVES = {
    "JLN": ["JALAN", "JLN"],
    "ST": ["STREET", "ST"],
    "AVE": ["AVENUE", "AVE"],
    "CTRL": ["CENTRAL", "CTRL"],
}


async def retry_street(client, street_name: str, original_name: str):
    """Try multiple search variations for a street"""
    
    # Try original first
    print(f"\n🔍 Retrying: {original_name}")
    print(f"   Original query: '{street_name}'")
    
    result = await client.search(street_name, page=1)
    if result and result.get('results'):
        print(f"   ✓ Found {len(result['results'])} result(s) with original query!")
        return result['results']
    
    # Try with expanded abbreviations
    modified = street_name
    for abbrev, expansions in SEARCH_ALTERNATIVES.items():
        if abbrev in street_name.split():
            for expansion in expansions:
                if expansion == abbrev:
                    continue
                test_query = street_name.replace(abbrev, expansion)
                print(f"   Trying: '{test_query}'")
                result = await client.search(test_query, page=1)
                if result and result.get('results'):
                    print(f"   ✓ Found {len(result['results'])} result(s)!")
                    return result['results']
    
    # Try with "SINGAPORE" appended
    test_query = f"{street_name} SINGAPORE"
    print(f"   Trying: '{test_query}'")
    result = await client.search(test_query, page=1)
    if result and result.get('results'):
        print(f"   ✓ Found {len(result['results'])} result(s) with Singapore!")
        return result['results']
    
    # Try just the street base without numbers/suffixes
    words = street_name.split()
    if len(words) > 2 and (words[-1].isdigit() or words[-2] in ['ST', 'AVE', 'CTRL']):
        base = ' '.join(words[:-2] if words[-2] in ['ST', 'AVE', 'CTRL'] else words[:-1])
        test_query = base
        print(f"   Trying base: '{test_query}'")
        result = await client.search(test_query, page=1)
        if result and result.get('results'):
            print(f"   ✓ Found {len(result['results'])} result(s) with base name!")
            return result['results']
    
    print(f"   ✗ No results found after all attempts")
    return None


async def main():
    db_path = Path(__file__).resolve().parent.parent / "street_geocode.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Get not found streets
    not_found = cursor.execute("""
        SELECT street_name 
        FROM street_locations 
        WHERE status = 'not_found' 
        ORDER BY street_name
    """).fetchall()
    
    if not not_found:
        print("✓ All streets already found!")
        conn.close()
        return
    
    print(f"📋 Retrying {len(not_found)} streets with alternative search patterns")
    
    client = OneMapClientHardcoded()
    found_count = 0
    
    for row in not_found:
        street_name = row[0]
        
        results = await retry_street(client, street_name, street_name)
        
        if results:
            found_count += 1
            # Update database with results
            best = results[0]
            cursor.execute("""
                UPDATE street_locations
                SET result_count = ?,
                    best_result_json = ?,
                    latitude = ?,
                    longitude = ?,
                    address = ?,
                    building = ?,
                    postal_code = ?,
                    status = 'found',
                    searched_at = CURRENT_TIMESTAMP
                WHERE street_name = ?
            """, (
                len(results),
                json.dumps(best),
                float(best.get('LATITUDE', 0)) if best.get('LATITUDE') else None,
                float(best.get('LONGITUDE', 0)) if best.get('LONGITUDE') else None,
                best.get('ADDRESS'),
                best.get('BUILDING'),
                best.get('POSTAL'),
                street_name,
            ))
            
            # Save all results
            cursor.execute("DELETE FROM street_all_results WHERE street_name = ?", (street_name,))
            for idx, result in enumerate(results):
                cursor.execute("""
                    INSERT INTO street_all_results
                    (street_name, result_index, latitude, longitude, address, building, postal_code, result_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    street_name,
                    idx,
                    float(result.get('LATITUDE', 0)) if result.get('LATITUDE') else None,
                    float(result.get('LONGITUDE', 0)) if result.get('LONGITUDE') else None,
                    result.get('ADDRESS'),
                    result.get('BUILDING'),
                    result.get('POSTAL'),
                    json.dumps(result),
                ))
            
            conn.commit()
        
        await asyncio.sleep(0.1)  # Rate limiting
    
    conn.close()
    
    print(f"\n📊 Results:")
    print(f"   Successfully found: {found_count}/{len(not_found)}")
    print(f"   Still missing: {len(not_found) - found_count}")


if __name__ == "__main__":
    asyncio.run(main())
