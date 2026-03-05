---
phase: 01-level-up
type: execute
wave: 1
depends_on: []
autonomous: true
requirements: ["ML-scoring", "crash-hedging", "pine-indicator"]
must_haves:
  truths:
    - "market_regime.py prints current VIX regime and hedging suggestions"
    - "feature_importance.json shows ranked scoring factors with accuracy"
    - "bounce2_indicator.pine compiles in Pine Script v6"
  artifacts:
    - path: "dossier/market_regime.py"
      provides: "VIX regime detection and hedging module"
      min_lines: 80
    - path: "docs/backtesting/feature_importance.json"
      provides: "ML analysis of which scoring factors predict returns"
    - path: "docs/pine/bounce2_indicator.pine"
      provides: "Bounce 2.0 TradingView indicator"
      min_lines: 100
---

<objective>
Level up the mphinance momentum trading screener with ML analysis, crash detection, and TradingView presence.

Purpose: Turn our 9-factor scoring system into the most complete, validated, and automated momentum screener.
Output: VIX regime module, ML feature rankings, Pine Script indicator.
</objective>

<context>
Python environment: /home/sam/Antigravity/empty/mphinance/venv/bin/python3
Project root: /home/sam/Antigravity/empty/mphinance

Key files:

- dossier/momentum_picks.py — 9-factor momentum scorer (score_momentum function)
- dossier/quality_filter.py — SPAC/penny/bio/shell detector
- data/screens_history/ — Historical scanner CSVs from Venus (37 days, Feb 6 → Mar 4)
- docs/backtesting/screens_backtest.json — Existing backtest results (827 scored entries)
</context>

<tasks>

<task type="auto">
  <name>Plan 1: VIX Regime & Crash Detection Module</name>
  <files>dossier/market_regime.py</files>
  <action>
  Read TASK_vix_regime.md for full specs. Create dossier/market_regime.py that:
  
  1. Uses yfinance to fetch ^VIX, ^VIX3M, ^VVIX, SPY
  2. Classifies market into: CALM (VIX<15), NORMAL (15-20), ELEVATED (20-25), FEAR (25-35), PANIC (>35)
  3. Computes VIX/VIX3M ratio (backwardation = fear signal)
  4. Checks SPY vs 20/50/200 SMA
  5. Returns regime + hedge suggestions + market context string
  
  Must run standalone: python3 dossier/market_regime.py → prints current regime
  </action>
  <verify>/home/sam/Antigravity/empty/mphinance/venv/bin/python3 dossier/market_regime.py</verify>
  <done>Module prints current VIX regime, hedge suggestions, and market context. No errors.</done>
</task>

<task type="auto">
  <name>Plan 2: ML Feature Importance Analysis</name>
  <files>docs/backtesting/feature_importance.json</files>
  <action>
  Read TASK_feature_importance.md for full specs. Write a script that:
  
  1. Loads History CSVs from data/screens_history/ (skip Fake_Strategy_History.csv)
  2. For each row, extracts features: ADX, RSI, Stoch_K, relative_volume_10d_calc, EMA alignment
  3. Fetches 5-day forward returns via yfinance (batch 50, sleep 1s between batches)
  4. Trains RandomForestClassifier to predict positive_5d_return (binary)
  5. Saves feature importances to docs/backtesting/feature_importance.json:
     {"features_ranked": [{"name": "adx", "importance": 0.23}], "accuracy": 0.67, "n_samples": 400}
  
  Use scikit-learn from the venv.
  </action>
  <verify>cat docs/backtesting/feature_importance.json | python3 -m json.tool</verify>
  <done>feature_importance.json exists with ranked features and accuracy score</done>
</task>

<task type="auto">
  <name>Plan 3: TradingView Pine Script — Bounce 2.0</name>
  <files>docs/pine/bounce2_indicator.pine</files>
  <action>
  Read TASK_pine_script.md for full specs. Write Pine Script v6 that:
  
  1. Plots EMA ribbon: 8 (cyan), 21 (yellow), 34 (orange), 55 (red), 89 (purple)
  2. Detects Bounce 2.0: FULL BULLISH stack + ADX>=25 + Stoch_K<=40 + price near EMA21
  3. Shows "⚡ B2.0" label below bar when signal fires
  4. Adds alertcondition() for alerts
  5. Score table in top-right showing factor breakdown
  
  indicator("Bounce 2.0 — mph1nance", overlay=true)
  </action>
  <verify>cat docs/pine/bounce2_indicator.pine | head -5</verify>
  <done>Pine Script file exists with v6 header, EMA plots, and Bounce 2.0 detection</done>
</task>

</tasks>

<verification>
Before declaring complete:
- [ ] dossier/market_regime.py runs and prints current regime
- [ ] docs/backtesting/feature_importance.json is valid JSON with feature rankings
- [ ] docs/pine/bounce2_indicator.pine has Pine Script v6 header and compiles conceptually
- [ ] No modifications to existing files (momentum_picks.py, quality_filter.py, etc.)
</verification>

<success_criteria>

- All three plans completed independently
- Each output file exists and passes its verification check
- Git commit with descriptive emoji-prefixed message
</success_criteria>

<output>
You may pause and confirm with the user after each plan is complete.
Commit your work with a descriptive emoji-prefixed message when done.
</output>
