# Substack Reading, Summary & Engagement — Complete Skill Gist

> **Purpose**: Everything another AI needs to build a "Substack Reader/Summarizer" skill from this codebase. Covers reading feeds, summarizing posts, engaging (likes), scraping Notes, exporting subscribers, creating drafts, and managing draft lifecycle.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Auth Pattern (SID Cookie)](#2-auth-pattern-sid-cookie)
3. [Vendor SDK: substack-api (TypeScript)](#3-vendor-sdk-substack-api-typescript)
4. [Core Python Client: substack_client.py](#4-core-python-client-substack_clientpy)
5. [Daily Reads Summarizer: summarize-reads.ts](#5-daily-reads-summarizer-summarize-readsts)
6. [Engagement Script: engage.ts](#6-engagement-script-engagets)
7. [Notes Scraper: substack_notes_scraper.py](#7-notes-scraper-substack_notes_scraperpy)
8. [Subscriber Export: substack_export_subscribers.py](#8-subscriber-export-substack_export_subscriberspy)
9. [Draft Creation: substack_dossier.py](#9-draft-creation-substack_dossierpy)
10. [Draft Poster: substack_poster.py](#10-draft-poster-substack_posterpy)
11. [Draft Lifecycle Manager: substack_draft_manager.py](#11-draft-lifecycle-manager-substack_draft_managerpy)
12. [Cron Automation: substack_cron.sh](#12-cron-automation-substack_cronsh)
13. [Content Style & Voice Rules](#13-content-style--voice-rules)
14. [API Gotchas & Hall of Shame](#14-api-gotchas--hall-of-shame)
15. [File Map](#15-file-map)

---

## 1. Architecture Overview

The system has two halves:

### READ + ENGAGE side (TypeScript)
- Uses the vendored `substack-api` npm library (fork of v4.0.0 with engagement methods added)
- Fetches user feed via `/api/v1/reader/feed`
- Fetches full post content via `client.postForId(id)`
- Likes posts/notes via `post.like()` / `note.like()`
- Gets followed profiles via `profile.following()`
- Lives in `substack_social/` directory

### CREATE + PUBLISH side (Python)
- Direct HTTP calls to Substack's undocumented API (`/api/v1/drafts`, `/api/v1/archive`, etc.)
- Creates drafts using ProseMirror JSON (NOT rawHtml, NOT body_html — both broken)
- Manages draft lifecycle via RSS feed polling + fuzzy matching
- Lives in repo root (`substack_client.py`, `substack_dossier.py`, `substack_poster.py`) and `scripts/`

### Shared Auth
Both sides auth via the same `substack.sid` cookie (a session cookie from the browser). It expires periodically and must be refreshed manually from DevTools.

---

## 2. Auth Pattern (SID Cookie)

```
Auth Method: Cookie-based session (substack.sid)
How to get it:
  1. Log into substack.com in browser
  2. DevTools → Application → Cookies → copy 'substack.sid' value
  3. Export as env var: export SUBSTACK_SID="s%3A..."

Python usage:
  session = requests.Session()
  session.cookies.set("substack.sid", sid, domain=".substack.com")

TypeScript usage:
  const client = new SubstackClient({
    token: sid,
    publicationUrl: 'mphinance.substack.com',
  });

  // OR raw fetch:
  headers = { 'Cookie': `substack.sid=${token}` }

Env vars:
  SUBSTACK_SID       — The raw cookie value (URL-encoded)
  SUBSTACK_PUB_URL   — Publication domain (default: mphinance.substack.com)

SID Expiration:
  - Expires periodically (days to weeks)
  - When expired: API returns 403 or redirects to login
  - Must be refreshed manually from browser
```

---

## 3. Vendor SDK: substack-api (TypeScript)

**Location**: `vendor/substack-api/`
**Source repo**: npm `substack-api` v4.0.0 (forked with engagement additions)
**Build**: `pnpm install && pnpm build` (produces `dist/`)

### Key Architecture
```
src/
  substack-client.ts     — Main client class
  domain/                — Entity classes (Profile, Post, Note, Comment)
  internal/
    services/            — Business logic (FollowingService, NoteService, etc.)
    http-client.ts       — HTTP abstraction
    types/               — Internal Substack API types
  types/                 — Public type definitions
```

### Key Patterns
```typescript
// Entity-based API
const profile = await client.ownProfile();
for await (const post of profile.posts({ limit: 5 })) { ... }
for await (const note of profile.notes({ limit: 20 })) { ... }
for await (const user of profile.following({ limit: 100 })) { ... }

// Full post content
const fullPost = await client.postForId(postId);
const html = fullPost.htmlBody;

// Engagement (fork additions — may need rebuild)
await post.like();           // POST /post/{id}/reaction
await post.addComment(body); // POST /posts/{id}/comments
await note.like();
```

### Fork Additions (mph's edits in src/)
- `Post.like()` — calls `/post/{id}/reaction`
- `Post.addComment(body)` — calls `/posts/{id}/comments`
- `Comment.like()` — NEW
- `Profile.getNotesForProfile()` — in ProfileService

**⚠️ Build status**: As of 2026-05-15, `dist/` is stale. Must run `pnpm build` to get engagement methods working.

---

## 4. Core Python Client: substack_client.py

**Location**: `substack_client.py` (repo root)
**Dependencies**: `requests`

```python
class SubstackClient:
    def __init__(self, sid=None, pub="mphinance.substack.com"):
        # Auth via cookie
        self.session = requests.Session()
        self.session.cookies.set("substack.sid", sid, domain=".substack.com")

    def get_user_id(self) -> Optional[int]:
        # GET /api/v1/drafts?limit=1 → extract byline ID
        # Fallback: GET /api/v1/archive?sort=new&limit=1

    def create_draft(self, title, subtitle, body_html, audience="everyone") -> Optional[int]:
        # POST /api/v1/drafts
        # Uses rawHtml ProseMirror node (⚠️ DEPRECATED — see dossier.py for native nodes)
        payload = {
            "draft_title": title,
            "draft_subtitle": subtitle,
            "draft_body": json.dumps({
                "type": "doc",
                "content": [{"type": "rawHtml", "attrs": {"html": body_html}}]
            }),
            "draft_bylines": [{"id": user_id, "is_guest": False}],
            "type": "newsletter",
            "audience": "everyone",
        }

    def list_drafts(self, limit=10) -> list:
        # GET /api/v1/drafts?limit={limit}

    def check_auth(self) -> bool:
        return self.get_user_id() is not None
```

---

## 5. Daily Reads Summarizer: summarize-reads.ts

**Location**: `vendor/substack-api/samples/summarize-reads.ts`
**This is the core "reading/summary" script.**

### What It Does
1. Authenticates via SID cookie
2. Fetches the user's mixed content feed (posts + notes) from `https://substack.com/api/v1/reader/feed`
3. Paginates via `?cursor=` parameter
4. For each post from last 24 hours, fetches full HTML content via `client.postForId(id)`
5. Strips HTML to plain text
6. Compiles into a markdown digest with per-post summaries
7. Saves to `daily-reads-digest.md`

### Key API Endpoints Used
```
GET https://substack.com/api/v1/reader/feed
    → Returns mixed feed: posts, notes, chats
    → Paginate with ?cursor={nextCursor}
    → Rate limited (429) — wait 10s and retry

Feed item structure:
  {
    type: "post" | "comment",
    post: { id, title, post_date, canonical_url, description, publication_id },
    publication: { name, base_url },
    // For notes:
    context: { type: "note", timestamp, users: [{name, handle}] },
    comment: { body }
  }
```

### Full Script
```typescript
import { SubstackClient } from '../src/index'

// Auth
const client = new SubstackClient({ publicationUrl, token })
const isConnected = await client.testConnectivity()

// Fetch feed with pagination
let url = 'https://substack.com/api/v1/reader/feed';
const headers = {
  'Cookie': `substack.sid=${token}`,
  'Accept': 'application/json',
  'Content-Type': 'application/json',
  'User-Agent': 'Mozilla/5.0 ...'
};

while (hasMore) {
  const res = await fetch(url, { headers });
  if (res.status === 429) { await sleep(10000); continue; }
  const data = await res.json();
  const items = data.items || [];

  for (const item of items) {
    if (item.type === 'post') {
      // Full content fetch
      const fullPost = await client.postForId(item.post.id);
      const cleanText = stripHtml(fullPost.htmlBody);
      // Build digest entry...
    } else if (item.type === 'comment' && item.context?.type === 'note') {
      // Note content
      const author = item.context.users?.[0]?.name;
      const body = item.comment.body;
    }
  }

  if (data.nextCursor) {
    url = `https://substack.com/api/v1/reader/feed?cursor=${encodeURIComponent(data.nextCursor)}`;
    await sleep(500);
  } else { hasMore = false; }
}

// Write digest
fs.writeFileSync('daily-reads-digest.md', digest);
```

---

## 6. Engagement Script: engage.ts

**Location**: `substack_social/engage.ts`

### What It Does
1. Gets own profile and following list
2. For each followed profile, fetches recent posts (last 2 weeks)
3. Likes posts and notes (up to 200 likes per run)
4. Generates a reading list markdown with liked/read status

```typescript
const me = await client.ownProfile();
const following = [];
for await (const user of me.following({ limit: 100 })) {
  following.push(user);
}

for (const prof of following) {
  for await (const post of prof.posts({ limit: 10 })) {
    if (post.publishedAt > twoWeeksAgo) {
      await post.like();  // Engagement!
      // Also fetch full post for reading list
      const fp = await post.fullPost();
    }
  }
  for await (const note of prof.notes({ limit: 20 })) {
    await note.like();
  }
}
```

---

## 7. Notes Scraper: substack_notes_scraper.py

**Location**: `scripts/substack_notes_scraper.py`
**Dependencies**: `aiohttp`

### What It Does
Fetches Notes from any Substack author profile and ranks by engagement.

### Key API Endpoints
```
Profile lookup:
  GET https://substack.com/api/v1/user/{handle}/public_profile
  → Returns: { id, name, subscriberCount, bio }

Notes feed:
  GET https://substack.com/api/v1/reader/feed/profile/{user_id}?types[]=comment&limit={limit}&offset={offset}
  → Returns: { items: [{ comment: { body, date, reactions, children_count, restacks, canonical_url, attachments } }] }
```

### Usage
```bash
python3 scripts/substack_notes_scraper.py --handle dickcapital --limit 50
python3 scripts/substack_notes_scraper.py --handle dickcapital --json
```

### Engagement Score Formula
```python
score = likes * 3 + comments * 2 + restacks
```

---

## 8. Subscriber Export: substack_export_subscribers.py

**Location**: `scripts/substack_export_subscribers.py`
**Dependencies**: `playwright`

### What It Does
Exports subscriber emails via Playwright browser automation (Substack doesn't expose emails via API).

### Methods (in priority order)
1. **Direct API export**: `GET {PUB_URL}/api/v1/subscribers/export` — fastest if it works
2. **Dashboard UI click**: Navigate to `/publish/users`, find overflow menu, click Export
3. **DOM scraping**: Scroll through subscriber table, extract email-like text from DOM

---

## 9. Draft Creation: substack_dossier.py

**Location**: `substack_dossier.py` (repo root)
**This is the CORRECT way to create drafts** (uses native ProseMirror nodes).

### Critical Gotcha (Hall of Shame)
```
rawHtml node type: BROKEN/DEPRECATED (March 2026)
body_html top-level field: Creates empty drafts
ONLY working approach: Native ProseMirror JSON nodes
```

### ProseMirror Node Builders
```python
def p(*texts):
    """Paragraph node"""
    return {'type': 'paragraph', 'content': [{'type': 'text', 'text': str(t)} for t in texts]}

def h(level, text):
    """Heading node"""
    return {'type': 'heading', 'attrs': {'level': level}, 'content': [{'type': 'text', 'text': str(text)}]}

def bold(text):
    return {'type': 'text', 'text': str(text), 'marks': [{'type': 'bold'}]}

def italic(text):
    return {'type': 'text', 'text': str(text), 'marks': [{'type': 'italic'}]}

def link(text, url):
    return {'type': 'text', 'text': str(text), 'marks': [{'type': 'link', 'attrs': {'href': url}}]}
```

### Draft Creation Payload
```python
payload = {
    "draft_title": title,
    "draft_subtitle": subtitle,
    "draft_body": json.dumps({"type": "doc", "content": nodes}),
    "draft_bylines": [{"id": user_id, "is_guest": False}],
    "type": "newsletter",
    "audience": "everyone",
}
# POST https://{pub}/api/v1/drafts
```

### Image Upload
```python
def upload_image(self, image_path: str) -> str | None:
    files = {"file": (basename, f, "image/png")}
    r = self.session.post(f"https://{pub}/api/v1/media", files=files)
    return r.json().get("url") or r.json().get("imageUrl")
```

### ASCII Safety
Substack's ProseMirror breaks on non-ASCII characters. Must strip:
```python
def _ascii_safe(text: str) -> str:
    # Replace em-dashes, arrows, bullets, smart quotes, etc.
    # Then: text.encode('ascii', 'ignore').decode('ascii')
```

---

## 10. Draft Poster: substack_poster.py

**Location**: `substack_poster.py` (repo root)
**Simpler version using rawHtml** (⚠️ rawHtml may be broken — prefer dossier.py approach)

### User ID Resolution (4 fallback methods)
```python
1. GET https://substack.com/api/v1/user/self → .id
2. GET https://{PUB}/api/v1/publication → .bylines[0].id
3. GET https://{PUB}/api/v1/drafts?limit=1 → .publishedBylines[0].id
4. GET https://{PUB}/api/v1/archive?sort=new&limit=1 → .publishedBylines[0].id
```

---

## 11. Draft Lifecycle Manager: substack_draft_manager.py

**Location**: `scripts/substack_draft_manager.py`
**Dependencies**: `feedparser` (optional, falls back to `xml.etree`)

### Commands
```bash
python3 scripts/substack_draft_manager.py status          # Show draft system status
python3 scripts/substack_draft_manager.py check           # Poll RSS, archive published drafts
python3 scripts/substack_draft_manager.py promote         # Promote next draft to latest.md
python3 scripts/substack_draft_manager.py inject-paywall  # Add paywall marker to draft
```

### How `check` Works
1. Fetches RSS from `https://mphinance.substack.com/feed/`
2. Lists all `.md` files in `docs/substack/musings/` and `docs/substack/dossier/`
3. Fuzzy-matches draft titles against RSS titles (threshold: 55%)
4. Moves matched drafts to `docs/substack/archive/`
5. Logs voice comparison data for future VOICE.md refinement

### Directory Structure
```
docs/substack/
  latest.md            — Current "next up" draft
  musings/             — Human-written drafts
  dossier/             — Auto-generated dossier drafts
  archive/             — Published (archived) drafts
  voice_refinement_log.json — Title comparison data
```

### Paywall Injection
```python
PAYWALL_MARKER = """
---
<!-- PAYWALL BREAK -->
## 🔒 Paid Subscribers: Deep Dive
"""
# Injected before a specific section (default: "AI Synthesis")
# Or at 60% mark if section not found
```

---

## 12. Cron Automation: substack_cron.sh

```bash
# Refresh SID (every 3 days at noon)
0 12 */3 * * scripts/substack_cron.sh refresh

# Draft lifecycle check (Mon-Fri at 6AM CST, after 5AM pipeline)
0 12 * * 1-5 scripts/substack_cron.sh draft
```

The `draft` command:
1. `git pull --rebase`
2. Runs `substack_draft_manager.py check` (polls RSS, archives published)

---

## 13. Content Style & Voice Rules

### Hard Rules (NON-NEGOTIABLE)
- **NO EM DASHES (—). EVER.** Use commas, periods, colons, or semicolons instead.
- **NO MARKDOWN TABLES.** Substack renders them as garbage. Generate Bloomberg-terminal-style dark-theme images instead.
- **Images inline in markdown**: `![Alt text](filename.png)`

### Voice (Michael Hanko / Momentum Phinance)
- Irreverent educator — teaches finance like a friend at a bar
- Self-deprecating, direct, PG-13 profanity
- Short paragraphs (3 sentences max)
- Bold key numbers. Readers skim.
- No passive voice, no hedging, no corporate speak
- Recovery/AA metaphors woven naturally into trading

### Article Structure
```
1. Hero image (generated, dark theme)
2. Bold opener (1-2 paragraphs, hook)
3. Context section (market RIGHT NOW)
4. The meat (data + infographics + personality)
5. "Here's the truth..." pivot
6. <!--paywall--> (if applicable)
7. Paid-only deep dive
8. CTA (never desperate)
9. Recovery wisdom closer
10. Signature: "- Michael Hanko"
```

### Image Generation Rules
- Dark background (#0a0a0a or #111)
- Neon green (#00ff41) bullish, gold (#f0b400) caution, red (#e53935) danger
- Bloomberg terminal aesthetic
- Landscape 1200x600 to 1200x800

---

## 14. API Gotchas & Hall of Shame

### Substack Draft API
1. **rawHtml node type is BROKEN** (March 2026). Even `<p>Hello</p>` causes silent editor failure with "Something has gone wrong". DO NOT USE.
2. **body_html top-level field** creates drafts but content is EMPTY.
3. **ONLY working approach**: Native ProseMirror JSON (`{'type': 'paragraph'}`, `{'type': 'heading'}`).
4. **Non-ASCII characters** cause editor bugs in ProseMirror content. Strip with `_ascii_safe()`.
5. **SID expiration** is silent — API just starts returning 403 or empty responses.

### Feed API
6. **Rate limiting**: Returns 429. Wait 10 seconds and retry.
7. **Feed not strictly sorted**: Items can be out of order. Use a stop-counter (10 consecutive old items) instead of stopping on first old item.
8. **Subscriber emails**: Not exposed via any API. Must use Playwright browser automation.

---

## 15. File Map

```
mphinance/
├── substack_client.py              # Core Python API client (create drafts, auth)
├── substack_dossier.py             # Auto-draft dossier to Substack (ProseMirror)
├── substack_poster.py              # Draft poster with hardcoded posts (rawHtml)
├── SUBSTACK.md                     # Content rules and article instructions
├── VOICE.md                        # Michael's writing voice guide
├── secrets.env                     # SUBSTACK_SID, SUBSTACK_PUB_URL (gitignored)
│
├── scripts/
│   ├── substack_notes_scraper.py   # Scrape Notes from any author profile
│   ├── substack_export_subscribers.py # Export subscriber emails via Playwright
│   ├── substack_draft_manager.py   # Draft lifecycle: check RSS, archive, promote
│   └── substack_cron.sh            # Cron wrapper for automation
│
├── substack_social/                # READ + ENGAGE side (TypeScript)
│   ├── engage.ts                   # Like posts/notes across followed profiles
│   ├── explore.ts                  # SDK exploration sandbox
│   ├── package.json                # Links to vendored substack-api
│   ├── README.md                   # Architecture notes
│   └── data/
│       ├── my-reads.md             # List of followed publications
│       ├── daily-reads-digest.md   # Generated daily digest (350KB+)
│       └── articles/               # Cached article content
│
└── vendor/substack-api/            # Forked substack-api npm library
    ├── src/
    │   ├── substack-client.ts      # Main client
    │   ├── domain/                 # Profile, Post, Note, Comment entities
    │   └── internal/services/      # FollowingService, NoteService, etc.
    ├── samples/
    │   └── summarize-reads.ts      # Daily digest generator (KEY SCRIPT)
    ├── package.json                # pnpm workspace
    └── CLAUDE.md                   # SDK architecture docs
```

---

## Quick Start for Skill Builder

If you're building a skill from this, here's the minimum viable version:

### "Substack Daily Digest" Skill
1. **Auth**: Accept `SUBSTACK_SID` env var
2. **Fetch feed**: `GET https://substack.com/api/v1/reader/feed` with cookie auth
3. **Paginate**: Use `?cursor=` for next page, handle 429 rate limits
4. **Get full content**: For each post, fetch via `postForId()` or direct API
5. **Strip HTML → plain text**
6. **Generate markdown digest** with publication, author, date, excerpt
7. **Optional engagement**: Like posts via `POST /post/{id}/reaction`

### Dependencies
- **TypeScript path**: `substack-api` (vendored fork)
- **Python path**: `requests`, `aiohttp` (async), optionally `playwright` for subscriber export
