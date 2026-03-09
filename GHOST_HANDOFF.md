# 👻 GHOST_HANDOFF.md — Session 2026-03-09 (Full System Audit)

## ⚠️ RESUME PRIORITY

1. **Deploy landing to Vultr** — `rsync -avz landing/ vultr:/home/mphinance/public_html/` (chart images + ebook link fixed)
2. **Fix Daily Dossier pipeline failures** — 2 of last 3 GH Actions runs failed. Check logs.
3. **Wire Discord bot** — `scripts/sam_discord.py` exists but isn't running. Needs bot token + cron.
4. **Wire dossier → Substack drafts** — Draft system exists but only has Musings, not daily reports.

---

## What Happened This Session

### 1. Timezone Fix (EST → CST) ✅
- `dossier/report/builder.py` — `ZoneInfo("America/New_York")` → `ZoneInfo("America/Chicago")` + label `CST`
- `dossier/pages/ticker_page.py` — same
- `dossier/watchlist_dive.py` — same

### 2. Blog & Landing Page Link Audit ✅
- **Chart images** — `../ticker/` → absolute GH Pages URL (won't resolve from Vultr otherwise)
- **VaultGuard link** — pointed to non-existent VAULT.md → fixed to `vaultguard/README.md`
- **Ebook checkout** — `/api/ebook/checkout` 404 → redirected to Substack for now
- **All other links verified working**: TraderDaddy ✅, TickerTrace ✅, Dossier ✅, Substack ✅, GitHub ✅, tt.mphinance.com ✅

### 3. Removed tightspread/ ✅
- Entire `tightspread/` directory deleted (lives separately as alpha-momentum)
- Updated 3 references in `docs/LIVING_EBOOK_PIPELINE.md` and `docs/MONEY_PLAN.md`
- Removed from `.gitignore`

### 4. Cleaned .gitignore ✅
- Removed `tightspread` line
- Removed `VAULT.md` line (file never existed)
- Added comment about vaultguard/ being intentionally tracked

### 5. Created .agents/workflows/ ✅
Six workflow files agents now auto-read:
- `deploy-landing.md` — rsync to Vultr
- `deploy-dossier.md` — full pipeline + GH Pages push
- `add-ticker.md` — add stock to watchlist + deep dive
- `blog-entry.md` — write Sam blog entry + commit
- `health-check.md` — verify all endpoints
- `full-audit.md` — comprehensive system check

### 6. GHOST.CONTROL Dashboard ✅
- `docs/dashboard.html` — overhauled from issue tracker to full system dashboard
- Live endpoint health checks (12 endpoints)
- Pipeline status cards
- Product link grid
- Documentation index (all 37 MD files, categorized)
- Mermaid architecture diagram

## What's Still Broken / Needs Work
- ❌ Discord bot — scripts exist, not running
- ⚠️ Daily Dossier pipeline — intermittent failures
- ⚠️ Ebook checkout — no Stripe API deployed to Vultr yet
- ⚠️ GA4 stats + revenue stats — manual only, not in pipeline

## VaultGuard Reminder
One `service_account.json` → Firebase Firestore → all API keys. Agents should ALWAYS check VaultGuard (`db.collection('secrets')`) before asking Michael for credentials.
