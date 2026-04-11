# Ghost Handoff — Last Updated 2026-04-11

## What Just Shipped

### Q1 2026 Earnings Report (The Phund)
- **Article**: `docs/articles/q1-2026-earnings/README.md` — ready to copy-paste to Substack
- **10 infographics** in same directory (hero, income statement, balance sheet, capital allocation, subscriber metrics, brokerage performance, trading recommendations, Q2 guidance, pick scorecard teaser, contributions vs returns)
- **Paywall** placed after "The Crossover" section. Free readers get full financials. Paid subs get live portfolio, R&D output, Q2 guidance, and the R&D Reserve vote.
- **New section**: "The R&D Reserve: You Decide" — 5 options for paid subs to vote on infrastructure spend

### Financial Reconciliation (Bank-Verified)
- Ran full reconciliation against all Relay bank CSVs (Dec 2025 through Apr 2026)
- **Fixed `revenue_stats.json`**: Tax savings was overstated by $154 (planned correction never executed). Corrected from $751.88 to $597.82 (actual bank balance)
- Tax target corrected to $589.61 (30% of post-payroll, not 30% of gross)
- Actually **$8.21 AHEAD** of target, not $81 behind
- All allocations reconcile: Brokerage ✅ ahead, Paychecks ✅ on target, Tax ✅ ahead

### Dashboard Update (mphinance.com)
- 4th allocation bucket renamed from "Unallocated" (grey) to "R&D Reserve" (cyan)
- Label: "~6% of net" / "infrastructure fund"
- JS updated to read `rd_reserve` with fallback to `unallocated`
- **Deployed to Vultr** — live at mphinance.com

### Key Financial Numbers (as of Q1 close, Mar 31)
- Checking #6604: $252.55 (R&D reserve float)
- Savings #6605: $597.82 (tax reserve, ahead of target)
- Tastytrade NLV: $945.27 ($1,284 deposited, -18.2% stock, $144 premium collected)
- All-time net revenue: $2,456.71
- The 6% R&D gap is INTENTIONAL — infrastructure budget to replace out-of-pocket costs

### The 50/30/20 Formula (Sequential)
- 50% brokerage off the top
- 20% paycheck off the top
- 30% of remainder (post-paycheck) to tax
- ~6% gap = R&D reserve
- On $100: $50 + $20 + $24 + $6 = $100

## What's Next
- **Pick Scorecard article** — next Friday, reviewing every Q1 ticker call
- **TraderDaddy.pro integration** — TickerTrace signals getting wired in this weekend
- **`fetch_revenue.py` needs refactoring** — currently only calculates 50% brokerage. Should compute full 50/30/20 allocation with the correct sequential formula and update JSON without overwriting manual fields
- **Blog entry** still needs to be written for this session

## Don't Break
- `docs/ticker/*/deep_dive.*` files — NEVER delete
- The Relay bank CSVs in `financials/` — source of truth for reconciliation
- The sequential 50/30/20 formula — brokerage and paycheck off gross, tax is 30% of post-payroll remainder
