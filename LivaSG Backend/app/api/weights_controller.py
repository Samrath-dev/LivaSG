# app/api/weights_controller.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, conint, confloat
from typing import Optional, Dict
from uuid import uuid4

from app.repositories.interfaces import IWeightsRepo
from app.domain.models import WeightsProfile

router = APIRouter(prefix="/weights", tags=["weights"])

# --- DI hook
def get_weights_repo() -> IWeightsRepo:
    raise RuntimeError("get_weights_repo not wired. Set dependency_overrides in main.py.")

# -------- Request models --------

class WeightValues(BaseModel):
    # Accept normalized weights in [0,1]; they don't have to sum to 1—we'll normalize
    wAff: confloat(ge=0.0, le=1.0)
    wAcc: confloat(ge=0.0, le=1.0)
    wAmen: confloat(ge=0.0, le=1.0)
    wEnv: confloat(ge=0.0, le=1.0)
    wCom: confloat(ge=0.0, le=1.0)

class WeightRanks(BaseModel):
    # Accept user “priority” ranks (1–5). Higher means more important.
    aff: conint(ge=1, le=5) = Field(..., description="Affordability rank 1-5")
    acc: conint(ge=1, le=5) = Field(..., description="Accessibility rank 1-5")
    amen: conint(ge=1, le=5) = Field(..., description="Amenities rank 1-5")
    env: conint(ge=1, le=5) = Field(..., description="Environment rank 1-5")
    com: conint(ge=1, le=5) = Field(..., description="Community rank 1-5")

class WeightsUpsert(BaseModel):
    # Either provide explicit weights OR ranks. If both are provided, `weights` wins.
    weights: Optional[WeightValues] = None
    ranks: Optional[WeightRanks] = None
    profileName: Optional[str] = Field(None, description="Optional label to show in UI")

# -------- Helpers --------

def _normalize(d: Dict[str, float]) -> Dict[str, float]:
    s = sum(max(0.0, v) for v in d.values())
    if s <= 0:
        # fallback to equal weighting
        n = len(d)
        return {k: 1.0 / n for k in d}
    return {k: max(0.0, v) / s for k, v in d.items()}

def _from_ranks(r: WeightRanks) -> Dict[str, float]:
    # Simple, predictable mapping: weight = rank / sum(ranks)
    raw = {
        "wAff": float(r.aff),
        "wAcc": float(r.acc),
        "wAmen": float(r.amen),
        "wEnv": float(r.env),
        "wCom": float(r.com),
    }
    return _normalize(raw)

# -------- Routes --------

@router.get("", response_model=WeightsProfile)
def get_active(repo: IWeightsRepo = Depends(get_weights_repo)) -> WeightsProfile:
    """Return the currently active weights profile."""
    return repo.get_active()

@router.post("", response_model=WeightsProfile)
def upsert_weights(body: WeightsUpsert, repo: IWeightsRepo = Depends(get_weights_repo)) -> WeightsProfile:
    """
    Create a new weights profile and make it active.
    - If `weights` provided, we normalize and use them.
    - Else if `ranks` provided, we convert ranks (1-5) → normalized weights.
    """
    if body.weights:
        w_raw = {
            "wAff": body.weights.wAff,
            "wAcc": body.weights.wAcc,
            "wAmen": body.weights.wAmen,
            "wEnv": body.weights.wEnv,
            "wCom": body.weights.wCom,
        }
        w_norm = _normalize(w_raw)
    elif body.ranks:
        w_norm = _from_ranks(body.ranks)
    else:
        raise HTTPException(status_code=400, detail="Provide either `weights` or `ranks`.")

    profile = WeightsProfile(
        id=str(uuid4()),
        name=body.profileName or "Custom",
        wAff=w_norm["wAff"],
        wAcc=w_norm["wAcc"],
        wAmen=w_norm["wAmen"],
        wEnv=w_norm["wEnv"],
        wCom=w_norm["wCom"],
    )
    repo.save(profile)           # MemoryWeightsRepo inserts newest at index 0
    return repo.get_active()     # return the active one (just saved)


"""
Instructions for frontend:
use GET /weights
update using POST /weights
example:
{
  "ranks": { "aff": 5, "acc": 4, "amen": 3, "env": 2, "com": 1 },
  "profileName": "My Priorities"
}

{
  "weights": { "wAff": 0.4, "wAcc": 0.2, "wAmen": 0.2, "wEnv": 0.1, "wCom": 0.1 },
  "profileName": "Power User"
}

"""