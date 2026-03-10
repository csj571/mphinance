# 👻 GHOST_HANDOFF.md — Night Shift 2026-03-09 (Pipeline Polish + Summary API)

## ⚠️ RESUME PRIORITY

1. **Deploy landing page to Vultr** — `rsync -avz landing/ vultr:/home/mphinance/public_html/` — new regime badge, Sam quotes, dynamic stats need to go live
2. **Run pipeline dry-run** to verify PipelineTimer + Summary API work end-to-end
3. **Fix Gemini yolo agent loading errors** — `~/.gemini/agents/gsd-*.md` files have `skills` key that Gemini doesn't recognize
4. **Wire Discord notification for Summary API** — when `docs/api/dossier-summary.json` is generated, post gold pick + VIX regime to Discord

---

## What Happened This Session (Night Shift)

### Data Analysis First
- Pulled GA4 data: 100% of traffic (1,116 views, 172 users) comes from Substack
- mphinance.com and GitHub Pages: ZERO tracked views
- Pipeline: 80% success rate (8/10 recent runs)
- Conclusion: Distribution is the bottleneck, not content creation

### Pipeline Infrastructure
- **PipelineTimer** — per-stage timing + error tracking, wired into every stage
- **Stage numbering** — fixed chaotic 8a/8b/8c to clean 1-16
- **Retry decorator** (`dossier/utils/retry.py`) — exponential backoff + jitter
- **Retry wired** into TickerTrace + market_pulse (Yahoo Finance) — the top 2 failure sources
- **Graceful degradation** — APIs return empty data after retries instead of crashing
- **GA4 stats** wired into pipeline (local-only, needs OAuth)
- **pipeline_stats.json** — dynamic stats for landing page consumption

### New Pipeline Features
- **Dossier Summary API** (`dossier/report/summary_api.py`) → `docs/api/dossier-summary.json`
  - Market snapshot, gold/silver/bronze picks with entry/target/stop, top 5 signals, grades, Sam's quote, narrative one-liner
  - Also generates `docs/api/latest.json` and date-stamped archives
  - The "atomic content unit" that feeds all distribution channels
- **Pipeline Status Dashboard** (`dossier/report/status_page.py`) → `docs/status.html`
  - Health score, stage timing bars, error log, coverage stats, 30-run history dots

### Landing Page
- **Market regime badge** in nav — 🟢🟡🔴💀 based on VIX level
- **Sam's Quote of the Day** — rotates daily in hero section
- **Dynamic hero badge** — shows "LAST DOSSIER: 3h ago · 12 signals"
- **Dynamic stats** — scanner count, ETF count, signals today from pipeline_stats.json
- **Signals Today** new stat card added
- **pipeline_stats.json seeded** with initial data so page works before first run

### Blog Page
- **Search bar** with real-time keyword filtering in Sam's voice

### Report Template
- **OG/Twitter meta tags** for social sharing
- **Print-friendly stylesheet** — white bg, readable colors
- **Keyboard navigation** — J/K section nav, T top, ? help
- **Read progress bar** — gradient bar at top showing scroll position
- **Scroll-to-top button** with keyboard hint tooltip

## What's Still Broken / Needs Work
- ❌ Landing not yet deployed to Vultr (pushed to GitHub only)
- ❌ Discord bot still not running
- ⚠️ Gemini yolo mode has agent loading errors (~/.gemini/agents/gsd-*.md)
- ⚠️ Ebook checkout — Ghost Alpha works ($8), Playbook needs work
- ⚠️ Revenue from GA4 tracking needs cross-domain setup for GitHub Pages

## Key Files Created/Changed
- `dossier/generate.py` — PipelineTimer, stage numbering, Summary API wiring, GA4 refresh
- `dossier/report/status_page.py` — **NEW** — Pipeline Status Dashboard
- `dossier/report/summary_api.py` — **NEW** — Dossier Summary API
- `dossier/utils/retry.py` — **NEW** — Retry decorator with exponential backoff
- `dossier/data_sources/tickertrace.py` — retry wired in
- `dossier/data_sources/market_pulse.py` — refactored with retry
- `dossier/report/template.html` — OG meta, print CSS, keyboard nav, progress bar
- `landing/index.html` — regime badge, Sam quotes, dynamic stats, hero badge
- `landing/blog/index.html` — search bar
- `landing/data/pipeline_stats.json` — **NEW** — seeded pipeline stats

## VaultGuard Reminder
One `service_account.json` → Firebase Firestore → all API keys.
