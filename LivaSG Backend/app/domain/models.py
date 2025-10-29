from pydantic import BaseModel, Field
from datetime import date, datetime, timezone, timedelta
from typing import Dict, List, Optional


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
    computedAt: datetime = Field(default_factory=lambda: datetime.now())

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
    latitude: float | None = None
    longitude: float | None = None


class OneMapSearchResult(BaseModel):
    """Model matching OneMap search API response"""
    SEARCHVAL: str
    BLK_NO: str = ""
    ROAD_NAME: str = ""
    BUILDING: str = ""
    ADDRESS: str
    POSTAL: str = ""
    X: str = ""
    Y: str = ""
    LATITUDE: str
    LONGITUDE: str


class OneMapSearchResponse(BaseModel):
    """Full OneMap search response"""
    found: int
    totalNumPages: int
    pageNum: int
    results: List[OneMapSearchResult]


class CommunityCentre(BaseModel):
    # Represents a community centre (CC) in an area.
    id: str
    name: str
    areaId: str
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class Transit(BaseModel):
    """A transit node: can be MRT, LRT or Bus stop."""
    id: str
    type: str  # expected: 'mrt' | 'lrt' | 'bus'
    name: str | None = None
    areaId: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class Carpark(BaseModel):
    id: str
    areaId: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    capacity: int | None = None


class AreaCentroid(BaseModel):
    """Simple area centroid record for proximity calculations."""
    areaId: str
    latitude: float
    longitude: float


class RankProfile(BaseModel):
    # 1 = highest priority … 5 = lowest. Duplicates allowed.
    rAff: int = Field(..., ge=1, le=5)
    rAcc: int = Field(..., ge=1, le=5)
    rAmen: int = Field(..., ge=1, le=5)
    rEnv: int  = Field(..., ge=1, le=5)
    rCom: int  = Field(..., ge=1, le=5)


class UserPreference(BaseModel):
    category_ranks: Dict[str, int] = Field(
        default_factory=lambda:{
            "Affordability": 3, #mid point default
            "Accessibility": 3,
            "Amenities": 3,
            "Environment": 3,
            "Community": 3
        }
    )

    created_at: datetime = Field(default_factory=lambda: datetime.now())
    updated_at: datetime = Field(default_factory=lambda: datetime.now())


class SavedLocation(BaseModel):
    postal_code: str
    address: str
    area: str
    name: Optional[str] = None #remove if you don't want custom name for area
    notes: Optional[str] = None
    saved_at: datetime=Field(default_factory=lambda: datetime.now())

class ExportData(BaseModel):
    preferences: UserPreference
    saved_locations: List[SavedLocation]
    weights: Optional[WeightsProfile]=None
    export_date: datetime = Field(default_factory=lambda: datetime.now())

class ImportRequest(BaseModel):
    data: str
    import_type: str = "csv" #functional requirements asked for csv or pdf, but json will suit it better