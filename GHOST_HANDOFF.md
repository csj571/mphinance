# Ghost Handoff — Last Updated 2026-04-25

## What Just Shipped (This Session)

### Daily Cuts Pipeline & Template Overhaul
- **Built `dossier/daily_cuts.py`**: A new extraction engine that runs all screeners and isolates the single best Momentum trade, CSP setup, and Leveraged ETF play, assigning them Prime/Choice/Select conviction tiers.
- **Wired into `generate.py`**: Injected as Stage 8f in the pipeline, seamlessly passing the new payload down to the template builder.
- **Template Gutted & Upgraded (`template.html`)**: Removed the massive legacy data grids (Daily Momentum Picks, Leveraged ETF Play, Scanner Signals Matrix, Technical Setups, and CSP Setups). The report is now sleek and punchy.
- **Paywall Positioning**: Inserted the new 3-card `DAILY CUTS` section **immediately below the paywall**, ensuring the most actionable, high-conviction trades are gated for premium subscribers. 

### Substack Post Polished & Pushed
- Fixed the GitHub Pages deployment bug by stripping out symlinks (`latest.md` and `latest_hero.png`) and replacing them with physical file copies of the post and hero image, ensuring the permalink resolves correctly.
- Pipeline pushed the post to the Substack drafts via API successfully.

### Pipeline Validated & Deployed
- Ran a full execution of the Alpha Dossier pipeline (`python -m dossier.generate --no-pdf`).
- It successfully pulled 192 signals, finalized the cuts (Gold: PNC, Silver: ACGL, Bronze: HIG), generated the streamlined HTML, and pushed all updates to GitHub Pages.

---

## What's Next (When Michael Returns)

### Priority 1 — TickerTrace Revival
Michael is fixing the TickerTrace scraper. It hasn't run since March 6. In the latest pipeline run, TickerTrace retried 3 times for each ticker and timed out (which gracefully falls back but adds 2-3 minutes to the pipeline execution).
- Once it's back online, the dossier pipeline will automatically start pulling Institutional Signals again. No pipeline changes needed.

### Priority 2 — Scanner Matrix & Status Check
- Keep an eye on the `docs/reports/latest.html` layout on mobile to make sure the new Daily Cuts cards wrap cleanly. 
- You may want to review if any other legacy metrics need stripping out from the individual ticker pages now that the daily report has been condensed.

---

## Don't Break
- `docs/ticker/*/deep_dive.*` files — NEVER delete (expensive AI-generated reports)
- The Relay bank CSVs in `financials/` — source of truth for reconciliation
- The sequential 50/30/20 formula — brokerage and paycheck off gross, tax is 30% of post-payroll remainder
- The dossier pipeline runs 5AM CST weekdays via GitHub Actions — don't push broken generate.py

---

## Previous Handoff Context (Q1 2026 — still relevant)

### Q1 2026 Earnings Report
- Article at `docs/articles/q1-2026-earnings/README.md` — Substack-ready
- 10 infographics in same directory
- Paywall after "The Crossover" section

### Financial Reconciliation
- All Relay CSVs reconciled through Apr 2026
- Tax reserve ahead of target, brokerage and paycheck on track
- 50/30/20 formula is sequential: 50% brokerage + 20% paycheck off gross, then 30% of remainder to tax, ~6% gap = R&D reserve

### Key Numbers (Q1 close, Mar 31)
- Checking #6604: $252.55
- Savings #6605: $597.82 (tax, ahead of target)
- Tastytrade NLV: $945.27
- All-time net revenue: $2,456.71
