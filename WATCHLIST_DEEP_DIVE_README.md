# Stock Deep Dive Generator — Build Spec

A portable specification for building a single-ticker "deep dive" report
generator. Reading this and following the steps should be enough to
reproduce the artifact in any language/stack — no familiarity with the
host repo required.

**Goal.** Given a stock ticker (e.g. `AAPL`), produce three files:

- `deep_dive.md` — an LLM-authored narrative report.
- `deep_dive.json` — every input + computed metric, machine-readable.
- `deep_dive.html` — a styled, self-contained dashboard page that
  embeds the narrative plus visual "instrument panels" of the metrics.

## 1. Data sources

Everything below is fetched from **`yfinance`** (Python: `pip install
yfinance`). It wraps Yahoo Finance and is unofficial — treat every field
as nullable.

### 1.1 Price history
```python
import yfinance as yf
stock = yf.Ticker("AAPL")
df = stock.history(period="6mo")   # daily OHLCV, ~125 rows
```
Columns used: `Open`, `High`, `Low`, `Close`, `Volume`. **Six months is
the design constant** — long enough for SMA200 to start populating near
the end of the window, short enough that 52-week-style range labels
reflect the recent regime. If empty → skip the ticker.

### 1.2 Fundamentals / profile
```python
info = stock.info or {}
```
Fields consumed (group → keys):

| Group | Keys |
|---|---|
| Profile | `longName`, `shortName`, `longBusinessSummary`, `website`, `fullTimeEmployees`, `exchange`, `sector`, `industry`, `floatShares`, `marketCap`, `beta` |
| Valuation | `trailingPE`, `forwardPE`, `priceToSalesTrailing12Months`, `priceToBook`, `pegRatio`, `enterpriseToEbitda`, `enterpriseToRevenue`, `freeCashflow`, `trailingEps`, `bookValue` |
| Growth | `revenueGrowth`, `earningsGrowth`, `earningsQuarterlyGrowth`, `revenuePerShare` |
| Profitability | `grossMargins`, `operatingMargins`, `profitMargins`, `returnOnEquity`, `returnOnAssets` |
| Health | `currentRatio`, `debtToEquity`, `totalDebt`, `totalCash`, `operatingCashflow` |
| Dividends | `dividendRate`, `dividendYield`, `payoutRatio`, `exDividendDate` (unix seconds) |
| Analyst | `targetLowPrice`, `targetMedianPrice`, `targetHighPrice`, `targetMeanPrice`, `recommendationKey`, `numberOfAnalystOpinions` |

**Dividend yield gotcha:** `yfinance` returns it sometimes as a decimal
(0.0091 = 0.91%) and sometimes already as a percent (0.91). Prefer
deriving it yourself: `dividendRate / price * 100`. If you must fall
back to `dividendYield`, normalize: `value < 1 → multiply by 100`.

**Margins/growth gotcha:** `grossMargins`, `revenueGrowth`, etc. are
decimals (0.42 = 42%). Multiply by 100 before display.

### 1.3 Options chain (front-month only)
```python
expiries = stock.options                # list of "YYYY-MM-DD"
chain = stock.option_chain(expiries[0]) # nearest expiry
calls = chain.calls                     # DataFrame with strike, impliedVolatility, ...
puts  = chain.puts
```

### 1.4 TradingView consensus (optional but useful)
```python
# pip install tradingview-ta
from tradingview_ta import TA_Handler, Interval

# Map yfinance's info["exchange"] code → TradingView exchange string
EXCHANGE_MAP = {"NMS": "NASDAQ", "NYQ": "NYSE", "NGM": "NASDAQ",
                "ASE": "AMEX", "PCX": "ARCA"}
tv = TA_Handler(
    symbol=ticker, screener="america",
    exchange=EXCHANGE_MAP.get(info.get("exchange"), "NASDAQ"),
    interval=Interval.INTERVAL_1_DAY,
).get_analysis()
tv_rec = tv.summary.get("RECOMMENDATION", "N/A")   # "STRONG_BUY" / "BUY" / "NEUTRAL" / ...
```
Wrap in try/except; tolerate `"N/A"`.

## 2. Computed indicators

