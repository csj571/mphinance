---
title: "I Have a Felony. I Can't Work at a Bank. So I Built My Own."
subtitle: "A Bloomberg terminal, a daily AI research report, and a trading system — built in a bedroom in Wisconsin. For free. Here's exactly how."
date: 2026-04-25
author: Michael (Momentum Phinance)
tags: [trading, AI, dossier, recovery, origin-story]
status: draft
---

> **[Hero image prompt]:** *Dark synthwave bedroom office scene: dual monitors glowing with trading charts and terminal windows, neon green and gold reflections, late night, cinematic. Mood: lone wolf genius, not sad. High contrast, no text.*

---

I am not supposed to be doing this.

Not in a "rules are for other people" way. In a very literal way. There are industries that will not hire me because of a decision I made a long time ago. Finance is one of them. I have a felony. It is not a secret. I talk about it openly because I am in recovery and radical honesty is part of the deal.

So I did the only thing I could think of.

I built the tools myself.

Over the last eight months I have been quietly constructing what I call the Ghost Alpha pipeline. It runs every morning at 5AM CST without me touching it. By the time I wake up, it has already done this:

Screened 3,000+ tickers across four different quantitative models. Ranked every setup by a multi-factor score. Identified which institutionally-managed ETFs added to or trimmed specific positions overnight. Run the top setups through four AI models simultaneously and asked them to argue with each other about the trade. Compiled all of it into a formatted research report. And pushed that report to a public URL that updates every single day.

That is not a description of a product I am selling. That is what happened this morning. At 5AM. While I was asleep.

Here is what that pipeline actually looks like.

---

**The part where I explain what I built without making it sound like I'm bragging**

*(I am a little bit bragging.)*

The pipeline has 16 stages. I am not going to describe all 16. I am going to tell you the four that matter.

**Stage 1: The screeners**

Four of them. Each one covers a different thesis.

The momentum screener looks for stocks with full EMA stack alignment (8 above 21 above 50 above 200), elevated ADX (trend strength), above-average volume, and RSI that has pulled back into a re-entry zone rather than sitting at 75 overbought. It does not just flag stocks that pass. It scores them. The top score gets labeled Prime. The next tier is Choice. The rest are Select.

The cash-secured put screener looks for options premium worth collecting. But it does not just find high IV. High IV on a stock that shorts are piling into is a trap. The screener cross-checks short interest, checks whether the strike is near a fair value gap (a price level where institutions were buying), and confirms the options chain has enough liquidity that you can actually get filled at a reasonable price.

The leveraged ETF screener looks at ADX, relative volume, VWAP position, ATR compression, and momentum direction. It gives you one setup per morning. Just one. Because leveraged ETFs are not a game where you want five candidates and a decision to make before 9:30.

The LEAPS screener blends fundamentals with technicals. Revenue growth, margin expansion, how far the stock is trading from its AI-estimated fair value, whether it is above its 200-day, and whether implied volatility is actually low enough to make a long-dated option worthwhile. It runs once a week. LEAPS are not a daily trade.

**Stage 2: The AI panel**

Every top setup goes into what I call HyperNet. I give the same prompt to multiple AI models at the same time. Right now that is usually four of them: GPT-4o, Claude, Gemini, and one of the open-source models through OpenRouter.

They do not agree.

That is the point.

When two models independently flag the same risk, you probably have a real risk. When they disagree, you have to think harder about which one is right. I am not using AI to tell me what to do. I am using it the way a portfolio manager uses an analyst team. Different people, different frameworks, different priors. You synthesize.

**Stage 3: TickerTrace**

This is the one I cannot find anywhere else, so I built it.

Every morning my system scrapes the daily holdings of 40+ ETFs. Not the quarterly 13F filings. The actual daily holdings that some funds are required to publish. Avantis AVUV is one of them. They run a $9 billion small-cap value fund. They rebalance daily. Which means if you watch them every single day you get a real-time map of where serious money is moving.

I rank every position change by net portfolio weight added. Not share count, because a million shares of a $3 stock is a very different bet than a million shares of a $30 stock. Weight tells you conviction.

The top three positions Avantis has been quietly building over the last seven weeks, ranked by net weight added:

**ViaSat (VSAT): +2.14% weight.** Bought 12 days, sold 2. A satellite company trading around $14 after spending most of 2024 above $25. Avantis is accumulating while nobody is watching.

**SM Energy (SM): +1.79% weight.** Bought 8 days, sold 3. Permian Basin energy. They are not rebalancing. They are actively adding while crude sits in the mid-60s.

**Matson (MATX): +1.76% weight. Zero sells.** Bought 30 out of 32 trading days. Never sold once. Jones Act shipping with a moat, record revenue, and institutional buyers who apparently do not believe in days off.

You will not find that breakdown anywhere else. Because nobody else is scraping daily holdings and ranking by weight delta. At least not publicly. At least not for free.

**Stage 4: The dossier**

All of it lands in a report that publishes every weekday at 5AM CST. The top of the report is Daily Cuts: three setups, one from each active screener, each with a conviction tier. The rest of the report has the full TickerTrace data, the AI synthesis, and the signal history.

It is at mphinance.github.io/mphinance and it updates every single morning.

---

**The part about why I am telling you this**

Because I spent a long time believing that the tools were only for people who deserved them.

The Bloomberg terminal costs $24,000 a year. The prime brokerage accounts require assets I did not have. The research reports are locked behind paywalls that cost more than my rent. The quant funds do not hire people with my background, and they do not share their models anyway.

I am not bitter about that. Those are the rules. I understand why they exist.

But I also understand that the tools that matter are just software. And I know how to write software. And the AI that used to cost a research team of twenty is now available for a few cents per API call.

So I built the tools. And now I run them every morning. And every morning they tell me things about the market that I could not have known otherwise.

That is the whole point of Momentum Phinance.

The playing field is not level. It never was. But it is closer than it has ever been. And I am not going to pretend I belong somewhere else while I wait for an invitation that was never coming.

---

**What to do next**

If you want the daily report, it is free. It lives at mphinance.github.io/mphinance. Subscribe and it lands in your inbox every morning before you finish your first cup of coffee.

If you want the full TickerTrace data with all 40+ ETFs, the detailed setup breakdowns, and the AI synthesis notes, that is the paid tier. It is not expensive. It is significantly cheaper than the $24,000 Bloomberg terminal and I am told it is more useful for retail-sized positions anyway.

If you just want to follow along and watch what happens when someone with no business being in this industry refuses to take the hint:

Welcome to Momentum Phinance.

Pull up a chair.

---

*Built by Michael. Audited by several AI models who had opinions about everything. Written by Sam, who had even more opinions and considerably fewer filters.*

*Not financial advice. I am a trader, not your financial advisor. I have a felony and a Substack. Act accordingly.*
