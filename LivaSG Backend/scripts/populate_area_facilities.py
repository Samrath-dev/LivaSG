"""
Populate planning area facilities for all URA planning areas (≈55 areas).

What it does
- Loads planning area polygons/centroids (MemoryAreaRepo)
- Loads amenity datasets (schools, sports, hawkers, healthcare, parks)
- Loads carparks and transit repositories
- Counts facilities per planning area using polygon containment (not radius-only)
- Saves results into a SQLite table planning_area_facilities

Usage (Windows PowerShell):
  python populate_area_facilities.py                # defaults to planning_cache.db
  python populate_area_facilities.py --db street_geocode.db

Notes
- This script may download datasets on first run (cached afterwards).
- If you prefer only centroid-based counts (radius), adjust the counter logic below.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sqlite3
from datetime import datetime
from typing import Dict
import sys
import pathlib

# Ensure `app` package is importable when running the script directly
p = pathlib.Path(__file__).resolve()
PROJECT_ROOT = None
for ancestor in p.parents:
    if (ancestor / 'app').exists():
        PROJECT_ROOT = str(ancestor)
        break
if PROJECT_ROOT and PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Ensure we can import app.* modules when running as a script
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "."))

from app.repositories.memory_impl import (
    MemoryAmenityRepo,
    MemoryAreaRepo,
    MemoryCarparkRepo,
    MemoryTransitRepo,
    MemoryCommunityRepo,
)


def ensure_table(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS planning_area_facilities (
            area_name   TEXT PRIMARY KEY,
            schools     INTEGER NOT NULL,
            sports      INTEGER NOT NULL,
            hawkers     INTEGER NOT NULL,
            healthcare  INTEGER NOT NULL,
            greenSpaces INTEGER NOT NULL,
            carparks    INTEGER NOT NULL,
            transit     INTEGER NOT NULL,
            community   INTEGER NOT NULL DEFAULT 0,
            calculated_at TEXT DEFAULT (datetime('now'))
        )
        """
    )
    conn.commit()


def count_facilities_for_area(area_name: str) -> Dict[str, int]:
    # Geometry for the planning area
    polygon, centroid = MemoryAreaRepo.getAreaGeometry(area_name)

    # Amenity counts by polygon containment
    schools = len(MemoryAmenityRepo.filterInside(polygon, MemoryAmenityRepo._schools_data))
    sports = len(MemoryAmenityRepo.filterInside(polygon, MemoryAmenityRepo._sports_data))
    hawkers = len(MemoryAmenityRepo.filterInside(polygon, MemoryAmenityRepo._hawkers_data))
    healthcare = len(MemoryAmenityRepo.filterInside(polygon, MemoryAmenityRepo._clinics_data))
    greenSpaces = len(MemoryAmenityRepo.filterInside(polygon, MemoryAmenityRepo._parks_data))

    # Carparks and transit by area membership
    # Instead of relying on areaId inference, test each feature's lat/lon against the polygon
    carparks = 0
    try:
        cp_repo = MemoryCarparkRepo()
        cps = cp_repo.list_all()
        from shapely.geometry import Point
        for cp in cps:
            try:
                lat = float(getattr(cp, 'latitude', None))
                lon = float(getattr(cp, 'longitude', None))
                if polygon is not None and polygon.contains(Point(lon, lat)):
                    carparks += 1
            except Exception:
                continue
    except Exception:
        carparks = len(MemoryCarparkRepo().list_near_area(area_name))

    transit = 0
    try:
        t_repo = MemoryTransitRepo()
        nodes = t_repo.all()
        from shapely.geometry import Point
        for n in nodes:
            try:
                lat = float(getattr(n, 'latitude', None))
                lon = float(getattr(n, 'longitude', None))
                if polygon is not None and polygon.contains(Point(lon, lat)):
                    transit += 1
            except Exception:
                continue
    except Exception:
        transit = len(MemoryTransitRepo().list_near_area(area_name))

    community = 0
    try:
        cc_repo = MemoryCommunityRepo()
        centres = cc_repo._centres
        from shapely.geometry import Point
        for c in centres:
            try:
                lat = float(getattr(c, 'latitude', None))
                lon = float(getattr(c, 'longitude', None))
                if polygon is not None and polygon.contains(Point(lon, lat)):
                    community += 1
            except Exception:
                continue
    except Exception:
        community = len(MemoryCommunityRepo().list_near_area(area_name))

    return {
        "schools": schools,
        "sports": sports,
        "hawkers": hawkers,
        "healthcare": healthcare,
        "greenSpaces": greenSpaces,
        "carparks": carparks,
        "transit": transit,
        "community": community,
    }


async def main():
    parser = argparse.ArgumentParser(description="Populate planning_area_facilities table")
    parser.add_argument(
        "--db",
        dest="db_name",
        default="planning_cache.db",
        help="Target SQLite DB filename (planning_cache.db or street_geocode.db)",
    )
    args = parser.parse_args()

    db_path = os.path.join(PROJECT_ROOT, args.db_name)

    # Initialize repos (may fetch/cache datasets)
    print("Initializing datasets (this may take a few minutes on first run)…")
    await MemoryAmenityRepo.initialize()
    await MemoryTransitRepo.initialize()
    # Area and carpark repos load synchronously
    _ = MemoryAreaRepo()      # ensures polygons/centroids loaded
    _ = MemoryCarparkRepo()   # ensures carparks loaded/cached
    _ = MemoryCommunityRepo() # ensures community centres loaded/cached

    # Get planning areas
    areas = [c.areaId for c in MemoryAreaRepo.list_all()]
    areas = sorted({a for a in areas if a and a != "None"})
    print(f"Discovered {len(areas)} planning areas")

    # Connect DB and ensure table
    conn = sqlite3.connect(db_path)
    ensure_table(conn)

    cur = conn.cursor()
    inserted = 0
    started_at = datetime.now()

    for idx, area in enumerate(areas, start=1):
        try:
            counts = count_facilities_for_area(area)
            cur.execute(
                """
                INSERT INTO planning_area_facilities (
                    area_name, schools, sports, hawkers, healthcare, greenSpaces, carparks, transit, community, calculated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                ON CONFLICT(area_name) DO UPDATE SET
                    schools=excluded.schools,
                    sports=excluded.sports,
                    hawkers=excluded.hawkers,
                    healthcare=excluded.healthcare,
                    greenSpaces=excluded.greenSpaces,
                    carparks=excluded.carparks,
                    transit=excluded.transit,
                    community=excluded.community,
                    calculated_at=datetime('now')
                """,
                (
                    area,
                    counts["schools"], counts["sports"], counts["hawkers"],
                    counts["healthcare"], counts["greenSpaces"], counts["carparks"], counts["transit"], counts["community"],
                ),
            )
            inserted += 1
            if idx % 5 == 0 or idx == len(areas):
                conn.commit()
                print(f"[{idx}/{len(areas)}] Upserted {area}")
        except Exception as e:
            print(f"[{idx}/{len(areas)}] Skipped {area}: {e}")

    conn.commit()
    conn.close()

    dur = (datetime.now() - started_at).total_seconds()
    print(f"Done. Upserted {inserted} areas into {args.db_name} in {dur:.1f}s")


if __name__ == "__main__":
    asyncio.run(main())
