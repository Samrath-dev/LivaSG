import sqlite3
from pathlib import Path

db_path = Path(__file__).parent.parent / "street_geocode.db"
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

not_found = cursor.execute("""
    SELECT street_name 
    FROM street_locations 
    WHERE status = 'not_found' 
    ORDER BY street_name
""").fetchall()

conn.close()

print(f"Streets not found: {len(not_found)}")
for row in not_found:
    print(f"  - {row[0]}")
