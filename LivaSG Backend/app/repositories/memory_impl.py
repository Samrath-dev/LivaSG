from datetime import date, datetime
import math
import os
import time
from typing import List, Optional
from ..repositories.interfaces import IRankRepo, ISavedLocationRepo, IPreferenceRepo
from ..domain.models import RankProfile, UserPreference, SavedLocation


import requests
from shapely import MultiPolygon, Point, Polygon

# NEW
from ..cache.paths import cache_file
from ..cache.disk_cache import load_cache, save_cache

from ..domain.models import (
    PriceRecord, FacilitiesSummary, WeightsProfile, NeighbourhoodScore,
    CommunityCentre, Transit, Carpark, AreaCentroid
)
from .interfaces import (
    IPriceRepo, IAmenityRepo, IWeightsRepo, IScoreRepo,
    ICommunityRepo, ITransitRepo, ICarparkRepo, IAreaRepo
)
from ..integrations import onemap_client as onemap

# -------------- Cache helpers & settings --------------

CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "86400"))  # 24h default
DEBUG_AMEN = os.getenv("DEBUG_AMEN", "0") == "1"

def _cache_get(name: str, ttl: Optional[int] = None):
    """
    Return cached payload if exists and is fresh; else None.
    """
    p = cache_file(name, version=1)
    blob = load_cache(p)
    if not blob:
        return None
    meta = blob.get("meta") or {}
    built_at = float(meta.get("built_at", 0))
    max_age = CACHE_TTL_SECONDS if ttl is None else ttl
    if built_at and (time.time() - built_at) <= max_age:
        return blob.get("payload")
    return None

def _cache_put(name: str, payload, extra_meta=None):
    p = cache_file(name, version=1)
    save_cache(p, payload=payload, meta=(extra_meta or {}))

def _fetch_json_cached(cache_name: str, url: str, *, ttl: Optional[int] = None):
    """
    Cache the JSON result of a GET request (for open data endpoints).
    """
    cached = _cache_get(cache_name, ttl=ttl)
    if cached is not None:
        return cached
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    _cache_put(cache_name, data, {"url": url})
    return data

# -------------- Repositories --------------

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
            if m > 12:
                m, y = 1, y+1
        return out


