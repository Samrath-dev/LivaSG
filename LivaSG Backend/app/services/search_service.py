from typing import List
from ..domain.models import NeighbourhoodScore, WeightsProfile
from .rating_engine import RatingEngine

class SearchService:
    def __init__(self, engine: RatingEngine): self.engine = engine

    def rank(self, areas: List[str], weights: WeightsProfile) -> List[NeighbourhoodScore]:
        scores = [self.engine.aggregate(a, weights) for a in areas]
        return sorted(scores, key=lambda s: s.total, reverse=True)