import requests
import json
from pathlib import Path

# Fetch token from OneMap
auth_url = "https://www.onemap.gov.sg//api/auth/post/getToken"
credentials = {
    "email": "",
    "password": ""
}

print("Requesting new token from OneMap...")
try:
    response = requests.post(auth_url, json=credentials, timeout=10)
    response.raise_for_status()
    data = response.json()
    token = data.get("access_token") or data.get("token")
    
    if not token:
        print(f"ERROR: No token in response: {data}")
        exit(1)
    
    print(f"✓ Got new token: {token[:50]}...")
    
    # Decode expiry
    import base64
    payload = token.split(".")[1]
    payload += "=" * (-len(payload) % 4)
    decoded = json.loads(base64.urlsafe_b64decode(payload))
    exp = decoded.get("exp")
    
    from datetime import datetime
    exp_dt = datetime.fromtimestamp(exp)
    print(f"✓ Expires: {exp_dt}")
    
    # Update .env file
    base = Path(__file__).parent
    # prefer the project's `LivaSG Backend` directory if it exists (script may be run from repo root)
    candidate_dir = base / "LivaSG Backend"
    if candidate_dir.exists() and candidate_dir.is_dir():
        env_dir = candidate_dir
    else:
        env_dir = base

    env_path = env_dir / ".env"

    # Read existing .env if possible
    try:
        if env_path.exists() and env_path.is_file():
            lines = env_path.read_text(encoding="utf-8").splitlines()
        else:
            lines = []
    except Exception as e:
        print(f"Warning: could not read existing .env at {env_path}: {e}")
        lines = []

    # Remove old token line and append new token
    filtered = [line for line in lines if not line.strip().startswith("ONEMAP_TOKEN=")]
    filtered.append(f"ONEMAP_TOKEN={token}")

    # Try writing the file; on failure, print helpful diagnostics and print the token so user can copy it
    try:
        env_path.write_text("\n".join(filtered) + "\n", encoding="utf-8")
        print(f"✓ Updated {env_path}")
        print("\nNow restart your backend server to use the new token.")
    except Exception as e:
        print(f"ERROR: Could not write to {env_path}: {e}")
        print("Diagnostic:")
        try:
            print(f"  parent exists: {env_path.parent.exists()}")
            print(f"  parent is dir: {env_path.parent.is_dir()}")
            if env_path.exists():
                print(f"  target exists and is_file: {env_path.is_file()}")
            else:
                print("  target does not exist yet")
        except Exception:
            pass
        print("\nYou can manually add the following line to your .env file:")
        print(f"ONEMAP_TOKEN={token}")
    
except requests.exceptions.RequestException as e:
    print(f"ERROR: Cannot reach OneMap API: {e}")
    print("\nYour network cannot access developers.onemap.sg.")
    print("Try running this script on a different network or machine.")
    exit(1)
