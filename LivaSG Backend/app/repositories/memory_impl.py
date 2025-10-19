from datetime import date
from typing import List, Optional
from ..domain.models import PriceRecord, FacilitiesSummary, WeightsProfile, NeighbourhoodScore, CommunityCentre, Transit, Carpark, AreaCentroid
from .interfaces import IPriceRepo, IAmenityRepo, IWeightsRepo, IScoreRepo, ICommunityRepo, ITransitRepo, ICarparkRepo, IAreaRepo

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


class MemoryCommunityRepo(ICommunityRepo):
    """In-memory community centre repo with hardcoded data for now."""
    # Hardcoded community centre records - areaId keys
    _centres: List[CommunityCentre] = [
        CommunityCentre(id="cc1", name="Bukit Panjang CC", areaId="Bukit Panjang", address="123 Fajar Rd", latitude=1.38, longitude=103.77),
        CommunityCentre(id="cc2", name="Tampines CC", areaId="Tampines", address="10 Tampines Ave", latitude=1.35, longitude=103.95),
        CommunityCentre(id="cc3", name="Marine Parade CC", areaId="Marine Parade", address="5 Marine Dr", latitude=1.30, longitude=103.91)
    ]

    def list_all(self) -> List[str]:
        return [c.areaId for c in self._centres]

    def exists(self, area_id: str) -> bool:
        # case-insensitive check
        return any(c.areaId.lower() == area_id.lower() for c in self._centres)
    
    def list_centres(self, area_id: str) -> List[CommunityCentre]:
        return [c for c in self._centres if c.areaId and c.areaId.lower() == area_id.lower()]


class MemoryTransitRepo(ITransitRepo):
    """Hardcoded transit nodes (MRT/LRT/Bus) and simple area mapping."""
    # a few sample transit nodes with lat/lon
    _nodes: List[Transit] = [
        Transit(id="mrt_bukit_panjang", type="mrt", name="Bukit Panjang MRT", areaId="Bukit Panjang", latitude=1.38, longitude=103.77),
        Transit(id="lrt_bukit_panjang", type="lrt", name="Bukit Panjang LRT", areaId="Bukit Panjang", latitude=1.379, longitude=103.771),
        Transit(id="mrt_tampines", type="mrt", name="Tampines MRT", areaId="Tampines", latitude=1.352, longitude=103.94),
        Transit(id="bus_marine_parade_1", type="bus", name="Marine Parade Bus Stop 1", areaId="Marine Parade", latitude=1.3005, longitude=103.9105)
    ]

    def list_near_area(self, area_id: str) -> List[Transit]:
        # return nodes that have matching areaId (case-insensitive), else empty
        return [n for n in self._nodes if n.areaId and n.areaId.lower() == area_id.lower()]

    def all(self) -> List[Transit]:
        return list(self._nodes)


class MemoryCarparkRepo(ICarparkRepo):
    """Hardcoded carparks with capacities and positions."""
    _parks: List[Carpark] = [
        Carpark(id="cp_bukit_panjang_1", areaId="Bukit Panjang", latitude=1.381, longitude=103.772, capacity=200),
        Carpark(id="cp_tampines_1", areaId="Tampines", latitude=1.353, longitude=103.945, capacity=500),
        Carpark(id="cp_marine_1", areaId="Marine Parade", latitude=1.301, longitude=103.911, capacity=120)
    ]

    def list_near_area(self, area_id: str) -> List[Carpark]:
        return [p for p in self._parks if p.areaId and p.areaId.lower() == area_id.lower()]

    def all(self) -> List[Carpark]:
        return list(self._parks)


class MemoryAreaRepo(IAreaRepo):
    """In-memory mapping of areaId -> centroid coordinates."""
    _centroids: List[AreaCentroid] = [
        AreaCentroid(areaId="Bukit Panjang", latitude=1.379, longitude=103.771),
        AreaCentroid(areaId="Tampines", latitude=1.352, longitude=103.94),
        AreaCentroid(areaId="Marine Parade", latitude=1.3005, longitude=103.9105),
        AreaCentroid(areaId="Bedok", latitude=1.323, longitude=103.930)
    ]

    def centroid(self, area_id: str) -> AreaCentroid | None:
        for c in self._centroids:
            if c.areaId.lower() == area_id.lower():
                return c
        return None

    def list_all(self) -> List[AreaCentroid]:
        return list(self._centroids)