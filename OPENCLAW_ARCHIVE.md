# OpenClaw Archive — sam2 Shutdown Reference

> **Purpose:** Everything needed to recreate an OpenClaw-like agent using the existing Gemini install on Venus.
> Captured from `sam2:/home/sam/.openclaw/` on 2026-03-07.

## Agent Configuration (`openclaw.json`)

### Models

| Role | Model | Fallback |
|------|-------|----------|
| Primary | `google/gemini-3-flash` | `google/gemini-3-pro` |
| Heartbeat | `google/gemini-2.5-flash-lite` | — |
| Image | `google/gemini-3-flash` | `openai/gpt-5.2` |
| Subagents | `google/gemini-3-flash` | — |

- Context tokens: 200,000
- Max concurrent agents: 2
- Subagent archive after: 60 min
- Heartbeat: every 30 min

### API Keys & Tokens

| Key | Value | Notes |
|-----|-------|-------|
| Brave Search | `BSAY-s7Y-uvTDiKKc43WIHRXy9S8JbF` | Web search tool |
| Telegram Bot | `8511502621:AAFn8lkpDxY_8dD_0gto9sb_dzkmUBF4870` | @mphinance bot |
| Telegram User ID | `8024985134` | Michael's Telegram |
| Tradier MCP | `GjMYgAD4ADrGxI78HVhJMjZMWSIU` | HTTP MCP at `https://mcp.tradier.com/mcp` |
| Hooks Token | `2c050c3c24564fac89d8595373b898a852e4e8a12adba4a6` | Internal webhook auth |
| Gateway Token | `25bdbc0bfbb8e554f75e72aa80eb72f8d7edd561498796ee` | Local gateway auth |
| Gateway Port | `18789` | Loopback only |

### MCP Servers (Skills)

| Skill | Transport | Config |
|-------|-----------|--------|
| **Tradier** | HTTP SSE | `https://mcp.tradier.com/mcp` — headers: `API_KEY`, `PAPER_TRADING=false` |
| **trading-signals** | stdio | `npx -y trading-signals-mcp` |
| **yfinance** | stdio | `uvx mcp-yahoo-finance` |
| **brave-search** | built-in | Brave API key above |

### Telegram Channel Config

- DM policy: `allowlist` (only Michael: `8024985134`)
- Group policy: `allowlist`
- Streaming: `partial`

### Hooks (Internal)

- `boot-md` — loads BOOT.md on startup
- `command-logger` — logs all commands
- `session-memory` — persists session context

---

## TastyTrade Service (`services/tastytrade_api.py`)

Full async service wrapping `tastytrade` Python SDK. Key methods:

| Method | Returns |
|--------|---------|
| `login()` | OAuth2 via client_secret + refresh_token |
| `get_accounts()` | List of Account objects |
| `get_positions(account)` | Processed positions with P/L, cost basis, multiplier |
| `get_dashboard_rows(positions)` | Grouped rows (bundles Covered Calls into composite) |
| `get_transactions(account, start_date)` | Transaction history (default YTD) |
| `get_ytd_deposits(account)` | Total deposits for YTD return calc |

**Env vars needed:** `TASTYTRADE_CLIENT_SECRET`, `TASTYTRADE_REFRESH_TOKEN`

**Strategy detection:** Automatically bundles Long Equity + Short Call positions into "Covered Call" composite rows.

---

## Cron Jobs

One active job at time of capture:

- **Podcast Script Reminder** — one-shot at `2026-03-07T14:00Z`, sends Telegram message about podcast script

---

## Workspace Contents (Key Files)

The `workspace/` directory contained the full working tree. Key items to preserve or port:

### Core Documents

- `AGENTS.md`, `IDENTITY.md`, `SOUL.md`, `USER.md` — Agent persona/instructions
- `STANDING_ORDERS.md` — Automated tasks (pre-market briefing, watchlist monitoring, EOD recap)
- `MISSION_BRIEF.md`, `STRATEGY_SPECS.md`, `STRATEGY_TECHNICAL_SPEC.md` — Trading strategy docs
- `STRATEGY_GRAVITY_WELL.md` — Custom strategy write-up
- `GHOST_INSTRUCTIONS.md`, `HEARTBEAT.md`, `MEMORY.md` — Agent memory/continuity system
- `INFRASTRUCTURE.md`, `TOOLS.md` — System architecture docs
- `GOOGLE_SETUP_GUIDE.md`, `PLAYWRIGHT_INSTRUCTIONS.md` — Setup guides

### Scripts & Scanners

- `batch_scanner.py`, `quick_scan.py` — Market scanning
- `alpha_standalone.py`, `cross_reference_engine.py` — Alpha generation
- `insider_alpha.py`, `sentiment_analyzer.py` — Data sources
- `pattern_detector.py`, `risk_metrics.py` — Analytics
- `ema_cross_alert.py`, `intelligent_alerts.py` — Alert systems
- `ghost_pulse.py` — Heartbeat/monitoring
- `generate_hud.py`, `generate_report.py`, `generate_playbook.py` — Report generators
- `generate_options_playbook.py` — Options-specific reports
- `scrape_avantis.py` — ETF scraper
- `streamlit_dashboard.py` — Dashboard UI
- `job_search_alpha.py`, `knowledge_manager.py` — Misc utilities

### Data Files

- `alpha_scan_summary.json`, `alpha_watchlist.json`, `last_scan_results.json`
- `normalized_holdings.csv`, `data.json`, `data.js`

### Templates

- `hud_template.html`, `dashboard_template.html`, `template.html`, `index_template.html`
- `income_tracker.html`, `income_delta.html`, `income_full.html`, `income_weekly.html`
- `options_template.html`, `TER_Alpha.html`

### Subdirectories

- `scanners/`, `scripts/`, `strategies/`, `tools/`, `skills/` — Modular components
- `data/`, `docs/`, `reports/`, `scans/`, `scan_summaries/`, `logs/` — Output directories
- `momentum-hub/`, `momentum-phund-tasty/`, `TickerTrace/` — Sub-projects
- `landing/`, `mphinance/`, `public/`, `templates/`, `drafts/` — Web/content
- `memory/`, `config/`, `backups/`, `_archive/` — State management
- `clawhub/`, `alpha-playbooks/` — Additional modules

---

## Recreation Plan — Venus Gemini Agent

To recreate on Venus using the existing Gemini install:

1. **Core:** Use `google/gemini-3-flash` as primary model (already available)
2. **MCP Servers:** Port Tradier, trading-signals, and yfinance MCPs to the Venus MCP infrastructure
3. **Telegram Bot:** Reuse bot token above OR create new bot for Discord (per Venus consolidation plan)
4. **Standing Orders:** Port `STANDING_ORDERS.md` tasks to Venus cron/scheduler
5. **Scanner Pipeline:** The batch scanner and quick scan scripts are already ported to `mphinance/dossier/`
6. **TastyTrade Service:** Copy `tastytrade_api.py` to Venus if TT integration needed
7. **Identity/Persona:** Port `SOUL.md`, `IDENTITY.md`, `USER.md` to the new agent's system prompt
