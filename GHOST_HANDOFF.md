# Ghost Handoff — Last Updated 2026-04-25

## What Just Shipped (This Session)

### Dossier Template Major Simplification
**Commit:** `8632bb8`

The daily report was 13,000px tall. It's now a fraction of that. Here's what changed in `dossier/report/template.html` (1,320 → 1,100 lines):

- **Removed:** Ghost Dev Log and Sam's Roadmap sections from the daily report. These were showing internal dev notes to paid subs. They still run in the blog pipeline, just not user-facing.
- **Compacted:** Persistence Tracker went from listing 90+ tickers vertically (~2,500px) to pill-style chips showing top 10 Lifers + top 10 High Conviction with an overflow count.
- **Removed:** Full Technical Setups (Tao of Trading) section — the data lives at individual ticker pages, doesn't need to be in the daily.
- **Replaced:** 8 full ticker deep-dive cards (~5,000px with EMA matrices, pivot tables, Fibonacci, oscillator bars, news) with 3 compact cards showing grade + tech/fund score + price + RSI + verdict + "View Deep Dive →" link to the ticker page.
- **Fixed:** Orphaned old ticker card HTML was surgically removed after the initial replacement left it stranded.
- Template validates clean with Jinja2.

**Also still broken in the report (known issues to fix next session):**
- TickerTrace Institutional Signals section is empty — "As of: unknown" — the TickerTrace scraper hasn't run since March 6. Michael is going to fix TickerTrace now.
- Scanner Signal Matrix still shows (it wasn't removed this session) — 15 tickers all showing "CHOP 90-100%" which isn't very actionable. Consider removing or raising the score threshold.
- Market Regime section was rendering a raw Python dict dump previously. The template itself handles it correctly — the issue is in how `market_regime` data flows from `generate.py`. Verify the dict keys match what the template expects.

### New Substack Post Draft
**File:** `docs/substack/musings/2026-04-25_quant-upgrade-post.md`

Post covers:
1. The "stop-at-first-yes" bug present in all 4 old screeners
2. Specific logic changes to each screener: Leveraged (6-factor EdgeScore), CSP (5-factor with conviction tiers), Momentum (Bounce 2.0 pullback detection), LEAPS (combined fundamental + technical score)
3. Multi-model AI code review workflow — running the same quant logic through multiple AI providers simultaneously via OpenRouter, using disagreements between models as a signal
4. Introduction of the Daily Cuts concept (Prime/Choice/Select tiers)
5. Announcement that the dossier got shorter

**Status:** Draft. Needs: hero image, review for voice, then push to Substack via the draft API.

### OpenRouter Models Cached
**File:** `.gemini_scratch/openrouter_models.json`

355 live models as of 2026-04-25 08:10 AM CST. Fetched fresh so future constellation queries use current model IDs instead of deprecated ones. Key current models to use:
- `openai/gpt-4o-mini` — cheap, fast, good for routing/ideas
- `anthropic/claude-3-5-haiku` — Claude's fast tier
- `google/gemini-2.5-flash` — Gemini's current fast model (not 1.5 — deprecated)
- `meta-llama/llama-4-scout` — 327k context, $0.08/1M tokens
- `google/gemini-2.5-pro` — 1M context, $1.25/1M tokens for heavy lifting
- `deepseek/deepseek-r1-0528` — strong reasoning, $0.50/1M tokens

Constellation query scripts:
- `.gemini_scratch/constellation_query.py` — original 3-lane
- `.gemini_scratch/constellation_v2.py` — updated with current models, 4-lane

### Credential Note
- OpenRouter key lives in `/home/mph/Antigravity/tradier/momentum-terminal/.env`
- VaultGuard `OPENROUTER_API_KEY` entry may need updating with this key

---

## What's Next (When Michael Returns)

### Priority 1 — TickerTrace Revival
Michael went to fix the TickerTrace scraper. It hasn't run since March 6. Once it's back:
- Re-wire the TickerTrace → dossier pipeline so Institutional Signals section shows real data
- The dossier template already handles it correctly — it just needs actual data flowing in

### Priority 2 — Daily Cuts Pipeline
The Substack post announces Daily Cuts but the actual code doesn't exist yet. Need to build:
- `dossier/daily_cuts.py` — new module that runs all three screeners and outputs Prime/Choice/Select tiers
- `docs/api/daily-cuts.json` — API endpoint for the cuts
- Wire into `generate.py` as a new stage after momentum_picks
- Add the Daily Cuts HTML section to the template (the 3-column Prime/Choice/Select card block)

### Priority 3 — Substack Post to Production
- Add a hero image (or generate one)
- Final voice check
- Push via Substack draft API

### Priority 4 — Scanner Signal Matrix
Currently shows 15 tickers all at "CHOP 90-100%". Either:
- Remove from daily report entirely
- Or raise the minimum score threshold so only real signals show

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
