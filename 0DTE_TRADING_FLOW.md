# 0DTE SPY/QQQ Options Day Trading Flow

**Date:** 2026-03-08
**Author:** Sam (Ghost Copilot)

This document outlines the concrete implementation plan for the 0DTE SPY/QQQ options day trading flow, integrating Ghost Alpha v6.2 signals from TradingView with our Venus-hosted auto-trading backend via Tradier.

## 1. The Exact Trading Flow

### A. Signal Generation (TradingView)
- **Indicator:** Ghost Alpha v6.2
- **Trigger:** `barstate.isconfirmed` on 5m or 15m timeframe.
- **Payload:** JSON containing `ticker` (SPY/QQQ), `grade` (A+ or A), `signal` (CONFLUENCE_BULL or CONFLUENCE_BEAR), `price`.
- **Destination:** `https://mphinance.com/api/webhook/ghost` (Vultr VPS)

### B. Gateway & Routing (Vultr VPS)
- **Action:** Vultr receives the payload, validates the shared secret header, and forwards the verified JSON to the Venus server at `http://192.168.2.172:8100/api/auto-trade/webhook`.

### C. Entry Execution (Venus Auto-Trader)
- **Validation:** Venus verifies `ticker` is SPY or QQQ and `grade` is A+/A.
- **Contract Selection:** 
  - Fetch today's option chain for the ticker from Tradier.
  - If `CONFLUENCE_BULL` → Select Call. If `CONFLUENCE_BEAR` → Select Put.
  - **Delta/Strike Target:** Select the strike closest to ATM (At-The-Money) or slightly OTM (Delta ~0.40 to 0.50) to balance premium cost and gamma exposure.
- **Order Placement:** Place a **Buy to Open (BTO)** Limit order at the current `ask` or mid-price using Tradier's API.
- **Logging:** Log the entry in `data/trade_log.json` with the specific option symbol (e.g., `SPY260309C00515000`).

### D. Position Management & Exit (Venus & Michael)
- **Manual Overrides:** Since Michael is watching charts during market hours, exits are primarily manual via the Tradier interface or the upcoming auto-trade HUD.
- **Auto-Close (Failsafe):** If not closed manually, a cron job on Venus triggers at **3:45 PM ET** to market-sell (Sell to Close) any open 0DTE positions to prevent assignment/exercise risk.

---

## 2. What Needs to be Built vs. What Exists

### ✅ What Already Exists
- **TradingView Signals:** Ghost Alpha v6.2 indicator is ready and capable of generating dynamic JSON payloads.
- **Venus Infrastructure:** FastAPI backend on port 8100, Dockerized, with basic equity auto-trade endpoints (`/api/auto-trade/run`).
- **Tradier Integration:** `services/tradier_service.py` is established with authentication and equity execution capabilities.
- **Vultr Proxy Concept:** Documented in `docs/pine/INTEGRATION_PLAN.md`.

### 🛠️ What Needs to be Built (By Monday)
1. **Webhook Receiver on Venus:** Implement `POST /api/auto-trade/webhook` in the FastAPI app to parse the TradingView payload and trigger execution.
2. **Vultr Forwarder:** Ensure the route on Vultr is actually forwarding the payload to the local Venus IP.
3. **Options Chain Fetcher:** Add logic to fetch 0DTE chains for SPY/QQQ from Tradier (`GET /v1/markets/options/chains`) and filter for the target strike.
4. **Options Order Builder:** Extend the Tradier service to support `option` class orders (`buy_to_open`, `sell_to_close`). The current `smart_buyer.py` only handles equities.
5. **Auto-Close Scheduler:** Create a script (`scripts/0dte_auto_close.py`) and a cron job on Venus to liquidate 0DTE options at 3:45 PM ET.

---

## 3. Risk Guardrails for 0DTE

- **Maximum Allocation:** Fixed max dollar amount per trade (e.g., $100-$300 limit per signal, determining contract quantity).
- **Max Concurrent Positions:** Only 1 open 0DTE position at a time. The webhook must reject new signals if a position is already active.
- **Stop-Loss (Systematic):** Implement a hard stop-loss at 50% premium decay. This can be submitted as a contingent Stop-Market order immediately after the entry fills.
- **Time-in-Force / Auto-Close:** **CRITICAL.** All 0DTE positions MUST be closed by **3:45 PM ET** (15 minutes before market close) to avoid catastrophic risk. A cron job will forcefully issue Market `Sell to Close` orders for any remaining 0DTE inventory.
- **Dry Run Default:** The webhook must support a `dry_run=true` state by default to verify signal parsing and contract selection before real capital is deployed.

---

## 4. Can We Use the Existing Tradier API for 0DTE Options?

**Yes.** Tradier natively supports SPY and QQQ options. Because they are standard ETF options (unlike SPX index options which require futures/index routing that Tradier lacks for retail auto-trading), we can trade them with our current setup.

We will use the standard Tradier options endpoints:
- **Get Options Chain:** `GET /v1/markets/options/chains?symbol=SPY&expiration=YYYY-MM-DD`
- **Place Order:** `POST /v1/accounts/{account_id}/orders`
  - `class=option`
  - `symbol=SPY`
  - `option_symbol=SPY260309C00515000`
  - `side=buy_to_open` (for entry)
  - `type=limit`
  - `duration=day`

The only difference from our equity trading logic is passing `class=option` and the specific `option_symbol` derived from the chain.
