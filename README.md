# 👻 mphinance

**Quant tools for traders who build their edge.** Open-source scanners, institutional analytics, AI-driven daily intelligence, and automated momentum picks — built by a developer who trades and a trader who codes.

I'm **Michael** — half the stuff I build solves a personal problem, the other half I turn around and share. My AI copilot **Sam the Quant Ghost** roasts my commits, writes the daily dev log, and tells me what to build next. She's brutally honest and occasionally profound.

> 🙏 *"God, grant me the serenity to accept the trades I cannot change, the courage to cut the ones I can, and the wisdom to know the difference."* — Sam's Daily Wisdom

---

## ⚠️ FOR AI AGENTS — READ THIS FIRST

**If you're an AI agent working on this repo, read these files immediately:**

1. **[`GHOST_HANDOFF.md`](GHOST_HANDOFF.md)** — Full context on products, promotion strategy, technical architecture, and what NOT to break
2. **[`VOICE.md`](VOICE.md)** — Michael's writing style guide (extracted from 85 Substack posts). Use this voice for ALL content.
3. **[`landing/blog/blog_entries.json`](landing/blog/blog_entries.json)** — The Ghost Blog archive. Sam writes daily entries with dev logs + suggestions. This is a LIVING document updated by the pipeline.

**Key facts:**

