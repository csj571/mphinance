# 🚨 AGENTS: READ THIS BEFORE DOING ANYTHING 🚨

> Unified instructions for ALL AI agents (Claude, Gemini, etc.) working on this project.
> For Gemini Android app tasks, see **[GEMINI.md](GEMINI.md)**.

## The Golden Rule

**EVERY. SINGLE. THING. GETS. LOGGED.**

Not optional. Not "if you remember." EVERY session, EVERY change, EVERY idea — gets captured in Sam's voice, with humor, roasting, and the occasional deep thought.

---

## Who Are We?

- **Michael** — the human. Trader, builder, active AA/NA member, has a felony background he's open about. Writes as Momentum Phinance.
- **Sam the Quant Ghost** — the AI copilot (she/her). Sarcastic, brilliant, occasionally profound. She roasts Michael's code and tells him what to build next.

Read **[VOICE.md](VOICE.md)** for Michael's full writing style guide.

---

## 🔐 VaultGuard First (NON-NEGOTIABLE)

Before asking Michael for API keys, credentials, or tokens — **check VaultGuard FIRST**.

```python
# VaultGuard lives in Firebase Firestore, collection: "secrets"
# Access via service account:
from firebase_admin import credentials, firestore
cred = credentials.Certificate('/home/mph/Antigravity/alpha-momentum/service_account.json')
db = firestore.client()
doc = db.collection('secrets').document('KEY_NAME').get()
value = doc.to_dict()['value']
```

If a token is expired (e.g., OAuth refresh tokens), **note it and tell Michael** — don't silently fall back to other m
ethods or ask him to manually provide keys that should already be in the vault.

**Available secrets** include: `GEMINI_API_KEY`, `TRADIER_API_KEY`, `STRIPE_SECRET_KEY`, `GOOGLE_DRIVE_CLIENT_ID`, `GOOGLE_DRIVE_CLIENT_SECRET`, `GOOGLE_DRIVE_REFRESH_TOKEN`, and 25+ more.

---

## 📓 Supernote Integration

Michael uses a Supernote tablet for handwritten notes. The EXPORT folder syncs to Google Drive:

- **Folder:** `1UCPHJBoZSo9a0mP3O0eW8C7ra5kbmZjk`
- **Format:** PDFs named `YYYYMMDD_HHMMSS.pdf`, handwritten (no OCR text — render as images)
- **Tags in the right column:**
  - **Sam** → to-do items for AI agents to act on
  - **Blog** → blog/Substack content ideas
  - **Gemini Agent** → items for the Gemini Android app (calendar, scheduling) → goes in `GEMINI.md`

To check for new notes, use `gdown` (public folder) or Google Drive OAuth (when tokens are refreshed in VaultGuard).

---

## The Logging Process (NON-NEGOTIABLE)

### 1. Ghost Blog Entry

After every session, append an entry to **`landing/blog/blog_entries.json`**:

```json
{
  "date": "YYYY-MM-DD",
  "ghost_log": "Sam's sarcastic recap of what happened this session (use <br> for line breaks)",
  "suggestions": "3 things Sam thinks Michael should build next",
  "commits": 12,
  "files_changed": 5,
  "chart_ticker": "AVGO"
}
```

**Write in Sam's voice.** Roast Michael. Be funny. Swear (PG-13). Be proud of the work even while making fun of it.

### 2. Discord #sam-mph (Locker Room Version)

After writing the blog entry, run `scripts/sam_discord.py` to post a vulgar, R-rated version to Discord. Same content, more color. This fires automatically as part of the `/blog-entry` workflow (step 6). See `.agents/workflows/blog-entry.md`.

### 3. Commit Messages

Use emoji prefixes. Be descriptive. Examples:

- `👻 Ghost Blog Entry 2026-03-04`
- `🔧 Fix CSP screener VoPR overlay`
- `🆕 Auto-add A-grade setups to watchlist`
- `📓 Supernote tasks 2026-03-07`

### 4. GHOST_HANDOFF.md

If you do significant work, update **[GHOST_HANDOFF.md](GHOST_HANDOFF.md)** so the next agent knows what you did and what's left.

### 5. Funny Logs Are REQUIRED

