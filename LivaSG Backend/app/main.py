# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# --- Existing Routers (module imports only) ---
from app.api import map_controller, details_controller, search_controller
from app.api import onemap_controller  # keep after DI objects created if you prefer

# --- new
from app.api import weights_controller  

# --- Existing Memory Repositories ---
from app.repositories.memory_impl import (
    MemoryPriceRepo, MemoryAmenityRepo, MemoryWeightsRepo,
    MemoryScoreRepo, MemoryTransitRepo, MemoryCarparkRepo,
    MemoryAreaRepo, MemoryCommunityRepo
)

# --- Existing Services ---
from app.services.trend_service import TrendService
from app.services.rating_engine import RatingEngine
from app.services.search_service import SearchService

# --- NEW: OneMap Integrations (hardcoded token path) ---
from app.integrations.onemap_client import OneMapClientHardcoded
from app.repositories.api_planning_repo import OneMapPlanningAreaRepo

# --- Create DI singletons (memory repos) ---
di_price     = MemoryPriceRepo()
di_amenity   = MemoryAmenityRepo()
di_weights   = MemoryWeightsRepo()
di_scores    = MemoryScoreRepo()
di_community = MemoryCommunityRepo()
di_transit   = MemoryTransitRepo()
di_carpark   = MemoryCarparkRepo()
di_area      = MemoryAreaRepo()   # still used by RatingEngine for now

# --- Create DI for OneMap planning areas ---
di_onemap_client = OneMapClientHardcoded()
di_planning_repo = OneMapPlanningAreaRepo(di_onemap_client)

# --- Services ---
di_trend  = TrendService(di_price)
di_engine = RatingEngine(
    di_price,
    di_amenity,
    di_scores,
    di_community,
    di_transit,
    di_carpark,
    di_area
)
di_search = SearchService(di_engine, di_onemap_client)

# --- FastAPI app ---
app = FastAPI(title="LivaSG API")

# CORS for local React dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Dependency overrides (avoid circular imports) ----
app.dependency_overrides[onemap_controller.get_planning_repo] = lambda: di_planning_repo
app.dependency_overrides[map_controller.get_engine] = lambda: di_engine
app.dependency_overrides[map_controller.get_weights_service] = lambda: di_weights
app.dependency_overrides[map_controller.get_planning_repo] = lambda: di_planning_repo

# Provide the OneMap client instance to controllers that depend on it
app.dependency_overrides[onemap_controller.get_onemap_client] = lambda: di_onemap_client

# new
app.dependency_overrides[weights_controller.get_weights_repo] = lambda: di_weights

# ---- Mount routers ----
app.include_router(map_controller.router)
app.include_router(details_controller.router, prefix="/details", tags=["details"])
app.include_router(search_controller.router, prefix="/search", tags=["search"])
app.include_router(onemap_controller.router)

# new
app.include_router(weights_controller.router)

# Health
@app.get("/")
def health():
    return {"ok": True}

# --- simple PopAPI debug probe ---
@app.get("/test-onemap")
async def test_onemap():
    import httpx
    url = "https://www.onemap.gov.sg/api/public/popapi/getAllPlanningarea?year=2019"
    headers = getattr(di_onemap_client, "_headers_pop", {})
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(url, headers=headers)
            return {"status": r.status_code, "raw": r.text[:500]}
    except Exception as e:
        return {"error": str(e)}