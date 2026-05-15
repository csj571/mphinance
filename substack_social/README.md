# substack_social

mph's Substack engagement + reading pipeline. Built on top of the vendored
substack-api library at `../vendor/substack-api/`.

## Why a vendored library
`substack-api` on npm (v4.0.0) is read-only by design. This repo's vendored
fork (`../vendor/substack-api/`) adds the engagement methods mph implemented
on top of v4:
  - `Post.like()` — was throwing not-implemented, now calls `/post/{id}/reaction`
  - `Post.addComment(body)` — was throwing, now calls `/posts/{id}/comments`
  - `Comment.like()` — NEW
  - `Comment.like()` / `likeComment` / `createComment` in CommentService
  - `Profile.getNotesForProfile()` in ProfileService

See `../vendor/substack-api/` for the full source.

## Setup
```bash
cd substack_social
npm install   # resolves substack-api from ../vendor/substack-api
```

## ⚠️ Build status of the vendored fork
As of 2026-05-15, the `dist/` in `../vendor/substack-api/` is stale and
does NOT contain the new engagement methods. The source is in `src/` but
hasn't been re-built since mph's edits.

To rebuild:
```bash
cd ../vendor/substack-api
pnpm install   # pnpm v9 on Node 18, or pnpm v10 on Node 22+
pnpm build     # produces fresh dist/
cd -
npm install    # re-link to refreshed dist
```

Until that build runs, the library calls available are the v4.0.0 baseline
ones only. Engagement features will throw "not implemented" or return
undefined methods.

## Scripts
- `npm run engage`  — interactive engagement dashboard (currently safe-mode/read-only)
- `npm run explore` — exploration / discovery sandbox

## Data
- `data/my-reads.json` + `data/my-reads.md` — your read list (generated)
- `data/daily-reads-digest.md` — daily digest summary
- `data/articles/` — cached article content

## Relationship to top-level Python tooling
- `../substack_dossier.py` / `../substack_poster.py` are the POST side
  (creating drafts via cookie-auth + ProseMirror JSON). Independent of this
  TS sub-project — they speak Substack's draft API directly.
- This sub-project is the READ + ENGAGE side, using substack-api's HTTP
  client + auth.

If a future task needs both create-draft AND like/comment, the two halves
can either share an SID/cookie via a shared `data/.substack_sid` file
(gitignored) or move toward a single typed client. For now they stay
independent.
