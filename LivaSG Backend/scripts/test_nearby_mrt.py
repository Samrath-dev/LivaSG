import os, sqlite3

# Small test: print planning areas with transit > 0 from planning_cache.db
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
db_path = os.path.join(base_dir, 'planning_cache.db')

if not os.path.exists(db_path):
    print('planning_cache.db not found at', db_path)
    raise SystemExit(1)

conn = sqlite3.connect(db_path)
cur = conn.cursor()
try:
    rows = cur.execute(
        "SELECT area_name, transit, schools, carparks FROM planning_area_facilities WHERE transit > 0 ORDER BY transit DESC LIMIT 20"
    ).fetchall()
    if not rows:
        print('No planning areas with transit > 0 found in planning_area_facilities')
    else:
        print('Sample planning areas with transit counts:')
        for area, transit, schools, carparks in rows:
            print(f"- {area}: transit={transit}, schools={schools}, carparks={carparks}")
finally:
    conn.close()
