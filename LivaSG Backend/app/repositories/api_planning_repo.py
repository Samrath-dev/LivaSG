# app/repositories/api_planning_repo.py
from typing import Any, Dict, List
from app.integrations.onemap_client import OneMapClientHardcoded

class OneMapPlanningAreaRepo:
    """Fetches & caches planning area polygons and names using OneMap."""

    def __init__(self, client: OneMapClientHardcoded):
        self.client = client
        self._cache: Dict[int, Dict[str, Any]] = {}  # year => FeatureCollection

    async def geojson(self, year: int = 2020) -> Dict[str, Any]:
        if year not in self._cache:
            self._cache[year] = await self.client.planning_areas(year)
        return self._cache[year]

    async def names(self, year: int = 2020) -> List[str]:
        fc = await self.geojson(year)
        areas = []
        for f in fc.get("features", []):
            props = f.get("properties", {}) or {}
            name = props.get("Name") or props.get("PA_NAME") or ""
            name = name.strip()
            if name:
                areas.append(name)
        return sorted(set(areas))