"""
Geocode street names via OneMap Search API and save results to street_geocode.db

This script:
1. Reads unique street names from unique_streets.txt
2. Queries OneMap search API for each street
3. Saves results to street_geocode.db with schema matching planning_cache.db style
4. Supports resume capability and rate limiting
"""

import asyncio
import json
import os
import sqlite3
import sys
import time
from argparse import ArgumentParser
from pathlib import Path
from typing import Optional, Dict, List, Any

# Import OneMap client from the app
script_dir = Path(__file__).resolve().parent
backend_dir = script_dir.parent
sys.path.insert(0, str(backend_dir))

from app.integrations.onemap_client import OneMapClientHardcoded


class StreetGeocoder:
    def __init__(self, db_path: str = "street_geocode.db"):
        self.db_path = db_path
        self.client = OneMapClientHardcoded()
        self.conn: Optional[sqlite3.Connection] = None
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database with schema similar to planning_cache.db"""
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()
        
        # Main table for geocoded streets
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS street_locations (
                street_name TEXT PRIMARY KEY,
                result_count INTEGER DEFAULT 0,
                best_result_json TEXT,
                latitude REAL,
                longitude REAL,
                address TEXT,
                building TEXT,
                postal_code TEXT,
                searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending'
            )
        """)
        
        # All results table (one row per result for streets with multiple matches)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS street_all_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                street_name TEXT NOT NULL,
                result_index INTEGER NOT NULL,
                latitude REAL,
                longitude REAL,
                address TEXT,
                building TEXT,
                postal_code TEXT,
                result_json TEXT,
                UNIQUE(street_name, result_index)
            )
        """)
        
        # Progress tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS geocode_progress (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                last_street TEXT,
                total_processed INTEGER DEFAULT 0,
                total_found INTEGER DEFAULT 0,
                total_not_found INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute(
            "INSERT OR IGNORE INTO geocode_progress (id, last_street, total_processed) VALUES (1, '', 0)"
        )
        
        # Indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_street_status ON street_locations(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_all_results_street ON street_all_results(street_name)")
        
        self.conn.commit()
        print(f"✓ Database initialized at {self.db_path}")
    
    def get_progress(self) -> Dict[str, Any]:
        """Get current geocoding progress"""
        cursor = self.conn.cursor()
        row = cursor.execute(
            "SELECT last_street, total_processed, total_found, total_not_found FROM geocode_progress WHERE id = 1"
        ).fetchone()
        if not row:
            return {"last_street": "", "total_processed": 0, "total_found": 0, "total_not_found": 0}
        return {
            "last_street": row[0],
            "total_processed": row[1],
            "total_found": row[2],
            "total_not_found": row[3],
        }
    
    def update_progress(self, last_street: str, found: bool):
        """Update progress tracking"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE geocode_progress 
            SET last_street = ?,
                total_processed = total_processed + 1,
                total_found = total_found + ?,
                total_not_found = total_not_found + ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
        """, (last_street, 1 if found else 0, 0 if found else 1))
        self.conn.commit()
    
    async def search_street(self, street_name: str) -> Optional[List[Dict]]:
        """Search for a street using OneMap search API"""
        try:
            result = await self.client.search(street_name, page=1)
            if result and 'results' in result and result['results']:
                return result['results']
            return None
        except Exception as e:
            print(f"  ✗ Error searching {street_name}: {e}")
            return None
    
    def save_results(self, street_name: str, results: Optional[List[Dict]]):
        """Save geocoding results to database"""
        cursor = self.conn.cursor()
        
        if not results:
            # No results found
            cursor.execute("""
                INSERT OR REPLACE INTO street_locations 
                (street_name, result_count, status)
                VALUES (?, 0, 'not_found')
            """, (street_name,))
            self.conn.commit()
            return
        
        # Save best (first) result to main table
        best = results[0]
        cursor.execute("""
            INSERT OR REPLACE INTO street_locations
            (street_name, result_count, best_result_json, latitude, longitude, 
             address, building, postal_code, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'found')
        """, (
            street_name,
            len(results),
            json.dumps(best),
            float(best.get('LATITUDE', 0)) if best.get('LATITUDE') else None,
            float(best.get('LONGITUDE', 0)) if best.get('LONGITUDE') else None,
            best.get('ADDRESS'),
            best.get('BUILDING'),
            best.get('POSTAL'),
        ))
        
        # Save all results to detail table
        cursor.execute("DELETE FROM street_all_results WHERE street_name = ?", (street_name,))
        for idx, result in enumerate(results):
            cursor.execute("""
                INSERT INTO street_all_results
                (street_name, result_index, latitude, longitude, address, building, postal_code, result_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                street_name,
                idx,
                float(result.get('LATITUDE', 0)) if result.get('LATITUDE') else None,
                float(result.get('LONGITUDE', 0)) if result.get('LONGITUDE') else None,
                result.get('ADDRESS'),
                result.get('BUILDING'),
                result.get('POSTAL'),
                json.dumps(result),
            ))
        
        self.conn.commit()
    
    async def geocode_streets(self, streets_file: Path, delay_ms: int = 100, resume: bool = True):
        """Geocode all streets from text file"""
        # Load street names
        if not streets_file.exists():
            print(f"✗ Streets file not found: {streets_file}")
            return
        
        street_names = [line.strip() for line in streets_file.read_text(encoding='utf-8').splitlines() if line.strip()]
        print(f"📋 Loaded {len(street_names)} street names from {streets_file.name}")
        
        # Resume from last position if enabled
        start_idx = 0
        if resume:
            progress = self.get_progress()
            if progress['last_street']:
                try:
                    start_idx = street_names.index(progress['last_street']) + 1
                    print(f"↻ Resuming from street #{start_idx + 1}: {progress['last_street']}")
                    print(f"   Previously: {progress['total_processed']} processed, "
                          f"{progress['total_found']} found, {progress['total_not_found']} not found")
                except ValueError:
                    print(f"⚠ Could not find last street '{progress['last_street']}' in file, starting from beginning")
        
        if start_idx >= len(street_names):
            print("✓ All streets already geocoded")
            return
        
        print(f"🔍 Geocoding {len(street_names) - start_idx} streets (delay: {delay_ms}ms)")
        
        # Process streets
        found_count = 0
        not_found_count = 0
        
        try:
            for idx in range(start_idx, len(street_names)):
                street = street_names[idx]
                
                # Search
                results = await self.search_street(street)
                
                # Save
                self.save_results(street, results)
                
                # Update counters
                if results:
                    found_count += 1
                    print(f"  ✓ [{idx + 1}/{len(street_names)}] {street}: {len(results)} result(s)")
                else:
                    not_found_count += 1
                    print(f"  ∅ [{idx + 1}/{len(street_names)}] {street}: no results")
                
                # Update progress
                self.update_progress(street, bool(results))
                
                # Rate limiting
                if delay_ms > 0 and idx < len(street_names) - 1:
                    await asyncio.sleep(delay_ms / 1000.0)
        
        except KeyboardInterrupt:
            print("\n\n⚠ Interrupted by user")
        except Exception as e:
            print(f"\n\n✗ Error: {e}")
        
        # Final stats
        progress = self.get_progress()
        print(f"\n📊 Final Statistics:")
        print(f"   Total processed: {progress['total_processed']}")
        print(f"   Found: {progress['total_found']}")
        print(f"   Not found: {progress['total_not_found']}")
        print(f"   Database: {self.db_path}")
    
    def close(self):
        if self.conn:
            self.conn.close()


