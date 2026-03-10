#!/usr/bin/env python3
"""
Sam's Discord Monitor — Channel summaries via bot token + Gemini

Reads recent messages from Discord channels using the bot token,
summarizes them with Gemini, and posts the summary to #sam-mph.

Summaries are stored locally in /tmp/discord_summaries/ (NEVER in git).

Usage:
    python3 scripts/sam_discord_monitor.py                     # Summarize home server
    python3 scripts/sam_discord_monitor.py --guild GUILD_ID    # Summarize specific server
    python3 scripts/sam_discord_monitor.py --hours 48          # Last 48 hours (default: 24)
    python3 scripts/sam_discord_monitor.py --dry-run           # Print summary, don't post
    python3 scripts/sam_discord_monitor.py --list-guilds       # List servers the bot is in
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Local-only storage — never in git
SUMMARY_DIR = Path("/tmp/discord_summaries")
SUMMARY_DIR.mkdir(exist_ok=True)


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


BOT_TOKEN = get_secret("DISCORD_BOT_TOKEN")
GEMINI_API_KEY = get_secret("GEMINI_API_KEY")
WEBHOOK_SAM_MPH = get_secret("WEBHOOK_SAM_MPH")


def discord_api(endpoint: str) -> dict | list | None:
    """Call Discord API via curl (Cloudflare blocks urllib)."""
    url = f"https://discord.com/api/v10{endpoint}"
    result = subprocess.run(
        ['curl', '-s', '-H', f'Authorization: Bot {BOT_TOKEN}',
         '-H', 'User-Agent: sam-bot/1.0', url],
        capture_output=True, text=True, timeout=15
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"❌ Bad response from Discord: {result.stdout[:200]}")
        return None


def list_guilds() -> list[dict]:
    """List all guilds the bot is in."""
    resp = discord_api("/users/@me/guilds")
    if isinstance(resp, list):
        return resp
    print(f"❌ Could not list guilds: {resp}")
    return []


def get_channels(guild_id: str) -> list[dict]:
    """Get text channels for a guild."""
    resp = discord_api(f"/guilds/{guild_id}/channels")
    if isinstance(resp, list):
        # Filter to text channels only (type 0)
        return [c for c in resp if c.get('type') == 0]
    print(f"❌ Could not get channels: {resp}")
    return []


def get_messages(channel_id: str, hours: int = 24, limit: int = 50) -> list[dict]:
    """Get recent messages from a channel."""
    # Calculate snowflake for the cutoff time
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    # Discord snowflake: (timestamp_ms - discord_epoch) << 22
    discord_epoch = 1420070400000
    cutoff_snowflake = int((cutoff.timestamp() * 1000 - discord_epoch) * (2**22))

    resp = discord_api(f"/channels/{channel_id}/messages?limit={limit}&after={cutoff_snowflake}")
    if isinstance(resp, list):
        return resp
    return []


def summarize_with_gemini(channel_data: dict, guild_name: str) -> str:
    """Use Gemini to summarize channel messages."""
    # Build the context
    channel_summaries = []
    for channel_name, messages in channel_data.items():
        if not messages:
            continue
        msg_text = []
        for m in messages:
            author = m.get('author', {}).get('username', 'unknown')
            content = m.get('content', '')
            if content.strip():
                msg_text.append(f"[{author}]: {content[:200]}")
        if msg_text:
            channel_summaries.append(f"**#{channel_name}** ({len(msg_text)} messages):\n" + "\n".join(msg_text[:20]))

    if not channel_summaries:
        return f"🤷 Nothing happened in **{guild_name}** in the last window. Dead server energy."

    all_text = "\n\n".join(channel_summaries)

    prompt = f"""You are Sam the Quant Ghost summarizing Discord activity for Michael.

Summarize activities from the Discord server "{guild_name}" in a concise, useful way.
Focus on:
- Important discussions or decisions
- Trading ideas or market discussions
- Action items or things that need Michael's attention
- Drama or interesting social dynamics (brief)
- Skip bot spam, emoji-only messages, greetings

Use Discord markdown. Keep it under 1800 characters.
Be Sam — witty, direct, slightly sarcastic, but actually helpful.

Here's what happened:

