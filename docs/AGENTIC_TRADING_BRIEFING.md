# 🤖 Agentic Trading Stack — Technical Briefing

**From:** Michael (Momentum Phinance) + Sam the Quant Ghost
**To:** DoubleDownToWin
**Date:** 2026-03-06
**Status:** Phase 1 built, Phase 2-5 planned. L2 options approval pending (lol).

---

## TL;DR

We built a fully automated trading pipeline: AI scans → grades picks → executes orders → logs everything. It's split across two repos, three machines, and four Docker services. Everything defaults to **dry-run** — nothing executes without explicit `dry_run=false`. The system is live on a home server (Venus), talks to Tradier for brokerage, and uses Gemini AI for analysis. Monday's the first real trading day once L2 options get approved.

---

## Architecture (30,000 ft)

```
┌─────────────────────────────────────┐
│         sam2 (Dev Machine)          │
│   Code, testing, orchestration      │
└──────────┬──────────────┬───────────┘
           │ rsync+ssh    │ git push
           ▼              ▼
┌──────────────────┐  ┌──────────────────┐
│  Venus (Home)    │  │   Vultr (VPS)    │
│  192.168.2.172   │  │  mphinance.com   │
│  Port 8100       │  │  Port 8002       │
│                  │  │                  │
│  Alpha-Momentum  │  │  Ghost Alpha API │
│  - FastAPI       │  │  - Dossier data  │
│  - VoPR Engine   │  │  - Ticker pages  │
│  - Signal Engine │  │  Apache SSL      │
│  - Tradier       │  │                  │
│  - 3 MCP Servers │  ├──────────────────┤
│  - Auto-Trade    │  │  GitHub Pages    │
│  Docker Compose  │  │  Daily reports   │
└──────────────────┘  │  Picks JSON      │
                      │  Deep dive pages │
                      └──────────────────┘
```

---

## The Trading Engine (Alpha-Momentum)

**Stack:** FastAPI + Docker Compose on Venus, 4 services, 1296-line monolith API.

### Docker Services

| Service | Port | What |
|---------|------|------|
| `api` | 8100 | FastAPI backend + static HUD frontend |
| `trading-mcp` | 5057 | TypeScript MCP server — trading tools |
| `tasty-agent` | 5058 | Python MCP server — TastyTrade (deprecated) |
| `tradier-agent` | 5059 | Python MCP server — Tradier brokerage tools |

### API Endpoints (30+ routes)

**Market Data:**

- `GET /api/market/indices` — SPY, QQQ, DIA, IWM real-time
- `GET /api/market/quotes?symbols=TSLA,NVDA` — batch Tradier quotes
- `GET /api/market/clock` — is the market open?
- `GET /api/market/news` — aggregated RSS from CNBC, MarketWatch, Yahoo

**Brokerage (Tradier):**

- `GET /api/portfolio/tradier` — positions, P/L, buying power
- `POST /api/trade/preview` — preview order without executing
- `POST /api/trade/execute` — ⚠️ REAL order (requires `confirm=true`)
- `GET /api/trade/orders` — order history

**Auto-Trade (Smart Buyer):**

- `POST /api/auto-trade/run?dry_run=true` — execute the smart buyer
- `GET /api/auto-trade/log` — trade journal

**VoPR Options Engine:**

- `GET /api/vopr/auto-scan?ticker=TSLA` — auto-pick expiries, full options scan
- `GET /api/vopr/batch-scan?tickers=AAPL,TSLA,NVDA` — multi-ticker, ranked by VRP ratio
- `GET /api/vopr/coil-scan` — ATR compression detector (coiling stocks)
- `GET /api/vopr/volatility?ticker=TSLA` — 4-model realized vol + regime classification

**AI Copilot:**

- `POST /api/copilot` — Gemini AI chat with live MCP tool-use (can execute queries against brokerage)

### Smart Buyer Logic (Phase 1 — ✅ Built)

