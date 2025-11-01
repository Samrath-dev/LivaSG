"""
Scrape all valid 6-digit Singapore postal codes using OneMap search API.
Groups results by road name and saves to SQLite database.

Singapore postal code ranges (by district):
- 01-45: D01-D28 (Central, North, Northeast, East, West)
- 46-82: Industrial/Special zones
- Each district has typical ranges (e.g., 01xxxx-02xxxx for CBD areas)

This script queries OneMap incrementally and handles:
- Rate limiting (sleeps between requests)
- Resume capability (tracks progress in DB)
- Validation (filters valid addresses with lat/lon)
"""

import asyncio
import sqlite3
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
import httpx

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    print("Note: Install 'tqdm' for progress bar support: pip install tqdm")

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.integrations.onemap_client import OneMapClientHardcoded


# Singapore postal code ranges to scan (6-digit codes)
# Only scan postal codes that start with specific 2-digit prefixes (Singapore sectors)
VALID_PREFIXES = [
    '01', '02', '03', '04', '05', '06', '07', '08', '09', '10',
    '11', '12', '13', '14', '15', '16', '17', '18', '19', '20',
    '21', '22', '23', '24', '25', '26', '27', '28', '29', '30',
    '31', '32', '33', '34', '35', '36', '37', '38', '39', '40',
    '41', '42', '43', '44', '45', '46', '47', '48', '49', '50',
    '51', '52', '53', '54', '55', '56', '57', '58', '59', '60',
    '61', '62', '63', '64', '65', '66', '67', '68', '69', '70',
    '71', '72', '73', '75', '76', '77', '78', '79', '80', '81', '82'
]

# Generate ranges from valid prefixes (e.g., '01' -> 010000 to 019999)
POSTAL_RANGES = [(int(prefix + '0000'), int(prefix + '9999')) for prefix in VALID_PREFIXES]

# For faster testing, use a smaller range like:
# POSTAL_RANGES = [(238800, 238900)]  # Small commercial area range


