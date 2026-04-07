# Ghost Auto-Trader — XSP 0DTE

**Deployed:** March 10, 2026  
**Server:** Venus (192.168.2.172)  
**URL:** https://ghost.mphanko.com

## What It Does

TradingView fires a Ghost Alpha Grade A alert on SPY → webhook hits Venus → Gemini 2.5 Flash AI gate reviews → XSP 0DTE option is bought automatically on Tradier.

Position monitor runs every 30s: **+50% TP**, **-40% SL**, **3:00 PM ET auto-flatten**.

## Key Files

| File | What |
|------|------|
| `alpha-momentum/services/auto_trader.py` | Core engine (chain fetch, strike selection, AI gate, execution, monitoring) |
| `alpha-momentum/api/main.py` | Webhook handler + status endpoint |
| `alpha-momentum/.env` | `AUTO_TRADE_XSP=true` to enable |

## TradingView Alert

**Webhook URL:** `https://ghost.mphanko.com/api/signals/webhook`

**Message:**
```json
{"ticker":"{{ticker}}","tf":"{{interval}}","grade":"{{plot_4}}","signal":"{{plot_5}}","regime":"{{plot_6}}","close":"{{close}}","rvol":"{{plot_7}}"}
```

## Risk Guardrails

- Entry: **9:45 AM – 11:30 AM ET** (prime), hard cutoff **2:30 PM ET**
- Max **2 trades/day**, **$30 max** per position
- Daily loss limit: **$100**
- Target delta: **0.12 – 0.25**
- All times in **Eastern** (code uses `zoneinfo`)

## Quick Commands

```bash
# Check status
curl https://ghost.mphanko.com/api/auto-trade/status

# Trade log
curl https://ghost.mphanko.com/api/auto-trade/log

# Disable
ssh venus "cd ~/alpha-momentum && sed -i 's/AUTO_TRADE_XSP=true/AUTO_TRADE_XSP=false/' .env && docker compose up -d api"

# Re-enable
ssh venus "cd ~/alpha-momentum && sed -i 's/AUTO_TRADE_XSP=false/AUTO_TRADE_XSP=true/' .env && docker compose up -d api"
```
