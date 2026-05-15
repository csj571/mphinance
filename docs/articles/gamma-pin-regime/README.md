# Market Pulse: The Gamma Loop Holding This Rally Together

*May 15, 2026*

![Market Pulse: The Gamma Loop Holding This Rally Together](hero_banner.png)

---

**SPY closed at $748 yesterday, VIX printed 17, and nobody can tell me why.**

Pull up the daily. The thing's been grinding higher for two weeks on a tape so quiet you can hear yourself blink. Earnings season is wrapping up, half the megacaps already reported, the AI capex narrative is back from the dead. None of that explains a market that won't even take a real breath on the way up. Realized vol has collapsed. Sectors are nodding along politely. Credit is sitting there with its hands in its pockets, refusing to confirm anything.

It looks like a story. It isn't.

The reason this tape behaves like it's been sedated isn't earnings. It isn't AI. It isn't even macro. It's a **gamma loop**, a self-reinforcing dealer-hedging mechanic that, once it gets going, can pin the index in place for weeks. We're sitting in the middle of one right now. Today is May monthly OpEx, which means most of the gamma holding this thing up evaporates at the close. Then we get to see whether the regime resets or breaks.

Either way, the play this week is not "fade the rip." Fading this regime with directional puts is the kind of trade that's killed a lot of accounts that should have known better. Trust me, I know a thing or two about the cost of trying to outsmart math. I've spent enough of my life on the wrong side of a probability table to know when the casino is the house and when I'm the house.

This week, the house is the dealer desk. Let's talk about what that actually means.

---

## What's Holding This Up

I ran the GEX engine on the index complex this morning. The data is unambiguous:

| Symbol | Spot | Total GEX | Gamma flip | Largest strike |
|---|---:|---:|---:|---|
| **SPY** | 748.17 | **+$3.80B** | 744.47 | **$750 call wall, +$987M** |
| QQQ | 719.79 | +$1.42B | 714.45 | $720 call wall, +$316M |
| IWM | 284.45 | +$685M | 282.59 | $285 call wall, +$345M |
| TLT | 84.92 | **−$605M** | 78.04 | $85 put pin, −$361M |
| GLD | 427.21 | +$54M | 439.09 | below flip, dealer effectively short |

That **$987 million** number at SPY $750? Not a typo. That's a billion dollars of dealer-net-long-gamma sitting at one strike, $2 above current spot. It means the market makers running the option desks at Citadel, Susquehanna, Jane Street, and everyone else who matters are obligated, *mechanically*, by their delta-hedging algorithms, to **sell into every rip toward $750 and buy every dip away from it**.

You're not fighting "the market." You're fighting a billion-dollar gravity well that doesn't care what you think about CPI.

And that's just SPY. Add QQQ ($316M at $720) and IWM ($345M at $285). The entire US equity index complex is sitting on its largest call walls of the cycle, with most of that gamma concentrated in options that expire **today**.

> *Sam the Quant Ghost on the line:*
> *"It's not a market, Michael, it's a fishtank. The fish think they're swimming. The water's the dealer book."*

Yeah. Pretty much.

---

## How the Loop Actually Works

The dealer-hedging mechanic is mechanical, but the loop is structural. Here's the whole thing in one diagram, in words.

**Step 1: Customers sell options to dealers.** When the public is complacent, and they are, with VVIX at 94 (the lowest in months), the dominant flow is option-*selling*. Covered call funds, the JPM Hedged Equity quarterly roll, structured products, retail call-selling for "income." All of those are dealers buying calls from someone else.

**Step 2: Dealers run long-gamma books.** When the public is short calls and puts, dealers are long them. Long-gamma desks hedge inverse to price. They *sell* when the market rises (their delta grows past their target) and *buy* when it falls (their delta shrinks past their target). This is the opposite of what dealers do in short-gamma regimes, where they chase the move. **Long-gamma stabilizes. Short-gamma destabilizes.**

**Step 3: The stabilization crushes realized volatility.** When every move gets faded mechanically, the 30-day realized vol on the S&P drops from 18% to 12% to 10%. The chart goes from looking like a heartbeat to looking like a flatline tilted slightly upward.

