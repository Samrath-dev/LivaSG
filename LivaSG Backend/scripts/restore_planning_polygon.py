"""
Restore a planning-area polygon (e.g., Serangoon) into planning_cache.db by fetching from OneMapClientHardcoded.

Usage:
  python scripts/restore_planning_polygon.py --name Serangoon

This will insert into planning_area_polygons(year, area_name, geojson, centroid_lat, centroid_lon)
if the area is found from the OneMap client.
"""
from __future__ import annotations
import argparse
import os
import sqlite3
import json
import sys
import pathlib

# Find repo root so imports work
p = pathlib.Path(__file__).resolve()
PROJECT_ROOT = None
for ancestor in p.parents:
    if (ancestor / 'app').exists():
        PROJECT_ROOT = str(ancestor)
        break
if PROJECT_ROOT and PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.integrations.onemap_client import OneMapClientHardcoded

BASE_DIR = str(p.parent.parent.resolve())
DB_PATH = os.path.join(BASE_DIR, 'planning_cache.db')
YEAR = 2019


def compute_centroid_from_geojson(geojson: dict):
    coords = []
    if geojson.get('type') == 'MultiPolygon':
        for polygon in geojson.get('coordinates', []):
            for ring in polygon:
                coords.extend(ring)
    elif geojson.get('type') == 'Polygon':
        for ring in geojson.get('coordinates', []):
            coords.extend(ring)
    if not coords:
        return None
    avg_lon = sum(c[0] for c in coords) / len(coords)
    avg_lat = sum(c[1] for c in coords) / len(coords)
    return (avg_lat, avg_lon)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', required=True, help='Area name (e.g., Serangoon)')
    args = parser.parse_args()
    target = args.name.title()

    print('Fetching planning areas from OneMap client...')
    client = OneMapClientHardcoded()
    try:
        pa = client.planning_areas(YEAR)
    except Exception as e:
        print('Error calling OneMap client:', e)
        return

    # pa may be a coroutine if client is async; handle both
    if hasattr(pa, '__await__'):
        import asyncio
        pa = asyncio.run(pa)

    found = None
    for area in pa.get('SearchResults', []):
        name = area.get('pln_area_n', '').title()
        if name == target:
            found = area
            break

    if not found:
        print(f'Area {target} not found in OneMap results')
        return

    geojson_str = found.get('geojson', '{}')
    try:
        geojson = json.loads(geojson_str)
    except Exception:
        geojson = {}

    centroid = compute_centroid_from_geojson(geojson)
    if centroid is None:
        print('Could not compute centroid for', target)
        return

    # Insert into planning_cache.db
    if not os.path.exists(DB_PATH):
        print('DB not found at', DB_PATH)
        return

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS planning_area_polygons (
                year INTEGER NOT NULL,
                area_name TEXT NOT NULL,
                geojson TEXT NOT NULL,
                centroid_lat REAL NOT NULL,
                centroid_lon REAL NOT NULL,
                PRIMARY KEY(year, area_name)
            )"""
        )
        conn.execute(
            "INSERT OR REPLACE INTO planning_area_polygons(year, area_name, geojson, centroid_lat, centroid_lon) VALUES (?, ?, ?, ?, ?)",
            (YEAR, target, json.dumps(geojson), centroid[0], centroid[1]),
        )
        conn.commit()
        print(f'Inserted polygon for {target} into planning_cache.db (year={YEAR})')
    finally:
        conn.close()

if __name__ == '__main__':
    main()
