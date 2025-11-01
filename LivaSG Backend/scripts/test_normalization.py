"""Quick test of street name normalization"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

def normalize_street_name(name):
    """Normalize street name by handling abbreviations"""
    if not name:
        return ""
    normalized = name.upper().strip()
    # Handle common abbreviations
    normalized = normalized.replace('AVENUE', 'AVE')
    normalized = normalized.replace('CENTRAL', 'CTRL')
    normalized = normalized.replace('STREET', 'ST')
    normalized = normalized.replace('ROAD', 'RD')
    normalized = normalized.replace('DRIVE', 'DR')
    normalized = normalized.replace('CRESCENT', 'CRES')
    normalized = normalized.replace('NORTH', 'NTH')
    normalized = normalized.replace('SOUTH', 'STH')
    normalized = normalized.replace('EAST', 'E')
    normalized = normalized.replace('WEST', 'W')
    # Remove extra spaces
    normalized = ' '.join(normalized.split())
    return normalized

# Test cases
test_cases = [
    ("TAMPINES AVENUE 7", "TAMPINES AVE 7"),
    ("TAMPINES CENTRAL 1", "TAMPINES CTRL 1"),
    ("ANG MO KIO STREET 31", "ANG MO KIO ST 31"),
    ("BUKIT BATOK CENTRAL", "BUKIT BATOK CTRL"),
]

print("Testing street name normalization:")
print("=" * 80)
for original, expected in test_cases:
    normalized = normalize_street_name(original)
    match = "✓" if normalized == expected else "✗"
    print(f"{match} '{original}' -> '{normalized}' (expected: '{expected}')")

# Test with database
import sqlite3
import os

base_dir = Path(__file__).parent.parent
street_db_path = base_dir / 'street_geocode.db'

if street_db_path.exists():
    print("\n" + "=" * 80)
    print("Testing with actual database:")
    print("=" * 80)
    
    conn = sqlite3.connect(street_db_path)
    cursor = conn.cursor()
    
    # Get sample streets from database
    rows = cursor.execute("""
        SELECT street_name FROM street_locations 
        WHERE street_name LIKE '%TAMPINES%' 
        LIMIT 5
    """).fetchall()
    
    print("\nDatabase streets (normalized):")
    for (street,) in rows:
        print(f"  {street} -> {normalize_street_name(street)}")
    
    # Test OneMap-style names
    onemap_names = [
        "TAMPINES AVENUE 7",
        "TAMPINES CENTRAL 1", 
        "TAMPINES STREET 82"
    ]
    
    print("\nOneMap names (normalized):")
    for name in onemap_names:
        normalized = normalize_street_name(name)
        # Check if it exists in database
        result = cursor.execute("""
            SELECT street_name, latitude, longitude 
            FROM street_locations 
            WHERE street_name = ?
        """, (normalized,)).fetchone()
        
        if result:
            print(f"  ✓ {name} -> {normalized} (FOUND in DB: {result[1]:.6f}, {result[2]:.6f})")
        else:
            print(f"  ✗ {name} -> {normalized} (NOT FOUND)")
    
    conn.close()
else:
    print(f"\n❌ Database not found: {street_db_path}")

print("\n✅ Test complete!")
