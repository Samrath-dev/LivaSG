# app/repositories/memory_impl.py
from __future__ import annotations

# stdlib
import csv
import math
import os
import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from statistics import median
from typing import DefaultDict, Dict, List, Optional, Tuple


try:
   
    from ..cache.paths import PROJECT_ROOT
except Exception:
    PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _norm_town(s: str) -> str:
    return (s or "").strip().upper()

def _parse_month(s: str) -> date:
    y, m = s.strip().split("-", 1)
    return date(int(y), int(m), 1)

# third-party
import requests
from shapely.geometry import Point, Polygon, MultiPolygon  # FIXED import path for shapely v2

# local cache utils
from ..cache.paths import PROJECT_ROOT, cache_file
from ..cache.disk_cache import (
    load_cache, save_cache,
    save_cache_with_manifest, try_load_valid_cache, hash_sources
)

# domain + interfaces
from ..domain.models import (
    PriceRecord, FacilitiesSummary, WeightsProfile, NeighbourhoodScore,
    CommunityCentre, Transit, Carpark, AreaCentroid, RankProfile,
    UserPreference, SavedLocation
)
from .interfaces import (
    IPriceRepo, IAmenityRepo, IWeightsRepo, IScoreRepo,
    ICommunityRepo, ITransitRepo, ICarparkRepo, IAreaRepo, IRankRepo,
    ISavedLocationRepo, IPreferenceRepo
)
from ..integrations import onemap_client as onemap


# --------------------------------------------------------------------------------------
# General cache helpers
# --------------------------------------------------------------------------------------
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "86400"))  # 24h default
DEBUG_AMEN = os.getenv("DEBUG_AMEN", "0") == "1"

def _cache_get(name: str, ttl: Optional[int] = None):
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
    cached = _cache_get(cache_name, ttl=ttl)
    if cached is not None:
        return cached
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    _cache_put(cache_name, data, {"url": url})
    return data


# --------------------------------------------------------------------------------------
# CSV-backed resale price index (for MemoryPriceRepo)
# --------------------------------------------------------------------------------------
def _percentile(sorted_vals: List[float], q: float) -> Optional[float]:
    if not sorted_vals:
        return None
    n = len(sorted_vals)
    if n == 1:
        return float(sorted_vals[0])
    idx = q * (n - 1)
    lo = int(idx)
    hi = min(lo + 1, n - 1)
    frac = idx - lo
    return float(sorted_vals[lo] * (1 - frac) + sorted_vals[hi] * frac)

def _parse_month(s: str) -> date:
    y, m = s.strip().split("-", 1)
    return date(int(y), int(m), 1)

def _normalize_area_name(s: str) -> str:
    return (s or "").strip().upper()

