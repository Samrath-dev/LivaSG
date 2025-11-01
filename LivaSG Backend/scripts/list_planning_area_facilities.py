#!/usr/bin/env python3
"""Dump planning_area_facilities table from planning_cache.db.

Usage:
  python scripts/list_planning_area_facilities.py            # prints CSV to stdout
  python scripts/list_planning_area_facilities.py --out out.csv
  python scripts/list_planning_area_facilities.py --json     # prints JSON
"""
import sqlite3
import os
import sys
import csv
import json
import argparse

DB = os.path.join(os.path.dirname(__file__), '..', 'LivaSG Backend', 'planning_cache.db')
DB = os.path.abspath(DB)

parser = argparse.ArgumentParser()
parser.add_argument('--out', '-o', help='Write CSV to this file (optional)')
parser.add_argument('--json', action='store_true', help='Output JSON instead of CSV')
args = parser.parse_args()

if not os.path.exists(DB):
    print('MISSING_DB', DB, file=sys.stderr)
    sys.exit(2)

conn = sqlite3.connect(DB)
cur = conn.cursor()

# Confirm table exists
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='planning_area_facilities'")
if not cur.fetchone():
    print('MISSING_TABLE planning_area_facilities', file=sys.stderr)
    conn.close()
    sys.exit(3)

q = '''SELECT area_name, schools, sports, hawkers, healthcare, greenSpaces, carparks, transit
       FROM planning_area_facilities
       ORDER BY area_name COLLATE NOCASE
'''
rows = cur.execute(q).fetchall()
conn.close()

columns = ['area_name','schools','sports','hawkers','healthcare','greenSpaces','carparks','transit']

if args.json:
    out = [dict(zip(columns, r)) for r in rows]
    print(json.dumps(out, indent=2))
    sys.exit(0)

# CSV output
if args.out:
    with open(args.out, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(columns)
        for r in rows:
            w.writerow(r)
    print('WROTE', args.out)
else:
    w = csv.writer(sys.stdout)
    w.writerow(columns)
    for r in rows:
        w.writerow(r)
