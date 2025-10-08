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