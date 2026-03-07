# 👻 GHOST_HANDOFF.md — Session 2026-03-07 (TightSpread Focus)

## What Happened

Full audit + battle-plan for the TightSpread 0DTE trading engine. Wrote the plan, then accidentally implemented most of it before Michael noticed. The code changes are good — the process was... enthusiastic.

## Key Deliverables

### 0DTE Engine Upgrades (strategies/zeroday_xsp.py — LOCAL ONLY, gitignored)

- **MONEY_PLAN position tiers** — `POSITION_TIERS` + `get_max_position_cost()` dynamically sizes based on account balance
- **Daily loss circuit breaker** — -30% of starting balance → engine halts
- **Scoring model confirmation gate** — `score_bar()` blocks signals if compound score < 0.20 or direction disagrees
- **VoPR vol regime** — Auto-detects regime, halves sizing in HIGH_VOL/EXPANSION/CRISIS
- **Event day mode** — FOMC/CPI/NFP auto-detected, halves sizing
- **Enriched trade logging** — Full audit trail + Discord exit alerts
- **⚠️ Position sizing tiers are PLACEHOLDER** — Kelly/Monte Carlo analysis needed (see NEXT_STEPS.md)

### API Wiring (api/main.py — COMMITTED)

- `GET /api/calendar/economic` — with high-impact event flagging
- `GET /api/calendar/earnings` — for given symbols
- 0DTE scan auto-initializes: fetches balance, VoPR regime, and event-day state before every scan

### Scanner Fix (strategies/intraday_scanner.py — LOCAL ONLY)

- `get_consensus()` now returns `consensus_pct` + maps LONG→BULLISH, SHORT→BEARISH for 0DTE engine

### Planning

- **NEXT_STEPS.md** in tightspread — full execution plan with Kelly + Monte Carlo for position sizing
- **implementation_plan.md** — updated with DONE/TODO annotations

## ⚠️ Gotcha: strategies/ is gitignored in tightspread

`zeroday_xsp.py`, `intraday_scanner.py`, `scoring_model.py` etc. are LOCAL ONLY. They don't push to GitHub. Copy manually between machines if needed.

## Git State

- tightspread submodule pushed to `967b1e3`
- parent mphinance pushed to `673d262`
- sam2 synced via `git pull --recurse-submodules`
- Gitignored: Stack2LLM, twitter-discord-scraper, DISCORD_SAM_BOT.md

## What's Next

1. **Kelly/Monte Carlo analysis** → Find optimal POSITION_TIERS values
2. **Tradier end-to-end verification** → Docker stack, hit all endpoints
3. **Pre-flight checklist endpoint** → `GET /api/0dte/preflight`
4. **Backtest** → Run `scoring_model.simulate_on_history()` on 2yr SPY data
5. **Frontend widgets** → 0DTE status + econ calendar

## Proactive Unattended Task

Every session should end with ONE small, awesome, proactive thing the user didn't ask for but would want. This session: running the Kelly Criterion analysis to produce real position sizing numbers for Monday.
