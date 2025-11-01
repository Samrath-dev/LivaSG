import sqlite3
from pathlib import Path

# Extract unique street names from hdb_streets
db_path = Path(__file__).parent.parent / "postal_codes.db"
output_path = Path(__file__).parent.parent / "unique_streets.txt"

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

streets = cursor.execute("""
    SELECT DISTINCT street 
    FROM hdb_streets 
    WHERE street != '' 
    ORDER BY street
""").fetchall()

conn.close()

# Write to text file
street_names = [row[0] for row in streets]
output_path.write_text('\n'.join(street_names), encoding='utf-8')

print(f"✓ Extracted {len(street_names):,} unique street names")
print(f"✓ Saved to: {output_path}")
