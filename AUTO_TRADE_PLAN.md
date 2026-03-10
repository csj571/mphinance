> ## 🚀 DEPLOY TO VENUS (port 8100)
>
> ```bash
> rsync -avz --exclude='.git' --exclude='AlexTrading-WebApp' --exclude='alpha-reflex' --exclude='__pycache__' --exclude='node_modules' --exclude='.env' --exclude='venv' --exclude='*.pyc' --exclude='_archive' /home/sam/Antigravity/alpha-momentum/ venus:/home/mph/alpha-momentum/
> ssh venus "cd /home/mph/alpha-momentum && docker compose build --no-cache api && docker compose up -d api"
> ```

# 🤖 AUTO-TRADING IMPLEMENTATION PLAN v2.0

**Date:** 2026-03-06
**Author:** Antigravity (refined from NotebookLM spec + existing v1 plan)
**Status:** PHASE 1 COMPLETE · PHASE 2–4 PLANNED

---

## Design Philosophy: "Glass Box" Execution

Every calculation is traceable. The system must never be a black box — all scores, filters, and signals are logged with the formula that produced them. This applies to equity picks, options scoring, and risk metrics. The Python backend writes values alongside the formula used (e.g., `score = (1 - |Δ|) × (250 / (DTE+5)) × (bid/strike)`) so Michael can audit any trade decision.

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│                    MARKET DATA LAYER                     │
│  Tradier (live quotes, chains)  ·  yfinance (history)    │
│  Future: Databento (tick data for 512t/1160t intervals)  │
└─────────────────────┬────────────────────────────────────┘
                      │
┌─────────────────────▼────────────────────────────────────┐
│                   PROCESSING LAYER                       │
│  DataEngine · AlphaScanner · VoPR Engine                 │
│  Pandas/NumPy vectorized pipelines                       │
└─────────────────────┬────────────────────────────────────┘
                      │
┌─────────────────────▼────────────────────────────────────┐
│                   STRATEGY ENGINE                        │
│  EMA Crossover · Supertrend · VoPR CSP/Wheel · 0DTE*    │
│  Modular strategy files, independent backtesting         │
└─────────────────────┬────────────────────────────────────┘
                      │
┌─────────────────────▼────────────────────────────────────┐
│                EXECUTION & BROKER LAYER                  │
│  Tradier (active) · Schwab/Alpaca (future)               │
│  TradierService · smart_buyer.py · MCP tools             │
└─────────────────────┬────────────────────────────────────┘
                      │
┌─────────────────────▼────────────────────────────────────┐
│                    DATA LAKE                             │
│  Raw: trade_log.json · signals_cache.json · OHLCV       │
│  Analytics: equity_curve · risk_metrics · sector_exposure│
└──────────────────────────────────────────────────────────┘
```

---

## Phase 1: Equity Smart Buyer ✅ BUILT

**Status:** Built, needs deployment + morning validation.

### What Exists

| Component | File | Status |
|-----------|------|--------|
| Smart buyer script | `scripts/smart_buyer.py` | ✅ |
| Market clock endpoint | `/api/market/clock` | ✅ |
| Auto-trade run endpoint | `/api/auto-trade/run` | ✅ |
| Trade journal viewer | `/api/auto-trade/log` | ✅ |
| MCP tools (buy, portfolio, picks, clock) | `tradier-agent/` | ✅ |
| Trade journal | `data/trade_log.json` | ✅ |

### Rules (Equity)

- **Max position:** $50 · **Max concurrent:** 2 · **Buffer:** $25 buying power min
- **Grade filter:** A or B only (from daily picks pipeline)
- **Order type:** Limit at bid price · **Duration:** Day
- **Entry only** — no auto-exits, Michael manages sells
- **Default: DRY RUN** — requires explicit `--live` or `dry_run=false`

### Flow

```
1. GET /api/market/clock         → abort if not "open"
2. GET /api/picks/today          → filter grade A/B
3. GET /api/portfolio/tradier    → buying power + held symbols
4. For each eligible pick:
   a. GET /api/quote/{symbol}    → price, bid
   b. Calculate qty = floor($50 / price)
   c. POST /api/trade/preview    → verify
   d. POST /api/trade/execute    → place order (if not dry_run)
