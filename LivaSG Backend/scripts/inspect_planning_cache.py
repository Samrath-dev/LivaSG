#!/usr/bin/env python3
import os, sqlite3, json

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
db_path = os.path.join(base_dir, 'planning_cache.db')
print('DB path:', db_path)
if not os.path.exists(db_path):
    print('planning_cache.db not found')
    raise SystemExit(1)

con = sqlite3.connect(db_path)
cur = con.cursor()

print('\nTables:')
rows = cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
tables = [r[0] for r in rows]
for t in tables:
    print(' -', t)

# Helper to get columns
def get_columns(table):
    return [c[1] for c in cur.execute(f"PRAGMA table_info('{table}')").fetchall()]

print('\nTable schemas and lat/lon availability:')
for t in tables:
    cols = get_columns(t)
    has_lat = any('lat' in c.lower() for c in cols)
    has_lon = any('lon' in c.lower() for c in cols) or any('lng' in c.lower() for c in cols)
    print(f"\nTable: {t}\n Columns: {cols}\n Has lat: {has_lat}, Has lon: {has_lon}")
    if has_lat and has_lon:
        # find likely latitude/longitude column names
        lat_cols = [c for c in cols if 'lat' in c.lower()]
        lon_cols = [c for c in cols if 'lon' in c.lower() or 'lng' in c.lower()]
        lat_col = lat_cols[0]
        lon_col = lon_cols[0]
        try:
            total = cur.execute(f"SELECT COUNT(*) FROM '{t}'").fetchone()[0]
            nonnull = cur.execute(f"SELECT COUNT(*) FROM '{t}' WHERE {lat_col} IS NOT NULL AND {lon_col} IS NOT NULL").fetchone()[0]
            print(f"  rows: {total}, rows with non-null lat/lon: {nonnull}")
            sample = cur.execute(f"SELECT * FROM '{t}' LIMIT 5").fetchall()
            print('  sample rows (up to 5):')
            for s in sample:
                print('   ', s)
        except Exception as e:
            print('  could not query rows:', e)

# Inspect planning_area_facilities specifically
if 'planning_area_facilities' in tables:
    print('\nplanning_area_facilities columns:', get_columns('planning_area_facilities'))
    rows = cur.execute("SELECT area_name, schools, sports, hawkers, healthcare, greenSpaces, carparks, transit FROM planning_area_facilities LIMIT 10").fetchall()
    print('Sample planning_area_facilities rows:')
    for r in rows:
        print(' ', r)

# Inspect planning_area_polygons
if 'planning_area_polygons' in tables:
    print('\nplanning_area_polygons columns:', get_columns('planning_area_polygons'))
    # show one sample geojson length
    row = cur.execute("SELECT area_name, LENGTH(geojson) FROM planning_area_polygons LIMIT 5").fetchall()
    for r in row:
        print(' ', r)

con.close()
print('\nDone')
