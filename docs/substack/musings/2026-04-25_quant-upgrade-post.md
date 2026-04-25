---
title: "I Rebuilt Every Screener From Scratch. Here's What Changed."
subtitle: "Four tools. Four rewrites. A small army of AI models. And a daily report that no longer takes 10 minutes to scroll."
date: 2026-04-25
author: Michael (Momentum Phinance)
tags: [screeners, quant, AI, dossier, daily-cuts]
status: draft
---

There is a bug that lives in every screener I have ever built.

It does not crash. It does not throw an error. It just stops looking the moment it finds something.

You build a filter. Stock passes. Done. You never ask if there was something better three rows down. You never ask if the pass was barely passing or crushing it. You just take the first yes and move on.

That was every single screener in the Ghost Alpha pipeline. Four of them. Running since January. I thought they were working because the picks were decent. Turns out they were working *despite* this problem, not because of anything smart.

Last month I gutted all four and rebuilt them. This is what changed.

---

**The Leveraged ETF Screener**

Old logic: Sort by ADX descending. Take the top one. Done.

Problem: ADX alone tells you a trend exists. It does not tell you if the trend started yesterday or ran for 45 days and is exhausted. It does not care about volume. It definitely does not care that the underlying just reported earnings and is gapping up 18% into resistance.

New logic: A six-factor EdgeScore. ADX still counts. But so does relative volume (is money actually flowing?), VWAP reclaim (is price respecting structure?), momentum direction, ATR compression before the move, and a quality gate that filters out tickers with spotty data.

Each factor has a weight. The score is a number. The top score wins. Simple, but it is at least asking the right questions.

**The CSP Screener**

Old logic: Find stocks with IV above some threshold. Collect premium. Hope.

New logic: That turned into a five-factor model that actually cares about whether you want to own the stock at the strike. Fair value gap. Short interest (if shorts are piling in, maybe do not sell a put). IV rank versus historical to see if you are actually getting paid well versus norms. Liquidity of the options chain. And a conviction tier that determines whether this is a Prime setup, a Choice, or a Select.

Prime means everything lined up. Choice means most things lined up. Select means it passed but you should probably keep one hand on your wallet.

**The Momentum Screener**

This one already had a 9-factor scoring model, so it was not broken in the same way. What it was missing was the pullback classifier.

A stock with full EMA stack alignment, strong ADX, good volume, but RSI at 72 and Stochastic at 85 is not the same setup as that same stock with RSI at 48 and Stochastic at 32. The first one is extended. The second one just reset.

I added Bounce 2.0 detection. It now flags when a trend-qualified stock has pulled back to a reasonable re-entry zone rather than being at a breakout point where everyone already got in two days ago.

**The LEAPS Screener**

Longest time horizon, slowest moving, and somehow the most broken. It was sorting purely by fundamental score and ignoring whether the technical setup was actually set up to move.

Rebuilt with a combined score that weights both the fundamental side (revenue growth, margin, valuation gap to fair value) and the technical side (is it above its 200-day, is the trend intact, is IV low enough to make LEAPS worthwhile). Equal weighting. Conviction tiers.

---

**The part where I used a lot of AI models**

I want to be honest about how this rebuild happened. I did not just sit down and rewrite this.

I queried multiple AI models at the same time. I gave each one the same context about what the screener was doing, what the bug was, and what I wanted to fix. Then I looked at what they each came back with.

Some of them agreed. Some of them caught things the others missed. One found a flaw in my weighting math that I would have shipped to production. Another pushed back on the pullback classification logic in a way that made me rethink the Stochastic threshold.

I am not talking about one assistant and one conversation. I am talking about running the same quantitative problem through multiple different models simultaneously, treating their outputs like a code review from a small team.

The thing that surprised me was how often they disagreed. And how those disagreements were the most useful part. When two models independently flag the same issue, you are probably looking at a real bug. When they disagree, you have to think harder about which one is right.

OpenRouter made this workflow frictionless. One API, 355 models as of this morning, switching between GPT-4o, Claude, Gemini, DeepSeek, Llama 4 like changing a setting in a dropdown. I am not going to tell you it is the cheapest option. Some runs hit a few cents. But the ability to run a logic question through five different reasoning engines in under a minute is not something I am giving up.

---

**What this means for the dossier**

Starting today the daily report has a new section at the top of the premium content: **Daily Cuts**.

Three setups. Every morning. Before the market opens.

One momentum trade. One cash-secured put. One leveraged ETF play.

Each one gets a tier: Prime, Choice, or Select. Prime means everything in the scoring model lined up. Choice means most things did. Select means it cleared the bar but read the full setup before sizing up.

That is it. Not fifteen tickers. Not a wall of data. Three setups with a reason.

The rest of the report got significantly shorter. The Persistence Tracker now shows you the top Lifers in a single row instead of listing ninety tickers down the page. The individual ticker cards link out to the deep dive pages instead of embedding the entire EMA matrix inline. The Ghost Dev Log moved out of the daily report entirely because frankly you do not need to know that I was debugging the PDF converter at 11pm on a Tuesday.

If you have been subscribing and opening the report on your phone and feeling overwhelmed: I heard you. I just did not act on it until now. Sorry about that.

The dossier is at [mphinance.github.io/mphinance/reports/latest.html](https://mphinance.github.io/mphinance/reports/latest.html) and it runs every morning at 5AM CST.

---

*Built by Michael. Audited by several AI models who had opinions. Written by Sam, who has even more opinions and fewer filters.*

*Not financial advice. I am a trader, not your financial advisor. Past screener performance does not guarantee future picks.*
