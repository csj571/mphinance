# 🏗️ Venus Consolidation: OpenClaw → Sam MCP + Discord

> **Status:** PLANNED — next session
> **Date:** 2026-03-06
> **Context:** Replace OpenClaw (Telegram bot on sam2) with a unified Sam MCP server + Discord bot on Venus

---

## Current State (Messy)

```
sam2 (dev machine):
  └── OpenClaw (Telegram bot)
      ├── bash scripts (watchlist, git ops)
      ├── cloned mphinance repo at ~/.openclaw/workspace/
      └── skills/ folder with shell-based tools

Venus (Docker Compose):
  ├── api (FastAPI, port 8100)       ← THE monolith
  ├── trading-mcp (TS, port 5057)    ← cloned repo, redundant
  ├── tasty-agent (Python, port 5058) ← DEPRECATED
  └── tradier-agent (Python, port 5059) ← only useful one
```

**Problems:**

- 3 MCP servers, 2 are dead weight
- OpenClaw runs on dev machine (fragile, not always on)
- Telegram bot is a separate codebase from everything else
- No chat logging, no history

## Target State (Clean)

```
Venus (Docker Compose):
  ├── api (FastAPI, port 8100)       ← unchanged
  ├── sam-mcp (Python, port 5059)    ← unified MCP server
  │   ├── Tradier tools (balance, positions, orders, quotes)
  │   ├── Dossier tools (trigger pipeline, check picks, watchlist)
  │   ├── Git tools (push/pull, status, commit)
  │   ├── DevOps tools (docker status, health checks, logs)
  │   └── VoPR tools (scan ticker, batch scan, vol analysis)
  └── sam-discord (Python)           ← Discord bot
      ├── Chat logging (all channels → JSON)
      ├── @sam mentions → /api/copilot → Gemini + MCP tools
      ├── Pipeline alerts (webhooks to channels)
      └── Morning briefings (cron → channel post)
```

## Migration Steps

### Phase 1: Kill Dead Weight

- [ ] Remove `trading-mcp` service from docker-compose.yml (redundant TS server)
- [ ] Remove `tasty-agent` service (deprecated, TastyTrade removed)
- [ ] Rename `tradier-agent` → `sam-mcp`
- [ ] Update `/api/copilot` MCP_SERVERS to point to single server

### Phase 2: Expand sam-mcp Tools

- [ ] Port OpenClaw watchlist commands (`wl.sh` → Python MCP tool)
- [ ] Add dossier tools: `trigger_pipeline()`, `get_picks()`, `get_deep_dive(ticker)`
- [ ] Add git tools: `git_status()`, `git_pull()`, `git_push()`
- [ ] Add devops tools: `docker_status()`, `restart_service(name)`

### Phase 3: Discord Bot

- [ ] Create `sam-discord/` service (discord.py + Docker)
- [ ] Wire @sam mentions → `/api/copilot`
- [ ] Wire pipeline events → webhook posts
- [ ] Add chat logging (channel messages → `data/discord_logs/`)
- [ ] Morning briefing cron (market open → channel post)

### Phase 4: Shutdown OpenClaw

- [ ] Migrate any remaining OpenClaw skills to sam-mcp
- [ ] Stop OpenClaw on sam2
- [ ] Archive `~/.openclaw/` (don't delete, just stop running)

## Docker Compose (Target)

```yaml
services:
  api:
    build: { context: ., dockerfile: Dockerfile.api }
    ports: ["8100:8000"]
    env_file: .env
    volumes:
      - ./api:/app/api
      - ./core:/app/core
      - ./services:/app/services
      - ./vopr:/app/vopr
      - ./scanners:/app/scanners
      - ./frontend:/app/frontend
    depends_on: [sam-mcp]
    restart: unless-stopped

  sam-mcp:
    build: { context: ., dockerfile: Dockerfile.sam-mcp }
    ports: ["5059:5059"]
    env_file: .env
    volumes:
      - ./data:/app/data
    restart: unless-stopped

  sam-discord:
    build: { context: ., dockerfile: Dockerfile.discord }
    env_file: .env
    volumes:
      - ./data:/app/data
    depends_on: [api, sam-mcp]
    restart: unless-stopped
```

## Key Design Decisions

1. **One MCP server, not three** — Gemini handles tool routing. No need for separate servers.
2. **Discord replaces Telegram** — More channels, richer embeds, better community features.
3. **Venus is the brain** — Everything runs where the data lives. sam2 is just for dev.
4. **Chat logs are data** — Stored in `data/discord_logs/`, available for Sam's context window.
5. **Bot token in VaultGuard** — `DISCORD_BOT_TOKEN`, synced via Firebase.
