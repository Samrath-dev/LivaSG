# app/services/trend_service.py
from __future__ import annotations
from typing import List
from ..repositories.interfaces import IPriceRepo
from ..domain.models import PriceRecord

class TrendService:
    def __init__(self, price_repo: IPriceRepo):
        self.price_repo = price_repo

    def series(self, area_id: str, months: int) -> List[PriceRecord]:
        # Defensive wrapper: guarantees a list
        try:
            res = self.price_repo.series(area_id, months)
            return res or []
        except Exception:
            return []
#new trend service 
