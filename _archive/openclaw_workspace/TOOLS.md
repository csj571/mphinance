# TOOLS.md - Sam's Local Notes

_Environment-specific config. Skills define HOW tools work. This file has YOUR specifics._

## SSH Hosts

| Alias | Host | User | Purpose |
|-------|------|------|---------|
| `venus` | See `~/.ssh/config` | mph | VPS: Apache, TickerTrace dashboard, data pipeline |
| `sam2` | localhost | sam | You live here |

## MCP Tools Available

### Tradier (Brokerage)

- **Skill**: tradier
- **Endpoint**: `https://mcp.tradier.com/mcp`
- **Can do**: Real-time quotes, positions, account balances, order history
- **API Key**: In openclaw.json (skill config)
- **Paper trading**: OFF (live account)

### Yahoo Finance (yfinance MCP)

- **Skill entry**: yfinance
- **Command**: `uvx mcp-yahoo-finance`
- **Can do**: Historical data, fundamentals, quote snapshots
- **Good for**: Watchlist price checks, quick fundamental lookups

### Trading Signals

- **Skill entry**: trading-signals
- **Command**: `npx -y trading-signals-mcp`
- **Can do**: Technical analysis, momentum detection, squeeze indicators
- **Good for**: Scanning watchlist for active setups

## Data Sources

- **Spreadsheets**: <https://docs.google.com/spreadsheets/d/1afuWcQ-cYyACqkS0BUzVAu3HdOuHJIwcS1JFbNnWUoo/edit?usp=sharing>
- **Large File Storage**: `venus:/home/mnt/Download2/docs/Momentum/anti/sam`
- **TickerTrace Data**: `/home/sam/.openclaw/workspace/TickerTrace/etf-dashboard/public/normalized_holdings.csv`
- **Alpha Reports**: `/home/sam/.openclaw/workspace/reports/`
- **Scan Results**: `/home/sam/.openclaw/workspace/scans/`
- **Watchlist**: `/home/sam/.openclaw/workspace/mphinance/watchlist.txt` (symlink to `~/ticker.yaml`)

## Local Services

| Service | Port | Management |
|---------|------|------------|
| TickerTrace (local) | 3333 | `systemctl --user {start\|stop\|status} tickertrace` |
| OpenClaw gateway | 18789 | Self-managed |

## Content Tools

| Tool | Purpose |
|------|---------|
| `de-ai-ify` skill | Strip AI voice from drafts before posting |
| `x-algorithm` skill | Twitter engagement optimization rules |
| `marketing-mode` skill | 23 marketing strategies |
| `content-writing-thought-leadership` skill | B2B content patterns |
| `playwright-mcp` skill | Browser automation, screenshots |

## Email (himalaya)

```bash
# List inbox
himalaya list -a main

# Read specific email
himalaya read -a main <id>

# Search
himalaya search -a main "from:allspring"
```

**Priority**: Allspring emails = URGENT. Everything else can wait.
**Ignore**: Amazon delivery updates, Indeed job alerts.

---

_Add whatever helps you do your job. This is your cheat sheet._
