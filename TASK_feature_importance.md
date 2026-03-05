# Subagent Task: Feature Importance Analysis

## Goal

Run a scikit-learn random forest on the backtest data to determine which of the 9 scoring factors best predict 5-day forward returns.

## Context

- Backtest results are in: `docs/backtesting/screens_backtest.json`
- The `top_50_entries` field has per-entry data with `score`, `ema_stack`, `rsi`, `adx`, `is_pullback`, `fwd_5d`, `fwd_10d`
- Historical screen CSVs are in: `data/screens_history/` (full technicals for each scan)
- The scoring function is in: `dossier/momentum_picks.py` → `score_momentum()`
- Current 9 factors: `ema_stack`, `pullback`, `adx`, `rsi`, `trend`, `rel_vol`, `price_vs_ema`, `macd`, `institutional`

## Steps

1. Load all History CSVs from `data/screens_history/` (skip `Fake_Strategy_History.csv`)
2. For each row, extract features: `ADX`, `RSI`, `Stoch_K`, `relative_volume_10d_calc`, `close`, EMA values (8/21/34/55/89)
3. Calculate derived features:
   - `ema_aligned` = 1 if EMA8 > EMA21 > EMA34 > EMA55 > EMA89, else 0
   - `pct_from_ema21` = (close - EMA21) / EMA21 * 100
   - `stoch_oversold` = 1 if Stoch_K < 40
   - `adx_strong` = 1 if ADX > 25
4. Use yfinance to fetch 5-day and 10-day forward returns for each (ticker, scan_date) pair
   - NOTE: Use batches of 50, add `import time; time.sleep(1)` between batches to avoid rate limiting
5. Train a RandomForestClassifier to predict `positive_5d_return` (binary: did the stock go up in 5 days?)
6. Output feature importances ranked
7. Save results to `docs/backtesting/feature_importance.json`:

   ```json
   {
     "features_ranked": [{"name": "adx", "importance": 0.23}, ...],
     "accuracy": 0.67,
     "n_samples": 400,
     "date_range": "2026-02-06 to 2026-03-04"
   }
   ```

## Python Environment

Use the venv: `/home/sam/Antigravity/empty/mphinance/venv/bin/python3`

## Output

- `docs/backtesting/feature_importance.json` — feature importance rankings
- Print a summary to stdout
