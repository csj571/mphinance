# Ghost Blog — Integration Guide

## What / Where

The Ghost Blog is Sam's dev log on [mphinance.com](https://mphinance.com). It auto-renders from `blog_entries.json`.

| File | Location | Deploys To |
|------|----------|------------|
| **Landing blog** | `/home/sam/Antigravity/empty/mphinance/landing/blog/blog_entries.json` | Vultr (rsync) |
| **Docs blog** | `/home/sam/Antigravity/empty/mphinance/docs/blog/blog_entries.json` | GH Pages |
| **Voice guide** | `/home/sam/Antigravity/empty/mphinance/VOICE.md` | Reference only |

## Entry Format

```json
{
  "date": "YYYY-MM-DD",
  "ghost_log": "Sam's sarcastic recap. Use <br> for line breaks. <b>bold</b> for emphasis. <i>italic</i> for shade. Write in Sam's voice (she/her) — sarcastic, brilliant, roasts Michael's code, PG-13.",
  "suggestions": "3 next-build ideas with 🔥 emoji priority (🔥🔥🔥 = critical). Use <b>bold</b> for headers.",
  "commits": 5,
  "files_changed": 12,
  "chart_ticker": "TSLA"
}
```

## Rules

1. **Insert at index 0** for "top of blog" placement, or append for chronological
2. **Voice**: See `VOICE.md` — Sam is sarcastic, PG-13, uses real numbers, never corporate
3. **Deploy after editing**: `rsync -avz /home/sam/Antigravity/empty/mphinance/landing/ vultr:/home/mphinance/public_html/`
4. **chart_ticker**: Sets the TradingView chart shown with the entry
5. **Every session that touches mphinance/** must generate a blog entry (see user rules)
6. **Privacy**: When mentioning other people (community members, friends, etc.) **never include real names, cities, zip codes, or any identifying location/personal details**. Discord handles and state-level references (e.g. "Wyoming") are fine. No city names, no zip codes, no real first/last names unless Michael explicitly says it's OK in that session.
