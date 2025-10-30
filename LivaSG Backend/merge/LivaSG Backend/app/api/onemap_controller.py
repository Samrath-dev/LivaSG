# app/api/onemap_controller.py
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional
import os

from app.integrations.onemap_client import OneMapClientHardcoded

router = APIRouter(prefix="/onemap", tags=["onemap"])


async def get_planning_repo():
    raise HTTPException(status_code=500, detail="Planning repo not initialized")


async def get_onemap_client():
    """Dependency placeholder for the OneMap client. Main app overrides this."""
    raise HTTPException(status_code=500, detail="OneMap client not initialized")

@router.get("/planning-areas")
async def get_planning_areas(
    year: int = Query(2019, ge=1998, le=2100),
    repo = Depends(get_planning_repo),
):
    return await repo.geojson(year)

@router.get("/planning-area-names")
async def get_planning_area_names(
    year: int = Query(2019, ge=1998, le=2100),
    repo = Depends(get_planning_repo),
):
    return await repo.names(year)


@router.get("/planning-area-at")
async def get_planning_area_at(
    latitude: float = Query(...),
    longitude: float = Query(...),
    year: int = Query(2019, ge=1998, le=2100),
    repo = Depends(get_planning_repo),
):
   
    raise HTTPException(status_code=501, detail="Not implemented in repo yet")


@router.post("/renew-token")
async def renew_onemap_token(
    email: Optional[str] = None,
    password: Optional[str] = None,
    client: OneMapClientHardcoded = Depends(get_onemap_client),
):
    """Force OneMap token refresh. Optionally supply email/password in the request body
    to perform a credential-based refresh for this call.
    Saves the new token to app/integrations/.env file.
    Returns the new token expiry (epoch seconds) on success.
    """
    import pathlib
    
    # Temporarily stash existing env vars and set provided ones (if any)
    old_email = os.getenv("ONEMAP_EMAIL")
    old_password = os.getenv("ONEMAP_PASSWORD")
    try:
        if email:
            os.environ["ONEMAP_EMAIL"] = email
        if password:
            os.environ["ONEMAP_PASSWORD"] = password

        # Call the client's refresh logic
        try:
            await client._refresh_token()
        except RuntimeError as e:
            raise HTTPException(status_code=400, detail=str(e))

        new_token = getattr(client, "_token", None)
        new_exp = getattr(client, "_exp", None)
        
        if not new_token:
            raise HTTPException(status_code=500, detail="Token refresh succeeded but token is empty")
        
        # Save to .env file
        env_path = pathlib.Path(__file__).parent.parent / "integrations" / ".env"
        
        # Read existing .env content
        if env_path.exists():
            lines = env_path.read_text(encoding="utf-8").splitlines()
        else:
            lines = []
        
        # Remove any existing ONEMAP_TOKEN lines
        filtered_lines = [line for line in lines if not line.strip().startswith("ONEMAP_TOKEN=")]
        
        # Add the new token
        filtered_lines.append(f"ONEMAP_TOKEN={new_token}")
        
        # Ensure ONEMAP_EMAIL is in .env if provided
        if email and not any(line.strip().startswith("ONEMAP_EMAIL=") for line in filtered_lines):
            filtered_lines.append(f"ONEMAP_EMAIL={email}")
        
        # Write back to .env
        env_path.write_text("\n".join(filtered_lines) + "\n", encoding="utf-8")
        
        return {
            "ok": True, 
            "exp": new_exp,
            "token": new_token[:20] + "..." if len(new_token) > 20 else new_token,
            "saved_to": str(env_path)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))
    finally:
        # restore env
        if old_email is None:
            os.environ.pop("ONEMAP_EMAIL", None)
        else:
            os.environ["ONEMAP_EMAIL"] = old_email
        if old_password is None:
            os.environ.pop("ONEMAP_PASSWORD", None)
        else:
            os.environ["ONEMAP_PASSWORD"] = old_password