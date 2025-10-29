from fastapi import APIRouter, Query
from ..domain.models import FacilitiesSummary, PriceRecord, CategoryBreakdown
router = APIRouter()

@router.get("/{area_id}/breakdown", response_model=CategoryBreakdown)
async def breakdown(area_id: str):
    """Try street-level breakdown first (if area_id is a street), otherwise fall back to area-level."""
    try:
        # Attempt street-level breakdown first
        return await street_breakdown(area_id)
    except Exception:
        # Fall back to original area-level breakdown
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
            SELECT schools, sports, hawkers, healthcare, greenSpaces, carparks
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

        schools, sports, hawkers, healthcare, parks, carparks = fac
        lat, lon = float(loc[0]), float(loc[1])

        # Slightly higher normalization to avoid saturating at 1.0 so nearby streets can differ
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
    from ..repositories.memory_impl import MemoryAmenityRepo
    
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
        
        if not loc:
            return {"error": f"Street {street_name} not found", "facilities": {}}
        
        street_lat, street_lon = float(loc[0]), float(loc[1])
        
        # Parse requested types
        requested = types.lower().split(",") if types != "all" else ["schools", "sports", "hawkers", "healthcare", "parks", "carparks"]
        
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
        
        return {
            "street": street_name,
            "street_latitude": street_lat,
            "street_longitude": street_lon,
            "facilities": result
        }
        
    finally:
        conn.close()

@router.get("/{area_id}/price-trend", response_model=list[PriceRecord])
def price_trend(area_id: str, months: int = Query(24, ge=1, le=120)):
    from ..main import di_trend
    return di_trend.series(area_id, months)
