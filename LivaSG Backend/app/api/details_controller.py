#api/details_controller.py

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from ..domain.models import PriceTrend
from ..services.trend_service import TrendService



from fastapi import APIRouter, Query
from ..domain.models import FacilitiesSummary, PriceRecord, CategoryBreakdown
router = APIRouter(prefix="/details", tags=["details"])

def get_trend_service():
    raise RuntimeError("TrendService not wired")

@router.get("/{area_id}/breakdown", response_model=CategoryBreakdown)
async def breakdown(area_id: str):
    """Return category breakdown.
    - If the area_id matches a street in our local DB, compute a street-level breakdown.
    - Otherwise, fall back to area-level breakdown from the engine.
    """
    # Try street-level first by checking our local street index (with normalization fallback)
    try:
        import os, sqlite3
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
        street_db_path = os.path.join(base_dir, 'street_geocode.db')
        conn = sqlite3.connect(street_db_path)
        cur = conn.cursor()
        try:
            # Fast exact check
            row = cur.execute(
                "SELECT 1 FROM street_locations WHERE UPPER(street_name) = UPPER(?) LIMIT 1",
                (area_id,)
            ).fetchone()

            if row:
                # Direct match -> return street breakdown
                conn.close()
                return await street_breakdown(area_id)

            # Otherwise try a normalized-name match (handles AVENUE/AVE etc.)
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

            target_norm = _norm_name(area_id)
            all_db_streets = cur.execute("SELECT street_name FROM street_locations").fetchall()
            for (s_name,) in all_db_streets:
                if _norm_name(s_name) == target_norm:
                    conn.close()
                    return await street_breakdown(s_name)

        finally:
            try:
                conn.close()
            except Exception:
                pass
    except Exception:
        # Any failure -> gracefully fall back to area-level
        pass

    # Area-level breakdown via engine
    from ..main import di_engine
    return await di_engine.category_breakdown(area_id)

@router.get("/{area_id}/facilities", response_model=FacilitiesSummary)
async def facilities(area_id: str):
    from ..main import di_amenity
    return await di_amenity.facilities_summary(area_id)

async def street_breakdown(street_name: str) -> CategoryBreakdown:
    """Internal helper: Street-level category breakdown so nearby streets can differ.
    Combines street_facilities + nearest transit; uses area-level values
    for Affordability and Community when available.
    Called by the main breakdown endpoint.
    """
    import os, sqlite3, math
    from ..repositories.memory_impl import MemoryTransitRepo
    from ..domain.models import CategoryBreakdown

    def haversine(lat1, lon1, lat2, lon2):
        R = 6371.0
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
        return 2*R*math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    def clamp01(x: float) -> float:
        return max(0.0, min(1.0, x))

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
    street_db_path = os.path.join(base_dir, 'street_geocode.db')
    conn = sqlite3.connect(street_db_path)
    cur = conn.cursor()
    try:
        fac = cur.execute(
            """
            SELECT schools, sports, hawkers, healthcare, greenSpaces, carparks, transit
            FROM street_facilities WHERE street_name = ?
            """,
            (street_name,)
        ).fetchone()
        loc = cur.execute(
            "SELECT latitude, longitude FROM street_locations WHERE street_name = ?",
            (street_name,)
        ).fetchone()
        if not fac or not loc:
            try:
                from ..main import di_engine, di_onemap_client
                if loc:
                    lat, lon = float(loc[0]), float(loc[1])
                    pa = await di_onemap_client.planning_area_at(lat, lon)
                    if pa and 'pln_area_n' in pa[0]:
                        area = pa[0]['pln_area_n'].title()
                        return await di_engine.category_breakdown(area)
            except Exception:
                pass
                raise ValueError(f"No street data found for {street_name}")

        schools, sports, hawkers, healthcare, parks, carparks, transit = fac
        lat, lon = float(loc[0]), float(loc[1])        # Slightly higher normalization to avoid saturating at 1.0 so nearby streets can differ
        amenities = clamp01((schools + sports + hawkers + healthcare + parks) / 30.0)
        environment = clamp01((parks or 0) / 11.0)

        try:
            nodes = MemoryTransitRepo().all()
        except Exception:
            nodes = []
        dists = [haversine(lat, lon, float(n.latitude), float(n.longitude)) for n in nodes if n.latitude is not None and n.longitude is not None]
        dmin = min(dists) if dists else None
        if dmin is None:
            tscore = 0.35
        elif dmin <= 0.2:
            tscore = 1.0
        elif dmin <= 1.0:
            tscore = clamp01(1.0 - (dmin - 0.2) / 0.8)
        else:
            tscore = 0.12
        cscore = clamp01((carparks or 0) / 22.0)
        accessibility = clamp01(0.7 * tscore + 0.3 * cscore)

        affordability = 0.5
        community = 0.5
        try:
            from ..main import di_engine, di_onemap_client
            pa = await di_onemap_client.planning_area_at(lat, lon)
            if pa and 'pln_area_n' in pa[0]:
                area = pa[0]['pln_area_n'].title()
                area_break = await di_engine.category_breakdown(area)
                affordability = float(area_break.scores.get("Affordability", affordability))
                community = float(area_break.scores.get("Community", community))
        except Exception:
            pass

        return CategoryBreakdown(scores={
            "Affordability": round(affordability, 3),
            "Accessibility": round(accessibility, 3),
            "Amenities": round(amenities, 3),
            "Environment": round(environment, 3),
            "Community": round(community, 3),
        })
    finally:
        conn.close()

