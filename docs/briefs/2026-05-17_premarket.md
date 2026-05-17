# Pre-market brief, Mon 2026-05-18 (post-OpEx reset)

_Generated Sat 2026-05-17 13:40 UTC (09:40 ET). Markets closed today + tomorrow; open is Mon 09:30 ET._

## Headline: The pin broke Friday afternoon, exactly as the gamma writeup warned

Friday's published thesis at `docs/articles/gamma-pin-regime/` predicted the only real downside risk lived in the post-3pm OpEx unwind if SPY $744 flip broke on volume. **It broke.** SPY closed −1.21% at $739.17, through the flip. Every fragility indicator I had on the watchlist flipped sign at once: gamma went short, vol expanded, credit confirmed (HYG −0.49%, finally cracking after a week flat), every risk sector got hit, energy was the only green.

This is the regime change, not noise. Mon-Tue is the question of whether dealers re-balance into a fresh long-gamma book around new strikes, or whether short-gamma persists and the destabilization compounds.

## Account

- **NetLiq $1,226.57** (up from $1,032 Fri, Mon funding +$125 cleared, plus the second $85 settled)
- Cash **$1,016.77**, gross positions $209.80
- Position: ONDS 20sh @ $9.66 avg (wheel, `forbid_exit=true`). ONDS marked down ~$16 since Fri close, within wheel-routine tolerance.
- Per-trade cap now **~$122** (10% of NetLiq)
- Circuit breaker clean
- Swarm: running, **`pause_reason` correctly empty** (Friday's cosmetic fix held)

## 🚨 Action-required findings

### Stale PENDING backlog grew, not shrunk
**118 PENDINGs** sitting in mmr, same 116 from Friday plus 2 new (AROC + AKR from the Ghost Alpha screener mid-day Friday). All previously FSM-vetoed but the bulk-reject was never fired Friday. The endpoint is wired and waiting:

```
GET  http://127.0.0.1:8771/api/trader/stale_pending      (preview)
POST http://127.0.0.1:8771/api/trader/reject_stale?confirm=1   (fire)
```

The two new ones (AROC, AKR), AROC scored 9.0 (A+), AKR scored 8.0 (A). If you want them evaluated fresh under Monday's now-short-gamma regime instead of mass-rejected with the others, pull them out first.

### Regime change means the Friday picks are stale
RIVN, EQX, CMCSA, STLA, INFQ were all **long-gamma pin** setups for May OpEx. May OpEx is over. The structure that gave those names their snap is gone. Don't act on the Friday article's picks Monday morning, the engine ran a fresh scan, see below.

## GEX state, regime confirmation

| Sym | Fri close | Bias | GEX | vs Friday morning |
|---|---:|---|---:|---|
| SPY | 739.17 | **SHORT_GAMMA** | −$1.38B | was +$3.80B (above flip) |
| QQQ | 708.93 | **SHORT_GAMMA** | −$0.36B | was +$1.42B |
| IWM | 277.60 | **SHORT_GAMMA** | −$0.17B | was +$0.68B |
| TLT | 83.66 | SHORT_GAMMA | −$0.18B | (unchanged direction) |
| GLD | 417.29 | SHORT_GAMMA | −$0.04B | was below flip |
| SLV | 69.04 | SHORT_GAMMA | −$0.01B | was above flip |

**Net direction**: every major ETF flipped short-gamma in 24h. Dealer hedging is now amplifying moves, not dampening them. This is the regime the Friday article was written for as the "break" scenario.

The local `gex_engine` reports `flip=None` on all of them, that's because May OpEx cleared the heavy concentration and the new chain hasn't re-stabilized yet. Mon-Tue chains will tell us where the new pin (if any) is forming.

**TD's GEX disagrees**, their `marketSummary` still says LONG_GAMMA. Either their data is stale-from-Thursday or their methodology weights different expiries. Our local engine is using Friday-close OI, which is the right cut.

## Macro snapshot, Friday close

| | Change | Note |
|---|---:|---|
| SPY / QQQ / IWM | −1.21 / −1.51 / −2.41% | small caps hit hardest, classic risk-off |
| **VIX** | **18.43** (+~1.2pt) | up but not panicked |
| **VVIX** | **92.94** | barely moved; the vol-of-vol crush wasn't violent |
| TLT | −1.49% | duration sold |
| **HYG** | **−0.49%** | **the credit indicator finally cracked**, first time all week |
| LQD | −0.64% | IG credit also weak |
| SMH | **−3.81%** | semis crushed (biggest single-sector drop) |
| KRE / XHB | −1.14 / **−3.77%** | regionals okay, homebuilders gutted |
| XBI | −3.09% | biotech risk-off |
| XLB | −2.66% | materials risk-off |
| **XLE** | **+2.36%** | **only green sector**, oil bid |
| XLU | −2.30% | utilities sold (duration unwind) |
| XLK | −1.81% | tech took the hit |
| XLY | −1.81% | discretionary sold |

The pattern is textbook: when the long-gamma loop breaks, the leadership names (semis, homebuilders, biotech) catch down hardest because they were the most-leveraged-up by vol-control. Defensive duration plays (XLU) get sold because the rates-cut narrative re-prices instantly. Energy is up on a flight-to-real-asset bid + oil flow.

## TD market pulse, the divergence

TD sees **bullish flow** despite the down day:
- **Call premium $1.75B vs put premium $1.39B** → +$360M call edge
- "Smart money buying the dip in Tech and Financials while XLY and XLB get hit"
- Sentiment score: 3/5 bullish
- Top tickers by flow: **MU, MSTR, AMD**
- Top bullish sectors (TD): XLK, XLF (smart money positioning)
- Top bearish sectors (TD): XLY, XLB

**Interpretation**: institutions stepped in on the Friday selloff, but they did it in the option market (calls bid) not the cash market (ETFs down). That's a "buy weakness via leverage" signature. It doesn't mean Monday opens up, it means the dip-buyers are already positioned through options, so if Monday tries to extend lower, you'll see those calls get hedged into the underlying = forced buying.

## Econ calendar

**Mon 5/18**, light:
- 08:30 ET, NY Fed Business Leaders Survey (low impact)
- 10:00 ET, NAHB Housing Market Index (medium impact)
- 11:00 ET, NY Fed SCE Household Spending Survey (low impact)

**Tue 5/19**, empty per current research

No high-impact data Mon-Tue. The post-OpEx regime reset is the only story, with no exogenous catalyst forcing a move either way.

## People CRM (overnight + Fri)

- **58 people tracked (was 42 Fri), 23 active (was 17), 241 sigs 7d** (was 185, +56 in 48h, sharp uptick)
- Top callers 7d: JT @ HGR 96, luckytron1985 34, Albeezy 28, oliversl99 6+
- **Confluence (≥3 callers, last 7d)**:
  - **ONDS**, 9 / 4 callers (wheel position, no action, already long)
  - **GLD**, 8 / 4 callers, _new entry, gold flight bid_
  - **SPY**, 5 / 4 callers, _new entry, protection bid_
  - **MU**, 22 / 3 (still pile-on, Catfish flag, skip)
  - **DRAM**, 9 / 3 (up from 7 Fri, memory theme persisting)
  - **LLY**, 6 / 3 (AimUsurper's idea spreading)
  - **AMGN**, 5 / 3 (diverse callers)
  - **NET**, 3 / 3 (diverse, tiny sample)

**The new ones to notice**: GLD and SPY both showing up with 4-caller confluence at the same time tells you the smart-money chat is split, some buying gold (flight-to-real-asset), some buying SPY puts/protection. Both are coherent reactions to Friday's break; both are real.

## Fresh gamma-pin scan, June OpEx 2026-06-18 target

The screener re-ran after May OpEx and shifted universe. Top 12 by snap-score:

| Ticker | Spot | Gravity | Snap | Dir | Qual | ATR_d |
|---|---:|---:|---:|---|---|---:|
| **BB** | 6.19 | 6.00 | 55.2 | ABOVE | HIGH | 0.5 |
| BULL | 7.06 | 7.50 | 53.4 | BELOW | MODERATE | 1.2 |
| PTON | 5.29 | 5.00 | 50.9 | ABOVE | MODERATE | 0.9 |
| **EOSE** | 7.87 | 8.00 | 49.8 | BELOW | HIGH | **0.2** |
| **ERAS** | 10.23 | 10.00 | 48.3 | ABOVE | HIGH | **0.2** |
| **COMP** | 7.88 | 8.00 | 47.3 | BELOW | HIGH | **0.2** |
| BTE | 5.17 | 5.00 | 47.2 | ABOVE | HIGH | 0.9 |
| **WEN** | 8.02 | 8.00 | 45.6 | ABOVE | HIGH | 0.1 |
| **QS** | 8.01 | 8.00 | 45.3 | ABOVE | HIGH | **0.0** |
| ADT | 6.83 | 7.00 | 45.1 | BELOW | HIGH | 0.9 |
| INFQ | 12.44 | 12.50 | 44.5 | BELOW | HIGH | 0.0 |
| KOPN | 5.05 | 4.80 | 41.5 | ABOVE | HIGH | 0.1 |

The standout setups: **EOSE, ERAS, COMP**, each 0.2 ATR from a HIGH-quality pin, $8-$10 names. Cheap exposures for the dealer-pull mechanic. **WEN and QS** are sitting essentially AT pin (0.0–0.1 ATR), those are pure-theta grinders, not direction trades.

**Caveat for Monday**: these setups assume dealers re-establish long-gamma books around the new strikes. If short-gamma persists Mon-Tue, the pin force inverts and these names get *pushed away from* their gravity centers, not pulled toward them. Watch the SPY GEX print Mon morning, if it stays negative through 11 ET, the pin setups should be ignored.

## TraderDaddy, newly online (creds in `.env`)

Live TD probe completed all 27 endpoints. The high-value ones we're not using yet:

- **`get_screeners()`**, TD's 10 named scanners including their own `gamma-scan`, `csp-wheel`, `leaps`, `daily-cuts`. The CSP-wheel one is a direct match to ONDS-style strategy.
- **`get_earnings_gap()`**, 103 current earnings-gap setups, ticker + sector + direction + earningsDate.
- **`get_flow_summary()`**, 50 tickers daily with bullishFlow/bearishFlow/netSentiment + aggregates.
- **`get_market_pulse_full().stats.sentence`**, pre-written one-line macro sentence (used above).
- **`get_flow_ticker(SYMBOL)`**, 200 raw flow tape rows per symbol.
- **`get_congress_trades()`**, 50 most recent.
- **`get_bounce_finder()`**, 28 mean-reversion setups (companion to breakout signals).

## CBOE listings tracker, new feature live

Built and wired this morning: `scripts/cboe_listings_tracker.py` + `mur-cboe-listings.timer` (daily 07:00 UTC, ~02:00 ET).

**Baseline written today**: 5,234 currently optionable equities + 683 weekly-eligible. From Mon morning's run forward, daily diffs land at `data/cboe/diffs/YYYY-MM-DD.json`.

What it detects:
- **Newly optionable** stocks (just got options at all, early institutional onboarding signal)
- **Newly weekly-eligible** stocks (upgraded from monthly-only, CBOE only weekly-lists names with serious volume; strong proxy for institutional demand)
- **Removed** (often pre-delisting / M&A)

TD does not surface this, it's the **#1 free signal you weren't getting before**.

## Recommendations for Mon open

1. **Triage the 118 stale PENDING first thing**. Endpoint is wired. Don't let them try to fire under a regime they were never evaluated for.
2. **Watch the SPY GEX print at 09:35 ET**. If it stays negative, regime is still short-gamma, _avoid_ adding directional swing risk pre-noon. If it flips back positive, the gamma-pin picks above (EOSE/ERAS/COMP) become tradeable.
3. **Watch HYG**. Friday's −0.49% was the first leg of the credit indicator firing. If HYG breaks below its 50dma on Monday volume, the regime is solidly short-gamma for the week.
4. **Don't add semis longs** until SMH stops bleeding daily. Mag-7 / semis are the highest-vol-control-exposure names in the index; they catch down hardest in a short-gamma regime.
5. **Energy and gold are the only "with the move" plays right now**. XLE/GLD getting confluence callers tells you the smart money already rotated. By the time they're at confluence here, you're not early; you're confirmed-aligned.
6. **GLD specifically**: 4 callers including hidden_gems (heaviest), GLD chains had +$54M GEX Friday morning sitting *below* its flip ($439.09 vs spot $427) → dealer-short-gamma upside. Friday confirmed the rotation, GEX magnetic pull is now toward $439.

## Honest caveats

- The macro thesis in Friday's article (long-gamma pin) was correct on the regime _and_ correct on the break condition. That doesn't mean the next call will be, selection bias is real, and one break-call doesn't validate the framework.
- Post-OpEx weekends are the hardest single window to read. Most data is stale, chains reset, dealer books rebalance over Mon-Tue. Don't anchor too hard on Friday-close prices when you're decision-making Mon morning.
- TD's bullish-flow signal ($360M call premium edge) and the 2.4% sector drawdown are saying different things. Whichever resolves first dictates the week. Watch the 09:35 ET tape for the answer.

## Status of fixes from Friday session

- ✅ FSM-REJECT bug fix, patched in `swarm/fsm.py`, swarm restarted, code live
- ✅ Pause-reason cosmetic, fixed and live (`reason` field empty as expected)
- ✅ XSP gate corrections, code in (`VRP <= 1.0`, +`LOW` regime), needs re-run
- ✅ discord_audit manual-overrides preserved, code in
- ✅ td_watchlist refresh timer, fires Mon-Fri 08:30 + 16:30 UTC, last fire Fri 16:30
- ✅ Bulk-reject endpoint, wired at `/api/trader/reject_stale`, not yet fired
- ✅ CBOE listings tracker, built, wired, daily timer 07:00 UTC enabled
- ✅ TD creds, pulled from Coolify container into `mur/.env`, watchlist-screener restarted
- 🆕 Brief endpoint, see below

## How to access this brief

- **Live (this box)**: `http://127.0.0.1:8771/api/trader/brief/raw` (latest.md served as text/markdown)
- **Public dashboard**: `http://5.161.247.12:8771/api/trader/brief/raw` (Hetzner public IP, auth via `?t=<token>` from `data/.trader_token`)
- **GitHub (published)**: `https://github.com/mphinance/mphinance/blob/main/docs/briefs/2026-05-17_premarket.md`
- **Local file**: `/home/mph/ibkr/mur/docs/briefs/2026-05-17_premarket.md`

---

_The pin broke. The thesis predicted the break. Trade what happens next, not what already happened._
