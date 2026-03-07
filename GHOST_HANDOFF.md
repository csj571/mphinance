# 👻 GHOST_HANDOFF — March 7, 2026 (Evening)

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

### This Machine (sam2)

- **Repo:** `/home/sam/mphinance` — main branch, up to date
- **Pipeline:** 16 stages (added watchlist cleanup, revenue refresh, auto-backtest)
- **Blog:** Latest entry March 7, rsynced to Vultr

## What Changed This Session

1. **AGENTS.md** — unified agent instructions (merged CLAUDE.md + GEMINI.md + VaultGuard-first + Supernote)
2. **CLAUDE.md** — slim redirect to AGENTS.md
3. **GEMINI.md** — repurposed as Gemini Android app task file ("Unless you ARE Gemini on Michael's phone")
4. **Substack Draft System** — GitHub-based drafts in `docs/substack/`:
   - `latest.md` = static bookmark link for reviewing drafts
   - `musings/` = "Michael's Musings" personal diary drafts
   - `dossier/` = auto-generated dossier drafts
   - `archive/` = published posts moved here
   - `scripts/substack_draft_manager.py` = RSS dedup checker + archive lifecycle
   - Playwright posting commented out in `scripts/substack_cron.sh`
5. **First Musing** — "Sobriety Doesn't Fix Your Character — And Neither Does Money" (from Art's AA insight)
6. **Money Plan** — `docs/MONEY_PLAN.md` with tier-based compounding/withdrawal/charity allocation
7. **Supernote Integration** — downloaded + transcribed 2 notebook PDFs via Google Drive API

## Key Files Created/Modified

| File | Action |
|------|--------|
| `AGENTS.md` | NEW — unified agent instructions |
| `CLAUDE.md` | MODIFIED — redirect to AGENTS.md |
| `GEMINI.md` | REWRITTEN — Gemini Android task file |
| `docs/substack/README.md` | NEW — draft system docs |
| `docs/substack/latest.md` | NEW — current draft |
| `docs/substack/musings/2026-03-07_*.md` | NEW — first musing |
| `docs/MONEY_PLAN.md` | NEW — money allocation plan |
| `scripts/substack_draft_manager.py` | NEW — RSS dedup + archive manager |
| `scripts/substack_cron.sh` | MODIFIED — Playwright → GitHub drafts |

## User's Next Focus

- **TraderDaddy.pro / tightspread** — 0DTE trading, expecting $100 → $2K this week
- **PineScripts** — `mphinance/tv-code-library` repo ready for tightspread submodule
- **Supernote** — may switch from Google Drive to Venus SFTP
- **VaultGuard OAuth** — refresh tokens expired, need Michael to re-auth

## Unresolved

- DNS A records not yet pointed
- `STRIPE_SECRET_KEY` not set in ebook container
- Google Drive OAuth refresh tokens expired in VaultGuard
- Substack dossier auto-generation needs wiring (currently only musings supported)
- All musings/money plan content → ebook pipeline (noted but not built yet)
