# INFRASTRUCTURE — Sam's Map of the World

_How the machines connect. What lives where. Updated 2026-03-05._

---

## Machines

### sam2 (You Live Here)

- **Role**: OpenClaw primary, Telegram bot, your home base
- **User**: `sam`
- **IP**: `192.168.2.94` (local network)
- **SSH alias**: `sam2` (from Michael's machine)
- **Key Paths**:
  - OpenClaw workspace: `/home/sam/.openclaw/workspace/`
  - OpenClaw config: `/home/sam/.openclaw/openclaw.json`
  - mphinance repo: `/home/sam/.openclaw/workspace/mphinance/`
  - TickerTrace local: `/home/sam/.openclaw/workspace/TickerTrace/`
  - Memory: `/home/sam/.openclaw/workspace/memory/`
  - Skills: `/home/sam/.openclaw/workspace/skills/`
  - Logs: `/home/sam/.openclaw/workspace/logs/`
  - Reports: `/home/sam/.openclaw/workspace/reports/`
- **Services**:
  - `systemctl --user status tickertrace` — local TickerTrace on port 3333
  - OpenClaw daemon (self-managed)
- **Cron**: `/home/sam/.openclaw/scripts/` (session cleanup, DB optimization, monitoring)

### venus (Home Server)

- **Role**: Home server, local compute, data storage
- **User**: `mph`
- **IP**: `192.168.2.172` (local network)
- **SSH**: `ssh venus` (from sam2 or Michael's machine)
- **Key Paths**:
  - Legacy scanners: `/home/mnt/Download2/docs/Momentum/`
  - Strategy rules: `/home/mnt/Download2/docs/Momentum/trading.md`
  - Gemini config: `/home/mph/.gemini/`
- **Note**: Can be used for heavier compute tasks. On the same LAN as sam2.

### vultr (The VPS — Public Facing)

- **Role**: Production VPS, Apache, hosts mphinance.com, tt.mphinance.com
- **User**: `root`
- **IP**: `207.148.19.144` (public) — DNS: `mphinance.com`
- **SSH**: `ssh vultr` (port 15422)
- **Key Paths**:
  - Landing page: `/home/mphinance/public_html/` → symlink to `/home/mphinance/mphinance-repo/landing/`
  - Landing git repo: `/home/mphinance/mphinance-repo/` (sparse checkout, auto-pulls every 5 min)
  - Landing sync log: `/home/mphinance/logs/landing_sync.log`
  - Momentum Phund (NiceGUI): `/home/mphinance/tt/` — live at <https://tt.mphinance.com>
  - SSL certs: `/home/mphinance/ssl.*`
  - Apache vhost: `/etc/apache2/sites-enabled/mphinance.com.conf`
- **Services**:
  - Apache (mphinance.com landing, blog, about)
  - NiceGUI app (tt.mphinance.com — Momentum Phund live dashboard)
  - Let's Encrypt SSL
- **Auto-deploy**: Landing page auto-syncs from GitHub every 5 min via cron `git pull`
- **⚠️**: Do NOT restart Apache, modify vhosts, or touch SSL without asking

### Michael's Dev Machine (Antigravity)

- **Role**: Primary development workspace — where code gets written
- **Note**: Not directly accessible from sam2. Changes flow via git.

---

## Data Flow

```
  GitHub Actions (6 AM CST)
       │
       ▼
  GitHub repo (mphinance/mphinance)
       │
       ├──── git pull (every 5 min) ──→ Vultr /home/mphinance/mphinance-repo/
       │                                  └── symlink → public_html (landing page)
       │
       └──── git pull ──→ sam2 /home/sam/.openclaw/workspace/mphinance/
```

## Key URLs

| Service | URL | Hosted On |
|---------|-----|-----------|
| Landing Page | <https://mphinance.com> | Vultr |
| Ghost Blog | <https://mphinance.com/blog/> | Vultr |
| Momentum Phund | <https://tt.mphinance.com> | Vultr |
| Alpha Dossier | <https://mphinance.github.io/mphinance/> | GitHub Pages |
| TraderDaddy Pro | <https://www.traderdaddy.pro/register?ref=8DUEMWAJ> | Whop |
| TickerTrace Pro | <https://www.tickertrace.pro> | Vultr |
| AMU | <https://mphinance.github.io/AMU/> | GitHub Pages |
| TickerTrace Local | <http://localhost:3333> | sam2 (no auth) |

## Deploy Commands

```bash
# Landing page — auto-deploys via git push (no rsync needed!)
cd /home/sam/.openclaw/workspace/mphinance && git add landing/ && git commit && git push
# Vultr picks up changes within 5 minutes automatically

# Manual force-sync (if cron missed it)
ssh vultr "sudo -u mphinance bash -c 'cd /home/mphinance/mphinance-repo && git pull'"

# Deploy alpha reports → use deploy_alpha_reports skill

# Push dossier/blog changes
cd /home/sam/.openclaw/workspace/mphinance && git add -A && git commit && git push
```

## Communication Channels

| Channel | Purpose | How |
|---------|---------|-----|
| Telegram | Primary comms with Michael | Built-in OpenClaw |
| GitHub | Issues, PRs, pipeline status | `gh` CLI + github skill |
| Email | Monitoring only (himalaya) | `himalaya list -a main` |
| Twitter/X | Marketing (@mphinance) | twitter skill (OAuth 1.0a) |
