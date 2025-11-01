"""
Query and analyze street facilities data in street_geocode.db

Usage:
    python scripts/query_street_facilities.py list [limit]      # List streets with facilities
    python scripts/query_street_facilities.py search <street>   # Search for specific street
    python scripts/query_street_facilities.py top [n]           # Show top N streets by facilities
    python scripts/query_street_facilities.py stats             # Show statistics
"""

import sqlite3
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).parent.parent
DB_PATH = BACKEND_DIR / "street_geocode.db"


def list_streets(conn, limit=20):
    """List streets with their facility counts."""
    cursor = conn.cursor()
    
    cursor.execute(f"""
        SELECT 
            sf.street_name,
            sf.schools,
            sf.sports,
            sf.hawkers,
            sf.healthcare,
            sf.greenSpaces,
            sf.carparks,
            (sf.schools + sf.sports + sf.hawkers + sf.healthcare + sf.greenSpaces + sf.carparks) as total
        FROM street_facilities sf
        ORDER BY sf.street_name
        LIMIT {limit}
    """)
    
    rows = cursor.fetchall()
    
    print(f"📋 Street Facilities (showing {len(rows)} streets)")
    print("━" * 120)
    print(f"{'Street Name':<45} {'Schools':>7} {'Sports':>7} {'Hawkers':>7} {'Health':>7} {'Parks':>7} {'Carpark':>7} {'Total':>7}")
    print("━" * 120)
    
    for row in rows:
        street, schools, sports, hawkers, health, parks, carparks, total = row
        print(f"{street[:43]:<45} {schools:>7} {sports:>7} {hawkers:>7} {health:>7} {parks:>7} {carparks:>7} {total:>7}")


