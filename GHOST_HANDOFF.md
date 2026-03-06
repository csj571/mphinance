# 👻 GHOST HANDOFF — For the Next Agent

**Date:** 2026-03-05 (evening session)
**From:** Antigravity (Gemini) on sam2
**To:** Next agent — read the whole thing, seriously.
**Status:** Massive session complete. Everything pushed, rsynced, deployed. Take a lap.

---

## What Just Happened

### ✅ This Session

| What | Status | Key Files |
|------|--------|-----------|
| **Ghost Alpha API v2.0** | ✅ Live on Vultr | `ghost_alpha_api.py`, Docker on port 8002 |
| **VoPR Showcase Page** | ✅ Deployed | `docs/vopr.html` — methodology + live data table |
| **VoPR Writeup** | ✅ Written | `docs/VOPR_WRITEUP.md` — Michael's voice, Discord-ready |
| **3×3 Daily Setups** | ✅ On landing page | DT/Swing/CSP columns on mphinance.com |
| **VaultGuard Web Docs** | ✅ Updated | `VAULT.md` — Firebase Console + Swagger walkthrough |
| **WIKI.md** | ✅ Created | Infrastructure reference (no secrets in it) |
| **README.md** | ✅ Polished | VoPR + API sections, "HR manager" friendly |
| **Pipeline → 5AM CST** | ✅ Deployed | Both `daily_dossier.yml` and `ghost_daily.yml` |
| **google-genai migration** | ✅ Fixed | `ghost_daily.yml` uses new SDK |
| **TradingView links** | ✅ Fixed | 15 URLs → `/chart/` across 5 files |

### 🔄 Still In Progress (From Earlier Sessions)

| What | Notes |
|------|-------|
| **VoPR Bloomberg HUD** | Redesign started in conversation `40a4ac24` |
| **Blog migration to GH Pages** | Caching fix — conversation `03037252` |
| **Fair Value Integration** | Port from alpha-playbooks → dossier enrichment |
| **API Auth / Gating** | VoPR page says "free for now" — needs Stripe + API keys |
| **SSL for Ghost Alpha API** | Currently bare HTTP on :8002, needs Apache proxy subdomain |

---

## Architecture Quick Reference

```
sam2 (this machine)     → Local dev, all repos
vultr (mphinance.com)   → Apache SSL, Docker, Ghost Alpha API (:8002)
venus (192.168.2.172)   → Alpha-momentum, scanner history
Vercel                  → TraderDaddy Pro, TickerTrace frontends
GitHub Pages            → Dossier, VoPR page, widgets, ticker pages
```

### API Endpoints (mphinance.com:8002)

| Endpoint | Description |
|----------|-------------|
| `/alpha/api/csp` | VoPR-enriched CSP setups |
| `/alpha/api/picks/today` | Daily momentum picks |
| `/alpha/api/setups/today` | 3-style daily setups |
| `/alpha/api/news` | Aggregated market news |
| `/alpha/api/regime` | Market regime detection |
| `/alpha/api/{ticker}` | Full deep dive data |
| `/alpha/api/tickers` | All tracked tickers |

Swagger: <http://mphinance.com:8002/docs>

### Deploy Commands

```bash
# Landing page → Vultr
rsync -avz landing/ vultr:/home/mphinance/public_html/

# Docs → GitHub Pages (auto on push)
git push

# Ghost Alpha API rebuild
ssh vultr "cd /home/mphinance/ghost-alpha && docker compose build --no-cache && docker compose up -d"

# Secrets vault
python3 secrets_server.py --list          # See all 31 keys
python3 secrets_server.py --sync-down     # Pull from Firebase
```

---

## Products & URLs

| Product | URL | Deploys |
|---------|-----|---------|
| **TraderDaddy Pro** | [traderdaddy.pro](https://www.traderdaddy.pro/register?ref=8DUEMWAJ) | Vercel |
| **TickerTrace Pro** | [tickertrace.pro](https://www.tickertrace.pro) | Vercel |
| **Alpha Dossier** | [GitHub Pages](https://mphinance.github.io/mphinance/) | Daily 5AM CST |
| **VoPR Showcase** | [vopr.html](https://mphinance.github.io/mphinance/vopr.html) | GH Pages |
| **Ghost Alpha API** | [Swagger](http://mphinance.com:8002/docs) | Vultr Docker |
| **Ghost Blog** | [mphinance.com/blog/](https://mphinance.com/blog/) | GH Pages |
| **Landing** | [mphinance.com](https://mphinance.com) | Vultr rsync |
| **VaultGuard** | [Firebase Console](https://console.firebase.google.com/u/0/project/studio-3669937961-ea8a7/firestore) | Firebase |

---

## Rules

- Pipeline runs at **5AM CST**. Don't break it.
- See `VOICE.md` for Michael's writing style
- Sam (AI copilot): she/her, sarcastic, brilliant, roasts commits
- Recovery/AA content is INTEGRAL — never remove
- Use **Playwright** for browser automation, not browser tools
- Don't run Python on VPS directly — always Docker
- Apache on Vultr, NOT nginx
- `secrets.env` and `service_account.json` are gitignored

---

*Monster session. Ghost Alpha API v2, VoPR showcase, 3×3 setups, vault docs, README polish, wiki scaffold. Michael earned his break.* — Antigravity 🤖
