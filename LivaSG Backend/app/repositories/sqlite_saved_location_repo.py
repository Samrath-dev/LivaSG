# app/repositories/sqlite_saved_location_repo.py
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from ..domain.models import SavedLocation
from .interfaces import ISavedLocationRepo

class SQLiteSavedLocationRepo(ISavedLocationRepo):
    def __init__(self, db_path: str = "user_cache.db"):
        base_dir = Path(__file__).resolve().parents[2]
        self.db_path = base_dir / db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize the saved_locations table in the cache database"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS saved_locations (
                postal_code TEXT PRIMARY KEY,
                address TEXT NOT NULL,
                area TEXT NOT NULL,
                name TEXT,
                notes TEXT,
                saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
    
    def get_saved_locations(self) -> List[SavedLocation]:
        conn = sqlite3.connect(self.db_path)
        rows = conn.execute(
            "SELECT postal_code, address, area, name, notes, saved_at FROM saved_locations ORDER BY saved_at DESC"
        ).fetchall()
        conn.close()
        
        locations = []
        for row in rows:
            postal_code, address, area, name, notes, saved_at = row
            if isinstance(saved_at, str):
                try:
                    saved_at = datetime.fromisoformat(saved_at.replace('Z', '+00:00'))
                except:
                    saved_at = datetime.now()
            elif saved_at is None:
                saved_at = datetime.now()
                
            locations.append(SavedLocation(
                postal_code=postal_code,
                address=address,
                area=area,
                name=name,
                notes=notes,
                saved_at=saved_at
            ))
        return locations
    
    def saved_location(self, location: SavedLocation) -> None:
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT OR REPLACE INTO saved_locations 
            (postal_code, address, area, name, notes, saved_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            location.postal_code,
            location.address,
            location.area,
            location.name,
            location.notes,
            location.saved_at.isoformat() if location.saved_at else datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()
    
    def delete_location(self, postal_code: str) -> None:
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "DELETE FROM saved_locations WHERE postal_code = ?",
            (postal_code,)
        )
        conn.commit()
        conn.close()
    
    def get_location(self, postal_code: str) -> Optional[SavedLocation]:
        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT postal_code, address, area, name, notes, saved_at FROM saved_locations WHERE postal_code = ?",
            (postal_code,)
        ).fetchone()
        conn.close()
        
        if row:
            postal_code, address, area, name, notes, saved_at = row
            if isinstance(saved_at, str):
                try:
                    saved_at = datetime.fromisoformat(saved_at.replace('Z', '+00:00'))
                except:
                    saved_at = datetime.now()
            elif saved_at is None:
                saved_at = datetime.now()
                
            return SavedLocation(
                postal_code=postal_code,
                address=address,
                area=area,
                name=name,
                notes=notes,
                saved_at=saved_at
            )
        return None