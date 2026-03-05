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

## Firebase Console Links

- [Project](https://console.firebase.google.com/u/0/project/studio-3669937961-ea8a7)
- [Firestore Data](https://console.firebase.google.com/u/0/project/studio-3669937961-ea8a7/firestore)
- [Service Accounts](https://console.firebase.google.com/u/0/project/studio-3669937961-ea8a7/settings/serviceaccounts/adminsdk)
