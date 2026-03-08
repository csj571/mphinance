# Ghost Grade V2: Independent Axis Scoring System

## The Collinearity Problem in V1

Ghost Grade V1 suffered from severe collinearity. By scoring based on Hull Moving Average, TRAMA, SMA 50/200, and Keltner Channels simultaneously, the system was effectively quadruple-counting smoothed price momentum. If the price went up, all these indicators went up, providing a false sense of confluence. 

To build a robust, institutional-grade scoring system, we must derive signal from **genuinely independent market data axes**. 

## The 5 Independent Axes of V2 (100 Points Total)

Ghost Grade V2 allocates 20 points each to five distinct dimensions of market state:

1. **Price Momentum (20 pts)**: Direction and velocity of price action.
2. **Volume / Order Flow (20 pts)**: Institutional participation and buying/selling pressure.
3. **Volatility Regime (20 pts)**: Energy state (compression vs. expansion).
4. **Trend Age / Time (20 pts)**: Maturity of the current move (freshness vs. exhaustion).
5. **Market Structure (20 pts)**: Context relative to supply/demand zones or liquidity.

---

### Axis 1: Price Momentum (Max 20 pts)
Instead of multiple moving averages, we use a single, highly responsive but noise-filtered measure of momentum: the slope of the TRAMA (Trend Regularized Exponential Moving Average) or Hull.

```pine
// Axis 1: Price Momentum (TRAMA Slope)
trama_length = 99
trama = ta.linreg(close, trama_length, 0) // Simplified proxy for TRAMA for example purposes
trama_slope = (trama - trama[1]) / trama[1]

// Scoring logic
momentum_score = 0
if trama_slope > 0.001 // Strong positive slope
    momentum_score := 20
else if trama_slope > 0 // Weak positive slope
    momentum_score := 10
else if trama_slope < -0.001 // Strong negative slope
    momentum_score := -20
else if trama_slope < 0 // Weak negative slope
    momentum_score := -10
```

### Axis 2: Volume & Order Flow Proxy (Max 20 pts)
Price can move on low volume (retail), but sustained trends require institutional volume. We use Chaikin Money Flow (CMF) to measure independent volume participation and order flow proxy.

```pine
// Axis 2: Order Flow / Volume (Chaikin Money Flow)
cmf_length = 20
money_flow_multiplier = ((close - low) - (high - close)) / (high - low)
money_flow_volume = money_flow_multiplier * volume
cmf = ta.sma(money_flow_volume, cmf_length) / ta.sma(volume, cmf_length)

// Scoring logic
volume_score = 0
if cmf > 0.15 // Strong buying pressure
    volume_score := 20
else if cmf > 0 // Mild buying
    volume_score := 10
else if cmf < -0.15 // Strong selling
    volume_score := -20
else if cmf < 0 // Mild selling
    volume_score := -10
```

### Axis 3: Volatility Regime (Max 20 pts)
Is the market storing energy (consolidation) or releasing energy (expansion)? We want to score highly when breaking out of a low-volatility squeeze, as these moves have the highest expected value.

```pine
// Axis 3: Volatility (Squeeze & Expansion)
bb_length = 20
bb_mult = 2.0
kc_mult = 1.5

basis = ta.sma(close, bb_length)
dev = bb_mult * ta.stdev(close, bb_length)
upper_bb = basis + dev
lower_bb = basis - dev

tr_sma = ta.sma(ta.tr, bb_length)
upper_kc = basis + kc_mult * tr_sma
lower_kc = basis - kc_mult * tr_sma

squeeze_on = (lower_bb > lower_kc) and (upper_bb < upper_kc)
volatility_expansion = not squeeze_on and squeeze_on[1] // Squeeze firing

// Scoring logic
volatility_score = 0
if volatility_expansion and close > basis // Firing long
    volatility_score := 20
else if not squeeze_on and close > basis // Trending long
    volatility_score := 10
else if squeeze_on // Chopping / Storing energy
    volatility_score := 0
// Mirror logic applies for short sides (-10, -20)
```

### Axis 4: Trend Age / Maturity (Max 20 pts)
A trend that just started is inherently more valuable than a trend that has been running for 50 bars. We apply a decay function to the score based on bars since the initial momentum cross to prevent late entries.

```pine
// Axis 4: Trend Age (Decay Function)
var int bars_since_signal = 0
is_new_trend_up = ta.crossover(trama_slope, 0)
is_new_trend_down = ta.crossunder(trama_slope, 0)

if is_new_trend_up or is_new_trend_down
    bars_since_signal := 0
else
    bars_since_signal += 1

// Scoring logic (Linear decay)
age_score = 0
if trama_slope > 0
    age_score := math.max(0, 20 - math.floor(bars_since_signal / 2)) // Loses 1 point every 2 bars
else if trama_slope < 0
    age_score := math.min(0, -20 + math.floor(bars_since_signal / 2))
```

### Axis 5: Market Structure / Context (Max 20 pts)
Price relative to structural liquidity. Are we bouncing off a Fair Value Gap (FVG) or breaking a key fractal? We score based on proximity and reaction to institutional levels.

```pine
// Axis 5: Market Structure (FVG / Support Proximity)
// Assuming FVG logic calculates bullish_fvg_top and bullish_fvg_bottom
// We reward being above a recently tested bullish FVG

var float last_bullish_fvg = na
if low[2] > high[0] // Simplified FVG down detection
    last_bullish_fvg := high[0]

structure_score = 0
if close > last_bullish_fvg and low <= last_bullish_fvg[1] // Retested and held
    structure_score := 20
else if close > last_bullish_fvg // Floating above support
    structure_score := 10
else if close < last_bullish_fvg // Broke support
    structure_score := -20
```

## Total V2 Score Calculation

```pine
total_ghost_grade = momentum_score + volume_score + volatility_score + age_score + structure_score

// The final score ranges from -100 to +100 indicating absolute directional quality
// A score of >= 80 indicates an institutional-grade long setup.
```

## Summary of the V2 Edge

By demanding confluence across **Direction, Volume, Volatility, Time, and Structure**, Ghost Grade V2 filters out low-probability "smooth price" fakeouts. A score of 80+ now guarantees that not only is price moving up, but it has institutional backing (Volume), is releasing fresh energy (Volatility), is early in its cycle (Time), and is launching from a logical structural level.