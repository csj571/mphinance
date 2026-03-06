"""
VaultGuard MCP Server — FastMCP tools for agent secret access

Agents connect via SSE and use these tools:
  - get_secret(key) → returns secret value
  - list_secrets() → returns all keys with previews
  - set_secret(key, value) → creates/updates a secret

Backed by Firebase Firestore, same collection as the REST API.
"""

import os
import logging

import firebase_admin
from firebase_admin import credentials, firestore
from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s [VaultGuard-MCP] %(message)s")
log = logging.getLogger("vaultguard-mcp")

# ── Firebase ─────────────────────────────────────────────
FIREBASE_CRED_PATH = os.getenv("FIREBASE_CREDENTIALS", "/app/service_account.json")
COLLECTION = "secrets"

def _get_db():
    try:
        cred = credentials.Certificate(FIREBASE_CRED_PATH)
        firebase_admin.initialize_app(cred)
    except ValueError:
        pass
    return firestore.client()

db = _get_db()

# ── MCP Server ───────────────────────────────────────────
mcp = FastMCP(
    "VaultGuard",
    description="Centralized secrets management. Get any API key with one tool call.",
)


@mcp.tool()
def get_secret(key: str) -> str:
    """Get a secret value by key name (e.g. STRIPE_SECRET_KEY, TRADIER_API_KEY).
    Returns the raw secret value string."""
    doc = db.collection(COLLECTION).document(key).get()
    if not doc.exists:
        return f"ERROR: Secret '{key}' not found. Use list_secrets() to see available keys."
    value = doc.to_dict().get("value", "")
    log.info(f"MCP get_secret: {key}")
    return value


@mcp.tool()
def list_secrets() -> str:
    """List all available secret key names with previews.
    Returns a formatted list of key names and partial values."""
    docs = db.collection(COLLECTION).stream()
    lines = []
    for doc in docs:
        data = doc.to_dict()
        value = data.get("value", "")
        preview = value[:15] + "..." if len(value) > 15 else value
        lines.append(f"  {doc.id:40s} = {preview}")
    log.info(f"MCP list_secrets: {len(lines)} keys")
    return f"Available secrets ({len(lines)}):\n" + "\n".join(sorted(lines))


@mcp.tool()
def set_secret(key: str, value: str, description: str = "") -> str:
    """Create or update a secret in VaultGuard.
    Args:
        key: Secret name (e.g. MY_API_KEY)
        value: The secret value
        description: Optional description of what this secret is for
    """
    from datetime import datetime
    doc_data = {"value": value, "updated_at": datetime.now().isoformat()}
    if description:
        doc_data["description"] = description
    db.collection(COLLECTION).document(key).set(doc_data, merge=True)
    log.info(f"MCP set_secret: {key}")
    return f"Secret '{key}' saved successfully."


@mcp.tool()
def delete_secret(key: str) -> str:
    """Delete a secret from VaultGuard."""
    doc = db.collection(COLLECTION).document(key).get()
    if not doc.exists:
        return f"ERROR: Secret '{key}' not found."
    db.collection(COLLECTION).document(key).delete()
    log.info(f"MCP delete_secret: {key}")
    return f"Secret '{key}' deleted."


# ── Run ──────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("VAULTGUARD_MCP_PORT", "8004"))
    log.info(f"Starting VaultGuard MCP on port {port}")
    mcp.run(transport="sse", host="0.0.0.0", port=port)
