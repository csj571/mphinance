# 👻 GHOST ALPHA: INTEGRATION PLAN
**Target:** Bridge TradingView Webhooks to Venus Auto-Trader (Alpha-Momentum)
**Author:** Claude (via Gemini CLI Partner Protocol)
**Date:** 2026-03-08

## Overview
Ghost Alpha v6.2 generates institutional-grade, multi-axis confluence signals. The goal is to pipe these signals automatically from TradingView into the `alpha-momentum` FastAPI backend running on **Venus (192.168.2.172:8100)** to execute trades via Tradier and update the HUD.

Since Venus is on a local network and TradingView requires a public URL, we will use **Vultr (mphinance.com)** as the public-facing webhook bridge.

## Phase 1: The Payload Architecture

Ghost Alpha emits a highly compressed JSON payload on confirmed bar closes when a signal fires.

**Example TradingView Payload:**
```json
{
  "ticker": "SPY",
  "tf": "5",
  "grade": "A+",
  "signal": "CONFLUENCE_BULL",
  "regime": "BULL",
  "struct": "INTACT",
  "cvd": "BUY",
  "price": 512.45,
  "rvol": 1.8
}
```

## Phase 2: The Vultr Bridge (mphinance.com:15422)

We need a lightweight FastAPI/Express endpoint on Vultr to catch the TradingView POST request and relay it to Venus.

1. **Endpoint:** `POST https://mphinance.com/api/webhooks/ghost`
2. **Security:** TradingView allows passing headers or basic auth in the webhook URL. We should use a `X-Ghost-Token` header stored in VaultGuard.
3. **Relay Logic:** Vultr catches the payload, validates the token, and pushes it to Venus. Since Venus is local (`192.168.2.172`), Vultr will need a secure tunnel to Venus (e.g., Wireguard, Tailscale) or it will write the signal to a secure Redis/Firebase queue that Venus polls.
   *Recommendation:* Use Firebase Firestore (`/signals` collection) as the intermediary. Vultr writes to Firestore; Venus listens to Firestore in real-time. No firewall holes needed.

## Phase 3: Venus (Alpha-Momentum) Processing

The `alpha-momentum` backend on Venus (FastAPI) receives the signal.

1. **Ingestion & SSE Broadcast:** 
   The signal is saved to the local database and immediately pushed to `/api/signals/stream` so the Alpha.HUD updates with neon alerts.

2. **The Auto-Trader Filter (`/api/auto-trade/run` logic):**
   *   **Grade Check:** Is the `grade` "A" or "A+"? (Reject B, C, D, F for automated entries).
   *   **Signal Type:** Is it a highly convicted signal? `CONFLUENCE_BULL`, `CONFLUENCE_BEAR`, `SWEEP_BULL`, or `SWEEP_BEAR`.
   *   **Regime Alignment:** Does the trade direction match the `regime`? (e.g., No shorts in a `BULL` regime).
   *   **Risk Management Check:** Does the portfolio have buying power? Is the position size within the $50/position limit?

3. **Tradier Execution (`/api/trade/execute`):**
   If the signal passes the gauntlet:
   *   Fetch current Tradier quote.
   *   Calculate share size based on the $50 limit and current price.
   *   Submit LIMIT order at the current Bid (for buys) or Ask (for sells) via the Tradier API.
   *   Write to `data/trade_log.json`.

4. **Trailing Stop Exit (The Ghost Trail):**
   When TradingView sends a `TRAIL_EXIT_BULL` or `TRAIL_EXIT_BEAR` signal, Venus immediately queries `/api/portfolio/tradier`. If we hold the ticker, Venus submits a MARKET sell order to close the position and prevent further losses.

## Implementation Steps

1. **Update Vultr:** Deploy the public webhook receiver endpoint.
2. **Update Venus:** Add the `/api/webhooks/internal` listener or Firebase subscriber.
3. **TradingView Alert:** Set up the alert on the NQ and SPY 5-minute charts. Use the webhook URL `https://mphinance.com/api/webhooks/ghost`. 
4. **Dry Run Validation:** Run the Auto-Trader in `dry_run=true` mode on Monday morning. Verify the logs in `data/trade_log.json` to see if it *would* have caught the A+ setups.
5. **Go Live:** Flip `dry_run=false` for $50 test trades.