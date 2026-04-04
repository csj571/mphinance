# 👻 GHOST_HANDOFF.md — Leveraged Day Trading Backtest Engine v2

## ⚠️ RESUME PRIORITY

1. **Run Full Parameter Sweep** — `python3 -m dossier.backtesting.intraday_backtest --sweep --save docs/ticker/leveraged_backtest_results.json`
   - Engine is v2 with conviction sizing, fallthrough, and full $27K capital
   - Uses pickle cache at `/tmp/yfinance_intraday_cache/` — runs in ~3s with warm cache
   - **Clear cache before sweep:** `rm /tmp/yfinance_intraday_cache/cache.pkl`
2. **Update Playbook Frontend** — Inject sweep results into `docs/leveraged-screener/index.html`
3. **Deploy** — Push to GitHub Pages and rsync landing page to Vultr

---

## What Happened This Session (2026-04-04)

### 1. Quant Diagnostic Completed
- Identified 7 systematic biases causing $8K backtest vs $39K live ($3K/week × 13 weeks)
- Primary issues: capital under-utilization ($18K of $27K), bull-only trading, data gaps

### 2. Bear ETF Experiment (FAILED — Key Finding)
- Implemented direction-aware trading: bear ETFs (TSDD, NVD, MSTZ) on bear-trend days
- **Result: PnL dropped from $10K to -$460**
- **Root cause:** Daily ADX trend ≠ intraday direction. The dip-buy strategy is fundamentally a long-side play. Bear ETFs fight the mean-reversion bounce logic.
- **Reverted to bull-only** with conviction-based sizing (70% position on bear-trend days)

### 3. Engine Overhaul (v2)
- **Full capital:** $27K deployed across 3 equal positions ($9K each)
- **Fallthrough:** When top-3 ETF has no 5m data, try next candidates (pad with +4 extras)
- **Conviction sizing:** Bear-trend days get 70% position size as risk management
- **Preload bug fix:** Fixed wrong dict keys (`bull_2x` → `bull`) in bulk fetcher
- **Underlying fallback:** Trade underlying at 2x size when no bull ETF exists
- **Dynamic pick count:** REMOVED — 3 positions is optimal. 4+ positions dilute the edge.

### 4. Position Count Discovery
| Positions | PnL | Win% | Profit Factor |
|-----------|-----|------|---------------|
| **3** | **$10,096** | **57%** | **1.66** |
| 4 | $5,464 | 53% | 1.32 |
| 5 | $4,057 | 51% | 1.24 |

### 5. SPY ADX Threshold Confirmation
| Threshold | PnL | Days | PF |
|-----------|-----|------|----|
| ≥15 | $8,568 | 57 | 1.38 |
| ≥18 | $5,596 | 52 | 1.26 |
| **≥20** | **$10,096** | **44** | **1.66** |

---

## Final v2 Metrics

```
Period:         2025-11-28 → 2026-04-02 (86 days)
Days traded:    44 / 86 (51%)
Total trades:   132
Total PnL:      $10,096 (+21% vs v1 $8,342)
Win Rate:       57% (trade) / 54% (day)
Avg Daily:      $229
Best Day:       $3,277
Worst Day:      -$1,148
Profit Factor:  1.66
Weeks ≥ $3K:    1/13
```

## Remaining Backtest-vs-Live Gap

$10K/13wk ($775/wk) vs $3K/wk live. Remaining gap is from:
- **DCA:** Michael adds to winners with reserve capital (not modeled)
- **Discretion:** Tape reading, L2 flow, real-time adjustments
- **Entry precision:** Fixed timer vs actual dip detection
- **Skipped days:** 49% skipped in backtest (ADX filter + data gaps)
- **16 no-data days** where yfinance has no 5m candles for newer ETFs

---

## Key Files

| File | Status |
|------|--------|
| `dossier/backtesting/intraday_backtest.py` | ✅ v2 engine — ready for sweep |
| `dossier/data_sources/leveraged_etf_map.py` | ✅ 72 underlyings mapped |
| `dossier/data_sources/leveraged_screener.py` | ✅ TradingView scanner |
| `docs/leveraged-screener/index.html` | ⚠️ Needs updated metrics from sweep |
| `docs/ticker/leveraged_backtest_results.json` | ✅ Saved from v2 run |

---

## What's Left (Actionable)

- [ ] Run `--sweep` with v2 engine to confirm optimal params haven't shifted
- [ ] Update frontend to show v2 metrics
- [ ] Git commit all changes
- [ ] Deploy to GitHub Pages
- [ ] Write Ghost Blog entry for the quant investigation
