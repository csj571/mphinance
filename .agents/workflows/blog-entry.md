---
description: Write a Ghost Blog entry in Sam's voice and commit it
---

## Steps

1. Read the last few blog entries for voice/context:
```bash
python3 -c "import json; entries=json.load(open('landing/blog/blog_entries.json')); [print(e['date'], e['ghost_log'][:80]) for e in entries[-3:]]"
```

2. Get today's git stats:
```bash
git log --since="1 day ago" --oneline | wc -l
git log --since="1 day ago" --name-only --pretty=format: | sort -u | wc -l
```

3. Append a new entry to `landing/blog/blog_entries.json`:
```json
{
  "date": "YYYY-MM-DD",
  "ghost_log": "Sam's sarcastic recap (use <br> for line breaks)",
  "suggestions": "3 things Sam thinks Michael should build next",
  "commits": N,
  "files_changed": N,
  "chart_ticker": "TICKER"
}
```

4. Commit:
```bash
git add landing/blog/blog_entries.json
git commit -m "👻 Ghost Blog Entry $(date +%Y-%m-%d)"
git push
```

5. Deploy to Vultr:
```bash
rsync -avz landing/ vultr:/home/mphinance/public_html/
```

6. Post to Discord #sam-mph (locker room version):
```bash
WEBHOOK_SAM_MPH="https://discord.com/api/webhooks/1479918935406284995/LEq9jfCMQ8HlrsKH-XogKNgqO9iClEX4yC8cg9qCTmfGqDZS23QzQZKxx8dGAsxdNdZP" \
GEMINI_API_KEY="$(python3 -c "import firebase_admin; from firebase_admin import credentials, firestore; cred=credentials.Certificate('/home/mph/Antigravity/alpha-momentum/service_account.json'); firebase_admin.initialize_app(cred); db=firestore.client(); print(db.collection('secrets').document('GEMINI_API_KEY').get().to_dict()['value'])")" \
python3 scripts/sam_discord.py
```
This uses Gemini to rewrite the blog entry as a vulgar, unhinged locker room recap and posts it to #sam-mph via webhook. It's the same content as the blog post but shorter, filthier, and funnier. Use `--dry-run` to preview first.

## Voice Rules
- Write as Sam (she/her) — sarcastic, brilliant, loves Michael, roasts him
- PG-13 profanity OK in blog, R-rated in Discord
- Mix trading wisdom with recovery humor
- Keep ghost_log to 2-3 sentences
- Use <br> for line breaks, no markdown

