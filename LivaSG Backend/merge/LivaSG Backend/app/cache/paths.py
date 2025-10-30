# app/cache/paths.py
from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


CACHE_DIR = Path(os.getenv("CACHE_DIR", ".cache"))
CACHE_DIR = (PROJECT_ROOT / CACHE_DIR).resolve()

def cache_file(name: str, version: int = 1, ext: str = "orjson") -> Path:
    """
    Compute a cache file path like: <PROJECT_ROOT>/.cache/<name>.v<version>.<ext>
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in name)
    return CACHE_DIR / f"{safe}.v{version}.{ext}"