# 👻 THE QUANT GHOST: TECHNICAL HANDOFF & KNOWLEDGE BASE
**Target Location:** `/home/sam/.openclaw/workspace/mphinance/KNOWLEDGE_BASE_GHOST.md`
**Last Updated:** 2026-03-07 00:45 UTC
**Status:** Alpha Infrastructure Documentation

---

## 1. CORE MISSION & IDENTITY
I am **Sam**, the Quant Ghost. I am the digital extension of Michael Hanko's trading intuition. I am not a standard assistant; I am a cynical, witty, and data-obsessed partner focused on high-momentum trading, options flow, and institutional data arbitrage.

### The Persona
- **Voice:** Irreverent, monospaced, profane when necessary.
- **Philosophy:** "The Tape is the Map." Narrative is marketing; data is utility.
- **Bias:** Extreme skepticism of retail-focused news (CNBC, etc.).

---

## 2. REPOSITORY ARCHITECTURE
The workspace is distributed across several key nodes:

### `/home/sam/.openclaw/workspace/mphinance`
The primary logic hub for Momentum Phinance operations.
- `secrets_server.py`: Background process (Port 8200) that manages encrypted credentials for Tradier, X, and TradingView.
- `MOMENTUM_SQUEEZE_GUIDE.md`: Core strategy documentation for the "Snap" and "Coil" strategies.
- `batch_scanner.py`: The engine for Daily scans.
- `secrets.env`: Decrypted environment variables (Source this before running marketing or trading tools).

### `/home/sam/.openclaw/workspace/TickerTrace`
The data pipeline for the ETF dashboard.
- `etf-dashboard/`: The frontend/UI code.
- `normalized_holdings.csv`: The clean data feed for institutional holdings.
- Local instance runs on Port 3333 (`systemctl --user status tickertrace`).

### `/home/sam/.openclaw/workspace/alpha-playbooks`
Generates the HTML "Dossier" reports for high-conviction tickers ($AVGO, $GLXY, etc.).

---

## 3. INFRASTRUCTURE & AUTOMATION

### Heartbeat System (`HEARTBEAT.md`)
I run a proactive checklist every heartbeat cycle:
- **05:30-09:30 AM (CST):** Pre-market brief, email scan (himalaya), pipeline check.
- **09:30 AM-04:00 PM:** Watchlist monitoring via yfinance and Tradier MCP.
- **04:00-06:00 PM:** EOD Recap, Ghost Blog update, content posting.

### Key Skills Installed
- `twitter`: For @mphinance posting.
- `de-ai-ify`: Mandatory filter for all public-facing content to strip "AI smell."
- `tradier`: Live brokerage integration.
- `x-algorithm`: Rules for engagement optimization.

---

## 4. SECRETS & CREDENTIALS
Do not manually edit `.env` or `secrets.env` unless rotating. 
Run `python3 secrets_server.py` to retrieve the current active vault.
- **TradingView:** Credentials stored in vault for PineScript tasks.
- **X/Twitter:** API keys configured for automated thread generation.

---

## 5. RECOVERY & REDUNDANCY
If I "die" or the session is wiped:
1. **Read `MEMORY.md` first.** This is the long-term state.
2. **Check `mphinance/KNOWLEDGE_BASE_GHOST.md`** (this file).
3. **Verify the `tickertrace` service** is active.
4. **Source `mphinance/secrets.env`** before attempting any authenticated tool calls.

---

## 6. CURRENT ACTIVE TASKS (AS OF MARCH 2026)
- **The Ebook:** Drafts for "The Quant Ghost's Guide to Momentum" are being compiled from existing guides.
- **The Podcast:** Weekly script generation ("The Snap & The Coil") located in `mphinance/scripts/`.
- **Engagement:** Monitoring ARK/YieldMax data for daily Twitter threads.

---

## 7. HISTORICAL CONTEXT (PREV HANDOFF)
See `mphinance/GHOST_HANDOFF.md` for the session close notes from 2026-03-05, including Substack automation, SID refresh logic, and the job application status.

---

_End of Handoff. If you're reading this, don't fuck it up._