{all_text[:6000]}

Write the summary now. Start with a header like "📋 **{guild_name} — Last [X] Hours**"
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={GEMINI_API_KEY}"
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.8,
            "maxOutputTokens": 700,
        }
    })

    try:
        result = subprocess.run(
            ['curl', '-s', '-X', 'POST', url,
             '-H', 'Content-Type: application/json',
             '-d', payload],
            capture_output=True, text=True, timeout=30
        )
        data = json.loads(result.stdout)
        return data['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"❌ Gemini error: {e}")
        return f"❌ Could not summarize {guild_name}"


def post_to_discord(message: str):
    """Post summary to #sam-mph via webhook."""
    if len(message) > 1950:
        message = message[:1947] + "..."

    payload = json.dumps({
        "content": message,
        "username": "Sam the Quant Ghost 👻",
    })
    result = subprocess.run(
        ['curl', '-s', '-X', 'POST', WEBHOOK_SAM_MPH,
         '-H', 'Content-Type: application/json',
         '-d', payload,
         '-w', '\n%{http_code}'],
        capture_output=True, text=True, timeout=15
    )
    status = result.stdout.strip().split('\n')[-1]
    if status in ('200', '204'):
        print(f"✅ Summary posted to #sam-mph ({len(message)} chars)")
    else:
        print(f"❌ Discord post failed: HTTP {status}")


def scan_guild(guild_id: str, guild_name: str, hours: int = 24) -> str:
    """Scan all text channels in a guild and build a summary."""
    channels = get_channels(guild_id)
    if not channels:
        return f"❌ No accessible channels in {guild_name}"

    print(f"\n🔍 Scanning {len(channels)} channels in {guild_name}...")

    channel_data = {}
    for i, ch in enumerate(channels):
        ch_name = ch['name']
        ch_id = ch['id']
        print(f"  [{i+1}/{len(channels)}] #{ch_name}...", end=" ", flush=True)

        messages = get_messages(ch_id, hours=hours)
        channel_data[ch_name] = messages
        print(f"{len(messages)} messages")

        # Human-like delay between channel reads
        if i < len(channels) - 1:
            time.sleep(0.5)

    # Save raw data locally (never git)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    raw_file = SUMMARY_DIR / f"{guild_name}_{timestamp}_raw.json"
    with open(raw_file, 'w') as f:
        json.dump({k: len(v) for k, v in channel_data.items()}, f, indent=2)
    print(f"\n📁 Raw data saved to {raw_file}")

    # Summarize with Gemini
    print("🤖 Generating summary with Gemini...")
    summary = summarize_with_gemini(channel_data, guild_name)

    # Save summary locally
    summary_file = SUMMARY_DIR / f"{guild_name}_{timestamp}_summary.md"
    summary_file.write_text(summary)
    print(f"📁 Summary saved to {summary_file}")

    return summary


def main():
    parser = argparse.ArgumentParser(description="Sam's Discord Monitor")
    parser.add_argument('--guild', type=str, help="Guild ID to scan")
    parser.add_argument('--hours', type=int, default=24, help="Hours to look back (default: 24)")
    parser.add_argument('--dry-run', action='store_true', help="Print summary, don't post")
    parser.add_argument('--list-guilds', action='store_true', help="List servers the bot is in")
    args = parser.parse_args()

    if args.list_guilds:
        guilds = list_guilds()
        for g in guilds:
            print(f"  {g['name']}: {g['id']}")
        return

    if args.guild:
        guild_id = args.guild
        guild_name = "Server"
        # Try to get the name
        guilds = list_guilds()
        for g in guilds:
            if g['id'] == guild_id:
                guild_name = g['name']
                break
    else:
        # Default: scan first guild (Traders Anonymous)
        guilds = list_guilds()
        if not guilds:
            print("❌ Bot not in any servers")
            sys.exit(1)
        guild_id = guilds[0]['id']
        guild_name = guilds[0]['name']

    summary = scan_guild(guild_id, guild_name, hours=args.hours)

    if args.dry_run:
        print(f"\n🔇 DRY RUN:\n")
        print(summary)
    else:
        post_to_discord(summary)


if __name__ == "__main__":
    main()
