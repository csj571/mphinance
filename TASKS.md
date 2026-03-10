---
phase: 02-automation-and-enrichment
type: execute
autonomous: true
---

# mphinance — Flash Task Queue (Phase 2)

Execute each plan in order. Confirm with user after each is complete.

**Python environment:** `/home/sam/Antigravity/empty/mphinance/venv/bin/python3`
**Project root:** `/home/sam/Antigravity/empty/mphinance`

---

## Plan 1: Auto-Backtest & Track Record (Wave 1)

<task type="auto">
  <name>Daily Auto-Backtest Module</name>
  <files>dossier/backtesting/auto_backtest.py, docs/backtesting/track_record.json</files>
  <action>
  Create `dossier/backtesting/auto_backtest.py` that:
  
  1. Reads `docs/daily-picks.json` — this has today's top 10 scored picks
  2. Reads `docs/backtesting/track_record.json` (create if missing, start with `{"entries":[], "stats":{}}`)
  3. For each entry in track_record older than 5 trading days that doesn't have `fwd_5d` yet:
     - Fetch actual close price via yfinance on scan_date and scan_date+5/10/21 trading days
     - Calculate forward returns as percentage
     - Update the entry with fwd_1d, fwd_5d, fwd_10d, fwd_21d
  4. Append today's picks to track_record entries (ticker, date, score, grade, ema_stack, is_pullback)
  5. Recalculate running stats:
     - `avg_5d_return`, `win_rate_5d` (% positive), `total_picks_tracked`, `total_validated`
     - `best_pick` (highest fwd_5d), `worst_pick` (lowest fwd_5d)
     - `sharpe_5d` = mean(fwd_5d) / std(fwd_5d) if std > 0
  6. Save updated `docs/backtesting/track_record.json`
  
  yfinance rate limiting: batch 50, sleep 1s between batches.
  Must work standalone: `python3 dossier/backtesting/auto_backtest.py`
  </action>
  <verify>/home/sam/Antigravity/empty/mphinance/venv/bin/python3 dossier/backtesting/auto_backtest.py</verify>
  <done>track_record.json has new entries and stats object with running metrics</done>
</task>

<task type="auto">
  <name>Track Record Leaderboard Page</name>
  <files>docs/track-record/index.html</files>
  <action>
  Create a dark-themed HTML page at `docs/track-record/index.html`:
  
  1. Fetch `../backtesting/track_record.json` via fetch()
  2. Header section with stats cards:
     - Total picks | Validated | Avg 5d Return | Win Rate | Sharpe
  3. Sortable table: date, ticker, score, grade, ema_stack, 1d/5d/10d/21d returns
     - Green text for positive returns, red for negative
     - Gold highlight for is_pullback rows
     - Gray italic for unvalidated (no returns yet)
  4. Simple SVG line chart showing cumulative 5d return over time
  
  Style (match existing site):

- Background: #0a0e27, panels: rgba(15,20,40,0.8) with border
- Text: #e0e0e0, accent green: #00ff41, gold: #f0b400, red: #e53935
- Font: 'JetBrains Mono', monospace
- No external libraries — vanilla HTML/CSS/JS only
  </action>

  <verify>ls -la docs/track-record/index.html</verify>
  <done>HTML file exists with dark HUD theme, stats cards, sortable table, cumulative chart</done>
</task>

---

## Plan 2: pandas-ta Enrichment Module (Wave 1 — parallel with Plan 1)

<task type="auto">
  <name>Technical Enrichment with pandas-ta</name>
  <files>dossier/data_sources/pandas_ta_enrichment.py</files>
  <action>
  Create `dossier/data_sources/pandas_ta_enrichment.py` that enriches ticker data with pandas-ta:
  
  pandas-ta is installed in the venv. Import: `import pandas_ta as ta`
  
  1. Function `enrich_ticker(ticker: str, period="6mo") -> dict`:
     - Download OHLCV via yfinance
     - Calculate with pandas-ta:
       - `ta.squeeze(df)` → Squeeze indicator (TTM Squeeze)
       - `ta.supertrend(df)` → Supertrend direction
       - `ta.bbands(df)` → Bollinger Band width (volatility measure)
       - `ta.vwap(df)` → VWAP (intraday anchor)
       - `ta.atr(df)` → Average True Range (position sizing)
       - `ta.ichimoku(df)` → Ichimoku cloud (trend confirmation)
       - `ta.rsi(df)` → RSI divergence detection (compare price trend vs RSI trend)
     - Return dict with all computed values as latest readings
  
  2. Function `batch_enrich(tickers: list) -> dict`:
     - Call enrich_ticker for each, with 0.5s sleep between
     - Return {ticker: enrichment_dict}
  
  3. Standalone test:

  ```python
  if __name__ == "__main__":
      result = enrich_ticker("AAPL")
      import json
      print(json.dumps(result, indent=2, default=str))
  ```
  
  Handle missing data gracefully — return None for indicators that fail.
  </action>
  <verify>/home/sam/Antigravity/empty/mphinance/venv/bin/python3 dossier/data_sources/pandas_ta_enrichment.py</verify>
  <done>Prints enrichment dict for AAPL with squeeze, supertrend, bbands etc.</done>