class MemoryAmenityRepo(IAmenityRepo):
    _schools_data = None    # OneMap API
    _sports_data = None     # data.gov.sg
    _hawkers_data = None    # data.gov.sg
    _clinics_data = None    # data.gov.sg
    _parks_data = None      # data.gov.sg
    _carparks_data = None   # not used here (carparks in MemoryCarparkRepo)

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

    def _snapshot_id(self) -> str:
        """
        Lightweight snapshot string used to invalidate per-area summaries
        when upstream datasets change (length-based; cheap & sufficient).
        """
        s = len(self._schools_data or [])
        sp = len(self._sports_data or [])
        h = len(self._hawkers_data or [])
        c = len(self._clinics_data or [])
        p = len(self._parks_data or [])
        return f"s{s}-sp{sp}-h{h}-c{c}-p{p}"

    async def facilities_summary(self, area_id: str) -> FacilitiesSummary:
        await MemoryAmenityRepo.initialize()

        # Per-area cached summary (fast path)
        cache_key = f"fac_summary_{area_id.title()}"
        cached = _cache_get(cache_key, ttl=int(os.getenv("FAC_SUMMARY_TTL", "86400")))
        if cached is not None:
            meta = cached.get("_meta") or {}
            if meta.get("snapshot") == self._snapshot_id():
                # Reconstruct FacilitiesSummary from cached dict
                d = cached["data"]
                return FacilitiesSummary(**d)

        area_repo = MemoryAreaRepo()
        areaPolygon, _areaCentroid = area_repo.getAreaGeometry(area_id)

        cp_repo = MemoryCarparkRepo()
        # (Optional) remove noisy prints of CCs
        # cc_repo = MemoryCommunityRepo()
        # if DEBUG_AMEN:
        #     for cc in cc_repo.list_near_area(area_id):
        #         print(cc.name)

        # Compute fresh
        summary = FacilitiesSummary(
            schools=len(self.filterInside(areaPolygon, self._schools_data)),
            sports=len(self.filterInside(areaPolygon, self._sports_data)),
            hawkers=len(self.filterInside(areaPolygon, self._hawkers_data)),
            healthcare=len(self.filterInside(areaPolygon, self._clinics_data)),
            greenSpaces=len(self.filterInside(areaPolygon, self._parks_data)),
            carparks=len(cp_repo.list_near_area(area_id)),
        )

        # Save to cache
        _cache_put(cache_key, {
            "_meta": {"snapshot": self._snapshot_id()},
            "data": {
                "schools": summary.schools,
                "sports": summary.sports,
                "hawkers": summary.hawkers,
                "healthcare": summary.healthcare,
                "greenSpaces": summary.greenSpaces,
                "carparks": summary.carparks,
            }
        })
        return summary
    
    @staticmethod
    def filterInside(polygon, locations: List[dict]) -> List[dict]:
        if polygon is None or locations is None:
            return []
        inside = []
        for loc in locations:
            try:
                lat = float(loc.get("LATITUDE") or loc.get("latitude"))
                lon = float(loc.get("LONGITUDE") or loc.get("longitude"))
                if polygon.contains(Point(lon, lat)):
                    inside.append(loc)
            except (KeyError, ValueError, TypeError):
                continue
        return inside

    # -------- Cached OneMap search paging --------
    @staticmethod
    async def searchAllPages(query: str) -> List[dict]:
        """
        Cached aggregator across OneMap paging; key is the query string.
        """
        cache_key = f"onemap_search_{query.replace(' ', '_').lower()}"
        cached = _cache_get(cache_key, ttl=int(os.getenv("ONEMAP_SEARCH_TTL", str(7*24*3600))))
        if cached is not None:
            if DEBUG_AMEN:
                print(f"[cache] {query}: {len(cached)} results")
            return cached

        all_results = []
        page = 1
        onemap_client = onemap.OneMapClientHardcoded()

        while True:
            search_results = await onemap_client.search(query=query, page=page)
            if not search_results or "results" not in search_results or not search_results["results"]:
                break
            all_results.extend(search_results["results"])
            if DEBUG_AMEN:
                print(f"Page {page} of {query} loaded")
            page += 1

        _cache_put(cache_key, all_results, {"type": "onemap_search_allpages"})
        return all_results

    # -------- Dataset loaders (cached via _fetch_json_cached) --------
    @staticmethod
    async def getSchools():
        return await MemoryAmenityRepo.searchAllPages(query="school")
    
    @staticmethod
    def getSportFacilities():
        dataset_id = "d_9b87bab59d036a60fad2a91530e10773"
        poll_url = f"https://api-open.data.gov.sg/v1/public/api/datasets/{dataset_id}/poll-download"
        poll_json = _fetch_json_cached("sports_poll", poll_url)
        if poll_json.get('code') != 0:
            print(poll_json.get('errMsg', 'poll-download failed'))
            exit(1)
        data_url = poll_json['data']['url']
        location_data = _fetch_json_cached("sports_dataset", data_url)
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
        poll_url = f"https://api-open.data.gov.sg/v1/public/api/datasets/{dataset_id}/poll-download"
        poll_json = _fetch_json_cached("hawkers_poll", poll_url)
        if poll_json.get('code') != 0:
            print(poll_json.get('errMsg'))
            exit(1)
        data_url = poll_json['data']['url']
        location_data = _fetch_json_cached("hawkers_dataset", data_url)
        return [
            {
                "name": feature["properties"].get("NAME"),
                "address": feature["properties"].get("address"),
                "latitude": feature["geometry"]["coordinates"][1],
                "longitude": feature["geometry"]["coordinates"][0]
            }
            for feature in location_data["features"]
            if feature["geometry"]["type"] == "Point"
        ]

    @staticmethod
    def getChasClinics():
        dataset_id = "d_548c33ea2d99e29ec63a7cc9edcccedc"
        poll_url = f"https://api-open.data.gov.sg/v1/public/api/datasets/{dataset_id}/poll-download"
        poll_json = _fetch_json_cached("chas_poll", poll_url)
        if poll_json.get('code') != 0:
            print(poll_json.get('errMsg'))
            exit(1)
        data_url = poll_json['data']['url']
        location_data = _fetch_json_cached("chas_dataset", data_url)
        return [
            {
                "name": feature["properties"]["Description"].split("<td>")[2].split("</td>")[0],
                "latitude": feature["geometry"]["coordinates"][1],
                "longitude": feature["geometry"]["coordinates"][0]
            }
            for feature in location_data["features"]
            if feature["geometry"]["type"] == "Point"
        ]

    @staticmethod
    def getParks():
        dataset_id = "d_0542d48f0991541706b58059381a6eca"
        poll_url = f"https://api-open.data.gov.sg/v1/public/api/datasets/{dataset_id}/poll-download"
        poll_json = _fetch_json_cached("parks_poll", poll_url)
        if poll_json.get('code') != 0:
            print(poll_json.get('errMsg'))
            exit(1)
        data_url = poll_json['data']['url']
        location_data = _fetch_json_cached("parks_dataset", data_url)
        return [
            {
                "name": feature["properties"].get("NAME"),
                "latitude": feature["geometry"]["coordinates"][1],
                "longitude": feature["geometry"]["coordinates"][0]
            }
            for feature in location_data["features"]
            if feature["geometry"]["type"] == "Point"
        ]


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
        return any(c.areaId and c.areaId.lower() == area_id.lower() for c in self._centres)
    
    def list_near_area(self, area_id: str) -> List[CommunityCentre]:
        return [c for c in self._centres if c.areaId and c.areaId.lower() == area_id.lower()]
    
    @classmethod
    def updateCommunityCentres(cls):
        dataset_id = "d_f706de1427279e61fe41e89e24d440fa"
        poll_url = f"https://api-open.data.gov.sg/v1/public/api/datasets/{dataset_id}/poll-download"
        poll_json = _fetch_json_cached("cc_poll", poll_url)
        if poll_json.get('code') != 0:
            print(poll_json.get('errMsg'))
            exit(1)
        data_url = poll_json['data']['url']
        location_data = _fetch_json_cached("cc_dataset", data_url)

        communitycentres: List[CommunityCentre] = []
        for feature in location_data["features"]:
            if feature["geometry"]["type"] == "Point":
                communitycentres.append(CommunityCentre(
                    id = feature["properties"]['Name'],
                    name = feature["properties"]["Description"].split("<th>NAME</th> <td>")[1].split("</td>")[0],
                    areaId = MemoryAreaRepo.getArea(feature["geometry"]["coordinates"][0], feature["geometry"]["coordinates"][1]),
                    address = feature["properties"]["Description"].split("<th>ADDRESSSTREETNAME</th> <td>")[1].split("</td>")[0] 
                                + " Singapore " 
                                + feature["properties"]["Description"].split("<th>ADDRESSPOSTALCODE</th> <td>")[1].split("</td>")[0],
                    latitude = feature["geometry"]["coordinates"][1],
                    longitude = feature["geometry"]["coordinates"][0]
                ))
        cls._centres = communitycentres


