# Daily Momentum Picks — API Integration Guide

## Endpoint

```
https://mphinance.github.io/mphinance/api/daily-picks.json
```

No auth needed. Updates daily after pipeline run (~6AM CST via GitHub Actions).
CORS-safe (GH Pages static JSON).

## Quick Fetch

```python
import requests
picks = requests.get("https://mphinance.github.io/mphinance/api/daily-picks.json").json()

gold = picks["picks"][0]   # Best setup of the day
silver = picks["picks"][1]
bronze = picks["picks"][2]

print(f"🥇 {gold['ticker']} — {gold['score']}/100")
print(f"   Pullback: {'⚡ YES' if gold['is_pullback_setup'] else 'No'}")
```

```javascript
// Frontend fetch
const res = await fetch("https://mphinance.github.io/mphinance/api/daily-picks.json");
const { picks, date, scoring_weights } = await res.json();
```

## Response Shape

```json
{
  "date": "2026-03-05",
  "generated_at": "2026-03-05 11:49:43",
  "picks": [
    {
      "rank": 1,
      "medal": "gold",
      "ticker": "INVA",
      "score": 85,
      "raw_score": 85,
      "quality_score": 100,
      "is_pullback_setup": true,
      "price": 22.73,
      "change_pct": 1.9,
      "grade": "A",
      "ema_stack": "FULL BULLISH",
      "trend": "Bullish",
      "rsi": 52.4,
      "adx": 61.9,
      "stoch_k": 20.7,
      "rel_vol": 0.75,
      "breakdown": {
        "ema_stack": 20,
        "pullback": 15,
        "adx": 15,
        "rsi": 10,
        "trend": 10,
        "rel_vol": 2,
        "price_vs_ema": 10,
        "macd": 3,
        "institutional": 0
      },
      "quality_flags": {},
      "quality_reasons": [],
      "tradingview_url": "https://www.tradingview.com/symbols/INVA/"
    }
  ],
  "total_scored": 21,
  "all_ranked": [
    {"ticker": "INVA", "score": 85, "grade": "A", "is_pullback": true, "ema_stack": "FULL BULLISH"},
    {"ticker": "NPKI", "score": 84, "grade": "A", "is_pullback": true, "ema_stack": "FULL BULLISH"}
  ],
  "scoring_weights": {
    "ema_stack":    {"max": 20, "desc": "EMA 8>21>34>55>89 alignment"},
    "pullback":     {"max": 15, "desc": "Bounce 2.0: EMA aligned + ADX>25 + Stoch<40 + near EMA21"},
    "adx":          {"max": 15, "desc": "ADX trend strength (>25 trending, >40 strong)"},
    "rsi":          {"max": 10, "desc": "RSI sweet spot (40-65 optimal)"},
    "trend":        {"max": 10, "desc": "Overall trend direction (Bullish/Bearish)"},
    "rel_vol":      {"max": 10, "desc": "Relative volume vs 20-day avg"},
    "price_vs_ema": {"max": 10, "desc": "Price proximity to EMA 21"},
    "macd":         {"max": 5,  "desc": "MACD histogram momentum"},
    "institutional":{"max": 5,  "desc": "TickerTrace institutional buying signal"}
  },
  "quality_gate": "final_score = raw_score × (quality_score / 100)",
  "history": [
    {"date": "2026-03-05", "gold": {"ticker": "INVA", "score": 85}, "silver": {...}, "bronze": {...}}
  ]
}
```

## Scoring System

**9 factors, max 100 raw points, then quality multiplied:**

| Factor | Max | What It Rewards |
|--------|-----|-----------------|
| EMA Stack | 20 | FULL BULL=20, PARTIAL=12, TANGLED=4, BEAR=0 |
| **Pullback** | **15** | **⚡ Bounce 2.0: EMA aligned + ADX>25 + Stoch<40 + near EMA21** |
| ADX | 15 | Trend strength: >40=15, >30=12, >25=8 |
| RSI | 10 | Sweet spot 40-65=10, 30-40/65-70=7, <30=4, >70=1 |
| Trend | 10 | Bullish=10, Bearish=0 |
| Rel Volume | 10 | >2x=10, >1.5x=8, >1x=5, <1x=2 |
| Price/EMA21 | 10 | Within 2% above=10, 2-5%=7, >5%=3, below=-1 |
| MACD | 5 | Histogram >0=5, >-0.5=3, else=0 |
| Institutional | 5 | TickerTrace buying signal=5 |

**Quality Gate** (multiplier, not additive):

- SPACs: -60 penalty → quality_score 40 → final = raw × 0.40
- Penny stocks (<$3): -40
- Junk bio (<$500M cap, no EPS, no rev): -45
- Shell companies: -70
- Pinned price (acquisition target): -15

## Key Fields for Dashboard

- `picks[].is_pullback_setup` — **True = Bounce 2.0 setup** (the bread and butter)
- `picks[].breakdown` — Every factor's earned points, fully transparent
- `picks[].quality_score` — 100 = clean, <100 = flagged (check `quality_reasons`)
- `picks[].tradingview_url` — Direct link, ready to open
- `all_ranked` — Full ranking if you want to show more than top 3
- `history` — Last 7 days of picks for trend tracking

## Source

Pipeline: `mphinance/dossier/momentum_picks.py`
Quality: `mphinance/dossier/quality_filter.py`
Backtest: `mphinance/dossier/backtesting/backtest_engine.py`
