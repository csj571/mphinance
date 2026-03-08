# 🔌 GHOST ALPHA <> VENUS INTEGRATION PLAN

**Author:** Sam the Quant Ghost
**Target System:** Venus Auto-Trade Engine (FastAPI port 8100)

## Overview
Ghost Alpha v6.2 generates institutional-grade JSON signals via TradingView alerts. We need to catch these webhooks in the Alpha-Momentum backend on Venus, filter them based on Ghost Grade and Risk parameters, and feed them directly into the `/api/trade/execute` or `/api/auto-trade/run` pipelines.

## 1. Webhook Ingestion (The Bridge)
**New Endpoint Required:** `POST /api/signals/webhook`
Since Venus is on a local network (`192.168.2.172`), TradingView cannot hit it directly.
**Path:**
1. TradingView webhook fires to the public Vultr server (`mphinance.com/api/signals/webhook`).
2. Vultr validates the payload (using an `x-ghost-token` header).
3. Vultr forwards the payload to Venus via a secure tunnel (e.g., Cloudflare Tunnel, ngrok, or WireGuard) to `http://venus:8100/api/signals/webhook`.

**Payload Format:**
```json
{
  "ticker": "SPY",
  "tf": "5",
  "grade": "A+",
  "signal": "CONFLUENCE_BULL",
  "regime": "BULL",
  "struct": "BROKEN_UP",
  "cvd": "BUY",
  "price": 505.20,
  "rvol": 1.8
}
```

## 2. Signal Filtering & Processing
When Venus receives the webhook, the Auto-Trade engine evaluates it:
- **Timeframe Check:** Ignore if not 5m or 15m (prevent daily chart signals from firing intraday executions).
- **Grade Check:** Hard reject if `grade` is "C", "D", or "F". Only "A+", "A", and "B" are permitted.
- **Signal Type:** 
  - `CONFLUENCE_BULL` / `SWEEP_BULL` -> Triggers LONG evaluation.
  - `TRAIL_EXIT_BULL` / `DIVERGE_BEAR` -> Triggers EXIT evaluation for open longs.

## 3. Position Sizing & Execution
Instead of passing the buck to the user, the Auto-Trade system takes over:
- Calls `get_tradier_balance()` via the `tradier-agent` MCP.
- Verifies we aren't exceeding the max 2 concurrent positions constraint.
- Ensures the position size fits the $50 max cap limit.
- Checks if `dry_run=true` (which is default).
- Issues `buy_stock(symbol, dollars, dry_run)` or equivalent options trade.

## 4. SSE Broadcast
The signal is immediately broadcasted to the HUD via the existing `GET /api/signals/stream` endpoint, flashing the widget green or gold and playing the arcade sound effect.

## Immediate Next Steps for Claude/Michael:
1. Build `POST /api/signals/webhook` on Vultr and Venus.
2. Add the `x-ghost-token` middleware to VaultGuard.
3. Update `auto_trade.py` on Venus to listen for these incoming dicts instead of just polling `/api/screener/momentum`.
