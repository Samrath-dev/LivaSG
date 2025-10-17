# app/integrations/onemap_client.py
import httpx
from typing import Any, Dict, List 

# Hardcoded token still used for search / reverse geocode (not needed for PopAPI planning areas)
ONE_MAP_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo5NDExLCJmb3JldmVyIjpmYWxzZSwiaXNzIjoiT25lTWFwIiwiaWF0IjoxNzYwNjkzMTk3LCJuYmYiOjE3NjA2OTMxOTcsImV4cCI6MTc2MDk1MjM5NywianRpIjoiNGI5N2I4MGUtNGY2MC00ZTU3LWIyNDYtODA4MGNhMTk2ZDliIn0.Jp0JvOXTLRNzbzMCKewjd7sy6M0fKY9w_HRoYK_GedyFRovGPTgeSdIiSGhSiBeCf8cETpcUuDhwCkbXmaAemnjoJDW8VHpydczm1bH0GjDppja15yv3SUjavd9UrOHI5nNvmzU4ydXISawlg4cJXu1Bf_cdcuiT0Bf31Q-VOc3utybsAmNHb9nuzOWcGy51dsrRyi2olCxbNvWkTpw04W1X5M_XcPrytE9cj_XZqv433nbuTcHPYFJhgUX9_bA7w7zUgKpswrr_cCm8GRhO7DN16-MvFPHtSHeTgdAy0zKl2iUAoGKDpIjhUVRskocDuEpEM4s6lp2891w6ZfLAvQ"

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