**Step 4: Vol-control strategies lever up.** Risk-parity funds, vol-targeted balanced products, CTAs, and pension-fund balanced sleeves all size positions *inversely* to realized vol. A fund targeting 12% vol that was 60% allocated to equities at 18% RV is now **100%+ allocated** at 10% RV. Same fund, same risk budget, twice the equity exposure. That re-allocation is incremental **buy flow**, which pushes prices higher, which compresses realized vol further.

**Step 5: Vol crush feeds the option-seller cycle.** As VIX drops from 18 to 14, structured-product issuers and option-selling income funds have to roll into shorter-dated, more aggressive structures to maintain their coupon. Those structures are *also* long-gamma at the dealer level. The supply of long-gamma to the dealer book grows because of the compression the dealer book created.

That's the loop. Every leg of it is buying the dip because the other legs did. **Nothing in this system is responding to fundamentals.** It's all flow, all mechanical, all self-reinforcing.

And this is exactly why every analyst on TV who keeps calling for a top is wrong about the timing. The fundamentals haven't changed, but the fundamentals weren't what got us here. You can't fade the gamma loop with a P/E argument.

---

## When This Has Played Out Before

This isn't new. It runs every low-vol stretch. And it always breaks the same way: a single exogenous catalyst that the system wasn't priced for.

**2017 Q4 / Feb 2018, the canonical case.** SPX ripped 5.7% in Q4 2017 with VIX averaging below 11. Short-vol products (XIV, SVXY) ballooned to $3B AUM, themselves a giant source of long-gamma supply to dealer books. The regime ran six months. It broke on a single CPI print. Feb 2 wages came in hot, Feb 5 the mechanical short-vol rebalance forced XIV to liquidate in the after-hours window, VIX went from 17 to 50 overnight, and "Volmageddon" wound down a $2B ETN in 24 hours. **The structural source of the long-gamma supply removed itself.** Pin regime over.

**2019, multiple shorter regimes.** May 2019 was a clean three-week pin punctuated by Powell's "patient" pivot that broke through the call wall in days. The lesson: a Fed pivot moves the dealer wall faster than dealers can re-hedge. Pins don't break to the downside as often as they break to the upside, but when the central bank moves the goalposts, all bets are off.

