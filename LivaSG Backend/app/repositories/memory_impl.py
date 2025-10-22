from datetime import date
import math
from typing import List, Optional

import requests
from shapely import MultiPolygon, Point, Polygon

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
    _schools_data = None    # 724 schools in Singapore #uses OneMap API
    _sports_data = None     # 35 sports facilities in Singapore
    _hawkers_data = None    # 129 hawker centres in Singapore
    _clinics_data = None    # 1193 CHAS clinics in Singapore
    _parks_data = None      # 441 parks in Singapore
    _carparks_data = None   # 2249 carparks in Singapore

    @classmethod
    async def initialize(cls):
        if cls._schools_data is None:
            cls._schools_data = await cls.getSchools()
        if cls._sports_data is None:
            cls._sports_data = cls.getSportFacilities()
        if cls._hawkers_data is None:
            cls._hawkers_data = cls.getHawkerCentres()
        if cls._clinics_data is None:
            cls._clinics_data = cls.getChasClinics()
        if cls._parks_data is None:
            cls._parks_data = cls.getParks()

    async def facilities_summary(self, area_id: str) -> FacilitiesSummary:
        await MemoryAmenityRepo.initialize()

        area_repo = MemoryAreaRepo()
        areaPolygon, areaCentroid = area_repo.getAreaGeometry(area_id)

        cp_repo = MemoryCarparkRepo()
        cc_repo = MemoryCommunityRepo()

        # for testing purposes
        for cc in cc_repo.list_near_area(area_id):
            print(cc.name)

        return FacilitiesSummary(   
            schools=len(self.filterInside(areaPolygon, self._schools_data)),
            sports=len(self.filterInside(areaPolygon, MemoryAmenityRepo._sports_data)),
            hawkers=len(self.filterInside(areaPolygon, MemoryAmenityRepo._hawkers_data)),
            healthcare=len(self.filterInside(areaPolygon, MemoryAmenityRepo._clinics_data)),
            greenSpaces=len(self.filterInside(areaPolygon, MemoryAmenityRepo._parks_data)), 
            carparks=len(cp_repo.list_near_area(area_id)),
        )
    
    @staticmethod
    def filterInside(polygon, locations: List[dict]) -> List[dict]:
        if locations is None:
            return []
        
        inside_locations = []
        for loc in locations:
            try:
                loc_lat = float(loc.get("LATITUDE") or loc.get("latitude"))
                loc_lon = float(loc.get("LONGITUDE") or loc.get("longitude"))
                point = Point(loc_lon, loc_lat)  # Create a shapely Point (longitude first)

                if polygon.contains(point):
                    inside_locations.append(loc)
                    #print(loc['SEARCHVAL'] if 'SEARCHVAL' in loc else loc.get('name', 'Unknown')) #for debugging

            except (KeyError, ValueError):
                continue  # Skip locations with missing or invalid coordinates
        return inside_locations

    # Search all pages for a given query for OneMap API
    @staticmethod
    async def searchAllPages(query: str) -> List[dict]:
        all_results = []
        page = 1
        onemap_client = onemap.OneMapClientHardcoded()

        while True:
            search_results = await onemap_client.search(query=query, page=page)

            if not search_results or "results" not in search_results or len(search_results["results"]) == 0:
                break  # No more results
            all_results.extend(search_results["results"])
            print(f"Page {page} of {query} loaded") #for debugging
            page += 1
        return all_results

    @staticmethod
    async def getSchools():
        # Use OneMap Search API to find nearby schools
        search_results = await MemoryAmenityRepo.searchAllPages(query="school")
        return search_results
    
    @staticmethod
    def getSportFacilities():
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

    @staticmethod
    def getHawkerCentres():
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

    @staticmethod
    def getChasClinics():
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

    @staticmethod
    def getParks():
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
    _centres: List[CommunityCentre] = []

    def __init__(self):
        if not MemoryCommunityRepo._centres:
            MemoryCommunityRepo.updateCommunityCentres()

    def list_all(self) -> List[str]:
        return [c.name for c in self._centres]

    def exists(self, area_id: str) -> bool:
        # case-insensitive check
        return any(c.areaId.lower() == area_id.lower() for c in self._centres)
    
    def list_near_area(self, area_id: str) -> List[CommunityCentre]:
        return [c for c in self._centres if c.areaId and c.areaId.lower() == area_id.lower()]
    
    @classmethod
    def updateCommunityCentres(cls):
        dataset_id = "d_f706de1427279e61fe41e89e24d440fa"
        url = "https://api-open.data.gov.sg/v1/public/api/datasets/" + dataset_id + "/poll-download"

        response = requests.get(url)
        json_data = response.json()
        if json_data['code'] != 0:
            print(json_data['errMsg'])
            exit(1)

        url = json_data['data']['url']
        location_data = requests.get(url).json()

        communitycentres = []

        for feature in location_data["features"]:
            if feature["geometry"]["type"] == "Point":
                community_centre = CommunityCentre(
                    id = feature["properties"]['Name'],
                    name = feature["properties"]["Description"].split("<th>NAME</th> <td>")[1].split("</td>")[0],
                    areaId = MemoryAreaRepo.getArea(feature["geometry"]["coordinates"][0], feature["geometry"]["coordinates"][1]),
                    address = feature["properties"]["Description"].split("<th>ADDRESSSTREETNAME</th> <td>")[1].split("</td>")[0] 
                                + " Singapore " 
                                + feature["properties"]["Description"].split("<th>ADDRESSPOSTALCODE</th> <td>")[1].split("</td>")[0],
                    latitude = feature["geometry"]["coordinates"][1],
                    longitude = feature["geometry"]["coordinates"][0]
                    )
                communitycentres.append(community_centre)
        cls._centres = communitycentres


