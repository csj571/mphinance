# 👻 GHOST_HANDOFF.md — VWAP Reclaim Algo Trader LIVE

## ⚠️ CURRENT STATE

**The algo bot is LIVE on newvultr.** Systemd service `ghost-vwap-algo` is running in `--live` mode. It will wake up Monday 9:10 AM ET and start trading.

### Quick Commands
```bash
ssh newvultr "journalctl -u ghost-vwap-algo -f"           # Watch live logs
ssh newvultr "systemctl status ghost-vwap-algo"            # Check status
ssh newvultr "systemctl restart ghost-vwap-algo"           # Restart
ssh newvultr "cat /home/mphinance/algo/data/trade_journal.json"  # Trade history
ssh newvultr "cat /home/mphinance/algo/data/wash_sales.json"     # Wash sale blacklist
```

---

## What Happened This Session (2026-04-04 Late Night)

### Algo Bot Built & Deployed
- **`algo/ghost_vwap_algo.py`** — 600-line trading bot implementing the full VWAP Reclaim strategy
- **`algo/config.py`** — Strategy parameters from optimal_config.json
- **`algo/ghost-vwap-algo.service`** — Systemd unit, enabled on boot
- **`algo/deploy.sh`** — One-command deploy script

### Key Design Decisions
1. **50% of actual Tradier balance** — dynamic, not hardcoded ($143.81 → $71.90 trading capital)
2. **Wash sale rule** — per-ticker 30-day blacklist after any losing trade (IRS compliance)
3. **Live from the start** — no dry-run phase, `--live` flag enabled
4. **Discord alerts** — all signals posted to #sam-mph via bot token

### Safety Stack
- SPY ADX ≥ 20 regime filter (from daily.json)
- Grade A/B picks only
- $500 daily loss circuit breaker
- 1.25x ATR trailing stop
- Limit orders at bid (never market)
- Force-close at 3:55 PM ET (no overnight holds)
- Wash sale 30-day blacklist per ticker after losses
- 70% position size on bear-trend days

---

## Key Files

| File | Status |
|------|--------|
| `algo/ghost_vwap_algo.py` | ✅ LIVE on newvultr |
| `algo/config.py` | ✅ Strategy params |
| `algo/deploy.sh` | ✅ One-command deploy |
| `algo/ghost-vwap-algo.service` | ✅ Installed, enabled on boot |
| `algo/data/trade_journal.json` | ✅ Empty, ready for Monday |
| `algo/data/wash_sales.json` | ✅ Empty, no blacklisted tickers |
| `docs/leveraged-screener/daily.json` | ✅ Synced to newvultr as local fallback |

---

## What's Next

- [ ] Fund the Tradier account — $71 ain't gonna cut it
- [ ] Push daily.json into the git pipeline so it deploys to GH Pages automatically
- [ ] Monitor Monday's first live trading day via journalctl
- [ ] Build an algo status page (picks, positions, P&L, wash sale list)
- [ ] Add daily.json sync to the 5AM pipeline cron on newvultr

