# Subagent Task: TradingView Pine Script — Bounce 2.0 Indicator

## Goal

Write a TradingView Pine Script v6 indicator that implements the Bounce 2.0 momentum scoring logic from our Python scorer, so users can see the signals directly on their charts.

## Context

- The scoring logic is in `dossier/momentum_picks.py` → `score_momentum()`
- Michael's TradingView account is `mph1nance`
- Existing published scripts are at: <https://www.tradingview.com/u/mph1nance/#published-scripts>

## Scoring Logic to Port (simplified for Pine)

### EMA Stack (must have all 5)

- EMA 8, 21, 34, 55, 89
- FULL BULLISH = 8 > 21 > 34 > 55 > 89
- Color background green when FULL BULLISH

### Bounce 2.0 Signal (the main alert)

Fire when ALL are true:

1. EMA stack is FULL BULLISH or PARTIAL BULLISH (8 > 21, 21 > 55)
2. ADX(14) >= 25 (strong trend)
3. Stochastic K(14,3,3) <= 40 (oversold in uptrend = pullback)
4. Price is within -3% to +5% of EMA 21 (near support)

### Additional factors to show

- RSI(14) sweet spot (40-65 = green, >70 = red)
- Relative volume (volume / SMA(volume, 10))

## Output File

Save to: `docs/pine/bounce2_indicator.pine`

## Pine Script Requirements

- Use Pine Script v6 (`//@version=6`)
- `indicator("Bounce 2.0 — mph1nance", overlay=true)`
- Plot EMA ribbons (8/21/34/55/89) with Michael's color scheme:
  - EMA 8: cyan, EMA 21: yellow, EMA 34: orange, EMA 55: red, EMA 89: purple  
- When Bounce 2.0 fires: plot a label below the bar with "⚡ B2.0"
- Add an `alertcondition()` so users can set alerts
- Show a score table in top-right corner with factor breakdown
- Include a `plotshape` for when all factors align

## Style

- Dark chart friendly (use bright colors on dark backgrounds)
- Clean, not cluttered — the EMA ribbons do most of the visual work
- Add tooltips explaining each factor
