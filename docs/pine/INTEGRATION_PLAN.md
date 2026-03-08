# 👻 Ghost Alpha — TradingView to Venus Integration Plan

## Objective
Connect TradingView's dynamic JSON webhook alerts from Ghost Alpha (v6.2+) to the Venus Auto-Trader, allowing automated execution of A-grade setups.

## Architecture

### 1. TradingView (The Signal Generator)
Ghost Alpha triggers an alert on `barstate.isconfirmed` with a dynamic JSON payload:
```json
{
  "ticker": "SPY",
  "tf": "5",
  "grade": "A+",
  "signal": "CONFLUENCE_BULL",
  "regime": "BULL",
  "struct": "INTACT",
  "cvd": "BUY",
  "price": 505.25,
  "rvol": 2.1
}
```
**Webhook URL:** `https://mphinance.com/api/webhook/ghost` (Vultr VPS)

### 2. Vultr VPS (The Public Gateway)
Vultr acts as a secure proxy to receive the payload from TradingView, validate the source, and forward it to Venus (since Venus is on a local IP `192.168.2.172`).
- **Endpoint:** `POST /api/webhook/ghost`
- **Validation:** Check a shared secret header (configured in TradingView alerts).
- **Action:** Forward verified JSON payload to Venus Auto-Trader.

### 3. Venus Auto-Trader (The Execution Engine)
Venus receives the signal on port 8100 (Docker FastAPI).
- **Endpoint:** `POST /api/auto-trade/webhook` (Needs to be built)
- **Logic:**
  1. **Parse:** Extract `ticker`, `grade`, `signal`, `price`.
  2. **Filter:** Enforce minimum grade (e.g., Reject `C`, `D`, `F`).
  3. **Direction:** Route `CONFLUENCE_BULL` to Long, `CONFLUENCE_BEAR` to Short.
  4. **Risk Management:** Default to $50/position limit, using bid/ask limit orders.
  5. **Execution:** Call the existing Tradier API routes (e.g., `/api/trade/execute`) with `dry_run=true` initially, toggling to `live` once verified.

## Implementation Steps

1. **Vultr Gateway:** Add webhook receiving route on the Vultr FastAPI server.
2. **Venus Endpoint:** Add `/api/auto-trade/webhook` to Alpha-Momentum backend on Venus.
3. **Tradier Execution Mapping:** Map specific signal text to proper buy/sell orders in Tradier.
4. **Testing Phase:** Send mock JSON payloads via cURL/Postman to Vultr and confirm they land in `data/trade_log.json` on Venus.