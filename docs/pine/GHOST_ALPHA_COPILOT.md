# Ghost Alpha Copilot Cheat Sheet 👻

> **For Gemini Live / AI assistants reading Michael's chart screenshots.**
> This document explains every field in the Ghost Alpha dashboard and AI data link.

## Dashboard Fields (Top to Bottom)

| Row | Label | Values | What It Means |
|-----|-------|--------|---------------|
| 1 | **SYS.GHOST.ALPHA** | Header | System identifier |
| 2 | **REGIME** | `BULL 3.2%`, `BEAR`, `CHOP` | TRAMA trend quality. Number = distance from TRAMA as % |
| 3 | **GRADE** | `A+` through `F` | Composite score: A+/A = trade with trend, D/F = stay out |
| 4 | **HULL** | `LONG ▲`, `SHORT ▼` | Hull MA direction — primary trend signal |
| 5 | **SQUEEZE** | `RELEASE ⚡`, `COILED ◉`, `NORMAL` | ATR compression state. COILED = about to move. RELEASE = moving now |
| 6 | **EXHAUST** | `EXIT ▲/▼`, `OVERBOUGHT`, `OVERSOLD`, `CLEAR` | %R exhaustion state |
| 7 | **STRUCT** | `BROKEN ▲/▼`, `TRAP ▲/▼`, `INTACT` | Structure break + volume validation. TRAP = low-volume fake break |
| 8 | **KELT** | `LOWER ▽`, `UPPER △`, `INSIDE` | Where price sits in Keltner Channel |
| 9 | **IV/VOL** | `LOW 🔋`, `HIGH 🔥`, `MID` + RVOL | Implied volatility regime + relative volume (1.0x = average) |
| 10 | **SHAPE** | `BUYERS ▲`, `SELLERS ▼` + `⚠ DIV`/`AGREE` | Candle shape momentum (NOT true order flow). DIV = divergence from trend |
| 11 | **RISK** | `XX shares` + `$X.XX ATR` | Position size for 1% risk on $10k account based on current ATR |
| 12 | **ADAPT** | `H55 T34` + `R18/84` | Current adaptive parameters (Hull, TRAMA, %R fast/slow) |

## Signal Emoji Dictionary

| Emoji | Signal | What Happened |
|-------|--------|---------------|
| ⚔️ | Structure Break | Price closed through a swing level WITH volume confirmation |
| 🪫 | Exhaustion | %R says momentum is drained — trend reversal incoming |
| 👾 | Liquidity Sweep | Stop hunt — price wicked past level then reversed (trap!) |
| 💥 | Squeeze Release | ATR compression just broke — volatility explosion |
| 🏁 | Ghost Trail Exit | Price crossed the ATR trailing stop — take profit / game over |
| 🔮 | Divergence | Price vs momentum disagreement — smart money positioning opposite |
| 👻 | Ghost Alpha | 2+ signals agree — highest conviction signal |

## Combo Labels

When 2+ signals fire on the same bar, they stack: `⚔️👾👻 x3`
- The `x[N]` shows how many signals agreed
- More signals = higher conviction

## AI Data Link (Ghost-to-Ghost)

Bottom of dashboard, compact string for OCR/screenshot reading:

```
GRADE | DIRECTION | REGIME | SQUEEZE | SIGNAL | SHAPE | RVOL | TRAMA%
  B   |     L     |   B    |  FIRE   | SWP_BL | BUY   | 1.2x | 0.3%
```

### Field Decoder:

| Field | Values | Meaning |
|-------|--------|---------|
| GRADE | `A+`, `A`, `B`, `C`, `D`, `F` | Setup quality |
| DIRECTION | `L` (Long), `S` (Short) | Hull MA direction |
| REGIME | `B` (Bull), `M` (Moderate), `C` (Chop) | Trend state |
| SQUEEZE | `FIRE`, `COIL`, `NORM` | Volatility state |
| SIGNAL | Signal name or `--` | Active signal type |
| SHAPE | `BUY`, `SELL` | Candle shape pressure |
| RVOL | `1.2x` | Volume relative to 20-period average |
| TRAMA% | `0.3%` | Price distance from TRAMA line |

## Reading the Chart at a Glance

1. **Candle colors**: Cyan = bullish Hull, Magenta = bearish Hull
2. **Hull Band**: Neon glow band — trend direction
3. **Ghost Trail**: Step-line that trails price — your stop loss
4. **FVG Boxes**: Cyan/magenta zones extending right — price magnets
5. **VWAP Force Fields**: Orchid-colored bands — ±2σ/±3σ statistical extremes

## Quick Decision Framework

| Grade | Action |
|-------|--------|
| A+ / A | Full position, ride the trend with Ghost Trail |
| B | Half position, tight trail |
| C | No new entries, manage existing |
| D / F | DO NOT TRADE. Wait for regime change. |
