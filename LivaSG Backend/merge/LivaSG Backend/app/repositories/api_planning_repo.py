from typing import Any, Dict, List, Optional
from fastapi import HTTPException
import httpx
import json

from app.integrations.onemap_client import OneMapClientHardcoded


class OneMapPlanningAreaRepo:
    """
    Fetches & caches planning area polygons and names using OneMap PopAPI.

    Shapes (typical):
      {"SearchResults": [ {"pln_area_n": "BEDOK", "geojson": "{\"type\":\"MultiPolygon\",...}"} ]}

    Names (variants):
      [ {"id": 114, "pln_area_n": "BEDOK"}, ... ]
      or {"SearchResults": [ {"id": 114, "pln_area_n": "BEDOK"}, ... ]}
    """

    def __init__(self, client: OneMapClientHardcoded):
        self.client = client
        self._fc_cache: Dict[int, Dict[str, Any]] = {}      
        self._names_cache: Dict[int, List[str]] = {}         

 
    #  (tolerant parse)
   
    @staticmethod
    def _unwrap_list_payload(payload: Any) -> List[Any]:
        """
        Accepts either a list or a dict wrapper; returns the inner list or [].
        Known wrappers: "SearchResults", "results", "data".
        """
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            for key in ("SearchResults", "results", "data"):
                val = payload.get(key)
                if isinstance(val, list):
                    return val
        # Not a recognized shape
        return []

    @staticmethod
    def _safe_parse_geojson(value: Any) -> Optional[Dict[str, Any]]:
        """
        Accepts either a JSON string or a dict; returns dict or None.
        """
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        return None

    @staticmethod
    def _extract_name(props: Dict[str, Any]) -> Optional[str]:
        """
        Normalize name from common keys.
        """
        for key in ("pln_area_n", "PA_NAME", "Name", "name"):
            v = props.get(key)
            if isinstance(v, str) and v.strip():
                return v.strip()
        return None

    # Public API

    async def geojson(self, year: int = 2019) -> Dict[str, Any]:
        """
        Returns a GeoJSON FeatureCollection with properties: {"pln_area_n": "<NAME>"}.
        Tolerates multiple upstream payload shapes.
        """
        if year in self._fc_cache:
            return self._fc_cache[year]

        try:
            payload = await self.client.planning_areas(year)
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"OneMap PopAPI error: {e.response.text}"
            )

        rows = self._unwrap_list_payload(payload)
        if not rows:
            # Show a concise preview to aid debugging
            sample = str(payload)[:240]
            raise HTTPException(
                status_code=502,
                detail=f"Unexpected PopAPI payload for shapes. Sample: {sample}"
            )

        features: List[Dict[str, Any]] = []
        for item in rows:
            if not isinstance(item, dict):
                continue
            name = self._extract_name(item) or item.get("pln_area_n")
            geom = self._safe_parse_geojson(item.get("geojson"))
            if not (name and isinstance(geom, dict)):
                # skip malformed lines silently
                continue

            features.append({
                "type": "Feature",
                "properties": {"pln_area_n": name},
                "geometry": geom
            })

        fc = {"type": "FeatureCollection", "features": features}
        self._fc_cache[year] = fc
        return fc

    async def names(self, year: int = 2019) -> List[str]:
        """
        Returns a sorted, de-duplicated list of planning area names.
        Tolerates both bare-list and wrapped responses; multiple name keys.
        """
        if year in self._names_cache:
            return self._names_cache[year]

        try:
            payload = await self.client.planning_area_names(year)
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"OneMap PopAPI error: {e.response.text}"
            )

        rows = self._unwrap_list_payload(payload) or (payload if isinstance(payload, list) else [])
        if not isinstance(rows, list):
            keys = list(payload.keys()) if isinstance(payload, dict) else type(payload).__name__
            raise HTTPException(
                status_code=502,
                detail=f"Unexpected PopAPI payload for names. Found: {keys}"
            )

        names: List[str] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            n = self._extract_name(row)
            if n:
                names.append(n)

        names = sorted(set(names))
        self._names_cache[year] = names
        return names