5. Append to data/trade_log.json
```

### Deploy & Verify Sequence

```bash
# 1. Rsync + rebuild
rsync -avz --exclude='.git' --exclude='AlexTrading-WebApp' --exclude='alpha-reflex' --exclude='__pycache__' --exclude='node_modules' --exclude='.env' --exclude='venv' --exclude='*.pyc' --exclude='_archive' /home/sam/Antigravity/alpha-momentum/ venus:/home/mph/alpha-momentum/
ssh venus "cd /home/mph/alpha-momentum && docker compose build --no-cache api && docker compose up -d api"

# 2. Health check
curl -s http://192.168.2.172:8100/api/health | python3 -m json.tool

# 3. Market clock (after 8:30 AM CST)
curl -s http://192.168.2.172:8100/api/market/clock | python3 -m json.tool

# 4. Dry run
curl -s -X POST "http://192.168.2.172:8100/api/auto-trade/run?dry_run=true" | python3 -m json.tool

# 5. Go live
curl -s -X POST "http://192.168.2.172:8100/api/auto-trade/run?dry_run=false" | python3 -m json.tool

# 6. Check log
curl -s http://192.168.2.172:8100/api/auto-trade/log | python3 -m json.tool
```

---

## Phase 2: Options Wheel via VoPR 🔲 PLANNED

Leverage the existing VoPR engine (`vopr/`) to sell cash-secured puts (CSPs) on preferred assets. Upon assignment, transition to covered calls (CCs). This is the core income strategy.

### What Already Exists for This

| Component | File | Notes |
|-----------|------|-------|
| 4-model Composite RV | `vopr/volatility_models.py` | Parkinson, GK, RS, CC weights (0.15/0.25/0.25/0.35) |
| Black-Scholes Greeks | `vopr/greeks.py` | Delta, Theta, Gamma, Vega |
| Options chain filters | `vopr/filters.py` | Delta range, OI, volume, liquidity gates |
| Full scanner orchestrator | `vopr/scanner.py` | `run_scan()` + `run_auto_scan()` |
| Config dataclass | `vopr/config.py` | All knobs: delta 0.10–0.25, OI ≥ 500, vol ≥ 100 |
| Tradier chain fetcher | `vopr/tradier_client.py` | Options chain + expirations via Tradier API |
| VoPR API endpoints | `/api/vopr/auto-scan`, `/api/vopr/batch-scan` | Live in API |

### What Needs Building

#### A. Option Scoring Formula

From the NotebookLM spec — annualized return adjusted for assignment probability:

```
score = (1 - |Δ|) × (250 / (DTE + 5)) × (bid / strike)
```

- **`(1 - |Δ|)`** — Higher score for lower delta (higher OTM probability)
- **`(250 / (DTE + 5))`** — Annualization factor, favoring shorter DTE
- **`(bid / strike)`** — Yield component

> **Implementation:** Add `score_option()` function to `vopr/filters.py` that computes this alongside the existing VoPR grade. Keep both scores — VoPR grade is the qualitative assessment, this formula is the quantitative rank.

#### B. Wheel State Machine

```
┌─────────────┐    assigned    ┌──────────────┐    called away    ┌──────────┐
│   SELL CSP   │──────────────→│   SELL CC    │───────────────────→│  CASH    │
│  (puts)      │               │ (calls on    │                   │ (restart)│
└──────┬───────┘               │  held shares)│                   └────┬─────┘
       │ expires OTM           └──────┬───────┘                        │
       └───────────────────────────────┘  expires OTM                  │
                                                                       │
       ◄──────────────────── cycle repeats ───────────────────────────┘
