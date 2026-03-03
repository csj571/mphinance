# Substack Auto-Publish Integration

## Goal

Automatically publish watchlist deep dives to Substack after generation,
eliminating the manual copy-paste step.

## Package

- **PyPI:** <https://pypi.org/project/substack-api/>
- **Install:** `pip install substack-api`

## How It Would Work

1. Watchlist deep dive generates `docs/ticker/{SYMBOL}/deep_dive.md`
2. After generation, script reads the markdown
3. Uses `substack-api` to create a draft or publish directly
4. Tags with `mphinance` and the ticker symbol

## Implementation Notes

```python
from substack_api import Api

api = Api(email="your@email.com", password="your_password")
# OR use cookie-based auth

# Create a draft from the deep dive markdown
api.create_post(
    title=f"[{ticker}] Deep Dive: {title}",
    content=md_content,
    subtitle=f"Full technical breakdown — {date}",
    tags=["mphinance", ticker.lower()],
    is_draft=True,  # Set to False for auto-publish
)
```

## Auth Setup

- Substack credentials stored in `.env`:

  ```
  SUBSTACK_EMAIL=your@email.com
  SUBSTACK_PASSWORD=your_password
  ```

- OR use cookie auth (more reliable):

  ```
  SUBSTACK_COOKIE=your_session_cookie
  ```

## Where to Add

- Add `--publish` flag to `watchlist_dive.py`
- After deep dive generation, call Substack API
- Keep it local-only (not in GitHub Actions) to control what gets published
- Could also add a `--draft` flag to create drafts for review before publishing

## Future Ideas

- Auto-attach the rendered HTML as a "web version" link
- Include the JSON data endpoint URL in the post
- Schedule posts for specific times (morning before market open)
- Cross-post to Twitter/X via the existing twitter skill
