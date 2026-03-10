# 🔗 Alpha-Momentum — Sister Repo Reference

> **This doc exists to give agents working in mphinance full context on the alpha-momentum trading engine.**
> Updated: 2026-03-06

## What Is Alpha-Momentum?

Alpha-Momentum is the **live trading engine and mission control** for the Ghost Alpha ecosystem. While mphinance generates daily intelligence reports, alpha-momentum **acts on them** — executing trades, scanning for setups, and providing real-time market data.

It's being positioned as the **agentic frontend to TraderDaddy Pro** (or "TraderMommy" 🤷‍♀️).

## Where It Lives

| Component | Location | Port |
|-----------|----------|------|
| FastAPI Backend | Venus (`192.168.2.172`) | 8100 |
| Trading-MCP (TypeScript) | Venus (Docker) | 5057 |
| Tasty-Agent (Python) | Venus (Docker) | 5058 |
| Tradier-Agent (Python) | Venus (Docker) | 5059 |
| Frontend HUD | Venus (served by FastAPI static mount) | 8100 |

**Dev path on sam2:** `/home/sam/Antigravity/alpha-momentum`
**Production path on Venus:** `/home/mph/alpha-momentum`

## API Endpoints (<http://192.168.2.172:8100>)

### Market Data

```
GET  /api/health               Health check
GET  /api/market/indices       Major index performance (SPY, QQQ, DIA, IWM)
GET  /api/market/crypto        BTC/ETH snapshot
GET  /api/market/news          Aggregated RSS news
GET  /api/market/quotes?s=X,Y  Batch real-time quotes (Tradier)
GET  /api/market/clock         Market open/closed status
GET  /api/quote/{symbol}       Single symbol quote
```

### Brokerage (Tradier)

```
GET  /api/portfolio/tradier    Portfolio summary + positions + P/L
GET  /api/trade/orders         Order history
POST /api/trade/preview        Preview order (no execution)
POST /api/trade/execute        ⚠️ REAL order (requires confirm=true)
DEL  /api/trade/cancel/{id}    Cancel open order
```

### Auto-Trade (Smart Buyer)

```
POST /api/auto-trade/run       Execute smart buyer (dry_run=true default)
GET  /api/auto-trade/log       View trade journal
```

### Analytics & Scanners

```
GET  /api/picks/today          Daily momentum picks (A-D grades) — proxied from GH Pages
GET  /api/signals/stream       SSE real-time signal alerts
GET  /api/signals/history      Signal history with technicals
GET  /api/screener/momentum    RSI/EMA/Volume scanner
GET  /api/screener/miners      Gold/silver miner alpha scanner
```

### VoPR Options Engine

```
GET  /api/vopr/auto-scan?ticker=X     Auto-pick expiries, full scan
GET  /api/vopr/batch-scan?tickers=X,Y Multi-ticker VoPR, rank by VRP
GET  /api/vopr/coil-scan?tickers=X,Y  ATR compression detector
GET  /api/vopr/volatility?ticker=X    Realized vol breakdown + regime
GET  /api/vopr/expirations?ticker=X   Available option expiry dates
GET  /api/vopr/history?ticker=X       OHLCV history
```

### AI Copilot

```
POST /api/copilot              Gemini AI chat with MCP tool-use
```

## Architecture

