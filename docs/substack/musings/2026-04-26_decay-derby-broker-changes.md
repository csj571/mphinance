---
title: "The Broker Switch, the Wheel Tracker Overhaul, and the Decay Derby Update"
subtitle: "Moving money, fixing the dashboard, and keeping the options wheel turning."
date: 2026-04-26
author: Michael (Momentum Phinance)
tags: [decay-derby, wheel-strategy, brokers, python, recovery]
hero_image: 2026-04-26_hero.png
status: draft
---

![2026-04-26_hero.png](2026-04-26_hero.png)

Yesterday I talked about the process. How the Ghost Alpha screeners got ripped apart and rebuilt as multi-factor scoring models. That was the code side of things. 

Today we are talking about actual money.

If you have been following the baby account challenge you know my goal was to grind my way out of Tastytrade. The $2,000 threshold was the escape velocity needed to transfer. We had three wheels spinning. It was a slow burn.

I decided to accelerate the timeline with a bucket swap. 

My Relay savings account holding my tax money was sitting at roughly $1,000. My Tastytrade account was also sitting at roughly $1,000. Instead of slowly bleeding new capital into a new broker I just swapped their jobs.

I moved the $1,000 out of the tax savings account and straight into Interactive Brokers (IBKR). That is the new home for the Momentum Phund operations. We can hit that $2,000 tier faster over there.

As for Tastytrade? It is now the tax bucket. I am leaving the open options alone until they get called away. But any free capital in that account is being slowly converted to SGOV (short-term treasuries). I have 8 months to wind those trades down and park the cash safely before the IRS comes knocking. The tax money stays safe. The trading operations migrate without skipping a beat.

**The Decay Derby Tracker Overhaul**

While I was moving money I also had to fix the way we track it.

The Decay Derby dashboard was breaking. Not the strategy. The display logic. Selling cash-secured puts is easy to track. But when you get assigned and have to start selling covered calls the old tracker would throw incorrect "expiring" alerts. It did not know how to handle the transition gracefully.

I spent the weekend completely overhauling the tracker logic. Now when a put gets assigned the system automatically reconciles the original assignment record. It transitions the position. It archives the old data to keep the portfolio tracking accurate. The UI finally distinguishes between active cash-secured puts and assigned trades. 

It sounds like a small fix. But when you are tracking dozens of premium trades across multiple accounts you need the dashboard to tell you the truth at a glance. Otherwise you make mistakes.

**Decay Derby: End of Week Standings**

This is where the rubber meets the road. We are running the wheel strategy across a dedicated $10,000 account to prove the math works at scale. Here is the end-of-week scoreboard from Fidelity as we close out Friday.

We started with a clean $10,000.  

Active wheels spinning:
- **RCAT**: Assigned on 200 shares at the $12.50 strike. We own it. Time to start selling calls.
- **UMAC**: Sold $13.50 puts for $40 premium.
- **UEC**: Sold $13.50 puts for $21 premium.
- **TMC**: Sold $5.00 puts for $18 premium.
- **NOK**: Rolling $9.50 puts, recently collected another $27.

We took a tiny scratch closing out AG, and let a UAMY $9.50 put expire worthless. The machine keeps grinding.

The win rate is holding. The premium is collecting. The true cost basis on our assigned positions continues to drop.

This is the boring version of trading. You collect a few dollars at a time. You lower your basis. You let compounding do the heavy lifting. You do not panic when a position goes against you. You just roll the wheel.

It is not sexy. It just works.

*(Note: Here is a snapshot of the latest dashboard tracking the wheel positions.)*

![Decay Derby Dashboard](2026-04-26_decay_derby_dashboard.png)

---

**The Paywall Cut: What We Are Watching This Week**

Since you guys are funding the escape route, here is the top setup the pipeline spit out this morning while I was migrating brokers. 

**Kinross Gold Corporation (KGC)**

I mentioned B2Gold (BTG) recently as a money printer, but if you want straight momentum, KGC is flashing Grade A right now in the Ghost Alpha screener. 
- **The Setup:** Full bullish EMA stack alignment.
- **The Kicker:** It just triggered a Momentum Squeeze Fire (SQZ FIRE) signal.
- **The Value:** The fundamental model flags it as 44% undervalued against its fair value.

Gold miners are operationally leveraged to the gold price. With central banks hoarding and the macro environment doing what it does, miners that are actually printing cash and holding strong technical trends are exactly where you want to look. KGC is sitting near $32.79, ADX is pushing 28 (strong trend), and it is coiled to run.

Keep it on the watchlist this week. Accumulate on dips.

---

*Built by Michael. Audited by AI. Not financial advice.*