#TODO WIP, doesnt work, and need add initialization
class MemoryTransitRepo(ITransitRepo):
    _transit_data = []
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
    
    @classmethod
    async def updateTransits(cls):
        _trains = await cls.getTrains()
        _buses = []
        #_buses = await cls.getBus() #need to change to LTA DATAMALL API

        for train in _trains: 
            if "EXIT" in train['SEARCHVAL']: #skip exits
                continue

            if "MRT" not in train['SEARCHVAL'].upper() and "LRT" not in train['SEARCHVAL'].upper(): #skip non-MRT/LRT
                continue

            if "LRT" in train['SEARCHVAL']:
                print(train["SEARCHVAL"] + " LRT")
    
            transit_node = Transit(
                id = train['SEARCHVAL'],
                type = 'mrt' if 'MRT' in train['SEARCHVAL'].upper() else 'lrt' if 'LRT' in train['SEARCHVAL'].upper() else '',
                name = train['SEARCHVAL'],
                areaId = MemoryAreaRepo.getArea(float(train['LONGITUDE']), float(train['LATITUDE'])),
                latitude = float(train['LATITUDE']),
                longitude = float(train['LONGITUDE'])
            )
            cls._nodes.append(transit_node)

        for bus in _buses: #TODO rmb to update this 
            print(bus["SEARCHVAL"] + " BUS STOP")
            transit_node = Transit(
                id = bus['SEARCHVAL'],
                type = 'bus',
                name = bus['SEARCHVAL'],
                areaId = MemoryAreaRepo.getArea(float(bus['LONGITUDE']), float(bus['LATITUDE'])),
                latitude = float(bus['LATITUDE']),
                longitude = float(bus['LONGITUDE'])
            )
            cls._nodes.append(transit_node)

    @staticmethod
    async def searchAllPages(query: str) -> List[dict]:
        all_results = []
        page = 1
        onemap_client = onemap.OneMapClientHardcoded()

        while True:
            search_results = await onemap_client.search(query=query, page=page)

            if not search_results or "results" not in search_results or len(search_results["results"]) == 0:
                break  # No more results
            all_results.extend(search_results["results"])
            print(f"Page {page} of {query} loaded")
            page += 1
        return all_results
    
    @staticmethod
    async def getTrains(): #try find another way
        search_results = await MemoryAmenityRepo.searchAllPages(query="MRT")
        return search_results
    
    @staticmethod
    async def getBus(): #need to change to LTA DATAMALL API or something
        search_results = await MemoryAmenityRepo.searchAllPages(query="BUS STOP")
        return search_results


class MemoryCarparkRepo(ICarparkRepo):
    _carparks: List[Carpark] = []

    def __init__(self):
        if not MemoryCarparkRepo._carparks:
            MemoryCarparkRepo.updateCarparks()
            pass

    def list_near_area(self, area_id: str) -> List[Carpark]:
        return [p for p in self._carparks if p.areaId and p.areaId.lower() == area_id.lower()]

    def list_all(self) -> List[Carpark]:
        return list(self._carparks)
    
    @classmethod
    def updateCarparks(cls):
        # Fetch carpark availability data
        url = "https://api.data.gov.sg/v1/transport/carpark-availability"
        response = requests.get(url)
        carpark_data = response.json()

        # Initialize carpark lots dictionary
        carpark_lots = {}

        # iterate through carpark availability data
        for record in carpark_data["items"][0]["carpark_data"]:
            carpark_number = record["carpark_number"]
            available_lots = 0

            # Sum up available lots across all lot types
            for lots in record["carpark_info"]:
                available_lots += int(lots["lots_available"])
            
            # Add to dictionary
            carpark_lots[carpark_number] = available_lots

        # Now fetch HDB carpark information to get names and coordinates
        dataset_id = "d_23f946fa557947f93a8043bbef41dd09" #HDB Carpark Information
        base_url = "https://data.gov.sg/"
        curr_url = "api/action/datastore_search?resource_id=" + dataset_id

        while True:
            url = base_url + curr_url
            response = requests.get(url)
            location_data = response.json()
            curr_url = location_data["result"]["_links"]["next"]

            print(len(cls._carparks), "/", location_data["result"]["total"], "carparks loaded")
            if len(cls._carparks) >= int(location_data["result"]["total"]):
                break  # Exit if we've reached the max number of carparks

            for record in location_data["result"]["records"]:
                easting = float(record['x_coord'])
                northing = float(record['y_coord'])
                lat, lon = svy21_to_wgs84(easting, northing)

                carpark = Carpark(
                    id = record['address'],
                    areaId = MemoryAreaRepo.getArea(lon, lat),
                    latitude = lat,
                    longitude = lon,
                    capacity = carpark_lots.get(record['car_park_no'], 0)
                )
                
                cls._carparks.append(carpark)


