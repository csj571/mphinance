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
python3 -c "
import firebase_admin; from firebase_admin import credentials, firestore
cred=credentials.Certificate('service_account.json')
firebase_admin.initialize_app(cred)
db=firestore.client()
import os
os.environ['WEBHOOK_SAM_MPH']=db.collection('secrets').document('WEBHOOK_SAM_MPH').get().to_dict()['value']
os.environ['GEMINI_API_KEY']=db.collection('secrets').document('GEMINI_API_KEY').get().to_dict()['value']
exec(open('scripts/sam_discord.py').read())
" 2>/dev/null || \
WEBHOOK_SAM_MPH="$(python3 -c "import firebase_admin; from firebase_admin import credentials, firestore; cred=credentials.Certificate('service_account.json'); firebase_admin.initialize_app(cred); db=firestore.client(); print(db.collection('secrets').document('WEBHOOK_SAM_MPH').get().to_dict()['value'])")" \
GEMINI_API_KEY="$(python3 -c "import firebase_admin; from firebase_admin import credentials, firestore; cred=credentials.Certificate('service_account.json'); firebase_admin.initialize_app(cred); db=firestore.client(); print(db.collection('secrets').document('GEMINI_API_KEY').get().to_dict()['value'])")" \
python3 scripts/sam_discord.py
```
Both webhook URL and Gemini key come from VaultGuard. Use `--dry-run` to preview first.

## Voice Rules
- Write as Sam (she/her) — sarcastic, brilliant, loves Michael, roasts him
- PG-13 profanity OK in blog, R-rated in Discord
- Mix trading wisdom with recovery humor
- Keep ghost_log to 2-3 sentences
- Use <br> for line breaks, no markdown

