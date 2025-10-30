# app/main.py
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

#transit debug
from app.api import transit_debug

# ---- Load env (shell + project .env) ----
load_dotenv()
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

# ---- Routers ----
from app.api import map_controller, details_controller, search_controller, onemap_controller
from app.api import weights_controller
from app.api import ranks_controller
from app.api import shortlist_controller, settings_controller  # NEW

# ---- Repositories ----
from app.repositories.memory_impl import (
    MemoryPriceRepo, MemoryAmenityRepo, MemoryWeightsRepo,
    MemoryScoreRepo, MemoryTransitRepo, MemoryCarparkRepo,
    MemoryAreaRepo, MemoryCommunityRepo, MemoryRankRepo, 
    MemorySavedLocationRepo
)

# ---- Services ----
from app.services.trend_service import TrendService
from app.services.rating_engine import RatingEngine
from app.services.search_service import SearchService
from app.services.shortlist_service import ShortlistService  # NEW
from app.services.settings_service import SettingsService    # NEW

# ---- Integrations ----
from app.integrations.onemap_client import OneMapClientHardcoded
from app.repositories.api_planning_repo import OneMapPlanningAreaRepo


# DI
# repos
di_price     = MemoryPriceRepo()
di_amenity   = MemoryAmenityRepo()
di_weights   = MemoryWeightsRepo()
di_scores    = MemoryScoreRepo()
di_community = MemoryCommunityRepo()
di_transit   = MemoryTransitRepo()
di_carpark   = MemoryCarparkRepo()
di_area      = MemoryAreaRepo()
di_ranks     = MemoryRankRepo()  # NEW

# planning areas / onemap
di_onemap_client = OneMapClientHardcoded()
di_planning_repo = OneMapPlanningAreaRepo(di_onemap_client)

# services
di_trend  = TrendService(di_price)
di_engine = RatingEngine(
    di_price,
    di_amenity,
    di_scores,
    di_community,
    di_transit,
    di_carpark,
    di_area,
    ranks=di_ranks,   # NEW
)
di_search = SearchService(di_engine, di_onemap_client)
             # NEW
di_saved_location_repo = MemorySavedLocationRepo()    # NEW

di_shortlist_service = ShortlistService(di_saved_location_repo) 
di_settings_service = SettingsService(di_weights) 

# new
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: warm any async caches you want ready
    await MemoryTransitRepo.initialize()
   
    yield
   


# app
app = FastAPI(title="LivaSG API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========= Dependency overrides =========
# onemap planning areas + client
app.dependency_overrides[onemap_controller.get_planning_repo] = lambda: di_planning_repo
app.dependency_overrides[onemap_controller.get_onemap_client] = lambda: di_onemap_client

# map
app.dependency_overrides[map_controller.get_engine] = lambda: di_engine
app.dependency_overrides[map_controller.get_weights_service] = lambda: di_weights
app.dependency_overrides[map_controller.get_planning_repo] = lambda: di_planning_repo

# details (trend)
app.dependency_overrides[details_controller.get_trend_service] = lambda: di_trend

# weights
app.dependency_overrides[weights_controller.get_weights_repo] = lambda: di_weights

# ranks
app.dependency_overrides[ranks_controller.get_rank_service] = lambda: di_ranks

#transit debug
app.dependency_overrides[transit_debug.get_transit_repo] = lambda: di_transit

app.dependency_overrides[shortlist_controller.get_shortlist_service] = lambda: di_shortlist_service
app.dependency_overrides[settings_controller.get_settings_service] = lambda: di_settings_service 
app.dependency_overrides[settings_controller.get_shortlist_service] = lambda: di_shortlist_service

# ========= Routers =========
app.include_router(map_controller.router)
app.include_router(details_controller.router)  # prefix handled inside the router
app.include_router(search_controller.router, prefix="/search", tags=["search"])
app.include_router(onemap_controller.router)
app.include_router(weights_controller.router)
app.include_router(ranks_controller.router)

#transit debug
app.include_router(transit_debug.router)
app.include_router(shortlist_controller.router)
app.include_router(settings_controller.router)

# ========= Health / debug =========
@app.get("/")
def health():
    return {"ok": True}

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