def _load_or_build_price_index(csv_path: Path):
    """
    Build and cache:
      { TOWN_UPPER: [ {month:(y,m), median,p25,p75,volume}, ... ] }
    """
    cache_path = cache_file("resale_prices_index", version=1)
    manifest = hash_sources([csv_path])

    cached = try_load_valid_cache(cache_path, manifest)
    if cached is not None:
        return cached

    if not csv_path.exists():
        save_cache_with_manifest(cache_path, manifest, {}, meta={"reason": "csv_missing"})
        return {}

    buckets: Dict[Tuple[str, date], List[float]] = defaultdict(list)
    with csv_path.open("r", newline="", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        for row in rdr:
            town = _normalize_area_name(row.get("town", ""))
            month_str = row.get("month")
            price_str = row.get("resale_price") or row.get("price")
            if not (town and month_str and price_str):
                continue
            try:
                d = _parse_month(month_str)
                p = float(str(price_str).replace(",", ""))
            except Exception:
                continue
            buckets[(town, d)].append(p)

    out: Dict[str, List[Dict[str, float]]] = defaultdict(list)
    per_town: Dict[str, List[Tuple[date, List[float]]]] = defaultdict(list)
    for (town, d), vals in buckets.items():
        per_town[town].append((d, vals))

    for town, items in per_town.items():
        items.sort(key=lambda x: x[0])
        for d, vals in items:
            vals_sorted = sorted(vals)
            med = float(median(vals_sorted))
            p25 = _percentile(vals_sorted, 0.25) or med
            p75 = _percentile(vals_sorted, 0.75) or med
            out[town].append({
                "month": (d.year, d.month),
                "median": med,
                "p25": p25,
                "p75": p75,
                "volume": len(vals_sorted),
            })

    save_cache_with_manifest(cache_path, manifest, out, meta={"source": str(csv_path)})
    return out


# --------------------------------------------------------------------------------------
# Repositories
# --------------------------------------------------------------------------------------
class MemoryPriceRepo(IPriceRepo):
    """
    Reads a CSV once into memory. Falls back to the old synthetic series
    if the town has no rows or the CSV is missing.
    """
    def __init__(self):
        # 1) Resolve path (env wins, else app/data/resale_2017_onwards.csv)
        env_path = os.getenv("RESALE_CSV_PATH")
        self._csv_path = Path(env_path).expanduser() if env_path else (PROJECT_ROOT / "data" / "resale_2017_onwards.csv")
        self._by_town = self._build_index(self._csv_path)
    @staticmethod
    def _build_index(csv_path: Path) -> dict[str, list[tuple[date, float, int]]]:
        """
        Return: { 'TAMPINES': [(date, median_price, volume), ...], ... }
        """
        out: dict[str, list[tuple[date, float, int]]] = {}
        if not csv_path.exists():
            return out

        # Aggregate prices per (town, month)
        buckets = defaultdict(list)  # (town, month_date) -> [prices]

        with csv_path.open("r", newline="", encoding="utf-8") as f:
            rdr = csv.DictReader(f)
            for row in rdr:
                # Normalize keys to lowercase and strip whitespace
                row = {
                    k.strip().lower(): (v.strip() if isinstance(v, str) else v)
                    for k, v in row.items()
                }

                town = _norm_town(row.get("town"))
                month_s = row.get("month")
                price_s = row.get("resale_price")

                if not (town and month_s and price_s):
                    continue

                try:
                    d = _parse_month(month_s)
                    p =float(str(price_s).replace(",", ""))
                except Exception:
                    continue

                buckets[(town, d)].append(p)

        per_town = defaultdict(list)
        for (town, d), vals in buckets.items():
            vals.sort()
            per_town[town].append((d, vals))

        for town, items in per_town.items():
            items.sort(key=lambda x: x[0])
            series = []
            for d, vals in items:
                med = median(vals)
                series.append((d, med, len(vals)))
            out[town] = series

        print(f"[PriceRepo] Loaded {sum(len(v) for v in out.values())} months across {len(out)} towns")
        return out
 

    def series(self, area_id: str, months: int) -> List[PriceRecord]:
        key = _norm_town(area_id)
        rows = self._by_town.get(key, [])
        if rows:
            tail = rows[-months:] if months > 0 else rows[:]
            return [
                PriceRecord(
                    areaId=area_id,
                    month=d,
                    medianResale=int(round(med)),
                    # quick fill for now; extend later if needed
                    p25=int(round(med)),
                    p75=int(round(med)),
                    volume=vol,
                )
                for (d, med, vol) in tail
            ]

        # Fallback (keeps app working if mapping/town mismatch)
        base = 520_000 if key == "TAMPINES" else 500_000
        out: List[PriceRecord] = []
        y, m = 2024, 1
        for i in range(max(1, months)):
            out.append(PriceRecord(
                areaId=area_id,
                month=date(y, m, 1),
                medianResale=base + i * 1200,
                p25=base - 40_000,
                p75=base + 40_000,
                volume=50 - (i % 5),
            ))
            m += 1
            if m > 12:
                m, y = 1, y + 1
        return out

class MemoryAmenityRepo(IAmenityRepo):
    _schools_data = None
    _sports_data = None
    _hawkers_data = None
    _clinics_data = None
    _parks_data = None

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
        s = len(self._schools_data or [])
        sp = len(self._sports_data or [])
        h = len(self._hawkers_data or [])
        c = len(self._clinics_data or [])
        p = len(self._parks_data or [])
        return f"s{s}-sp{sp}-h{h}-c{c}-p{p}"

    async def facilities_summary(self, area_id: str) -> FacilitiesSummary:
        await MemoryAmenityRepo.initialize()

        cache_key = f"fac_summary_{area_id.title()}"
        cached = _cache_get(cache_key, ttl=int(os.getenv("FAC_SUMMARY_TTL", "86400")))
        if cached is not None:
            meta = cached.get("_meta") or {}
            if meta.get("snapshot") == self._snapshot_id():
                d = cached["data"]
                return FacilitiesSummary(**d)

        area_repo = MemoryAreaRepo()
        areaPolygon, _areaCentroid = area_repo.getAreaGeometry(area_id)

        cp_repo = MemoryCarparkRepo()

        summary = FacilitiesSummary(
            schools=len(self.filterInside(areaPolygon, self._schools_data)),
            sports=len(self.filterInside(areaPolygon, self._sports_data)),
            hawkers=len(self.filterInside(areaPolygon, self._hawkers_data)),
            healthcare=len(self.filterInside(areaPolygon, self._clinics_data)),
            greenSpaces=len(self.filterInside(areaPolygon, self._parks_data)),
            carparks=len(cp_repo.list_near_area(area_id)),
        )

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

    # ----- Cached OneMap search paging -----
    @staticmethod
    async def searchAllPages(query: str) -> List[dict]:
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

    # ----- Datasets (via data.gov.sg poll-download) -----
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
        return [
            {
                "name": f["properties"]["Description"].split("<td>")[1].split("</td>")[0],
                "address": f["properties"].get("address"),
                "latitude": f['geometry']['coordinates'][0][0][1] if f['geometry']['type'] == "Polygon" else f['geometry']['coordinates'][0][0][0][1],
                "longitude": f["geometry"]["coordinates"][0][0][0] if f["geometry"]["type"] == "Polygon" else f["geometry"]["coordinates"][0][0][0][0]
            }
            for f in location_data["features"]
        ]

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
                "name": f["properties"].get("NAME"),
                "address": f["properties"].get("address"),
                "latitude": f["geometry"]["coordinates"][1],
                "longitude": f["geometry"]["coordinates"][0]
            }
            for f in location_data["features"] if f["geometry"]["type"] == "Point"
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
                "name": f["properties"]["Description"].split("<td>")[2].split("</td>")[0],
                "latitude": f["geometry"]["coordinates"][1],
                "longitude": f["geometry"]["coordinates"][0]
            }
            for f in location_data["features"] if f["geometry"]["type"] == "Point"
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
                "name": f["properties"].get("NAME"),
                "latitude": f["geometry"]["coordinates"][1],
                "longitude": f["geometry"]["coordinates"][0]
            }
            for f in location_data["features"] if f["geometry"]["type"] == "Point"
        ]


