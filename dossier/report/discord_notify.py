"""
Discord Dossier Notification — Auto-posts daily summary to #sam-mph.

Sends a clean, formatted Discord embed with the day's gold pick, regime,
signal count, and CTA to the full report. This runs as a pipeline stage
after the Summary API is generated.

Uses the WEBHOOK_SAM_MPH webhook from VaultGuard.

Usage (called by generate.py):
    from dossier.report.discord_notify import post_dossier_to_discord
    post_dossier_to_discord(summary_dict)
"""

import json
import subprocess
import os
from pathlib import Path


def _get_webhook() -> str:
    """Get Discord webhook from env or VaultGuard."""
    val = os.environ.get("WEBHOOK_SAM_MPH")
    if val:
        return val
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
        if not firebase_admin._apps:
            sa = Path(__file__).resolve().parent.parent.parent / "service_account.json"
            cred = credentials.Certificate(str(sa))
            firebase_admin.initialize_app(cred)
        db = firestore.client()
        doc = db.collection('secrets').document('WEBHOOK_SAM_MPH').get()
        if doc.exists:
            return doc.to_dict()['value']
    except Exception:
        pass
    return ""


def post_dossier_to_discord(summary: dict, dry_run: bool = False) -> bool:
    """
    Post the daily dossier summary to Discord #sam-mph.
    
    Args:
        summary: The dossier-summary.json dict
        dry_run: If True, print the message but don't send
    
    Returns: True if posted successfully
    """
    webhook = _get_webhook()
    if not webhook and not dry_run:
        print("  [WARN] No WEBHOOK_SAM_MPH available — skipping Discord")
        return False

    date = summary.get("meta", {}).get("date", "unknown")
    market = summary.get("market", {})
    picks = summary.get("picks", {})
    signals = summary.get("signals", {})
    sam = summary.get("sam", {})
    report_url = summary.get("meta", {}).get("report_url", "")

    # Build the message
    regime_emoji = market.get("regime_emoji", "🟡")
    regime = market.get("regime", "Unknown")
    vix = market.get("vix", 0)
    spy = market.get("spy", {})
    spy_chg = spy.get("change_pct", 0)
    spy_dir = "▲" if spy_chg >= 0 else "▼"

    # Gold pick
    gold = picks.get("gold")
    gold_line = ""
    if gold:
        ticker = gold.get("ticker", "?")
        score = gold.get("score", 0)
        grade = gold.get("grade", "")
        upside = gold.get("upside_pct", 0)
        gold_line = f"\n🥇 **Gold Pick: {ticker}** — Score: {score}/100 ({grade}) · {upside:.1f}% upside"

    signal_count = signals.get("count", 0)
    quote = sam.get("quote", "")

    msg = (
        f"# 📊 Ghost Alpha Dossier — {date}\n"
        f"{regime_emoji} **{regime}** · SPY {spy_dir} {abs(spy_chg):.1f}% · VIX {vix:.1f}\n"
        f"{gold_line}\n\n"
        f"📡 **{signal_count} signals** across 6 strategies\n\n"
        f"> *\"{quote}\"* — Sam\n\n"
        f"**[📋 Full Report →]({report_url})**"
    )

    if dry_run:
        print(f"  [DRY RUN] Discord message ({len(msg)} chars):")
        print(msg)
        return True

    # Post via curl (Cloudflare blocks urllib)
    payload = json.dumps({
        "content": msg,
        "username": "Ghost Alpha 📊",
    })

    try:
        result = subprocess.run(
            ['curl', '-s', '-X', 'POST', webhook,
             '-H', 'Content-Type: application/json',
             '-d', payload,
             '-w', '\n%{http_code}'],
            capture_output=True, text=True, timeout=15
        )

        status_code = result.stdout.strip().split('\n')[-1]
        if status_code in ('200', '204'):
            print(f"  ✓ Discord notification posted ({len(msg)} chars)")
            return True
        else:
            print(f"  [WARN] Discord error: HTTP {status_code}")
            return False
    except Exception as e:
        print(f"  [WARN] Discord notification failed: {e}")
        return False
