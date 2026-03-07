# Security Audit & Cleanup Plan — alpha-momentum → mphinance Monorepo

## TL;DR: How Dangerous Is This?

### Threat Rating: 🔴 7/10 — Seriously Dangerous If Released As-Is

If someone cloned this repo as it sits right now and asked an AI agent "what can I do with this codebase?", here's what they'd get:

| What They'd Find | Damage Potential |
|---|---|
| **Tastytrade OAuth refresh token** (`.env`, `clean_env.py`) | 🔴 Could read your brokerage positions, balances, orders |
| **Tradier API key** (`.env`, `gemini_settings.json`) | 🔴 Could pull your positions, make quotes, potentially trade |
| **SMTP password** for `contact@mphinance.com` | 🟠 Could send email as you |
| **5 Discord webhook URLs** | 🟠 Could post messages to your channels |
| **Google Sheets/Apps Script URLs** | 🟡 Could trigger your automation scripts |
| **Gemini API key** | 🟡 Could burn your API credits |
| **Venus internal IP** (`192.168.2.172`) + SSH paths | 🟡 Network topology leak (LAN-only risk) |
| **VaultGuard API key** (in mphinance repo's `GHOST_HANDOFF.md`) | 🔴 Master key to everything |
| **Entire trading strategy logic** (VoPR, scanners, alpha engine) | 💰 Your IP, your edge |
| **Infrastructure layout** (Docker, MCP agents, data flow) | 📐 Full blueprint of your system |

> [!CAUTION]
> The brokerage credentials are the biggest risk. Even "read-only" OAuth tokens for Tastytrade reveal positions, account value, and open orders — valuable intel for a motivated attacker.

### But After Cleanup? 3/10 — Manageable

With secrets removed and obfuscation applied, someone gets:
- A well-architected trading platform skeleton
- Scanner strategies (your IP, but not your data/keys)
- No ability to connect to anything without VaultGuard access

---

## Disk Cleanup: 2.05 GB of Deletable Bloat

| Path | Size | Action |
|------|------|--------|
| `alpha-reflex/venv/` | 566 MB | **Delete** |
| `venv_api/` | 510 MB | **Delete** |
| `tasty-agent/.venv/` | 360 MB | **Delete** |
| `venv_openbb/` | 308 MB | **Delete** |
| `alpha-reflex/.web/` | 200 MB | **Delete** (Reflex auto-regenerates) |
| `_archive/` | 85 MB | **Compress → stash 90 days** |
| `trading-mcp/node_modules/` | 57 MB | **Delete** (`npm install` restores) |
| `tradier-agent/.venv/` | 44 MB | **Delete** |
| `venv_api310/` | 16 MB | **Delete** |
| `node_modules/` (root) | 3.8 MB | **Delete** |
| `.ruff_cache/` | 12 KB | **Delete** |
| **Total reclaimable** | **~2.05 GB** | **Directory drops to ~150 MB** |

---

## Secret Exposure Inventory — Files That Must NEVER Be Committed

### 🔴 Critical — Delete or Gitignore Before Any Commit

| File | Contains |
|------|----------|
| `.env` | ALL keys: Gemini, Tastytrade OAuth, Tradier, Discord webhooks, SMTP password, Google Drive paths |
| `clean_env.py` | Full copy of `.env` values **hardcoded as strings** in a Python file |
| `trading-mcp/gemini_settings.json` | Hardcoded Tradier API key in JSON |
| `trading-mcp/.env` | Likely additional keys |

### 🟠 Hardcoded Infrastructure — Must Refactor

| File(s) | Issue |
|---------|-------|
| `core/data_engine.py` (lines 160, 175, 191, 193) | Hardcoded `ssh venus` commands with full paths |
| `alpha-reflex/core/data_engine.py` (lines 213, 228, 246) | Same — duplicate of above |
| `alpha-reflex/rxconfig.py` (line 6) | Hardcoded `192.168.2.172` |
| `alpha-reflex/alpha_reflex/components/copilot.py` (lines 31-33) | Hardcoded `192.168.2.172` for MCP endpoints |
| `api/main.py` (lines 367-369) | Hardcoded `192.168.2.172` for MCP endpoints |

---

## The Obfuscation Strategy

You asked about making this "not fully reproducible yet." Here's the approach:

### What We Commit (Public-Safe)
- All scanner/strategy code (VoPR, alpha engine, etc.)
- Frontend UI code
- API framework and route definitions
- MCP agent structure and tool definitions
- Docker/compose configurations (generic)
- Documentation and architecture diagrams

### What We Withhold/Obfuscate
1. **All secrets → VaultGuard** — Code uses `os.getenv()` everywhere, `.env.example` has placeholder values only
2. **Venus-specific paths → Config variables** — Replace all `ssh venus` and `192.168.2.172` with configurable env vars
3. **`clean_env.py` → DELETE** — This file is just a copy of `.env` in Python. It serves no purpose and is a massive leak
4. **`gemini_settings.json` → `.gitignore`** — Or template it with `YOUR_KEY_HERE`
5. **Scanner calibration data** — If you have tuning params that represent your edge, we can move those to a separate config file that's gitignored

### The Result
Someone cloning the repo gets a **fully functional framework** that does nothing without:
- VaultGuard (or their own `.env` with brokerage access)
- A running Venus server (or their own infra)
- Their own Tastytrade/Tradier accounts

---

## Phase 1: Cleanup Script

Here's what the cleanup will do:

```bash
# 1. Compress and stash archive
tar -czf /tmp/alpha-momentum-archive-$(date +%Y%m%d).tar.gz _archive/
# → Keep the tarball for 90 days, delete the directory

# 2. Delete all virtual environments
rm -rf venv_api/ venv_api310/ venv_openbb/
rm -rf alpha-reflex/venv/ alpha-reflex/.web/
rm -rf tasty-agent/.venv/ tradier-agent/.venv/
rm -rf node_modules/ trading-mcp/node_modules/
rm -rf .ruff_cache/ trading-mcp/dist/

# 3. Delete/sanitize secret-containing files
rm clean_env.py                    # Pure secret leak
rm trading-mcp/gemini_settings.json # Hardcoded Tradier key

# 4. Create .env.example from .env (scrubbed)
# 5. Move .env to ~/.env-alpha-momentum (keep on machine, not in repo)
```

## Phase 2: Refactor Hardcoded Infrastructure

Replace all `192.168.2.172` and `ssh venus` references with environment variables:
- `VENUS_HOST` — defaults to `venus` (SSH alias) or `192.168.2.172`
- `MCP_TRADING_URL` — defaults to `http://${VENUS_HOST}:5057/sse`
- `MCP_TASTY_URL` — defaults to `http://${VENUS_HOST}:5058/sse`
- `MCP_TRADIER_URL` — defaults to `http://${VENUS_HOST}:5059/sse`
- `SCAN_DATA_PATH` — replaces hardcoded `/home/mnt/Download2/docs/Momentum/anti/scheduling/scans/`

## Phase 3: Git Init + Merge into mphinance

1. Init git in cleaned directory
2. Create comprehensive `.gitignore`
3. Write `CODEBASE_INDEX.md` and module READMEs
4. Create feature branch on `mphinance/mphinance`
5. Copy files into proposed directory structure
6. Update `GHOST_HANDOFF.md`
7. Test Docker builds
8. Push

---

## On the Desktop Brokerage Vision

> *"I think I can create pretty much an entire desktop brokerage trading suite right?"*

Yes. You already have the core pieces:
- **Market data** (Tradier API, scanners)
- **Brokerage connections** (Tastytrade SDK, Tradier API)
- **AI analysis** (MCP agents, Gemini integration, VoPR engine)
- **Frontend** (running on :8100)
- **Infrastructure** (Docker, VaultGuard, GitHub Actions)

What's missing to make it a "suite":
- Order execution (currently read-only)
- Position management UI (partial)
- Risk/P&L dashboards
- Real-time streaming quotes
- Multi-account support

But that's all additive — the architecture supports it. The Reflex app was probably heading there before the vanilla frontend took over.

---

## On Your Random Thought

> *"why aren't there something that can understand if I were to talk without talking"*

That's called **subvocal speech recognition** and it does exist — [AlterEgo from MIT Media Lab](https://www.media.mit.edu/projects/alterego/) used jaw/facial muscle EMG sensors to detect "silent speech" with ~92% accuracy. Google's been researching it too. Bone conduction + EMG + ML is the approach. It's not consumer-ready yet but it's real research, not sci-fi. With modern transformer models trained on your specific jaw/muscle patterns, personal calibration would probably get accuracy much higher.

---

## The "Susquehanna" Question: How Proprietary is VoPR?

> *"how Susquehannah are we getting? Lol."*

**The harsh truth:** What you have built is incredibly impressive for a retail trader/developer, but Susquehanna International Group (SIG) or Jane Street operates in a completely different dimension. 

- **Your Edge:** You are calculating historical/realized volatility using math (Garman-Klass, Parkinson, Hodges-Tompkins) to find mid-term mispricings in the options chain (VRP). You are using 1-minute to daily timeframe data.
- **Their Edge:** They are using FPGAs (custom hardware) located *inside* the exchange racks to calculate implied volatility surfaces across thousands of strikes in nanoseconds. They trade on order book imbalances, latency arbitrage, and complex statistical models using petabytes of tick-by-tick data.

**Is your algorithm proprietary? Yes.**
It embodies a specific mechanical trading strategy that works for *you*. Revealing your exact Volatility Risk Premium thresholds, ATR compression filters, and strike-selection criteria gives away the rules of your system. 
But it's not "institutional HF quant" IP. It's a highly refined retail/swing strategy. The danger of releasing it isn't that Citadel will steal it; the danger is that thousand of retail traders will clone it, over-capitalize the strategy, and squeeze the edge out of the specific setups you target.

---

## The Desktop Migration: Building a Native Desktop Suite

> *"what if we brought part of that API inside this container so I can travel? ... There's not any real advantage to using [Tauri] if we're not really using rust underneath is there? We may as well use electron right?"*

**You are 100% correct.** If we are bundling a Python sub-process to do the heavy lifting (VoPR, pandas, API routing) and sticking to an HTML/JS frontend, the primary advantage of Tauri (the tiny Rust binary size) is mostly lost. 

**Electron is the right tool for this job.**
- **Maturity & Ecosystem:** It's exactly what Discord, VS Code, and Slack use. It has bulletproof support for bundling background Python processes (using tools like `pyinstaller` and `electron-builder`).
- **Ease of Dev:** The UI is just chromium. You already know exactly how your JS will render. No weird Webkit vs WebView2 quirks.

### The Electron Migration Plan

1. We wrap your current `frontend/` (HTML/JS/CSS) in an Electron shell.
2. We configure Electron's `main.js` to spawn `api/main.py` as a background child process when the app opens, and kill it when the app closes.
3. Your UI talks to `localhost:8100` just like it does today, but it feels like a native desktop app.

---

## The Low Hanging Fruit: WebSockets for Blistering Speed

> *"MCP vs API - is there any real difference for YOU? If not then start communicated via those websockets! Get the speed where we can the easiest - lowest hanging fruit first."*

**For me (the LLM Copilot):** MCP via SSE is perfect. It's event-driven and instant for tools.
**For the Live Trading HUD:** Polling REST APIs (`/markets/quotes`) every second is slow and burns rate limits. We need **WebSockets**.

### The WebSockets Upgrade Plan

Tradier offers a streaming WebSocket API for level 1 market data (ticks, quotes, greeks). We need to upgrade the Python `DataEngine` to establish a persistent WebSocket connection to Tradier, and then stream that data to the frontend UI via FastAPI WebSockets or SSE.

**This is the single biggest bottleneck we can fix today.** It upgrades the dashboard from "refreshing every 3 seconds" to "flashing prices instantly as trades occur."

---

## User Review Needed

> [!IMPORTANT]
> **Direction Check:** Our new plan is to prioritize **WebSockets integration in the Python API** for instant market data streaming (the lowest hanging fruit), and then use **Electron** to package the frontend and Python API into a desktop app. Do you want to start building the Tradier WebSocket connection into `api/main.py` right now?
