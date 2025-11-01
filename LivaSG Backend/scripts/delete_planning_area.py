"""
Delete a planning-area (by area_name) from planning_cache.db and optionally repopulate.

Usage (PowerShell from the `LivaSG Backend` folder):
  python .\scripts\delete_planning_area.py --name Serangoon --repopulate

This will:
- create a backup copy planning_cache.db.bak
- delete rows from planning_area_polygons and planning_area_facilities where area_name matches
- if --repopulate, run scripts/populate_area_facilities.py to rebuild counts

Be careful: this mutates planning_cache.db in-place.
"""
from __future__ import annotations
import argparse
import os
import shutil
import sqlite3
import subprocess
import sys
import pathlib
from datetime import datetime

# Resolve paths relative to this file so the script can be run from anywhere
p = pathlib.Path(__file__).resolve()
# repo root (one level above scripts/)
REPO_ROOT = str(p.parent.parent.resolve())
SCRIPTS_DIR = str(p.parent.resolve())
DB_NAME = "planning_cache.db"
# planning_cache.db lives in repo root
DB_PATH = os.path.join(REPO_ROOT, DB_NAME)


def backup_db(path: str) -> str:
    if not os.path.exists(path):
        raise FileNotFoundError(f"DB not found at {path}")
    bak_path = path + ".bak"
    shutil.copy2(path, bak_path)
    return bak_path


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    return cur.fetchone() is not None


def delete_area(conn: sqlite3.Connection, area_name: str) -> dict:
    cur = conn.cursor()
    results = {}
    # planning_area_polygons: column is area_name
    if table_exists(conn, 'planning_area_polygons'):
        cur.execute("SELECT COUNT(*) FROM planning_area_polygons WHERE area_name = ?", (area_name,))
        c = cur.fetchone()[0]
        results['polygons_before'] = c
        if c:
            cur.execute("DELETE FROM planning_area_polygons WHERE area_name = ?", (area_name,))
            results['polygons_deleted'] = c
    else:
        results['polygons_before'] = 0
        results['polygons_deleted'] = 0

    # planning_area_facilities: column is area_name
    if table_exists(conn, 'planning_area_facilities'):
        cur.execute("SELECT COUNT(*) FROM planning_area_facilities WHERE area_name = ?", (area_name,))
        c = cur.fetchone()[0]
        results['facilities_before'] = c
        if c:
            cur.execute("DELETE FROM planning_area_facilities WHERE area_name = ?", (area_name,))
            results['facilities_deleted'] = c
    else:
        results['facilities_before'] = 0
        results['facilities_deleted'] = 0

    conn.commit()
    return results


def run_repopulate():
    # Call populate_area_facilities.py using the same Python executable
    # script lives in the repo's scripts/ directory
    script = os.path.join(REPO_ROOT, 'scripts', 'populate_area_facilities.py')
    if not os.path.exists(script):
        raise FileNotFoundError(f"Repopulation script not found: {script}")
    print(f"Running repopulation script: {script}")
    proc = subprocess.run([sys.executable, script], cwd=REPO_ROOT)
    return proc.returncode


def main():
    parser = argparse.ArgumentParser(description="Delete a planning-area from planning_cache.db and optionally repopulate")
    parser.add_argument("--name", required=True, help="Area name to delete (case-sensitive, e.g., 'Serangoon')")
    parser.add_argument("--repopulate", action="store_true", help="Run populate_area_facilities.py after deletion")
    args = parser.parse_args()

    if not os.path.exists(DB_PATH):
        print(f"Error: {DB_PATH} not found", file=sys.stderr)
        sys.exit(2)

    print(f"Backing up {DB_PATH} -> {DB_PATH}.bak")
    bak = backup_db(DB_PATH)
    print(f"Backup created at: {bak}")

    conn = sqlite3.connect(DB_PATH)
    try:
        print(f"Deleting area rows for: {args.name}")
        res = delete_area(conn, args.name)
        print("Deletion summary:")
        for k, v in res.items():
            print(f"  {k}: {v}")
    finally:
        conn.close()

    if args.repopulate:
        code = run_repopulate()
        if code == 0:
            print("Repopulation finished successfully.")
        else:
            print(f"Repopulation exited with code {code}")


if __name__ == '__main__':
    main()
