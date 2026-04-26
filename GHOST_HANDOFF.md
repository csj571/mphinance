# Ghost Handoff — Last Updated 2026-04-25

## What Just Shipped (This Session)

### Substack Post Finalized & Enhanced
- **"Bucket Swap" Narrative**: Clarified the financial move of transferring $1,000 from Relay savings into Interactive Brokers (operations) and re-designating Tastytrade as the SGOV tax bucket.
- **Decay Derby Tracker UI**: Overhauled the UI logic to seamlessly transition assigned puts into active wheels without throwing "expiring" alerts.
- **End-of-Week Derby Update**: Wrote the Decay Derby standings and embedded a fresh Playwright screenshot of the dashboard directly into the draft (`docs/substack/images/2026-04-26_decay_derby_dashboard.png`).
- **Paywall Section**: Ran the Alpha Dossier pipeline to find a high-conviction trade. The pipeline surfaced Kinross Gold Corporation (KGC) with a Grade A setup, full bullish EMA stack, and a Momentum Squeeze Fire (SQZ FIRE) trigger. Added this deep-dive analysis behind the paywall.

### Pipeline
- The pipeline ran successfully and generated the Alpha Dossier reports in `docs/reports/2026-04-26_alpha_dossier.md` (and `.html`).

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
