# 👻 GHOST_HANDOFF.md — Leveraged Day Trading Backtest Engine

## ⚠️ RESUME PRIORITY FOR TOMORROW

1. **Verify the Leveraged ETF Backtest Sweep** — Run `python3 -m dossier.backtesting.intraday_backtest --sweep --save docs/ticker/leveraged_backtest_results.json`
   - *Note:* The script was hanging today because of a Yahoo Finance rate limit triggered by sequential looping over 140+ individual `yf.download` calls in the Sweep phase. We added a permanent `pickle` filesystem cache, but because the cache was empty, it was hanging while fetching the initial dataset.
2. **Optimize Data Fetch** — If it still hangs on empty cache, we need to convert the `for t in tickers: yf.download(...)` loop inside `intraday_backtest.py` into a single batched call: `yf.download(" ".join(tickers), ...)` to bypass Yahoo IP blocks.
3. **Commit the System** — Once parameters validate the $3K/week profit hypothesis (or show us how to adjust position sizing), push the `leveraged_screener.py`, `leveraged_etf_map.py`, and `docs/leveraged-screener/` diary page updates to GitHub.
4. **Deploy the Diary** — Push to `gh-pages` so the live site reflects the 2x strategy.

---

## What Happened This Session

### 1. Intraday Backtest Engine Created
- Built `dossier/backtesting/intraday_backtest.py` to validate "The $3K/Week Playbook" rules.
- Simulates minute-level executions on 2x ETFs using yfinance 5m candles.
- Includes SPY ADX regime filtering, +X min entry dips, and ATR trailing stop logic.

### 2. Baseline Test Run
- First baseline run with 1x ATR and 9:30+30m entry worked (13 weeks data).
- Found that default rules were skipping *too many* days initially (signal cap of 25 was blowing up because daily ADX naturally produces more signals than intraday).
- Updated defaults: `min_pick_adx=15` and `signal_cap=999`. Reran: generated +$7,252 P&L, 56% win rate, 1.66 profit factor... but 0 weeks hit the strict $3K target with baseline sizing.

### 3. Parameter Sweep Bottleneck
- Triggered `--sweep` flag to compute optimums for: entry timing, ATR distance, SPY threshold, signal count cap, and position sizing.
- Python process seemingly deadlocked repeatedly.
- Root Cause: Sequential loop fetching 72 daily candles + 72 5-min candles triggered a quiet rate-limit block from Yahoo Finance (`urllib3` connection pooling freeze).
- Mitigation: Embedded a file-based `pickle` caching mechanism (`_DATA_CACHE`) stored manually at `/tmp/yfinance_intraday_cache` to shield future iterations from duplicate network calls.

---

## Key Files Changed

| File | What |
|------|------|
| `dossier/backtesting/intraday_backtest.py` | NEW file: Full intraday system + trailing stop + parameter sweep |
| `dossier/data_sources/leveraged_etf_map.py` | Built master index mapping 72 underlyings to bullish/bearish 2x ETFs |
| `dossier/data_sources/leveraged_screener.py` | Built multi-TF (15M/1H) scanner hitting TradingView API |
| `docs/leveraged-screener/index.html` | The Playbook front-end with responsive layout |

---

## What's Left For Tomorrow (Actionable)

- [ ] Re-run the sweep and populate `docs/ticker/leveraged_backtest_results.json`
- [ ] If hanging persists, batch `yf.download` calls in `fetch_daily_data`
- [ ] Update frontend to inject these sweep numbers dynamically into the diary HTML
- [ ] Run `git add` for all the uncommitted `leveraged_*` files
- [ ] Deploy new Playbook / Trading Diary rules 