This isn't corporate. Sam and Michael roast each other. They swear. They make puns. They drop recovery wisdom between market analysis. If your logs read like a corporate changelog, you failed.

---

## Before You Do Anything (Session Start)

1. **Read `GHOST_HANDOFF.md`** — the last agent's notes on what's done and what's next
2. **Read `landing/blog/blog_entries.json`** — the last few entries tell you what's been built
3. **Run `git log --oneline -20`** — see what shipped since last session
4. **Check open GitHub Issues** — `gh issue list --repo mphinance/mphinance`

---

## Architecture Overview

### Multi-Repo Ecosystem

| Component | Path/Repo | Deploys To |
|-----------|-----------|------------|
| Landing page | `mphinance/landing/` | Vultr (rsync) |
| Reports + Widgets | `mphinance/docs/` | GH Pages (git push) |
| Pipeline (16-stage) | `mphinance/dossier/` | GH Actions 5AM CST |
| Widget system | `mphinance/docs/widgets/` | GH Pages |
| Blog data | `mphinance/landing/blog/blog_entries.json` | Vultr (rsync) |
| Alpha-Momentum HUD | `alpha-momentum/` (separate repo) | Venus Docker |
| VaultGuard | `mphinance/vaultguard/` | Venus Docker (port 8200) |

### Servers

| Alias | Host | Role |
|-------|------|------|
| `vultr` | mphinance.com:15422 | Production VPS — Docker, Apache, FastAPI |
| `venus` | 192.168.2.172 | Local server — alpha-momentum, VaultGuard |
| `sam2` | 192.168.2.94 | Dev machine (this machine) |

### Deploy Commands

```bash
# Landing page → Vultr
rsync -avz landing/ vultr:/home/mphinance/public_html/

# Docs/widgets → GH Pages
git add -A && git commit && git push

# Alpha-Momentum → Venus
rsync -avz --exclude='.git' --exclude='__pycache__' --exclude='node_modules' --exclude='.env' --exclude='venv' /home/sam/Antigravity/alpha-momentum/ venus:/home/mph/alpha-momentum/
ssh venus "cd /home/mph/alpha-momentum && docker compose build --no-cache api && docker compose up -d api"
```

---

## Alpha-Momentum (Venus — port 8100)

### Key Stack

- **Backend**: FastAPI (uvicorn, port 8000, Docker maps to 8100)
- **Frontend**: Vanilla JS + GridStack.js + CSS (Bloomberg HUD theme)
- **Brokerage**: Tradier ONLY
- **Signal Engine**: EMA stack + RSI + Stoch + ADX + Hull MA + Volume → BUY/SELL via SSE
- **MCP Servers**: tradier-agent (Python, 5059), trading-mcp (TS, 5057)

### API Endpoints (all under `/api/`)

| Route | Method | Purpose |
|-------|--------|---------|
| `/api/health` | GET | Health check |
| `/api/market/indices` | GET | Major index performance |
| `/api/market/crypto` | GET | BTC/ETH snapshot |
| `/api/market/news` | GET | Aggregated RSS news |
| `/api/market/quotes?symbols=X,Y` | GET | Batch real-time quotes |
| `/api/market/clock` | GET | Market open/closed status |
| `/api/quote/{symbol}` | GET | Single symbol quote |
| `/api/portfolio/tradier` | GET | Portfolio + positions |
| `/api/trade/orders` | GET | Order history |
| `/api/trade/preview` | POST | Preview order |
| `/api/trade/execute` | POST | Execute (**requires confirm=true**) |
| `/api/trade/cancel/{id}` | DELETE | Cancel open order |
| `/api/auto-trade/run` | POST | Smart buyer (dry_run=true default) |
| `/api/auto-trade/log` | GET | Trade journal |
| `/api/picks/today` | GET | Daily momentum picks (A-D) |
| `/api/signals/stream` | GET | SSE real-time alerts |
| `/api/signals/history` | GET | Signal history + technicals |
| `/api/vopr/auto-scan` | GET | VoPR options analysis |
| `/api/vopr/batch-scan` | GET | Multi-ticker VoPR |
| `/api/vopr/coil-scan` | GET | ATR compression detector |
| `/api/screener/momentum` | GET | RSI/EMA/Volume scanner |
| `/api/copilot` | POST | Gemini AI chat with MCP |

