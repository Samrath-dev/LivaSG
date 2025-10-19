from datetime import date
import math
import requests
from typing import List, Optional
from ..domain.models import PriceRecord, FacilitiesSummary, WeightsProfile, NeighbourhoodScore, CommunityCentre, Transit, Carpark, AreaCentroid
from .interfaces import IPriceRepo, IAmenityRepo, IWeightsRepo, IScoreRepo, ICommunityRepo, ITransitRepo, ICarparkRepo, IAreaRepo
from ..integrations import onemap_client as onemap

class MemoryPriceRepo(IPriceRepo):
    def series(self, area_id: str, months: int) -> List[PriceRecord]:
        base = 500_000 if area_id != "Tampines" else 520_000
        out: List[PriceRecord] = []
        y, m = 2024, 1
        for i in range(months):
            out.append(PriceRecord(
                areaId=area_id, month=date(y, m, 1),
                medianResale=base + i*1200, p25=base-40_000, p75=base+40_000, volume=50-i%5
            ))
            m += 1
            if m > 12: m, y = 1, y+1
        return out

class MemoryAmenityRepo(IAmenityRepo):
    def __init__(self):
        self._schools_data = {}     # 724 schools in Singapore
        self._sports_data = self.getSportFacilities()  # 35 sports facilities in Singapore
        self._hawkers_data = self.getHawkerCentres()  # 129 hawker centres in Singapore
        self._clinics_data = self.getHealthcareClinics()  # 1193 CHAS clinics in Singapore
        self._parks_data = self.getParks()  # 441 parks in Singapore
        self._carparks_data = {}  # 524 carparks in Singapore

    async def facilities_summary(self, area_id: str) -> FacilitiesSummary:
        if self._schools_data == {}:
            self._schools_data = await self.getSchools()

        if self._carparks_data == {}:
            self._carparks_data = await self.getCarparks()

        return FacilitiesSummary(   
            schools=len(self.filterNearest(area_id, self._schools_data, threshold_km=2.0)),
            sports=len(self.filterNearest(area_id, self._sports_data, threshold_km=5.0)),
            hawkers=len(self.filterNearest(area_id, self._hawkers_data, threshold_km=5.0)),
            healthcare=len(self.filterNearest(area_id, self._clinics_data, threshold_km=2.0)),
            greenSpaces=len(self.filterNearest(area_id, self._parks_data, threshold_km=5.0)), 
            carparks=len(self.filterNearest(area_id, self._carparks_data, threshold_km=5.0)),
        )
    
    @staticmethod
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
        return 2*R*math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    def filterNearest(self, area_id: str, locations: List[dict], threshold_km: float) -> List[dict]:
        area_centroid = MemoryAreaRepo().centroid(area_id)
        if not area_centroid:
            return []  # Return empty list if the area_id is invalid or not found

        nearby_locations = []
        for loc in locations:
            try:
                # Check if the location is an AreaCentroid object
                if isinstance(loc, AreaCentroid):
                    loc_lat = loc.latitude
                    loc_lon = loc.longitude

                else:  # Assume it's a dictionary
                    loc_lat = float(loc.get("LATITUDE") or loc.get("latitude"))
                    loc_lon = float(loc.get("LONGITUDE") or loc.get("longitude"))

                # Calculate the distance
                distance = self.haversine(
                    area_centroid.latitude, area_centroid.longitude,
                    loc_lat, loc_lon
                )
                if distance <= threshold_km:
                    nearby_locations.append(loc)
            except (KeyError, ValueError):
                continue  # Skip locations with missing or invalid coordinates
        return nearby_locations

    # Search all pages for a given query for OneMap API
    async def searchAllPages(self, query: str) -> List[dict]:
        all_results = []
        page = 1
        onemap_client = onemap.OneMapClientHardcoded()

        while True:
            search_results = await onemap_client.search(query=query, page=page)

            if not search_results or "results" not in search_results or len(search_results["results"]) == 0:
                break  # No more results
            all_results.extend(search_results["results"])
            page += 1
        return all_results

    async def getSchools(self):
        # Use OneMap Search API to find nearby schools
        search_results = await self.searchAllPages(query="school")
        return search_results
    
    def getSportFacilities(self):
        dataset_id = "d_9b87bab59d036a60fad2a91530e10773"
        url = "https://api-open.data.gov.sg/v1/public/api/datasets/" + dataset_id + "/poll-download"

        response = requests.get(url)
        json_data = response.json()
        if json_data['code'] != 0:
            print(json_data['errMsg'])
            exit(1)

        url = json_data['data']['url']
        location_data = requests.get(url).json()

        sportfacilities = [
            {
            "name": feature["properties"]["Description"].split("<td>")[1].split("</td>")[0],
            "address": feature["properties"].get("address"),
            "latitude": feature['geometry']['coordinates'][0][0][1] if feature['geometry']['type'] == "Polygon" else feature['geometry']['coordinates'][0][0][0][1],
            "longitude": feature["geometry"]["coordinates"][0][0][0] if feature["geometry"]["type"] == "Polygon" else feature["geometry"]["coordinates"][0][0][0][0]
            }
            for feature in location_data["features"]
        ]

        return sportfacilities
    
    def getHawkerCentres(self):
        dataset_id = "d_4a086da0a5553be1d89383cd90d07ecd"
        url = "https://api-open.data.gov.sg/v1/public/api/datasets/" + dataset_id + "/poll-download"

        response = requests.get(url)
        json_data = response.json()
        if json_data['code'] != 0:
            print(json_data['errMsg'])
            exit(1)

        url = json_data['data']['url']
        location_data = requests.get(url).json()

        hawkers = [
            {
                "name": feature["properties"].get("NAME"),
                "address": feature["properties"].get("address"),
                "latitude": feature["geometry"]["coordinates"][1],
                "longitude": feature["geometry"]["coordinates"][0]
            }
            for feature in location_data["features"]
            if feature["geometry"]["type"] == "Point"
        ]
        return hawkers
    
    def getHealthcareClinics(self):
        dataset_id = "d_548c33ea2d99e29ec63a7cc9edcccedc"
        url = "https://api-open.data.gov.sg/v1/public/api/datasets/" + dataset_id + "/poll-download"

        response = requests.get(url)
        json_data = response.json()
        if json_data['code'] != 0:
            print(json_data['errMsg'])
            exit(1)

        url = json_data['data']['url']
        location_data = requests.get(url).json()

        clinics = [
            {
                "name": feature["properties"]["Description"].split("<td>")[2].split("</td>")[0],
                "latitude": feature["geometry"]["coordinates"][1],
                "longitude": feature["geometry"]["coordinates"][0]
            }
            for feature in location_data["features"]
            if feature["geometry"]["type"] == "Point"
        ]
        return clinics
    
    def getParks(self):
        dataset_id = "d_0542d48f0991541706b58059381a6eca"
        url = "https://api-open.data.gov.sg/v1/public/api/datasets/" + dataset_id + "/poll-download"

        response = requests.get(url)
        json_data = response.json()
        if json_data['code'] != 0:
            print(json_data['errMsg'])
            exit(1)

        url = json_data['data']['url']
        location_data = requests.get(url).json()

        parks = [
            {
                "name": feature["properties"].get("NAME"),
                "latitude": feature["geometry"]["coordinates"][1],
                "longitude": feature["geometry"]["coordinates"][0]
            }
            for feature in location_data["features"]
            if feature["geometry"]["type"] == "Point"
        ]
        return parks
    
    async def getCarparks(self):
        search_results = await self.searchAllPages(query="carpark")
        return search_results

