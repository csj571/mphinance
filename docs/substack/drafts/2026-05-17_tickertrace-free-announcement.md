# TickerTrace Is Free Now. Here's Why.

*by Michael Hanko, Managing Partner, The Phund*

I spent eight months building a tool that scrapes what ETFs are actually buying and selling every single day. Then I put it behind a paywall. Then I tore the paywall down.

*[IMAGE: tickertrace_landing_v2.png - the updated hero with "Front-run the institutions" headline and TraderDaddy integration]*

Let me explain.

## The Problem That Started All This

Your broker shows you what institutions held last quarter. Go pull up any ETF on Fidelity or Schwab right now. You will see 13F filings from 45 days ago. Holdings data that is already priced in by the time you read it.

That is not intelligence. That is archaeology.

Meanwhile, the actual funds? They publish their holdings to their own websites every single day. Not all of them, but enough. YieldMax, Defiance, REX, Roundhill, Innovator, Corgi, GraniteShares. 56 funds. Updated daily. Just sitting there on public web pages like a $15/month Bloomberg terminal that nobody thought to build.

So I built it.

## What TickerTrace Actually Does

Every market day, a Python scraper hits 56 ETF provider websites, pulls their current holdings data, and diffs it against yesterday. It catches:

**Weight changes.** NVDA went from 6.04% to 6.21% in ULTY? That is a buy signal hiding in plain sight.

**New positions.** Three providers all added COHR in the same week? That is convergence.

**Multi-provider signals.** When NVDA shows up as a buy across 4 different fund families simultaneously, that is not a coincidence. That is institutional consensus forming in real time.

**Active streaks.** CSCO has been accumulating in KOQO for 7 straight days? That is not noise. That is a trend.

**Divergences.** One fund buying TSLA while another is dumping it? That is the kind of conflict that creates opportunity.

**New options.** When a fund writes a covered call capping MSTR's upside at $50, that tells you something about where the smart money thinks the ceiling is.

The dashboard tracks all of this. 56 funds. 101 underlying stocks. Updated every market day before the bell.

## Why This Is Free

I launched TraderDaddy Pro earlier this year. It is a full trading platform with AI-driven signals, technical analysis, momentum scoring, and option flow tools. That is the paid product. That is where the strategy lives.

But the raw data? What the funds are buying and selling today? That should not cost you anything.

Think about it. These funds publish their holdings to their own websites for free. The information is public. The only thing standing between a retail trader and that data is knowing where to look and having something that reads it all in one place. Charging $15/month for that felt like gatekeeping information that was already sitting in the open.

Retail traders are already bleeding $200/month on tools. TradingView. Discord servers. Scanner subscriptions. Options flow services. I did not want to be another line item on that stack.

