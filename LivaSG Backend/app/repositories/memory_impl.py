from datetime import date
from typing import List, Optional
from ..domain.models import PriceRecord, FacilitiesSummary, WeightsProfile, NeighbourhoodScore
from .interfaces import IPriceRepo, IAmenityRepo, IWeightsRepo, IScoreRepo

class MemoryPriceRepo(IPriceRepo):
    def series(self, area_id: str, months: int) -> List[PriceRecord]:
        base = 500_000 if area_id != "Tampines" else 520_000
        out: List[PriceRecord] = []
        y, m = 2024, 1
        for i in range(months):
            out.append(PriceRecord(
                areaId=area_id, month=date(y, m, 1),
                medianResale=base + i*1200, p25=base-40_000, p75=base+40_000, volume=50-i%5
            ))
            m += 1
            if m > 12: m, y = 1, y+1
        return out

class MemoryAmenityRepo(IAmenityRepo):
    def facilities_summary(self, area_id: str) -> FacilitiesSummary:
        return FacilitiesSummary(
            schools=5 if area_id=="Bedok" else 4,
            sports=2, hawkers=3, healthcare=4, greenSpaces=6, carparks=8
        )

class MemoryWeightsRepo(IWeightsRepo):
    _profiles = [WeightsProfile()]
    def get_active(self) -> WeightsProfile: return self._profiles[0]
    def list(self) -> List[WeightsProfile]: return list(self._profiles)
    def save(self, p: WeightsProfile) -> None: self._profiles.insert(0, p)

class MemoryScoreRepo(IScoreRepo):
    _scores: List[NeighbourhoodScore] = []
    def latest(self, area_id: str, weights_id: str) -> Optional[NeighbourhoodScore]:
        arr = [s for s in self._scores if s.areaId==area_id and s.weightsProfileId==weights_id]
        return arr[-1] if arr else None
    def save(self, s: NeighbourhoodScore) -> None: self._scores.append(s)