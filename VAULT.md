# VaultGuard — Centralized Secrets & API Key Store

**Firebase Project:** `studio-3669937961-ea8a7` (VaultGuard)  
**Firestore Collection:** `secrets`

## What Is This?

VaultGuard is your "API for APIs" — a centralized place to store, retrieve, and sync API keys and secrets across all your machines and projects. No more hunting through scattered `.env` files on sam2, venus, and vultr.

## Architecture

```
┌──────────────┐     sync-up      ┌───────────────────┐
│  secrets.env │ ───────────────→ │  Firestore Cloud  │
│  (sam2 local)│ ←─────────────── │  (VaultGuard)     │
└──────────────┘     sync-down    └───────────────────┘
       ↑                                   ↑
       │ CLI/REST/MCP                      │ sync-down
       │                                   │
  secrets_server.py              venus / vultr / any machine
  port 8200                      with service_account.json
```

## Quick Start

```bash
# List all keys (masked values)
py secrets_server.py --list

# Get a specific key (partial match works)
py secrets_server.py --get GEMINI
py secrets_server.py --get PATHFINDERS

# Set a new key
py secrets_server.py --set TWITTER_BEARER_TOKEN abc123

# Push local → Firestore cloud
py secrets_server.py --sync-up

# Pull Firestore cloud → local
py secrets_server.py --sync-down

# Start REST + MCP server (port 8200)
py secrets_server.py
```

## REST API (when server is running)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/secrets` | GET | List all keys (masked) |
| `/secrets/{key}` | GET | Get value by name |
| `/secrets/{key}?value=xxx` | POST | Set/update a key |
| `/health` | GET | Health check + key count |

## MCP Endpoints (for AI agents)

| Endpoint | Description |
|----------|-------------|
| `/mcp/tools` | Tool discovery (list_secrets, get_secret, set_secret) |
| `/mcp/call` | Tool invocation |

## Current Keys (8)

| Category | Key | Source |
|----------|-----|--------|
| AI | `GEMINI_API_KEY` | mphinance/.env |
| Discord | `WEBHOOK_WEATHER_CHANNEL` | mphinance/.env |
| Discord | `WEBHOOK_ALISON` | mphinance/.env |
| Discord | `WEBHOOK_PATHFINDERS` | mphinance/.env |
| Discord | `WEBHOOK_THE_KINGDOM` | mphinance/.env |
| Google | `GOOGLE_SHEETS_WEBHOOK` | mphinance/.env |
| Firebase | `FIREBASE_PROJECT_ID` | manual |
| TickerTrace | `TICKERTRACE_API_BASE` | mphinance/.env |

Empty slots ready: `TRADIER_API_KEY`, `TASTYTRADE_TOKEN`, `TWITTER_BEARER_TOKEN`, `OPENBB_API_KEY`

## Files

| File | Gitignored | Purpose |
|------|-----------|---------|
| `secrets.env` | ✅ YES | Local key-value store |
| `service_account.json` | ✅ YES | Firebase service account credentials |
| `secrets_server.py` | No | Server code (no secrets in source) |
| `firebase.json` | No | Firebase project config |
| `firestore.rules` | No | Firestore security rules |

## Setting Up on Another Machine

```bash
# 1. Copy the service account JSON
scp sam2:~/Antigravity/empty/mphinance/service_account.json ./

# 2. Pull all secrets from cloud
python3 secrets_server.py --sync-down

# 3. Done — secrets.env is populated
```

## Firebase Console

- **Project:** [VaultGuard Console](https://console.firebase.google.com/u/0/project/studio-3669937961-ea8a7)
- **Firestore:** [View Data](https://console.firebase.google.com/u/0/project/studio-3669937961-ea8a7/firestore)
- **Service Accounts:** [Manage](https://console.firebase.google.com/u/0/project/studio-3669937961-ea8a7/settings/serviceaccounts/adminsdk)
