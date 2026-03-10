---
description: Add a stock ticker to the watchlist for deep-dive generation
---

# Add Ticker to Watchlist

## How It Works

`watchlist.txt` holds the **current ticker** to generate a deep dive for. Replace the
existing ticker with the new one — this avoids re-running expensive Gemini AI reports.

## Steps

1. **Edit `watchlist.txt`** — replace the current ticker with the new one (keep the header comments)

2. **Commit and push** to trigger the GitHub Actions deep-dive workflow:

```bash
cd /home/sam/Antigravity/empty/mphinance && git add watchlist.txt && git commit -m "📋 Add TICKER to watchlist" && git push
```

## What Happens Next

- Pushing `watchlist.txt` to `main` triggers `.github/workflows/watchlist_dive.yml`
- The workflow runs `python -m dossier.watchlist_dive` for the ticker in the file
- Deep dive reports are generated in `docs/ticker/TICKER/` (html + md + json)
- The index page at `docs/index.html` is regenerated with all tickers grouped by sector

## Important

- **Deep dive reports persist** in `docs/ticker/TICKER/` even after the ticker is removed from `watchlist.txt`
- The index page scans `docs/ticker/` directories directly — it does NOT read `watchlist.txt`
- **DO NOT** delete `docs/ticker/*/deep_dive.*` files — these are expensive AI-generated reports
- **DO NOT** add `deep_dive.*` patterns to `.gitignore` — this was done once and destroyed all reports
