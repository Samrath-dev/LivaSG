import sqlite3
import os
import sys

# Path to planning_cache.db (adjust if your project is elsewhere)
DB = r"c:\NTU\Y2.1\SC2006\Project stuff\Code\2006-SCS3-06\LivaSG Backend\planning_cache.db"

print('Checking DB at:', DB)
if not os.path.exists(DB):
    print('MISSING_DB', DB)
    sys.exit(0)

conn = sqlite3.connect(DB)
cur = conn.cursor()

# Verify table exists
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='planning_area_facilities'")
if not cur.fetchone():
    print('MISSING_TABLE planning_area_facilities')
    conn.close()
    sys.exit(0)

areas = ['Jurong East', 'Tuas']
for area in areas:
    row = cur.execute(
        'SELECT area_name, schools, sports, hawkers, healthcare, greenSpaces, carparks, transit FROM planning_area_facilities WHERE area_name = ?',
        (area,)
    ).fetchone()
    print('AREA:', area, '=>', row)

conn.close()
print('Done')