class MemoryWeightsRepo(IWeightsRepo):
    _profiles = [WeightsProfile()]
    def get_active(self) -> WeightsProfile: return self._profiles[0]
    def list(self) -> List[WeightsProfile]: return list(self._profiles)
    def save(self, p: WeightsProfile) -> None: self._profiles.insert(0, p)

class MemoryScoreRepo(IScoreRepo):
    _scores: List[NeighbourhoodScore] = []
    def latest(self, area_id: str, weights_id: str) -> Optional[NeighbourhoodScore]:
        arr = [s for s in self._scores if s.areaId==area_id and s.weightsProfileId==weights_id]
        return arr[-1] if arr else None
    def save(self, s: NeighbourhoodScore) -> None: self._scores.append(s)


class MemoryCommunityRepo(ICommunityRepo):
    """In-memory community centre repo with hardcoded data for now."""
    # Hardcoded community centre records - areaId keys
    _centres: List[CommunityCentre] = [
        CommunityCentre(id="cc1", name="Bukit Panjang CC", areaId="Bukit Panjang", address="123 Fajar Rd", latitude=1.38, longitude=103.77),
        CommunityCentre(id="cc2", name="Tampines CC", areaId="Tampines", address="10 Tampines Ave", latitude=1.35, longitude=103.95),
        CommunityCentre(id="cc3", name="Marine Parade CC", areaId="Marine Parade", address="5 Marine Dr", latitude=1.30, longitude=103.91)
    ]

    def list_all(self) -> List[str]:
        return [c.areaId for c in self._centres]

    def exists(self, area_id: str) -> bool:
        # case-insensitive check
        return any(c.areaId.lower() == area_id.lower() for c in self._centres)
    
    def list_centres(self, area_id: str) -> List[CommunityCentre]:
        return [c for c in self._centres if c.areaId and c.areaId.lower() == area_id.lower()]


