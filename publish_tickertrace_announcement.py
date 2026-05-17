#!/usr/bin/env python3
"""
publish_tickertrace_announcement.py — Push the TickerTrace Free announcement to Substack as a draft.

Converts the markdown draft to HTML and creates a Substack draft post.
Review and publish from the Substack dashboard.
"""

import requests
import json
import os
import re
import sys

# ═══ Load secrets ═══
SECRETS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "secrets.env")
secrets = {}
with open(SECRETS_FILE) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            secrets[k] = v.strip('"')

SID = secrets.get('SUBSTACK_SID', '')
PUB = secrets.get('SUBSTACK_PUB_URL', 'mphinance.substack.com')

# ═══ Session setup ═══
session = requests.Session()
session.cookies.set('substack.sid', SID, domain='.substack.com')
HEADERS = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}


def get_user_id():
    """Fetch the authenticated user's ID."""
    r = session.get("https://substack.com/api/v1/user/self", headers=HEADERS, timeout=15)
    if r.status_code == 200:
        try:
            return r.json().get("id")
        except Exception:
            pass
    # Fallback: publication bylines
    r2 = session.get(f"https://{PUB}/api/v1/publication", headers=HEADERS, timeout=15)
    if r2.status_code == 200:
        bylines = r2.json().get("bylines", [])
        if bylines:
            return bylines[0].get("id")
    return None


def markdown_to_html(md_text):
    """Convert our specific markdown format to clean HTML for Substack."""
    lines = md_text.strip().split('\n')
    html_parts = []
    in_list = False
    skip_title = True  # Skip the H1 title line and byline

    for line in lines:
        stripped = line.strip()

        # Skip the H1 title (we use draft_title instead)
        if skip_title and stripped.startswith('# '):
            continue
        # Skip byline
        if skip_title and stripped.startswith('*by '):
            skip_title = False
            continue
        skip_title = False

        # Skip image markers (they'll be added manually in Substack editor)
        if stripped.startswith('*[IMAGE:'):
            html_parts.append(f'<p><em>{stripped.strip("*")}</em></p>')
            continue

        # H2 headers
        if stripped.startswith('## '):
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            html_parts.append(f'<h2>{stripped[3:]}</h2>')
            continue

        # H3 headers
        if stripped.startswith('### '):
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            html_parts.append(f'<h3>{stripped[4:]}</h3>')
            continue

        # Horizontal rule
        if stripped == '---':
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            html_parts.append('<hr>')
            continue

        # Empty lines
        if not stripped:
            if in_list:
                html_parts.append('</ul>')
                in_list = False
            continue

        # Bold text processing
        def process_inline(text):
            # Bold
            text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
            # Italic
            text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
            # Links - convert bare URLs
            # Already-linked markdown links
            text = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', text)
            return text

        processed = process_inline(stripped)

        # List items
        if stripped.startswith('- '):
            if not in_list:
                html_parts.append('<ul>')
                in_list = True
            item = process_inline(stripped[2:])
            html_parts.append(f'<li>{item}</li>')
            continue

        # Regular paragraphs
        html_parts.append(f'<p>{processed}</p>')

    if in_list:
        html_parts.append('</ul>')

    return '\n'.join(html_parts)


def create_draft(title, subtitle, body_html, user_id):
    """Create a Substack draft post."""
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

    r = session.post(f"https://{PUB}/api/v1/drafts", json=payload, headers=HEADERS, timeout=30)
    if r.status_code in (200, 201):
        data = r.json()
        return True, data.get("id")
    else:
        return False, f"HTTP {r.status_code}: {r.text[:500]}"


def main():
    # Read the markdown draft
    draft_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "docs/substack/drafts/2026-05-17_tickertrace-free-announcement.md"
    )

    print(f"📄 Reading draft: {draft_path}")
    with open(draft_path) as f:
        md_content = f.read()

    # Convert to HTML
    print("🔄 Converting markdown to HTML...")
    html_body = markdown_to_html(md_content)

    # Preview
    print(f"   HTML length: {len(html_body)} chars")
    print(f"   Preview: {html_body[:200]}...")

    # Authenticate
    print("🔑 Authenticating with Substack...")
    user_id = get_user_id()
    if not user_id:
        print("❌ SID expired! Refresh it:")
        print("   1. Log into mphinance.substack.com")
        print("   2. DevTools → Application → Cookies → copy 'substack.sid'")
        print("   3. Update secrets.env with the new SUBSTACK_SID value")
        return

    print(f"✅ Authenticated (user ID: {user_id})")

    # Create draft
    title = "TickerTrace Is Free Now. Here's Why."
    subtitle = "56 ETFs. 101 stocks. Open API. Open source. No paywall. No login. Just institutional-grade data, every market day."

    print(f"\n📝 Creating draft: {title}")
    ok, result = create_draft(title, subtitle, html_body, user_id)

    if ok:
        print(f"✅ Draft created! ID: {result}")
        print(f"   Edit URL: https://{PUB}/publish/post/{result}")
        print(f"\n🎯 Next steps:")
        print(f"   1. Open the edit URL above")
        print(f"   2. Add screenshots at the [IMAGE: ...] markers")
        print(f"   3. Preview, then publish!")
    else:
        print(f"❌ Failed: {result}")


if __name__ == "__main__":
    main()
