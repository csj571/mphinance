# 👻 GHOST_HANDOFF — March 7, 2026

> This is the current state doc. Next agent reads this first.

## Infrastructure State

### Vultr (Production)

- **API Gateway:** `api.mphinance.com` — 3 routes active:
  - `/alpha/` → Ghost Alpha API (port 8002) ✅
  - `/tt/` → TickerTrace API (port 8100) ✅
  - `/ebook/` → Ebook Checkout (port 8300) ✅
- **SSL:** `alpha.mphinance.com` cert obtained + reverse proxy
- **DNS NEEDED:** A records for `api.mphinance.com` and `alpha.mphinance.com` → 207.148.19.144
- **Ebook Reader:** `/ebook/read/69533e52220545f7` (obfuscated permanent URL)
- **TickerTrace:** Unchanged, `api.tickertrace.pro` still works independently

### Venus (Local Server)

- **VaultGuard:** Running localhost:8003/8004 (Docker Compose, Firebase Firestore backed)
- **Alpha-Momentum API:** Port 8100 via Docker
- **Gemini CLI:** Configured with GEMINI.md + MCP servers (tradier, yfinance, vaultguard)
- **GHOST_HANDOFF.md:** At `/home/mph/alpha-momentum/GHOST_HANDOFF.md`

### This Machine (sam1)

- **Repo:** `/home/sam/mphinance` — main branch, up to date
- **Pipeline:** 16 stages (added watchlist cleanup, revenue refresh, auto-backtest)
- **Blog:** Latest entry March 7, rsynced to Vultr

## What Changed This Session

1. API Gateway consolidation (single vhost, path routing)
2. SSL for alpha.mphinance.com
3. 16-stage pipeline (was 13)
4. OpenClaw archived from sam2 → `OPENCLAW_ARCHIVE.md` + `_archive/openclaw_workspace/`
5. VaultGuard deployed to venus
6. Venus Gemini CLI configured
7. Ebook checkout deployed on Vultr with obfuscated reader URL
8. `gcp/setup.sh` rewritten (was all comments)
9. Widgets stripped from blog + landing
10. Ghost Blog entry for session

## User's Next Focus

- **TraderDaddy.pro** — Michael's priority. Promote it, add to blog signatures, grab screenshots
- **0DTE Dashboard** — tightspread submodule, see `tightspread/TODO_backtesting.md`
- **sam2 is retired** — all relevant data archived here

## Unresolved

- DNS A records not yet pointed
- `STRIPE_SECRET_KEY` not set in ebook container (checkout will fail without it)
- Cloud Scheduler needs `gcloud` CLI (run `gcp/setup.sh`)
