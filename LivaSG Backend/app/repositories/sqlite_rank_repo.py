# app/repositories/sqlite_rank_repo.py
import sqlite3
from pathlib import Path
from ..domain.models import RankProfile
from .interfaces import IRankRepo

class SQLiteRankRepo(IRankRepo):
    def __init__(self, db_path: str = "user_cache.db"):
        base_dir = Path(__file__).resolve().parents[2]
        self.db_path = base_dir / db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize the ranks table in the cache database"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS user_ranks (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                rAff INTEGER NOT NULL DEFAULT 3,
                rAcc INTEGER NOT NULL DEFAULT 3,
                rAmen INTEGER NOT NULL DEFAULT 3,
                rEnv INTEGER NOT NULL DEFAULT 3,
                rCom INTEGER NOT NULL DEFAULT 3,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            INSERT OR IGNORE INTO user_ranks (id, rAff, rAcc, rAmen, rEnv, rCom)
            VALUES (1, 3, 3, 3, 3, 3)
        """)
        conn.commit()
        conn.close()
    
    def get_active(self) -> RankProfile | None:
        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT rAff, rAcc, rAmen, rEnv, rCom FROM user_ranks WHERE id = 1"
        ).fetchone()
        conn.close()
        
        if row:
            return RankProfile(rAff=row[0], rAcc=row[1], rAmen=row[2], rEnv=row[3], rCom=row[4])
        return None
    
    def set(self, r: RankProfile) -> None:
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            UPDATE user_ranks 
            SET rAff = ?, rAcc = ?, rAmen = ?, rEnv = ?, rCom = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
        """, (r.rAff, r.rAcc, r.rAmen, r.rEnv, r.rCom))
        conn.commit()
        conn.close()
    
    def clear(self) -> None:
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            UPDATE user_ranks 
            SET rAff=3, rAcc=3, rAmen=3, rEnv=3, rCom=3, updated_at = CURRENT_TIMESTAMP 
            WHERE id=1
        """)
        conn.commit()
        conn.close()