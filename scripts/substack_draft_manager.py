#!/usr/bin/env python3
"""
Substack Draft Manager — GitHub-Based Draft System

Manages the lifecycle of Substack drafts:
1. Checks Substack RSS feed for published posts
2. Fuzzy-matches draft titles against published titles
3. Archives published drafts, promotes next draft to latest.md
4. Optionally generates dossier drafts from pipeline output

Usage:
    python3 scripts/substack_draft_manager.py check     # Check RSS & archive published drafts
    python3 scripts/substack_draft_manager.py promote    # Promote next draft to latest.md
    python3 scripts/substack_draft_manager.py status     # Show current draft status
"""

import os
import sys
import re
import shutil
import glob
import json
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

# Try to import feedparser, fall back to xml.etree
try:
    import feedparser
    HAS_FEEDPARSER = True
except ImportError:
    HAS_FEEDPARSER = False

import urllib.request
import xml.etree.ElementTree as ET

REPO_ROOT = Path(__file__).parent.parent
SUBSTACK_DIR = REPO_ROOT / "docs" / "substack"
MUSINGS_DIR = SUBSTACK_DIR / "musings"
DOSSIER_DIR = SUBSTACK_DIR / "dossier"
ARCHIVE_DIR = SUBSTACK_DIR / "archive"
LATEST_FILE = SUBSTACK_DIR / "latest.md"
FEED_URL = "https://mphinance.substack.com/feed/"

# Also flag content for the ebook pipeline
EBOOK_FLAG_DIR = REPO_ROOT / "docs" / "ebook_candidates"

FUZZY_THRESHOLD = 0.55  # Titles need to be 55%+ similar to count as a match


def extract_title(filepath: Path) -> str:
    """Extract the H1 title from a markdown file."""
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if line.startswith("# "):
                # Strip emoji and markdown formatting
                title = re.sub(r'^#\s+', '', line)
                title = re.sub(r'[^\w\s\-—]', '', title).strip()
                return title
    return filepath.stem


def fuzzy_match(a: str, b: str) -> float:
    """Compare two titles using SequenceMatcher. Returns 0-1 similarity."""
    # Normalize: lowercase, strip punctuation, collapse whitespace
    def normalize(s):
        s = s.lower()
        s = re.sub(r'[^\w\s]', '', s)
        s = re.sub(r'\s+', ' ', s).strip()
        return s
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


def fetch_rss_titles() -> list[dict]:
    """Fetch published post titles from Substack RSS feed."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; mphinance-bot/1.0)'
    }
    req = urllib.request.Request(FEED_URL, headers=headers)
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        data = resp.read()
    except Exception as e:
        print(f"⚠️  Could not fetch RSS feed: {e}")
        return []

    root = ET.fromstring(data)
    posts = []
    for item in root.findall('.//item'):
        title_el = item.find('title')
        pubdate_el = item.find('pubDate')
        link_el = item.find('link')
        if title_el is not None:
            posts.append({
                'title': title_el.text or '',
                'pubDate': pubdate_el.text if pubdate_el is not None else '',
                'link': link_el.text if link_el is not None else '',
            })
    return posts


def get_all_drafts() -> list[Path]:
    """Get all draft files from musings/ and dossier/ directories, sorted newest first."""
    drafts = []
    for d in [MUSINGS_DIR, DOSSIER_DIR]:
        if d.exists():
            drafts.extend(d.glob("*.md"))
    # Sort by filename (date prefix) descending
    return sorted(drafts, key=lambda p: p.name, reverse=True)


def check_and_archive():
    """Check RSS feed and archive any drafts that have been published."""
    print("🔍 Checking Substack RSS feed for published drafts...\n")
    
    rss_posts = fetch_rss_titles()
    if not rss_posts:
        print("No RSS posts found or feed unavailable.")
        return
    
    print(f"📰 Found {len(rss_posts)} published posts on Substack\n")
    
    drafts = get_all_drafts()
    if not drafts:
        print("No drafts found.")
        return
    
    archived = 0
    for draft in drafts:
        draft_title = extract_title(draft)
        best_match = 0
        best_post = None
        
        for post in rss_posts:
            score = fuzzy_match(draft_title, post['title'])
            if score > best_match:
                best_match = score
                best_post = post
        
        if best_match >= FUZZY_THRESHOLD:
            print(f"✅ MATCH ({best_match:.0%}): \"{draft_title}\"")
            print(f"   → Published as: \"{best_post['title']}\"")
            print(f"   → Archiving {draft.name}...")
            
            # Move to archive
            ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
            dest = ARCHIVE_DIR / draft.name
            shutil.move(str(draft), str(dest))
            archived += 1
            
            # Voice refinement: save the mapping for VOICE.md analysis
            _log_voice_comparison(draft_title, best_post['title'], best_match)
        else:
            status = f"({best_match:.0%} best match)" if best_post else "(no match)"
            print(f"📝 DRAFT: \"{draft_title}\" {status}")
    
    print(f"\n📦 Archived {archived} published drafts.")
    
    # If latest.md was archived, promote next draft
    if archived > 0:
        promote_next()


def _log_voice_comparison(draft_title: str, published_title: str, score: float):
    """Log title comparisons for future VOICE.md refinement."""
    log_file = SUBSTACK_DIR / "voice_refinement_log.json"
    log = []
    if log_file.exists():
        with open(log_file) as f:
            log = json.load(f)
    
    log.append({
        "date": datetime.now().isoformat(),
        "draft_title": draft_title,
        "published_title": published_title,
        "similarity": round(score, 3),
        "title_changed": score < 0.95,
    })
    
    with open(log_file, 'w') as f:
        json.dump(log, f, indent=2)


def promote_next():
    """Copy the most recent unarchived draft to latest.md."""
    drafts = get_all_drafts()
    if not drafts:
        print("📭 No drafts to promote. latest.md cleared.")
        if LATEST_FILE.exists():
            LATEST_FILE.write_text("# No Draft Available\n\nCheck back soon!\n")
        return
    
    next_draft = drafts[0]
    print(f"\n🔄 Promoting {next_draft.name} → latest.md")
    shutil.copy2(str(next_draft), str(LATEST_FILE))
    
    # Also flag for ebook pipeline
    EBOOK_FLAG_DIR.mkdir(parents=True, exist_ok=True)
    flag = EBOOK_FLAG_DIR / f"substack_{next_draft.stem}.flag"
    flag.write_text(f"source: {next_draft}\nflagged: {datetime.now().isoformat()}\n")
    print(f"📚 Flagged for ebook pipeline: {flag.name}")


def show_status():
    """Show current draft system status."""
    print("📊 Substack Draft System Status\n")
    print("=" * 50)
    
    # Latest
    if LATEST_FILE.exists():
        title = extract_title(LATEST_FILE)
        print(f"\n📌 Latest Draft: \"{title}\"")
    else:
        print("\n📌 Latest Draft: (none)")
    
    # Musings
    musings = sorted(MUSINGS_DIR.glob("*.md"), reverse=True) if MUSINGS_DIR.exists() else []
    print(f"\n✏️  Musings ({len(musings)}):")
    for m in musings[:5]:
        print(f"   • {m.name}: \"{extract_title(m)}\"")
    
    # Dossier drafts
    dossiers = sorted(DOSSIER_DIR.glob("*.md"), reverse=True) if DOSSIER_DIR.exists() else []
    print(f"\n📊 Dossier Drafts ({len(dossiers)}):")
    for d in dossiers[:5]:
        print(f"   • {d.name}: \"{extract_title(d)}\"")
    
    # Archive
    archived = sorted(ARCHIVE_DIR.glob("*.md"), reverse=True) if ARCHIVE_DIR.exists() else []
    print(f"\n📦 Archived ({len(archived)}):")
    for a in archived[:5]:
        print(f"   • {a.name}: \"{extract_title(a)}\"")
    
    print()


PAYWALL_MARKER = """
---

