import sqlite3

conn = sqlite3.connect('street_geocode.db')
cursor = conn.cursor()

print("street_locations schema:")
schema = cursor.execute('PRAGMA table_info(street_locations)').fetchall()
for col in schema:
    print(f"  {col[1]} ({col[2]})")

print("\nstreet_facilities schema:")
schema = cursor.execute('PRAGMA table_info(street_facilities)').fetchall()
for col in schema:
    print(f"  {col[1]} ({col[2]})")

print("\nstreet_scores schema:")
schema = cursor.execute('PRAGMA table_info(street_scores)').fetchall()
for col in schema:
    print(f"  {col[1]} ({col[2]})")

conn.close()