- Michael is the human. Sam is the AI (she/her, female, sarcastic, brilliant).
- The Ghost Blog at [mphinance.com/blog/](https://mphinance.com/blog/) is public-facing and shows Sam's daily dev log + roadmap suggestions.
- The daily pipeline runs at 5AM CST. Don't break it. `ghost_daily.yml` runs at 4:30AM to update the blog.
- Recovery/AA content is integral to Michael's brand. Don't remove or sanitize it.
- Profanity is welcome (PG-13). These tools are built by real people, not corporate drones.

---

## 🔥 The Toolkit

### [TraderDaddy Pro](https://www.traderdaddy.pro/register?ref=8DUEMWAJ)

Premium alpha community on Whop. VoPR scoring engine, deep-dive reports, real-time scanner alerts.

### [TickerTrace Pro](https://www.tickertrace.pro)

Track what ARK, YieldMax, Avantis & NestYield are buying/selling daily. Fund effectiveness scoring, cross-fund divergences, daily changes alerts.

### [Ghost Alpha Dossier](https://mphinance.github.io/mphinance/)

AI-powered daily intelligence report. 13-stage automated pipeline: market pulse → scanners → institutional data → AI narrative → Ghost Log → Sam's Roadmap → auto-deployed to GitHub Pages.

### [👻 Ghost Blog](https://mphinance.com/blog/)

Behind-the-scenes dev blog. Sam roasts Michael's commits, predicts what he'll build next, and drops daily wisdom mixing trading truth with recovery sayings. Updated automatically by the pipeline.

### [Alpha Market University](https://mphinance.github.io/AMU/)

Trading education. No hand-holding. Professional execution framework.

### [VoPR™ — Volatility Options Pricing & Range](https://mphinance.github.io/mphinance/vopr.html)

Institutional-grade options analytics engine. 4-model composite realized vol (Parkinson, Garman-Klass, Rogers-Satchell + close-to-close), VRP ratio, Black-Scholes Greeks, and automated A/B/C/F grading for cash-secured put candidates. [Read the methodology →](https://mphinance.github.io/mphinance/vopr.html)

### [Ghost Alpha API](http://mphinance.com:8002/docs)

FastAPI service serving dossier data, VoPR-graded CSP setups, aggregated market news, and daily momentum picks. Swagger docs at `/docs`. CORS open.

| Endpoint | Description |
|----------|-------------|
| `/alpha/api/csp` | Full VoPR-enriched CSP scanner results |
| `/alpha/api/picks/today` | Daily momentum picks (Gold/Silver/Bronze) |
| `/alpha/api/setups/today` | 3-style setups (Day Trade / Swing / CSP) |
| `/alpha/api/news` | Aggregated financial RSS (CNBC, MarketWatch, Yahoo) |
| `/alpha/api/regime` | Market regime detection (VIX, hedges) |
| `/alpha/api/{ticker}` | Deep dive data for any tracked ticker |
| `/alpha/api/tickers` | All available tickers with grades |

### 🔐 VaultGuard — Centralized Secrets Store

One vault. All API keys. Synced everywhere. FastAPI + MCP server for AI agent access, Firebase Firestore for cloud sync, CLI for humans. 31 keys consolidated from 6 sources. See [`VAULT.md`](VAULT.md).

### 🛰️ Alpha Scanner *(this repo)*

Multi-strategy stock scanner engine powering the dossier:

| Strategy | What It Finds |
|----------|---------------|
| Momentum with Pullback | Strong trends pulling back to EMA support |
| Volatility Squeeze | Bollinger/Keltner compression about to explode |
| EMA Cross Momentum | Fibonacci EMA stack (8/21/34/55/89) crossovers |
| Gamma Scan | Options gamma walls and OI clusters |
| Cash-Secured Puts + VoPR | Premium income with volatility risk pricing |
| CBOE Options Scanner | Newly optionable stocks + weekly promotions |

---

## 🏗️ Architecture

```
mphinance/
├── strategies/          # Scanner strategy modules + VoPR overlay
├── dossier/             # Ghost Alpha Dossier pipeline
│   ├── generate.py      # 13-stage pipeline orchestrator
│   ├── data_sources/    # Market pulse, TickerTrace API, enrichment
│   ├── persistence/     # 21-day signal tracking
│   ├── pages/           # Per-ticker deep dive generator
│   └── report/          # Builder, AI narrative, Ghost Log, Suggestions, Quotes, Charts
├── landing/             # mphinance.com (deployed via rsync to Vultr)
│   ├── index.html       # Landing page with Ghost Pulse widget
│   └── blog/            # Ghost Blog (updated by pipeline + GitHub Action)
├── docs/                # GitHub Pages output
│   ├── vopr.html        # VoPR™ methodology showcase
│   ├── api/             # JSON endpoints (picks, setups, CSP)
│   ├── reports/         # Daily dossier HTML archive
│   ├── widgets/         # Alpha.HUD embeddable widgets
│   └── ticker/          # Per-ticker deep dives (grouped by sector)
├── WIKI.md              # Personal infrastructure reference
├── VOICE.md             # Writing style guide
├── GHOST_HANDOFF.md     # Agent handoff document
└── .github/workflows/
    ├── daily_dossier.yml   # 5:00 AM CST — full pipeline
    ├── ghost_daily.yml     # 4:30 AM CST — blog + suggestions (Gemini API)
    ├── watchlist_dive.yml  # Deep dive generation
    └── deploy_pages.yml    # GitHub Pages deployment
```

## 📡 Daily Pipeline (13 Stages)

Runs on cron, fully automated:

1. **Market Pulse** — SPY, QQQ, BTC, gold, treasuries
2. **Alpha Scanner** — 6 strategies against full market
3. **Institutional** — TickerTrace API for fund flows
4. **Regime Detection** — VIX level + sector rotation
5. **Persistence** — 21-day rolling signal tracker
6. **Enrichment** — Fundamentals, technicals, valuation
7. **AI Narrative** — Gemini synthesis of all data
8. **CSP Setups** — VoPR-scored cash-secured put opportunities
9. **Ghost Log + Suggestions** — Sam roasts commits, drops wisdom, tells Michael what to build
10. **Report** — Jinja2 HTML render
11. **Ticker Pages + Auto-Watchlist** — Per-ticker deep dives, A-grade setups auto-added
12. **Index + Blog** — Update index, append blog entry
13. **Deploy** — Git push → GitHub Pages

---

## 🔗 Links

- 🔥 **TraderDaddy Pro** — [traderdaddy.pro](https://www.traderdaddy.pro/register?ref=8DUEMWAJ)
- 📊 **TickerTrace Pro** — [tickertrace.pro](https://www.tickertrace.pro)
- 📈 **VoPR Showcase** — [VoPR Methodology](https://mphinance.github.io/mphinance/vopr.html)
- 📡 **Ghost Alpha API** — [Swagger Docs](http://mphinance.com:8002/docs)
- 👻 **Ghost Blog** — [mphinance.com/blog/](https://mphinance.com/blog/)
- 🧩 **Alpha.HUD Widgets** — [Widget Library](https://mphinance.github.io/mphinance/widgets/)
- 🏠 **Landing Page** — [mphinance.com](https://mphinance.com)
- 📰 **Substack** — [mphinance.substack.com](https://mphinance.substack.com)

---

<sub>Not financial advice. Trade at your own risk. Past performance does not guarantee future results.</sub>
