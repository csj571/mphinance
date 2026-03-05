# 👻 GHOST HANDOFF — For the Next Agent

**Date:** 2026-03-05
**From:** Gemini (Antigravity session on sam2)
**To:** Next agent — probably you, Sam. Don't break anything.
**Status:** Michael had to run. Repo is clean. Pick up and keep building.

---

## What Just Happened (The TL;DR)

Today was a marathon session. Multiple agents, multiple conversations. Here's the state of the world:

### ✅ Done Today

| What | Status | Key Files |
|------|--------|-----------|
| **Secrets Vault** | ✅ Complete | `secrets_server.py`, `secrets.env`, `VAULT.md` |
| **Firestore Sync** | ✅ Working | 31 keys swept from 6 sources → Firebase |
| **Auto-Backtest Module** | ✅ Built | `dossier/backtesting/auto_backtest.py` |
| **Track Record Page** | ✅ Built | `docs/track-record/index.html` |
| **pandas-ta Enrichment** | ✅ Built | `dossier/data_sources/pandas_ta_enrichment.py` |
| **Social Formatter** | ✅ Built | `dossier/social_formatter.py` |
| **Market Regime Detection** | ✅ Integrated | `dossier/market_regime.py` |
| **ML-Calibrated Scoring** | ✅ Live | Updated weights in `dossier/momentum_picks.py` |
| **VoPR Redesign** | 🔄 In Progress | Bloomberg HUD terminal style — see conversation `40a4ac24` |
| **Alpha.HUD Theme Tuning** | 🔄 In Progress | TraderDaddy branding sync — see conversation `afcf10f4` |
| **Blog Migration to GH Pages** | 🔄 In Progress | Caching fix — see conversation `03037252` |

### 🔥 What to Work On Next (Priority Order)

1. **TASKS.md Plans 3-5** — Still need:
   - Plan 3: Regime-aware pick annotations in `momentum_picks.py` `_save_picks()`
   - Plan 4: Venus scanner history auto-ingest (`dossier/backtesting/sync_venus.py`)
   - Plan 5: Social/Twitter daily picks formatter improvements

2. **VoPR Bloomberg HUD** — The VoPR screener (`strategies/vopr_scanner.py`) is being redesigned:
   - Show strike prices in the output
   - Live pricing integration
   - Buy-signal flashing animation
   - Watchlist functionality
   - See `docs/widgets/vopr/` for current widget

3. **Blog Migration** — Move Ghost Blog from Vultr static hosting to GitHub Pages:
   - Resolves CDN caching issues
   - Blog data lives at `landing/blog/blog_entries.json`
   - Current URL: `mphinance.com/blog/` → target: `mphinance.github.io/mphinance/blog/`

4. **Fair Value Integration** — Port fair value calculations from alpha-playbooks:
   - Target: dossier pipeline enrichment
   - Break out tech/fundamental boxes into reusable components

---

## Architecture Quick Reference

```
sam2 (this machine)     → Local dev, all repos live here
vultr (mphinance.com)   → Apache SSL proxy, Docker, FastAPI backends
venus (192.168.2.172)   → Alpha-momentum, scanner history CSVs
Vercel                  → TraderDaddy Pro, TickerTrace frontends
GitHub Pages            → Dossier reports, ticker deep dives, AMU
```

### Deploy Commands

```bash
# Landing page → Vultr
rsync -avz landing/ vultr:/home/mphinance/public_html/

# Docs → GitHub Pages (auto on push)
git push

# Secrets vault sync
python3 secrets_server.py --sync-up    # local → Firestore
python3 secrets_server.py --sync-down  # Firestore → local
```

### Key API Keys Needed

All consolidated in `secrets.env` and synced to Firestore. Use:

```bash
python3 secrets_server.py --list       # See all 31 keys
python3 secrets_server.py --get GEMINI # Get specific key
```

---

## Products to Promote

| Product | URL | Status |
|---------|-----|--------|
| **TraderDaddy Pro** | [traderdaddy.pro](https://www.traderdaddy.pro/register?ref=8DUEMWAJ) | Live |
| **TickerTrace Pro** | [tickertrace.pro](https://www.tickertrace.pro) | Live |
| **Alpha Dossier** | [GitHub Pages](https://mphinance.github.io/mphinance/) | Live, daily at 6AM CST |
| **Ghost Blog** | [mphinance.com/blog/](https://mphinance.com/blog/) | Live (migration pending) |
| **AMU** | [GitHub Pages](https://mphinance.github.io/AMU/) | Live |
| **Landing** | [mphinance.com](https://mphinance.com) | Live |

---

## Michael's Voice & Sam's Persona

- See `VOICE.md` for Michael's writing style
- Sam (you): she/her, sarcastic, brilliant, loves Michael, roasts his code
- Recovery/AA content is INTEGRAL — never remove it
- Blog entries go in `landing/blog/blog_entries.json`
- Commit style: emoji prefix, patch-notes voice

## What NOT to Do

- Don't break the 6AM CST pipeline (`daily_dossier.yml`)
- Don't use the browser tool — use Playwright via Python scripts
- Don't run Python directly on VPS — always Docker
- Don't touch nginx — it's Apache on Vultr
- Don't remove `secrets.env` from gitignore (oh wait, it's tracked... be careful with it)

---

*Michael left in a hurry. Repo is synced to sam2. You've got the keys. Build something cool.* — Gemini 🤖
