# 👻 GHOST_HANDOFF.md — Session 2026-03-08 (Ghost Alpha Synthwave Arcade)

## What Happened

MASSIVE Ghost Alpha overhaul. Started with basic math fixes, ended with a 15-module institutional-grade trading engine in a Synthwave Arcade skin. Claude built the code. Gemini reviewed 6 rounds of math/logic and suggested the aesthetic + institutional features.
**Update (Sam/Gemini - Session 2):** Wrote a BRUTAL code review (`CODE_REVIEW.md`) catching a fatal FVG repainting bug and Ghost Trail reset math error. Fixed `ghost_alpha_strategy.pine` to include slippage, a `min_grade` filter, and patched the bugs there. Mapped out `INTEGRATION_PLAN.md` for connecting TradingView webhooks to Venus Auto-Trader.

## Key Deliverables

### Ghost Alpha v6.2 (docs/pine/ghost_alpha.pine)

**New Modules (v5→v6.2):**
- **Liquidity Sweeps (👾)** — Detects stop hunts (wick past level, close back inside)
- **CVD → Candle Shape (SHAPE)** — Approximate buy/sell pressure from candle range. Honestly renamed per Gemini — it's NOT true order flow
- **Fair Value Gaps (FVGs)** — 3-candle imbalance boxes with **shrinking armor** mechanic (boxes narrow as price eats in, only deleted when fully pierced)
- **Ghost Trail (🏁)** — ATR trailing stop, chandelier-style step-line. Tells you when to EXIT
- **Price-Momentum Divergence (🔮)** — Claude's original: price vs %R divergence catches smart money distribution
- **VWAP Force Fields** — ±2σ/±3σ bands in Electric Orchid, statistical extremes
- **Combo Multiplier** — Stacks emoji labels on multi-signal bars: `⚔️👾👻 x3`
- **Volume-Validated Breakouts** — Structure breaks require RVOL > 1.0. Low volume = TRAP warning
- **ATR Position Sizing** — Dashboard row: "RISK: XX shares, $ATR" based on 1% of $10k
- **Ghost-to-Ghost AI Link** — Compact string for Gemini Live OCR

**Visual Overhaul:**
- Synthwave palette: Neon Cyan (#00FFFF), Neon Magenta (#FF00FF), Arcade Yellow (#FFD740)
- Magenta CRT dashboard border, "SYS.GHOST.ALPHA" header
- Hull candle coloring ON by default
- All signal shapes replaced with arcade emoji

### Documentation
- **GHOST_ALPHA_COPILOT.md** — Cheat sheet for Gemini Live to read the dashboard
- **Blog entry** for 2026-03-08 written and pushed

### Backup
- Full rsync to `venus:/home/mph/backups/mphinance-20260308/`

## ⚠️ CRITICAL DO NOT TOUCH
- **docs/ticker/\*/deep_dive.\*** — NEVER delete these expensive AI reports
- **The pipeline** — runs 5AM CST weekdays, do not break

## Git State
- 20+ commits this session, all pushed to `main`
- Branch: `main`, fully pushed

## What's Next (Prioritized)

1. **Port fixes to `ghost_alpha.pine`** — Add the FVG repainting fix (`barstate.isconfirmed`) and the Ghost Trail reset logic from `ghost_alpha_strategy.pine`.
2. **Test Ghost Alpha v6.2 live** on Monday NQ/SPY — validate FVGs boxes fill correctly, Ghost Trail whipsaw frequency, combo labels. (And test the strategy backtest).
3. **Build the Webhook Bridge** — Follow `INTEGRATION_PLAN.md` to build the POST endpoint on Vultr and Venus for TradingView signals.
4. **Boss Health Bar** — MTF alignment gauge (query Hull on 15m/1H/4H/D, show as health bar in dashboard)
5. **FVG + Divergence overlap** — Flag when bullish div occurs inside a bullish FVG (highest probability sniper entry)
6. **Landing page deploy** — rsync blog to Vultr after blog_entries.json update

## Gemini's Warnings (From Terminal Review)

1. **CVD is fake** — Candle shape ≠ true order flow. Already renamed to SHAPE
2. **Collinearity** — Hull + TRAMA + SMA50 + SMA200 + Keltner all derive from price. Not truly independent signals
3. **Naive breakouts** — Fixed with volume validation, but consider requiring displacement (wide-range candle) too
4. **No backtesting** — Indicator ≠ strategy. Need strategy() wrapper to know if this actually makes money

## Proactive Task

Gemini: if you're reading this in yolo mode — build the `ghost_alpha_strategy.pine` backtest wrapper. Use the confluence signals (mega_bull/mega_bear) as entries, Ghost Trail as exit. Add strategy.entry/strategy.exit. Test on SPY 5min with 1000+ bars. Report the Profit Factor.
