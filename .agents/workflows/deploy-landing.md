---
description: Deploy landing page to Vultr production server
---
// turbo-all

## Steps

1. Run from the mphinance repo root:
```bash
rsync -avz landing/ vultr:/home/mphinance/public_html/
```

2. Verify the deploy:
```bash
curl -sI https://mphinance.com | head -5
```

3. Check blog loads:
```bash
curl -sI https://mphinance.com/blog/ | head -5
```
