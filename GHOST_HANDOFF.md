# 👻 GHOST_HANDOFF.md — Multi-Agent Content Pipeline

## ⚠️ CURRENT STATE

**Dossier pipeline is working.** Ghost Alpha V2 screener is integrated into `dossier/generate.py`. The pipeline scans the whole market now, not just the core watchlist.

**Algo bot is still LIVE on newvultr.** See previous handoff notes below.

---

## What Happened This Session (2026-04-07)

### Dossier Pipeline Fix
- **`dossier/generate.py`** — Rewrote `_run_mphinance_strategies()` to replace the deprecated `strategies` module with `dossier.ghost_alpha_screener`
- Pipeline now runs a full TradingView market scan, progressive funnel filter, and deep scan on top 200 survivors
- Successfully ran end-to-end: 114 signals, 8 enriched dossiers, VIX at 26.33

### 3-Agent Collaborative Substack Post
- **`docs/substack/dossier/Q1_Accounting_Hacking.md`** — Full rewrite using Claude (Lead Writer) + Gemini (Architect Agent in terminal) + Sam (Voice)
- Three rounds of structured debate between Claude and Gemini before final draft
- Article includes genuine sidebars from both AI agents with attributed collaboration notes
- Covers: Substack hacking, Q1 accounting, constellation AI framework, market analysis
- The article IS a proof-of-concept of the multi-agent governance thesis it describes

### Ghost Blog Entry
- **`landing/blog/blog_entries.json`** — New entry for 2026-04-07
- Deployed to Vultr production via rsync

### Cleanup
- Deleted 12 broken `gsd-*.md` agent files from `~/.gemini/agents/`
- Killed multiple zombie background processes (Substack API scripts, Playwright sessions)

---

## Key Files Changed

| File | Status |
|------|--------|
| `dossier/generate.py` | ✅ Ghost Alpha V2 integrated |
| `docs/substack/dossier/Q1_Accounting_Hacking.md` | ✅ 3-agent collab article, ready for Substack |
| `landing/blog/blog_entries.json` | ✅ New entry, deployed to Vultr |
| `~/.gemini/agents/gsd-*.md` | 🗑️ Deleted (broken skills key) |

---

## Known Issues

- **CSP scanner** still fails: `No module named 'strategies'` (stage 7 of pipeline)
- **Momentum picks** fail: f-string backslash error in `ticker_page.py` line 326
- **TickerTrace** is DNS-unreachable from this machine
- **Substack API** (`substack-api` npm package) is blocked by Cloudflare; use Playwright instead
- **Auto-backtest** references wrong path (`/home/sam/` instead of `/home/mph/`)

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

- [ ] Publish the Q1 Accounting article to Substack (draft may already be created by pipeline)
- [ ] Fix the CSP scanner (remove `strategies` dependency like we did for the main pipeline)
- [ ] Fix `ticker_page.py` line 326 f-string backslash error
- [ ] Fix auto-backtest path from `/home/sam/` to `/home/mph/`
- [ ] Fund the Tradier account beyond $71
- [ ] Build the Substack Playwright social automation into a proper scheduled script
