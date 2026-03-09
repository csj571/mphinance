---
description: Run the full dossier pipeline and deploy to GitHub Pages
---

## Steps

1. Check if the pipeline ran today:
```bash
ls -la docs/reports/ | tail -5
```

2. Run the pipeline manually (from repo root):
```bash
python -m dossier.generate --no-pdf
```

3. Commit and push:
```bash
git add docs/ dossier/persistence/data/
git commit -m "📊 Alpha Dossier $(date +%Y-%m-%d)"
git push
```

4. Verify GH Pages deploy:
```bash
curl -sI https://mphinance.github.io/mphinance/ | head -5
```

## Notes
- Pipeline also runs automatically via GH Actions at 5AM CST Mon-Fri
- If it fails, check `gh run list --limit 5` for errors
- Common failure: Gemini API rate limits or TickerTrace timeouts
