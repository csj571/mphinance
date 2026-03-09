---
description: Full system audit — map what works, what's broken, and what needs wiring
---

## Steps

1. Run the health check workflow first:
```
See: .agents/workflows/health-check.md
```

2. Check GH Actions for recent failures:
```bash
gh run list --limit 10 --repo mphinance/mphinance
```

3. Audit all markdown files:
```bash
find . -name "*.md" -not -path "./.git/*" -not -path "./node_modules/*" | sort
```

4. Check for broken references:
```bash
grep -r "tightspread\|VAULT.md\|api/ebook/checkout" --include="*.md" --include="*.html" --include="*.py" .
```

5. Check VaultGuard secrets:
```python
# Use firebase_admin to verify secrets are accessible
from firebase_admin import credentials, firestore
cred = credentials.Certificate('service_account.json')
db = firestore.client()
docs = db.collection('secrets').stream()
for doc in docs:
    print(f"  {doc.id}: {'SET' if doc.to_dict().get('value') else 'EMPTY'}")
```

6. Check Google Drive OAuth:
```bash
python3 scripts/supernote_reader.py --check 2>/dev/null || echo "Script not found or tokens expired"
```

7. Document findings in GHOST_HANDOFF.md

## Outputs
- Updated GHOST_HANDOFF.md
- Ghost Blog entry with audit results
- List of broken items with priority levels
