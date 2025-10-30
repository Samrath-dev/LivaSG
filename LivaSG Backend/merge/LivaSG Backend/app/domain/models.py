<<<<<<< HEAD
# app/domain/models.py
=======
>>>>>>> aebfb1e88ac24c0de92153cc418cb9948149cd09
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
<<<<<<< HEAD
    name: str = "Default"
=======
    label: str = "Default"
>>>>>>> aebfb1e88ac24c0de92153cc418cb9948149cd09
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
<<<<<<< HEAD
=======
    # keys are: Affordability, Accessibility, Amenities, Environment, Community
>>>>>>> aebfb1e88ac24c0de92153cc418cb9948149cd09
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

<<<<<<< HEAD
class OneMapSearchResult(BaseModel):
=======

class OneMapSearchResult(BaseModel):
    """Model matching OneMap search API response"""
>>>>>>> aebfb1e88ac24c0de92153cc418cb9948149cd09
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

<<<<<<< HEAD
class OneMapSearchResponse(BaseModel):
=======

class OneMapSearchResponse(BaseModel):
    """Full OneMap search response"""
>>>>>>> aebfb1e88ac24c0de92153cc418cb9948149cd09
    found: int
    totalNumPages: int
    pageNum: int
    results: List[OneMapSearchResult]

<<<<<<< HEAD
class CommunityCentre(BaseModel):
=======

class CommunityCentre(BaseModel):
    # Represents a community centre (CC) in an area.
>>>>>>> aebfb1e88ac24c0de92153cc418cb9948149cd09
    id: str
    name: str
    areaId: str
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None

<<<<<<< HEAD
class Transit(BaseModel):
    id: str
    type: str
=======

class Transit(BaseModel):
    """A transit node: can be MRT, LRT or Bus stop."""
    id: str
    type: str  # expected: 'mrt' | 'lrt' | 'bus'
>>>>>>> aebfb1e88ac24c0de92153cc418cb9948149cd09
    name: str | None = None
    areaId: str | None = None
    latitude: float | None = None
    longitude: float | None = None

<<<<<<< HEAD
=======

>>>>>>> aebfb1e88ac24c0de92153cc418cb9948149cd09
class Carpark(BaseModel):
    id: str
    areaId: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    capacity: int | None = None

<<<<<<< HEAD
class AreaCentroid(BaseModel):
=======

class AreaCentroid(BaseModel):
    """Simple area centroid record for proximity calculations."""
>>>>>>> aebfb1e88ac24c0de92153cc418cb9948149cd09
    areaId: str
    latitude: float
    longitude: float

<<<<<<< HEAD
class RankProfile(BaseModel):
    rAff: int = Field(..., ge=1, le=5)
    rAcc: int = Field(..., ge=1, le=5)
    rAmen: int = Field(..., ge=1, le=5)
    rEnv: int = Field(..., ge=1, le=5)
    rCom: int = Field(..., ge=1, le=5)
=======

from pydantic import BaseModel, Field
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

>>>>>>> aebfb1e88ac24c0de92153cc418cb9948149cd09

class SavedLocation(BaseModel):
    postal_code: str
    address: str
    area: str
<<<<<<< HEAD
    name: Optional[str] = None
    notes: Optional[str] = None
    saved_at: datetime = Field(default_factory=datetime.now)
=======
    name: Optional[str] = None #remove if you don't want custom name for area
    notes: Optional[str] = None
    saved_at: datetime=Field(default_factory=lambda: datetime.now())
>>>>>>> aebfb1e88ac24c0de92153cc418cb9948149cd09

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ExportData(BaseModel):
<<<<<<< HEAD
    ranks: Optional[RankProfile] = None
    saved_locations: List[SavedLocation]
    weights: Optional[WeightsProfile] = None
    export_date: datetime = Field(default_factory=datetime.now)
    
=======
    preferences: UserPreference
    saved_locations: List[SavedLocation]
    weights: Optional[WeightsProfile]=None
    export_date: datetime = Field(default_factory=lambda: datetime.now())
>>>>>>> aebfb1e88ac24c0de92153cc418cb9948149cd09
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ImportRequest(BaseModel):
    data: str
<<<<<<< HEAD
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
=======
    import_type: str = "csv" #functional requirements asked for csv or pdf, but json will suit it better

from datetime import date
from pydantic import BaseModel

class PricePoint(BaseModel):
    month: date
    median: int

class PriceTrend(BaseModel):
    areaId: str
    points: list[PricePoint]
>>>>>>> aebfb1e88ac24c0de92153cc418cb9948149cd09
