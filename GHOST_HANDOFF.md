# 👻 GHOST HANDOFF — Session Close 2026-03-06

## What Just Happened

### Shipped

- **📕 "The Agentic Trader's Playbook" Ebook** — 8 chapters, 685 lines. Covers the thesis, tech stack, AI persona, data pipeline, 9-factor scoring, VoPR, building in public, and the agentic future. Enriched from 4 NotebookLM notebooks (Tao of Trading, AI Trading Guide 2026, Wheel Strategy, CSP analysis).
- **Stripe Checkout** — `landing/ebook_checkout.py` FastAPI endpoint for $19 one-time purchase. Uses env var for Stripe key (NOT hardcoded — GitHub secret scanning taught us that).
- **Ebook Buy Section** — Purple gradient CTA on landing page between stats and analytics sections.
- **Quality Filter Upgrades** — `quality_filter.py` now detects ETFs (80pt penalty), ADRs (20pt), and recent IPOs (<6mo = 30pt, <1yr = 10pt).
- **Market Breadth Analysis** — `market_regime.py` now calculates % above 200SMA, % above 50SMA, advance/decline ratio, and composite breadth score (0-100).
- **GA4 Expansion** — Analytics Pulse widget now tracks TickerTrace + Substack (4 properties total). Real data flowing: 1,116 pageviews, 172 users from Substack.
- **Responsive Analytics Widget** — 4→2→1 column CSS breakpoints for mobile.
- **Ghost Blog Entry** — Session recap added.

### NOT Shipped (Next Session)

- [ ] Deploy ebook checkout server on Vultr (uvicorn + Docker + Apache proxy + STRIPE_SECRET_KEY env var)
- [ ] Wire `auto_backtest.py` into daily pipeline as Stage 14
- [ ] Factor correlation analysis (needs 30+ days of picks data first)
- [ ] Sector-relative scoring in `momentum_picks.py`
- [ ] API request logging middleware for Ghost Alpha

## Key Info for Next Agent

- **Ebook source:** `landing/ebook/the-agentic-traders-playbook.md` (685 lines)
- **Ebook HTML:** `landing/ebook/the-agentic-traders-playbook.html` (styled, dark theme)
- **Ebook checkout:** `landing/ebook_checkout.py` (needs STRIPE_SECRET_KEY env var to run)
- **Stripe key:** In VaultGuard (`secrets.env` → `STRIPE_SECRET_KEY`)
- **GA4 stats:** `dossier/fetch_ga4_stats.py` fetches for 4 properties, outputs to `landing/data/ga4_stats.json`
- **GA4 token:** `dossier/ga4_token.json` (OAuth cached)
- **Build ebook HTML:** `pip3 install markdown && python3 /tmp/build_ebook.py`
- **NotebookLM CLI:** `notebooklm` (installed at `/home/sam/.local/bin/notebooklm`)

## Deploy Commands

```bash
# Landing page (includes ebook + analytics)
rsync -avz landing/ vultr:/home/mphinance/public_html/

# Push to GH Pages
git push  # auto-deploys via GH Actions

# Start ebook checkout (local testing)
STRIPE_SECRET_KEY=sk_live_... uvicorn landing.ebook_checkout:app --port 8300
```
