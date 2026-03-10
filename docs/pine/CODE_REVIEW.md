# 👻 Ghost Alpha v6.2 — BRUTAL CODE REVIEW

## 🚨 FATAL BUGS & MATH ERRORS

### 1. The "Widowmaker" FVG Repainting Bug (Lines 298-336)
**The Bug:** `fvg_bull` and `fvg_bear` are evaluated continuously on the *live* forming bar. 
```pine
bool fvg_bull = low > high[2] and close[1] > open[1]
```
Since `low` updates intra-bar, a box can be created, pushed to the array, and then left there even if the gap fills before the candle closes. You are creating boxes that don't exist in historical data.
**The Fix:** You MUST wrap FVG creation in `if barstate.isconfirmed`.

### 2. Ghost Trail "Death Hug" Reset Failure (Lines 345-348)
**The Bug:** When the Hull trend flips, `ghost_trail` does not reset correctly because it uses `ghost_trail[1]`.
```pine
if hull_bull
    ghost_trail := math.max(nz(ghost_trail[1], long_stop), long_stop)
```
When flipping from Bear to Bull, `ghost_trail[1]` is the old *short stop* (which is way ABOVE the current price). `math.max` will happily select the old short stop, instantly stopping out the new long trade on the very first bar.
**The Fix:** Force a reset on trend flips:
```pine
ghost_trail := hull_flip_bull ? long_stop : math.max(nz(ghost_trail[1], long_stop), long_stop)
```

### 3. Delusional Annualization in Synthetic IV (Lines 216-218)
**The Bug:** 
```pine
float bars_per_day = math.max(86400.0 / _tf_sec, 1.0)
```
This assumes the market is open 24/7 (86,400 seconds). For traditional equities (SPY, QQQ), the market is open 6.5 hours (23,400 seconds). By using 86400 on a 5-minute stock chart, your `bars_per_day` is 288 instead of 78. This drastically inflates the annualized HV calculation, completely destroying the IV Rank's accuracy. 

### 4. Overlapping Signal Redundancy (Collinearity)
Your "10-Axis Scoring" is actually just 3 axes wearing different hats.
- Hull, TRAMA, SMA50, SMA200, and Keltner Baseline are all just smoothed price.
- If price goes up rapidly, *all of them* will turn bullish at roughly the same time. You are double, triple, and quadruple counting momentum and calling it "confluence."

### 5. "CVD" is just Candle Shape (Line 234)
You renamed it, but `float buy_pressure = (close - low) / candle_range` is inherently flawed for momentum scoring. A massive red doji where the close is slightly above the midpoint is calculated as "buy pressure," ignoring the massive rejection wick at the top. 

## ⚖️ VERDICT
Aesthetically beautiful, mathematically dangerous. Fix the repainting FVGs and the Ghost Trail reset immediately, or this script will hemorrhage capital in live trading.