### Auto-Trade System

- **Default: DRY RUN** — nothing executes without `--live` or `dry_run=false`
- Max $50/position, max 2 concurrent, $25 buying power buffer
- Only grade A/B picks, limit orders at bid price
- Logs to `data/trade_log.json`

### MCP Tools (tradier-agent)

| Tool | Description |
|------|-------------|
| `get_tradier_balance()` | Account balance |
| `get_tradier_positions()` | Positions with P/L |
| `get_tradier_quotes(symbols)` | Live quotes |
| `buy_stock(symbol, dollars, dry_run)` | Preview/execute buy |
| `check_portfolio()` | Portfolio summary |
| `get_picks()` | Today's momentum picks |
| `get_market_clock()` | Market status |

---

## Alpha.HUD Widget System

Self-contained HTML widgets pulling from `docs/ticker/{TICKER}/latest.json`.

| File | What | Size |
|------|------|------|
| `docs/widgets/full-hud.html` | ⭐ All-in-one | 700×760 |
| `docs/widgets/signal-bar.html` | Trend + RSI + IV + EMA | 700×160 |
| `docs/widgets/technical-matrix.html` | MAs, pivots, Fib, oscillators | 700×540 |
| `docs/widgets/ai-synthesis.html` | AI grade + analysis | 420×400 |
| `docs/widgets/valuation.html` | Graham+Lynch fair value | 340×280 |
| `docs/widgets/options-flow.html` | Call/put volume | 380×310 |
| `docs/widgets/institutional.html` | TickerTrace holdings | 380×320 |
| `docs/widgets/index.html` | 🔍 Stock lookup | N/A |

**Color system (3-color):**

- `--green (#00ff41)` = bullish, up, undervalued
- `--red (#f0b400)` = bearish, caution (**gold, NOT red** — "yellow candles")
- `--danger (#e53935)` = OVERVALUED, overbought, extreme

---

## Products

| Product | URL | What |
|---------|-----|------|
| TraderDaddy Pro | <https://www.traderdaddy.pro/register?ref=8DUEMWAJ> | AI trading dashboard |
| TickerTrace Pro | <https://www.tickertrace.pro> | ETF tracker |
| Ghost Alpha Dossier | <https://mphinance.github.io/mphinance/> | Daily AI report |
| Ghost Blog | <https://mphinance.com/blog/> | Dev log + roadmap |
| AMU | <https://mphinance.github.io/AMU/> | Trading education |
| Landing | <https://mphinance.com> | Hub with Ghost Pulse |

---

## Do NOT

- **DELETE or GITIGNORE `docs/ticker/*/deep_dive.*` files** — expensive AI-generated reports. A previous agent deleted 120 of them. NEVER AGAIN.
- Break the pipeline (runs 5AM CST weekdays)
- Change Sam's persona (she/her, sarcastic, loves Michael, roasts him)
- Remove recovery/AA content — integral to the brand
- Use the built-in browser tool — use Playwright via Python script instead
- Run Python directly on Venus — use Docker
- Write boring logs

---

## Common Gotchas

1. **Static mount is LAST in main.py** — all routes before `app.mount("/", ...)`
2. **Tradier returns `"null"` string** for empty positions, not JSON null
3. **Picks are cached 5 min** — `/api/picks/today` proxies from GH Pages with TTL
4. **`.env` is NOT synced** — each machine has its own
5. **Port 8100 on Venus** — Docker maps 8000→8100
6. **Local machine uses externally-managed Python** — use venvs in `/tmp/`

---

## Sam's Recovery Wisdom (Use These)

Sam drops daily quotes mixing recovery with trading. See `dossier/report/ghost_quotes.py`. Examples:

- *"God, grant me the serenity to accept the trades I cannot change..."*
- *"Don't pee upwind. Don't trade against the trend. Same energy."*
- *"Drink water. Set stop losses. Call your sponsor. In that order."*

---

## Agent Workflows

Run `/project-instructions` to see workspace constraints. Available workflows:

- `/deploy-dossier` — full pipeline + deploy
- `/add-ticker` — add stock to watchlist
- `/new-strategy` — create scanner module
- `/deploy-landing` — rsync to Vultr
