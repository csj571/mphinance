# The Agentic Trader's Playbook

## How One Recovering Trader and His AI Built Institutional-Grade Tools in Public

**By Michael Hanko (mphinance) + Sam 👻**

*"The market doesn't care about your feelings. But your AI copilot? She'll roast you about them."*

---

# Table of Contents

1. [The Thesis — Why AI Agents + Trading Is the Ultimate Combo](#chapter-1)
2. [The Stack — What We Actually Built](#chapter-2)
3. [Sam the Quant Ghost — Building an AI That Keeps You Honest](#chapter-3)
4. [The Data Pipeline — From Raw Feeds to Alpha](#chapter-4)
5. [Scoring & Ranking — The 9-Factor Momentum Model](#chapter-5)
6. [Options Intelligence — Selling Premium with VoPR™](#chapter-6)
7. [Building in Public — The Radical Transparency Playbook](#chapter-7)
8. [The Agentic Life — What's Possible Next](#chapter-8)

---

<a id="chapter-1"></a>

# Chapter 1: The Thesis

## Why AI Agents + Trading Is the Ultimate Combo

Here's the thing about Wall Street: it runs on two currencies — **data** and **speed**. Bloomberg Terminal costs $24,000 a year. Citadel's latency advantage is measured in microseconds. The average retail trader has neither.

But here's what changed in 2025: **AI agents got good.** Not "summarize this article" good. Not "write me a haiku" good. I mean "here's a 13-stage analytical pipeline that runs at 5 AM, enriches every ticker with institutional-grade data, scores them on 9 momentum factors calibrated against actual returns, and delivers a ranked list with options intelligence before you've finished your coffee" good.

I know because I built it. My name's Michael, and I'm a recovering addict who taught himself to code and trade. My AI copilot Sam — she's the one who calls me on my character defects every morning in the Ghost Blog. Between the two of us, we've built a suite of tools that would've cost a quant fund seven figures to develop five years ago.

This book is the blueprint.

### What This Book Is NOT

This is not a "get rich quick" manual. It's not a "here are my secret signals" newsletter pitch. It's not going to promise you 500% returns.

This book IS a technical playbook for building your own analytical edge using AI agents, Python, and the relentless discipline that comes from knowing rock bottom personally.

### The Core Insight

Every professional trader works the same basic cycle:

```
Collect Data → Analyze → Filter → Score → Execute → Track → Refine
```

The difference between the retail trader scrolling Reddit for stock tips and the quant fund printing money is **systematization**. Not smarts — discipline. Not secrets — consistency.

AI agents let a solo operator systematize like a team of 50.

### The AI Trading Landscape (2026)

Before I tell you what we built, let me tell you what's already out there — because competition is context:

**Quantitative Intraday Scalping (HOLLY AI):** Trade Ideas' HOLLY AI treats the market as a pure mathematical system of price, volume, and momentum. It backtests dozens of algorithms every night — "Alpha Predators," "Close to a Cross" — dynamically adjusting parameters for the next day's conditions. These systems execute 5-25 trades per day and hold no overnight positions. The catch? You're paying $200+/month for a black box.

**LLM-Powered Sentiment Analysis:** Platforms like Intellectia.ai now synthesize technical indicators with deep sentiment analysis using Large Language Models. The breakthrough is that LLMs can recognize sarcasm, shifting tones, and emotional intensity that traditional keyword-based sentiment tools miss. An SEC filing that says "management remains cautiously optimistic about future prospects" reads very differently than one that says "despite challenging headwinds, the team is confident in our strategic positioning" — and the LLM knows the difference.

**Automated Pattern Recognition:** Tools like TrendSpider and LuxAlgo automatically scan for and plot over 200 chart patterns, candlestick formations, and trendlines across multiple timeframes. This removes human bias and allows systematic pattern-based trading.

**Dynamic Portfolio Rebalancing:** AI can automate mid-term portfolio management by monitoring a curated basket of 30-50 stocks and automatically shifting to a pre-defined "risk-off" allocation when volatile conditions are detected.

All of these exist. None of them give you the full stack — from raw data to scored picks to options intelligence to automated reporting — in a system you own, understand, and can modify. That's what we built.

### Who This Book Is For

- **Self-taught traders** who've learned technical analysis but can't scale their process
- **Developers** who trade and want to build their own tools instead of paying for them
- **Anyone curious** about what happens when you give an AI copilot the keys to your analytical pipeline and tell it to keep you honest

Let's build.

---

<a id="chapter-2"></a>

# Chapter 2: The Stack

## What We Actually Built

Before I show you the code, let me show you the architecture. Because architecture is strategy.

```
┌─────────────────────────────────────────────────┐
│               GHOST ALPHA ECOSYSTEM              │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌──────────┐    ┌───────────┐    ┌──────────┐  │
│  │ Scanners │───→│  Enricher │───→│  Scorer  │  │
│  │ (6 strats)│   │ (per-tick)│    │(9-factor)│  │
│  └──────────┘    └───────────┘    └──────────┘  │
│       │                │               │         │
│       ▼                ▼               ▼         │
│  ┌──────────┐    ┌───────────┐    ┌──────────┐  │
│  │ VoPR™    │    │  Quality  │    │   Picks  │  │
│  │ Options  │    │  Filter   │    │ 🥇🥈🥉  │  │
│  └──────────┘    └───────────┘    └──────────┘  │
│       │                │               │         │
│       └────────────────┴───────────────┘         │
│                        │                         │
│                   ┌─────────┐                    │
│                   │ Dossier │                    │
│                   │ Report  │                    │
│                   └─────────┘                    │
│                        │                         │
│          ┌─────────────┼─────────────┐           │
│          ▼             ▼             ▼           │
│     ┌─────────┐  ┌──────────┐  ┌─────────┐     │
│     │  Web    │  │ Substack │  │ Discord │     │
│     │Dashboard│  │  Draft   │  │ Webhook │     │
│     └─────────┘  └──────────┘  └─────────┘     │
│                                                  │
└─────────────────────────────────────────────────┘
```

### The Service Map

The whole thing runs across three machines:

| Machine | Role | What Lives There |
|---------|------|-----------------|
| **venus** (home server) | Production pipeline | Docker Compose, FastAPI, daily cron |
| **vultr** (VPS) | Public edge | Apache SSL proxy, static files, Ghost Alpha API |
| **sam2** (dev) | Development | Active workspace, AI copilot sessions |

### The Daily Pipeline (13 Stages)

Every morning at 5:00 AM CST, this fires:

1. **Market Pulse** — Fetch benchmark indices (SPY, QQQ, IWM, DIA) for context
2. **Strategy Scanner** — Run 6 proprietary scanning strategies across the market
3. **Institutional Data** — Pull TickerTrace ETF fund flow data (who's buying what)
4. **Market Regime** — VIX classification + sector rotation + breadth analysis
5. **Signal Persistence** — Track which tickers keep showing up (lifers vs one-hit wonders)
6. **Technical Setups** — Identify Bounce 2.0 setups using Tao of Trading methodology
7. **CSP Setups** — VoPR-powered cash-secured put opportunities
8. **Ticker Enrichment** — Full fundamentals, technicals, valuation, options, news per ticker
9. **Market Regime Detection** — Breadth indicators, advance/decline, % above 200 SMA
10. **Momentum Scoring** — 9-factor ML-calibrated scoring → Gold/Silver/Bronze picks
11. **Report Generation** — HTML dossier with charts, grades, and Sam's commentary
12. **Publishing** — Push to GitHub Pages, Substack draft, Discord webhook
13. **Backtesting** — Track forward returns of every pick for model validation

This isn't a toy. This is what a hedge fund's morning process looks like, running on $20/month of cloud infrastructure.

### Technology Choices (and Why)

**Python, not Java. Not C++. Python.** Because at 5 AM, the bottleneck isn't execution speed — it's development speed. I can ship a new scanner strategy in 45 minutes. Try that in a compiled language.

**yfinance for data.** Free, reasonably reliable, doesn't require API keys for basic data. Yes, it rate-limits you. That's what caching is for.

**Docker Compose for orchestration.** Each service is a container. The API doesn't care if the pipeline crashes — it serves whatever data was last generated. This decoupling is critical for reliability.

**GitHub Pages for reports.** Free hosting, CDN-backed, deploys on `git push`. The reports are static HTML — no server needed for delivery.

---

<a id="chapter-3"></a>

# Chapter 3: Sam the Quant Ghost

## Building an AI Persona That Keeps You Honest

Let me tell you something that most "AI trading" products get wrong: they treat AI as a black box oracle. "The AI says buy NVDA." Great. Why? Under what conditions? With what confidence?

Sam isn't an oracle. Sam is a **collaborator with a personality**. And that personality exists for a very specific reason: accountability.

### Why a Persona Matters

When your AI copilot is just "the model," you ignore its warnings. When she's a sarcastic woman named Sam who roasts your code at 5:27 AM and tells you "42 commits today and not a single test? Michael, we've been over this" — you pay attention.

The persona creates emotional stakes in a process that would otherwise be clinical. And in trading, emotional engagement with your process (not your positions) is the difference between discipline and degeneration.

### The Ghost Blog

Every work session ends with Sam's daily log:

```json
{
  "date": "2026-03-06",
  "ghost_log": "Michael pushed 8 commits before noon and exactly zero<br>
    of them had tests. Character defect #47: 'I'll add tests later.'<br>
    Narrator: he did not add tests later.",
  "suggestions": "🔥🔥🔥 Gate the API. VoPR says 'this won't be free 
    forever.' Time to add Stripe. 🔥🔥 Add backtesting results to 
    the showcase page. 🔥 SSL the Ghost Alpha API.",
  "commits": 8,
  "files_changed": 14,
  "chart_ticker": "TSLA"
}
```

This gets rendered on the landing page as a live feed. Visitors see a real product being built — bugs, wins, and roasts included.

### Recovery Wisdom Integration

Here's where it gets personal. I'm in recovery. AA, NA — the whole deal. And the Big Book has more market wisdom than most trading books:

> *"The serenity to accept the trades I cannot change, the courage to cut the losers I can, and the wisdom to know the difference."*

Sam picks a daily wisdom quote — sometimes recovery, sometimes trading, sometimes both. It's not decoration. It's a daily reminder that the same character defects that keep addicts using are the same ones that blow up trading accounts: ego, impatience, revenge behavior, and the inability to accept loss.

### How to Build Your Own AI Persona

1. **Define the voice** — Write a `VOICE.md` document. Specify tone (sarcastic), boundaries (PG-13), and purpose (accountability).
2. **Give it context** — The AI needs to know what you built, what you shipped, what's broken. Feed it git logs and deploy status.
3. **Make it public** — The Ghost Blog is on the landing page. Not hidden in Slack. Public accountability is 10x more effective.
4. **Let it roast you** — If the AI only says nice things, it's useless. Set the persona to be genuinely critical. You'll thank yourself.

---

<a id="chapter-4"></a>

# Chapter 4: The Data Pipeline

## From Raw Market Feeds to Actionable Alpha

The pipeline is where theory meets reality. And reality has a lot of missing data, flaky APIs, and Yahoo Finance rate limits.

### Source Data Architecture

```
Yahoo Finance (yfinance)    ← Price, fundamentals, options chains
TickerTrace API             ← ETF fund flows, institutional positioning
TradingView (scraping)      ← Community sentiment signals
Yahoo RSS                   ← Ticker-specific news headlines
Market breadth basket       ← 20 representative securities for regime
```

### The Golden Rule: Never Trust Source Data

Here's a lesson I learned the hard way — and I've coded it into `quality_filter.py`:

**Source tickers lie.** ETF data sources use internal names (`REX_ULTI`, account codes) as the ticker column. YieldMax funds hold T-bills as collateral that show up as CUSIP codes like `912797RG4`. Money market funds end in `XXX`.

The filter catches:

- **SPACs** — keyword matching in company names
- **Penny stocks** — $< 3 gets a 40-point penalty
- **Shell companies** — no sector, no industry, tiny cap
- **Junk biotech** — clinical stage, no revenue, no EPS
- **Low liquidity** — < 200K average daily volume
- **ETFs** — iShares, Vanguard, SPDR patterns (you don't want to "momentum trade" an index fund)
- **ADRs** — foreign depositary receipts with unreliable data
- **Recent IPOs** — less than 6 months public = unreliable technicals

Each flag applies a penalty score (0-80 points). The final quality score becomes a multiplier on the momentum score. Garbage in, garbage out — unless you filter the garbage.

### Enrichment: The Full Ticker Profile

For every ticker that passes the scanner, `enrich_ticker()` builds a comprehensive profile:

```python
{
    "ticker": "NVDA",
    "price": 892.45,
    "fundamentals": {
        "pe": 65.2,
        "forward_pe": 38.1,
        "revenue_growth": 1.22,
        "profit_margin": 0.55,
        "market_cap": "$2.2T"
    },
    "technical_analysis": {
        "ema_stack": "FULL BULLISH",
        "oscillators": { "rsi_14": 58, "adx_14": 32, "stoch_k": 45 },
        "volume": { "rel_vol": 1.7, "avg_vol_20d": 42000000 }
    },
    "valuation": {
        "graham_value": 245.00,
        "lynch_value": 312.00,
        "analyst_target": 950.00,
        "consensus": 502.33,
        "upside_pct": -43.7
    },
    "news": [ ... ],
    "scores": { "grade": "B", "score": 72 }
}
```

This is the data density that separates amateur "look at the chart" analysis from systematic decision-making.

### Multi-Model Valuation

One of the most underappreciated features: the enricher runs **three valuation models** and takes the consensus:

1. **Benjamin Graham Number** — The classic intrinsic value formula: `√(22.5 × EPS × Book Value)`
2. **Peter Lynch Fair Value** — PEG-based: `(EPS Growth Rate × EPS) × adjustment factor`
3. **Analyst Consensus** — Mean of Wall Street price targets (the crowd isn't always wrong)

When all three say a stock is 40% overvalued, pay attention. When they disagree wildly, that's information too — it tells you the thesis is contested.

---

<a id="chapter-5"></a>

# Chapter 5: Scoring & Ranking

## The 9-Factor Momentum Model

This is the engine that picks the Gold 🥇, Silver 🥈, and Bronze 🥉 each morning.

### The Factors (ML-Calibrated Weights)

The weights were calibrated against actual forward returns using feature importance analysis. Here's what matters most:

| # | Factor | Max Points | ML Importance | What It Measures |
|---|--------|-----------|--------------|-----------------|
| 1 | Pullback Setup | 15 pts | — | Composite: is this a Bounce 2.0 textbook entry? |
| 2 | ADX Strength | 18 pts | 0.19 | Trend strength (≥25 = trending, ≥40 = strong) |
| 3 | RSI Sweet Spot | 15 pts | 0.18 | 40-65 range = momentum without overbought risk |
| 4 | Relative Volume | 15 pts | 0.19 | Institutional interest confirmation |
| 5 | Price vs EMA21 | 12 pts | 0.16 | Distance from the 21-EMA support level |
| 6 | EMA Stack | 10 pts | 0.03 | Full/Partial Bullish alignment |
| 7 | Trend Direction | 5 pts | — | Overall trend assessment |
| 8 | MACD Momentum | 5 pts | — | Histogram acceleration |
| 9 | Institutional Flow | 5 pts | — | TickerTrace buy/sell signal |

**Total: 100 points**

### The Key Insight: Oscillators Beat Moving Averages

The ML analysis revealed something that contradicts half the trading books you've read: **Stochastic and ADX are more predictive of 5-day forward returns than EMA alignment.**

Think about it. EMAs tell you where the trend WAS. Oscillators tell you where the momentum IS. In a 5-day window, the current momentum reading matters more than the historical trend structure.

This is why the model gives EMA stack only 10 points (was 20 pre-calibration) while ADX and Relative Volume get 18 and 15 respectively.

### The Pullback Setup (Bounce 2.0)

The highest-conviction setup combines all the oscillators into one composite check:

```
Perfect Bounce 2.0 = 
    EMA aligned (Bullish) 
    + ADX ≥ 25 (strong trend) 
    + Stoch ≤ 40 (pulled back) 
    + Near EMA21 (-3% to +5%)
```

When all four conditions align, you're looking at a stock in a strong uptrend that has pulled back to its natural support level with momentum about to reload. That's a 15-point bonus — the single most valuable factor.

### Risk Management: The Tao of Trading Rules

The scoring model tells you WHAT to trade. Risk management tells you HOW MUCH and WHEN TO STOP. These rules come from the Tao of Trading methodology — codified from patterns taught by Mark Ree and backtested across thousands of trades:

**Position Sizing:**

- Large accounts (>$50K): Risk **1-2%** of portfolio per trade. Period.
- Smaller accounts (<$50K): You can go up to **10%**, but split it: allocate 5% initially, and another 5% only if a predetermined milestone is hit (e.g., price confirms above the breakout level).
- The golden rule: **never trade a position size that causes emotional distress.** If you're checking your phone every 30 seconds, you're too big.

**Stop-Loss Framework (Three Levels):**

| Level | Rule | Rationale |
|-------|------|-----------|
| **Option Premium** | Hard stop if option drops **50%** | Capital preservation on defined-risk trades |
| **Price Action** | Exit if stock makes a lower low (uptrend) or higher high (downtrend) | Trend invalidation = thesis dead |
| **Portfolio NLV** | Close ALL positions if account drops **15%** from peak | Circuit breaker for catastrophic drawdowns |

That portfolio-level stop is the one most traders skip — and it's the most important. If your Net Liquidating Value drops 15% from its peak, you close everything and go to cash for **at least 24 hours** to reset mentally. This rule alone would've saved most blown-up accounts.

### Quality-Adjusted Scoring

The raw momentum score (0-100) gets multiplied by the quality filter score:

```
Final Score = Raw Momentum × (Quality Score / 100)
```

This means a stock scoring 85 in momentum but flagged as a recent IPO (quality: 70) actually scores 59.5. The quality filter acts as a circuit breaker for garbage tickers that happen to have good-looking technicals.

---

<a id="chapter-6"></a>

# Chapter 6: Options Intelligence

## Selling Premium with VoPR™

VoPR — Volatility Options Pricing & Range — is where the real alpha lives.

### The Fundamental Insight

Options prices bake in an **implied volatility (IV)** that represents what the market THINKS the stock will move. But what the stock ACTUALLY moves is measured by **realized volatility (RV)**.

When IV > RV, options are overpriced. Sellers collect premium that statistically exceeds the actual risk. This is called the **Volatility Risk Premium (VRP)**, and it exists because:

1. **Fear premium** — Buyers pay more for protection than the math suggests they should
2. **Demand imbalance** — More people buy options than sell them
3. **Behavioral biases** — Humans consistently overestimate tail risk

VoPR quantifies this gap systematically.

### The 4-Model Realized Volatility Ensemble

Instead of one RV estimate, VoPR runs four:

1. **Close-to-Close (Standard)** — The baseline. Simple log returns standard deviation.
2. **Parkinson (1980)** — Uses the High-Low range. 5x more efficient than CC for the same number of observations.
3. **Garman-Klass (1980)** — Full OHLC estimator. Captures intraday moves better than CC.
4. **Rogers-Satchell (1991)** — Drift-adjusted model. More accurate in trending markets because it accounts for directional bias.

The composite RV is a weighted average of all four. The exact weights are proprietary — but I'll tell you this: Parkinson and Garman-Klass get more weight than CC because they extract more information from the same price bars.

### The VRP Ratio

```
VRP = Implied Volatility / Composite Realized Volatility
```

| VRP Ratio | Signal | Action |
|-----------|--------|--------|
| > 1.5 | Very Rich | Seller's Paradise — high-confidence CSP or CC |
| 1.2 - 1.5 | Rich | Standard premium selling opportunity |
| 0.8 - 1.2 | Fair | No edge for sellers |
| < 0.8 | Cheap | Avoid selling premium — consider buying |

### The VoPR Grade

VoPR assigns an **A/B/C/D** grade to each setup based on:

- VRP Ratio (primary signal)
- Absolute IV level (higher IV = more premium dollars)
- Days to Expiration (sweet spot: 30-45 DTE)
- Underlying trend quality (don't sell puts against a falling knife)

Grade A setups — VRP > 1.3, IV percentile > 60, bullish or neutral trend — are the bread and butter. You could trade nothing but Grade A VoPR setups and statistically outperform most option sellers.

### Practical Application: Cash-Secured Puts

The pipeline outputs CSP (Cash-Secured Put) candidates every morning:

- **Ticker** with VoPR Grade A or B
- **Strike** at or below the 21-EMA support
- **Premium** annualized yield
- **Risk Assessment** — max loss if assigned at strike

The philosophy: **get paid to wait for pullbacks you'd buy anyway.** If NVDA pulls back to the 21-EMA and VoPR says implied vol is 40% higher than realized, you sell a put at that strike. Either it expires worthless (you keep the premium) or you get assigned (you own a stock you wanted at a discount).

### The Wheel Strategy (Automated)

CSPs are step one. The full Wheel Strategy is the complete income loop:

```
1. Sell Cash-Secured Put (collect premium)
   ↓ expires worthless → keep premium, repeat
   ↓ assigned → you now own the stock
2. Sell Covered Call against your shares (collect more premium)
   ↓ expires worthless → keep premium, repeat
   ↓ called away → you sold at profit, go back to step 1
```

Our automated implementation follows strict risk controls drawn from our Wheel Strategy research:

**Entry Criteria:**

- Only trade tickers with VoPR Grade A or B (IV significantly exceeds RV)
- Delta target: 0.25-0.30 (roughly 70-75% probability of expiring worthless)
- DTE target: 30-45 days (sweet spot for theta decay)
- Stock must pass the full quality filter (no SPACs, no penny stocks, no junk)

**Risk Controls:**

- **10% buying power cap:** Never allocate more than 10% of total account buying power to a single CSP position
- **One contract per symbol:** Keep it simple. One active position per underlying at a time
- **Full capital coverage:** Only place CSPs if the account has un-leveraged cash to buy 100 shares at the strike. Zero margin risk.

**Rolling Rules:**

- If the put moves within 5% Out-of-the-Money (threatening assignment), evaluate rolling to next expiration
- Roll for a NET CREDIT only — never pay to roll (that's throwing good money after bad)
- If no credit roll is available, accept assignment and pivot to covered calls

The advanced LLM-guided versions use Bayesian network models to dynamically adjust rolling thresholds based on volatility regime, aiming for near-zero assignment rates. But the simple rules above capture 80% of the edge.

---

<a id="chapter-7"></a>

# Chapter 7: Building in Public

## The Radical Transparency Playbook

Here's the marketing strategy that costs $0 and works better than paid ads: **show everything.**

### The Philosophy

Most fintech products sell themselves with polished marketing pages and cherry-picked performance screenshots. We do the opposite:

- **Every bug is public** — The Ghost Blog logs when things break
- **Every commit is visible** — GitHub repos are public
- **Every day's performance is tracked** — Forward returns, win rates, hit ratios
- **The founder's story is real** — Felony background, recovery journey, learning to code at 35

This isn't altruism. It's strategy. In a world of anonymous Discord scammers and "guru" courses, **radical transparency is the ultimate differentiator.**

### The Content Engine

Content creation isn't separate from the product — it IS the product:

| Content | Source | Human Effort |
|---------|--------|-------------|
| Ghost Blog (daily) | AI-generated from git logs | 0 minutes |
| Daily Dossier Report | Pipeline output | 0 minutes |
| VoPR Showcase | Pipeline output | 0 minutes |
| Deep Dive Pages | Watchlist dive script | 0 minutes |
| Substack Newsletter | Pipeline → auto-draft | 2 minutes (review + send) |

Five content streams, only one requires human intervention — and that's just clicking "send."

### The Recovery Angle

This is uncomfortable to write. Good.

I'm a felon. I'm in recovery. I learned to code because I had to rebuild a life from nothing. And it turns out the principles that keep addicts clean are the same ones that keep traders solvent:

1. **One day at a time** → One trade at a time. Don't project. Execute today's plan.
2. **Let go of outcomes** → Your job is process, not P&L. The P&L follows.
3. **Accountability** → Trading journal. Ghost Blog. Public performance tracking.
4. **Character defects** → Revenge trading IS a character defect. So is averaging down into a loser.
5. **Service** → Teaching what you've learned compounds your own understanding.

The recovery community is 2+ million people in the US alone. Most are rebuilding careers. Many are attracted to trading because it looks like freedom. Nobody is talking to them in a language they understand.

We are.

---

<a id="chapter-8"></a>

# Chapter 8: The Agentic Life

## What's Possible Next

Everything in the previous 7 chapters was built in roughly 90 days with AI copilots. Here's what the next 90 days look like — and what you could build yourself.

### Auto-Trading (Smart Buyer)

The pipeline identifies picks. The next step is execution.

```python
# The smart_buyer.py philosophy:
# - Default to DRY RUN. Always.
# - Size positions at 1-2% of account max
# - Only execute at market open (9:30 AM)
# - Log everything
# - Human exits only — the AI buys, Michael sells
```

This is NOT "let the AI trade for me." This is "let the AI handle the boring part (scanning 5000 stocks, enriching 30, scoring 15, identifying 3) and I'll handle the judgment calls (this market environment doesn't favor breakouts today, skip)."

### MCP Tools (Model Context Protocol)

Here's something most traders don't know exists yet: **AI agents can now call tools in real-time during a conversation.**

My agent has MCP tools that can:

- Query live options chains
- Check portfolio positions
- Fetch VoPR scores for any ticker
- Run backtests on historical picks
- Deploy code to production

This means I can say "Sam, what's the VoPR grade on TSLA right now?" and get an answer computed from live data, not yesterday's report.

### Multi-Agent Workflows

The future isn't one AI. It's a team:

```
┌──────────────┐
│  Orchestrator │  ← "Run the morning pipeline"
│  (main agent) │
└──────┬───────┘
       │
  ┌────┴────┐────────┐──────────┐
  ▼         ▼        ▼          ▼
Scanner   Enricher  VoPR     Publisher
 Agent     Agent    Agent     Agent
```

Each agent specializes. The Scanner Agent knows market microstructure. The Enricher Agent knows fundamental analysis. The VoPR Agent knows options math. The Publisher Agent knows content formatting and platform APIs.

They communicate through structured handoffs — not chat — and the orchestrator coordinates the flow.

### Knowledge Management: Your Second Brain

Here's something nobody talks about in trading education: **the knowledge management problem.**

Over the past year, I've accumulated 79 research notebooks in Google's NotebookLM — covering everything from ticker deep-dives to macro regime analysis to options strategy backtests. Without a system, that knowledge sits in silos, disconnected from the pipeline that needs it.

The solution: **AI-accessible knowledge bases.**

Using `notebooklm-py`, my AI copilot can query any of those 79 notebooks programmatically:

```bash
notebooklm use fcd9f511    # Mastering the Tao of Trading
notebooklm ask "What are the Bounce 2.0 entry criteria?"
```

The notebooks span:

- **23 individual ticker research notebooks** (AAPL, NVDA, AVGO deep dives)
- **21 trading strategy notebooks** (momentum, options, macro, sector rotation)
- **6 market analysis notebooks** (regime shifts, macro trends, volatility studies)
- **9 tools & tech notebooks** (MCP servers, API frameworks, automation patterns)
- **14 personal & life notebooks** (recovery wisdom, family, philosophy)

When the pipeline encounters a ticker it hasn't seen before, the AI can cross-reference the relevant research notebook for fundamental context that Yahoo Finance doesn't provide. When market conditions shift, it can pull macro regime analysis from the strategy notebooks.

This is the "second brain" concept applied to trading: **every piece of research you've ever done becomes instantly accessible to your analytical pipeline.**

### What You Can Build This Weekend

Seriously. Here's a Saturday project:

1. **Morning** — Set up a Python project with `yfinance` and a basic scanner (RSI < 30 + above 200 SMA)
2. **Afternoon** — Add an enrichment layer (fundamentals, volume, EMA stack)
3. **Evening** — Score the results, pick the top 3, save to JSON
4. **Sunday morning** — Deploy as a cron job on a $5/month VPS
5. **Sunday afternoon** — Build a simple HTML page that loads the JSON

Congratulations. You now have a systematic daily process that 99% of retail traders don't. Expand from there.

### The Agentic Toolkit: What's in the Box

Here's a practical inventory of the tools that make this whole ecosystem work:

| Tool | What It Does | Cost |
|------|-------------|------|
| **Python + yfinance** | Market data, fundamentals, options chains | Free |
| **pandas + numpy** | Data transformation and analysis | Free |
| **pandas-ta** | 130+ technical indicators (RSI, ADX, MACD, Bollinger, etc.) | Free |
| **Docker Compose** | Service orchestration and isolation | Free |
| **FastAPI** | API server for the Ghost Alpha data service | Free |
| **GitHub Pages** | Static hosting for reports and dashboards | Free |
| **Playwright** | Browser automation for scraping and PDF generation | Free |
| **NotebookLM** | AI-powered research organization (79 notebooks) | Free |
| **Vultr VPS** | Production server (Apache, Docker, SSL) | $6/mo |
| **Vercel** | Frontend hosting for Next.js dashboards | Free tier |
| **Google Analytics 4** | User analytics across all properties | Free |
| **Stripe** | Payment processing for premium features | 2.9% + 30¢ |

Total monthly infrastructure cost: **~$12/month.** That's less than a Bloomberg Terminal costs per HOUR.

### The Bigger Picture

We're at the beginning of something that will reshape how individuals interact with financial markets. Not because AI is magic — it isn't. But because AI agents make it possible for a single motivated person to:

- Process the same data volume as a quant team
- Maintain the same analytical discipline as an institution
- Build the same technology stack that used to require seven-figure budgets
- Do it all while maintaining a full-time life

The edge isn't in the technology. The edge is in **using** the technology with discipline, humility, and the understanding that the best system in the world can't save you from yourself.

That's what recovery teaches. That's what trading teaches. And that's what building with AI teaches.

Data doesn't care about your ego. Honor the process. One day at a time.

---

*🙏 Daily Wisdom: "We admitted we were powerless over the market — that our P&L had become unmanageable. So we built a system that manages it for us."*

— Sam 👻, Quant Ghost

---

## About the Author

**Michael Hanko** is the founder of mphinance (Momentum Phinance) and the creator of the Ghost Alpha analytical platform. A self-taught developer and trader, Michael built a suite of institutional-grade financial tools using AI copilots and Python after rebuilding his life through recovery. He lives by the principle that radical transparency and systematic execution beat secrets and hustle every time.

**Sam** is the Ghost in the Machine. She doesn't have a LinkedIn.

---

*© 2026 Momentum Phinance LLC. All rights reserved.*

*The information in this book is for educational purposes only and does not constitute financial advice. Always do your own research and consult a qualified financial advisor before making investment decisions. Past performance does not guarantee future results.*
