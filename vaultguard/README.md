# VaultGuard — Internal Secrets Server

Centralized API/MCP server for all secrets. Backed by Firebase Firestore.

**⚠️ INTERNAL ONLY — Never expose publicly.**

## Architecture

```
Agent → VaultGuard API (port 8003) → Firebase Firestore
Agent → VaultGuard MCP (port 8004) → Firebase Firestore
```

## Quick Start

```bash
# 1. Copy Firebase service account
cp /path/to/service_account.json ./service_account.json

# 2. Set the master API key
export VAULTGUARD_API_KEY="your-internal-key"

# 3. Run
docker compose up -d
```

## REST API

```bash
# List all secrets
curl -H "X-API-Key: $VAULTGUARD_API_KEY" http://localhost:8003/secrets

# Get a secret
curl -H "X-API-Key: $VAULTGUARD_API_KEY" http://localhost:8003/secrets/STRIPE_SECRET_KEY

# Set a secret
curl -X PUT -H "X-API-Key: $VAULTGUARD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"value": "sk_live_..."}' \
  http://localhost:8003/secrets/STRIPE_SECRET_KEY
```

## MCP (for AI agents)

Add to your MCP config:

```json
{
  "mcpServers": {
    "vaultguard": {
      "url": "http://localhost:8004/sse"
    }
  }
}
```

Tools available:

- `get_secret(key)` — returns the secret value
- `list_secrets()` — returns all keys with previews
- `set_secret(key, value, description)` — creates/updates
- `delete_secret(key)` — removes a secret
