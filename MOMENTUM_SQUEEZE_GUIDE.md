# Momentum & Squeeze Strategy Guide

Two complementary strategies that capture different phases of a stock's momentum cycle.

---

## The Relationship

```
┌─────────────────────────────────────────────────────────────────┐
│                    THE MOMENTUM CYCLE                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   VOLATILITY SQUEEZE          MOMENTUM WITH PULLBACK            │
│   ═══════════════════         ══════════════════════            │
│                                                                 │
│   Stock coils quietly    →    BREAKOUT!    →    Stock trends    │
│   Low volatility               Volume spike       Strong move   │
│   EMAs aligned                 Price expands      EMAs expand   │
│                                                                 │
│            ↑                                          ↓         │
│            │                                          │         │
│            │         ← ── PULLBACK ── ←               │         │
│            │            Price retraces                │         │
│            │            to EMA21                      │         │
│            │            Stoch oversold                │         │
│            │                                          │         │
│            └──────── RE-COIL (consolidation) ─────────┘         │
│                      Volatility compresses                      │
│                      Back to Squeeze scanner                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1️⃣ Volatility Squeeze ("The Snap")

**Purpose:** Find stocks that have been **quietly coiling** and are ready to **explode**.

### What Makes a Squeeze

| Condition | Meaning |
|-----------|---------|
| **SqueezeRatio < 1.0** | Daily ATR is compressed vs weekly ATR (volatility contraction) |
| **SqueezeRatio < 0.7** | Extremely tight squeeze — maximum coil |
| **EMA Stack Aligned** | 8 > 21 > 34 > 55 > 89 (bullish bias) |
| **Not at 52wk High** | Not a flatlined M&A target |
| **Rel Volume ≥ 1.3x** | Starting to wake up |

### The Squeeze Ratio
```
SqueezeRatio = ATR(14) / (ATR_Weekly / 2)

< 0.70  →  🔋 Tight Squeeze (ready to snap)
< 0.85  →  ⚡ Moderate Squeeze
< 1.00  →  📊 Light Compression
> 1.00  →  ❌ Expanded (not squeezed)
```

### Entry Signals
- **Volume Spark** (1.5x+) — Institutions entering
- **Deep Coil** (ADX < 15) — Maximum compression
- **Price at EMA** — Clean entry level

### Entry Thesis
> "This stock has gone quiet. The daily volatility is compressed against the weekly baseline. EMAs are bullishly stacked. Volume is picking up. It's ready to snap out of the coil."

---

## 2️⃣ Momentum with Pullback

**Purpose:** Find stocks in **confirmed uptrends** that have **pulled back** to a buyable entry.

### The TAO Multi-Timeframe EMA Stack

This strategy requires **triple timeframe alignment**:

```
DAILY:    EMA8 > EMA21 > EMA34 > EMA55 > EMA89  ✓
WEEKLY:   EMA8 > EMA21 > EMA34 > EMA55 > EMA89  ✓
MONTHLY:  EMA8 > EMA21 > EMA34 > EMA55 > EMA89  ✓
          ─────────────────────────────────────
          ALL THREE = CONFIRMED MEGA-TREND
```

### Pullback Filters

| Condition | Purpose |
|-----------|---------|
| **SMA50 > EMA200** (D/W/M) | Uptrend on all timeframes |
| **Stochastic < 40** | Oscillator oversold (dip) |
| **Within 1 ATR of EMA21** | Not overextended |
| **ADX 20-40** | Trending but not exhausted |

### Entry Thesis
> "This stock is in a powerful multi-timeframe uptrend — daily, weekly, AND monthly EMAs all stacked bullish. But it just pulled back to the 21 EMA. The stochastic is oversold. Perfect dip buy."

---

## How They Connect

### Squeeze → Momentum Flow

1. Stock appears on **Volatility Squeeze** (coiled, ready to break)
2. Volume spikes, price breaks out 🚀
3. After initial run, price pulls back to EMA21
4. Stock now appears on **Momentum with Pullback** (confirmed trend, buying the dip)
5. Ride the trend with additional entries on pullbacks

### Momentum → Squeeze Flow

1. Strong trend eventually exhausts (ADX peaks, stoch overbought)
2. Stock consolidates sideways (volatility contracts)
3. Daily ATR compresses toward weekly baseline
4. Stock reappears on **Volatility Squeeze** (new coil forming)
5. Watch for next breakout

---

## Quick Comparison

| Aspect | Volatility Squeeze | Momentum with Pullback |
|--------|-------------------|----------------------|
| **Stage** | Pre-breakout | Mid-trend |
| **Volatility** | Compressed | Normal/Expanded |
| **ADX** | Lower (can be any) | 20-100 |
| **Stochastic** | Any | < 40 (oversold) |
| **Volume** | Waking up (≥1.3x) | Normal |
| **Risk** | Higher (breakout may fail) | Lower (trend confirmed) |
| **Reward** | Higher (catch the snap) | Moderate (ride the wave) |
| **Timeframe Focus** | Daily only | Daily + Weekly + Monthly |

---

## Practical Workflow

```
WEEKLY ROUTINE
──────────────

1. Saturday/Sunday: Run VOLATILITY SQUEEZE
   → Watchlist stocks that are coiled

2. Monday-Friday: Monitor watchlist for breakouts
   → Entry on volume + close above resistance

3. Mid-week: Run MOMENTUM WITH PULLBACK
   → Find pullback entries in existing trends

4. Manage positions:
   → Stop below EMA21 (for momentum plays)
   → Trail stops as trend continues

5. When trend exhausts → stock goes back to Squeeze watchlist
```

---

## Files

| Strategy | File |
|----------|------|
| Momentum with Pullback | `strategies/momentum.py` |
| Volatility Squeeze | `strategies/volatility_squeeze.py` |
