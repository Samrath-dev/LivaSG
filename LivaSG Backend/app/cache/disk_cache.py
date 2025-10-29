# app/cache/disk_cache.py
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Tuple

try:
    import orjson as _json  
    def _dumps(obj: Any) -> bytes: return _json.dumps(obj)
    def _loads(b: bytes) -> Any: return _json.loads(b)
    EXT = "orjson"
except Exception:
   
    import json as _json_std
    def _dumps(obj: Any) -> bytes: return _json_std.dumps(obj).encode("utf-8")
    def _loads(b: bytes) -> Any: return _json_std.loads(b.decode("utf-8"))
    EXT = "json"

@dataclass
class SourceManifest:
    algo: str
    digest: str
    files: Dict[str, Dict[str, float]]  # {"path": {"size": int, "mtime": float}}

def ensure_dir(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)

def _file_fingerprint(p: Path) -> Tuple[int, float]:
    st = p.stat()
    return int(st.st_size), float(st.st_mtime)

def hash_sources(paths: Iterable[Path], algo: str = "sha256") -> SourceManifest:
    """
    Build a content hash and a file manifest for a set of source files.
  
    """
    h = hashlib.new(algo)
    files: Dict[str, Dict[str, float]] = {}
    for p in sorted({Path(x) for x in paths}):
        if not p.exists():
            # still include path so a later appearance invalidates cache
            k = str(p)
            files[k] = {"size": -1, "mtime": -1.0}
            h.update(k.encode("utf-8") + b"|missing")
            continue
        size, mtime = _file_fingerprint(p)
        k = str(p)
        files[k] = {"size": size, "mtime": mtime}
        h.update(k.encode("utf-8") + b"|" + str(size).encode() + b"|" + str(mtime).encode())
    return SourceManifest(algo=algo, digest=h.hexdigest(), files=files)

def _atomic_write(path: Path, data: bytes) -> None:
    ensure_dir(path)
    with tempfile.NamedTemporaryFile(dir=str(path.parent), delete=False) as tmp:
        tmp.write(data)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp_path = Path(tmp.name)
    tmp_path.replace(path)

def save_cache(path: Path, payload: Any, meta: Optional[Dict[str, Any]] = None) -> None:
    """
    Save payload + metadata atomically.
    """
    blob = {
        "meta": {
            **(meta or {}),
            "built_at": time.time(),
            "format": EXT,
        },
        "payload": payload,
    }
    _atomic_write(path, _dumps(blob))

def load_cache(path: Path) -> Optional[Dict[str, Any]]:
    """
    Load a cache file if present, else None.
    """
    if not path.exists():
        return None
    try:
        data = _loads(path.read_bytes())
        if not isinstance(data, dict) or "payload" not in data:
            return None
        return data
    except Exception:
        return None

def validate_manifest(stored: Dict[str, Any], current: SourceManifest) -> bool:
    """
    Validate that cache manifest matches current sources (by digest).
    Falls back to per-file size/mtime check if digest missing.
    """
    m = stored.get("manifest") if stored else None
    if not isinstance(m, dict):
        return False
    if m.get("algo") == current.algo and m.get("digest") == current.digest:
        return True

    cur_files = current.files
    old_files = m.get("files") if isinstance(m.get("files"), dict) else {}
    if set(cur_files.keys()) != set(old_files.keys()):
        return False
    for k, v in cur_files.items():
        ov = old_files.get(k, {})
        if int(v.get("size", -2)) != int(ov.get("size", -1)):
            return False
        if float(v.get("mtime", -2.0)) != float(ov.get("mtime", -1.0)):
            return False
    return True

def package_cache(meta: Dict[str, Any], manifest: SourceManifest, payload: Any) -> Dict[str, Any]:
    return {
        "meta": {
            **meta,
            "built_at": time.time(),
            "format": EXT,
        },
        "manifest": {
            "algo": manifest.algo,
            "digest": manifest.digest,
            "files": manifest.files,
        },
        "payload": payload,
    }

def save_cache_with_manifest(path: Path, manifest: SourceManifest, payload: Any, meta: Optional[Dict[str, Any]] = None) -> None:
    blob = package_cache(meta or {}, manifest, payload)
    _atomic_write(path, _dumps(blob))

def try_load_valid_cache(path: Path, current_manifest: SourceManifest) -> Optional[Any]:
    blob = load_cache(path)
    if not blob:
        return None
    if not validate_manifest(blob, current_manifest):
        return None
    return blob.get("payload")