def search_street(conn, search_term):
    """Search for streets matching the search term."""
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            sf.street_name,
            sf.schools,
            sf.sports,
            sf.hawkers,
            sf.healthcare,
            sf.greenSpaces,
            sf.carparks,
            (sf.schools + sf.sports + sf.hawkers + sf.healthcare + sf.greenSpaces + sf.carparks) as total,
            sl.latitude,
            sl.longitude
        FROM street_facilities sf
        JOIN street_locations sl ON sf.street_name = sl.street_name
        WHERE sf.street_name LIKE ?
        ORDER BY total DESC
    """, (f"%{search_term}%",))
    
    rows = cursor.fetchall()
    
    if not rows:
        print(f"❌ No streets found matching: {search_term}")
        return
    
    print(f"🔍 Search Results for '{search_term}' ({len(rows)} found)")
    print("━" * 140)
    
    for row in rows:
        street, schools, sports, hawkers, health, parks, carparks, total, lat, lon = row
        print(f"\n📍 {street}")
        print(f"   Location: {lat:.6f}, {lon:.6f}")
        print(f"   Facilities (within 1km):")
        print(f"     🏫 Schools:     {schools:>3}")
        print(f"     ⚽ Sports:      {sports:>3}")
        print(f"     🍜 Hawkers:     {hawkers:>3}")
        print(f"     🏥 Healthcare:  {health:>3}")
        print(f"     🌳 Parks:       {parks:>3}")
        print(f"     🚗 Carparks:    {carparks:>3}")
        print(f"     ━━━━━━━━━━━━━━━━━━")
        print(f"     📊 Total:       {total:>3}")


def show_top(conn, n=10):
    """Show top N streets by total facilities."""
    cursor = conn.cursor()
    
    # Top by total
    cursor.execute(f"""
        SELECT 
            sf.street_name,
            sf.schools,
            sf.sports,
            sf.hawkers,
            sf.healthcare,
            sf.greenSpaces,
            sf.carparks,
            (sf.schools + sf.sports + sf.hawkers + sf.healthcare + sf.greenSpaces + sf.carparks) as total
        FROM street_facilities sf
        ORDER BY total DESC
        LIMIT {n}
    """)
    
    rows = cursor.fetchall()
    
    print(f"🏆 Top {n} Streets by Total Facilities")
    print("━" * 120)
    print(f"{'Rank':<5} {'Street Name':<45} {'Schools':>7} {'Sports':>7} {'Hawkers':>7} {'Health':>7} {'Parks':>7} {'Total':>7}")
    print("━" * 120)
    
    for idx, row in enumerate(rows, 1):
        street, schools, sports, hawkers, health, parks, carparks, total = row
        print(f"{idx:<5} {street[:43]:<45} {schools:>7} {sports:>7} {hawkers:>7} {health:>7} {parks:>7} {total:>7}")
    
    # Top by schools
    print(f"\n🏫 Top {min(5, n)} Streets by Schools")
    print("━" * 80)
    cursor.execute(f"""
        SELECT street_name, schools
        FROM street_facilities
        ORDER BY schools DESC
        LIMIT {min(5, n)}
    """)
    for idx, (street, count) in enumerate(cursor.fetchall(), 1):
        print(f"{idx}. {street[:50]:<50} {count:>3} schools")
    
    # Top by healthcare
    print(f"\n🏥 Top {min(5, n)} Streets by Healthcare")
    print("━" * 80)
    cursor.execute(f"""
        SELECT street_name, healthcare
        FROM street_facilities
        ORDER BY healthcare DESC
        LIMIT {min(5, n)}
    """)
    for idx, (street, count) in enumerate(cursor.fetchall(), 1):
        print(f"{idx}. {street[:50]:<50} {count:>3} clinics")


def show_stats(conn):
    """Show detailed statistics."""
    cursor = conn.cursor()
    
    # Overall stats
    cursor.execute("""
        SELECT 
            COUNT(*) as total_streets,
            AVG(schools) as avg_schools,
            AVG(sports) as avg_sports,
            AVG(hawkers) as avg_hawkers,
            AVG(healthcare) as avg_healthcare,
            AVG(greenSpaces) as avg_parks,
            AVG(carparks) as avg_carparks,
            MAX(schools) as max_schools,
            MAX(sports) as max_sports,
            MAX(hawkers) as max_hawkers,
            MAX(healthcare) as max_healthcare,
            MAX(greenSpaces) as max_parks,
            MAX(carparks) as max_carparks
        FROM street_facilities
    """)
    
    row = cursor.fetchone()
    
    print("📊 Street Facilities Statistics")
    print("━" * 80)
    print(f"Total streets: {row[0]}")
    print(f"Search radius: 1.0 km")
    print()
    
    print("Average Facilities per Street:")
    print(f"  🏫 Schools:     {row[1]:>6.2f}  (max: {row[7]})")
    print(f"  ⚽ Sports:      {row[2]:>6.2f}  (max: {row[8]})")
    print(f"  🍜 Hawkers:     {row[3]:>6.2f}  (max: {row[9]})")
    print(f"  🏥 Healthcare:  {row[4]:>6.2f}  (max: {row[10]})")
    print(f"  🌳 Parks:       {row[5]:>6.2f}  (max: {row[11]})")
    print(f"  🚗 Carparks:    {row[6]:>6.2f}  (max: {row[12]})")
    
    # Distribution
    print(f"\n📈 Distribution by Total Facilities:")
    print("━" * 80)
    cursor.execute("""
        SELECT 
            CASE 
                WHEN total < 10 THEN '0-9'
                WHEN total < 20 THEN '10-19'
                WHEN total < 30 THEN '20-29'
                WHEN total < 40 THEN '30-39'
                WHEN total < 50 THEN '40-49'
                ELSE '50+'
            END as range,
            COUNT(*) as count
        FROM (
            SELECT (schools + sports + hawkers + healthcare + greenSpaces + carparks) as total
            FROM street_facilities
        )
        GROUP BY range
        ORDER BY range
    """)
    
    for range_str, count in cursor.fetchall():
        bar = "█" * int(count / 10)
        print(f"  {range_str:>6} facilities: {bar} {count}")
    
    # Streets with zero facilities
    cursor.execute("""
        SELECT COUNT(*) 
        FROM street_facilities
        WHERE schools = 0 AND sports = 0 AND hawkers = 0 
          AND healthcare = 0 AND greenSpaces = 0 AND carparks = 0
    """)
    zero_count = cursor.fetchone()[0]
    if zero_count > 0:
        print(f"\n⚠️  {zero_count} streets have no facilities within 1km")


def main():
    if not DB_PATH.exists():
        print(f"❌ Database not found: {DB_PATH}")
        print("Run generate_street_facilities.py first.")
        return
    
    if len(sys.argv) < 2:
        print(__doc__)
        return
    
    command = sys.argv[1].lower()
    
    conn = sqlite3.connect(DB_PATH)
    
    try:
        if command == "list":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
            list_streets(conn, limit)
        
        elif command == "search":
            if len(sys.argv) < 3:
                print("Usage: python scripts/query_street_facilities.py search <street_name>")
            else:
                search_street(conn, sys.argv[2])
        
        elif command == "top":
            n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            show_top(conn, n)
        
        elif command == "stats":
            show_stats(conn)
        
        else:
            print(f"Unknown command: {command}")
            print(__doc__)
    
    finally:
        conn.close()


if __name__ == "__main__":
    main()