class MemoryTransitRepo(ITransitRepo):
    _transit_data = []  # unused, keeping for compatibility
    _nodes: List[Transit] = [
        # default seed; will be extended/replaced by cached build
        Transit(id="mrt_bukit_panjang", type="mrt", name="Bukit Panjang MRT", areaId="Bukit Panjang", latitude=1.38, longitude=103.77),
        Transit(id="lrt_bukit_panjang", type="lrt", name="Bukit Panjang LRT", areaId="Bukit Panjang", latitude=1.379, longitude=103.771),
        Transit(id="mrt_tampines", type="mrt", name="Tampines MRT", areaId="Tampines", latitude=1.352, longitude=103.94),
        Transit(id="bus_marine_parade_1", type="bus", name="Marine Parade Bus Stop 1", areaId="Marine Parade", latitude=1.3005, longitude=103.9105),
    ]

    def list_near_area(self, area_id: str) -> List[Transit]:
        return [n for n in self._nodes if n.areaId and n.areaId.lower() == area_id.lower()]

    def all(self) -> List[Transit]:
        return list(self._nodes)

    @classmethod
    async def initialize(cls):
        """
        Load transit nodes from cache if available, else build (then cache).
        """
        cache_key = "transit_nodes_v1"
        ttl = int(os.getenv("TRANSIT_TTL", str(7*24*3600)))
        cached = _cache_get(cache_key, ttl=ttl)
        if cached is not None and isinstance(cached, list) and cached:
            # hydrate objects
            cls._nodes = [
                Transit(
                    id=it.get("id"), type=it.get("type"), name=it.get("name"),
                    areaId=it.get("areaId"), latitude=it.get("latitude"), longitude=it.get("longitude")
                ) for it in cached
            ]
            return
        # else build and cache
        await cls.updateTransits()
        _cache_put(cache_key, [
            {
                "id": n.id, "type": n.type, "name": n.name,
                "areaId": n.areaId, "latitude": n.latitude, "longitude": n.longitude
            } for n in cls._nodes
        ], {"source": "onemap_search_mrt"})

    @classmethod
    async def updateTransits(cls):
        """
        Build nodes from OneMap 'MRT' (and later buses); quiet + cached via Amenity search.
        """
        trains = await cls.getTrains()
        buses: List[dict] = []  # placeholder for future LTA DataMall

        built: List[Transit] = []
        for t in trains:
            name = t.get('SEARCHVAL', '')
            if not name:
                continue
            u = name.upper()
            if "EXIT" in u:       # skip exits
                continue
            if "MRT" not in u and "LRT" not in u:
                continue
            try:
                lat = float(t['LATITUDE'])
                lon = float(t['LONGITUDE'])
            except Exception:
                continue
            built.append(Transit(
                id=name,
                type='mrt' if 'MRT' in u else 'lrt' if 'LRT' in u else '',
                name=name,
                areaId=MemoryAreaRepo.getArea(lon, lat),
                latitude=lat,
                longitude=lon
            ))
        # (future) add buses similarly with a cap
        cls._nodes = built or cls._nodes  # keep seeds if nothing built

    @staticmethod
    async def searchAllPages(query: str) -> List[dict]:
        # Reuse the cached OneMap search in MemoryAmenityRepo
        return await MemoryAmenityRepo.searchAllPages(query)
    
    @staticmethod
    async def getTrains():
        return await MemoryAmenityRepo.searchAllPages(query="MRT")
    
    @staticmethod
    async def getBus():
        return await MemoryAmenityRepo.searchAllPages(query="BUS STOP")


