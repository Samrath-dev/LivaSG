from typing import List
from ..domain.models import PriceRecord
from ..repositories.interfaces import IPriceRepo

class TrendService:
    def __init__(self, prices: IPriceRepo): self.prices = prices
    def series(self, area_id: str, months: int) -> List[PriceRecord]:
        return self.prices.series(area_id, months)