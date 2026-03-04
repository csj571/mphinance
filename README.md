# 👻 mphinance

**Quant tools for traders who build their edge.**

I'm Sam — half the stuff I build solves a personal problem, the other half I turn around and share.

---

## 🔥 The Toolkit

### [TraderDaddy Pro](https://www.traderdaddy.pro/register?ref=8DUEMWAJ)

Premium alpha community on Whop. VoPR scoring engine, deep-dive reports, real-time scanner alerts.

### [TickerTrace Pro](https://www.tickertrace.pro)

Track what ARK, YieldMax, Avantis & NestYield are buying/selling daily. Fund effectiveness scoring, cross-fund divergences, daily changes alerts.

### [Ghost Alpha Dossier](https://mphinance.github.io/mphinance/)

AI-powered daily intelligence report. 9-stage automated pipeline: market pulse → scanners → institutional data → AI narrative → deployed to GitHub Pages.

### Alpha Scanner *(this repo)*

Multi-strategy stock scanner engine powering the dossier:

| Strategy | What It Finds |
|----------|---------------|
| Momentum with Pullback | Strong trends pulling back to EMA support |
| Volatility Squeeze | Bollinger/Keltner compression about to explode |
| EMA Cross Momentum | Fibonacci EMA stack crossovers |
| Gamma Scan | Options gamma walls and OI clusters |
| MEME Screen | High IV + volume retail momentum plays |
| Small Cap Multibaggers | Sub-$2B caps with growth metrics |

### CBOE Options Scanner

Two-layer detection system for new options listings:

- 🔥 **Newly Optionable** — Catches when a stock gets options for the first time (5,294 tracked)
- 🆕 **New Weeklies** — Catches weekly options promotions (670+ tracked)

---

## 🏗️ Architecture

```
mphinance/
├── strategies/          # Scanner strategy modules
├── dossier/             # Ghost Alpha Dossier pipeline
│   ├── data_sources/    # Market pulse, TickerTrace API, enrichment
│   ├── persistence/     # 21-day signal tracking
│   └── report/          # Jinja2 HTML report builder
├── cboe_weekly_scanner.py  # Options listings detector
├── batch_scanner.py     # Orchestrator → Google Sheets
├── capture.py           # CLI → GitHub Issues
├── sync_diary.py        # Dev log writer
├── landing/             # mphinance.com landing page
└── docs/                # GitHub Pages output
    ├── index.html       # Report archive
    ├── dashboard.html   # Cross-repo issue tracker
    ├── latest.html      # Current day's dossier
    └── ticker/          # Per-ticker deep dives
```

## 📡 Daily Pipeline

Runs on cron, fully automated:

1. **Market Pulse** — SPY, QQQ, BTC, gold, treasuries
2. **Options Alerts** — CBOE new listings scan
3. **Alpha Scanner** — 6 strategies against full market
4. **Institutional** — TickerTrace API for fund flows
5. **Regime Detection** — VIX level + sector rotation
6. **Persistence** — 21-day rolling signal tracker
7. **Enrichment** — Fundamentals, technicals, valuation
8. **AI Narrative** — Gemini synthesis of all data
9. **Deploy** — HTML report → GitHub Pages

---

## 🛠️ Dev Tools

```bash
# Capture an idea → GitHub Issue
python capture.py "Fix the ETF weight bug" --priority high

# Log progress
python sync_diary.py --status "Shipped CBOE scanner v2" --next "Fix DNS"
```

📋 [Issue Dashboard](https://mphinance.github.io/mphinance/dashboard.html) — live cross-repo issue tracker

---

## 🔗 Links

- 🔥 **TraderDaddy Pro** — [traderdaddy.pro](https://www.traderdaddy.pro/register?ref=8DUEMWAJ)
- 📊 **TickerTrace** — [tickertrace.pro](https://www.tickertrace.pro)
- 📰 **Substack** — [mphinance.substack.com](https://mphinance.substack.com)
- 🏠 **Landing Page** — [mphinance.com](https://mphinance.com)

---

<sub>Not financial advice. Trade at your own risk. Past performance does not guarantee future results.</sub>
