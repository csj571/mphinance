---
description: Add a stock ticker to the watchlist and generate a deep dive report
---

## Steps

1. Add the ticker to watchlist (if not already present):
```bash
grep -q "TICKER" dossier/config.py || echo "  Add TICKER to WATCHLIST in dossier/config.py"
```

2. Generate a single-ticker deep dive:
```bash
python -m dossier.watchlist_dive --tickers TICKER
```

3. Verify output:
```bash
ls docs/ticker/TICKER/
```

4. Commit and push:
```bash
git add docs/ticker/TICKER/
git commit -m "🆕 Add TICKER to watchlist"
git push
```

## Notes
- Replace TICKER with the actual stock symbol (e.g., NVDA, AAPL)
- Deep dive generates: `deep_dive.md`, `deep_dive.html`, `deep_dive.json`
- The pipeline will also generate a `latest.json` + `latest.html` on next daily run
- DO NOT delete existing `deep_dive.*` files — they're expensive AI-generated reports