class MemoryAreaRepo(IAreaRepo):
    _polygons = {}
    _centroids = {}

    def __init__(self):
        if not MemoryAreaRepo._polygons:
            MemoryAreaRepo.updateArea()

    @classmethod
    def updateArea(cls):
        dataset_id = "d_4765db0e87b9c86336792efe8a1f7a66"
        url = "https://api-open.data.gov.sg/v1/public/api/datasets/" + dataset_id + "/poll-download"
        response = requests.get(url)
        json_data = response.json()
        if json_data['code'] != 0:
            print(json_data['errMsg'])
            exit(1)

        url = json_data['data']['url']
        location_data = requests.get(url).json()
        
        # Convert geojson to Polygon or MultiPolygon
        for feature in location_data['features']:
            area_name = feature["properties"]["Description"].split("<td>")[1].split("</td>")[0].title()

            if feature['geometry']['type'] == "MultiPolygon":
                polygons = []
                for polygon_coords in feature['geometry']['coordinates']:
                    for ring in polygon_coords:
                        polygons.append(Polygon(ring))
                cls._polygons[area_name] = MultiPolygon(polygons)
            
            elif feature['geometry']['type'] == "Polygon":
                cls._polygons[area_name] = Polygon(feature['geometry']['coordinates'][0])

        # Calculate centroid from polygon coordinates
            coords = []
            if feature['geometry']['type'] == "MultiPolygon":
                for polygon_coords in feature['geometry']['coordinates']:
                    for ring in polygon_coords:
                        coords.extend(ring)
            elif feature['geometry']['type'] == "Polygon":
                for ring in feature['geometry']['coordinates']:
                    coords.extend(ring)

            if coords:
                avg_lon = sum(c[0] for c in coords) / len(coords)
                avg_lat = sum(c[1] for c in coords) / len(coords)
                cls._centroids[area_name] = AreaCentroid(
                    areaId=area_name, latitude=avg_lat, longitude=avg_lon
                )

    @classmethod
    def getArea(cls, longitude: float, latitude: float) -> str:
        if not cls._polygons:
            cls.updateArea()

        area_id = "None"
        point = Point(longitude, latitude)

        for area_name, polygon in cls._polygons.items():
            if polygon.contains(point):
                area_id = area_name
                break

        return area_id

    @classmethod
    def getAreaGeometry(cls, area_id: str): #returns the polygon and centroid for a given area ID
        area_id = area_id.title()
        return cls._polygons.get(area_id), cls._centroids.get(area_id)

    @classmethod
    def list_all(cls) -> List[AreaCentroid]: #TODO update this
        return list(cls._centroids)


# Convert X Y to Latitude Longitude
def svy21_to_wgs84(E, N):
    # Constants
    a = 6378137.0  # semi-major axis
    f = 1 / 298.257223563  # flattening
    e2 = 2*f - f**2  # eccentricity squared
    phi0 = math.radians(1 + 22/60 + 0/3600)  # reference latitude in radians
    lambda0 = math.radians(103 + 50/60 + 0/3600)  # reference longitude in radians
    k0 = 1.0  # scale factor
    N0 = 38744.572
    E0 = 28001.642

    # Meridional arc
    M = (N - N0) / k0

    # Footprint latitude
    phi = phi0 + M / (a * (1 - e2/4 - 3*e2**2/64 - 5*e2**3/256))

    # Radii of curvature
    nu = a / math.sqrt(1 - e2 * math.sin(phi)**2)
    rho = a * (1 - e2) / (1 - e2 * math.sin(phi)**2)**1.5
    eta2 = nu / rho - 1

    # Delta Easting
    dE = E - E0

    # Latitude series
    phi_lat = phi - (math.tan(phi) / (2 * rho * nu)) * dE**2 \
                   + (math.tan(phi) / (24 * rho * nu**3)) * (5 + 3*math.tan(phi)**2 + eta2 - 9*math.tan(phi)**2*eta2) * dE**4

    # Longitude series
    lambda_lon = lambda0 + (1 / (math.cos(phi) * nu)) * dE \
                        - (1 / (6 * math.cos(phi) * nu**3)) * (nu/rho + 2*math.tan(phi)**2) * dE**3

    # Convert to degrees
    lat = math.degrees(phi_lat)
    lon = math.degrees(lambda_lon)

    return lat, lon