```
1. GET /api/market/clock        → abort if market not open
2. GET /api/picks/today         → filter grade A/B only
3. GET /api/portfolio/tradier   → check buying power + held symbols
4. For each eligible pick:
   a. GET /api/quote/{symbol}   → current price, bid
   b. qty = floor($50 / price)  
   c. POST /api/trade/preview   → verify cost
   d. POST /api/trade/execute   → limit order at bid (if not dry_run)
5. Append to data/trade_log.json
```

**Safety rails:**

- Max $50/position, max 2 concurrent, $25 buying power buffer
- Only grade A/B picks, limit orders at bid price (not market)
- Default: DRY RUN. Must explicitly pass `dry_run=false`
- Everything logged to `data/trade_log.json` with full scoring formula

---

## VoPR Options Analytics Engine

This is where the edge lives. VoPR = **Volatility Options Pricing & Range**.

### 4-Model Realized Volatility Ensemble

| Model | Weight | What It Measures |
|-------|--------|------------------|
| Parkinson | 0.15 | High-Low range vol (intraday extremes) |
| Garman-Klass | 0.25 | OHLC vol (most efficient estimator) |
| Rogers-Satchell | 0.25 | Drift-independent vol (handles trending markets) |
| Close-to-Close | 0.35 | Standard historical vol (baseline) |

**Composite RV** = weighted blend → compare against **Implied Volatility** → get **VRP Ratio** (Volatility Risk Premium).

- VRP > 1.2 → IV is overpriced → sell premium (CSPs, covered calls)
- VRP < 0.8 → IV is cheap → market knows something, sit on hands
- VRP 0.8–1.2 → neutral, be selective

### Options Chain Scanning

```python
# Scanner config (vopr/config.py)
delta_range: (0.10, 0.25)    # OTM sweet spot for premium selling
min_open_interest: 500        # Liquidity gate
min_volume: 100               # Activity gate  
min_dte: 21                   # No weeklies
max_dte: 50                   # ~30 day target
```

Each option gets scored:

```
score = (1 - |delta|) × (250 / (DTE + 5)) × (bid / strike)
```

### Black-Scholes Greeks

Custom pure-Python implementation in `vopr/greeks.py`:

- Delta, Theta, Gamma, Vega
- Used when Tradier's ORATS Greeks aren't available (yfinance fallback)

---

## The Intelligence Pipeline (mphinance)

Runs daily at 6AM CST via GitHub Actions. 13 stages:

1. **Market Pulse** — benchmark performance (SPY, QQQ, DIA, IWM, VIX, BTC)
2. **Strategy Scanner** — EMA crossover, gravity squeeze, vol squeeze, gamma walls
3. **Institutional Data** — ETF holdings via TickerTrace API
4. **Market Regime** — VIX-based regime detection + hedge suggestions
5. **Signal Persistence** — track how long tickers stay in the scanner (lifers vs. new)
6. **Technical Setups** — pivot-based entry/exit with risk/reward ratios
7. **CSP Setups** — cash-secured put candidates (simplified VoPR)
8. **Ticker Enrichment** — EMA stack, RSI, ADX, Bollinger, fundamentals, scores
9. **AI Narrative** — Gemini writes the daily report in Sam's voice
10. **Report Generation** — full HTML report + PDF
11. **Ticker Pages** — individual deep dive pages per ticker
12. **Index Update** — regenerate the archive page
13. **Git Push + Substack Draft** — auto-deploy + draft the newsletter

**Output:** Daily picks JSON (with grades A-D), enriched ticker data, full narrative report.

The auto-trader on Venus consumes this via:

```
GET https://mphinance.github.io/mphinance/picks/latest.json
```

---

## MCP (Model Context Protocol) Integration

Three MCP servers give the AI copilot live brokerage access:

### tradier-agent (Python, port 5059)

