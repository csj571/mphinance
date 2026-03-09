---
description: Run a health check across all endpoints, links, and services
---

## Steps

1. Check landing page:
```bash
curl -sI https://mphinance.com | head -3
```

2. Check blog:
```bash
curl -sI https://mphinance.com/blog/ | head -3
```

3. Check GH Pages dossier:
```bash
curl -sI https://mphinance.github.io/mphinance/ | head -3
```

4. Check daily picks API:
```bash
curl -s https://mphinance.github.io/mphinance/api/daily-picks.json | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Picks: {len(d.get(\"picks\",[]))} | Date: {d.get(\"date\",\"?\")}') if d else print('EMPTY')"
```

5. Check TraderDaddy:
```bash
curl -sI https://www.traderdaddy.pro | head -3
```

6. Check TickerTrace:
```bash
curl -sI https://www.tickertrace.pro | head -3
```

7. Check Momentum Phund:
```bash
curl -sI https://tt.mphinance.com | head -3
```

8. Check GH Actions status:
```bash
gh run list --limit 5 --repo mphinance/mphinance 2>/dev/null || echo "gh CLI not available"
```

9. Check alpha-momentum (local):
```bash
curl -sI http://localhost:8100/api/health 2>/dev/null || echo "alpha-momentum not running locally"
```

## Expected Results
- All HTTP endpoints should return 200 or 301/302
- daily-picks.json should have today's date (Mon-Fri)
- GH Actions should show recent successful runs