<!-- PAYWALL BREAK — Everything below is for paid subscribers -->
<!-- On Substack: Insert paywall divider here -->

## 🔒 Paid Subscribers: Deep Dive

"""

SIGNATURE_FOOTER = """
---

— Michael

*Momentum Phinance — [mphinance.com](https://mphinance.com)*
*TraderDaddy Pro — [traderdaddy.pro](https://www.traderdaddy.pro/register?ref=8DUEMWAJ)*
*Ghost Alpha Dossier — [Daily AI Report](https://mphinance.github.io/mphinance/)*
*Sam's Dev Log — [Ghost Blog](https://mphinance.com/blog.html)*
"""


def inject_paywall(filepath: Path, before_section: str = "AI Synthesis"):
    """Inject a paywall break before a specific section in a draft."""
    content = filepath.read_text()

    # Find the section header to put the paywall before
    pattern = f"## {before_section}"
    alt_pattern = f"## 🤖 {before_section}"

    if pattern in content:
        content = content.replace(pattern, PAYWALL_MARKER + pattern)
        print(f"🔒 Paywall injected before '{before_section}' in {filepath.name}")
    elif alt_pattern in content:
        content = content.replace(alt_pattern, PAYWALL_MARKER + alt_pattern)
        print(f"🔒 Paywall injected before '{before_section}' in {filepath.name}")
    else:
        # No matching section, insert 60% through the document
        lines = content.split('\n')
        insert_at = int(len(lines) * 0.6)
        lines.insert(insert_at, PAYWALL_MARKER)
        content = '\n'.join(lines)
        print(f"🔒 Paywall injected at 60% mark in {filepath.name} (no '{before_section}' section found)")

    # Add signature if not present
    if "traderdaddy.pro" not in content.lower():
        content = content.rstrip() + SIGNATURE_FOOTER

    filepath.write_text(content)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"

    if cmd == "check":
        check_and_archive()
    elif cmd == "promote":
        promote_next()
    elif cmd == "status":
        show_status()
    elif cmd == "inject-paywall":
        # Inject paywall into latest.md or specified file
        target = Path(sys.argv[2]) if len(sys.argv) > 2 else LATEST_FILE
        section = sys.argv[3] if len(sys.argv) > 3 else "AI Synthesis"
        inject_paywall(target, section)
    else:
        print(f"Unknown command: {cmd}")
        print("Usage: substack_draft_manager.py {check|promote|status|inject-paywall}")
        sys.exit(1)