</task>

---

## Plan 3: Regime-Aware Pick Annotations (Wave 2 — after Plan 1)

<task type="auto">
  <name>Regime-Aware Daily Picks</name>
  <files>dossier/momentum_picks.py (MODIFY — only the _save_picks function)</files>
  <action>
  In `dossier/momentum_picks.py`, modify ONLY the `_save_picks()` function to include regime context.
  
  The function currently saves `docs/daily-picks.json`. Add these fields to the JSON:
  
  ```python
  # At the top of _save_picks, add:
  # Try to get current regime
  regime_data = {}
  try:
      from dossier.market_regime import detect_regime
      regime_data = detect_regime()
  except:
      pass
  
  # Then in the output dict, add:
  "market_regime": {
      "regime": regime_data.get("regime", "UNKNOWN"),
      "vix": regime_data.get("vix", 0),
      "hedge_suggestions": regime_data.get("hedge_suggestions", []),
  }
  ```
  
  Also annotate each pick with a `regime_note` field:

- If regime is FEAR/PANIC: `"⚠️ High VIX — reduce size, tighten stops"`
- If regime is ELEVATED: `"🟡 Caution — prefer pullback setups only"`
- If regime is CALM/NORMAL: `"✅ Market favorable for momentum entries"`
  
  DO NOT modify the scoring logic. Only modify `_save_picks()`.
  </action>
  <verify>/home/sam/Antigravity/empty/mphinance/venv/bin/python3 -c "import json; d=json.load(open('docs/daily-picks.json')); print(d.get('market_regime', 'NOT ADDED YET'))"</verify>
  <done>daily-picks.json includes market_regime object and each pick has regime_note</done>
</task>

---

## Plan 4: Venus Scanner History Auto-Ingest (Wave 2)

<task type="auto">
  <name>Auto-Sync Scanner History from Venus</name>
  <files>dossier/backtesting/sync_venus.py</files>
  <action>
  Create `dossier/backtesting/sync_venus.py`:
  
  1. SCP the latest *_History.csv files from Venus:
     Source: `venus:/home/mnt/Download2/docs/Momentum/anti/scheduling/scans/*_History.csv`
     Dest: `data/screens_history/`
  
  2. After sync, print diff: how many new rows/dates compared to local files
  
  3. Function `sync_from_venus() -> dict`:
     - Use subprocess to run scp
     - Compare before/after row counts
     - Return {"synced": True, "new_rows": 42, "new_dates": 3}
  
  4. Function `ingest_to_backtest()`:
     - After sync, automatically run `screens_backtest.py` to re-score with latest data
  
  Handle SSH errors gracefully (Venus might be offline).
  
  SSH config: ssh alias `venus` is already in ~/.ssh/config (192.168.2.172, user mph)
  
  Standalone: `python3 dossier/backtesting/sync_venus.py`
  </action>
  <verify>/home/sam/Antigravity/empty/mphinance/venv/bin/python3 -c "from dossier.backtesting.sync_venus import sync_from_venus; print(sync_from_venus())"</verify>
  <done>Script syncs CSVs from Venus and reports new data counts</done>
</task>

---

## Plan 5: Social/Twitter Daily Picks Formatter (Wave 2)

<task type="auto">
  <name>Daily Picks Social Media Formatter</name>
  <files>dossier/social_formatter.py</files>
  <action>
  Create `dossier/social_formatter.py` that formats daily picks for social sharing:
  
  1. Function `format_twitter_thread(picks_json_path="docs/daily-picks.json") -> list[str]`:
     - Read the daily-picks.json
     - Generate a thread of tweets (each ≤280 chars):

     Tweet 1 (header):

     ```
     ⚡ MOMENTUM PICKS — {date}
     
     Market: {regime} (VIX {vix})
     
     Today's top setups scored by our 9-factor ML-calibrated algorithm 🧵👇
     ```

     Tweet 2-4 (Gold/Silver/Bronze):

     ```
     🥇 ${ticker} — Score: {score}/100
     
     EMA: {ema_stack} | ADX: {adx} | RSI: {rsi}
     {regime_note}
     
     Key: {breakdown summary}
     ```

     Tweet 5 (track record):

     ```
     📊 Track Record: {win_rate}% win rate over {days} days
     Avg 5d return: {avg}%
     
     Full analysis: mphinance.com
     ```
  
  2. Function `format_discord_embed(picks_json_path) -> dict`:
     - Return a Discord webhook-compatible embed dict
  
  3. Standalone: prints the thread to stdout
  </action>

  <verify>/home/sam/Antigravity/empty/mphinance/venv/bin/python3 dossier/social_formatter.py</verify>
  <done>Prints formatted Twitter thread with today's picks and regime context</done>
</task>

---

## Rules

- Execute plans in order, but Plans 1 and 2 can run in parallel (Wave 1)
- Plans 3-5 depend on Plan 1 (Wave 2)
- Use the venv Python, not system Python
- If yfinance rate-limits, add `time.sleep(1)` between batches
- Commit each plan with emoji-prefixed message when done
- Pause and confirm with user between plans
