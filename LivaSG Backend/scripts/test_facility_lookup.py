"""
Simple test to verify facility data enrichment works
"""

import sqlite3
from pathlib import Path

base_dir = Path(__file__).parent.parent
street_db_path = base_dir / 'street_geocode.db'

print("🧪 Testing Facility Data Lookup")
print("=" * 80)

if not street_db_path.exists():
    print(f"❌ Database not found: {street_db_path}")
    exit(1)

conn = sqlite3.connect(street_db_path)
cursor = conn.cursor()

# Test 1: Query facilities for a known street
test_streets = ["TAMPINES ST 82", "SAGO LANE", "ANG MO KIO ST 31"]

for street_name in test_streets:
    row = cursor.execute("""
        SELECT schools, sports, hawkers, healthcare, greenSpaces, carparks
        FROM street_facilities
        WHERE street_name = ?
    """, (street_name,)).fetchone()
    
    if row:
        schools, sports, hawkers, healthcare, parks, carparks = row
        print(f"\n✓ {street_name}:")
        print(f"  Schools: {schools}, Sports: {sports}, Hawkers: {hawkers}")
        print(f"  Healthcare: {healthcare}, Parks: {parks}, Carparks: {carparks}")
        
        # Build facility list like in the actual code
        facility_list = []
        if schools > 0:
            facility_list.append(f"{schools} Schools")
        if sports > 0:
            facility_list.append(f"{sports} Sports Facilities")
        if hawkers > 0:
            facility_list.append(f"{hawkers} Hawker Centres")
        if healthcare > 0:
            facility_list.append(f"{healthcare} Healthcare")
        if parks > 0:
            facility_list.append(f"{parks} Parks")
        if carparks > 0:
            facility_list.append(f"{carparks} Carparks")
        
        print(f"  Facility List: {', '.join(facility_list)}")
    else:
        print(f"\n✗ {street_name}: NOT FOUND in street_facilities table")

# Test 2: Check facility filtering logic
print("\n" + "=" * 80)
print("Testing Facility Filter Logic:")
print("=" * 80)

facility_filter_map = {
    'good schools': 'schools',
    'schools': 'schools',
    'healthcare': 'healthcare',
    'parks': 'greenSpaces',
}

test_filters = ["Good Schools", "Healthcare", "Parks"]
test_street = "TAMPINES ST 82"

row = cursor.execute("""
    SELECT schools, sports, hawkers, healthcare, greenSpaces, carparks
    FROM street_facilities
    WHERE street_name = ?
""", (test_street,)).fetchone()

if row:
    schools, sports, hawkers, healthcare, parks, carparks = row
    facility_counts = {
        'schools': schools,
        'sports': sports,
        'hawkers': hawkers,
        'healthcare': healthcare,
        'greenSpaces': parks,
        'carparks': carparks
    }
    
    print(f"\nTest street: {test_street}")
    print(f"Facility counts: {facility_counts}")
    
    for filter_name in test_filters:
        filter_key = filter_name.lower()
        db_column = facility_filter_map.get(filter_key)
        if db_column:
            count = facility_counts.get(db_column, 0)
            match = "✓ MATCH" if count > 0 else "✗ NO MATCH"
            print(f"  {filter_name}: {match} (count: {count})")

conn.close()

print("\n✅ Test complete!")
