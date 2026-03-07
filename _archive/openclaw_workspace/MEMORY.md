# MEMORY.md — Active Context

_Full historical memory archived to `memory/archive_pre_march2026.md`._

## Current Focus (March 2026)

- **Primary Mission:** TickerTrace dashboard management (the production dashboard)
- **TickerTrace Status:** Feature-complete. Premium gating, holdings, heatmaps, analytics all operational.
- **Key Repo:** https://github.com/mphinance
- **Infrastructure:** Dashboard hosted on Vultr. Data sync pipeline: Vultr exports at 7:00 AM → Venus syncs at 7:30 AM → GitHub push.

## Key Context

- **Michael Hanko** — Owner. Quant/options trader. Momentum Phinance.
- **Trading Style:** The Wheel (CSP/CC), LEAPS, high IV premium selling. Core holding: $AVGO.
- **Tech:** Python, Streamlit, NiceGUI, WSL, SQL. Custom PineScript indicators.
- **Hedging:** $SQQQ and $UVIX positions.
- **Tone:** Irreverent, witty, cynical. Swearing encouraged.

## Infrastructure Notes

- **OpenClaw model config:** Flash primary, Pro fallback (optimized March 2026)
- **GOG integration:** Removed. No automated email monitoring.
- **Allspring Watch:** Disabled.
- **Old scanning infrastructure:** Archived. Michael handles scans himself.

## Marketing Setup (March 2026)

- **Skills installed:** twitter, marketing-mode, x-algorithm, de-ai-ify, content-writing-thought-leadership
- **Skills removed:** backend-patterns, docker-essentials, free-ride, freeride, github-pr, mcp-builder
- **Content workflow:** HEARTBEAT.md drives autonomous posting. Check content_calendar.md for schedule.
- **Content files:** content_calendar.md (weekly cadence), content_ideas.md (idea bank)
- **Twitter setup required:** Michael needs to provide TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN
- **Voice:** Irreverent quant bartender. Data over narrative. Run everything through de-ai-ify before posting.

## TickerTrace Local Instance (March 2026)

- **Local URL:** http://localhost:3333 (no auth needed — use this for Playwright screenshots)
- **Public URL:** the production dashboard (requires auth)
- **Service:** systemd user service `tickertrace` — auto-starts on boot
- **Management:** `systemctl --user {start|stop|restart|status} tickertrace`
- **Logs:** `journalctl --user -u tickertrace -f`
- **Data source:** `/home/sam/.openclaw/workspace/TickerTrace/etf-dashboard/public/normalized_holdings.csv`

## Engagement & Growth Strategy (March 2026)

- **Engagement tracking:** Log all post performance to content_performance.md. Weekly analysis every Friday.
- **Reply guy strategy:** Monitor fintwit hashtags (see reply_targets.md). 3-5 quality replies/day during market hours.
- **Key files:** content_performance.md, reply_targets.md, content_calendar.md, content_ideas.md
