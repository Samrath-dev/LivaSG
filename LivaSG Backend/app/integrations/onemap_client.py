
import httpx
from typing import Any, Dict



ONE_MAP_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo5NDExLCJmb3JldmVyIjpmYWxzZSwiaXNzIjoiT25lTWFwIiwiaWF0IjoxNzYwMTg5NjczLCJuYmYiOjE3NjAxODk2NzMsImV4cCI6MTc2MDQ0ODg3MywianRpIjoiYWQwOGVkNjItZWE4NS00OWIzLTk3YWYtNTkzZGZiZDAyM2M3In0.ipinaP7XNELHIY7ZoNUSxSR0i-i-RFIIxxIUKs3fW_o1cxBlkO2XSJmvAg6xLI2bCierkCUHBEhnotYgGF8h5UmFSRecnpP3kuo9Tld_5Ja8e_QWG13wIPmka7KW_jMiymJr53_4Y39DA2Tv6xLvHVlMdRptlbIUFYZD1Y2I6A9ZD4yrptQuTve8qrwcwwLDKn1c0KU7ljFtdjYkRq9jzBBBmGFh_OIIk9EAwk3HjOpWzFVyMNRDboM7nrxzbwLKjHp5tX2Q--n74G5o41LrUZ01ycND5aQFGgDThnjc4pUhwG0aJHzU0haQGUltr0SXwRkQ4BDAfrRyyDARZbnbIw"


class OneMapClientHardcoded:
    """Im going to setup a docker later with some solution to this problem"""

    def __init__(self):
        self._timeout = httpx.Timeout(12.0, connect=5.0)
        self._headers = {"Authorization": f"Bearer {ONE_MAP_TOKEN}"}

    async def planning_areas(self, year: int = 2020) -> Dict[str, Any]:
        url = f"https://www.onemap.gov.sg/api/public/themes/planningarea?year={year}"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.get(url, headers=self._headers)
            r.raise_for_status()
            return r.json()  # GeoJSON FeatureCollection

    async def search(self, query: str, page: int = 1) -> Dict[str, Any]:
        url = "https://www.onemap.gov.sg/api/common/elastic/search"
        params = {"searchVal": query, "returnGeom": "Y", "getAddrDetails": "Y", "pageNum": page}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.get(url, headers=self._headers, params=params)
            r.raise_for_status()
            return r.json()

    async def reverse_geocode(self, lat: float, lon: float) -> Dict[str, Any]:
        url = "https://www.onemap.gov.sg/api/common/ReverseGeocode"
        params = {"location": f"{lat},{lon}", "buffer": 10, "addressType": "All"}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.get(url, headers=self._headers, params=params)
            r.raise_for_status()
            return r.json()