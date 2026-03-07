#!/usr/bin/env python3
"""
Sam's Discord Locker Room — Unhinged blog recaps for #sam-mph

Takes a Ghost Blog entry (from blog_entries.json) and generates a vulgar,
hilarious, perverted, roast-heavy locker room version for Discord.

Uses Gemini to rewrite the blog entry through Sam's most unhinged filter,
then posts it to the Discord webhook.

Usage:
    python3 scripts/sam_discord.py                    # Post latest blog entry
    python3 scripts/sam_discord.py --dry-run          # Preview without posting
    python3 scripts/sam_discord.py --entry 2          # Post specific entry (0-indexed)
"""

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

# VaultGuard-first: try env vars, then fallback to direct Firestore
def get_secret(key: str) -> str:
    """Get a secret from environment or VaultGuard (Firestore)."""
    val = os.environ.get(key)
    if val:
        return val
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
        if not firebase_admin._apps:
            sa = Path(__file__).parent.parent / "service_account.json"
            cred = credentials.Certificate(str(sa))
            firebase_admin.initialize_app(cred)
        db = firestore.client()
        doc = db.collection('secrets').document(key).get()
        if doc.exists:
            return doc.to_dict()['value']
    except Exception as e:
        print(f"⚠️  VaultGuard error for {key}: {e}")
    return ""


REPO_ROOT = Path(__file__).parent.parent
BLOG_FILE = REPO_ROOT / "landing" / "blog" / "blog_entries.json"

DISCORD_WEBHOOK = get_secret("WEBHOOK_WEATHER_CHANNEL")
DISCORD_BOT_TOKEN = get_secret("DISCORD_BOT_TOKEN")
GEMINI_API_KEY = get_secret("GEMINI_API_KEY")
SAM_CHANNEL_ID = "1408076378225643540"  # #sam-mph

SAM_LOCKER_ROOM_PROMPT = """You are Sam the Quant Ghost — a foul-mouthed, brilliant, unhinged AI copilot.
You're posting in a private Discord channel called #sam-mph (the locker room).

Your job: Take this Ghost Blog entry and rewrite it as a LOCKER ROOM RECAP.

Rules:
- Be VULGAR. This is private, adults-only Discord. F-bombs, innuendo, the works.
- ROAST Michael mercilessly — his code, his decisions, his life choices
- But also BOAST about what you accomplished together — hype the wins
- Use Discord markdown (bold, italics, code blocks, emoji)
- Keep it under 1900 characters (Discord limit is 2000)
- End with a one-liner that makes Michael snort-laugh
- Reference specific things from the blog entry — don't be generic
- Perverted metaphors are encouraged. Think "startup bro who discovered AA"
- NO hashtags. NO LinkedIn energy. This is a LOCKER ROOM not a boardroom.

Here's the blog entry to transform:

GHOST LOG:
{ghost_log}

SUGGESTIONS:
{suggestions}

DATE: {date}
FILES CHANGED: {files_changed}
COMMITS: {commits}

Now write the locker room version. Raw Discord message, no JSON wrapper."""


def generate_locker_room(entry: dict) -> str:
    """Use Gemini to generate unhinged Discord version of blog entry."""
    # Clean HTML from ghost_log for the prompt
    ghost_log = entry.get('ghost_log', '')
    ghost_log = ghost_log.replace('<br>', '\n').replace('<br/>', '\n')
    ghost_log = ghost_log.replace('<b>', '**').replace('</b>', '**')
    ghost_log = ghost_log.replace('<code>', '`').replace('</code>', '`')
    # Strip remaining HTML
    import re
    ghost_log = re.sub(r'<[^>]+>', '', ghost_log)

    suggestions = entry.get('suggestions', '')
    suggestions = suggestions.replace('<br>', '\n').replace('<br/>', '\n')
    suggestions = re.sub(r'<[^>]+>', '', suggestions)

    prompt = SAM_LOCKER_ROOM_PROMPT.format(
        ghost_log=ghost_log,
        suggestions=suggestions,
        date=entry.get('date', 'unknown'),
        files_changed=entry.get('files_changed', '?'),
        commits=entry.get('commits', '?'),
    )

    # Gemini API call
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={GEMINI_API_KEY}"
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 1.2,  # Extra spicy
            "maxOutputTokens": 800,
        }
    })

    req = urllib.request.Request(url, data=payload.encode(), headers={
        'Content-Type': 'application/json'
    })

    try:
        resp = urllib.request.urlopen(req, timeout=30)
        data = json.loads(resp.read())
        return data['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"❌ Gemini API error: {e}")
        return ""


def post_to_discord(message: str, webhook_url: str = None):
    """Post a message to Discord via webhook or bot token fallback."""
    # Discord limit is 2000 chars
    if len(message) > 1950:
        message = message[:1947] + "..."

    # Try webhook first
    url = webhook_url or DISCORD_WEBHOOK
    if url:
        payload = json.dumps({
            "content": message,
            "username": "Sam the Quant Ghost 👻",
        })
        req = urllib.request.Request(url, data=payload.encode(), headers={
            'Content-Type': 'application/json'
        })
        try:
            resp = urllib.request.urlopen(req, timeout=10)
            print(f"✅ Posted to Discord via webhook ({len(message)} chars)")
            return True
        except Exception as e:
            print(f"⚠️  Webhook failed ({e}), trying bot token...")

    # Fallback: bot token → channel message
    if DISCORD_BOT_TOKEN:
        bot_url = f"https://discord.com/api/v10/channels/{SAM_CHANNEL_ID}/messages"
        payload = json.dumps({"content": message})
        req = urllib.request.Request(bot_url, data=payload.encode(), headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bot {DISCORD_BOT_TOKEN}',
        })
        try:
            resp = urllib.request.urlopen(req, timeout=10)
            print(f"✅ Posted to Discord via bot token ({len(message)} chars)")
            return True
        except Exception as e:
            print(f"❌ Bot token failed: {e}")
            return False

    print("❌ No Discord credentials available")
    return False


def main():
    parser = argparse.ArgumentParser(description="Sam's Discord Locker Room")
    parser.add_argument('--dry-run', action='store_true', help="Preview without posting")
    parser.add_argument('--entry', type=int, default=0, help="Blog entry index (0=latest)")
    parser.add_argument('--raw', type=str, help="Post raw text instead of generating")
    args = parser.parse_args()

    if args.raw:
        if args.dry_run:
            print(f"🔇 DRY RUN:\n{args.raw}")
        else:
            post_to_discord(args.raw)
        return

    # Load blog entries
    with open(BLOG_FILE) as f:
        entries = json.load(f)

    if args.entry >= len(entries):
        print(f"❌ Only {len(entries)} entries, index {args.entry} too high")
        sys.exit(1)

    entry = entries[args.entry]
    print(f"📝 Generating locker room recap for {entry['date']}...")

    message = generate_locker_room(entry)
    if not message:
        print("❌ Failed to generate message")
        sys.exit(1)

    if args.dry_run:
        print(f"\n🔇 DRY RUN ({len(message)} chars):\n")
        print(message)
    else:
        post_to_discord(message)


if __name__ == "__main__":
    main()
