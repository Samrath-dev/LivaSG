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
    # Try street-level first
    try:
        import os, sqlite3
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
        street_db_path = os.path.join(base_dir, 'street_geocode.db')
        conn = sqlite3.connect(street_db_path)
        cur = conn.cursor()
        try:
            row = cur.execute(
                "SELECT 1 FROM street_locations WHERE UPPER(street_name) = UPPER(?) LIMIT 1",
                (area_id,)
            ).fetchone()
        finally:
            conn.close()

        if row:
            # area_id is a street — compute detailed street-specific breakdown
            return await street_breakdown(area_id)
        else:
            # If exact match failed, try a normalized match against stored street names
            try:
                conn = sqlite3.connect(street_db_path)
                cur = conn.cursor()
                all_db_streets = cur.execute(
                    "SELECT street_name FROM street_locations WHERE status = 'found'"
                ).fetchall()

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
                for (s_name,) in all_db_streets:
                    if _norm_name(s_name) == target_norm:
                        conn.close()
                        return await street_breakdown(s_name)
                conn.close()
            except Exception:
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
        if loc:
            street_lat, street_lon = float(loc[0]), float(loc[1])
        else:
            # Fallback: treat input as planning area id and use centroid if available
            try:
                _, centroid = MemoryAreaRepo.getAreaGeometry(street_name)
                if centroid is None:
                    # Try title-cased area name
                    _, centroid = MemoryAreaRepo.getAreaGeometry(street_name.title())
                if centroid is not None:
                    street_lat, street_lon = float(centroid.latitude), float(centroid.longitude)
                else:
                    return {"error": f"Street or area '{street_name}' not found", "facilities": {}}
            except Exception:
                return {"error": f"Street or area '{street_name}' not found", "facilities": {}}
        
        # Parse requested types (include transit)
        requested = types.lower().split(",") if types != "all" else ["schools", "sports", "hawkers", "healthcare", "parks", "carparks", "transit"]

        # Initialize repo to get datasets
        await MemoryAmenityRepo.initialize()

        result = {}
        
        # Schools
        if "schools" in requested:
            schools_data = MemoryAmenityRepo._schools_data or []
            nearby_schools = []
            for school in schools_data:
                try:
                    lat = float(school.get("LATITUDE") or school.get("latitude", 0))
                    lon = float(school.get("LONGITUDE") or school.get("longitude", 0))
                    dist = haversine(street_lat, street_lon, lat, lon)
                    if dist <= 1.0:  # within 1km
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
            sports_data = MemoryAmenityRepo._sports_data or []
            nearby_sports = []
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
            hawkers_data = MemoryAmenityRepo._hawkers_data or []
            nearby_hawkers = []
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
            clinics_data = MemoryAmenityRepo._clinics_data or []
            nearby_healthcare = []
            seen_grid = set()
            for clinic in clinics_data:
                try:
                    lat = float(clinic.get("latitude", 0))
                    lon = float(clinic.get("longitude", 0))
                    dist = haversine(street_lat, street_lon, lat, lon)
                    if dist <= 0.5:  # 0.5km for healthcare
                        # Dedupe by ~100m grid
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
            parks_data = MemoryAmenityRepo._parks_data or []
            nearby_parks = []
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
            # For now, return empty or implement if you have carpark lat/lon data
            result["carparks"] = []

        # Transit nodes (MRT/LRT/bus stops)
        if "transit" in requested:
            try:
                try:
                    nodes = MemoryTransitRepo().all()
                except Exception:
                    # If not initialized, attempt async initialize then .all()
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

            nearby_transit = []
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