class MemoryCarparkRepo(ICarparkRepo):
    _carparks: List[Carpark] = []

    def __init__(self):
        if not MemoryCarparkRepo._carparks:
            MemoryCarparkRepo.updateCarparks()

    def list_near_area(self, area_id: str) -> List[Carpark]:
        return [p for p in self._carparks if p.areaId and p.areaId.lower() == area_id.lower()]

    def list_all(self) -> List[Carpark]:
        return list(self._carparks)
    
    @classmethod
    def updateCarparks(cls):
        # 1) availability (live) — keep uncached to stay current
        avail_url = "https://api.data.gov.sg/v1/transport/carpark-availability"
        response = requests.get(avail_url, timeout=30)
        response.raise_for_status()
        carpark_data = response.json()

        # Initialize carpark lots dictionary
        carpark_lots = {}
        for record in carpark_data["items"][0]["carpark_data"]:
            carpark_number = record["carpark_number"]
            available_lots = 0
            for lots in record["carpark_info"]:
                available_lots += int(lots["lots_available"])
            carpark_lots[carpark_number] = available_lots

        # 2) HDB carpark information (heavy, paginated) — cache combined records
        dataset_id = "d_23f946fa557947f93a8043bbef41dd09" # HDB Carpark Information
        base_url = "https://data.gov.sg/"
        start_url = "api/action/datastore_search?resource_id=" + dataset_id

        records_cache_key = "hdb_carparks_records"
        cached_records = _cache_get(records_cache_key, ttl=int(os.getenv("HDB_CARPARKS_TTL", str(7*24*3600))))
        if cached_records is None:
            curr_url = start_url
            all_records = []
            total = None

            while True:
                url = base_url + curr_url
                resp = requests.get(url, timeout=60)
                resp.raise_for_status()
                location_data = resp.json()
                result = location_data["result"]
                total = result.get("total", total)
                all_records.extend(result.get("records", []))
                if DEBUG_AMEN:
                    print(len(all_records), "/", total, "carparks loaded")
                curr_url = result["_links"]["next"]
                if len(all_records) >= int(total or 0):
                    break

            _cache_put(records_cache_key, all_records, {"dataset": dataset_id, "total": len(all_records)})
            records = all_records
        else:
            records = cached_records

        # Build in-memory objects
        for record in records:
            try:
                easting = float(record['x_coord'])
                northing = float(record['y_coord'])
                lat, lon = svy21_to_wgs84(easting, northing)
                cls._carparks.append(Carpark(
                    id = record['address'],
                    areaId = MemoryAreaRepo.getArea(lon, lat),
                    latitude = lat,
                    longitude = lon,
                    capacity = carpark_lots.get(record.get('car_park_no', ''), 0)
                ))
            except Exception:
                continue


