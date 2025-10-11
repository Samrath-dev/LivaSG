from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Dict, List

class FacilitiesSummary(BaseModel):
    schools: int = 0
    sports: int = 0
    hawkers: int = 0
    healthcare: int = 0
    greenSpaces: int = 0
    carparks: int = 0

class PriceRecord(BaseModel):
    areaId: str
    month: date
    medianResale: int
    p25: int
    p75: int
    volume: int

class WeightsProfile(BaseModel):
    id: str = "default"
    label: str = "Default"
    wAff: float = 0.2
    wAcc: float = 0.2
    wAmen: float = 0.2
    wEnv: float = 0.2
    wCom: float = 0.2

class NeighbourhoodScore(BaseModel):
    areaId: str
    total: float
    weightsProfileId: str = "default"
    computedAt: datetime = Field(default_factory=datetime.utcnow)

class CategoryBreakdown(BaseModel):
    # keys are: Affordability, Accessibility, Amenities, Environment, Community
    scores: Dict[str, float]

class SearchFilters(BaseModel):
    facilities: List[str] = []
    price_range: List[int] = Field(default_factory=lambda: [500000, 3000000])
    search_query: str = ""

class LocationResult(BaseModel):
    id: int
    street: str
    area: str
    district: str
    price_range: List[int]
    avg_price: int
    facilities: List[str]
    description: str
    growth: float
    amenities: List[str]


class CommunityCentre(BaseModel):
    # Represents a community centre (CC) in an area.
    id: str
    name: str
    areaId: str
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None