@router.get("/street/{street_name}/facilities-locations")
async def street_facilities_locations(
    street_name: str,
    types: str = Query("all", description="Comma-separated: schools,sports,hawkers,healthcare,parks,carparks or 'all'")
):
    """Return lat/lon + metadata for facilities near a street.
    Frontend can use this to add map markers based on user's filter selection.
    """
    import os, sqlite3, math
    from ..repositories.memory_impl import MemoryAmenityRepo, MemoryAreaRepo, MemoryTransitRepo
    
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371.0
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
        return 2*R*math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    
    # Get street coordinates
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
    street_db_path = os.path.join(base_dir, 'street_geocode.db')
    conn = sqlite3.connect(street_db_path)
    cur = conn.cursor()
    
    try:
        loc = cur.execute(
            "SELECT latitude, longitude FROM street_locations WHERE street_name = ?",
            (street_name,)
        ).fetchone()

        street_lat = street_lon = None
        planning_area_mode = False
        planning_area_name = None
        if loc:
            street_lat, street_lon = float(loc[0]), float(loc[1])
        else:
            # Fallback: treat input as planning area id and use planning_area.db instead
            try:
                _, centroid = MemoryAreaRepo.getAreaGeometry(street_name)
                if centroid is None:
                    # Try title-cased area name
                    _, centroid = MemoryAreaRepo.getAreaGeometry(street_name.title())
                if centroid is not None:
                    street_lat, street_lon = float(centroid.latitude), float(centroid.longitude)
                    planning_area_mode = True
                    planning_area_name = street_name.title()
                else:
                    return {"error": f"Street or area '{street_name}' not found", "facilities": {}}
            except Exception:
                return {"error": f"Street or area '{street_name}' not found", "facilities": {}}
        
        # Parse requested types (include transit and community)
        requested = types.lower().split(",") if types != "all" else ["schools", "sports", "hawkers", "healthcare", "parks", "carparks", "transit", "community"]

        # Try to load facility locations from DB tables in street_geocode.db or planning_cache.db
        result = {}

        def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
            try:
                cur = conn.cursor()
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,))
                return cur.fetchone() is not None
            except Exception:
                return False

        def _load_from_street_db(table_name: str):
            """Return list of dicts with keys name, latitude, longitude (or empty list)."""
            try:
                if not _table_exists(conn, table_name):
                    return []
                rows = cur.execute(f"SELECT name, latitude, longitude FROM {table_name}").fetchall()
                out = []
                for r in rows:
                    try:
                        n, la, lo = r[0], r[1], r[2]
                        if la is None or lo is None:
                            continue
                        out.append({"name": n or table_name, "latitude": float(la), "longitude": float(lo)})
                    except Exception:
                        continue
                return out
            except Exception:
                return []

    # Map backend categories to candidate DB table names (best-effort)
        db_category_tables = {
            'schools': ['schools_locations', 'onemap_schools', 'schools'],
            'sports': ['sports_locations', 'sports'],
            'hawkers': ['hawkers_locations', 'hawkers'],
            'healthcare': ['clinics_locations', 'chas_clinics', 'clinics'],
            'parks': ['parks_locations', 'parks'],
            'carparks': ['carparks_locations', 'hdb_carparks', 'carparks'],
            'transit': ['transit_nodes', 'transit'],
            'community': ['community_centres_locations', 'community_centres']
        }
        import json
        # Load planning-area polygon for containment checks when in planning_area_mode
        polygon_geojson = None
        if planning_area_mode and planning_area_name:
            try:
                planning_db_path = os.path.join(base_dir, 'planning_cache.db')
                pconn = sqlite3.connect(planning_db_path)
                pcur = pconn.cursor()
                row = pcur.execute(
                    'SELECT geojson FROM planning_area_polygons WHERE area_name = ? LIMIT 1',
                    (planning_area_name,)
                ).fetchone()
                if row and row[0]:
                    polygon_geojson = json.loads(row[0])
                try:
                    pconn.close()
                except Exception:
                    pass
            except Exception:
                polygon_geojson = None

        def point_in_polygon(lon, lat, polygon):
            # Ray casting algorithm for point-in-polygon. polygon is list of [lon, lat] points
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

        def point_in_geojson(geojson, lat, lon):
            if not geojson:
                return False
            gtype = geojson.get('type')
            if gtype == 'MultiPolygon':
                for polygon_group in geojson.get('coordinates', []):
                    for ring in polygon_group:
                        if point_in_polygon(lon, lat, ring):
                            return True
            elif gtype == 'Polygon':
                for ring in geojson.get('coordinates', []):
                    if point_in_polygon(lon, lat, ring):
                        return True
            return False

        # If we resolved a planning area (fallback), prefer actual facility locations from planning_cache.db
        # when polygon geometry is available; otherwise fall back to the pre-computed counts -> synthetic markers.
        if planning_area_mode and planning_area_name:
            try:
                base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
                planning_db_path = os.path.join(base_dir, 'planning_cache.db')
                pconn = sqlite3.connect(planning_db_path)
                pcur = pconn.cursor()

                # Try to load actual facility location tables from the planning DB and filter by polygon
                found_real = False
                for cat in requested:
                    # Use 'parks' for table lookup (db_category_tables key), cat for result dict
                    table_key = cat  # always use 'parks' for table lookup
                    result[cat] = []
                    for tbl in db_category_tables.get(table_key, []):
                        try:
                            # Check table exists in planning DB
                            pcur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (tbl,))
                            if not pcur.fetchone():
                                continue
                            rows = pcur.execute(f"SELECT name, latitude, longitude, COALESCE(type, '') FROM {tbl}").fetchall()
                            for r in rows:
                                try:
                                    name = r[0] or tbl
                                    latf = float(r[1])
                                    lonf = float(r[2])
                                    # If polygon exists, prefer containment
                                    if polygon_geojson and point_in_geojson(polygon_geojson, latf, lonf):
                                        dist = haversine(street_lat, street_lon, latf, lonf)
                                        found_real = True
                                        result[cat].append({
                                            'name': name,
                                            'latitude': latf,
                                            'longitude': lonf,
                                            'distance': round(dist, 2)
                                        })
                                    else:
                                        # If polygon not present, include if within radius
                                        dist = haversine(street_lat, street_lon, latf, lonf)
                                        if dist <= 1.0:
                                            found_real = True
                                            result[cat].append({
                                                'name': name,
                                                'latitude': latf,
                                                'longitude': lonf,
                                                'distance': round(dist, 2)
                                            })
                                except Exception:
                                    continue
                            # If we collected any rows for this table, stop searching other tables for this category
                            if result[cat]:
                                break
                        except Exception:
                            continue

                # If we found any real facility points, return them. Otherwise fall back to synthetic counts.
                if found_real:
                    try:
                        pconn.close()
                    except Exception:
                        pass
                    return {
                        'street': street_name,
                        'street_latitude': street_lat,
                        'street_longitude': street_lon,
                        'facilities': result
                    }

                # No real rows found -> use counts -> synthetic markers as before
                row = pcur.execute(
                    'SELECT schools, sports, hawkers, healthcare, greenSpaces, carparks, transit, community FROM planning_area_facilities WHERE area_name = ?',
                    (planning_area_name,)
                ).fetchone()
                if row:
                    # DB column is 'greenSpaces', so use that as the dict key
                    counts = dict(zip(['schools','sports','hawkers','healthcare','greenSpaces','carparks','transit','community'], row))
                else:
                    counts = {k: 0 for k in ['schools','sports','hawkers','healthcare','greenSpaces','carparks','transit','community']}

                for cat in requested:
                    # Map 'parks' request to 'greenSpaces' DB column
                    count_key = 'greenSpaces' if cat == 'parks' else cat
                    n = counts.get(count_key, 0)
                    items = []
                    for i in range(n):
                        items.append({
                            'name': f"{cat.title()} {i+1}",
                            'latitude': street_lat,
                            'longitude': street_lon,
                            'distance': 0.0
                        })
                    result[cat] = items

                try:
                    pconn.close()
                except Exception:
                    pass

                return {
                    'street': street_name,
                    'street_latitude': street_lat,
                    'street_longitude': street_lon,
                    'facilities': result
                }
            except Exception:
                # If anything fails, continue with DB/memory approach below
                try:
                    pconn.close()
                except Exception:
                    pass

        # Schools
        if "schools" in requested:
            # Prefer DB tables if available
            nearby_schools = []
            for tbl in db_category_tables.get('schools', []):
                rows = _load_from_street_db(tbl)
                if rows:
                    for r in rows:
                                try:
                                    latf = float(r['latitude'])
                                    lonf = float(r['longitude'])
                                    included = False
                                    # If we have a planning-area polygon, prefer polygon containment
                                    if polygon_geojson and point_in_geojson(polygon_geojson, latf, lonf):
                                        dist = haversine(street_lat, street_lon, latf, lonf)
                                        nearby_schools.append({
                                            'name': r.get('name', 'School'),
                                            'latitude': latf,
                                            'longitude': lonf,
                                            'distance': round(dist, 2)
                                        })
                                        included = True
                                    else:
                                        dist = haversine(street_lat, street_lon, latf, lonf)
                                        if dist <= 1.0:
                                            nearby_schools.append({
                                                'name': r.get('name', 'School'),
                                                'latitude': latf,
                                                'longitude': lonf,
                                                'distance': round(dist, 2)
                                            })
                                            included = True
                                except Exception:
                                    continue
                    break

            # Fallback to MemoryAmenityRepo if DB tables not present
            if not nearby_schools:
                schools_data = MemoryAmenityRepo._schools_data or []
                for school in schools_data:
                    try:
                        lat = float(school.get("LATITUDE") or school.get("latitude", 0))
                        lon = float(school.get("LONGITUDE") or school.get("longitude", 0))
                        dist = haversine(street_lat, street_lon, lat, lon)
                        if dist <= 1.0:
                            nearby_schools.append({
                                "name": school.get("SEARCHVAL", "School"),
                                "latitude": lat,
                                "longitude": lon,
                                "distance": round(dist, 2)
                            })
                    except (ValueError, TypeError):
                        continue

            result["schools"] = nearby_schools
        
        # Sports facilities
        if "sports" in requested:
            nearby_sports = []
            for tbl in db_category_tables.get('sports', []):
                rows = _load_from_street_db(tbl)
                if rows:
                    for r in rows:
                        try:
                            latf = float(r['latitude'])
                            lonf = float(r['longitude'])
                            if polygon_geojson and point_in_geojson(polygon_geojson, latf, lonf):
                                dist = haversine(street_lat, street_lon, latf, lonf)
                                nearby_sports.append({
                                    'name': r.get('name', 'Sports Facility'),
                                    'latitude': latf,
                                    'longitude': lonf,
                                    'distance': round(dist, 2)
                                })
                            else:
                                dist = haversine(street_lat, street_lon, latf, lonf)
                                if dist <= 1.0:
                                    nearby_sports.append({
                                        'name': r.get('name', 'Sports Facility'),
                                        'latitude': latf,
                                        'longitude': lonf,
                                        'distance': round(dist, 2)
                                    })
                        except Exception:
                            continue
                    break
            if not nearby_sports:
                sports_data = MemoryAmenityRepo._sports_data or []
                for sport in sports_data:
                    try:
                        lat = float(sport.get("latitude", 0))
                        lon = float(sport.get("longitude", 0))
                        dist = haversine(street_lat, street_lon, lat, lon)
                        if dist <= 1.0:
                            nearby_sports.append({
                                "name": sport.get("name", "Sports Facility"),
                                "latitude": lat,
                                "longitude": lon,
                                "distance": round(dist, 2)
                            })
                    except (ValueError, TypeError):
                        continue
            result["sports"] = nearby_sports
        
        # Hawker centres
        if "hawkers" in requested:
            nearby_hawkers = []
            for tbl in db_category_tables.get('hawkers', []):
                rows = _load_from_street_db(tbl)
                if rows:
                    for r in rows:
                        try:
                            latf = float(r['latitude'])
                            lonf = float(r['longitude'])
                            if polygon_geojson and point_in_geojson(polygon_geojson, latf, lonf):
                                dist = haversine(street_lat, street_lon, latf, lonf)
                                nearby_hawkers.append({
                                    'name': r.get('name', 'Hawker Centre'),
                                    'latitude': latf,
                                    'longitude': lonf,
                                    'distance': round(dist, 2)
                                })
                            else:
                                dist = haversine(street_lat, street_lon, latf, lonf)
                                if dist <= 1.0:
                                    nearby_hawkers.append({
                                        'name': r.get('name', 'Hawker Centre'),
                                        'latitude': latf,
                                        'longitude': lonf,
                                        'distance': round(dist, 2)
                                    })
                        except Exception:
                            continue
                    break
            if not nearby_hawkers:
                hawkers_data = MemoryAmenityRepo._hawkers_data or []
                for hawker in hawkers_data:
                    try:
                        lat = float(hawker.get("latitude", 0))
                        lon = float(hawker.get("longitude", 0))
                        dist = haversine(street_lat, street_lon, lat, lon)
                        if dist <= 1.0:
                            nearby_hawkers.append({
                                "name": hawker.get("name", "Hawker Centre"),
                                "latitude": lat,
                                "longitude": lon,
                                "distance": round(dist, 2)
                            })
                    except (ValueError, TypeError):
                        continue
            result["hawkers"] = nearby_hawkers
        
        # Healthcare (with 0.5km radius and dedupe)
        if "healthcare" in requested:
            nearby_healthcare = []
            seen_grid = set()
            for tbl in db_category_tables.get('healthcare', []):
                rows = _load_from_street_db(tbl)
                if rows:
                    for r in rows:
                        try:
                            latf = float(r['latitude'])
                            lonf = float(r['longitude'])
                            # Prefer polygon containment for healthcare too
                            if polygon_geojson and point_in_geojson(polygon_geojson, latf, lonf):
                                dist = haversine(street_lat, street_lon, latf, lonf)
                                grid_key = (round(latf * 1000), round(lonf * 1000))
                                if grid_key not in seen_grid:
                                    seen_grid.add(grid_key)
                                    nearby_healthcare.append({
                                        'name': r.get('name', 'Clinic'),
                                        'latitude': latf,
                                        'longitude': lonf,
                                        'distance': round(dist, 2)
                                    })
                            else:
                                dist = haversine(street_lat, street_lon, latf, lonf)
                                if dist <= 0.5:
                                    grid_key = (round(latf * 1000), round(lonf * 1000))
                                    if grid_key not in seen_grid:
                                        seen_grid.add(grid_key)
                                        nearby_healthcare.append({
                                            'name': r.get('name', 'Clinic'),
                                            'latitude': latf,
                                            'longitude': lonf,
                                            'distance': round(dist, 2)
                                        })
                        except Exception:
                            continue
                    break
            if not nearby_healthcare:
                clinics_data = MemoryAmenityRepo._clinics_data or []
                for clinic in clinics_data:
                    try:
                        lat = float(clinic.get("latitude", 0))
                        lon = float(clinic.get("longitude", 0))
                        dist = haversine(street_lat, street_lon, lat, lon)
                        if dist <= 0.5:  # 0.5km for healthcare
                            grid_key = (round(lat * 1000), round(lon * 1000))
                            if grid_key not in seen_grid:
                                seen_grid.add(grid_key)
                                nearby_healthcare.append({
                                    "name": clinic.get("name", "Clinic"),
                                    "latitude": lat,
                                    "longitude": lon,
                                    "distance": round(dist, 2)
                                })
                    except (ValueError, TypeError):
                        continue
            result["healthcare"] = nearby_healthcare
        
        # Parks
        if "parks" in requested:
            nearby_parks = []
            for tbl in db_category_tables.get('parks', []):
                rows = _load_from_street_db(tbl)
                if rows:
                    for r in rows:
                        try:
                            latf = float(r['latitude'])
                            lonf = float(r['longitude'])
                            if polygon_geojson and point_in_geojson(polygon_geojson, latf, lonf):
                                dist = haversine(street_lat, street_lon, latf, lonf)
                                nearby_parks.append({
                                    'name': r.get('name', 'Park'),
                                    'latitude': latf,
                                    'longitude': lonf,
                                    'distance': round(dist, 2)
                                })
                            else:
                                dist = haversine(street_lat, street_lon, latf, lonf)
                                if dist <= 1.0:
                                    nearby_parks.append({
                                        'name': r.get('name', 'Park'),
                                        'latitude': latf,
                                        'longitude': lonf,
                                        'distance': round(dist, 2)
                                    })
                        except Exception:
                            continue
                    break
            if not nearby_parks:
                parks_data = MemoryAmenityRepo._parks_data or []
                for park in parks_data:
                    try:
                        lat = float(park.get("latitude", 0))
                        lon = float(park.get("longitude", 0))
                        dist = haversine(street_lat, street_lon, lat, lon)
                        if dist <= 1.0:
                            nearby_parks.append({
                                "name": park.get("name", "Park"),
                                "latitude": lat,
                                "longitude": lon,
                                "distance": round(dist, 2)
                            })
                    except (ValueError, TypeError):
                        continue
            result["parks"] = nearby_parks
        
        # Carparks (placeholder - you may need to load actual carpark dataset)
        if "carparks" in requested:
            nearby_carparks = []
            for tbl in db_category_tables.get('carparks', []):
                rows = _load_from_street_db(tbl)
                if rows:
                    for r in rows:
                        try:
                            latf = float(r['latitude'])
                            lonf = float(r['longitude'])
                            if polygon_geojson and point_in_geojson(polygon_geojson, latf, lonf):
                                dist = haversine(street_lat, street_lon, latf, lonf)
                                nearby_carparks.append({
                                    'name': r.get('name', 'Carpark'),
                                    'latitude': latf,
                                    'longitude': lonf,
                                    'distance': round(dist, 2)
                                })
                            else:
                                dist = haversine(street_lat, street_lon, latf, lonf)
                                if dist <= 1.0:
                                    nearby_carparks.append({
                                        'name': r.get('name', 'Carpark'),
                                        'latitude': latf,
                                        'longitude': lonf,
                                        'distance': round(dist, 2)
                                    })
                        except Exception:
                            continue
                    break
            # Fallback: empty (or try MemoryCarparkRepo if needed)
            result["carparks"] = nearby_carparks

        # Transit nodes (MRT/LRT/bus stops)
        if "transit" in requested:
            nearby_transit = []
            # Try DB tables first
            for tbl in db_category_tables.get('transit', []):
                rows = _load_from_street_db(tbl)
                if rows:
                    for r in rows:
                        try:
                            latf = float(r['latitude'])
                            lonf = float(r['longitude'])
                            if polygon_geojson and point_in_geojson(polygon_geojson, latf, lonf):
                                dist = haversine(street_lat, street_lon, latf, lonf)
                                nearby_transit.append({
                                    'name': r.get('name', r.get('id', 'Transit')),
                                    'type': r.get('type', ''),
                                    'latitude': latf,
                                    'longitude': lonf,
                                    'distance': round(dist, 2)
                                })
                            else:
                                dist = haversine(street_lat, street_lon, latf, lonf)
                                if dist <= 1.0:
                                    nearby_transit.append({
                                        'name': r.get('name', r.get('id', 'Transit')),
                                        'type': r.get('type', ''),
                                        'latitude': latf,
                                        'longitude': lonf,
                                        'distance': round(dist, 2)
                                    })
                        except Exception:
                            continue
                    break

            # Fallback to MemoryTransitRepo
            if not nearby_transit:
                try:
                    try:
                        nodes = MemoryTransitRepo().all()
                    except Exception:
                        try:
                            import asyncio
                            asyncio.get_event_loop().run_until_complete(MemoryTransitRepo.initialize())
                        except Exception:
                            pass
                        try:
                            nodes = MemoryTransitRepo().all()
                        except Exception:
                            nodes = []
                except Exception:
                    nodes = []

                for node in nodes:
                    try:
                        lat = float(node.latitude)
                        lon = float(node.longitude)
                        dist = haversine(street_lat, street_lon, lat, lon)
                        if dist <= 1.0:
                            nearby_transit.append({
                                "name": getattr(node, "name", getattr(node, "id", "Transit")),
                                "type": getattr(node, "type", ""),
                                "latitude": lat,
                                "longitude": lon,
                                "distance": round(dist, 2)
                            })
                    except Exception:
                        continue

            result["transit"] = nearby_transit
        
        # Community centres
        if "community" in requested:
            nearby_community = []
            # Try DB tables first (if available in street DB)
            for tbl in db_category_tables.get('community', []):
                rows = _load_from_street_db(tbl)
                if rows:
                    for r in rows:
                        try:
                            latf = float(r['latitude'])
                            lonf = float(r['longitude'])
                            if polygon_geojson and point_in_geojson(polygon_geojson, latf, lonf):
                                dist = haversine(street_lat, street_lon, latf, lonf)
                                nearby_community.append({
                                    'name': r.get('name', 'Community Centre'),
                                    'latitude': latf,
                                    'longitude': lonf,
                                    'distance': round(dist, 2)
                                })
                            else:
                                dist = haversine(street_lat, street_lon, latf, lonf)
                                if dist <= 1.0:
                                    nearby_community.append({
                                        'name': r.get('name', 'Community Centre'),
                                        'latitude': latf,
                                        'longitude': lonf,
                                        'distance': round(dist, 2)
                                    })
                        except Exception:
                            continue
                    break

            # Fallback to in-memory community centres dataset
            if not nearby_community:
                try:
                    from ..repositories.memory_impl import MemoryCommunityRepo
                    repo = MemoryCommunityRepo()
                    for cc in getattr(repo, '_centres', []) or []:
                        try:
                            if cc.latitude is None or cc.longitude is None:
                                continue
                            lat = float(cc.latitude)
                            lon = float(cc.longitude)
                            # Prefer polygon containment when available, else 1km radius
                            if polygon_geojson:
                                if not point_in_geojson(polygon_geojson, lat, lon):
                                    continue
                                dist = haversine(street_lat, street_lon, lat, lon)
                                nearby_community.append({
                                    'name': cc.name or 'Community Centre',
                                    'latitude': lat,
                                    'longitude': lon,
                                    'distance': round(dist, 2)
                                })
                            else:
                                dist = haversine(street_lat, street_lon, lat, lon)
                                if dist <= 1.0:
                                    nearby_community.append({
                                        'name': cc.name or 'Community Centre',
                                        'latitude': lat,
                                        'longitude': lon,
                                        'distance': round(dist, 2)
                                    })
                        except Exception:
                            continue
                except Exception:
                    pass

            result["community"] = nearby_community
        
        return {
            "street": street_name,
            "street_latitude": street_lat,
            "street_longitude": street_lon,
            "facilities": result
        }
        
    finally:
        conn.close()


# DI hook (must be overridden in main.py)
def get_trend_service() -> TrendService:
    raise RuntimeError("get_trend_service not wired. Set dependency_overrides in main.py.")

@router.get("/{area_id}/price-trend", response_model=PriceTrend)
def price_trend(
    area_id: str,
    months: int = Query(60, ge=1, le=240),
    svc: TrendService = Depends(get_trend_service),
):
    """
    Return a PriceTrend -> points: list[PricePoint].
    TrendService currently returns list[PriceRecord], so we map fields.
    """
    try:
        records = svc.series(area_id, months) or []

        # Map PriceRecord -> PricePoint shape expected by Pydantic:
        # Adjust the key names below if your PricePoint uses different field names.
        points = [
            {
                "month": r.month,                 # date
                "median": getattr(r, "medianResale", None),  # if PricePoint expects 'median'
                "p25": r.p25,
                "p75": r.p75,
                "volume": r.volume,
            }
            for r in records
        ]

        return PriceTrend(areaId=area_id, points=points)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"price-trend failed: {e}")