class PostalCodeScraper:
    def __init__(self, db_path: str = "postal_codes.db"):
        self.db_path = Path(__file__).parent.parent / db_path
        self.client = OneMapClientHardcoded()
        self.conn: Optional[sqlite3.Connection] = None
        self._init_db()
        
    def _init_db(self):
        """Initialize SQLite database with required tables."""
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()
        
        # Table for individual postal code results
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS postal_codes (
                postal_code TEXT PRIMARY KEY,
                road_name TEXT NOT NULL,
                building TEXT,
                block TEXT,
                address TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                x REAL,
                y REAL,
                searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(postal_code)
            )
        """)
        
        # Table for road name groupings (aggregate view)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS roads (
                road_name TEXT PRIMARY KEY,
                postal_code_count INTEGER DEFAULT 0,
                min_postal TEXT,
                max_postal TEXT,
                avg_latitude REAL,
                avg_longitude REAL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Progress tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scrape_progress (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                last_postal_code INTEGER NOT NULL,
                total_found INTEGER DEFAULT 0,
                total_searched INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Initialize progress if not exists
        cursor.execute("INSERT OR IGNORE INTO scrape_progress (id, last_postal_code) VALUES (1, 0)")
        
        self.conn.commit()
        
        # Create indices for faster queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_road_name ON postal_codes(road_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_searched_at ON postal_codes(searched_at)")
        
        self.conn.commit()
        print(f"✓ Database initialized at {self.db_path}")
    
    def get_progress(self) -> Dict[str, int]:
        """Get current scraping progress."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT last_postal_code, total_found, total_searched FROM scrape_progress WHERE id = 1")
        row = cursor.fetchone()
        return {
            "last_postal_code": row[0] if row else 0,
            "total_found": row[1] if row else 0,
            "total_searched": row[2] if row else 0
        }
    
    def update_progress(self, postal_code: int, found: int, searched: int):
        """Update scraping progress."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE scrape_progress 
            SET last_postal_code = ?, total_found = ?, total_searched = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
        """, (postal_code, found, searched))
        self.conn.commit()
    
    async def search_postal_code(self, postal_code: int) -> Optional[Dict[str, Any]]:
        """Query OneMap for a specific postal code."""
        try:
            # Format as 6-digit string with leading zeros
            postal_str = str(postal_code).zfill(6)
            result = await self.client.search(postal_str, page=1)
            
            if not result or "results" not in result or not result["results"]:
                return None
            
            # Take first result (most relevant)
            data = result["results"][0]
            
            # Validate essential fields
            if not all(k in data for k in ["LATITUDE", "LONGITUDE", "ADDRESS"]):
                return None
            
            return {
                "postal_code": postal_str,
                "road_name": data.get("ROAD_NAME", "").strip() or "Unknown",
                "building": data.get("BUILDING", "").strip(),
                "block": data.get("BLK_NO", "").strip(),
                "address": data.get("ADDRESS", "").strip(),
                "latitude": float(data["LATITUDE"]),
                "longitude": float(data["LONGITUDE"]),
                "x": float(data.get("X", 0)),
                "y": float(data.get("Y", 0))
            }
        except Exception as e:
            print(f"  Error querying {postal_code}: {e}")
            return None
    
    def save_postal_code(self, data: Dict[str, Any]):
        """Save postal code data to database."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO postal_codes 
            (postal_code, road_name, building, block, address, latitude, longitude, x, y)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["postal_code"],
            data["road_name"],
            data["building"],
            data["block"],
            data["address"],
            data["latitude"],
            data["longitude"],
            data["x"],
            data["y"]
        ))
        self.conn.commit()
    
    def rebuild_road_aggregates(self):
        """Rebuild the roads table with aggregated data."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM roads")
        cursor.execute("""
            INSERT INTO roads (road_name, postal_code_count, min_postal, max_postal, avg_latitude, avg_longitude)
            SELECT 
                road_name,
                COUNT(*) as postal_code_count,
                MIN(postal_code) as min_postal,
                MAX(postal_code) as max_postal,
                AVG(latitude) as avg_latitude,
                AVG(longitude) as avg_longitude
            FROM postal_codes
            WHERE road_name != 'Unknown'
            GROUP BY road_name
            ORDER BY postal_code_count DESC
        """)
        self.conn.commit()
        
        row_count = cursor.execute("SELECT COUNT(*) FROM roads").fetchone()[0]
        print(f"✓ Rebuilt roads table with {row_count} unique road names")
    
    async def scrape_range(self, start: int, end: int, delay_ms: int = 100):
        """Scrape a range of postal codes with rate limiting."""
        progress = self.get_progress()
        
        # Resume from last checkpoint if within this range
        if start <= progress["last_postal_code"] < end:
            start = progress["last_postal_code"] + 1
            print(f"↻ Resuming from postal code {start}")
        
        total_found = progress["total_found"]
        total_searched = progress["total_searched"]
        
        batch_size = 100
        batch_count = 0
        
        print(f"\n🔍 Scanning postal codes {start:06d} to {end:06d}")
        print(f"   Rate: {delay_ms}ms between requests")
        print(f"   Progress checkpoint every {batch_size} codes\n")
        
        start_time = time.time()
        total_codes = end - start + 1
        
        # Initialize progress bar if tqdm is available
        if TQDM_AVAILABLE:
            pbar = tqdm(
                total=total_codes,
                desc=f"Scanning {start:06d}-{end:06d}",
                unit="codes",
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}] Found: {postfix}"
            )
            pbar.set_postfix_str(f"{total_found}")
        else:
            pbar = None
        
        for postal_code in range(start, end + 1):
            result = await self.search_postal_code(postal_code)
            total_searched += 1
            
            if result:
                self.save_postal_code(result)
                total_found += 1
                if not pbar:  # Only print if no progress bar
                    print(f"  ✓ {postal_code:06d} → {result['road_name']} ({result['address'][:50]}...)")
            
            batch_count += 1
            
            # Update progress bar
            if pbar:
                pbar.update(1)
                pbar.set_postfix_str(f"{total_found}")
            
            # Checkpoint progress every batch
            if batch_count >= batch_size:
                self.update_progress(postal_code, total_found, total_searched)
                
                if not pbar:  # Only print stats if no progress bar
                    elapsed = time.time() - start_time
                    rate = total_searched / elapsed if elapsed > 0 else 0
                    eta_seconds = (end - postal_code) / rate if rate > 0 else 0
                    eta_hours = eta_seconds / 3600
                    print(f"\n  📊 Checkpoint: {total_found}/{total_searched} found | Rate: {rate:.1f} codes/sec | ETA: {eta_hours:.1f}h\n")
                
                batch_count = 0
            
            # Rate limiting (skip if delay is 0)
            if delay_ms > 0:
                await asyncio.sleep(delay_ms / 1000.0)
        
        # Close progress bar
        if pbar:
            pbar.close()
        
        # Final update
        self.update_progress(end, total_found, total_searched)
        
        elapsed = time.time() - start_time
        print(f"\n✓ Range complete: {total_found} valid postal codes found out of {total_searched} searched")
        print(f"  Time taken: {elapsed/60:.1f} minutes")
    
    async def scrape_all(self, delay_ms: int = 100):
        """Scrape all configured postal code ranges."""
        print(f"🚀 Starting postal code scraper")
        print(f"   Database: {self.db_path}")
        print(f"   Ranges: {len(POSTAL_RANGES)}")
        
        total_start = time.time()
        
        for start, end in POSTAL_RANGES:
            await self.scrape_range(start, end, delay_ms)
        
        # Rebuild aggregates
        print("\n🔄 Building road name aggregates...")
        self.rebuild_road_aggregates()
        
        total_elapsed = time.time() - total_start
        progress = self.get_progress()
        
        print(f"\n✅ Scraping complete!")
        print(f"   Total found: {progress['total_found']}")
        print(f"   Total searched: {progress['total_searched']}")
        print(f"   Total time: {total_elapsed/3600:.2f} hours")
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            print("✓ Database connection closed")


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Scrape Singapore postal codes from OneMap")
    parser.add_argument("--db", default="postal_codes.db", help="SQLite database path")
    parser.add_argument("--delay", type=int, default=100, help="Delay between requests in milliseconds")
    parser.add_argument("--start", type=int, help="Override start postal code")
    parser.add_argument("--end", type=int, help="Override end postal code")
    parser.add_argument("--rebuild", action="store_true", help="Only rebuild road aggregates from existing data")
    
    args = parser.parse_args()
    
    scraper = PostalCodeScraper(db_path=args.db)
    
    try:
        if args.rebuild:
            print("🔄 Rebuilding road aggregates...")
            scraper.rebuild_road_aggregates()
        elif args.start and args.end:
            await scraper.scrape_range(args.start, args.end, args.delay)
            scraper.rebuild_road_aggregates()
        else:
            await scraper.scrape_all(args.delay)
    finally:
        scraper.close()


if __name__ == "__main__":
    asyncio.run(main())
