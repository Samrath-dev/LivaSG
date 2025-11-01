#!/usr/bin/env python3
"""
List streets with transit > 0 from street_geocode.db and write a CSV.
Run from repo root or directly with python.
"""
import os
import sqlite3
import csv

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(BASE, "street_geocode.db")
OUT_CSV = os.path.join(BASE, "transit_streets.csv")

if not os.path.exists(DB_PATH):
    print(f"Error: DB not found at {DB_PATH}")
    raise SystemExit(1)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

query = """
SELECT f.street_name, f.transit, IFNULL(l.planning_area, '') as planning_area
FROM street_facilities f
LEFT JOIN street_locations l ON f.street_name = l.street_name
WHERE f.transit > 0
ORDER BY f.transit DESC, f.street_name
"""

rows = list(cur.execute(query))
if not rows:
    print("No streets with transit > 0 found in street_facilities.")
else:
    print(f"Found {len(rows)} streets with transit > 0 (street, transit_count, planning_area):\n")
    for street, transit, pa in rows:
        print(f"{transit:>3}  {street}  ({pa})")

    # Write CSV
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["street_name", "transit", "planning_area"])
        w.writerows(rows)
    print(f"\nCSV written to {OUT_CSV}")

conn.close()
