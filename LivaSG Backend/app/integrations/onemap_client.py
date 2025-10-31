# app/integrations/onemap_client.py
from __future__ import annotations

import os
import json
import base64
import time
import asyncio
import random
from typing import Any, Dict, List, Optional

import httpx
try:
    from dotenv import load_dotenv  
    load_dotenv()
except Exception:
    pass


AUTH_URL = "https://www.onemap.gov.sg//api/auth/post/getToken"

REFRESH_SKEW_SECONDS = 300 #6 * 3600            # refresh ~6 hours before exp
REFRESH_JITTER_RANGE = (60, 300)           

def _decode_exp(token: str) -> Optional[int]:
    """Return exp (epoch seconds) from JWT, or None if unreadable."""
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        data = json.loads(base64.urlsafe_b64decode(payload).decode("utf-8"))
        exp = data.get("exp")
        return int(exp) if isinstance(exp, (int, float)) else None
    except Exception:
        return None

def _now() -> int:
    return int(time.time())

class OneMapClientHardcoded:
    """
    Minimal OneMap client with auto-renew.
    - POPAPI endpoints (planning area polygons & names): Authorization: <token> (no 'Bearer')
    - Common endpoints (search, reverse geocode): Authorization: Bearer <token>
    """

    def __init__(self):
        self._timeout = httpx.Timeout(12.0, connect=5.0)

        self._client_kwargs = {
            "timeout": self._timeout,
            "trust_env": False,
            "limits": httpx.Limits(max_connections=15, max_keepalive_connections=0),
        }


        initial_token = os.getenv("ONEMAP_TOKEN") or "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo5NDExLCJmb3JldmVyIjpmYWxzZSwiaXNzIjoiT25lTWFwIiwiaWF0IjoxNzYxMjE1OTAyLCJuYmYiOjE3NjEyMTU5MDIsImV4cCI6MTc2MTQ3NTEwMiwianRpIjoiYzRhMTlmMWUtZmZiNy00ZjE3LWFhMmItNWRiNDJiZDM2ZTVlIn0.n5nL21swDIa8gFmaVuUmzirLCLYKCJJ4ofPcB_uAw3HPAACKtWVJNFnPJhokazIAVOOjJ-UbbTJZ4KbdzwfqrZYNQyAVpBQEmhOFduKu6_wIZIynyAXgldkl3Tl8zCuQAGICKn3HTcFfnCjZ4e_WGyTXOnDsoZ55FhZJGQJemRNPcPivTjNQG3Kk2b57ZMOhdL_XTOUbUHJ1Ae6F1QjdAHNOq-dBuEVJKvBcaxtFp5Mu3c4uEMBQSnx4RO89tU2A4LlpH62upgWTheGbCq86Ii3yKtl7Ltt0R_uBeaIYIJa__TLLfRCLcEOEQBm3Dv2zAYLSG__bPcf1WBlGwMRxog"
        self._token: Optional[str] = initial_token
        self._exp: Optional[int] = _decode_exp(initial_token) if initial_token else None

       
        self._refresh_lock = asyncio.Lock()


    def _need_refresh(self) -> bool:
        if not self._token or not self._exp:
            return True
        skew = REFRESH_SKEW_SECONDS + random.randint(*REFRESH_JITTER_RANGE)
        return _now() >= (self._exp - skew)

    async def _refresh_token(self) -> None:
        email = os.getenv("ONEMAP_EMAIL")
        password = os.getenv("ONEMAP_PASSWORD")
        if not email or not password:
       
            if not self._token:
                raise RuntimeError("Missing ONEMAP_EMAIL/ONEMAP_PASSWORD and no usable token.")
            return

        async with httpx.AsyncClient(**self._client_kwargs) as c:
            r = await c.post(AUTH_URL, json={"email": email, "password": password})
            r.raise_for_status()
            data = r.json()
            new_tok = data.get("access_token") or data.get("token")
            if not new_tok:
                raise RuntimeError(f"Auth response missing token: {data!r}")

            self._token = new_tok
            self._exp = _decode_exp(new_tok) or (_now() + 48 * 3600)  

    async def _ensure_token(self) -> str:
        if not self._need_refresh():
            return self._token  
        async with self._refresh_lock:
           
            if not self._need_refresh():
                return self._token  
            await self._refresh_token()
            return self._token  

    async def _pop_headers(self) -> Dict[str, str]:
        tok = await self._ensure_token()
        return {"Authorization": tok}

    async def _bearer_headers(self) -> Dict[str, str]:
        tok = await self._ensure_token()
        return {"Authorization": f"Bearer {tok}"}

    # ---------- POPAPI ----------

    async def planning_areas(self, year: int = 2019) -> Dict[str, Any]:
        """
        GET /api/public/popapi/getAllPlanningarea?year=2019
        Returns: {"SearchResults": [ { "pln_area_n": "...", "geojson": "{\"type\":\"MultiPolygon\"...}" }, ... ]}
        """
        url = f"https://www.onemap.gov.sg/api/public/popapi/getAllPlanningarea?year={year}"
        async with httpx.AsyncClient(**self._client_kwargs) as client:
            r = await client.get(url, headers=await self._pop_headers())
            r.raise_for_status()
            return r.json()

    async def planning_area_names(self, year: int = 2019) -> List[Dict[str, Any]]:
        """
        GET /api/public/popapi/getPlanningareaNames?year=2019
        Returns: [ { "id": 114, "pln_area_n": "BEDOK" }, ... ]
        """
        url = f"https://www.onemap.gov.sg/api/public/popapi/getPlanningareaNames?year={year}"
        async with httpx.AsyncClient(**self._client_kwargs) as client:
            r = await client.get(url, headers=await self._pop_headers())
            r.raise_for_status()
            return r.json()

    async def planning_area_at(self, lat: float, lon: float, year: int = 2019) -> List[Dict[str, Any]]:
        """
        GET /api/public/popapi/getPlanningarea?latitude=1.3&longitude=103.8&year=2019
        Returns: [ { "pln_area_n": "QUEENSTOWN", "geojson": "{...}" } ]
        """
        url = "https://www.onemap.gov.sg/api/public/popapi/getPlanningarea"
        params = {"latitude": str(lat), "longitude": str(lon), "year": str(year)}
        async with httpx.AsyncClient(**self._client_kwargs) as client:
            r = await client.get(url, headers=await self._pop_headers(), params=params)
            r.raise_for_status()
            return r.json()

    # ---------- Common endpoints (Bearer) ----------

    async def search(self, query: str, page: int = 1) -> Dict[str, Any]:
        url = "https://www.onemap.gov.sg/api/common/elastic/search"
        params = {"searchVal": query, "returnGeom": "Y", "getAddrDetails": "Y", "pageNum": page}
        async with httpx.AsyncClient(**self._client_kwargs) as client:
            r = await client.get(url, headers=await self._bearer_headers(), params=params)
            r.raise_for_status()
            return r.json()

    async def reverse_geocode(self, lat: float, lon: float) -> Dict[str, Any]:
        url = "https://www.onemap.gov.sg/api/common/ReverseGeocode"
        params = {"location": f"{lat},{lon}", "buffer": 10, "addressType": "All"}
        async with httpx.AsyncClient(**self._client_kwargs) as client:
            r = await client.get(url, headers=await self._bearer_headers(), params=params)
            r.raise_for_status()
            return r.json()