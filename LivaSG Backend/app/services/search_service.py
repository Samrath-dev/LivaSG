from typing import List
from ..domain.models import NeighbourhoodScore, WeightsProfile, SearchFilters, LocationResult, OneMapSearchResponse
from .rating_engine import RatingEngine
from ..integrations.onemap_client import OneMapClientHardcoded

class SearchService:
    def __init__(self, engine: RatingEngine, onemap_client: OneMapClientHardcoded = None): 
        self.engine = engine
        self.onemap_client = onemap_client or OneMapClientHardcoded()
        self._initialize_location_data()

    def rank(self, areas: List[str], weights: WeightsProfile) -> List[NeighbourhoodScore]:
        scores = [self.engine.aggregate(a, weights) for a in areas]
        return sorted(scores, key=lambda s: s.total, reverse=True)
    
    def _initialize_location_data(self):
        """No longer used. All local locations are loaded from onemap_locations.json."""
        pass

    async def filter_locations(self, filters: SearchFilters, view_type: str = "street") -> List[LocationResult]:
        """
        Filter locations based on search query and filters:
        - If search_query exists: Use OneMap search API and check "found" count:
          - found == 0: Return nothing
          - found == 1: Return this specific location
          - found > 1: Return street names from street_geocode.db (if view_type="street")
                       or planning areas (if view_type="planning_area")
        - If no search_query: Return all locations matching filters.
        
        Args:
            filters: Search filters including query, facilities, price range
            view_type: Controls result prioritization:
                - "street": Prioritize street-level results (default)
                - "planning_area": Prioritize planning area results
        """
        import os, json, re, math, sqlite3
        from app.domain.models import LocationResult, OneMapSearchResult, AreaCentroid
        results: List[LocationResult] = []

        def is_postal_code(query):
            return bool(re.fullmatch(r"\d{6}", query.strip()))

        async def load_planning_areas_cached(year: int = 2019):
            """Load planning area names using a local sqlite cache; fetch from PopAPI if cache is empty."""
            import sqlite3
            try:
                base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
                db_path = os.path.join(base_dir, 'planning_cache.db')
                conn = sqlite3.connect(db_path)
                try:
                    conn.execute(
                        "CREATE TABLE IF NOT EXISTS planning_area_names (year INTEGER NOT NULL, area_name TEXT NOT NULL, PRIMARY KEY(year, area_name))"
                    )
                    rows = conn.execute(
                        "SELECT area_name FROM planning_area_names WHERE year = ?",
                        (year,)
                    ).fetchall()
                    if rows:
                        return {r[0].title() for r in rows}
                    # Cache miss: fetch from PopAPI
                    pa_names = await self.onemap_client.planning_area_names(year)
                    to_insert = [(year, pa['pln_area_n'].title()) for pa in pa_names if 'pln_area_n' in pa]
                    if to_insert:
                        conn.executemany(
                            "INSERT OR IGNORE INTO planning_area_names(year, area_name) VALUES (?, ?)",
                            to_insert
                        )
                        conn.commit()
                    return {name for _, name in to_insert}
                finally:
                    conn.close()
            except Exception:
                # On any failure, fall back to direct API call (no cache persistence)
                try:
                    pa_names = await self.onemap_client.planning_area_names(year)
                    return {pa['pln_area_n'].title() for pa in pa_names if 'pln_area_n' in pa}
                except Exception:
                    return set()

        async def load_planning_area_polygons_cached(year: int = 2019):
            """Load planning area polygons and centroids using local sqlite cache; fetch from PopAPI if cache is empty."""
            import sqlite3
            centroids = {}
            polygons = {}
            try:
                base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
                db_path = os.path.join(base_dir, 'planning_cache.db')
                conn = sqlite3.connect(db_path)
                try:
                    conn.execute(
                        """CREATE TABLE IF NOT EXISTS planning_area_polygons (
                            year INTEGER NOT NULL, 
                            area_name TEXT NOT NULL, 
                            geojson TEXT NOT NULL,
                            centroid_lat REAL NOT NULL,
                            centroid_lon REAL NOT NULL,
                            PRIMARY KEY(year, area_name)
                        )"""
                    )
                    rows = conn.execute(
                        "SELECT area_name, geojson, centroid_lat, centroid_lon FROM planning_area_polygons WHERE year = ?",
                        (year,)
                    ).fetchall()
                    if rows:
                        for area_name, geojson_str, clat, clon in rows:
                            centroids[area_name] = (clat, clon)
                            polygons[area_name] = json.loads(geojson_str)
                        return centroids, polygons
                    
                    # Cache miss: fetch from PopAPI
                    pa_data = await self.onemap_client.planning_areas(year)
                    to_insert = []
                    for area in pa_data.get('SearchResults', []):
                        area_name = area['pln_area_n'].title()
                        geojson_str = area.get('geojson', '{}')
                        geojson = json.loads(geojson_str)
                        polygons[area_name] = geojson
                        # Calculate centroid from polygon coordinates
                        coords = []
                        if geojson.get('type') == 'MultiPolygon':
                            for polygon in geojson.get('coordinates', []):
                                for ring in polygon:
                                    coords.extend(ring)
                        elif geojson.get('type') == 'Polygon':
                            for ring in geojson.get('coordinates', []):
                                coords.extend(ring)
                        if coords:
                            avg_lon = sum(c[0] for c in coords) / len(coords)
                            avg_lat = sum(c[1] for c in coords) / len(coords)
                            centroids[area_name] = (avg_lat, avg_lon)
                            to_insert.append((year, area_name, geojson_str, avg_lat, avg_lon))
                    
                    if to_insert:
                        conn.executemany(
                            "INSERT OR IGNORE INTO planning_area_polygons(year, area_name, geojson, centroid_lat, centroid_lon) VALUES (?, ?, ?, ?, ?)",
                            to_insert
                        )
                        conn.commit()
                    return centroids, polygons
                finally:
                    conn.close()
            except Exception:
                # On any failure, fall back to direct API call (no cache persistence)
                try:
                    pa_data = await self.onemap_client.planning_areas(year)
                    for area in pa_data.get('SearchResults', []):
                        area_name = area['pln_area_n'].title()
                        geojson_str = area.get('geojson', '{}')
                        geojson = json.loads(geojson_str)
                        polygons[area_name] = geojson
                        coords = []
                        if geojson.get('type') == 'MultiPolygon':
                            for polygon in geojson.get('coordinates', []):
                                for ring in polygon:
                                    coords.extend(ring)
                        elif geojson.get('type') == 'Polygon':
                            for ring in geojson.get('coordinates', []):
                                coords.extend(ring)
                        if coords:
                            avg_lon = sum(c[0] for c in coords) / len(coords)
                            avg_lat = sum(c[1] for c in coords) / len(coords)
                            centroids[area_name] = (avg_lat, avg_lon)
                except Exception:
                    pass
                return centroids, polygons

        def haversine(lat1, lon1, lat2, lon2):
            R = 6371
            phi1, phi2 = math.radians(lat1), math.radians(lat2)
            dphi = math.radians(lat2 - lat1)
            dlambda = math.radians(lon2 - lon1)
            a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
            return 2*R*math.atan2(math.sqrt(a), math.sqrt(1-a))

        def point_in_polygon(lon, lat, polygon):
            # Ray casting algorithm for point-in-polygon
            # GeoJSON: [longitude, latitude]
            num = len(polygon)
            j = num - 1
            inside = False
            for i in range(num):
                lon_i, lat_i = polygon[i][0], polygon[i][1]
                lon_j, lat_j = polygon[j][0], polygon[j][1]
                if ((lat_i > lat) != (lat_j > lat)) and (lon < (lon_j - lon_i) * (lat - lat_i) / (lat_j - lat_i + 1e-12) + lon_i):
                    inside = not inside
                j = i
            return inside

        async def find_area_by_point(lat, lon, polygons_cache):
            # Check if point is inside any planning area polygon using cached data
            for area_name, geojson in polygons_cache.items():
                if geojson.get('type') == 'MultiPolygon':
                    for polygon in geojson.get('coordinates', []):
                        for ring in polygon:
                            if point_in_polygon(lon, lat, ring):
                                return area_name
                elif geojson.get('type') == 'Polygon':
                    for ring in geojson.get('coordinates', []):
                        if point_in_polygon(lon, lat, ring):
                            return area_name
            return None

        # -------- Facility datasets (from disk cache) --------
        def _load_facility_datasets():
            """Load and cache facility datasets from disk cache for quick radius counts."""
            # Cache at instance level to avoid reloading within the same process
            if hasattr(self, "_facility_datasets") and self._facility_datasets is not None:
                return self._facility_datasets

            try:
                from app.cache.disk_cache import load_cache as _dc_load
                from app.cache.paths import cache_file as _cache_file
            except Exception:
                # If cache utils are not available, return empty datasets
                self._facility_datasets = {
                    'schools': [], 'sports': [], 'hawkers': [],
                    'healthcare': [], 'greenSpaces': [], 'carparks': [], 'transit': []
                }
                return self._facility_datasets

            datasets = {
                'schools': [], 'sports': [], 'hawkers': [],
                'healthcare': [], 'greenSpaces': [], 'carparks': [], 'transit': []
            }

            # Schools (from OneMap search cached pages)
            try:
                blob = _dc_load(_cache_file("onemap_search_school", version=1))
                if blob:
                    datasets['schools'] = blob.get('payload', [])
            except Exception:
                pass

            # Sports facilities (data.gov.sg GeoJSON)
            try:
                blob = _dc_load(_cache_file("sports_dataset", version=1))
                sports_raw = blob.get('payload', {}) if blob else {}
                sports = []
                for feature in sports_raw.get('features', []):
                    geom = feature.get('geometry', {})
                    coords = geom.get('coordinates', [])
                    if geom.get('type') == 'Polygon' and coords:
                        lat = coords[0][0][1] if coords[0] else None
                        lon = coords[0][0][0] if coords[0] else None
                    elif geom.get('type') == 'MultiPolygon' and coords:
                        lat = coords[0][0][0][1] if coords[0][0] else None
                        lon = coords[0][0][0][0] if coords[0][0] else None
                    else:
                        lat, lon = None, None
                    if lat is not None and lon is not None:
                        sports.append({'latitude': lat, 'longitude': lon})
                datasets['sports'] = sports
            except Exception:
                pass

            # Hawker centres (Point GeoJSON)
            try:
                blob = _dc_load(_cache_file("hawkers_dataset", version=1))
                hawkers_raw = blob.get('payload', {}) if blob else {}
                hawkers = []
                for feature in hawkers_raw.get('features', []):
                    geom = feature.get('geometry', {})
                    if geom.get('type') == 'Point':
                        coords = geom.get('coordinates', [])
                        if len(coords) >= 2:
                            hawkers.append({'latitude': coords[1], 'longitude': coords[0]})
                datasets['hawkers'] = hawkers
            except Exception:
                pass

            # CHAS clinics (Point GeoJSON)
            try:
                blob = _dc_load(_cache_file("chas_dataset", version=1))
                clinics_raw = blob.get('payload', {}) if blob else {}
                clinics = []
                for feature in clinics_raw.get('features', []):
                    geom = feature.get('geometry', {})
                    if geom.get('type') == 'Point':
                        coords = geom.get('coordinates', [])
                        if len(coords) >= 2:
                            clinics.append({'latitude': coords[1], 'longitude': coords[0]})
                datasets['healthcare'] = clinics
            except Exception:
                pass

            # Parks (Point GeoJSON)
            try:
                blob = _dc_load(_cache_file("parks_dataset", version=1))
                parks_raw = blob.get('payload', {}) if blob else {}
                parks = []
                for feature in parks_raw.get('features', []):
                    geom = feature.get('geometry', {})
                    if geom.get('type') == 'Point':
                        coords = geom.get('coordinates', [])
                        if len(coords) >= 2:
                            parks.append({'latitude': coords[1], 'longitude': coords[0]})
                datasets['greenSpaces'] = parks
            except Exception:
                pass

            # HDB Carparks (list of records)
            try:
                blob = _dc_load(_cache_file("hdb_carparks_records", version=1))
                carparks_raw = blob.get('payload', []) if blob else []
                carparks = []
                for cp in carparks_raw:
                    lat = cp.get('latitude')
                    lon = cp.get('longitude')
                    if lat and lon:
                        carparks.append({'latitude': float(lat), 'longitude': float(lon)})
                datasets['carparks'] = carparks
            except Exception:
                pass

            # Transit nodes (MRT/LRT stations)
            try:
                # Load transit nodes from the rating engine's transit repository
                if hasattr(self.engine, 'transit') and hasattr(self.engine.transit, 'all'):
                    transit_nodes = self.engine.transit.all()
                    transit = []
                    for node in transit_nodes:
                        if node.latitude is not None and node.longitude is not None:
                            transit.append({'latitude': float(node.latitude), 'longitude': float(node.longitude)})
                    datasets['transit'] = transit
                else:
                    datasets['transit'] = []
            except Exception:
                datasets['transit'] = []

            self._facility_datasets = datasets
            return datasets

        def _count_facilities_near(lat: float, lon: float, datasets, radius_km: float = 1.0) -> dict:
            """Count facilities near a point.
            Tweaks:
            - Use a smaller radius for healthcare (0.5 km) to avoid inflated counts.
            - Deduplicate very close healthcare points (~100m) to avoid multiple clinics in the same building inflating counts.
            """
            out = {k: 0 for k in ['schools', 'sports', 'hawkers', 'healthcare', 'greenSpaces', 'carparks', 'transit']}
            # category-specific radius override
            category_radius = {'healthcare': 0.5}
            # approx degrees per ~100m (lat ~ 0.0009, lon depends on latitude)
            lat_cell = 0.0009
            lon_cell = 0.0009 / max(math.cos(math.radians(lat)), 0.3)
            healthcare_cells = set()
            for key, items in datasets.items():
                try:
                    eff_r = float(category_radius.get(key, radius_km))
                    for it in items:
                        f_lat = float(it.get('LATITUDE') or it.get('latitude'))
                        f_lon = float(it.get('LONGITUDE') or it.get('longitude'))
                        if haversine(lat, lon, f_lat, f_lon) <= eff_r:
                            if key == 'healthcare':
                                # dedup nearby clinics by 100m grid
                                cell = (int(f_lat / lat_cell), int(f_lon / lon_cell))
                                if cell in healthcare_cells:
                                    continue
                                healthcare_cells.add(cell)
                            out[key] += 1
                except Exception:
                    continue
            return out

        def _clamp01(x: float) -> float:
            return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x

        def _compute_local_street_score(lat: float, lon: float, counts: dict) -> float:
            """Compute a local street-level score using nearby facilities and transit proximity.
            Uses only Amenities, Accessibility, Environment and normalizes weights accordingly.
            """
            # Local amenities score
            amen = _clamp01((counts.get('schools', 0) + counts.get('sports', 0) + counts.get('hawkers', 0)
                            + counts.get('healthcare', 0) + counts.get('greenSpaces', 0)) / 22.0)
            # Environment: based on parks
            env = _clamp01((counts.get('greenSpaces', 0)) / 11.0)

            # Accessibility: distance to nearest transit + carparks
            transit_score = 0.35
            try:
                nodes = (self.engine.transit.list_near_area("dummy") if hasattr(self.engine, 'transit') and hasattr(self.engine.transit, 'list_near_area') else None)
            except Exception:
                nodes = None
            if not nodes and hasattr(self.engine, 'transit') and hasattr(self.engine.transit, 'all'):
                try:
                    nodes = self.engine.transit.all()
                except Exception:
                    nodes = []
            dmin = None
            if nodes:
                dists = []
                for n in nodes:
                    try:
                        if n.latitude is None or n.longitude is None:
                            continue
                        d = haversine(lat, lon, float(n.latitude), float(n.longitude))
                        dists.append(d)
                    except Exception:
                        continue
                dmin = min(dists) if dists else None
            # Transit scoring (mirror RatingEngine logic)
            if dmin is None:
                transit_score = 0.35
            elif dmin <= 0.2:
                transit_score = 1.0
            elif dmin <= 1.0:
                transit_score = _clamp01(1.0 - (dmin - 0.2) / 0.8)
            else:
                transit_score = 0.12

            carpark_score = _clamp01((counts.get('carparks', 0)) / 22.0)
            acc = _clamp01(0.7 * transit_score + 0.3 * carpark_score)

            # Normalize weights across available categories (Amen, Acc, Env)
            wA, wAcc, wEnv = 0.2, 0.2, 0.2
            denom = (wA + wAcc + wEnv) or 1.0
            local = (amen * wA + acc * wAcc + env * wEnv) / denom
            return float(round(local, 4))
        
        # Load planning area polygons and centroids from cache (also populates planning_areas set)
        centroids, polygons = await load_planning_area_polygons_cached()
        planning_areas = set(polygons.keys())  # Get area names from polygon cache for consistency

        # Case 1: Search query exists
        if filters.search_query:
            query = filters.search_query.strip()
            
            # Use OneMap search API and check "found" count
            onemap_response = await self.search_onemap(query)
            found_count = onemap_response.found
            print(f"OneMap search for '{query}' found {found_count} results.")
            
            if found_count == 0:
                print("No results found.")
            
            elif found_count == 1:
                # Exactly one result - return this specific location
                om = onemap_response.results[0]
                lat, lon = float(om.LATITUDE), float(om.LONGITUDE)
                print("street name:", om.ROAD_NAME)
                print("address:", om.ADDRESS)
                
                # Try to get planning area for this location from database first
                matched_area = None
                try:
                    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
                    street_db_path = os.path.join(base_dir, 'street_geocode.db')
                    temp_conn = sqlite3.connect(street_db_path)
                    temp_cursor = temp_conn.cursor()
                    
                    # Try to find existing street in database with planning_area
                    if om.ROAD_NAME and om.ROAD_NAME != "NIL":
                        db_row = temp_cursor.execute(
                            "SELECT planning_area FROM street_locations WHERE street_name = ? AND planning_area IS NOT NULL",
                            (om.ROAD_NAME,)
                        ).fetchone()
                        if db_row:
                            matched_area = db_row[0]
                    
                    temp_conn.close()
                except Exception:
                    pass
                
                # If not found in database, try API
                if not matched_area:
                    try:
                        pa_result = await self.onemap_client.planning_area_at(lat, lon)
                        if pa_result and 'pln_area_n' in pa_result[0]:
                            matched_area = pa_result[0]['pln_area_n'].title()
                    except Exception:
                        # Fallback to polygon containment
                        matched_area = await find_area_by_point(lat, lon, polygons)

                road_name = matched_area
                if om.ROAD_NAME != "NIL":
                    road_name = om.ROAD_NAME or om.SEARCHVAL

                # Map the single result to street_geocode facilities if possible; else compute and persist
                street_name_for_facilities = road_name
                try:
                    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
                    street_db_path = os.path.join(base_dir, 'street_geocode.db')
                    conn = sqlite3.connect(street_db_path)
                    cursor = conn.cursor()

                    # Helper normalization (inline to avoid refactor)
                    def _norm_name(name: str) -> str:
                        if not name:
                            return ""
                        n = name.upper().strip()
                        n = n.replace('AVENUE', 'AVE')
                        n = n.replace('CENTRAL', 'CTRL')
                        n = n.replace('STREET', 'ST')
                        n = n.replace('ROAD', 'RD')
                        n = n.replace('DRIVE', 'DR')
                        n = n.replace('CRESCENT', 'CRES')
                        n = n.replace('NORTH', 'NTH')
                        n = n.replace('SOUTH', 'STH')
                        n = n.replace('EAST', 'E')
                        n = n.replace('WEST', 'W')
                        return ' '.join(n.split())

                    # Only attempt mapping when we have a proper OneMap road name
                    if road_name and road_name != "NIL":
                        onm_norm = _norm_name(road_name)

                        # Build normalized lookup from DB (include planning_area)
                        all_db_streets = cursor.execute(
                            "SELECT street_name, latitude, longitude, address, postal_code, planning_area FROM street_locations WHERE status = 'found'"
                        ).fetchall()
                        db_map = { _norm_name(s): (s, la, lo, ad, pc, pa) for s, la, lo, ad, pc, pa in all_db_streets }

                        if onm_norm in db_map:
                            # Use DB street name and planning_area for enrichment lookup
                            matched_db_name, _, _, _, _, db_planning_area = db_map[onm_norm]
                            street_name_for_facilities = matched_db_name
                            # Use database planning_area if available
                            if db_planning_area and not matched_area:
                                matched_area = db_planning_area
                            # Recompute facilities with refined logic and persist (overrides older counts)
                            try:
                                datasets = _load_facility_datasets()
                                counts = _count_facilities_near(lat, lon, datasets, radius_km=1.0)
                                cursor.execute(
                                    """
                                    CREATE TABLE IF NOT EXISTS street_facilities (
                                        street_name TEXT PRIMARY KEY,
                                        schools INTEGER,
                                        sports INTEGER,
                                        hawkers INTEGER,
                                        healthcare INTEGER,
                                        greenSpaces INTEGER,
                                        carparks INTEGER,
                                        radius_km REAL DEFAULT 1.0,
                                        calculated_at TEXT DEFAULT (datetime('now'))
                                    )
                                    """
                                )
                                cursor.execute(
                                    """
                                    CREATE TABLE IF NOT EXISTS street_scores (
                                        street_name TEXT PRIMARY KEY,
                                        local_score REAL NOT NULL,
                                        transit_km REAL,
                                        calculated_at TEXT DEFAULT (datetime('now'))
                                    )
                                    """
                                )
                                cursor.execute(
                                    """
                                    INSERT OR REPLACE INTO street_facilities (
                                        street_name, schools, sports, hawkers, healthcare, greenSpaces, carparks, transit, radius_km, calculated_at
                                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1.0, datetime('now'))
                                    """,
                                    (
                                        street_name_for_facilities,
                                        counts.get('schools', 0),
                                        counts.get('sports', 0),
                                        counts.get('hawkers', 0),
                                        counts.get('healthcare', 0),
                                        counts.get('greenSpaces', 0),
                                        counts.get('carparks', 0),
                                        counts.get('transit', 0)
                                    )
                                )
                                # Compute and upsert local street-level score
                                try:
                                    local_score = _compute_local_street_score(lat, lon, counts)
                                    nodes = self.engine.transit.all() if hasattr(self.engine, 'transit') and hasattr(self.engine.transit, 'all') else []
                                    dmin = None
                                    if nodes:
                                        dists = [
                                            haversine(lat, lon, float(n.latitude), float(n.longitude))
                                            for n in nodes if n.latitude is not None and n.longitude is not None
                                        ]
                                        dmin = min(dists) if dists else None
                                    cursor.execute(
                                        """
                                        INSERT OR REPLACE INTO street_scores (street_name, local_score, transit_km, calculated_at)
                                        VALUES (?, ?, ?, datetime('now'))
                                        """,
                                        (street_name_for_facilities, float(local_score), float(dmin) if dmin is not None else None)
                                    )
                                except Exception:
                                    pass
                                conn.commit()
                            except Exception:
                                pass
                        else:
                            # Persist this new street and compute facilities now
                            try:
                                # Ensure facilities table exists
                                cursor.execute(
                                    """
                                    CREATE TABLE IF NOT EXISTS street_facilities (
                                        street_name TEXT PRIMARY KEY,
                                        schools INTEGER,
                                        sports INTEGER,
                                        hawkers INTEGER,
                                        healthcare INTEGER,
                                        greenSpaces INTEGER,
                                        carparks INTEGER,
                                        radius_km REAL DEFAULT 1.0,
                                        calculated_at TEXT DEFAULT (datetime('now'))
                                    )
                                    """
                                )
                            except Exception:
                                pass

                            # Upsert into street_locations (including planning_area)
                            try:
                                cursor.execute(
                                    """
                                    INSERT OR REPLACE INTO street_locations (street_name, latitude, longitude, address, building, postal_code, status, planning_area)
                                    VALUES (?, ?, ?, ?, ?, ?, 'found', ?)
                                    """,
                                    (
                                        road_name,
                                        lat,
                                        lon,
                                        om.ADDRESS,
                                        getattr(om, 'BUILDING', None) if hasattr(om, 'BUILDING') else None,
                                        om.POSTAL if hasattr(om, 'POSTAL') else None,
                                        matched_area
                                    )
                                )
                            except Exception:
                                pass

                            # Compute and upsert facilities
                            try:
                                datasets = _load_facility_datasets()
                                counts = _count_facilities_near(lat, lon, datasets, radius_km=1.0)
                                cursor.execute(
                                    """
                                    INSERT OR REPLACE INTO street_facilities (
                                        street_name, schools, sports, hawkers, healthcare, greenSpaces, carparks, transit, radius_km, calculated_at
                                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1.0, datetime('now'))
                                    """,
                                    (
                                        road_name,
                                        counts.get('schools', 0),
                                        counts.get('sports', 0),
                                        counts.get('hawkers', 0),
                                        counts.get('healthcare', 0),
                                        counts.get('greenSpaces', 0),
                                        counts.get('carparks', 0),
                                        counts.get('transit', 0)
                                    )
                                )
                                # Also upsert local street-level score
                                try:
                                    local_score = _compute_local_street_score(lat, lon, counts)
                                    # Ensure street_scores table exists
                                    cursor.execute(
                                        """
                                        CREATE TABLE IF NOT EXISTS street_scores (
                                            street_name TEXT PRIMARY KEY,
                                            local_score REAL NOT NULL,
                                            transit_km REAL,
                                            calculated_at TEXT DEFAULT (datetime('now'))
                                        )
                                        """
                                    )
                                    # compute nearest transit distance
                                    nodes = self.engine.transit.all() if hasattr(self.engine, 'transit') and hasattr(self.engine.transit, 'all') else []
                                    dmin = None
                                    if nodes:
                                        dists = [
                                            haversine(lat, lon, float(n.latitude), float(n.longitude))
                                            for n in nodes if n.latitude is not None and n.longitude is not None
                                        ]
                                        dmin = min(dists) if dists else None
                                    cursor.execute(
                                        """
                                        INSERT OR REPLACE INTO street_scores (street_name, local_score, transit_km, calculated_at)
                                        VALUES (?, ?, ?, datetime('now'))
                                        """,
                                        (road_name, float(local_score), float(dmin) if dmin is not None else None)
                                    )
                                except Exception as score_err:
                                    print(f"Warning: Could not compute score for {road_name}: {score_err}")
                                conn.commit()
                            except Exception as fac_err:
                                print(f"Warning: Could not compute facilities for {road_name}: {fac_err}")

                    conn.close()
                except Exception as _e:
                    # If mapping/persisting fails, continue without enrichment persistence
                    pass

                results.append(LocationResult(
                    id=1,
                    street=street_name_for_facilities,
                    area=street_name_for_facilities,  # prefer street as area label
                    district=matched_area or road_name,  # show planning area as district tag
                    price_range=[0, 0],
                    avg_price=0,
                    facilities=[],
                    description=om.ADDRESS,
                    growth=0.0,
                    amenities=[],
                    latitude=lat,
                    longitude=lon
                ))
            
            else:  # found_count > 1
                # Multiple results - behavior depends on view_type:
                # - "street": return street names from street_geocode.db (default)
                # - "planning_area": return aggregated planning area results
                base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
                street_db_path = os.path.join(base_dir, 'street_geocode.db')
                
                if view_type == "planning_area":
                    # Planning area view: group results by planning area
                    print(f"Planning area view: grouping {found_count} OneMap results by planning area")
                    area_matches = {}  # planning_area -> {lat, lon, count}
                    
                    try:
                        conn = sqlite3.connect(street_db_path)
                        cursor = conn.cursor()

                        # If the query exactly matches a planning area name, short-circuit to that area only
                        try:
                            q = (query or "").strip()
                            exact_match = next((name for name in planning_areas if name.upper() == q.upper()), None)
                        except Exception:
                            exact_match = None

                        if exact_match:
                            lat, lon = centroids.get(exact_match, (0.0, 0.0))
                            area_matches[exact_match] = {'lat': lat, 'lon': lon, 'count': 0}
                            print(f"Planning area exact match: {exact_match}")
                        else:
                            for result in onemap_response.results:
                                if result.LATITUDE and result.LONGITUDE:
                                    lat, lon = float(result.LATITUDE), float(result.LONGITUDE)
                                    
                                    # Try to get planning area from result's street if in database
                                    matched_area = None
                                    if result.ROAD_NAME and result.ROAD_NAME != "NIL":
                                        row = cursor.execute(
                                            "SELECT planning_area FROM street_locations WHERE UPPER(street_name) = UPPER(?) LIMIT 1",
                                            (result.ROAD_NAME,)
                                        ).fetchone()
                                        if row and row[0]:
                                            matched_area = row[0]
                                    
                                    # Fallback to API or polygon lookup
                                    if not matched_area:
                                        try:
                                            pa_result = await self.onemap_client.planning_area_at(lat, lon)
                                            if pa_result and 'pln_area_n' in pa_result[0]:
                                                matched_area = pa_result[0]['pln_area_n'].title()
                                        except Exception:
                                            matched_area = await find_area_by_point(lat, lon, polygons)
                                    
                                    if matched_area:
                                        if matched_area not in area_matches:
                                            area_matches[matched_area] = {'lat': lat, 'lon': lon, 'count': 0}
                                        else:
                                            # Average the coordinates for multiple points in same area
                                            area_matches[matched_area]['lat'] = (area_matches[matched_area]['lat'] * area_matches[matched_area]['count'] + lat) / (area_matches[matched_area]['count'] + 1)
                                            area_matches[matched_area]['lon'] = (area_matches[matched_area]['lon'] * area_matches[matched_area]['count'] + lon) / (area_matches[matched_area]['count'] + 1)
                                        area_matches[matched_area]['count'] += 1
                        
                        conn.close()
                        
                        # Create LocationResult for each planning area
                        for idx, (area_name, data) in enumerate(area_matches.items(), start=1):
                            results.append(LocationResult(
                                id=idx,
                                street=area_name,
                                area=area_name,
                                district=area_name,
                                price_range=[0, 0],
                                avg_price=0,
                                facilities=[],
                                description=f"Planning area: {area_name} ({data['count']} locations)",
                                growth=0.0,
                                amenities=[],
                                latitude=data['lat'],
                                longitude=data['lon']
                            ))
                        
                        # Debug: show distribution of matches across planning areas
                        try:
                            dist = {k: v.get('count', 0) for k, v in area_matches.items()}
                            print(f"Planning area distribution: {dist}")
                        except Exception:
                            pass
                        print(f"Grouped into {len(area_matches)} planning areas")
                    except Exception as e:
                        print(f"Error in planning_area view: {e}")
                    
                    # Skip the street-level logic below when in planning_area view
                else:
                    # Street view (default): return street names from street_geocode.db
                    
                    # Helper function to normalize street names for matching
                    def normalize_street_name(name):
                        """Normalize street name by handling abbreviations"""
                        if not name:
                            return ""
                        normalized = name.upper().strip()
                        # Handle common abbreviations
                        normalized = normalized.replace('AVENUE', 'AVE')
                        normalized = normalized.replace('CENTRAL', 'CTRL')
                        normalized = normalized.replace('STREET', 'ST')
                        normalized = normalized.replace('ROAD', 'RD')
                        normalized = normalized.replace('DRIVE', 'DR')
                        normalized = normalized.replace('CRESCENT', 'CRES')
                        normalized = normalized.replace('NORTH', 'NTH')
                        normalized = normalized.replace('SOUTH', 'STH')
                        normalized = normalized.replace('EAST', 'E')
                        normalized = normalized.replace('WEST', 'W')
                        # Remove extra spaces
                        normalized = ' '.join(normalized.split())
                        return normalized
                    
                    # Use a set to track which streets we've already added to avoid duplicates
                    added_streets = set()
                    
                    try:
                        conn = sqlite3.connect(street_db_path)
                        cursor = conn.cursor()
                    
                        # Get all streets from database for fuzzy matching (include planning_area)
                        all_db_streets = cursor.execute(
                            "SELECT street_name, latitude, longitude, address, postal_code, planning_area FROM street_locations WHERE status = 'found'"
                        ).fetchall()
                    
                        # Create normalized lookup
                        db_street_map = {}
                        for street_name, lat, lon, address, postal_code, planning_area in all_db_streets:
                            normalized = normalize_street_name(street_name)
                            db_street_map[normalized] = (street_name, lat, lon, address, postal_code, planning_area)
                    
                        # Extract unique street names from OneMap results and try to match
                        # Filter: only include results where the street name contains the query
                        matched_streets = []
                        unmatched_onemap_streets = []  # Track streets not in database
                    
                        for result in onemap_response.results:
                            if result.ROAD_NAME and result.ROAD_NAME != "NIL":
                                # Check if the road name contains the search query
                                if query.upper() not in result.ROAD_NAME.upper():
                                    continue  # Skip this result if query is not in the road name
                            
                                normalized_name = normalize_street_name(result.ROAD_NAME)
                                if normalized_name in db_street_map:
                                    street_name, lat, lon, address, postal_code, planning_area = db_street_map[normalized_name]
                                    if street_name not in added_streets:
                                        added_streets.add(street_name)
                                        matched_streets.append((street_name, lat, lon, address, postal_code, planning_area))
                                else:
                                    # Street not in database, add to unmatched list
                                    if result.ROAD_NAME.upper() not in added_streets:
                                        unmatched_onemap_streets.append(result)
                    
                        print(f"Found {len(matched_streets)} matching streets in street_geocode.db")
                        print(f"Found {len(unmatched_onemap_streets)} unique streets from OneMap not in database")
                    
                        if matched_streets:
                            # Found matches in street_geocode.db
                            # Load datasets once; ensure facilities table exists
                            _datasets = _load_facility_datasets()
                            try:
                                cursor.execute(
                                    """
                                    CREATE TABLE IF NOT EXISTS street_facilities (
                                        street_name TEXT PRIMARY KEY,
                                        schools INTEGER,
                                        sports INTEGER,
                                        hawkers INTEGER,
                                        healthcare INTEGER,
                                        greenSpaces INTEGER,
                                        carparks INTEGER,
                                        radius_km REAL DEFAULT 1.0,
                                        calculated_at TEXT DEFAULT (datetime('now'))
                                    )
                                    """
                                )
                                cursor.execute(
                                    """
                                    CREATE TABLE IF NOT EXISTS street_scores (
                                        street_name TEXT PRIMARY KEY,
                                        local_score REAL NOT NULL,
                                        transit_km REAL,
                                        calculated_at TEXT DEFAULT (datetime('now'))
                                    )
                                    """
                                )
                            except Exception:
                                pass
                            for idx, (street_name, lat, lon, address, postal_code, planning_area) in enumerate(matched_streets, start=1):
                                # Use planning_area from database (already populated by migration)
                                matched_area = planning_area if planning_area else None
                            
                                # Only query API/polygon if planning_area is not in database
                                if not matched_area and lat and lon:
                                    try:
                                        pa_result = await self.onemap_client.planning_area_at(lat, lon)
                                        if pa_result and 'pln_area_n' in pa_result[0]:
                                            matched_area = pa_result[0]['pln_area_n'].title()
                                            # Update database with the found planning_area
                                            cursor.execute(
                                                "UPDATE street_locations SET planning_area = ? WHERE street_name = ?",
                                                (matched_area, street_name)
                                            )
                                    except Exception:
                                        matched_area = await find_area_by_point(lat, lon, polygons)
                                        if matched_area:
                                            cursor.execute(
                                                "UPDATE street_locations SET planning_area = ? WHERE street_name = ?",
                                                (matched_area, street_name)
                                            )

                                # Recompute and persist refined facility counts for matched streets as well
                                try:
                                    if lat and lon:
                                        counts = _count_facilities_near(float(lat), float(lon), _datasets, radius_km=1.0)
                                        cursor.execute(
                                            """
                                            INSERT OR REPLACE INTO street_facilities (
                                                street_name, schools, sports, hawkers, healthcare, greenSpaces, carparks, transit, radius_km, calculated_at
                                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1.0, datetime('now'))
                                            """,
                                            (
                                                street_name,
                                                counts.get('schools', 0),
                                                counts.get('sports', 0),
                                                counts.get('hawkers', 0),
                                                counts.get('healthcare', 0),
                                                counts.get('greenSpaces', 0),
                                                counts.get('carparks', 0),
                                                counts.get('transit', 0)
                                            )
                                        )
                                        # Upsert local street-level score
                                        try:
                                            local_score = _compute_local_street_score(float(lat), float(lon), counts)
                                            nodes = self.engine.transit.all() if hasattr(self.engine, 'transit') and hasattr(self.engine, 'transit') else []
                                            dmin = None
                                            try:
                                                if nodes:
                                                    dists = [
                                                        haversine(float(lat), float(lon), float(n.latitude), float(n.longitude))
                                                        for n in nodes if n.latitude is not None and n.longitude is not None
                                                    ]
                                                    dmin = min(dists) if dists else None
                                            except Exception:
                                                dmin = None
                                            cursor.execute(
                                                """
                                                INSERT OR REPLACE INTO street_scores (street_name, local_score, transit_km, calculated_at)
                                                VALUES (?, ?, ?, datetime('now'))
                                                """,
                                                (street_name, float(local_score), float(dmin) if dmin is not None else None)
                                            )
                                        except Exception as score_err:
                                            print(f"Warning: Could not compute score for {street_name}: {score_err}")
                                except Exception as fac_err:
                                    print(f"Warning: Could not compute facilities for {street_name}: {fac_err}")
                            
                                results.append(LocationResult(
                                    id=len(results) + 1,
                                    street=street_name,
                                    area=street_name,  # prefer street for label
                                    district=matched_area or street_name,  # planning area as district
                                    price_range=[0, 0],
                                    avg_price=0,
                                    facilities=[],
                                    description=address or f"Street: {street_name}",
                                    growth=0.0,
                                    amenities=[],
                                    latitude=lat,
                                    longitude=lon
                                ))
                            try:
                                conn.commit()
                            except Exception:
                                pass
                    
                        # Add unique unmatched streets from OneMap (up to 20 total results)
                        if unmatched_onemap_streets and len(results) < 20:
                            print(f"Adding {min(len(unmatched_onemap_streets), 20 - len(results))} unique streets from OneMap")
                            # Ensure facility datasets are loaded once
                            _datasets = _load_facility_datasets()
                            # Ensure street_facilities table exists before upserting
                            try:
                                cursor.execute(
                                    """
                                    CREATE TABLE IF NOT EXISTS street_facilities (
                                        street_name TEXT PRIMARY KEY,
                                        schools INTEGER,
                                        sports INTEGER,
                                        hawkers INTEGER,
                                        healthcare INTEGER,
                                        greenSpaces INTEGER,
                                        carparks INTEGER,
                                        radius_km REAL DEFAULT 1.0,
                                        calculated_at TEXT DEFAULT (datetime('now'))
                                    )
                                    """
                                )
                                cursor.execute(
                                    """
                                    CREATE TABLE IF NOT EXISTS street_scores (
                                        street_name TEXT PRIMARY KEY,
                                        local_score REAL NOT NULL,
                                        transit_km REAL,
                                        calculated_at TEXT DEFAULT (datetime('now'))
                                    )
                                    """
                                )
                            except Exception:
                                pass
                            for om in unmatched_onemap_streets[:20 - len(results)]:
                                road_name = om.ROAD_NAME or om.SEARCHVAL
                                if road_name and road_name != "NIL":
                                    added_streets.add(road_name.upper())
                                    lat, lon = float(om.LATITUDE), float(om.LONGITUDE)
                                    matched_area = None
                                    try:
                                        pa_result = await self.onemap_client.planning_area_at(lat, lon)
                                        if pa_result and 'pln_area_n' in pa_result[0]:
                                            matched_area = pa_result[0]['pln_area_n'].title()
                                    except Exception:
                                        matched_area = await find_area_by_point(lat, lon, polygons)
                                    # Persist this new street into street_locations and street_facilities with computed facility counts
                                    try:
                                        # Upsert into street_locations (including planning_area)
                                        cursor.execute(
                                            """
                                            INSERT OR REPLACE INTO street_locations (street_name, latitude, longitude, address, building, postal_code, status, planning_area)
                                            VALUES (?, ?, ?, ?, ?, ?, 'found', ?)
                                            """,
                                            (
                                                road_name,
                                                lat,
                                                lon,
                                                om.ADDRESS,
                                                getattr(om, 'BUILDING', None) if hasattr(om, 'BUILDING') else None,
                                                om.POSTAL if hasattr(om, 'POSTAL') else None,
                                                matched_area
                                            )
                                        )
                                    except Exception as _e:
                                        # If street_locations table or columns differ, log warning
                                        print(f"Warning: Could not insert location data for {road_name}: {_e}")
                                    # Compute facility counts around this point and upsert
                                    try:
                                        counts = _count_facilities_near(lat, lon, _datasets, radius_km=1.0)
                                        cursor.execute(
                                            """
                                            INSERT OR REPLACE INTO street_facilities (
                                                street_name, schools, sports, hawkers, healthcare, greenSpaces, carparks, transit, radius_km, calculated_at
                                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1.0, datetime('now'))
                                            """,
                                            (
                                                road_name,
                                                counts.get('schools', 0),
                                                counts.get('sports', 0),
                                                counts.get('hawkers', 0),
                                                counts.get('healthcare', 0),
                                                counts.get('greenSpaces', 0),
                                                counts.get('carparks', 0),
                                                counts.get('transit', 0)
                                            )
                                        )
                                        # Upsert local street-level score
                                        local_score = _compute_local_street_score(lat, lon, counts)
                                        # Estimate nearest transit distance again to persist (optional)
                                        try:
                                            # reuse logic to compute dmin
                                            nodes = self.engine.transit.all() if hasattr(self.engine, 'transit') and hasattr(self.engine.transit, 'all') else []
                                            dmin = None
                                            if nodes:
                                                dists = [
                                                    haversine(lat, lon, float(n.latitude), float(n.longitude))
                                                    for n in nodes if n.latitude is not None and n.longitude is not None
                                                ]
                                                dmin = min(dists) if dists else None
                                        except Exception:
                                            dmin = None
                                        cursor.execute(
                                            """
                                            INSERT OR REPLACE INTO street_scores (street_name, local_score, transit_km, calculated_at)
                                            VALUES (?, ?, ?, datetime('now'))
                                            """,
                                            (road_name, float(local_score), float(dmin) if dmin is not None else None)
                                        )
                                        conn.commit()
                                    except Exception as _e:
                                        # If facility upsert fails, log warning
                                        print(f"Warning: Could not compute/save facilities for {road_name}: {_e}")
                                
                                    results.append(LocationResult(
                                        id=len(results) + 1,
                                        street=road_name,
                                        area=road_name,  # prefer street label
                                        district=matched_area or road_name,  # planning area as district
                                        price_range=[0, 0],
                                        avg_price=0,
                                        facilities=[],
                                        description=om.ADDRESS,
                                        growth=0.0,
                                        amenities=[],
                                        latitude=lat,
                                        longitude=lon
                                    ))
                    
                        conn.close()
                    except Exception as e:
                        print(f"Error querying street_geocode.db: {e}")
                        # Fallback: return OneMap results grouped by street
                        for om in onemap_response.results:
                            road_name = om.ROAD_NAME or om.SEARCHVAL
                            if road_name.upper() not in added_streets:
                                added_streets.add(road_name.upper())
                                lat, lon = float(om.LATITUDE), float(om.LONGITUDE)
                                
                                results.append(LocationResult(
                                    id=len(results) + 1,
                                    street=road_name,
                                    area=road_name,
                                    district=road_name,
                                    price_range=[0, 0],
                                    avg_price=0,
                                    facilities=[],
                                    description=om.ADDRESS,
                                    growth=0.0,
                                    amenities=[],
                                    latitude=lat,
                                    longitude=lon
                                ))
        else:
            # No search query: return all planning areas as LocationResults
            for idx, area_name in enumerate(planning_areas, start=1):
                lat, lon = centroids.get(area_name, (0.0, 0.0))
                results.append(LocationResult(
                    id=idx,
                    street=area_name,
                    area=area_name,
                    district=area_name,
                    price_range=[0, 0],
                    avg_price=0,
                    facilities=[],
                    description=f"Planning area: {area_name}",
                    growth=0.0,
                    amenities=[],
                    latitude=lat if lat != 0.0 else None,
                    longitude=lon if lon != 0.0 else None
                ))

        # Enrich results with facility data. For planning-area results, prefer the
        # `planning_area_facilities` table in planning_cache.db; otherwise fall back
        # to street-level `street_facilities` in street_geocode.db.
        if results:
            try:
                base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
                street_db_path = os.path.join(base_dir, 'street_geocode.db')
                planning_db_path = os.path.join(base_dir, 'planning_cache.db')

                # Partition requested names into planning areas vs streets
                area_names = [r.street for r in results if r.street and r.street in planning_areas]
                street_names = [r.street for r in results if r.street and r.street not in planning_areas]

                facility_map = {}

                # 1) Load planning-area facilities from planning_cache.db if available
                if area_names:
                    try:
                        conn_pa = sqlite3.connect(planning_db_path)
                        cursor_pa = conn_pa.cursor()
                        placeholders = ','.join('?' * len(area_names))
                        query = f"SELECT area_name, schools, sports, hawkers, healthcare, greenSpaces, carparks, transit FROM planning_area_facilities WHERE area_name IN ({placeholders})"
                        rows = cursor_pa.execute(query, tuple(area_names)).fetchall()
                        for area_name, schools, sports, hawkers, healthcare, parks, carparks, transit in rows:
                            facility_map[area_name] = {
                                'schools': schools,
                                'sports': sports,
                                'hawkers': hawkers,
                                'healthcare': healthcare,
                                'greenSpaces': parks,
                                'carparks': carparks,
                                'transit': transit
                            }
                        conn_pa.close()
                    except Exception:
                        # If planning cache isn't available or query fails, ignore and fall back
                        try:
                            conn_pa.close()
                        except Exception:
                            pass

                # 2) Load street-level facilities for remaining street results
                if street_names:
                    try:
                        conn = sqlite3.connect(street_db_path)
                        cursor = conn.cursor()
                        placeholders = ','.join('?' * len(street_names))
                        facility_query = f"""
                            SELECT street_name, schools, sports, hawkers, healthcare, greenSpaces, carparks, transit
                            FROM street_facilities
                            WHERE street_name IN ({placeholders})
                        """
                        facility_rows = cursor.execute(facility_query, tuple(street_names)).fetchall()
                        for street_name, schools, sports, hawkers, healthcare, parks, carparks, transit in facility_rows:
                            facility_map[street_name] = {
                                'schools': schools,
                                'sports': sports,
                                'hawkers': hawkers,
                                'healthcare': healthcare,
                                'greenSpaces': parks,
                                'carparks': carparks,
                                'transit': transit
                            }
                        conn.close()
                    except Exception:
                        try:
                            conn.close()
                        except Exception:
                            pass

                # Enrich results with whatever facility data we found (area or street)
                for location in results:
                    if location.street in facility_map:
                        fac = facility_map[location.street]
                        facility_list = []
                        if fac.get('schools', 0) > 0:
                            facility_list.append(f"{fac['schools']} Schools")
                        if fac.get('sports', 0) > 0:
                            facility_list.append(f"{fac['sports']} Sports Facilities")
                        if fac.get('hawkers', 0) > 0:
                            facility_list.append(f"{fac['hawkers']} Hawker Centres")
                        if fac.get('healthcare', 0) > 0:
                            facility_list.append(f"{fac['healthcare']} Healthcare")
                        if fac.get('greenSpaces', 0) > 0:
                            facility_list.append(f"{fac['greenSpaces']} Parks")
                        if fac.get('carparks', 0) > 0:
                            facility_list.append(f"{fac['carparks']} Carparks")
                        if fac.get('transit', 0) > 0:
                            facility_list.append(f"{fac['transit']} Transit Stations")
                        location.facilities = facility_list
            except Exception as e:
                print(f"Error loading facility data: {e}")
        
        # Apply filter logic (price range, facilities)
        filtered_results = []
        for location in results:
            # Check if location's price range overlaps with filter's price range
            # Skip price check for OneMap results without price data
            price_check_passed = False
            if location.price_range == [0, 0]:
                # OneMap results without price data - pass price check
                price_check_passed = True
            elif (location.price_range[1] >= filters.price_range[0] and 
                  location.price_range[0] <= filters.price_range[1]):
                price_check_passed = True
            
            if price_check_passed:
                # Apply facilities filter
                if not filters.facilities:
                    # No facility filters applied, include this location
                    filtered_results.append(location)
                else:
                    # Check if location has any of the required facilities based on street_facilities data
                    # Map filter names to database columns
                    facility_filter_map = {
                        'good schools': 'schools',
                        'schools': 'schools',
                        'sports facilities': 'sports',
                        'sports': 'sports',
                        'hawker centres': 'hawkers',
                        'hawkers': 'hawkers',
                        'healthcare': 'healthcare',
                        'parks': 'greenSpaces',
                        'green spaces': 'greenSpaces',
                        'carparks': 'carparks',
                        'parking': 'carparks',
                        'transit': 'transit',
                        'near mrt': 'transit',
                        'mrt': 'transit'
                    }
                    
                    # Check if location meets facility requirements
                    has_matching_facility = False
                    
                    # Try to get facility counts from street_facilities
                    if location.street:
                        try:
                            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
                            street_db_path = os.path.join(base_dir, 'street_geocode.db')
                            conn_filter = sqlite3.connect(street_db_path)
                            cursor_filter = conn_filter.cursor()
                            
                            fac_row = cursor_filter.execute("""
                                SELECT schools, sports, hawkers, healthcare, greenSpaces, carparks, transit
                                FROM street_facilities
                                WHERE street_name = ?
                            """, (location.street,)).fetchone()

                            if fac_row:
                                schools, sports, hawkers, healthcare, parks, carparks, transit = fac_row
                                facility_counts = {
                                    'schools': schools,
                                    'sports': sports,
                                    'hawkers': hawkers,
                                    'healthcare': healthcare,
                                    'greenSpaces': parks,
                                    'carparks': carparks,
                                    'transit': transit
                                }

                                # Check if any requested facility type has count > 0
                                for filter_facility in filters.facilities:
                                    filter_key = filter_facility.lower()
                                    db_column = facility_filter_map.get(filter_key)
                                    if db_column and facility_counts.get(db_column, 0) > 0:
                                        has_matching_facility = True
                                        break
                            
                            conn_filter.close()
                        except Exception:
                            # Fallback to string matching in facilities list
                            has_matching_facility = any(
                                any(filter_facility.lower() in facility.lower() 
                                    for facility in location.facilities)
                                for filter_facility in filters.facilities
                            )
                    else:
                        # No street name, use string matching
                        has_matching_facility = any(
                            any(filter_facility.lower() in facility.lower() 
                                for facility in location.facilities)
                            for filter_facility in filters.facilities
                        )
                    
                    if has_matching_facility:
                        filtered_results.append(location)

        return filtered_results

    def search_and_rank(self, filters: SearchFilters, weights: WeightsProfile) -> List[dict]:
        """
        Combined search, filter, and ranking function.
        Returns locations with their scores for comprehensive results.
        """
        # First filter locations based on search criteria
        filtered_locations = self.filter_locations(filters)
        
        # Extract area names for ranking
        area_names = list(set(location.area for location in filtered_locations))
        
        # Get ranking scores for these areas
        area_scores = self.rank(area_names, weights)
        score_map = {score.areaId: score.total for score in area_scores}
        
        # Combine location data with scores
        results = []
        for location in filtered_locations:
            location_dict = location.dict()
            location_dict['score'] = score_map.get(location.area, 0.0)
            results.append(location_dict)
        
        # Sort by score (highest first)
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return results
    
    async def search_onemap(self, query: str, page: int = 1) -> OneMapSearchResponse:
        """
        Search using OneMap API and return results in OneMap format.
        This maintains the exact format as OneMap API for compatibility.
        """
        result = await self.onemap_client.search(query, page)
        return OneMapSearchResponse(**result)
    
    
    def _convert_onemap_to_location_result(self, onemap_result, idx: int) -> LocationResult:
        """
        Helper method to convert OneMap search result to LocationResult format.
        Useful for integrating OneMap results with existing ranking system.
        """
        # Area: extract from ROAD_NAME (first word, typical for Singapore)
        area = onemap_result.ROAD_NAME.split()[0] if onemap_result.ROAD_NAME else "Unknown"
        # Street: SEARCHVAL and BLK_NO (block number)
        street = f"{onemap_result.SEARCHVAL} {onemap_result.BLK_NO}".strip()
        return LocationResult(
            id=idx,
            street=street,
            area=area,
            district=onemap_result.POSTAL or "Unknown",
            price_range=[0, 0],  # Would need to fetch from your pricing data
            avg_price=0,  # Would need to fetch from your pricing data
            facilities=[],  # Would need to fetch from amenities data
            description=f"Located at {onemap_result.ADDRESS}",
            growth=0.0,  # Would need historical data
            amenities=[],
            latitude=float(onemap_result.LATITUDE) if onemap_result.LATITUDE else None,
            longitude=float(onemap_result.LONGITUDE) if onemap_result.LONGITUDE else None
        )
