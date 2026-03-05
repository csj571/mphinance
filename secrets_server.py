"""
secrets_server.py — Centralized API Key Store + MCP Server

The "API for APIs" — one place to get/set/list all secrets.
Serves both as FastAPI REST and as an MCP server for AI agent access.

Usage:
  python3 secrets_server.py               # Start server on port 8200
  python3 secrets_server.py --list        # List all key names
  python3 secrets_server.py --get GEMINI  # Get a specific key

Config: reads from secrets.env (key=value format)
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

SECRETS_FILE = Path(__file__).parent / "secrets.env"
CATALOG_FILE = Path(__file__).parent / "secrets_catalog.json"


def _load_secrets() -> dict:
    """Load all secrets from secrets.env into a dict."""
    secrets = {}
    if not SECRETS_FILE.exists():
        return secrets
    for line in SECRETS_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip()
            if value:  # Skip empty values
                secrets[key] = value
    return secrets


def _save_secrets(secrets: dict):
    """Write secrets dict back to secrets.env, preserving comments."""
    lines = []
    existing_lines = SECRETS_FILE.read_text().splitlines() if SECRETS_FILE.exists() else []

    written_keys = set()
    for line in existing_lines:
        stripped = line.strip()
        if stripped.startswith("#") or not stripped:
            lines.append(line)
        elif "=" in stripped:
            key = stripped.split("=", 1)[0].strip()
            if key in secrets:
                lines.append(f"{key}={secrets[key]}")
                written_keys.add(key)
            else:
                lines.append(line)

    # Append any new keys not in the original file
    for key, value in secrets.items():
        if key not in written_keys:
            lines.append(f"{key}={value}")

    SECRETS_FILE.write_text("\n".join(lines) + "\n")


def _build_catalog(secrets: dict) -> dict:
    """Build a catalog with metadata about each secret (no values exposed)."""
    catalog = {}
    for key in secrets:
        # Infer category from key name
        if "WEBHOOK" in key:
            category = "discord"
        elif "GEMINI" in key:
            category = "ai"
        elif "FIREBASE" in key:
            category = "firebase"
        elif "GOOGLE" in key:
            category = "google"
        elif "TICKERTRACE" in key:
            category = "tickertrace"
        elif "TWITTER" in key or "SOCIAL" in key:
            category = "social"
        elif "SSH" in key:
            category = "infrastructure"
        else:
            category = "other"

        catalog[key] = {
            "category": category,
            "has_value": bool(secrets.get(key)),
            "key_preview": secrets[key][:8] + "..." if len(secrets.get(key, "")) > 8 else "***",
        }
    return catalog


def list_secrets() -> dict:
    """List all secret names and categories (no values)."""
    secrets = _load_secrets()
    return _build_catalog(secrets)


def get_secret(key: str) -> str | None:
    """Get a single secret value by name. Supports partial matching."""
    secrets = _load_secrets()
    # Exact match first
    if key in secrets:
        return secrets[key]
    # Partial match (case-insensitive)
    key_upper = key.upper()
    matches = {k: v for k, v in secrets.items() if key_upper in k.upper()}
    if len(matches) == 1:
        return list(matches.values())[0]
    elif len(matches) > 1:
        return json.dumps({"error": "multiple matches", "keys": list(matches.keys())})
    return None


def set_secret(key: str, value: str) -> bool:
    """Set or update a secret."""
    secrets = _load_secrets()
    secrets[key] = value
    _save_secrets(secrets)
    return True


# ═══ CLI ═══
def cli():
    if "--list" in sys.argv:
        catalog = list_secrets()
        print(f"\n  ═══ SECRETS VAULT ({len(catalog)} keys) ═══")
        by_cat = {}
        for k, v in catalog.items():
            by_cat.setdefault(v["category"], []).append((k, v))
        for cat, items in sorted(by_cat.items()):
            print(f"\n  [{cat.upper()}]")
            for k, v in items:
                print(f"    {k:40s} {v['key_preview']}")
        return

    if "--get" in sys.argv:
        idx = sys.argv.index("--get")
        if idx + 1 < len(sys.argv):
            key = sys.argv[idx + 1]
            val = get_secret(key)
            if val:
                print(val)
            else:
                print(f"Key '{key}' not found", file=sys.stderr)
                sys.exit(1)
        return

    if "--set" in sys.argv:
        idx = sys.argv.index("--set")
        if idx + 2 < len(sys.argv):
            key, value = sys.argv[idx + 1], sys.argv[idx + 2]
            set_secret(key, value)
            print(f"✓ Set {key}")
        return

    # Default: start FastAPI + MCP server
    start_server()


# ═══ FastAPI + MCP Server ═══
def start_server():
    try:
        from fastapi import FastAPI, HTTPException
        from fastapi.responses import JSONResponse
        import uvicorn
    except ImportError:
        print("Install fastapi+uvicorn: pip install fastapi uvicorn")
        sys.exit(1)

    app = FastAPI(
        title="mphinance Secrets Vault",
        description="Centralized API key store — the API for APIs",
        version="1.0.0",
    )

    @app.get("/")
    def root():
        return {"service": "mphinance-secrets", "keys_loaded": len(_load_secrets())}

    @app.get("/secrets")
    def api_list_secrets():
        """List all secret names and categories (values masked)."""
        return list_secrets()

    @app.get("/secrets/{key}")
    def api_get_secret(key: str):
        """Get a secret by name (supports partial matching)."""
        val = get_secret(key)
        if val is None:
            raise HTTPException(404, f"Key '{key}' not found")
        return {"key": key, "value": val}

    @app.post("/secrets/{key}")
    def api_set_secret(key: str, value: str):
        """Set or update a secret."""
        set_secret(key, value)
        return {"status": "ok", "key": key}

    @app.get("/health")
    def health():
        return {"status": "ok", "keys": len(_load_secrets()), "ts": datetime.now().isoformat()}

    # ── MCP SSE endpoint ──
    @app.get("/mcp/tools")
    def mcp_tools():
        """MCP-compatible tool listing for AI agent discovery."""
        return {
            "tools": [
                {
                    "name": "list_secrets",
                    "description": "List all API key names and categories in the vault",
                    "inputSchema": {"type": "object", "properties": {}},
                },
                {
                    "name": "get_secret",
                    "description": "Get an API key value by name. Supports partial matching.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {"key": {"type": "string", "description": "Key name or partial match"}},
                        "required": ["key"],
                    },
                },
                {
                    "name": "set_secret",
                    "description": "Set or update an API key in the vault.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "key": {"type": "string"},
                            "value": {"type": "string"},
                        },
                        "required": ["key", "value"],
                    },
                },
            ]
        }

    @app.post("/mcp/call")
    def mcp_call(tool: str, arguments: dict = {}):
        """MCP-compatible tool invocation."""
        if tool == "list_secrets":
            return list_secrets()
        elif tool == "get_secret":
            val = get_secret(arguments.get("key", ""))
            return {"value": val}
        elif tool == "set_secret":
            set_secret(arguments["key"], arguments["value"])
            return {"status": "ok"}
        raise HTTPException(400, f"Unknown tool: {tool}")

    print(f"  ═══ SECRETS VAULT SERVER ═══")
    print(f"  Keys loaded: {len(_load_secrets())}")
    print(f"  REST API:  http://localhost:8200/secrets")
    print(f"  MCP tools: http://localhost:8200/mcp/tools")
    print(f"  Health:    http://localhost:8200/health")
    uvicorn.run(app, host="0.0.0.0", port=8200, log_level="warning")


if __name__ == "__main__":
    cli()