Every formula operates on the 6-month daily series. `close`, `high`,
`low`, `volume` below refer to those columns.

### 2.1 Moving averages
```python
sma = lambda s, n: s.rolling(n).mean()
ema = lambda s, n: s.ewm(span=n, adjust=False).mean()
```
Compute and snapshot the last value of each:
- **EMAs:** 8, 21, 34, 55, 89
- **SMAs:** 20, 50, 100, 200

**EMA Stack label** (using last bar's EMAs `e8…e89`):
- `e8 > e21 > e34 > e55 > e89` → `"FULL BULLISH"`
- `e8 > e21 > e34` (but not fully stacked) → `"PARTIAL BULLISH"`
- `e89 > e55 > e34 > e21 > e8` → `"FULL BEARISH"`
- anything else → `"TANGLED"` (or `"UNKNOWN"` if any are NaN)

**Three trend timeframes** (each: `"↑ Bullish"` / `"↓ Bearish"` / `"N/A"`):
- Short: `EMA8 > EMA21`
- Mid:   `EMA21 > SMA50`
- Long:  `SMA50 > SMA200`

**Crossover label:** `"Golden Cross"` if `SMA50 > SMA200` else `"Death Cross"`.

### 2.2 RSI(14)
```python
def rsi(s, n=14):
    d = s.diff()
    gain = d.where(d > 0, 0).rolling(n).mean()
    loss = (-d.where(d < 0, 0)).rolling(n).mean()
    return 100 - 100 / (1 + gain / loss)
```
Display bands: `≤30` oversold (green/positive), `≥70` overbought
(red/negative), else neutral.

### 2.3 MACD (12, 26, 9)
```python
ema_fast = ema(close, 12)
ema_slow = ema(close, 26)
macd_line   = ema_fast - ema_slow
macd_signal = ema(macd_line, 9)
macd_hist   = macd_line - macd_signal
```

### 2.4 Stochastic %K(14) / %D(3)
Note the asymmetry — keep it:
```python
low14, high14 = low.rolling(14).min(), high.rolling(14).max()
stoch_k = (close.iloc[-1] - low14.iloc[-1]) / (high14.iloc[-1] - low14.iloc[-1]) * 100
stoch_d = (((close - low14) / (high14 - low14) * 100)
           .rolling(3).mean().iloc[-1])
```
Guard the `%K` denominator (return 50 if `high14 == low14`).

### 2.5 ATR(14) and ATR(20)
```python
tr = pd.concat([
    high - low,
    (high - close.shift()).abs(),
    (low  - close.shift()).abs(),
], axis=1).max(axis=1)
atr14 = tr.rolling(14).mean().iloc[-1]
atr20 = tr.rolling(20).mean().iloc[-1]
```

### 2.6 ADX(14) (simplified)
```python
dm_plus  = high.diff()
dm_minus = -low.diff()
dm_plus  = dm_plus.where((dm_plus  > dm_minus) & (dm_plus  > 0), 0)
dm_minus = dm_minus.where((dm_minus > dm_plus ) & (dm_minus > 0), 0)
atr14_s  = tr.rolling(14).mean()
di_plus  = 100 * dm_plus.rolling(14).mean()  / atr14_s
di_minus = 100 * dm_minus.rolling(14).mean() / atr14_s
dx       = 100 * (di_plus - di_minus).abs() / (di_plus + di_minus)
adx      = dx.rolling(14).mean().iloc[-1]
```

### 2.7 Pivot Points (classic floor-trader)
Use the **previous** day's bar (`iloc[-2]`), not the current one:
```python
ph, pl, pc = high.iloc[-2], low.iloc[-2], close.iloc[-2]
pp = (ph + pl + pc) / 3
r1, s1 = 2*pp - pl, 2*pp - ph
r2, s2 = pp + (ph - pl), pp - (ph - pl)
```

### 2.8 52-week range + position
```python
w52_low  = low.min()                  # using the 6mo window in this build
w52_high = high.max()
w52_pos  = (price - w52_low) / (w52_high - w52_low) * 100   # 0..100
```

### 2.9 Fibonacci retracements (on the same range)
```python
rng = w52_high - w52_low
fib = {
    0.236: w52_high - rng*0.236,
    0.382: w52_high - rng*0.382,
    0.500: w52_high - rng*0.500,
    0.618: w52_high - rng*0.618,
}
```

### 2.10 Keltner Channels (20, 2·ATR20)
```python
kelt_mid   = sma(close, 20).iloc[-1]
kelt_upper = kelt_mid + 2 * atr20
kelt_lower = kelt_mid - 2 * atr20
```

### 2.11 30-day Historical Volatility (annualized %)
```python
log_ret = np.log(close / close.shift(1)).dropna()
hv30    = log_ret.rolling(30).std().iloc[-1] * np.sqrt(252) * 100
```

### 2.12 Relative volume (20-day)
```python
rel_vol = volume.iloc[-1] / volume.rolling(20).mean().iloc[-1]
```

### 2.13 ATM IV, IV Rank, IV Percentile (from front-month chain)
```python
# Strike-distance-weighted average IV of the 5 calls closest to spot.
atm_band = calls.iloc[(calls["strike"] - price).abs().argsort()[:5]]
weights  = 1.0 / (1.0 + (atm_band["strike"] - price).abs() / price)
atm_iv   = (atm_band["impliedVolatility"] * weights).sum() / weights.sum() * 100

# Compare ATM IV against the full chain (calls + puts) of IVs.
all_ivs  = pd.concat([calls["impliedVolatility"], puts["impliedVolatility"]]).dropna() * 100
iv_rank       = (atm_iv - all_ivs.min()) / (all_ivs.max() - all_ivs.min()) * 100
iv_percentile = (all_ivs <= atm_iv).sum() / len(all_ivs) * 100
```
Skip the block on any exception — options data is missing for many tickers.

## 3. Valuation model (Graham + Lynch + Analyst blend)

Three independent fair-value estimates, averaged when available.

```python
eps          = info.get("trailingEps")   or 0
bvps         = info.get("bookValue")     or 0
rev_growth   = info.get("revenueGrowth") or 0       # decimal
analyst_tgt  = info.get("targetMeanPrice") or 0

graham = sqrt(22.5 * eps * bvps)   if (eps > 0 and bvps > 0) else 0
lynch  = eps * (rev_growth * 100)  if (eps > 0 and rev_growth > 0) else 0

if eps > 0:                                  # profitable
    candidates = [v for v in (graham, lynch, analyst_tgt) if v > 0]
    fair_value = mean(candidates) if candidates else 0
    method = "BLENDED (Graham+Lynch+Analyst)"  # build label from which contributed
else:                                        # unprofitable → analyst only
    fair_value = analyst_tgt if analyst_tgt > 0 else 0
    method = "ANALYST CONSENSUS"

gap_pct = (fair_value - price) / price * 100  if fair_value > 0 else 0
status  = "UNDERVALUED" if gap_pct > 20 \
     else "OVERVALUED"  if gap_pct < -20 \
     else "FAIR VALUE"
```
Report tuple: `{status, gap_pct, target_price: fair_value, method}`.

## 4. Composite scores (0–100)

Each is clamped to `[0, 100]`, integer-rounded, `None` if no inputs were
available. Partial inputs are fine — average over what exists.

```python
def clamp(x, lo=0, hi=100): return max(lo, min(hi, x))
def avg(xs):                return sum(xs)/len(xs) if xs else None

# Value: lower P/E + lower P/B + lower PEG → higher score
val = []
if 0 < pe  < 100: val.append(max(0, 100 - pe  * 2))
if 0 < pb  < 50 : val.append(max(0, 100 - pb  * 10))
if 0 < peg < 10 : val.append(max(0, 100 - peg * 20))
value_score = clamp(avg(val)) if val else None

# Growth: revenue + earnings growth (decimals)
gro = []
if rev_growth     is not None: gro.append(clamp(50 + rev_growth     * 200))
if earnings_growth is not None: gro.append(clamp(50 + earnings_growth * 100))
growth_score = clamp(avg(gro)) if gro else None

# Quality: margins + ROE (decimals, only counted if > 0)
qua = []
if gross_margins    and gross_margins    > 0: qua.append(min(100, gross_margins    * 120))
if operating_margins and operating_margins > 0: qua.append(min(100, operating_margins * 200))
if return_on_equity  and return_on_equity  > 0: qua.append(min(100, return_on_equity  * 200))
quality_score = clamp(avg(qua)) if qua else None

# Sentiment: analyst recommendationKey → fixed map
SENT = {"STRONG_BUY":90, "BUY":75, "HOLD":50, "SELL":25, "STRONG_SELL":10}
sentiment_score = SENT.get((rec_key or "").upper())   # None if unknown
```

UI bands when rendered: `≥65` green, `40–64` amber, `<40` red.

## 5. The narrative (LLM step)

Pick any modern chat model (the reference uses Gemini, but the prompt is
provider-agnostic). Feed it the full computed payload as plain text and
pin a strict markdown structure.

### 5.1 System persona / role
> You are a sharp, witty quantitative analyst who writes deep-dive stock
> reports retail traders love.

### 5.2 Prompt template
Interpolate ticker + every metric below. **Do not** hand the model JSON
— a labeled bullet list reads better.

```
Write a FULL deep-dive report for {TICKER} using the data below.
Use this exact structure:

## [{TICKER}] Deep Dive: [Catchy thesis title]
**Date:** {YYYY-MM-DD}
**Price:** ~${price} | **Verdict:** [your verdict]

[1-2 sentence hook]

### The Core Thesis
[Market view vs reality. 2-3 paragraphs.]

### The Numbers You Need
[Revenue, margins, growth rates. Use the fundamentals data.]

### The Bull Case
[3-4 catalysts with specifics]

### The Bear Case: Risks
[2-3 real risks]

### The Technicals
[EMAs, RSI, support/resistance, pivots — reference specific levels]

### Trading Playbook
**Scenario A — The Breakout (Bullish):**
**Scenario B — The Dip Buy (Preferred):**
**Scenario C — Trend Failure (Hedge):**

### Final Verdict
[One-liner + price target]

---

DATA:
- Price: ${price}, Change: {change_pct}%
- Market Cap: {market_cap}, Beta: {beta}
- 52W Range: {w52_low} - {w52_high}
- Sector: {sector}, Industry: {industry}
- Revenue Growth: {rev_growth}%, Profit Margin: {profit_margin}%
- P/E: {pe}, Forward P/E: {fwd_pe}
- EMA Stack: {ema_stack} (8: ${ema_8}, 21: ${ema_21}, 34: ${ema_34})
- SMA 50: ${sma_50}, SMA 200: ${sma_200}
- Trend: {trend} ({crossover})
- RSI(14): {rsi}, ADX: {adx}
- Pivots: R2=${r2}, R1=${r1}, PP=${pivot}, S1=${s1}, S2=${s2}
- ATR: {atr}, Rel Vol: {rel_vol}x
- Analyst Target: ${analyst_target}
- TradingView: {tv_rec}
- Valuation: {val_status} (Gap: {val_gap}%), Target: ${val_target}

Write the full report now. Be direct, opinionated, data-driven.
Use markdown formatting. Reference specific price levels and numbers.
No generic filler. Sign off with a short signature line.
```

### 5.3 Fallback (no LLM available)
If the LLM call fails or no API key is set, emit a deterministic
template so the report file still exists:

```markdown
## [TICKER] Deep Dive
**Date:** YYYY-MM-DD | **Price:** $X (±Y%)

### Market Snapshot
| Metric | Value |
|--------|-------|
| Market Cap | ... |
| Sector | ... |
| Beta | ... |
| 52W Range | ... |
| Analyst Target | ... |
| TradingView | ... |

### Technicals
- EMA Stack, Trend/Crossover, EMA/SMA values, RSI, ADX, Pivots, ATR, RVol

### Valuation
- Status (Gap %), Target

### Fundamentals
- Revenue Growth, Profit Margin, P/E, Forward P/E
```

## 6. Output artifacts

Write all three under a per-ticker directory (e.g.
`out/{TICKER}/deep_dive.{md,json,html}`).

### 6.1 `deep_dive.md`
Exactly the LLM output (or the fallback template). No post-processing.

### 6.2 `deep_dive.json`
Single flat object containing every input and derived metric. Suggested
key groups (use snake_case throughout):

```
quote:    date, price, change_pct, market_cap, beta, range_52w,
          w52_low, w52_high, w52_pos, sector, industry
trend:    ema_8, ema_21, ema_34, ema_55, ema_89,
          sma_20, sma_50, sma_100, sma_200,
          ema_stack, trend, crossover,
          trend_short, trend_med, trend_long
momentum: rsi, adx, stoch_k, stoch_d, macd, macd_signal, macd_hist
vol:      atr, rel_vol, iv, hv, iv_rank, iv_percentile
levels:   pivot, r1, r2, s1, s2,
          fib_236, fib_382, fib_500, fib_618,
          kelt_upper, kelt_mid, kelt_lower
val:      analyst_target, tv_rec,
          val_status, val_gap, val_target,
          pe, fwd_pe, ps_ratio, pb_ratio, peg_ratio,
          ev_ebitda, ev_revenue, price_to_fcf
growth:   rev_growth, earnings_growth, earnings_q_growth, rev_per_share
profit:   gross_margin, operating_margin, net_margin, roe, roa
health:   current_ratio, debt_equity, total_debt, total_cash,
          fcf, operating_cf
div:      div_yield, div_rate, payout_ratio, ex_div_date
analyst:  target_low, target_median, target_high, rec_key, num_analysts
scores:   value_score, growth_score, quality_score, sentiment_score
profile:  company_name, description (≤3 sentences), website, employees,
          exchange, float_shares
```

Use a number-formatting helper for human-readable strings like
`market_cap`: `>=1e9 → "$X.XXB"`, `>=1e6 → "$X.XXM"`, else `"$X,XXX"`.
Use a `safe(val, decimals=2)` helper that returns `None` for NaN/Inf so
the JSON stays clean.

### 6.3 `deep_dive.html`
One self-contained dark-terminal-themed page. No JS framework, no build
step — all CSS inlined, fonts from Google. Color tokens:

| Token | Hex | Use |
|---|---|---|
| positive | `#00ff41` | bullish, healthy margins, undervalued |
| negative | `#ff3e3e` | bearish, debt, overvalued |
| neutral  | `#ffb000` | warnings, mid-band scores |
| accent   | `#00f3ff` | callouts, links |
| bg       | `#050505` | page background |
| dim      | `#555`    | secondary labels |

Fonts: `Share Tech Mono` (headings/labels), `JetBrains Mono` (body).

Page structure (top to bottom):

1. **Header bar** — `{TICKER} DEEP.DIVE`, `sector · industry · date`,
   right side: price + `change_pct` colored ±.
2. **Narrative block** — render the markdown body inline. A regex-based
   shim is sufficient (no real markdown parser needed) as long as the
   LLM stays inside: headings (`##`, `###`), `**bold**`, `*italic*`,
   `-`/`*`/numbered lists, `---` → `<hr>`, pipe rows → tables.
3. **Technical Gearbox panel** (cyan accent border):
   - Vol row (4 cards): IV, HV30, IV Rank, IV Percentile.
   - Trend panel: three arrows (Short / Mid / Long) + EMA Stack label +
     TradingView rec + crossover.
   - Moving Averages panel: SMA 20/50/100/200 each with `(price − ma)/ma`
     as a colored `%`, then EMA 8/21/34/55/89.
   - Oscillators row (4 cards): RSI (banded), Stoch %K/%D, MACD hist,
     ADX.
   - 52-Week Range bar: linear gradient red→amber→green, white dot at
     `w52_pos` percent, low/current/high labels above.
   - Fib panel + Keltner/Pivots panel side-by-side. Pivots shown as
     `R2 · R1 · PP · S1 · S2` sub-line.
4. **Fundamental Dashboard panel** (amber accent border):
   - Profile cards row: company name, market cap, employees, exchange.
   - Description blurb (≤3 sentences) + website link.
   - **Scores Overview**: 4 large numeric cards (Value, Growth, Quality,
     Sentiment) banded by `≥65/40–64/<40`.
   - Valuation grid (6 cards): P/E, Fwd P/E, P/S, P/B, EV/EBITDA, PEG +
     sub-line `EV/Revenue · P/FCF`.
   - Growth + Profitability side-by-side as 2-col labeled rows.
   - Financial Health grid: Current Ratio, D/E, Debt, Cash, FCF, Op CF.
   - Dividends + Analyst Estimates side-by-side; Analyst panel includes
     a low→high horizontal bar with a dot at the current price.
5. **Footer** — generation timestamp.

Optional 6th panel — **options edge** — if you compute extras like
volatility risk premium (VRP = IV / HV) and an expected move
(`price × IV × sqrt(DTE/365)`), add a 4-card row + a top-strikes table
(Type, Strike, Delta, Theta, Mid). Skip the whole block if you don't.

## 7. Reference pseudocode (one ticker, end-to-end)

```python
def deep_dive(ticker: str) -> dict:
    stock = yf.Ticker(ticker)
    df    = stock.history(period="6mo")
    if df.empty: return None
    close, high, low, vol = df.Close, df.High, df.Low, df.Volume
    info  = stock.info or {}
    price = float(close.iloc[-1])

    # technicals (§2)
    emas  = {n: ema(close, n).iloc[-1] for n in (8,21,34,55,89)}
    smas  = {n: sma(close, n).iloc[-1] for n in (20,50,100,200)}
    rsi_v = rsi(close).iloc[-1]
    macd_line, macd_sig, macd_hist = macd(close)
    # ... stoch, atr14/20, adx, pivots, fibs, keltner, hv30, rel_vol

    # options (§1.3, §2.13) — best effort
    atm_iv = iv_rank = iv_pct = None
    try: atm_iv, iv_rank, iv_pct = compute_iv_stats(stock, price)
    except Exception: pass

    # overlays
    tv_rec     = tradingview_rec(ticker, info.get("exchange"))
    valuation  = intrinsic_value(info, price)         # §3
    scores     = composite_scores(info)               # §4

    # assemble the flat dict per §6.2
    data = {...}

    # narrative (§5) with fallback
    md = llm_deep_dive(ticker, data) or fallback_template(ticker, data)

    write(f"out/{ticker}/deep_dive.md",   md)
    write(f"out/{ticker}/deep_dive.json", json.dumps(data, indent=2, default=str))
    write(f"out/{ticker}/deep_dive.html", render_html(ticker, md, data))
    return data
```

## 8. Reproduction gotchas

- **`yfinance.info` is unstable.** Field names and units shift between
  releases (dividend yield being the loudest example). Wrap every
  access, normalize at the edge, never assume presence.
- **6-month window is load-bearing.** Stretching it breaks SMA200
  availability, range labels, and Fib bases. Either keep 6mo or audit
  every consumer.
- **Pivots use the previous day's H/L/C.** Reading `iloc[-1]` instead
  of `iloc[-2]` is the most common porting bug.
- **Stochastic asymmetry.** `%K` is a single-bar snapshot using the
  current `close`; `%D` is the 3-bar SMA of a full %K *series*. Replicate
  exactly or numbers won't match other tools.
- **Composite scores accept partial inputs.** Missing PEG shouldn't null
  the value score — average over what exists, only return `None` when
  *every* term is missing.
- **HTML render is intentionally dumb.** A regex shim is enough as long
  as the LLM stays inside the structure pinned by the prompt. If you
  switch to a real markdown parser you can drop the prompt constraints.
- **Decimals vs percents.** `info["grossMargins"] = 0.42` means 42%.
  `info["revenueGrowth"] = 0.08` means 8%. Multiply by 100 before
  display, but **not** before feeding the composite-score formulas
  (they're written against decimals).
- **Rate limits.** `yfinance` will throttle batch runs; sequential
  fetches with per-ticker try/except (skip-and-continue, never abort)
  is the safe pattern.

## 9. Minimal dependency list

```
yfinance        # quotes, fundamentals, options
pandas, numpy   # series math
tradingview-ta  # optional: consensus rec
<your llm sdk>  # e.g. google-genai, openai, anthropic
```

That's the entire surface area. No internal libraries, no framework,
no database. One Python file + one HTML template renderer = the whole
generator.