```

**Constraint:** 1 contract per symbol max (simplifies capital allocation).

**Roll Logic:** If an expiring put is near the strike (within 1% ITM), evaluate roll vs. assignment:

- If `yield_on_roll > YIELD_MIN` and `new_delta <= max_delta`: Roll
- Otherwise: Accept assignment → transition to CC selling

#### C. CSP/CC Filtering Criteria (refined from NotebookLM)

| Filter | CSP (Puts) | CC (Calls) |
|--------|------------|------------|
| Delta range | -0.42 to -0.18 | 0.18 to 0.42 |
| Min Open Interest | > 200 | > 200 |
| Yield | Within `YIELD_MIN` – `YIELD_MAX` | Within `YIELD_MIN` – `YIELD_MAX` |
| Symbols | From `data/wheel_symbols.txt` | Held positions only |

> **Note:** VoPR's current config uses delta 0.10–0.25 for premium selling. The Wheel strategy uses a wider delta band (0.18–0.42) because it's *willing to be assigned*. These are two different use cases — premium farming vs. entry-via-assignment.

#### D. New Files

```
scripts/wheel_runner.py          # Wheel state machine + execution
data/wheel_state.json            # Position state (CSP, CC, CASH per symbol)
data/wheel_symbols.txt           # Approved wheel candidates
```

#### E. New API Endpoints

```
POST /api/auto-trade/wheel       # Run wheel logic (dry_run default)
GET  /api/auto-trade/wheel-state # View current wheel positions + state
```

---

## Phase 3: Strategy Modules 🔲 PLANNED

Modular strategy files that can run independently for backtesting and live signals. Each outputs to the unified signal format (`TradeSignal` from `core/signals.py`).

### 3A. EMA Crossover Strategy

**Already partly built** in `scanners/alpha_engine.py` — has EMA 8/21/34/55/89, RSI, ATR, and a scoring system.

**Refinement from NotebookLM spec:**

| Parameter | Current | Spec Target |
|-----------|---------|-------------|
| Fast/Slow EMA | 8/21 | 9/21 and 8/21 (configurable) |
| Entry signal | EMA8 > EMA21 + proximity | Crossover event (not just state) |
| Exit signal | None (manual) | Reverse crossover OR 2x delta stop-loss |
| Stop-loss | 2 × ATR from close | 2 × initial delta (entry price – stop) |

**New file:** `strategies/ema_strategy.py`

### 3B. Supertrend Reversal Strategy

**Not yet built.** This is a new module.

**Spec:**

- ATR-based dynamic band (ThinkScript parity)
- Signal on bullish/bearish reversal candle breaking the Supertrend line
- Reversal candle detection (not just price crossing the line)

**New file:** `strategies/supertrend_strategy.py`

### 3C. 0DTE SPX Options ⚠️ ASPIRATIONAL

**Requires:** Futures-capable broker (Schwab or Alpaca — not Tradier). Parking this for now.

- Instruments: /MES, /ES futures or SPX index options
- Auto-close before 3:30 PM ET
- Intraday execution on same-day expirations

> **Dependency:** Schwab OAuth 2.0 integration or Alpaca futures. Neither is wired yet.

---

## Phase 4: Risk Management & Institutional Analytics 🔲 PLANNED

### A. Position Sizing Rules

| Rule | Value |
|------|-------|
| Max buying power per trade | 10% |
| Stop-loss (equity) | 2 × initial delta OR 50% premium (options) |
| Buying power buffer | $25 minimum reserved |
| Max concurrent positions | 2 (equity) · 1 contract/symbol (options) |

### B. KPI Dashboard (Equity Curve Analytics)

Calculate on `data/trade_log.json` as the system accumulates trade history:

| KPI | Formula | Notes |
|-----|---------|-------|
| **Sharpe Ratio** | `mean(daily_returns) / std(daily_returns) × √252` | Annualized |
| **Sortino Ratio** | `mean(daily_returns) / std(downside_returns) × √252` | Downside only |
| **VaR (95%)** | `percentile(daily_returns, 5)` | 90-day lookback |
| **VaR (99%)** | `percentile(daily_returns, 1)` | 90-day lookback |
| **Beta to SPY** | `cov(portfolio, SPY) / var(SPY)` | Rolling 90-day |
| **Max Drawdown** | `max(peak - trough) / peak` | Since inception |

> **Implementation:** `scripts/analytics.py` — reads `trade_log.json` + yfinance price history, outputs to `data/equity_curve.json`.

### C. Trade Log Schema (enhanced)

Every entry must include:

```json
{
  "trade_id": "auto-001",
  "timestamp": "2026-03-06T14:35:00Z",
  "symbol": "NVDA",
  "side": "buy",
  "quantity": 2,
  "price": 24.50,
  "order_id": "tradier-12345",
  "net_cost": 49.00,
  "commission": 0.00,
  "cash_balance_after": 51.00,
  "pick_rank": 1,
  "pick_grade": "A",
  "pick_score": 87,
  "source": "auto-buy",
  "strategy": "momentum_equity",
  "dry_run": false,
  "scoring_formula": "score = conviction(0.87) × grade_weight(1.0)"
}
```

### D. Execution Scheduler (Venus cron)

| Time (ET) | Action | Command |
|-----------|--------|---------|
| 10:00 AM | Trend confirmation + equity picks | `curl POST /api/auto-trade/run?dry_run=false` |
| 1:00 PM | Mid-day portfolio sync | `curl GET /api/portfolio/tradier` (log only) |
| 3:30 PM | Roll-or-rinse expiring options | `curl POST /api/auto-trade/wheel` |
| 4:00 PM | End-of-day backup | Archive `trade_log.json` |

**Cron setup (Venus):**

```bash
# Equity auto-buy at 10:00 AM ET (9:00 AM CST = 15:00 UTC) Mon-Fri
0 15 * * 1-5 curl -s -X POST "http://localhost:8100/api/auto-trade/run?dry_run=false" >> /home/mph/alpha-momentum/data/auto_trade.log 2>&1