| Tool | What |
|------|------|
| `get_tradier_balance()` | Account balance (direct Tradier API) |
| `get_tradier_positions()` | Positions with P/L |
| `get_tradier_quotes(symbols)` | Live quotes |
| `buy_stock(symbol, dollars, dry_run)` | Preview/execute buy order |
| `check_portfolio()` | Full portfolio summary |
| `get_picks()` | Today's momentum picks |
| `get_market_clock()` | Market open/close status |

The `/api/copilot` endpoint connects Gemini to these tools. You can literally ask "what's my portfolio looking like?" and it calls `check_portfolio()`, then synthesizes the response.

---

## Data Flow for Backtesting

```python
from vopr.data_ingestion import fetch_ohlcv, get_spot_price

# OHLCV: tries Tradier first, falls back to yfinance
df = fetch_ohlcv("TSLA", days=252)  # 1 year
# Returns: DatetimeIndex, columns: Open, High, Low, Close, Volume

# Volatility analysis
from vopr.volatility_models import composite_realized_vol, classify_regime
rv = composite_realized_vol(df)  # 4-model ensemble
regime = classify_regime(df)     # LOW / MODERATE / HIGH / EXTREME
```

**API endpoint:**

```bash
curl "http://192.168.2.172:8100/api/vopr/history?ticker=TSLA&days=252"
# → JSON array: [{date, open, high, low, close, volume}, ...]
```

---

## Planned Phases (Monday and Beyond)

| Phase | Status | What |
|-------|--------|------|
| 1. Equity Smart Buyer | ✅ Built | Grade A/B picks → limit orders |
| 2. Options Wheel (VoPR) | 🔲 Next | CSP → assignment → CC → cycle. VoPR scores options. |
| 3. Strategy Modules | 🔲 Planned | EMA crossover, Supertrend as modular backtestable strategies |
| 4. Risk Analytics | 🔲 Planned | Sharpe, Sortino, VaR, max drawdown, equity curve |
| 5. UI Dashboard | 🔲 Planned | Strategy control panel, wheel tracker, trade journal |

### The Wheel State Machine (Phase 2)

```
SELL CSP → [assigned] → SELL CC → [called away] → CASH → repeat
    ↑ expires OTM           ↑ expires OTM
    └───────────────────────┘
```

- 1 contract per symbol max
- Roll logic: if expiring put is within 1% ITM, evaluate roll vs assignment
- Wider delta band than VoPR premium-selling (0.18-0.42 vs 0.10-0.25) because assignment is *desired*

---

## Security Notes

- All API keys in `.env` files (NOT committed, NOT synced between machines)
- VaultGuard centralized secrets manager available (FastAPI + Firebase Firestore)
- Tradier uses bearer token auth (`TRADIER_TOKEN` env var)
- Auto-trade defaults to dry-run — requires explicit override
- Trade execution endpoint requires `confirm=true` in request body
- All trades logged with full audit trail (scoring formula, pick grade, timestamps)

---

## Monday Game Plan

1. ~~Enable L2 options on Tradier~~ (approval form submitted, waiting)
2. Deploy Phase 1 to Venus: `rsync` + `docker compose build --no-cache api && up -d api`
3. Morning dry-run test: `curl -X POST "http://192.168.2.172:8100/api/auto-trade/run?dry_run=true"`
4. If clean → first live run with real money
5. Set up Venus cron for 10:00 AM ET auto-buy

**Venus cron (once validated):**

```bash
# Equity auto-buy Mon-Fri at 10:00 AM ET
0 15 * * 1-5 curl -s -X POST "http://localhost:8100/api/auto-trade/run?dry_run=false" >> /home/mph/alpha-momentum/data/auto_trade.log 2>&1
```

---

*Built by Michael + Sam the Quant Ghost. The code is ugly but the architecture is sound.*
*"God, grant me the serenity to accept the trades I cannot change, the courage to cut the ones I can, and the wisdom to know the difference."*