So I ripped the paywall down. No login required. No "Pro tier." No account needed. Just go to [tickertrace.pro](https://tickertrace.pro) and start reading the damn data.

Not everyone wants to trade options. Not everyone needs a full AI-powered dashboard. But everyone deserves to know what the institutions are doing with their money. That is the whole point.

## What You Are Looking At

*[IMAGE: tickertrace_dashboard.png - the top of the dashboard showing search, stats bar, and top buys/sells/multi-provider/streaks]*

The dashboard has four main sections that matter.

**Top Buys and Top Sells.** The three biggest daily weight increases and decreases across all tracked funds. Right now NVDA is up 6.04% conviction across ULTY, CMAG, FDRS, and NVDW. TSLA is being trimmed by SLTY and KOQO. That polarity tells a story.

**Multi-Provider Consensus.** When multiple fund families are all buying the same stock, it shows up here. NVDA across 3 providers. GOOGL across 4. FTNT across 2. This is not one fund manager's opinion. This is a pattern emerging across independent allocation decisions.

**Active Streaks.** How many consecutive days a stock has been accumulated or distributed. CSCO on a 7-day buying streak in KOQO. FIGXX on a 4-day streak in KYLD. These are not random. These are programs running.

**The Heatmap.** Every fund on the Y-axis, every underlying stock on the X-axis. Green is accumulating. Red is reducing. Bright means big move. This is the single most useful view in the entire app. One glance and you know where the money is flowing.

*[IMAGE: tickertrace_dashboard_full.png - cropped to the heatmap section showing the fund x ticker grid]*

## How This Fits Into TraderDaddy Pro

TickerTrace is part of the TraderDaddy Pro ecosystem. Same team, same mission, same codebase.

Inside TraderDaddy Pro, we use this exact data alongside option flow analysis to make real trading decisions. When TickerTrace shows NVDA being accumulated across 4 providers and the option flow confirms heavy call buying at the same strikes, that is a signal we act on. The convergence between what institutions are holding and how the options market is positioning around those holdings is where the edge lives.

But here is the thing. You do not need to trade options to benefit from knowing what the funds are doing.

Maybe you just want to know that 3 different ETF providers all started buying GOOGL this week before you add to your 401k. Maybe you want to see that TSLA is being trimmed across multiple funds before you panic-buy the dip. Maybe you just want a heatmap that shows you where the money is flowing so you can stop guessing.

That is TickerTrace. Free. Forever.

If you want the full platform with AI signals, momentum scoring, option flow, and trade execution tools, that is [traderdaddy.pro](https://traderdaddy.pro). But the intelligence layer? The "what are the institutions actually doing" part? That belongs to everyone.

Beat the institutions with their own data. That is the pitch. That is the whole product.

## 56 Funds and Counting

Here is what we are currently tracking:

**YieldMax:** TSLY, NVDY, CONY, MSTY, AMZY, OARK, APLY, GOOY, FBY, DISO, SQY, MRNY, NFLY, YMAX, ULTY, and more

**Defiance:** QQQY, JEPY, IWMY, USOY, WDTE, MSTW, ROOY

**REX:** FEPI, AIPI

**Roundhill:** XDTE, QDTE, RDTE

**GraniteShares:** NVDL, TSLL

**Innovator, Corgi, KQQO, KYLD, SLTY, XA, FDRS, and others.**

We just added 16 Corgi Funds thematic ETFs this week. If your fund is not on the list, there is a "Request a Fund" button. If it publishes daily holdings, we will scrape it.

## The Whole Thing Is Open Source

This is the part that matters most to me.

The entire TickerTrace codebase is public on GitHub: [github.com/mphinance/TickerTrace](https://github.com/mphinance/TickerTrace)

165 commits. Every scraper. Every API endpoint. Every data pipeline. Every line of code that powers the dashboard you see at [tickertrace.pro](https://tickertrace.pro). If you do not trust the data, read the code. If you do not like how it works, fork it and build your own.

But it goes further than that.

**The API is fully open.** No API key. No authentication. No rate caps beyond basic IP throttling. Hit api.tickertrace.mphinance.com/api/v1/signals right now from your terminal and you get back every buy, sell, streak, and divergence in JSON. Build your own tools on top of it. Build a Discord bot. Build a spreadsheet integration. I do not care. The data is there.

**There is an MCP server.** If you use Claude Desktop or any AI agent that supports MCP, you can plug TickerTrace directly into your AI workflow. Ask your agent "what are institutions buying today?" and it pulls live data from the same API. The config is in the README.

**The daily scraper runs on GitHub Actions.** Every morning at 7 AM CST, it hits all 56 fund provider websites, scrapes their holdings, resolves CUSIPs, normalizes the data into a single CSV, and commits it to the repo. You can literally watch the commits roll in every market day. The history of every holding change, going back months, is sitting right there in the public repo.

I am not giving you a free trial. I am not giving you a limited version. I am giving you the whole damn thing. The dashboard, the API, the data, and the source code to verify all of it.

Why? Because the information was never mine to begin with. The funds publish it. I just wrote the scrapers. And scraper code should not be behind a paywall.

## What's Next

The TraderDaddy ecosystem keeps growing. TickerTrace is the free intelligence layer. TraderDaddy Pro is the strategy platform. The Ghost Alpha Dossier is the daily AI-generated research report. All three feed into each other. All three are pointed at the same mission: give retail traders the same information the institutions have, and the tools to act on it.

I genuinely believe that access to this kind of data should not depend on how much money you have. The funds publish it. We just read it faster. And now everyone can.

The paywall is gone. The code is open. The API is live. Go look at what the funds bought today.

[tickertrace.pro](https://tickertrace.pro)

[github.com/mphinance/TickerTrace](https://github.com/mphinance/TickerTrace)

Drink water. Check the heatmap. Call your sponsor.

*Not financial advice. I am a felon with a GitHub repo, 56 web scrapers, and zero patience for information asymmetry. But the data is real, the code is open source, and every number on that dashboard came directly from the funds' own published holdings. Fork it if you don't believe me.*

---

**Subscribe to Momentum Phinance for the wheel series, the daily dossier, and whatever I build next. Half of every paid subscription goes directly into the brokerage account. You are literally funding the machine.**

- Michael Hanko