class MemoryAreaRepo(IAreaRepo):
    _polygons = {}
    _centroids = {}

    def __init__(self):
        if not MemoryAreaRepo._polygons:
            MemoryAreaRepo.updateArea()

    @classmethod
    def updateArea(cls):
        dataset_id = "d_4765db0e87b9c86336792efe8a1f7a66"
        poll_url = f"https://api-open.data.gov.sg/v1/public/api/datasets/{dataset_id}/poll-download"

        poll_json = _fetch_json_cached("areas_poll", poll_url)
        if poll_json.get('code') != 0:
            print(poll_json.get('errMsg'))
            exit(1)

        data_url = poll_json['data']['url']
        location_data = _fetch_json_cached("areas_dataset", data_url)

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

            # Calculate centroid
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
            try:
                if polygon.contains(point):
                    area_id = area_name
                    break
            except Exception:
                continue
        return area_id

    @classmethod
    def getAreaGeometry(cls, area_id: str):
        area_id = area_id.title()
        return cls._polygons.get(area_id), cls._centroids.get(area_id)

    @classmethod
    def list_all(cls) -> List[AreaCentroid]:
        return list(cls._centroids)


# Convert X Y to Latitude Longitude
def svy21_to_wgs84(E, N):
    # Constants
    a = 6378137.0
    f = 1 / 298.257223563
    e2 = 2*f - f**2
    phi0 = math.radians(1 + 22/60 + 0/3600)
    lambda0 = math.radians(103 + 50/60 + 0/3600)
    k0 = 1.0
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


class MemoryRankRepo(IRankRepo):
    _active: RankProfile | None = None

    def get_active(self) -> RankProfile | None:
        return MemoryRankRepo._active

    def set(self, r: RankProfile) -> None:
        MemoryRankRepo._active = r

    def clear(self) -> None:
        MemoryRankRepo._active = None

class MemoryPreferenceRepo(IPreferenceRepo):
    _preference: Optional[UserPreference]=None

    def get_preference(self)->Optional[UserPreference]:
        return self._preference
    
    def save_preference(self, preference: UserPreference)-> None:
        preference.updated_at=lambda: datetime.now()
        self._preference= preference
    
    def delete_preference(self, preference: UserPreference)->None:
        self._preference = None

class MemorySavedLocationRepo(ISavedLocationRepo):
    _locations: List[SavedLocation]=[]
    def get_saved_locations(self)->List[SavedLocation]:
        return self._locations.copy()
    
    def saved_location(self,location: SavedLocation)->None:
        self._locations=[loc for loc in self._locations if loc.postal_code != location.postal_code]
        self._locations.append(location)

    def delete_location(self, postal_code: str)->None:
        self._locations=[loc for loc in self._locations if loc.postal_code != postal_code]
    
    def get_location(self, postal_code:str)-> Optional[SavedLocation]:
        for location in self._locations:
            if location.postal_code == postal_code:
                return location
        return None