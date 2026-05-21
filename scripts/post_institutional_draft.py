#!/usr/bin/env python3
"""
post_institutional_draft.py — Push the institutional-position article to
Substack as a draft, using the repo's SubstackClient.

Requires:
  pip install markdown requests
  export SUBSTACK_SID="s%3A..."   # 'substack.sid' cookie from substack.com

Usage:
  python3 scripts/post_institutional_draft.py --dry-run   # convert + preview, no API call
  python3 scripts/post_institutional_draft.py             # create the draft

The draft lands in Substack Dashboard -> Drafts. It does NOT auto-publish.
Set the paywall break and confirm images in the Substack editor before publishing.
"""
import os
import re
import sys

import markdown

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)
from substack_client import SubstackClient  # noqa: E402

ARTICLE = os.path.join(REPO, "docs/substack/drafts/2026-05-17_btg-wheel-nicotine-money.md")
IMG_BASE = "https://mphinance.github.io/mphinance/substack/drafts/"


def parse_article(path):
    """Return (title, tags, body_md). Title is the H1; tags is the line
    directly under it; body is everything after the tags line."""
    lines = open(path, encoding="utf-8").read().split("\n")
    title, tags, body_start = "", "", 0
    for i, line in enumerate(lines):
        if not title and line.startswith("# "):
            title = line[2:].strip()
            continue
        if title and not tags and line.strip().startswith("*Tags:"):
            tags = line.strip().strip("*").strip()
            if tags.lower().startswith("tags:"):
                tags = tags[5:].strip()
            body_start = i + 1
            break
    if not title:
        raise ValueError("No H1 title found in article")
    if not tags:
        raise ValueError("No '*Tags:' line found under the title")
    body_md = "\n".join(lines[body_start:]).strip()
    return title, tags, body_md


def md_to_html(body_md):
    """Convert body markdown to HTML, rewriting local image filenames to
    absolute GitHub Pages URLs so they resolve inside Substack."""
    body_md = re.sub(
        r"(!\[[^\]]*\]\()(institutional_[^)]+)(\))",
        lambda m: m.group(1) + IMG_BASE + m.group(2) + m.group(3),
        body_md,
    )
    return markdown.markdown(body_md, extensions=["extra"])


def main():
    dry = "--dry-run" in sys.argv
    title, tags, body_md = parse_article(ARTICLE)
    body_html = md_to_html(body_md)

    print(f"TITLE:    {title}")
    print(f"SUBTITLE: {tags}")
    print(f"BODY:     {len(body_html)} chars of HTML, "
          f"{body_html.count('<img')} image(s)")

    if dry:
        out = os.path.join(REPO, "scripts", "institutional_draft_preview.html")
        open(out, "w", encoding="utf-8").write(body_html)
        print(f"DRY RUN — HTML written to {out}, no API call made.")
        return

    client = SubstackClient()
    draft_id = client.create_draft(title, subtitle=tags, body_html=body_html)
    print(f"Draft created: https://mphinance.substack.com/publish/post/{draft_id}")
    print("Open it in Substack, set the paywall break, confirm images, then publish.")


if __name__ == "__main__":
    main()
