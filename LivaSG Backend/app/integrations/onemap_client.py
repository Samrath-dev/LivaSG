# app/integrations/onemap_client.py
import httpx
from typing import Any, Dict, List 

# Hardcoded token still used for search / reverse geocode (not needed for PopAPI planning areas)
ONE_MAP_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo5NDExLCJmb3JldmVyIjpmYWxzZSwiaXNzIjoiT25lTWFwIiwiaWF0IjoxNzYwOTY3MDUzLCJuYmYiOjE3NjA5NjcwNTMsImV4cCI6MTc2MTIyNjI1MywianRpIjoiZDJlOTBjZDUtZDRhNS00NzdjLTljNDItZDZmOGNjYjRmYjhjIn0.bpEZeCkdcuy5j-i47bl7AlI3wGvYQIYw3drjMkYM4ejM_OjxJ6e6licn8tKFID0WyFvM3gSX8cI727_8JKWr1m_-39AoYMaDShhlhb90Fsvh2e4yQdWUB3iTdmBqXsWkDKyo-RF7Uk5H_5rZgTgh2NMfyAhx9OA2rOq5StHaMrc6y64aO9FTVnjgRxzZv_jUnmtADG8n9HW2Go4ttFtmUhS-y7Sow5V8rySdPIMWoEkgcYsxiOYKduXq4Xr-MuI2ihbc5tDFwqafWNuPKzIrsTw38GoPprf0jaMSS2OxVs5GwpZKLK5kiQ1Sp-tXljRAnfd1emxHXnzLBShjVKx1bA"
class OneMapClientHardcoded:
    """
    Minimal OneMap client.
    - PopAPI endpoints (planning area polygons & names): Authorization: <token> (no 'Bearer')
    - Common endpoints (search, reverse geocode): keep Bearer (legacy/common style)
    """

    def __init__(self):
        self._timeout = httpx.Timeout(12.0, connect=5.0)
      
        self._headers_pop = {"Authorization": ONE_MAP_TOKEN}
       
        self._headers_bearer = {"Authorization": f"Bearer {ONE_MAP_TOKEN}"}

    #  POPAPI: Planning Areas (polygons) 
    async def planning_areas(self, year: int = 2019) -> Dict[str, Any]:
        """
        GET /api/public/popapi/getAllPlanningarea?year=2019
        Returns: {"SearchResults": [ { "pln_area_n": "...", "geojson": "{\"type\":\"MultiPolygon\"...}" }, ... ]}
        """
        url = f"https://www.onemap.gov.sg/api/public/popapi/getAllPlanningarea?year={year}"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.get(url, headers=self._headers_pop)
            r.raise_for_status()
            return r.json()

    #  POPAPI: Planning Area names 
    async def planning_area_names(self, year: int = 2019) -> List[Dict[str, Any]]:
        """
        GET /api/public/popapi/getPlanningareaNames?year=2019
        Returns: [ { "id": 114, "pln_area_n": "BEDOK" }, ... ]
        """
        url = f"https://www.onemap.gov.sg/api/public/popapi/getPlanningareaNames?year={year}"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.get(url, headers=self._headers_pop)
            r.raise_for_status()
            return r.json()

    #  POPAPI: Planning Area by point 
    async def planning_area_at(self, lat: float, lon: float, year: int = 2019) -> List[Dict[str, Any]]:
        """
        GET /api/public/popapi/getPlanningarea?latitude=1.3&longitude=103.8&year=2019
        Returns: [ { "pln_area_n": "QUEENSTOWN", "geojson": "{...}" } ]
        """
        url = "https://www.onemap.gov.sg/api/public/popapi/getPlanningarea"
        params = {"latitude": str(lat), "longitude": str(lon), "year": str(year)}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.get(url, headers=self._headers_pop, params=params)
            r.raise_for_status()
            return r.json()

    #  Common endpoints  
    async def search(self, query: str, page: int = 1) -> Dict[str, Any]:
        url = "https://www.onemap.gov.sg/api/common/elastic/search"
        params = {"searchVal": query, "returnGeom": "Y", "getAddrDetails": "Y", "pageNum": page}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.get(url, headers=self._headers_bearer, params=params)
            r.raise_for_status()
            return r.json()

    async def reverse_geocode(self, lat: float, lon: float) -> Dict[str, Any]:
        url = "https://www.onemap.gov.sg/api/common/ReverseGeocode"
        params = {"location": f"{lat},{lon}", "buffer": 10, "addressType": "All"}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.get(url, headers=self._headers_bearer, params=params)
            r.raise_for_status()
            return r.json()