class MemoryWeightsRepo(IWeightsRepo):
    _profiles = [WeightsProfile()]
    def get_active(self) -> WeightsProfile: return self._profiles[0]
    def list(self) -> List[WeightsProfile]: return list(self._profiles)
    def save(self, p: WeightsProfile) -> None: self._profiles.insert(0, p)


class MemoryScoreRepo(IScoreRepo):
    _scores: List[NeighbourhoodScore] = []
    def latest(self, area_id: str, weights_id: str) -> Optional[NeighbourhoodScore]:
        arr = [s for s in self._scores if s.areaId == area_id and s.weightsProfileId == weights_id]
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
            if feature["geometry"]["type"] != "Point":
                continue
            try:
                name = feature["properties"]["Description"].split("<th>NAME</th> <td>")[1].split("</td>")[0]
            except Exception:
                name = feature["properties"].get('Name')
            communitycentres.append(CommunityCentre(
                id=feature["properties"]['Name'],
                name=name,
                areaId=MemoryAreaRepo.getArea(feature["geometry"]["coordinates"][0], feature["geometry"]["coordinates"][1]),
                address=feature["properties"]["Description"].split("<th>ADDRESSSTREETNAME</th> <td>")[1].split("</td>")[0]
                        + " Singapore "
                        + feature["properties"]["Description"].split("<th>ADDRESSPOSTALCODE</th> <td>")[1].split("</td>")[0],
                latitude=feature["geometry"]["coordinates"][1],
                longitude=feature["geometry"]["coordinates"][0]
            ))
        cls._centres = communitycentres


