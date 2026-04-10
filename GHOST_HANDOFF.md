# 👻 GHOST_HANDOFF.md — ROIC Fortress Screener + CI Fix

## ⚠️ CURRENT STATE

**Dossier pipeline is working.** Ghost Alpha V2 screener integrated. ROIC Fortress Screener added.

**Algo bot is still LIVE on newvultr.** See below.

**GitHub Actions race conditions are FIXED.** Concurrency groups + rebase before push.

---

## What Happened This Session (2026-04-10)

### 🧹 Pipeline Exorcism
- **`.github/workflows/*`** — Successfully tracked down the phantom `.syncthing` files causing `git push` failures in the Ghost Daily pipeline.
- Cleared up the workflow race conditions, added concurrency groups, and successfully tested the `daily_dossier.yml` workflow run.
- The pipeline is green again.

### 🏰 ROIC Fortress Screener (PREVIOUS)
- **`dossier/roic_fortress_screener.py`** — Full-market quality screener for macro uncertainty
- TradingView bulk API (Stage 1) → Quality pre-filter (Stage 2) → yfinance deep fundamentals (Stage 3)
- 6-axis "Fortress Score" (0-100):
  - ROIC Efficiency (25%) — How well management deploys capital
  - FCF Yield (20%) — Real cash generation vs price
  - Balance Sheet (15%) — Debt/EBITDA + interest coverage
  - Margin Quality (15%) — Operating margin level + gross margin bonus
  - Growth Durability (15%) — Revenue growth + earnings trajectory
  - Shareholder Return (10%) — Dividends + buybacks
- Tiers: 🏰 FORTRESS (80+) → 🛡️ CASTLE (65-79) → 🏠 HOUSE (50-64) → 🏚️ SHACK (30-49) → 💀 RUBBLE (<30)
- CPI-readiness flag: ROIC≥12%, OpMargin≥15%, Debt/EBITDA≤3x, IntCov≥5x
- First full scan ($5B+ cap): **79 Fortress, 219 Castle, 208 CPI-ready** out of 771 stocks
- Top 5: ORLA (97.8), KNSL (96.2), KGC (95.0), IBKR (94.8), CF (93.5)
- CLI: `python3 -m dossier.roic_fortress_screener [--tickers X,Y] [--sector Tech] [--min-cap 10B] [--top 30] [--json] [--csv file.csv] [--cpi-only]`

### 🔧 GitHub Actions Race Condition Fix
- **`.github/workflows/ghost_daily.yml`** — Added `concurrency: ghost-daily` group + `cancel-in-progress: true`
- **`.github/workflows/daily_dossier.yml`** — Added `concurrency: daily-dossier` group + `cancel-in-progress: false`
- Both workflows now do `git pull --rebase origin main || true` before push
- Fixes the recurring "Commit & Push: failure" step that was failing ~1x/day

---

## Key Files Changed

| File | Status |
|------|--------|
| `dossier/roic_fortress_screener.py` | ✅ NEW — Full ROIC quality screener |
| `dossier/data/fortress_scan.csv` | ✅ First scan results (771 stocks) |
| `.github/workflows/ghost_daily.yml` | ✅ Race condition fix |
| `.github/workflows/daily_dossier.yml` | ✅ Race condition fix |

---

## Known Issues

- **CSP scanner** still fails: `No module named 'strategies'` (stage 7 of pipeline)
- **Momentum picks** fail: f-string backslash error in `ticker_page.py` line 326
- **TickerTrace** is DNS-unreachable from this machine
- **Substack API** (`substack-api` npm package) is blocked by Cloudflare; use Playwright instead
- **Auto-backtest** references wrong path (`/home/sam/` instead of `/home/mph/`)
- **ROIC Screener bank scoring** — Financial sector ROIC can be inflated due to leverage structure; may need sector-specific adjustments
- **tmp/substack_social/** has node_modules that almost got committed — added to .gitignore

---

## Algo Bot (Still Live from 2026-04-04)

### Quick Commands
```bash
ssh newvultr "journalctl -u ghost-vwap-algo -f"           # Watch live logs
ssh newvultr "systemctl status ghost-vwap-algo"            # Check status
ssh newvultr "systemctl restart ghost-vwap-algo"           # Restart
```

---

## What's Next

- [ ] Publish the Q1 Accounting article to Substack
- [ ] Fix the CSP scanner (remove `strategies` dependency)
- [ ] Fix `ticker_page.py` line 326 f-string backslash error
- [ ] Fix auto-backtest path from `/home/sam/` to `/home/mph/`
- [ ] Integrate Fortress Screener into the daily dossier pipeline
- [ ] Add Fortress scan results to the landing page / widget system
- [ ] Sector-adjusted ROIC scoring for financials (leverage skews ROIC high)
- [ ] Fund the Tradier account beyond $71
