#!/usr/bin/env python3
"""
VaultGuard MCP Server — AI agent access to secrets via Model Context Protocol.

Tools:
  list_secrets() — List all secret key names and categories
  get_secret(key) — Retrieve a specific secret value
  set_secret(key, value) — Store/update a secret
"""
import os
import firebase_admin
from firebase_admin import credentials, firestore
from fastmcp import FastMCP
from datetime import datetime

# Firebase init (share app if already initialized by vault_server)
try:
    firebase_admin.get_app()
except ValueError:
    cred_path = os.environ.get("FIREBASE_CREDENTIALS", "service_account.json")
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    else:
        firebase_admin.initialize_app()

db = firestore.client()
COLLECTION = "secrets"

mcp = FastMCP("VaultGuard", port=int(os.environ.get("VAULTGUARD_MCP_PORT", 8004)))


@mcp.tool()
def list_secrets() -> str:
    """List all API key names and categories (masked values)."""
    docs = db.collection(COLLECTION).stream()
    lines = []
    for doc in docs:
        d = doc.to_dict()
        cat = d.get("category", "unknown")
        preview = d.get("value", "")[:4] + "..." if d.get("value") else "empty"
        lines.append(f"{doc.id} [{cat}] {preview}")
    return "\n".join(lines) if lines else "No secrets found"


@mcp.tool()
def get_secret(key: str) -> str:
    """Get an API key value by name. Supports exact match."""
    doc = db.collection(COLLECTION).document(key).get()
    if doc.exists:
        return doc.to_dict().get("value", "")

    # Fuzzy: check if key is a substring of any secret name
    docs = db.collection(COLLECTION).stream()
    for d in docs:
        if key.lower() in d.id.lower():
            return d.to_dict().get("value", "")
    return f"Secret '{key}' not found"


@mcp.tool()
def set_secret(key: str, value: str, category: str = "") -> str:
    """Set or update an API key in the vault."""
    if not category:
        kl = key.lower()
        if any(x in kl for x in ["tradier", "tasty", "schwab"]):
            category = "brokerage"
        elif any(x in kl for x in ["gemini", "openai", "anthropic"]):
            category = "ai"
        elif any(x in kl for x in ["stripe"]):
            category = "billing"
        else:
            category = "other"

    db.collection(COLLECTION).document(key).set({
        "value": value,
        "category": category,
        "updated_at": datetime.utcnow().isoformat(),
        "source": os.environ.get("HOSTNAME", "unknown"),
    })
    return f"✓ Secret '{key}' saved [{category}]"


if __name__ == "__main__":
    mcp.run(transport="sse")
