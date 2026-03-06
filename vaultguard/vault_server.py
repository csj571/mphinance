"""
VaultGuard — Centralized Secrets Server
FastAPI REST + FastMCP tools backed by Firebase Firestore

Internal only — never expose publicly.
All agents use a single VAULTGUARD_API_KEY to access any secret.
"""

import os
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

import firebase_admin
from firebase_admin import credentials, firestore

# ── Logging ──────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [VaultGuard] %(message)s")
log = logging.getLogger("vaultguard")

# ── Firebase ─────────────────────────────────────────────
FIREBASE_CRED_PATH = os.getenv("FIREBASE_CREDENTIALS", "/app/service_account.json")
COLLECTION = "secrets"

db = None

def _init_firebase():
    global db
    if db:
        return db
    try:
        cred = credentials.Certificate(FIREBASE_CRED_PATH)
        firebase_admin.initialize_app(cred)
    except ValueError:
        pass  # Already initialized
    db = firestore.client()
    log.info("Firebase Firestore connected")
    return db


# ── Auth ─────────────────────────────────────────────────
API_KEY = os.getenv("VAULTGUARD_API_KEY", "")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(key: Optional[str] = Security(api_key_header)):
    if not API_KEY:
        raise HTTPException(500, "VAULTGUARD_API_KEY not configured")
    if key != API_KEY:
        raise HTTPException(401, "Invalid API key")
    return key


# ── Models ───────────────────────────────────────────────
class SecretValue(BaseModel):
    value: str
    description: Optional[str] = None

class SecretResponse(BaseModel):
    key: str
    value: str
    updated_at: Optional[str] = None

class SecretListItem(BaseModel):
    key: str
    preview: str  # first 20 chars + ...
    updated_at: Optional[str] = None


# ── FastAPI App ──────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    _init_firebase()
    log.info(f"VaultGuard ready — {COLLECTION} collection")
    yield
    log.info("VaultGuard shutting down")

app = FastAPI(
    title="VaultGuard",
    description="Internal secrets management API. Never expose publicly.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "vaultguard", "timestamp": datetime.now().isoformat()}


@app.get("/secrets", response_model=list[SecretListItem])
async def list_secrets(_: str = Depends(verify_api_key)):
    """List all secret keys with previews (no full values)."""
    docs = db.collection(COLLECTION).stream()
    items = []
    for doc in docs:
        data = doc.to_dict()
        value = data.get("value", "")
        preview = value[:20] + "..." if len(value) > 20 else value
        items.append(SecretListItem(
            key=doc.id,
            preview=preview,
            updated_at=data.get("updated_at"),
        ))
    log.info(f"Listed {len(items)} secrets")
    return items


@app.get("/secrets/{key}", response_model=SecretResponse)
async def get_secret(key: str, _: str = Depends(verify_api_key)):
    """Get a specific secret by key."""
    doc = db.collection(COLLECTION).document(key).get()
    if not doc.exists:
        raise HTTPException(404, f"Secret '{key}' not found")
    data = doc.to_dict()
    log.info(f"Retrieved secret: {key}")
    return SecretResponse(
        key=key,
        value=data.get("value", ""),
        updated_at=data.get("updated_at"),
    )


@app.put("/secrets/{key}", response_model=SecretResponse)
async def set_secret(key: str, body: SecretValue, _: str = Depends(verify_api_key)):
    """Create or update a secret."""
    now = datetime.now().isoformat()
    doc_data = {
        "value": body.value,
        "updated_at": now,
    }
    if body.description:
        doc_data["description"] = body.description
    db.collection(COLLECTION).document(key).set(doc_data, merge=True)
    log.info(f"Set secret: {key}")
    return SecretResponse(key=key, value=body.value, updated_at=now)


@app.delete("/secrets/{key}")
async def delete_secret(key: str, _: str = Depends(verify_api_key)):
    """Delete a secret."""
    doc = db.collection(COLLECTION).document(key).get()
    if not doc.exists:
        raise HTTPException(404, f"Secret '{key}' not found")
    db.collection(COLLECTION).document(key).delete()
    log.info(f"Deleted secret: {key}")
    return {"status": "deleted", "key": key}


# ── Run ──────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("VAULTGUARD_PORT", "8003"))
    uvicorn.run(app, host="0.0.0.0", port=port)
