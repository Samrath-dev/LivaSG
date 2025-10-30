# app/domain/models.py
from pydantic import BaseModel, Field
from datetime import date, datetime
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
    name: str = "Default"
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
    found: int
    totalNumPages: int
    pageNum: int
    results: List[OneMapSearchResult]

class CommunityCentre(BaseModel):
    id: str
    name: str
    areaId: str
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None

class Transit(BaseModel):
    id: str
    type: str
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
    areaId: str
    latitude: float
    longitude: float

class RankProfile(BaseModel):
    rAff: int = Field(..., ge=1, le=5)
    rAcc: int = Field(..., ge=1, le=5)
    rAmen: int = Field(..., ge=1, le=5)
    rEnv: int = Field(..., ge=1, le=5)
    rCom: int = Field(..., ge=1, le=5)

class SavedLocation(BaseModel):
    postal_code: str
    address: str
    area: str
    name: Optional[str] = None
    notes: Optional[str] = None
    saved_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ExportData(BaseModel):
    ranks: Optional[RankProfile] = None
    saved_locations: List[SavedLocation]
    weights: Optional[WeightsProfile] = None
    export_date: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ImportRequest(BaseModel):
    data: str
    import_type: str = "json"

class PricePoint(BaseModel):
    month: date
    median: Optional[int] = None
    p25: Optional[int] = None
    p75: Optional[int] = None
    volume: Optional[int] = None

class PriceTrend(BaseModel):
    areaId: str
    points: List[PricePoint]