# Options wheel check at 3:30 PM ET (2:30 PM CST = 20:30 UTC) Mon-Fri
30 20 * * 1-5 curl -s -X POST "http://localhost:8100/api/auto-trade/wheel?dry_run=false" >> /home/mph/alpha-momentum/data/auto_trade.log 2>&1
```

---

## Technical Indicator Signal Map

Color mapping for the dashboard (from `frontend/` HUD widgets):

| Indicator | Function | 🟢 Bullish | 🔴 Bearish | 🟡 Neutral |
|-----------|----------|-----------|-----------|-----------|
| RSI | Momentum | < 30 (Oversold) | > 70 (Overbought) | 30 – 70 |
| MACD | Trend | Bullish Crossover | Bearish Crossover | Flat |
| Bollinger Bands | Volatility | Price < Lower | Price > Upper | Within |
| Moving Averages | Trend | Price > MA | Price < MA | At MA |
| Stochastic | Momentum | %K crosses %D (low) | %K crosses %D (high) | Mid |
| ATR | Volatility | Low (compressing) | Extreme | Mean |

> These are already partially wired in the AlphaScanner scoring and VoPR regime classification. The dashboard widget in `frontend/js/widgets/scanner.js` should reflect these colors.

---

## Developer Toolkit

### Currently Used

- **Data:** Pandas, NumPy, httpx, yfinance
- **Greeks:** Pure-Python Black-Scholes in `vopr/greeks.py`
- **Viz:** Frontend HUD (vanilla JS + GridStack.js)
- **AI:** Gemini Copilot via `/api/copilot` + MCP tools
- **Broker:** Tradier (via `services/tradier_service.py` + `uvatradier`)

### Future Additions (from NotebookLM spec)

| Tool | Purpose | Priority |
|------|---------|----------|
| `py_vollib` | Jäckel's LetsBeRational for max-precision Greeks | HIGH — replace custom BS |
| Backtrader / Jesse | Strategy backtesting framework | MEDIUM |
| Redis | Session/state persistence for wheel state machine | LOW (JSON file is fine for now) |
| Databento | Tick-level data (512t, 1160t intervals) | LOW — nice to have |
| Schwab/Alpaca | Additional brokers (needed for 0DTE/futures) | DEFERRED |

### Security (already in place)

- All API keys in `.env` (NOT synced between machines)
- `.env` in `.gitignore`
- Tradier token accessed via `os.getenv("TRADIER_TOKEN")`
- VaultGuard secrets server available for centralized management

---

## TODO Tracker

### Ready Now

- [x] Smart buyer script (`scripts/smart_buyer.py`)
- [x] Market clock endpoint
- [x] Auto-trade API endpoints
- [x] MCP trading tools
- [x] Trade journal
- [ ] Deploy Phase 1 to Venus (rsync + rebuild)
- [ ] Morning validation (dry run → live)
- [ ] Set up Venus cron (equity auto-buy at 10:00 AM ET)

### Phase 2 (Options Wheel)

- [ ] Implement `score_option()` formula in `vopr/filters.py`
- [ ] Create `data/wheel_symbols.txt` with approved tickers
- [ ] Build `scripts/wheel_runner.py` (CSP → CC state machine)
- [ ] Create `data/wheel_state.json` schema
- [ ] Add `/api/auto-trade/wheel` and `/api/auto-trade/wheel-state` endpoints
- [ ] Implement roll logic (yield threshold + delta check)
- [ ] Wire Wheel into Venus cron (3:30 PM ET)

### Phase 3 (Strategy Modules)

- [ ] Extract `strategies/ema_strategy.py` from AlphaScanner
- [ ] Build `strategies/supertrend_strategy.py` (new)
- [ ] Implement crossover event detection (vs. current state-based)
- [ ] Add stop-loss logic to strategy outputs
- [ ] Backtest framework integration (Backtrader or Jesse)

### Phase 4 (Analytics & Polish)

- [ ] Build `scripts/analytics.py` (Sharpe, Sortino, VaR, Beta, MaxDD)
- [ ] Enhance trade log schema with net_cost, commission, cash_balance
- [ ] Create equity curve visualization endpoint
- [ ] Replace custom BS with py_vollib (if precision matters)
- [ ] Evaluate Databento for tick-level data

### Aspirational (Not Currently Feasible)

- [ ] 0DTE SPX strategy (requires futures broker)
- [ ] Schwab OAuth 2.0 integration
- [ ] Alpaca API integration
- [ ] Redis state persistence
- [ ] Hummingbot HFT integration

---

## Phase 5: UI & Tracking Dashboard (Inspired by tasty-schwab-trade-FE) 🔲 PLANNED

To manage the newly modular strategies (EMA, Supertrend, Options Wheel) efficiently, the frontend needs a unified configuration and tracking dashboard.

### A. Strategy Parameter Control Panel

*Inspired by the `strategy-control` components in the reference repo.*

A new dashboard tab in TraderDaddy / Mission Control dedicated to strategy management:

- **Global Strategy Toggles**: Enable/disable entire strategies (e.g., Turn off Options Wheel during FOMC).
- **Ticker-Level Configuration Data Tables**:
  - `Symbol`
  - `Trade Enabled` (Boolean toggle switch)
  - `Strategy Parameters` (e.g., MA Type, Period 1, Period 2, Option Delta limit)
  - `Capital Allocation` (Max $ or Quantity per broker routing, e.g. Tradier vs Schwab)
  - **Inline Editing**: Ability to tweak parameters or quantities on the fly and save them instantly to the backend (updating `data/wheel_state.json` or strategy configs).

### B. The Wheel Options Tracker

A dedicated view to track the state machine of the Options Wheel:

- **Current State**: Displays whether the ticker is in `CASH`, `CSP` (Cash-Secured Put), or `CC` (Covered Call) state.
- **Position Tracking**:
  - Strike Price, Expiration (DTE), Premium Received, Current Mark.
  - Live P&L and Distance to Strike (ITM/OTM probability).
- **Action Required Flags**: Highlights expiring positions or positions where the roll-or-rinse logic is triggered (e.g., 1% ITM near expiry).

### C. Trade Journal / Alpha Feed UI

- A scrolling feed (similar to the current news ticker) broadcasting auto-trade executions in real-time.
- Historical data table reflecting the enhanced schema (`net_cost`, `commission`, `cash_balance`).

---

## NotebookLM Reference

**AI Trading and Sentiment Analysis Guide 2026**
ID: `fde96caa-0037-4452-a155-16d15de0b0c0`
URL: `https://notebooklm.google.com/notebook/fde96caa-0037-4452-a155-16d15de0b0c0`

37 sources loaded. Covers Trade Ideas, TrendSpider, StockHero, Holly AI. The v2 spec above was refined from its technical strategy and algorithmic execution specifications, plus UI inspiration from `tasty-schwab-trade-FE`.

---

*Phase 1 is plumbing. Phase 2 is where the VoPR engine earns its keep. Phase 3 is where it gets modular. Phase 4 is where it gets institutional. Phase 5 is where it becomes a usable product.* — Antigravity