class MemoryTransitRepo(ITransitRepo):
    _nodes: List[Transit] = [
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
        cache_key = "transit_nodes_v1"
        ttl = int(os.getenv("TRANSIT_TTL", str(7*24*3600)))
        cached = _cache_get(cache_key, ttl=ttl)
        if cached and isinstance(cached, list):
            cls._nodes = [
                Transit(
                    id=it.get("id"),
                    type=it.get("type"),
                    name=it.get("name"),
                    areaId=it.get("areaId"),
                    latitude=it.get("latitude"),
                    longitude=it.get("longitude"),
                ) for it in cached
            ]
            return
        await cls.updateTransits()
        _cache_put(cache_key, [
            {
                "id": n.id, "type": n.type, "name": n.name,
                "areaId": n.areaId, "latitude": n.latitude, "longitude": n.longitude
            } for n in cls._nodes
        ], {"source": "onemap_search_mrt"})

    @classmethod
    async def updateTransits(cls):
        trains = await MemoryAmenityRepo.searchAllPages(query="MRT")
        built: List[Transit] = []
        for t in trains:
            name = t.get('SEARCHVAL', '')
            if not name:
                continue
            u = name.upper()
            if "EXIT" in u:
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
        cls._nodes = built or cls._nodes

    @staticmethod
    async def getBus():
        # placeholder for LTA DataMall integration
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
        # 1) live availability
        avail_url = "https://api.data.gov.sg/v1/transport/carpark-availability"
        response = requests.get(avail_url, timeout=30)
        response.raise_for_status()
        carpark_data = response.json()

        carpark_lots: Dict[str, int] = {}
        for rec in carpark_data["items"][0]["carpark_data"]:
            cp_no = rec["carpark_number"]
            total = 0
            for lots in rec["carpark_info"]:
                total += int(lots["lots_available"])
            carpark_lots[cp_no] = total

        # 2) static info (heavy, paginate) – cached
        dataset_id = "d_23f946fa557947f93a8043bbef41dd09"
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
                payload = resp.json()
                result = payload["result"]
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

        for record in records:
            try:
                easting = float(record['x_coord'])
                northing = float(record['y_coord'])
                lat, lon = svy21_to_wgs84(easting, northing)
                cls._carparks.append(Carpark(
                    id=record['address'],
                    areaId=MemoryAreaRepo.getArea(lon, lat),
                    latitude=lat,
                    longitude=lon,
                    capacity=carpark_lots.get(record.get('car_park_no', ''), 0)
                ))
            except Exception:
                continue


class MemoryAreaRepo(IAreaRepo):
    _polygons: Dict[str, Polygon | MultiPolygon] = {}
    _centroids: Dict[str, AreaCentroid] = {}

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

        for feature in location_data['features']:
            area_name = feature["properties"]["Description"].split("<td>")[1].split("</td>")[0].title()
            geom = feature['geometry']
            gtype = geom['type']

            if gtype == "MultiPolygon":
                polygons = []
                for polygon_coords in geom['coordinates']:
                    for ring in polygon_coords:
                        polygons.append(Polygon(ring))
                cls._polygons[area_name] = MultiPolygon(polygons)
            elif gtype == "Polygon":
                cls._polygons[area_name] = Polygon(geom['coordinates'][0])

            # centroid
            coords = []
            if gtype == "MultiPolygon":
                for polygon_coords in geom['coordinates']:
                    for ring in polygon_coords:
                        coords.extend(ring)
            elif gtype == "Polygon":
                for ring in geom['coordinates']:
                    coords.extend(ring)

            if coords:
                avg_lon = sum(c[0] for c in coords) / len(coords)
                avg_lat = sum(c[1] for c in coords) / len(coords)
                cls._centroids[area_name] = AreaCentroid(areaId=area_name, latitude=avg_lat, longitude=avg_lon)

    @classmethod
    def getArea(cls, longitude: float, latitude: float) -> str:
        if not cls._polygons:
            cls.updateArea()
        point = Point(longitude, latitude)
        for area_name, polygon in cls._polygons.items():
            try:
                if polygon.contains(point):
                    return area_name
            except Exception:
                continue
        return "None"

    @classmethod
    def getAreaGeometry(cls, area_id: str):
        area_id = area_id.title()
        return cls._polygons.get(area_id), cls._centroids.get(area_id)

    @classmethod
    def list_all(cls) -> List[AreaCentroid]:
        return list(cls._centroids.values())


# --------------------------------------------------------------------------------------
# Utilities
# --------------------------------------------------------------------------------------
def svy21_to_wgs84(E, N):
    a = 6378137.0
    f = 1 / 298.257223563
    e2 = 2*f - f**2
    phi0 = math.radians(1 + 22/60 + 0/3600)
    lambda0 = math.radians(103 + 50/60 + 0/3600)
    k0 = 1.0
    N0 = 38744.572
    E0 = 28001.642

    M = (N - N0) / k0
    phi = phi0 + M / (a * (1 - e2/4 - 3*e2**2/64 - 5*e2**3/256))
    nu = a / math.sqrt(1 - e2 * math.sin(phi)**2)
    rho = a * (1 - e2) / (1 - e2 * math.sin(phi)**2)**1.5
    eta2 = nu / rho - 1
    dE = E - E0

    phi_lat = phi - (math.tan(phi) / (2 * rho * nu)) * dE**2 \
                   + (math.tan(phi) / (24 * rho * nu**3)) * (5 + 3*math.tan(phi)**2 + eta2 - 9*math.tan(phi)**2*eta2) * dE**4
    lambda_lon = lambda0 + (1 / (math.cos(phi) * nu)) * dE \
                        - (1 / (6 * math.cos(phi) * nu**3)) * (nu/rho + 2*math.tan(phi)**2) * dE**3

    lat = math.degrees(phi_lat)
    lon = math.degrees(lambda_lon)
    return lat, lon


# --------------------------------------------------------------------------------------
# Ranks (user priorities) in-memory repo
# --------------------------------------------------------------------------------------
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
    
    def delete_preference(self)->None:
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
