---
phase: 02-automation
type: execute
wave: 1
depends_on: []
autonomous: true
requirements: ["auto-backtest", "track-record"]
must_haves:
  truths:
    - "Backtest auto-runs at end of pipeline and appends to rolling track record"
    - "Track record page shows 90-day rolling leaderboard on GH Pages"
  artifacts:
    - path: "dossier/backtesting/auto_backtest.py"
      provides: "Daily auto-backtest that scores today's picks and logs previous picks' outcomes"
      min_lines: 80
    - path: "docs/track-record/index.html"
      provides: "Rolling leaderboard showing daily picks vs actual returns"
      min_lines: 60
---

<objective>
Automate backtesting as part of the daily pipeline and publish a rolling track record.

Purpose: Build public proof that the momentum scorer works. Every day's picks get validated against actual returns.
Output: Auto-backtest module + public track record page.
</objective>

<context>
Python environment: /home/sam/Antigravity/empty/mphinance/venv/bin/python3
Project root: /home/sam/Antigravity/empty/mphinance

Key files:

- dossier/generate.py — 13-stage dossier pipeline, runs daily at 6AM CST
- dossier/momentum_picks.py — 9-factor scorer (ML-calibrated weights as of today)
- dossier/backtesting/screens_backtest.py — existing backtest against historical screens
- docs/backtesting/screens_backtest.json — backtest results
- docs/daily-picks.json — daily API output with top 10 picks

Existing backtest results (for reference):

- 827 scored, 754 with returns, 25 days
- High 70+ = +1.9% avg, 66% win rate  
- Gold pick 10-day = +1.8% avg, 70% win rate
</context>

<tasks>

<task type="auto">
  <name>Plan 1: Auto-Backtest Module</name>
  <files>dossier/backtesting/auto_backtest.py</files>
  <action>
  Create a module that:
  
  1. Reads `docs/daily-picks.json` for today's scored picks (top 10)
  2. Reads `docs/backtesting/track_record.json` for the rolling log of previous picks
  3. For picks that are 5+ trading days old, fetch their actual forward returns via yfinance
  4. Append validated entries to the track record with: ticker, date, score, predicted_grade, fwd_1d, fwd_5d, fwd_10d, fwd_21d
  5. Calculate running stats: avg_return_5d, win_rate_5d, sharpe_ratio, best_pick, worst_pick
  6. Save updated `docs/backtesting/track_record.json`
  
  Make it work as both standalone AND importable:

  ```python
  if __name__ == "__main__":
      update_track_record()
  ```
  
  Rate limiting: batch 50 tickers with 1s sleep between batches.
  </action>
  <verify>/home/sam/Antigravity/empty/mphinance/venv/bin/python3 dossier/backtesting/auto_backtest.py</verify>
  <done>track_record.json exists and contains validated entries with forward returns</done>
</task>

<task type="auto">
  <name>Plan 2: Track Record Leaderboard Page</name>
  <files>docs/track-record/index.html</files>
  <action>
  Create a dark-themed HTML page that fetches and displays the track record:
  
  1. Reads `../backtesting/track_record.json` via fetch
  2. Shows summary stats at top: total picks tracked, avg 5d return, win rate, sharpe
  3. Sortable table of all picks: date, ticker, score, grade, 1d/5d/10d/21d returns
  4. Color-code returns (green positive, red negative)
  5. Chart showing cumulative return over time (simple SVG or canvas line)
  6. Match the existing site style (dark HUD terminal aesthetic)
  
  Style requirements:

- Background: #0a0e27
- Text: white/gray  
- Accent: #00ff41 (green), #f0b400 (gold), #e53935 (red)
- Font: monospace
- No external libraries — vanilla HTML/CSS/JS only
  </action>

  <verify>ls -la docs/track-record/index.html</verify>
  <done>HTML page loads and displays track record data in dark HUD style</done>
</task>

</tasks>

<verification>
Before declaring complete:
- [ ] auto_backtest.py runs standalone without errors
- [ ] track_record.json is valid JSON with entry structure
- [ ] index.html renders in browser with dark theme and data table
- [ ] No modifications to existing files
</verification>

<success_criteria>

- Both plans completed
- Output files exist and pass verification
- Commit with descriptive emoji-prefixed message
</success_criteria>

<output>
You may pause and confirm with the user after each plan is complete.
Commit your work with a descriptive emoji-prefixed message when done.
</output>
