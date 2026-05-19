#!/usr/bin/env python3
"""
substack_client.py — Reusable Substack API client.

Auth: Pass SUBSTACK_SID as env var, or inline via SID param.
      SID is the raw cookie value from substack.com.

Usage:
    export SUBSTACK_SID="s%3A..."
    python3 substack_client.py                   # Test auth
    python3 substack_client.py --draft           # Create a test draft

Programmatic use:
    from substack_client import SubstackClient
    client = SubstackClient()
    draft_id = client.create_draft("Title", "Subtitle", "<p>Body HTML</p>")
    print(f"Draft: https://mphinance.substack.com/publish/post/{draft_id}")
"""

import os
import sys
import json
import requests
from typing import Optional

PUB = "mphinance.substack.com"


class SubstackClient:
    def __init__(self, sid: Optional[str] = None, pub: str = PUB):
        self.pub = pub
        self.sid = sid or os.environ.get("SUBSTACK_SID", "")
        if not self.sid:
            raise ValueError("SUBSTACK_SID not set. Export it or pass sid= to SubstackClient().")

        self.session = requests.Session()
        # Pass cookie URL-encoded — Substack accepts both encoded and decoded
        self.session.cookies.set("substack.sid", self.sid, domain=".substack.com")
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "Accept": "application/json",
        }

    def get_user_id(self) -> Optional[int]:
        """Fetch authenticated user ID. Returns None if SID is expired."""
        # Try drafts endpoint — most reliable for getting byline id
        r = self.session.get(
            f"https://{self.pub}/api/v1/drafts?limit=1",
            headers=self.headers,
            timeout=15,
        )
        if r.status_code == 200:
            data = r.json()
            posts = data.get("posts", data) if isinstance(data, dict) else data
            if isinstance(posts, list) and posts:
                bylines = posts[0].get("publishedBylines", [])
                if bylines:
                    return bylines[0].get("id")

        # Fallback: archive
        r2 = self.session.get(
            f"https://{self.pub}/api/v1/archive?sort=new&limit=1",
            headers=self.headers,
            timeout=15,
        )
        if r2.status_code == 200:
            posts = r2.json()
            if posts:
                bylines = posts[0].get("publishedBylines", [])
                if bylines:
                    return bylines[0].get("id")

        return None

    def create_draft(
        self,
        title: str,
        subtitle: str = "",
        body_html: str = "",
        audience: str = "everyone",
    ) -> Optional[int]:
        """
        Create a Substack draft. Returns draft ID on success, None on failure.
        Draft will appear in Dashboard → Drafts.
        """
        user_id = self.get_user_id()
        if not user_id:
            raise RuntimeError("SID expired or invalid — re-grab from browser cookies.")

        payload = {
            "draft_title": title,
            "draft_subtitle": subtitle,
            "draft_body": json.dumps({
                "type": "doc",
                "content": [{"type": "rawHtml", "attrs": {"html": body_html}}],
            }),
            "draft_bylines": [{"id": user_id, "is_guest": False}],
            "type": "newsletter",
            "audience": audience,
        }

        r = self.session.post(
            f"https://{self.pub}/api/v1/drafts",
            json=payload,
            headers=self.headers,
            timeout=30,
        )

        if r.status_code in (200, 201):
            draft_id = r.json().get("id")
            return draft_id
        else:
            raise RuntimeError(f"Draft creation failed ({r.status_code}): {r.text[:300]}")

    def list_drafts(self, limit: int = 10) -> list:
        """List recent drafts."""
        r = self.session.get(
            f"https://{self.pub}/api/v1/drafts?limit={limit}",
            headers=self.headers,
            timeout=15,
        )
        if r.status_code == 200:
            data = r.json()
            return data.get("posts", data) if isinstance(data, dict) else data
        return []

    def check_auth(self) -> bool:
        """Returns True if SID is valid."""
        return self.get_user_id() is not None


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    sid = os.environ.get("SUBSTACK_SID", "")

    # Allow passing SID as first arg for quick testing
    if len(sys.argv) > 1 and not sys.argv[1].startswith("--"):
        sid = sys.argv[1]

    try:
        client = SubstackClient(sid=sid)
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)

    if "--draft" in sys.argv:
        print("📝 Creating test draft...")
        try:
            draft_id = client.create_draft(
                title="[TEST] Substack API Working",
                subtitle="Automated test draft — safe to delete",
                body_html="<p>If you're seeing this, the Substack API client is working correctly.</p>",
            )
            print(f"✅ Draft created! ID: {draft_id}")
            print(f"   Edit: https://{PUB}/publish/post/{draft_id}")
        except RuntimeError as e:
            print(f"❌ {e}")
            sys.exit(1)
    else:
        print("🔑 Testing auth...")
        user_id = client.get_user_id()
        if user_id:
            print(f"✅ Auth OK — user ID: {user_id}")
            drafts = client.list_drafts(limit=3)
            print(f"📋 Recent drafts ({len(drafts)}):")
            for d in drafts:
                print(f"   [{d.get('id')}] {d.get('draft_title', d.get('title', '?'))[:60]}")
        else:
            print("❌ Auth failed — SID expired or invalid")
            sys.exit(1)


if __name__ == "__main__":
    main()
