import csv
import os
import re
import sqlite3
import sys
import time
from argparse import ArgumentParser
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


def detect_column(headers: List[str], candidates: List[str]) -> Optional[str]:
    lowered = {h.lower(): h for h in headers}
    for cand in candidates:
        if cand.lower() in lowered:
            return lowered[cand.lower()]
    # fuzzy: pick first header containing any candidate token
    for h in headers:
        hl = h.lower()
        for cand in candidates:
            if cand.lower() in hl:
                return h
    return None


def normalize_postal_code(v: str) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip()
    if not s:
        return None
    # Some CSVs have float-like numbers; drop decimals
    s = s.split(".")[0]
    # Keep digits only
    s = re.sub(r"\D", "", s)
    if len(s) == 6:
        return s
    # Occasionally 7+ digits; take last 6 if plausible
    if len(s) > 6:
        return s[-6:]
    return None


def read_hdb_csv(csv_path: Path) -> Dict[str, str]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        if not headers:
            raise RuntimeError("CSV has no headers: " + str(csv_path))

        postal_col = detect_column(headers, [
            "postal_code",
            "postal",
            "postalcode",
            "postal_cd",
            "post_code",
            "postcode",
        ])
        street_col = detect_column(headers, [
            "street",
            "street_name",
            "streetname",
            "road",
            "road_name",
        ])
        block_col = detect_column(headers, [
            "blk_no",
            "block",
            "block_no",
            "blk",
            "house_blk",
        ])

        if not street_col:
            raise RuntimeError(
                f"Could not detect street column. Found headers={headers}. "
                f"Detected street_col={street_col}"
            )

        # If no postal_col, we'll try to synthesize from block+street via OneMap
        # For now, just support direct postal code column or skip
        if not postal_col and not block_col:
            raise RuntimeError(
                f"Could not detect postal_code or block column. Found headers={headers}."
            )

        mapping: Dict[str, str] = {}
        
        # If we have postal codes directly, use them
        if postal_col:
            for row in reader:
                pc_raw = row.get(postal_col)
                st_raw = row.get(street_col)
                pc = normalize_postal_code(pc_raw)
                st = (st_raw or "").strip().upper()
                if not pc or not st:
                    continue
                mapping.setdefault(pc, st)
        else:
            # HDB CSV doesn't have postal codes; we have blk_no + street
            # We'll create synthetic keys like "BLK|STREET" for now
            # (In production, you'd geocode these via OneMap search to get postal codes)
            for row in reader:
                blk_raw = row.get(block_col)
                st_raw = row.get(street_col)
                blk = (blk_raw or "").strip().upper()
                st = (st_raw or "").strip().upper()
                if not blk or not st:
                    continue
                # Store as synthetic key; won't match postal_codes table directly
                # but will populate hdb_streets for reference
                synthetic_key = f"{blk}|{st}"
                mapping.setdefault(synthetic_key, st)
        
        return mapping


def ensure_schema(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS hdb_streets (
            key TEXT PRIMARY KEY,
            street TEXT NOT NULL,
            block TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_hdb_street ON hdb_streets(street)"
    )
    conn.commit()


def upsert_hdb_streets(
    conn: sqlite3.Connection,
    rows: Iterable[Tuple[str, str]],
    batch_size: int = 500,
    sleep_ms: int = 10,
) -> Tuple[int, int]:
    cur = conn.cursor()
    inserted = 0
    updated = 0
    batch: List[Tuple[str, str, str]] = []
    sql = (
        "INSERT INTO hdb_streets (key, street, block) VALUES (?, ?, ?) "
        "ON CONFLICT(key) DO UPDATE SET street=excluded.street, block=excluded.block, updated_at=CURRENT_TIMESTAMP"
    )
    for key, street in rows:
        # Extract block from synthetic keys like "BLK|STREET"
        block = key.split("|")[0] if "|" in key else ""
        batch.append((key, street, block))
        if len(batch) >= batch_size:
            cur.executemany(sql, batch)
            conn.commit()
            inserted += len(batch)
            batch.clear()
            if sleep_ms > 0:
                time.sleep(sleep_ms / 1000.0)
    if batch:
        cur.executemany(sql, batch)
        conn.commit()
        inserted += len(batch)
    return inserted, updated


def create_view(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    # Helper view: for now just list HDB blocks/streets
    # (Since this CSV lacks postal codes, can't join directly to postal_codes)
    cur.execute(
        """
        CREATE VIEW IF NOT EXISTS v_hdb_blocks AS
        SELECT 
            block,
            street,
            COUNT(*) AS variant_count,
            MIN(updated_at) AS first_seen
        FROM hdb_streets
        WHERE block != ''
        GROUP BY block, street
        ORDER BY street, block
        """
    )
    conn.commit()


def main():
    parser = ArgumentParser(description="Import HDB street names into postal_codes.db (non-destructive)")
    parser.add_argument("--csv", default="hdb-property-information.csv", help="Path to HDB CSV (default: repo root)")
    parser.add_argument("--db", default="postal_codes.db", help="Path to SQLite DB (default: LivaSG Backend/postal_codes.db)")
    parser.add_argument("--batch-size", type=int, default=500, help="Rows per transaction (default 500)")
    parser.add_argument("--sleep-ms", type=int, default=10, help="Sleep between batches in ms (default 10) to reduce lock contention")
    args = parser.parse_args()

    # Resolve default DB path relative to this script if user didn't provide absolute path
    db_path = Path(args.db)
    if not db_path.is_absolute():
        # Default to LivaSG Backend/postal_codes.db
        script_dir = Path(__file__).resolve().parent
        default_db = script_dir.parent / "postal_codes.db"
        db_path = default_db if args.db == "postal_codes.db" else db_path.resolve()

    csv_path = Path(args.csv)
    if not csv_path.is_absolute():
        # Try repo root (two levels up from LivaSG Backend/scripts)
        repo_root = Path(__file__).resolve().parents[2]
        candidate = repo_root / args.csv
        if candidate.exists():
            csv_path = candidate
        else:
            csv_path = csv_path.resolve()

    if not csv_path.exists():
        print(f"✗ CSV not found: {csv_path}")
        sys.exit(1)

    print(f"→ Reading CSV: {csv_path}")
    mapping = read_hdb_csv(csv_path)
    print(f"✓ Parsed {len(mapping):,} unique postal_code → street rows from CSV")

    # Open DB with a busy timeout to avoid interrupting the running scraper
    conn = sqlite3.connect(str(db_path), timeout=30)
    conn.execute("PRAGMA busy_timeout=5000")

    print(f"→ Updating DB: {db_path}")
    ensure_schema(conn)
    inserted, updated = upsert_hdb_streets(
        conn,
        mapping.items(),
        batch_size=args.batch_size,
        sleep_ms=args.sleep_ms,
    )
    create_view(conn)

    total_rows = conn.execute("SELECT COUNT(*) FROM hdb_streets").fetchone()[0]
    unique_streets = conn.execute("SELECT COUNT(DISTINCT street) FROM hdb_streets").fetchone()[0]
    conn.close()

    print(f"✓ hdb_streets total rows: {total_rows:,}")
    print(f"✓ Unique streets: {unique_streets:,}")
    print(f"✓ Upserts applied: {inserted:,}")
    print("Note: This HDB CSV has block+street but no postal codes.")
    print("      Use v_hdb_blocks to see aggregated block/street pairs.")


if __name__ == "__main__":
    main()
