# 👻 GHOST_HANDOFF.md — Session 2026-03-09 (Landing Page Overhaul)

## ⚠️ RESUME PRIORITY

1. **Wire RSS fuzzy matcher into latest.md workflow** — `scripts/substack_draft_manager.py` has the logic. Need a pre-append check: "has this draft been published? If yes, archive and start fresh."
2. **Fix Daily Dossier pipeline failures** — 2 of last 3 GH Actions runs failed. Check logs.
3. **Wire Discord bot** — `scripts/sam_discord.py` exists but isn't running. Needs bot token + cron.
4. **Wire dossier → Substack drafts** — Draft system exists but only has Musings, not daily reports.

---

## What Happened This Session

### 1. Alpha.HUD Removed ✅
- Entire HUD section deleted: HTML (75 lines), CSS (24 lines), JS functions (`doHUD`, `loadHUD`, keypress listener), and HUD pick-button injection from daily picks fetch
- Zero orphan references remain

### 2. Landing Page Cleanup ✅
- **Scanline animation** — removed (was running at 3% opacity doing nothing after z-index fix)
- **Ghost Alpha price** — fixed "$49 one-time" → removed stale price reference (button says $8)
- **Duplicate stats** — removed from About section (same data lives in animated "By The Numbers" section)

### 3. CSS Externalized ✅
- All 5 inline `<style>` blocks extracted into `landing/styles.css` (828 lines)
- `index.html` reduced from **2271 → 1408 lines** (net -863 lines, or -38%)
- Single `<link rel="stylesheet" href="styles.css">` in head
- Zero functional changes — pure structural refactor

### 4. Section Reorder ✅
- **Products** moved from after Revenue to right after Hero
- New flow: Hero → **Products** → Daily Picks → 3x3 Setups → Revenue → About → Stats → Ebook → Analytics → Ghost Pulse → Footer

### 5. Substack Draft Updated ✅
- `docs/substack/latest.md` — new title: "The Pipeline That Reads My Handwriting (And Everything Else I Forgot I Said)"
- Added session notes: Ghost Alpha launch, Venus exorcism, system audit, workflow fixes
- This is Michael's running scratchpad — agents should APPEND session highlights, not replace

### 6. Ghost Blog Entry ✅
- "The Great HUD Exorcism + Landing Page Glow-Up"

## What's Still Broken / Needs Work
- ❌ Discord bot — scripts exist, not running
- ⚠️ Daily Dossier pipeline — intermittent failures
- ⚠️ Ebook checkout — Ghost Alpha on Stripe works ($8), but Playbook checkout endpoint still needs work
- ⚠️ GA4 stats + revenue stats — manual only, not in pipeline

## Key Files Changed
- `landing/index.html` — main landing page (1408 lines, was 2271)
- `landing/styles.css` — **NEW** — all extracted CSS (828 lines)
- `docs/substack/latest.md` — refreshed Substack draft
- `landing/blog/blog_entries.json` — new ghost blog entry

## VaultGuard Reminder
One `service_account.json` → Firebase Firestore → all API keys. Agents should ALWAYS check VaultGuard (`db.collection('secrets')`) before asking Michael for credentials.
