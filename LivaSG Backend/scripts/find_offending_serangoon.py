"""
Find facility rows in planning_cache.db that are considered inside the 'Serangoon' polygon
but whose computed area (via MemoryAreaRepo.getArea) is not Serangoon.

This helps identify wrongly-assigned facilities to Serangoon. The script only reports them.
Run:
  python scripts/find_offending_serangoon.py
"""
from __future__ import annotations
import os, sqlite3, json
import sys
import pathlib

# Ensure project root is on sys.path so `import app` works when running this script
# Find nearest ancestor that contains the `app` package (so imports like `import app...` work)
p = pathlib.Path(__file__).resolve()
PROJECT_ROOT = None
for ancestor in p.parents:
    if (ancestor / 'app').exists():
        PROJECT_ROOT = str(ancestor)
        break
if PROJECT_ROOT is None:
    # fallback to two levels up (best-effort)
    PROJECT_ROOT = str(pathlib.Path(__file__).resolve().parents[1])

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.repositories.memory_impl import MemoryAreaRepo

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DB_PATH = os.path.join(BASE_DIR, 'planning_cache.db')
TARGET = 'Serangoon'

TABLES = [
    ('schools_locations', ['name','latitude','longitude']),
    ('sports_locations', ['name','latitude','longitude']),
    ('hawkers_locations', ['name','latitude','longitude']),
    ('clinics_locations', ['name','latitude','longitude']),
    ('parks_locations', ['name','latitude','longitude']),
    ('carparks_locations', ['id','name','latitude','longitude']),
    ('transit_nodes', ['id','name','type','latitude','longitude']),
]

def point_in_polygon(lon, lat, polygon):
    num = len(polygon)
    j = num - 1
    inside = False
    for i in range(num):
        lon_i, lat_i = polygon[i][0], polygon[i][1]
        lon_j, lat_j = polygon[j][0], polygon[j][1]
        if ((lat_i > lat) != (lat_j > lat)) and (lon < (lon_j - lon_i) * (lat - lat_i) / (lat_j - lat_i + 1e-12) + lon_i):
            inside = not inside
        j = i
    return inside

def point_in_geojson(geojson, lat, lon):
    if not geojson:
        return False
    gtype = geojson.get('type')
    if gtype == 'MultiPolygon':
        for polygon_group in geojson.get('coordinates', []):
            for ring in polygon_group:
                if point_in_polygon(lon, lat, ring):
                    return True
    elif gtype == 'Polygon':
        for ring in geojson.get('coordinates', []):
            if point_in_polygon(lon, lat, ring):
                return True
    return False


def main():
    if not os.path.exists(DB_PATH):
        print('planning_cache.db not found at', DB_PATH)
        return
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    row = cur.execute("SELECT geojson FROM planning_area_polygons WHERE area_name = ? LIMIT 1", (TARGET,)).fetchone()
    if not row or not row[0]:
        print('No polygon found for', TARGET)
        return
    polygon_geojson = json.loads(row[0])

    offenders = []
    reverse_offenders = []
    area_repo = MemoryAreaRepo()

    for tbl, cols in TABLES:
        # Check table exists
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (tbl,))
        if not cur.fetchone():
            continue
        # Build select
        sel = ','.join(cols)
        rows = cur.execute(f"SELECT {sel} FROM {tbl}").fetchall()
        for r in rows:
            try:
                # Extract latitude and longitude based on last columns
                lat = float(r[-2])
                lon = float(r[-1])
            except Exception:
                continue
            # If polygon contains the point according to stored geojson
            in_db_polygon = point_in_geojson(polygon_geojson, lat, lon)
            # Compute area via MemoryAreaRepo
            detected = area_repo.getArea(lon, lat)
            if in_db_polygon and detected and detected.lower() != TARGET.lower():
                offenders.append((tbl, cols, r, detected))
            # Also check the reverse: MemoryAreaRepo says it's Serangoon but DB polygon doesn't contain it
            if (detected and detected.lower() == TARGET.lower()) and not in_db_polygon:
                reverse_offenders.append((tbl, cols, r, detected))
    conn.close()

    if not offenders:
        print('No offending rows found for', TARGET)
        return
    print(f'Found {len(offenders)} rows inside DB polygon but assigned elsewhere by MemoryAreaRepo for {TARGET}:')
    for tbl, cols, row, detected in offenders:
        print('\nTable:', tbl)
        info = {cols[i]: row[i] for i in range(min(len(cols), len(row)))}
        print(' Row:', info)
        print(' Detected area (MemoryAreaRepo.getArea):', detected)

    if reverse_offenders:
        print('\nAdditionally found {0} rows assigned to {1} by MemoryAreaRepo but NOT inside the DB polygon:'.format(len(reverse_offenders), TARGET))
        for tbl, cols, row, detected in reverse_offenders:
            print('\nTable:', tbl)
            info = {cols[i]: row[i] for i in range(min(len(cols), len(row)))}
            print(' Row:', info)
            print(' Detected area (MemoryAreaRepo.getArea):', detected)

if __name__ == '__main__':
    main()