**H1 2024, the deepest one of the decade.** SPX up 20% YTD by late July with VIX 13-15. Powered by call-selling at institutional scale (the JPM Hedged Equity Fund alone runs ~$25B in covered-call structures). Dealers ran long-gamma for months. Then early August: BoJ surprise rate hike, weak NFP, and a single-name shock (Buffett's reported AAPL selling) all hit in 72 hours. VIX touched 65 intraday on August 5. **The break wasn't one trigger. It was three independent things stacking inside three days.** No single one alone would have done it.

The pattern, every time:

- **The regime ran longer than skeptics expected.**
- **The break wasn't telegraphed by price action.** The tape pinned tighter and tighter right up to the trigger.
- **The trigger was always exogenous.** CPI, central bank, geopolitical, single-name credit. Never a rollover.
- **Recovery was fast.** All three regimes were back at fresh highs within weeks of the break.

Most traders made the same mistake every time. They faded the pin too early, exhausted capital on weekly puts that decayed worthless, and were underexposed when the regime resumed.

Don't be that trader.

---

## What Specifically Breaks These Things

I keep five fragility indicators on my desk every morning. None of them are flashing red today. But knowing what to watch is the difference between getting out two days early and getting out two days late.

1. **CPI / PPI surprise.** A hot inflation print resets Fed expectations and re-prices the entire vol surface in milliseconds. This week's CPI landed Tuesday, in-line. The next print is mid-June. Until then, this fuse is dark.

2. **FOMC pivot or hawk.** Powell's August 2022 Jackson Hole "some pain" comment took the S&P down 4% in three days. Next FOMC meeting is June. Fed is in the quiet period right now. Fuse dark.

3. **Single-name shock with concentration risk.** The top-10 S&P weighting is ~33%. An NVDA earnings miss, an AAPL antitrust ruling, a single-stock CEO event. Any one of them metastasizes across the index because the index *is* those names. **This is the most underwriting-priced risk in the whole setup.** Hard to see coming, easy to get blindsided by.

4. **Credit cracks.** The most reliable *leading* indicator I track. When HYG breaks its 50-day on volume, equity follows within 2-6 sessions. Today HYG is **−0.08% on the day, flat on the week**. Credit is *not confirming* the rally, but it's not breaking either. **Watch HYG more than VIX.** VIX is a result. HYG is a leading.

5. **Concentration unwind / forced de-grossing.** When CTAs or vol-control funds hit stops in unison, mechanical de-leveraging creates a self-reinforcing *sell* loop. The opposite of what's holding us up right now. Triggers are hard to predict. You see it in real time via the index put/call skew blowing out.

The honest assessment: **none of the five are red.** The pin holds until at least the next high-impact data release. That's NFP first Friday in June. Until then, you're trading inside the gravity well.

---

## How to Trade With the Pin, Not Against It

The whole reason this writeup exists is because I keep seeing people fade these regimes the wrong way and bleed out. Let me be specific.

**Don't:**

- Buy weekly OTM puts as a "lottery." In long-gamma, dealer dampening keeps realized vol below implied vol, and your expected value on those puts is *negative*. You're paying the casino vig for hope.
- Short the indices outright. The pin will run you over before any of the fragility indicators flash.
- Fade individual call walls expecting "the wall to break." The wall doesn't break. The regime breaks, and then *every* wall breaks at once.

**Do:**

- Buy pullbacks toward the gamma flip level. SPY $744.47 today. Mechanical buying lives there. Reverse only if flip breaks decisively *and* credit confirms.
- Trim or take profits into call walls. SPY $750/$755 today. Dealers sell into rallies there, you should too.
- Sell premium, don't buy it. In a long-gamma regime, the option seller harvests the very flow you can't fight as a buyer. Tight short strangles (15-delta) on index ETFs collect theta inside the band.
- **Size on distance-to-wall, not distance-to-stop.** This is the one piece of intuition that flips in this regime. A name that's 1 ATR from your stop but 0.4 ATR from a $300M call wall has *less risk than your stop tells you*, because the wall is going to do half the work.

---

## Single-Name Expressions Today

The dealer-hedging mechanic plays out at the equity level too. Stocks with their own large GEX setups generate their own micro-pins, independent of (or amplified by) the index. The screener pulled six clean instances for today's expiry.

**RIVN. Spot $14.59, dealer net call OI at $15 is 305,000 contracts.** That's the largest single-strike concentration in my universe. Dealers are short calls at $15, long the underlying as a hedge, and they have to *buy more shares* every time spot drifts toward $15. Snap quality HIGH, 0.2 ATR distance. The probability of touching $15 today is very high. The magnitude is small. This is the cleanest expression of dealer-pull-toward-pin on the screen.

**EQX. Spot $14.47 to a $15 call wall.** HIGH quality, 0.7 ATR. Notable because the same setup was tagged earlier in the week and the structure has *held*. Confirmation the magnet is persistent, not a one-day phenomenon.

**CMCSA. Spot $25.08 to a $28 pin.** Wider distance (+4.5%) requires a real 1.4 ATR move, not a drift. HIGH quality, but the bigger move means the index pin's dampening force is going to matter more here. The trade: morning weakness toward $25 flat, snap up if SPX holds its $744 flip.

**T. Spot $24.68 to a $26 pin.** HIGH quality, 1.0 ATR. Defensive telco dividend name, less correlated to index dynamics. This is the "boring high-conviction" version of the trade.

**STLA. Spot $7.82 to an $8 pin.** Small ticker, small move, HIGH quality. Essentially a $0.20 grind from $7.82 to $8.00 by close. Cheapest expression of the mechanic on the board.

**INFQ. Spot $14.07 to a $15 call wall.** **+6.6% distance**, by far the biggest mover, but only MODERATE quality. The call wall and put wall are stacked at $12.50/$15 with equal OI, so the gravity isn't concentrated. High vega, lower probability. If the regime breaks down mid-day, INFQ is the one that fails first.

> *Sam, weighing in:*
> *"RIVN is the trade. EQX is the carry. STLA is the snack. INFQ is the lottery. Don't confuse them."*

For what it's worth, the short side of the screen (HPE −7.1%, MO −3.9%, AAPL −2.2%, KO −2.1%) reads the same mechanic in reverse. Call walls *below* spot, dealers having to *sell* down to the pin. HPE has the biggest potential single-name move on the entire board today. No clean 2x inverse LETF available for the small-account set, so it's mostly an academic observation unless you can size into outright shares or naked puts.

**The systemic risk on all six is identical.** If SPY breaks $744 flip pre-noon, every long-gamma pin on this screen flips sign simultaneously. All the BELOW-spot pins currently pulling up would invert and pull down. That's the OpEx-day asymmetric risk worth pre-defining before you put anything on.

---

## The Honest Caveats

This is the part where I admit what I don't know. There are six places this whole framework is fragile, in declining order of probability.

**One. The dealer book skew is estimated, not measured.** The GEX number depends on assumptions about who owns the open interest. When customer flow flips from net call-selling to net call-buying, like late 2021 when retail piled into Tesla calls, the headline GEX can mis-sign the regime for months. **Cross-check with realized-vs-implied.** If realized vol is above implied and rising, the long-gamma story isn't matching tape behavior.

**Two. The pin holds until it doesn't, and "until it doesn't" is unpredictable.** The five fragility indicators are necessary but not sufficient. August 5, 2024 broke from a setup that looked indistinguishable from the prior six weeks. Position sizing should reflect this.

**Three. Monthly OpEx mechanics reset the regime overnight.** Today's pin at SPY $750 with $987M GEX is mostly Friday-expiring. By Monday's open, the gamma profile resets to whatever the new week's OI structure looks like. **Today's thesis does not carry into Monday without re-running the engine.**

**Four. Single-name correlations to the index pin matter.** A clean idiosyncratic setup like RIVN can fail if the index break-pin-down drag overwhelms the single-name pull-up. HIGH quality with low ATR distance is the safer expression. Those depend least on the index cooperating.

**Five. The thesis explains mechanics, not direction.** Long-gamma stabilizes, but it doesn't tell you whether the median outcome over the next two weeks is +50bps or −50bps. The current data leans modestly bullish (vol crush, sector breadth, credit silent) but a hawkish surprise from anywhere flips the mid-point. **Don't confuse "the pin is intact" with "the next 5% is up."**

**Six. Local data quality.** The GEX engine uses Tradier option chains and same-day OI. OI is a T+1 figure, updated by OCC overnight. Intraday OI movement on heavy-flow names (especially the meme-flavored small caps) can shift the picture within hours. Re-run the engine before you act on the morning print.

---

## Closing

The S&P isn't going up because earnings are great or because the AI narrative is back. It's going up because **the dealer book is structurally long gamma, vol is collapsing, vol-control flows are mechanically buying, and the option-seller industry is reinforcing the loop**.

That can run another two weeks or another two months. It's running because the structure permits it. It will end abruptly, exogenously, and the trader who fights it from inside the regime loses both the long side *and* the short side.

The whole job this week is:

- Trade with the pin, not against it.
- Size on distance-to-wall, not distance-to-stop.
- Watch the five indicators daily. The break, when it comes, will move two of them at once.
- Cash up before 3:30 ET on monthly OpEx, not through it.
- Don't fall in love with the regime. They all end the same way.

The picks above are the same mechanic at the equity level. RIVN is the cleanest. EQX is the carry. STLA is the snack. INFQ is the lottery. If the index pin breaks before noon, ignore them all and step aside.

Trade safe, trade small, and trade *with* the math. The casino runs this floor today. Try not to be a customer.

---

*Michael*

*If you want the full data pipeline, live GEX engine output, the daily pin screener, the five-indicator dashboard, that's all running inside the [Phund](https://mphinance.com) right now. The whole thing is an open book.*
