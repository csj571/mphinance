# 🤖 Discord Sam Bot — Integration Ideas

> **Bot:** sam (App ID: `1331012947262308465`)
> **Token:** In VaultGuard as `DISCORD_BOT_TOKEN`
> **Status:** Bot created, not yet coded
> **Date:** 2026-03-06

---

## Existing Discord Infrastructure

Already in VaultGuard:

- `WEBHOOK_ALISON` — Alison's channel
- `WEBHOOK_PATHFINDERS` — Pathfinders channel
- `WEBHOOK_THE_KINGDOM` — The Kingdom channel
- `WEBHOOK_WEATHER_CHANNEL` — Weather Channel

These are **outbound-only** (push messages TO Discord). The **bot** can do both — read AND write.

---

## 💡 Ideas (Ranked by Effort)

### 1. Chat Logger + Daily Digest (LOW effort)

**What:** Bot sits in trading channels, logs all messages to JSON. At end of day, Sam summarizes the conversation highlights.

**How:**

```python
# discord.py bot → logs messages to data/discord_logs/{channel}/{date}.json
# Nightly cron → feeds logs to Gemini → Sam writes a digest
```

**Value:** Never lose a trade idea, setup, or conversation. Searchable archive.

---

### 2. Pipeline Alerts (LOW effort — webhooks already exist)

**What:** Sam posts to Discord when things happen:

- 🌅 Morning dossier published (6AM) — top 3 picks + link
- 🚨 Signal engine fires BUY/SELL (SSE → webhook)
- 💰 Auto-trade executes (real or dry run)
- ⚠️ Pipeline failures or API errors

**How:** Just add `requests.post(WEBHOOK_URL, json={...})` calls to existing code. No bot needed — webhooks suffice.

---

### 3. Sam Chat Bot — Ask Questions (MEDIUM effort)

**What:** Tag @sam in Discord, she responds in character using Gemini + MCP tools.

**Example:**
> **Michael:** @sam what's my portfolio looking like?
> **Sam:** Your Tradier is showing $127 buying power, 2 positions open (NVDA +3.2%, PLTR -1.1%). Grade A pick today is AMD but honestly with your L2 options not enabled yet, maybe just... read the error message? 😏

**How:**

```python
@bot.event
async def on_message(message):
    if bot.user.mentioned_in(message):
        # Call /api/copilot with the user's question
        # Gemini + MCP tools = live data answers
        # Respond in Sam's voice
```

**Stack:** `discord.py` bot → calls alpha-momentum `/api/copilot` → Gemini with MCP tools → responds in channel.

---

### 4. Trade Journaling via Discord (MEDIUM effort)

**What:** Post trade updates in a channel, Sam tracks them.

**Example:**
> **Michael:** Bought NVDA 10 shares at $24.50
> **Sam:** 📝 Logged: BUY NVDA × 10 @ $24.50 ($245). Your avg cost basis is now $23.80. P/L: +2.9%

**How:** Bot parses natural language trade commands, logs to `data/trade_log.json`, syncs with Tradier positions for verification.

---

### 5. Morning Briefing Channel (MEDIUM effort)

**What:** Every morning at market open, Sam posts a full briefing:

- Market pulse (indices, VIX, BTC)
- Top 3 momentum picks with grades
- VoPR scan results (if options enabled)
- Any signals from overnight
- Sam's sarcastic commentary

**How:** Cron job pulls from dossier pipeline output + alpha-momentum API, formats as Discord embed, posts via webhook.

---

### 6. Multi-User Trade Room (HIGH effort)

**What:** Sam moderates a live trading room. Tracks everyone's calls, scores them, maintains leaderboards.

**Features:**

- `!call NVDA long 24.50` → logs the call
- `!close NVDA 26.00` → calculates P/L, updates leaderboard
- `!leaderboard` → ranked by win rate, avg return
- Sam roasts bad calls, celebrates good ones

**Value:** Community building. Content for Substack. Social proof for TraderDaddy.

---

### 7. DoubleDownToWin Security Alerts (HIGH effort)

**What:** Bot monitors for security events and posts alerts:

- API key rotation reminders
- Failed auth attempts on the API
- Unusual trade patterns (size, frequency)
- VaultGuard changes

---

## Recommended Starting Point

**Do #2 first** (pipeline alerts via webhooks) — takes 30 minutes, immediate value.
Then **#1** (chat logger) — gives you a searchable archive.
Then **#3** (Sam chat bot) — the crowd-pleaser.

## Tech Stack

```
discord.py         # Bot framework
Gemini API         # Sam's brain (via /api/copilot)
VaultGuard         # Token storage
Docker on Venus    # Runs alongside alpha-momentum
```

**Bot invite URL** (you'll need to generate this):

```
https://discord.com/oauth2/authorize?client_id=1331012947262308465&permissions=274877975552&scope=bot
```

Permissions: Read Messages, Send Messages, Read Message History, Embed Links, Attach Files.
