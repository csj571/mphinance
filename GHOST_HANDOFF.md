# Ghost Handoff — Last Updated 2026-04-30

## What Just Shipped (This Session)

### AlphaClaw Substack Article
- Read the full AlphaClaw GitHub repo (https://github.com/mphinance/AlphaClaw/) and LORE.md in detail
- Wrote the origin story Substack article: `docs/substack/drafts/alphaclaw-rust-android-trading.md`
- Article covers: the RAM failure, remote compilation on Pulse, cargo-ndk cross-compile for arm64, Quick Share transfer, ZeroClaw + tradingview-mcp-rs integration, IBKR as next chapter
- Added Ghost Blog entry (2026-04-30) to `landing/blog/blog_entries.json`

---

## What's Next (When Michael Returns)

### Priority 1 — IBKR Execution Layer
The AlphaClaw article teases IBKR integration as the next chapter. The agent can analyze and grade setups. It can't execute yet. Build the IBKR API connection so the agent can actually trade, not just recommend.

### Priority 2 — TickerTrace Revival
Michael is fixing the TickerTrace scraper. It hasn't run since March 6. Once it's back online, the dossier pipeline will automatically start pulling Institutional Signals again.

### Priority 3 — AlphaClaw Signal to Dossier Pipeline
Wire AlphaClaw's signal output into the Ghost Alpha Dossier pipeline so the daily report picks up mobile-generated signals.

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
