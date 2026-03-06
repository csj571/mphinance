# VaultGuard — Centralized Secrets & API Key Store

**Firebase Project:** `studio-3669937961-ea8a7` (VaultGuard)  
**Firestore Collection:** `secrets`  
**Total Keys:** 27

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

## Quick Reference

```bash
py secrets_server.py --list          # List all (masked)
py secrets_server.py --get GEMINI    # Get by partial match
py secrets_server.py --set KEY val   # Add/update key
py secrets_server.py --sync-up       # Push to Firestore
py secrets_server.py --sync-down     # Pull from Firestore
py secrets_server.py                 # Start REST+MCP server (port 8200)
```

## Full Key Inventory (27 keys)

| Category | Key | Source |
|----------|-----|--------|
| **AI** | `GEMINI_API_KEY` | mphinance/.env |
| **AI** | `GEMINI_API_KEY_ALT` | alpha-momentum/.env |
| **Brokerage** | `TRADIER_API_KEY` | ~/.env.tradier |
| **Brokerage** | `TRADIER_ENDPOINT` | ~/.env.tradier |
| **Brokerage** | `TASTYTRADE_CLIENT_ID` | alpha-momentum/.env |
| **Brokerage** | `TASTYTRADE_CLIENT_SECRET` | alpha-momentum/.env |
| **Brokerage** | `TASTYTRADE_REFRESH_TOKEN` | alpha-momentum/.env |
| **Payments** | `STRIPE_SECRET_KEY` | cred.txt (sk_live) |
| **Discord** | `WEBHOOK_WEATHER_CHANNEL` | mphinance/.env |
| **Discord** | `WEBHOOK_ALISON` | mphinance/.env |
| **Discord** | `WEBHOOK_PATHFINDERS` | mphinance/.env |
| **Discord** | `WEBHOOK_THE_KINGDOM` | mphinance/.env |
| **Google** | `GOOGLE_SHEETS_WEBHOOK` | mphinance/.env |
| **Google** | `GOOGLE_SHEETS_WEBHOOK_ALT` | alpha-momentum/.env |
| **Google** | `DRIVE_FOLDER_ID` | alpha-momentum/.env |
| **Google** | `DRIVE_FOLDER_NAME` | alpha-momentum/.env |
| **Google** | `NOTEBOOKLM_NOTEBOOK_ID` | alpha-momentum/.env |
| **Email** | `SMTP_HOST` | alpha-momentum/.env |
| **Email** | `SMTP_PORT` | alpha-momentum/.env |
| **Email** | `SMTP_USER` | <contact@mphinance.com> |
| **Email** | `SMTP_PASSWORD` | alpha-momentum/.env |
| **Email** | `SMTP_FROM` | alpha-momentum/.env |
| **Publishing** | `SUBSTACK_SID` | alpha-momentum/.env |
| **Publishing** | `SUBSTACK_PUB_URL` | alpha-momentum/.env |
| **Data** | `OPENBB_CREDENTIALS_TRADIER_API_KEY` | alpha-momentum/.env |
| **Firebase** | `FIREBASE_PROJECT_ID` | manual |
| **TickerTrace** | `TICKERTRACE_API_BASE` | mphinance/.env |

**Still needed:** `TWITTER_BEARER_TOKEN`, `OPENBB_API_KEY`, `STRIPE_PUBLISHABLE_KEY`

## API Endpoints (port 8200)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/secrets` | GET | List all keys (masked) |
| `/secrets/{key}` | GET | Get value (partial match) |
| `/secrets/{key}?value=xxx` | POST | Set/update |
| `/health` | GET | Health check |
| `/mcp/tools` | GET | MCP tool discovery |
| `/mcp/call` | POST | MCP tool invocation |

## Files

| File | Gitignored | Purpose |
|------|-----------|---------|
| `secrets.env` | ✅ | Local key-value store (27 keys) |
| `service_account.json` | ✅ | Firebase credentials |
| `secrets_server.py` | No | Server code (no secrets) |
| `VAULT.md` | No | This documentation |

## Setup on Another Machine

```bash
scp sam2:~/Antigravity/empty/mphinance/service_account.json ./
scp sam2:~/Antigravity/empty/mphinance/secrets_server.py ./
python3 secrets_server.py --sync-down   # Done — all 27 keys populated
```

## 🌐 Web Interfaces

You have **two** web interfaces for managing secrets:

### 1. Firebase Console (Cloud — Works Anywhere)

This is your primary web UI. Log into Google and go here:

🔗 **[Firestore Data Browser](https://console.firebase.google.com/u/0/project/studio-3669937961-ea8a7/firestore/databases/-default-/data/~2Fsecrets)**

**To view all keys:**

1. Open the link above
2. Click the `secrets` collection on the left
3. Each document = one key. Click any to see its value

**To edit a key:**

1. Click the key name in the left panel
2. Click the `value` field on the right
3. Edit inline, press Enter or click away to save
4. Run `python3 secrets_server.py --sync-down` locally to pull the update

**To add a new key:**

1. Click `+ Add document` at the top
2. Document ID = your key name (e.g., `TWITTER_BEARER_TOKEN`)
3. Add a field called `value` (type: string) = the actual secret
4. Add a field called `category` (type: string) = e.g., `Social`, `AI`, `Brokerage`
5. Run `python3 secrets_server.py --sync-down` to pull it locally

**To delete a key:**

1. Click the key name, click the 3 dots menu → Delete document
2. Run `python3 secrets_server.py --sync-down` to update local

### 2. Local Swagger UI (REST API — Run on sam2)

Start the server and get a full interactive API:

```bash
python3 secrets_server.py    # Starts on port 8200
```

Then open: **<http://localhost:8200/docs>**

From Swagger you can:

- `GET /secrets` — list all keys (values masked)
- `GET /secrets/GEMINI` — get a key (partial match works)
- `POST /secrets/NEW_KEY?value=xxx` — add or update
- `GET /health` — check status

### Which to Use When?

| Situation | Use |
|-----------|-----|
| Quick key lookup from your phone/browser | Firebase Console |
| Rotating an API key | Firebase Console → edit → sync-down |
| Adding a bunch of new keys | CLI (`--set`) or Firebase Console |
| AI agent needs a key | Start server → MCP endpoint at `:8200/mcp/tools` |
| Setting up a new machine | `--sync-down` pulls everything from Firebase |

### Sync Cheat Sheet

```bash
# You changed a key in Firebase Console → pull it locally:
python3 secrets_server.py --sync-down

# You added a key locally → push to cloud:
python3 secrets_server.py --sync-up

# You changed keys on BOTH sides (merge):
python3 secrets_server.py --sync-down   # cloud wins
# Then manually add any local-only keys and --sync-up
```

## Firebase Console Links

- [Project](https://console.firebase.google.com/u/0/project/studio-3669937961-ea8a7)
- [Firestore Data](https://console.firebase.google.com/u/0/project/studio-3669937961-ea8a7/firestore)
- [Service Accounts](https://console.firebase.google.com/u/0/project/studio-3669937961-ea8a7/settings/serviceaccounts/adminsdk)