```
alpha-momentum/
├── api/main.py              # THE monolith (1296 lines, 30+ endpoints)
├── core/
│   ├── data_engine.py       # Market data + scanner coordination
│   ├── mcp_client.py        # MCP server communication
│   └── signals.py           # Unified signal format (TradeSignal)
├── services/
│   ├── signal_engine.py     # Real-time EMA+RSI+ADX+Volume (25KB)
│   ├── tradier_service.py   # Tradier brokerage wrapper
│   ├── news_engine.py       # RSS aggregation
│   └── charting.py          # Chart generation
├── vopr/                    # VoPR Options Analytics Engine
│   ├── volatility_models.py # 4-model composite RV (Parkinson, GK, RS, CC)
│   ├── greeks.py            # Black-Scholes Greeks
│   ├── scanner.py           # Options chain scanner
│   ├── filters.py           # Delta/OI/volume/liquidity gates
│   ├── technicals.py        # Technical indicator library
│   ├── tradier_client.py    # Options chain fetcher
│   └── config.py            # All scanner knobs
├── scanners/
│   └── alpha_engine.py      # EMA 8/21/34/55/89 + RSI + ATR scoring
├── strategies/
│   └── reversal_exhaustion.py  # Trend reversal strategy
├── scripts/
│   └── smart_buyer.py       # Auto-buy CLI (dry-run default)
├── tradier-agent/           # MCP server (Python FastMCP, port 5059)
├── trading-mcp/             # MCP server (TypeScript, port 5057)
├── tasty-agent/             # MCP server (Python, port 5058)
├── frontend/                # Bloomberg-style HUD (vanilla JS + GridStack.js)
└── docker-compose.yml       # 4 services
```

## How mphinance Already Integrates

1. **Picks pipeline** — alpha-momentum's `/api/picks/today` fetches from `mphinance.github.io/mphinance/picks/latest.json` (the dossier-generated picks)
2. **VoPR in dossier** — mphinance's `dossier/data_sources/csp_setups.py` has a simplified VoPR. The real engine is in alpha-momentum's `vopr/`.
3. **Scanner strategies** — mphinance `strategies/` and alpha-momentum `scanners/` both scan tickers. Should be unified signal format.

## How mphinance COULD Integrate More

1. **Real-time quotes** — Instead of yfinance in the dossier, call `GET /api/market/quotes` for Tradier real-time data
2. **VoPR data in reports** — The dossier could call `/api/vopr/auto-scan` for rich options data in ticker pages
3. **Signal alerts in blog** — Alpha-momentum's SSE signal stream could generate blog entries
4. **Portfolio awareness** — Dossier could check which picks Michael actually holds via `/api/portfolio/tradier`
5. **Copilot in pipeline** — The `/api/copilot` endpoint (Gemini + MCP tools) could replace raw Gemini calls in `watchlist_dive.py`

## Auto-Trade System Status

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1: Equity Smart Buyer | ✅ BUILT | Grade A/B picks → limit orders ($50 max) |
| Phase 2: Options Wheel | 🔲 PLANNED | VoPR-powered CSP → CC state machine |
| Phase 3: Strategy Modules | 🔲 PLANNED | EMA crossover, Supertrend, modular backtesting |
| Phase 4: Risk Analytics | 🔲 PLANNED | Sharpe, Sortino, VaR, equity curve |
| Phase 5: UI Dashboard | 🔲 PLANNED | Strategy control panel, wheel tracker |

**⚠️ L2 Options NOT yet enabled on Tradier** — equity auto-buy works, options Wheel blocked until approval.

## Deployment (from sam2)

```bash
# Rsync to Venus + rebuild
rsync -avz --exclude='.git' --exclude='AlexTrading-WebApp' --exclude='alpha-reflex' --exclude='__pycache__' --exclude='node_modules' --exclude='.env' --exclude='venv' --exclude='*.pyc' --exclude='_archive' /home/sam/Antigravity/alpha-momentum/ venus:/home/mph/alpha-momentum/
ssh venus "cd /home/mph/alpha-momentum && docker compose build --no-cache api && docker compose up -d api"
```

## ⚠️ Critical Gotchas

1. **Venus has ancient Python** — NEVER run Python directly on Venus. Always use Docker.
2. **Port 8100** — Docker maps 8000→8100 externally.
3. **`.env` not synced** — Each machine has its own API keys.
4. **Static mount is LAST** in main.py — all routes must be defined before `app.mount("/", ...)`.
5. **Tradier returns `"null"` string** — not JSON null for empty positions.
6. **Picks are cached 5 min** — `/api/picks/today` proxies from GH Pages with TTL.