class MemoryTransitRepo(ITransitRepo):
    """Hardcoded transit nodes (MRT/LRT/Bus) and simple area mapping."""
    # a few sample transit nodes with lat/lon
    _nodes: List[Transit] = [
        Transit(id="mrt_bukit_panjang", type="mrt", name="Bukit Panjang MRT", areaId="Bukit Panjang", latitude=1.38, longitude=103.77),
        Transit(id="lrt_bukit_panjang", type="lrt", name="Bukit Panjang LRT", areaId="Bukit Panjang", latitude=1.379, longitude=103.771),
        Transit(id="mrt_tampines", type="mrt", name="Tampines MRT", areaId="Tampines", latitude=1.352, longitude=103.94),
        Transit(id="bus_marine_parade_1", type="bus", name="Marine Parade Bus Stop 1", areaId="Marine Parade", latitude=1.3005, longitude=103.9105)
    ]

    def list_near_area(self, area_id: str) -> List[Transit]:
        # return nodes that have matching areaId (case-insensitive), else empty
        return [n for n in self._nodes if n.areaId and n.areaId.lower() == area_id.lower()]

    def all(self) -> List[Transit]:
        return list(self._nodes)


class MemoryCarparkRepo(ICarparkRepo):
    """Hardcoded carparks with capacities and positions."""
    _parks: List[Carpark] = [
        Carpark(id="cp_bukit_panjang_1", areaId="Bukit Panjang", latitude=1.381, longitude=103.772, capacity=200),
        Carpark(id="cp_tampines_1", areaId="Tampines", latitude=1.353, longitude=103.945, capacity=500),
        Carpark(id="cp_marine_1", areaId="Marine Parade", latitude=1.301, longitude=103.911, capacity=120)
    ]

    def list_near_area(self, area_id: str) -> List[Carpark]:
        return [p for p in self._parks if p.areaId and p.areaId.lower() == area_id.lower()]

    def all(self) -> List[Carpark]:
        return list(self._parks)


class MemoryAreaRepo(IAreaRepo):
    dataset_id = "d_4765db0e87b9c86336792efe8a1f7a66"
    url = "https://api-open.data.gov.sg/v1/public/api/datasets/" + dataset_id + "/poll-download"
    response = requests.get(url)
    json_data = response.json()
    if json_data['code'] != 0:
        print(json_data['errMsg'])
        exit(1)

    url = json_data['data']['url']
    location_data = requests.get(url).json()

    """In-memory mapping of areaId -> centroid coordinates."""
    _centroids: List[AreaCentroid] = [
        AreaCentroid(
            areaId=feature["properties"]["Description"].split("<td>")[1].split("</td>")[0].lower(),
            latitude=feature['geometry']['coordinates'][0][0][1] if feature['geometry']['type'] == "Polygon" else feature['geometry']['coordinates'][0][0][0][1],
            longitude=feature['geometry']['coordinates'][0][0][0] if feature['geometry']['type'] == "Polygon" else feature['geometry']['coordinates'][0][0][0][0]
        )
        for feature in location_data['features']
    ]

    def centroid(self, area_id: str) -> AreaCentroid | None:
        for c in self._centroids:
            if c.areaId.lower() == area_id.lower():
                return c
        return None

    def list_all(self) -> List[AreaCentroid]:
        return list(self._centroids)