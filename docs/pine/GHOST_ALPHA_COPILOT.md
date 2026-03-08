# 👻 Ghost Alpha — AI Copilot Cheat Sheet

> **For Gemini Live, Sam, or any AI watching the TradingView screen.**
> Read the dashboard panel (top-right by default) and narrate market state.

---

## Dashboard Row Reference

| Row | Field | Values | What It Means | What To Say |
|-----|-------|--------|---------------|-------------|
| **REGIME** | Left: label | `BULL ▲` / `BEAR ▼` / `MODERATE` / `CHOP ═` | TRAMA trend quality. Strong = trending, Chop = no edge. | BULL/BEAR: "Strong trend in play." CHOP: "No clean trend — reduce size or sit out." |
| | Right: phase | `FRESH` / `YOUNG` / `MATURE` / `AGING` | How old the current Hull trend is (bars). | FRESH (<5): "New trend, highest conviction." AGING (50+): "Trend getting long in the tooth — tighten stops." |
| **TRAMA Δ** | Center: % | `AT VALUE` / `+2.1%` / `-3.4%` | Price distance from TRAMA (adaptive mean). | AT VALUE: "Price at fair value — good entry zone." ±3%+: "Extended — potential pullback/bounce." |
| | Right: % | `42%` | TRAMA tc value = regime quality score. | >25%: strong trend. <9%: chop. |
| **SQUEEZE** | Center: state | `COILED ◉` / `RELEASE ⚡` / `NORMAL` | ATR compression vs its 50-bar average. | COILED: "Volatility compressing — big move brewing." RELEASE: "Breakout happening NOW." |
| | Right: ratio | `0.68` | ATR / SMA(ATR,50). <0.75 = coiled. | Lower = tighter squeeze = bigger potential move. |
| **EXHAUST** | Center: state | `CLEAR` / `OVERBOUGHT` / `OVERSOLD` / `EXIT ▲` / `EXIT ▼` | Dual %R exhaustion (fast + slow periods agree). | OVERBOUGHT: "Buyers are getting tired." EXIT ▼: "Reversal signal — exhaustion confirmed." |
| | Right: value | `-64` | Fast %R value. Near 0 = overbought, near -100 = oversold. | |
| **STRUCT** | Center: state | `INTACT` / `BROKEN ▼` / `BROKEN ▲` | Whether price violated the last swing high/low. | INTACT: "Structure holding — trend valid." BROKEN: "Price broke key level — thesis invalidated." |
| | Right: price | `671.32` | Last swing low price (the critical support level). | "Support is at [price]. If we close below it, structure breaks." |
| **KELT** | Center: position | `INSIDE` / `LOWER ▽` / `UPPER △` | Where price is relative to Keltner Channel bands. | LOWER + uptrend: "Value buy zone." UPPER + downtrend: "Shorting zone." INSIDE: "Normal range." |
| | Right: MA status | `50>200 ✓` / `50<200 ✗` | Golden cross (SMA50 > SMA200) or death cross. | ✓: "Macro trend is bullish." ✗: "Macro trend is bearish — swim upstream carefully." |
| **IV/VOL** | Center: IV state | `LOW 🔋` / `MID` / `HIGH 🔥` | Synthetic IV percentile (options vol proxy). | LOW: "Vol is cheap — options are discounted." HIGH: "Vol is rich — consider selling premium." |
| | Right: RVOL | `1.23x` / `⚡2.8x` | Relative volume vs 20-bar average. | 1.5x+: "Volume confirming the move." ⚡2.5x+: "Volume SURGE — institutional activity." |
| **ADAPT** | Center+Right | `H34 T21` / `R14/55` | Auto-adapted periods. H=Hull, T=TRAMA, R=%R fast/slow. | "Auto-scaled to [timeframe]. Hull [X], TRAMA [Y], %R [fast]/[slow]." |
| **GRADE** | Center: grade | `A+` / `A` / `B` / `C` / `D` / `F` | Composite score across 10 axes (0-5+ scale). | A/A+: "High conviction setup — everything aligns." D/F: "No edge — stay flat or very careful." |
| | Right: direction | `LONG ▲` / `SHORT ▼` | Hull band direction. | "The indicator favors [LONG/SHORT] here." |

---

## On-Chart Signal Reference

| Signal | Shape | Color | Meaning | Action |
|--------|-------|-------|---------|--------|
| **BREAK ↓** | ▼ triangle above bar | Red | Price closed below last swing low | "Structure just broke bearish. If you're long, this is your exit signal." |
| **BREAK ↑** | ▲ triangle below bar | Cyan | Price closed above last swing high | "Structure cleared bullish. Resistance is gone." |
| **TIRED ↓** | ▼ triangle above bar | Coral | Both %R periods overbought & reversing | "Bulls are exhausted. Expect a pullback." |
| **TIRED ↑** | ▲ triangle below bar | Cyan | Both %R periods oversold & reversing | "Bears are exhausted. Bounce is likely." |
| **FIRE ⚡** | ◆ diamond above bar | Amber | ATR broke out of compression | "Squeeze just released. Volatility expanding." |
| **🎯** | Large ▲/▼ | Green | Confluence: 2+ signals agree simultaneously | "Multiple systems agree. High conviction." |

---

## Combined State Interpretation

### Best Long Setup (Grade A+)
- REGIME: BULL ▲ FRESH
- TRAMA Δ: AT VALUE (or slightly negative)
- KELT: LOWER ▽ (at lower band = value zone)
- STRUCT: INTACT
- 50>200 ✓
- RVOL: 1.5x+ confirming
- SQUEEZE: RELEASE ⚡ (or just fired)

**Say:** "This is the setup. Strong fresh trend, price pulled back to value, structure intact, MAs aligned, volume confirming. Grade A+."

### Warning Signs (Grade D/F)
- REGIME: CHOP ═
- TRAMA Δ: ±3%+ (extended)
- STRUCT: BROKEN
- EXHAUST: OVERBOUGHT/OVERSOLD
- RVOL: <1x (no volume)

**Say:** "No edge here. Choppy regime, structure broken, low volume. Sit this one out or reduce size significantly."

### Reversal Watch
- TIRED ↑ or TIRED ↓ just fired
- KELT: at outer band
- RVOL: high (confirming the exhaustion)
- Grade dropped from B→D

**Say:** "Exhaustion signal fired at the Keltner band with volume. The trend may be reversing. Tighten stops or look for the other direction."

---

## JSON Webhook Payload (for external systems)

When any signal fires, Ghost Alpha sends a JSON alert:

```json
{
  "ticker": "SPY",
  "tf": "5",
  "grade": "B",
  "signal": "BREAK_DOWN",
  "regime": "CHOP",
  "struct": "BROKEN_DN",
  "price": 671.30,
  "rvol": 1.45
}
```

**Signal values:** `BREAK_DOWN`, `BREAK_UP`, `EXHAUSTION_BEAR`, `EXHAUSTION_BULL`, `SQUEEZE_FIRE`, `CONFLUENCE_BULL`, `CONFLUENCE_BEAR`, `HULL_BULL`, `HULL_BEAR`

---

## Quick Decision Tree

```
Is GRADE A or A+?
  YES → Is direction matching your bias?
    YES → Enter with confidence, stops below swing low
    NO → Wait for flip or pass
  NO → Is GRADE B or C?
    YES → Reduced size, tighter stops
    NO → Grade D or F → DO NOT TRADE (or fade with caution)
```

---

*Built by Sam the Quant Ghost 👻 for mph1nance*
*Auto-adapts 5min → Daily. Zero external dependencies.*
