from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Routers
from .api import map_controller, details_controller, search_controller

# Repos
from .repositories.memory_impl import (
    MemoryPriceRepo, MemoryAmenityRepo, MemoryWeightsRepo, MemoryScoreRepo, MemoryTransitRepo, MemoryCarparkRepo, MemoryAreaRepo
)
from .repositories.memory_impl import MemoryCommunityRepo

# Services
from .services.trend_service import TrendService
from .services.rating_engine import RatingEngine
from .services.search_service import SearchService

# --- very light DI container (module-level for skeleton) ---
di_price   = MemoryPriceRepo()
di_amenity = MemoryAmenityRepo()
di_weights = MemoryWeightsRepo()
di_scores  = MemoryScoreRepo()
di_community = MemoryCommunityRepo()
di_transit = MemoryTransitRepo()
di_carpark = MemoryCarparkRepo()
di_area = MemoryAreaRepo()

di_trend   = TrendService(di_price)
di_engine  = RatingEngine(di_price, di_amenity, di_scores, di_community, di_transit, di_carpark, di_area)
di_search  = SearchService(di_engine)

app = FastAPI(title="LivaSG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(map_controller.router, prefix="/map", tags=["map"])
app.include_router(details_controller.router, prefix="/details", tags=["details"])
app.include_router(search_controller.router, prefix="/search", tags=["search"])

@app.get("/")
def health(): return {"ok": True}