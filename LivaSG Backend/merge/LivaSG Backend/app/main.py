# app/main.py
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

<<<<<<< HEAD
# transit debug
=======
#transit debug
>>>>>>> aebfb1e88ac24c0de92153cc418cb9948149cd09
from app.api import transit_debug

# ---- Load env (shell + project .env) ----
load_dotenv()
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

# ---- Routers ----
from app.api import map_controller, details_controller, search_controller, onemap_controller
from app.api import weights_controller
<<<<<<< HEAD
from app.api import ranks_controller  # Only ranks controller now
from app.api import shortlist_controller, settings_controller
=======
from app.api import ranks_controller, preference_controller
from app.api import shortlist_controller, settings_controller  # NEW
>>>>>>> aebfb1e88ac24c0de92153cc418cb9948149cd09

# ---- Repositories ----
from app.repositories.memory_impl import (
    MemoryPriceRepo, MemoryAmenityRepo, MemoryWeightsRepo,
    MemoryScoreRepo, MemoryTransitRepo, MemoryCarparkRepo,
<<<<<<< HEAD
    MemoryAreaRepo, MemoryCommunityRepo,
    MemorySavedLocationRepo
)
# Use SQLite for ranks persistence
from app.repositories.sqlite_rank_repo import SQLiteRankRepo
=======
    MemoryAreaRepo, MemoryCommunityRepo, MemoryRankRepo, 
    MemoryPreferenceRepo, MemorySavedLocationRepo
)
>>>>>>> aebfb1e88ac24c0de92153cc418cb9948149cd09

# ---- Services ----
from app.services.trend_service import TrendService
from app.services.rating_engine import RatingEngine
from app.services.search_service import SearchService
<<<<<<< HEAD
from app.services.shortlist_service import ShortlistService
from app.services.settings_service import SettingsService
=======
from app.services.preference_service import PreferenceService
from app.services.shortlist_service import ShortlistService  # NEW
from app.services.settings_service import SettingsService    # NEW
>>>>>>> aebfb1e88ac24c0de92153cc418cb9948149cd09

# ---- Integrations ----
from app.integrations.onemap_client import OneMapClientHardcoded
from app.repositories.api_planning_repo import OneMapPlanningAreaRepo

<<<<<<< HEAD
=======

>>>>>>> aebfb1e88ac24c0de92153cc418cb9948149cd09
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
<<<<<<< HEAD
di_ranks     = SQLiteRankRepo()  # Persistent SQLite storage
=======
di_ranks     = MemoryRankRepo()  # NEW
>>>>>>> aebfb1e88ac24c0de92153cc418cb9948149cd09

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
<<<<<<< HEAD
    ranks=di_ranks,
)
di_search = SearchService(di_engine, di_onemap_client)

di_saved_location_repo = MemorySavedLocationRepo()
di_shortlist_service = ShortlistService(di_saved_location_repo)
di_settings_service = SettingsService(di_ranks, di_weights)

=======
    ranks=di_ranks,   # NEW
)
di_search = SearchService(di_engine, di_onemap_client)

di_preference_repo = MemoryPreferenceRepo()           # NEW
di_saved_location_repo = MemorySavedLocationRepo()    # NEW

di_shortlist_service = ShortlistService(di_saved_location_repo) 
di_preference_service = PreferenceService(di_preference_repo) 
di_settings_service = SettingsService(di_preference_repo, di_weights) 

# new
>>>>>>> aebfb1e88ac24c0de92153cc418cb9948149cd09
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: warm any async caches you want ready
    await MemoryTransitRepo.initialize()
<<<<<<< HEAD
    yield
=======
   
    yield
   

>>>>>>> aebfb1e88ac24c0de92153cc418cb9948149cd09

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

<<<<<<< HEAD
# ranks (now handles both ranks and preferences)
app.dependency_overrides[ranks_controller.get_rank_service] = lambda: di_ranks

# transit debug
app.dependency_overrides[transit_debug.get_transit_repo] = lambda: di_transit

# shortlist and settings
app.dependency_overrides[shortlist_controller.get_shortlist_service] = lambda: di_shortlist_service
app.dependency_overrides[settings_controller.get_settings_service] = lambda: di_settings_service 
app.dependency_overrides[settings_controller.get_shortlist_service] = lambda: di_shortlist_service

# ========= Routers =========
app.include_router(map_controller.router)
app.include_router(details_controller.router)
=======
# ranks
app.dependency_overrides[ranks_controller.get_rank_service] = lambda: di_ranks

#transit debug
app.dependency_overrides[transit_debug.get_transit_repo] = lambda: di_transit

app.dependency_overrides[shortlist_controller.get_shortlist_service] = lambda: di_shortlist_service
app.dependency_overrides[settings_controller.get_settings_service] = lambda: di_settings_service 
app.dependency_overrides[settings_controller.get_shortlist_service] = lambda: di_shortlist_service
app.dependency_overrides[settings_controller.get_preference_service] = lambda: di_preference_service
app.dependency_overrides[preference_controller.get_preference_service] = lambda: di_preference_service

# ========= Routers =========
app.include_router(map_controller.router)
app.include_router(details_controller.router)  # prefix handled inside the router
>>>>>>> aebfb1e88ac24c0de92153cc418cb9948149cd09
app.include_router(search_controller.router, prefix="/search", tags=["search"])
app.include_router(onemap_controller.router)
app.include_router(weights_controller.router)
app.include_router(ranks_controller.router)
<<<<<<< HEAD
app.include_router(transit_debug.router)
=======

#transit debug
app.include_router(transit_debug.router)

app.include_router(preference_controller.router)
>>>>>>> aebfb1e88ac24c0de92153cc418cb9948149cd09
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
<<<<<<< HEAD
        return {"error": str(e)}
=======
        return {"error": str(e)}
>>>>>>> aebfb1e88ac24c0de92153cc418cb9948149cd09
