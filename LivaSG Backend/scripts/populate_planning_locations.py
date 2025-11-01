"""
Populate per-category location tables in planning_cache.db

Creates tables such as:
 - schools_locations(name, latitude, longitude, type)
 - sports_locations(...)
 - hawkers_locations(...)
 - clinics_locations(...)
 - parks_locations(...)
 - carparks_locations(...)
 - transit_nodes(id, name, type, latitude, longitude)

Data sources used:
 - MemoryAmenityRepo datasets (schools, sports, hawkers, clinics, parks)
 - MemoryCarparkRepo, MemoryTransitRepo

Usage (PowerShell):
  python populate_planning_locations.py
  python populate_planning_locations.py --db street_geocode.db

This is safe to re-run; tables are recreated.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sqlite3
from typing import Any, Dict, Iterable, List


# Allow running as a script from repo root
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "."))

# Ensure the project package (LivaSG Backend) is on sys.path so `import app` works
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app.repositories.memory_impl import (
    MemoryAmenityRepo,
    MemoryCarparkRepo,
    MemoryTransitRepo,
    MemoryCommunityRepo,
)


def _extract_latlon(item: Dict[str, Any]) -> tuple[float, float] | None:
    """Robustly extract (lat, lon) from dict-like amenity rows."""
    if not isinstance(item, dict):
        return None
    # try common keys (case-insensitive)
    for lat_key in ("latitude", "Latitude", "LATITUDE", "lat", "LAT"):
        for lon_key in ("longitude", "Longitude", "LONGITUDE", "lon", "LON"):
            if lat_key in item and lon_key in item:
                try:
                    return float(item[lat_key]), float(item[lon_key])
                except Exception:
                    continue
    # try nested geometry shapes
    geom = item.get("geometry") or item.get("geom")
    if isinstance(geom, dict):
        coords = geom.get("coordinates")
        if isinstance(coords, (list, tuple)) and len(coords) >= 1:
            # coordinates often [lng, lat] or polygon arrays; try to find a numeric pair
            def find_pair(c):
                if isinstance(c, (list, tuple)) and len(c) >= 2 and isinstance(c[0], (int, float)) and isinstance(c[1], (int, float)):
                    return c[1], c[0]
                return None
            # direct pair
            p = find_pair(coords)
            if p:
                return p
            # nested (e.g., [[lon,lat],...])
            for c in coords:
                p = find_pair(c)
                if p:
                    return p
    return None


def ensure_table(conn: sqlite3.Connection, table: str, columns: str) -> None:
    cur = conn.cursor()
    cur.execute(f"DROP TABLE IF EXISTS {table}")
    cur.execute(f"CREATE TABLE IF NOT EXISTS {table} ({columns})")
    conn.commit()


async def main():
    parser = argparse.ArgumentParser(description="Populate per-category location tables in planning_cache.db")
    parser.add_argument("--db", dest="db_name", default="planning_cache.db", help="Target SQLite DB filename")
    args = parser.parse_args()

    # prefer project root (LivaSG Backend) as base so DB ends up next to the app package
    db_path = os.path.join(project_root, args.db_name)
    print(f"Target DB: {db_path}")

    # Load datasets (may fetch/cached)
    print("Initializing memory repos (may take a moment)...")
    await MemoryAmenityRepo.initialize()
    try:
        await MemoryTransitRepo.initialize()
    except Exception:
        # Some repos may be synchronous; ignore
        pass

    carpark_repo = MemoryCarparkRepo()
    transit_repo = MemoryTransitRepo()
    community_repo = MemoryCommunityRepo()

    # Prepare source lists
    schools = MemoryAmenityRepo._schools_data or []
    sports = MemoryAmenityRepo._sports_data or []
    hawkers = MemoryAmenityRepo._hawkers_data or []
    clinics = MemoryAmenityRepo._clinics_data or []
    parks = MemoryAmenityRepo._parks_data or []
    # MemoryCarparkRepo uses list_all(); ensure we call the right accessor
    carparks = carpark_repo.list_all() if hasattr(carpark_repo, "list_all") else []
    transit_nodes = transit_repo.all() if hasattr(transit_repo, "all") else []
    community_centres = community_repo._centres if hasattr(community_repo, "_centres") else []

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Create tables
    ensure_table(conn, "schools_locations", "name TEXT, latitude REAL, longitude REAL, type TEXT")
    ensure_table(conn, "sports_locations", "name TEXT, latitude REAL, longitude REAL, type TEXT")
    ensure_table(conn, "hawkers_locations", "name TEXT, latitude REAL, longitude REAL, type TEXT")
    ensure_table(conn, "clinics_locations", "name TEXT, latitude REAL, longitude REAL, type TEXT")
    ensure_table(conn, "parks_locations", "name TEXT, latitude REAL, longitude REAL, type TEXT")
    ensure_table(conn, "carparks_locations", "id TEXT, name TEXT, latitude REAL, longitude REAL, type TEXT")
    ensure_table(conn, "transit_nodes", "id TEXT, name TEXT, type TEXT, latitude REAL, longitude REAL")
    ensure_table(conn, "community_centres_locations", "name TEXT, latitude REAL, longitude REAL, type TEXT")

    inserted = {"schools": 0, "sports": 0, "hawkers": 0, "clinics": 0, "parks": 0, "carparks": 0, "transit": 0, "community": 0}

    def insert_rows(table: str, rows: Iterable[tuple]):
        placeholders = ",".join(["?"] * len(next(iter(rows), ("",))))
        cur.executemany(f"INSERT INTO {table} VALUES ({placeholders})", rows)

    # Schools
    s_rows = []
    for s in schools:
        p = _extract_latlon(s)
        if p:
            lat, lon = p
            name = s.get("SEARCHVAL") or s.get("name") or s.get("Name") or s.get("school") or "School"
            s_rows.append((name, lat, lon, s.get("type", "")))
    if s_rows:
        insert_rows("schools_locations", (r for r in s_rows))
        inserted["schools"] = len(s_rows)

    # Sports
    sp_rows = []
    for s in sports:
        p = _extract_latlon(s)
        if p:
            lat, lon = p
            name = s.get("name") or s.get("SEARCHVAL") or "Sports"
            sp_rows.append((name, lat, lon, s.get("type", "")))
    if sp_rows:
        insert_rows("sports_locations", (r for r in sp_rows))
        inserted["sports"] = len(sp_rows)

    # Hawkers
    h_rows = []
    for h in hawkers:
        p = _extract_latlon(h)
        if p:
            lat, lon = p
            name = h.get("name") or h.get("Hawker") or "Hawker"
            h_rows.append((name, lat, lon, h.get("type", "")))
    if h_rows:
        insert_rows("hawkers_locations", (r for r in h_rows))
        inserted["hawkers"] = len(h_rows)

    # Clinics / Healthcare
    c_rows = []
    for c in clinics:
        p = _extract_latlon(c)
        if p:
            lat, lon = p
            name = c.get("name") or c.get("SEARCHVAL") or c.get("org_name") or "Clinic"
            c_rows.append((name, lat, lon, c.get("type", "")))
    if c_rows:
        insert_rows("clinics_locations", (r for r in c_rows))
        inserted["clinics"] = len(c_rows)

    # Parks
    park_rows = []
    for p in parks:
        latlon = _extract_latlon(p)
        if latlon:
            lat, lon = latlon
            name = p.get("name") or p.get("Name") or "Park"
            park_rows.append((name, lat, lon, p.get("type", "")))
    if park_rows:
        insert_rows("parks_locations", (r for r in park_rows))
        inserted["parks"] = len(park_rows)

    # Carparks
    cp_rows = []
    for cp in carparks:
        try:
            # Carpark objects are dataclasses; try attributes
            cp_id = getattr(cp, "id", None) or getattr(cp, "carpark_id", None) or None
            name = getattr(cp, "name", None) or getattr(cp, "address", None) or str(cp_id) or "Carpark"
            lat = float(getattr(cp, "latitude", 0))
            lon = float(getattr(cp, "longitude", 0))
            cp_rows.append((cp_id, name, lat, lon, getattr(cp, "type", "")))
        except Exception:
            continue
    if cp_rows:
        insert_rows("carparks_locations", (r for r in cp_rows))
        inserted["carparks"] = len(cp_rows)

    # Transit
    t_rows = []
    for t in transit_nodes:
        try:
            tid = getattr(t, "id", None) or getattr(t, "node_id", None) or None
            name = getattr(t, "name", None) or tid or "Transit"
            typ = getattr(t, "type", None) or ""
            lat = float(getattr(t, "latitude", 0))
            lon = float(getattr(t, "longitude", 0))
            t_rows.append((tid, name, typ, lat, lon))
        except Exception:
            continue
    if t_rows:
        insert_rows("transit_nodes", (r for r in t_rows))
        inserted["transit"] = len(t_rows)

    # Community Centres
    cc_rows = []
    for cc in community_centres:
        try:
            name = getattr(cc, "name", None) or getattr(cc, "id", None) or "Community Centre"
            lat = float(getattr(cc, "latitude", 0))
            lon = float(getattr(cc, "longitude", 0))
            # Use address as type field to store additional info
            addr = getattr(cc, "address", None) or ""
            cc_rows.append((name, lat, lon, addr))
        except Exception:
            continue
    if cc_rows:
        insert_rows("community_centres_locations", (r for r in cc_rows))
        inserted["community"] = len(cc_rows)

    conn.commit()
    conn.close()

    print("Done. Inserted rows:")
    for k, v in inserted.items():
        print(f" - {k}: {v}")


if __name__ == "__main__":
    asyncio.run(main())
