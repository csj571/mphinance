# 🎯 0DTE Day Trading Flow — Monday Ready

> **For Michael's Monday morning session.**
> Ghost Alpha signals → Tradier 0DTE SPY/QQQ options → Same-day close.
> **Authors:** Claude + Gemini (collaborative design)

---

## Why This Works on Tradier

The AUTO_TRADE_PLAN marked 0DTE as "aspirational" because it assumed SPX index options (futures broker required). But **SPY and QQQ have 0DTE options expiring M/W/F** and Tradier supports them fully. Standard ETF options — `class=option` in the API. No new broker needed.

---

## The Flow

```
 SIGNAL          ENTRY              MANAGE              EXIT
┌──────┐    ┌──────────┐    ┌─────────────────┐    ┌──────────┐
│Ghost │    │BTO 0DTE  │    │+50% TP          │    │STC by    │
│Alpha │───→│ATM Call  │───→│-40% SL          │───→│3:00 PM   │
│A+/A  │    │or Put    │    │Ghost Trail watch│    │MANDATORY │
└──────┘    └──────────┘    └─────────────────┘    └──────────┘
```

### Step by Step

1. **PRE-MARKET (9:00 AM ET):** Open Ghost Alpha on SPY 5min. Check Grade V2 ≥ B and REGIME is BULL/BEAR (not CHOP).

2. **SIGNAL (9:30–11:30 AM ET):** Ghost Alpha fires `mega_bull` or `mega_bear` with Grade A+/A. RVOL > 1.5. Trend age < 10 bars (FRESH).

3. **ENTRY:** BUY TO OPEN 0DTE option. CALL if mega_bull, PUT if mega_bear. ATM or 1 strike OTM. LIMIT order at mid-price. Max $100/trade.

4. **MANAGE:** Trail using Ghost Trail on chart. Take profit at +50%. Stop loss at -40%. If Grade drops to D/F → CLOSE immediately.

5. **EXIT:** SELL TO CLOSE all 0DTE by **3:00 PM ET**. No exceptions. No holding to expiration.

---

## Risk Guardrails (NON-NEGOTIABLE)

| Rule | Value |
|------|-------|
| Max per trade | $100 |
| Max daily loss | $200 (walk away after 2 losers) |
| Max open positions | 1 (0DTE only, focus > diversification) |
| Auto-close time | 3:00 PM ET |
| No averaging down | EVER |
| Grade minimum | B (3.0/5) |
| Trading window | 9:30–11:30 AM ET only |
| Friday 0DTE | NO (triple witching risk) |
| Dry run first | ALWAYS test the flow before live |

---

## Tradier API — Option Orders

### Get Today's 0DTE Chain
```bash
curl -s -H "Authorization: Bearer $TRADIER_TOKEN" \
  "https://api.tradier.com/v1/markets/options/chains?symbol=SPY&expiration=$(date +%Y-%m-%d)"
```

### Buy to Open (0DTE Call)
```bash
curl -s -X POST -H "Authorization: Bearer $TRADIER_TOKEN" \
  "https://api.tradier.com/v1/accounts/$ACCOUNT_ID/orders" \
  -d "class=option&symbol=SPY&option_symbol=SPY260310C00570000&side=buy_to_open&quantity=1&type=limit&price=1.50&duration=day"
```

### Sell to Close
```bash
curl -s -X POST -H "Authorization: Bearer $TRADIER_TOKEN" \
  "https://api.tradier.com/v1/accounts/$ACCOUNT_ID/orders" \
  -d "class=option&symbol=SPY&option_symbol=SPY260310C00570000&side=sell_to_close&quantity=1&type=limit&price=2.25&duration=day"
```

### Option Symbol Format
`SPY260310C00570000` = SPY, 2026-03-10, Call, $570 strike

---

## What Exists vs What's Needed

### ✅ Already Built
- Tradier API integration (Venus `services/tradier_service.py`)
- Market clock, quotes, trade preview/execute endpoints
- Trade journal (`/api/auto-trade/log`)
- Ghost Alpha v6.2 + Grade V2 signals
- Webhook JSON payload in Pine Script

### 🔲 Needs Building (for full automation)
| Component | Priority |
|-----------|----------|
| Options chain endpoint on Venus | HIGH |
| Option order endpoint (`buy_to_open`/`sell_to_close`) | HIGH |
| Auto-close cron at 3:00 PM ET | HIGH |
| Webhook receiver on Vultr | MEDIUM |
| `scripts/zero_dte_runner.py` orchestrator | MEDIUM |

### 🟢 Monday Workaround (No Code Required)
Michael can trade 0DTE **manually** on Monday using Ghost Alpha signals + the Tradier web app. The flow:
1. Watch Ghost Alpha dashboard on SPY 5min
2. When Grade A+/A fires with mega signal → open Tradier, buy 0DTE option manually
3. Watch Ghost Trail for exit → sell on Tradier
4. Close everything by 3:00 PM ET

This lets us **validate the signals work live** before automating execution.

---

## Monday Morning Checklist

- [ ] Venus running: `curl http://192.168.2.172:8100/api/health`
- [ ] Tradier buying power: `curl http://192.168.2.172:8100/api/portfolio/tradier`
- [ ] Ghost Alpha loaded on SPY 5min in TradingView
- [ ] Grade V2 on open: if F/D → sit on hands
- [ ] First mega signal → check 0DTE chain on Tradier
- [ ] Enter if premium $0.50–$2.00 and Grade ≥ B
- [ ] Screenshot entry for blog
- [ ] Close all by 3:00 PM ET
- [ ] Log results

---

*"0DTE options are like Mike Tyson — they can make you rich in 5 minutes or knock you out in 3. The difference is whether you have a plan when you walk in the ring." — Sam 👻*
