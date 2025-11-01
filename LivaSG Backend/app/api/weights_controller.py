# app/api/weights_controller.py
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, confloat
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
    # Accept normalized weights in [0,1]; they don't have to sum to 1—we'll normalize.
    wAff: confloat(ge=0.0, le=1.0)
    wAcc: confloat(ge=0.0, le=1.0)
    wAmen: confloat(ge=0.0, le=1.0)
    wEnv: confloat(ge=0.0, le=1.0)
    wCom: confloat(ge=0.0, le=1.0)

class WeightsUpsert(BaseModel):
    """
    Weights-only endpoint.
    NOTE: 'ranks' are NOT accepted here; use /ranks instead.
    """
    weights: WeightValues
    profileName: Optional[str] = Field(None, description="Optional label to show in UI")
    # trap accidental ranks usage so we can error cleanly instead of silently converting
    ranks: Optional[dict] = Field(None, description="Do not send. Use /ranks endpoint.")

    class Config:
        extra = "forbid"  # reject any unexpected fields

# -------- Helpers --------

def _normalize(d: Dict[str, float]) -> Dict[str, float]:
    s = sum(max(0.0, v) for v in d.values())
    if s <= 0:
        n = len(d)
        return {k: 1.0 / n for k in d}
    return {k: max(0.0, v) / s for k, v in d.items()}

# -------- Routes --------

@router.get("", response_model=WeightsProfile)
def get_active(repo: IWeightsRepo = Depends(get_weights_repo)) -> WeightsProfile:
    """Return the currently active weights profile."""
    return repo.get_active()

@router.post("", response_model=WeightsProfile)
def upsert_weights(body: WeightsUpsert, repo: IWeightsRepo = Depends(get_weights_repo)) -> WeightsProfile:
    """
    Create a new weights profile and make it active.
    Only explicit `weights` are accepted here.
    If you want to set user ranks, call the /ranks endpoint instead.
    """
    if body.ranks is not None:
        raise HTTPException(
            status_code=400,
            detail="`ranks` are not accepted on /weights. Use the /ranks endpoint."
        )

    w_raw = {
        "wAff": float(body.weights.wAff),
        "wAcc": float(body.weights.wAcc),
        "wAmen": float(body.weights.wAmen),
        "wEnv": float(body.weights.wEnv),
        "wCom": float(body.weights.wCom),
    }
    w_norm = _normalize(w_raw)

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