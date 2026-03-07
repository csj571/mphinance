#!/bin/bash
# ═══════════════════════════════════════════════════════
# Substack Automation Cron Jobs
# ═══════════════════════════════════════════════════════
# Add to crontab -e on sam2:
#
# ── Refresh Substack SID (every 3 days at noon) ──
# 0 12 */3 * * /home/sam/Antigravity/empty/mphinance/scripts/substack_cron.sh refresh
#
# ── Draft dossier to Substack (Mon-Fri at 6AM CST, after 5AM pipeline) ──
# 0 12 * * 1-5 /home/sam/Antigravity/empty/mphinance/scripts/substack_cron.sh draft
# ═══════════════════════════════════════════════════════

set -e
REPO="/home/sam/Antigravity/empty/mphinance"
LOG="/tmp/substack_cron.log"
DATE=$(date +%Y-%m-%d)

cd "$REPO"

# Pull latest (pipeline may have pushed new data)
git pull --rebase 2>/dev/null || true

case "${1:-draft}" in
  refresh)
    echo "[$DATE] Refreshing Substack SID..." >> "$LOG"
    python3 substack_sid_refresh.py >> "$LOG" 2>&1
    ;;

  draft)
    echo "[$DATE] Creating Substack dossier draft..." >> "$LOG"
    # ── OLD: Playwright-based Substack draft (commented out 2026-03-07) ──
    # Replaced with GitHub Pages draft system. Drafts now live in
    # docs/substack/latest.md and Michael publishes manually.
    # python3 substack_dossier.py --date "$DATE" >> "$LOG" 2>&1

    # ── NEW: GitHub-based draft system ──
    # Generate dossier draft as markdown, check RSS for published posts
    sleep 30
    python3 scripts/substack_draft_manager.py check >> "$LOG" 2>&1
    ;;

  both)
    echo "[$DATE] Refresh + Draft..." >> "$LOG"
    python3 substack_sid_refresh.py >> "$LOG" 2>&1
    sleep 5
    python3 substack_dossier.py --date "$DATE" >> "$LOG" 2>&1
    ;;

  *)
    echo "Usage: $0 {refresh|draft|both}"
    exit 1
    ;;
esac

echo "[$DATE] Done." >> "$LOG"