async def main():
    parser = ArgumentParser(description="Geocode street names via OneMap search API")
    parser.add_argument(
        "--streets",
        default="unique_streets.txt",
        help="Path to text file with street names (default: unique_streets.txt)"
    )
    parser.add_argument(
        "--db",
        default="street_geocode.db",
        help="Path to output SQLite database (default: street_geocode.db)"
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=100,
        help="Delay between requests in milliseconds (default: 100)"
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Start from beginning instead of resuming"
    )
    
    args = parser.parse_args()
    
    # Resolve paths
    streets_path = Path(args.streets)
    if not streets_path.is_absolute():
        script_dir = Path(__file__).resolve().parent
        candidate = script_dir.parent / args.streets
        if candidate.exists():
            streets_path = candidate
        else:
            streets_path = streets_path.resolve()
    
    db_path = args.db
    if not Path(db_path).is_absolute():
        script_dir = Path(__file__).resolve().parent
        db_path = str(script_dir.parent / args.db)
    
    # Run geocoder
    geocoder = StreetGeocoder(db_path)
    try:
        await geocoder.geocode_streets(
            streets_path,
            delay_ms=args.delay,
            resume=not args.no_resume
        )
    finally:
        geocoder.close()


if __name__ == "__main__":
    asyncio.run(main())
