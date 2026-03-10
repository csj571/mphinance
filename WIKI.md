# 🔐 Personal Wiki

> **⚠️ DO NOT commit actual passwords, tokens, or secrets to this file.**
> Credentials live in VaultGuard (Firebase Firestore) or in `.env` files on the respective servers.
> This wiki is for documenting *where things are* and *how to access them*, not for storing the credentials themselves.

---

## 🖥️ Servers

| Name | Host | Port | User | Purpose |
|------|------|------|------|---------|
| Vultr VPS | mphinance.com | 15422 | root | Production — Docker, Apache, Ghost Alpha API |
| Venus | 192.168.2.172 | 22 | mph | Home server — alpha-momentum, heavy compute |
| sam2 | 192.168.2.94 | 22 | sam | Local dev |

## 🌐 Domains & Services

| Domain | Service | Where It Runs |
|--------|---------|---------------|
| mphinance.com | Landing page + Ghost Blog | Vultr (Apache) |
| tt.mphinance.com | Momentum Phund (TastyTrade portfolio) | Vultr (NiceGUI, port 8080) |
| mphinance.com:8002 | Ghost Alpha API (FastAPI) | Vultr (Docker) |
| api.tickertrace.pro | TickerTrace API | Vultr (Docker, port 8100) |
| tickertrace.pro | TickerTrace Frontend | Vercel |
| traderdaddy.pro | TraderDaddy Pro | Vercel / Whop |
| mphinance.github.io/mphinance | Alpha Dossier + VoPR | GitHub Pages |
| mphinance.github.io/AMU | Alpha Market University | GitHub Pages |

## 🔑 Credential Locations

| Service | Where Creds Live | Notes |
|---------|------------------|-------|
| TastyTrade | `/home/mphinance/tt/.env` on Vultr | CLIENT_ID, SECRET, REFRESH_TOKEN |
| Substack | `/home/mphinance/tt/.env` on Vultr | SUBSTACK_SID, SUBSTACK_PUB_URL |
| SMTP / Email | `/home/mphinance/tt/.env` on Vultr | For notifications |
| Gemini API | GitHub Secrets (mphinance repo) | Used by pipeline + ghost blog |
| TickerTrace API | `/home/mphinance/TickerTrace/.env` | Docker reads this |
| VaultGuard/Firebase | `secrets_server.py` on sam2 | Firebase Firestore sync |
| Let's Encrypt SSL | `/etc/letsencrypt/live/` on Vultr | Auto-renews, Apache config |

## 📊 API Endpoints Quick Reference

### Ghost Alpha API (mphinance.com:8002)

```
GET /health                    — Service health + ticker count
GET /alpha/api/news            — Aggregated market news (RSS, 15m cache)
GET /alpha/api/csp             — Full VoPR-graded CSP setups
GET /alpha/api/picks/today     — Daily momentum picks (Gold/Silver/Bronze)
GET /alpha/api/setups/today    — Daily 3-style setups (DT/Swing/CSP)
GET /alpha/api/regime          — Market regime (VIX, hedge suggestions)
GET /alpha/api/tickers         — All available tickers
GET /alpha/api/{TICKER}        — Full deep dive data
POST /alpha/api/sync           — Trigger git pull
```

Swagger: <http://mphinance.com:8002/docs>

### TickerTrace API (api.tickertrace.pro)

```
GET /health
GET /api/fund/{ticker}/holdings
GET /api/fund/{ticker}/daily-changes
```

Swagger: <https://api.tickertrace.pro/docs>

## 🔧 Common Tasks

### Deploy Ghost Alpha API update

```bash
ssh vultr "cd /home/mphinance/ghost-alpha && docker compose build --no-cache && docker compose up -d"
```

### Deploy landing page

```bash
rsync -avz mphinance/landing/ vultr:/home/mphinance/public_html/
```

### Check what's running on Vultr

```bash
ssh vultr "docker ps --format '{{.Names}} {{.Status}} {{.Ports}}' && ss -tlnp | grep -E ':80|:443|:8002|:8100'"
```

### Run pipeline manually

```bash
cd mphinance && python -m dossier.generate --no-pdf
```

## 📝 Notes

- *Add your notes here*

---

> Last updated: 2026-03-05 by Ghost Alpha session
