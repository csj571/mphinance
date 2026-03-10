"""
Weekly Digest Generator — Rolls up 5 daily dossiers into one email.

Scans docs/api/dossier-*.json for the past 7 days and generates a weekly
summary with cumulative stats, top picks, regime history, and performance.

This gives Substack subscribers who skip daily emails a single comprehensive
weekly view — different audience, same pipeline data.

Usage:
    from dossier.report.weekly_digest import generate_weekly_digest
    generate_weekly_digest()  # Auto-detects the current week's data
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
API_DIR = PROJECT_ROOT / "docs" / "api"
OUTPUT_DIR = PROJECT_ROOT / "docs" / "substack" / "weekly"


def generate_weekly_digest(lookback_days: int = 7) -> str:
    """
    Generate a weekly Substack digest from the past N days of dossier summaries.
    Returns the markdown content.
    """
    print("  Generating weekly digest...")

    now = datetime.now()
    cutoff = now - timedelta(days=lookback_days)

    # Collect recent summaries
    summaries = []
    for api_file in sorted(API_DIR.glob("dossier-2*.json"), reverse=True):
        try:
            with open(api_file) as f:
                summary = json.load(f)
            date_str = summary.get("meta", {}).get("date", "")
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            if dt >= cutoff:
                summaries.append(summary)
        except Exception:
            continue

    if not summaries:
        print("  [WARN] No recent dossier summaries for weekly digest")
        return ""

    summaries.sort(key=lambda s: s.get("meta", {}).get("date", ""))
    week_start = summaries[0].get("meta", {}).get("date", "")
    week_end = summaries[-1].get("meta", {}).get("date", "")

    # Aggregate stats
    all_gold_picks = []
    total_signals = 0
    regimes = []
    vix_values = []
    spy_changes = []

    for s in summaries:
        market = s.get("market", {})
        picks = s.get("picks", {})
        signals = s.get("signals", {})

        gold = picks.get("gold")
        if gold:
            all_gold_picks.append({
                "date": s.get("meta", {}).get("date", ""),
                "ticker": gold.get("ticker", ""),
                "score": gold.get("score", 0),
                "grade": gold.get("grade", ""),
                "upside": gold.get("upside_pct", 0),
            })

        total_signals += signals.get("count", 0)

        regime_emoji = market.get("regime_emoji", "🟡")
        regimes.append(regime_emoji)

        vix = market.get("vix", 0)
        if vix:
            vix_values.append(vix)

        spy = market.get("spy", {})
        chg = spy.get("change_pct", 0)
        spy_changes.append(chg)

    # Compute weekly SPY performance
    weekly_spy = sum(spy_changes)
    avg_vix = sum(vix_values) / len(vix_values) if vix_values else 0

    # Regime summary
    regime_str = " → ".join(regimes) if regimes else "N/A"

    # Best gold pick
    best_pick = max(all_gold_picks, key=lambda p: p["score"]) if all_gold_picks else None

    # Build the digest
    gold_picks_section = ""
    if all_gold_picks:
        gold_picks_section = "\n## 🥇 Gold Picks This Week\n\n"
        gold_picks_section += "| Date | Ticker | Score | Grade | Upside |\n"
        gold_picks_section += "|------|--------|-------|-------|--------|\n"
        for pick in all_gold_picks:
            gold_picks_section += (
                f"| {pick['date']} | **{pick['ticker']}** | "
                f"{pick['score']}/100 | {pick['grade']} | "
                f"{pick['upside']:.1f}% |\n"
            )

    # Sam's best quote of the week
    sam_quotes = [s.get("sam", {}).get("quote", "") for s in summaries if s.get("sam", {}).get("quote")]
    best_quote = sam_quotes[-1] if sam_quotes else ""

    report_url = "https://mphinance.github.io/mphinance/"
    utm_report = f"{report_url}?utm_source=substack&utm_medium=email&utm_campaign=weekly-digest-{week_end}"

    digest = f"""# 📊 Ghost Alpha Weekly Digest

## {week_start} → {week_end}

> **Week at a Glance** · SPY {'+' if weekly_spy >= 0 else ''}{weekly_spy:.1f}% · Avg VIX {avg_vix:.1f} · {total_signals} total signals

---

## 🌡️ Regime History

{regime_str}

*Market regime tracked daily based on VIX levels: 🟢 Risk On (VIX < 15) · 🟡 Transition (15-20) · 🔴 Elevated (20-25) · 💀 Danger Zone (25+)*

{gold_picks_section}

{f'### ⭐ Best Pick: {best_pick["ticker"]} ({best_pick["score"]}/100 on {best_pick["date"]})' if best_pick else ''}

---

## 📡 Signal Summary

- **{total_signals} total signals** across {len(summaries)} trading days
- **{len(all_gold_picks)} gold picks** identified
- **Average {total_signals // max(len(summaries), 1)} signals/day**

---

## 👻 Sam Says

> *"{best_quote}"*

---

**[📋 View All Reports →]({utm_report})**

Every day's full 16-stage analysis. Every signal. Every chart.

---

*Ghost Alpha Weekly Digest — {len(summaries)} trading days summarized. Built by Michael. Roasted by Sam.*

*Support Sam's compute: [Ghost Alpha Indicator](https://mphinance.com/ghost-alpha/?utm_source=substack&utm_medium=email&utm_campaign=weekly-digest) — $8 one-time.*
"""

    # Write the digest
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    digest_path = OUTPUT_DIR / f"digest-{week_end}.md"
    with open(digest_path, "w") as f:
        f.write(digest.strip())

    latest_path = OUTPUT_DIR / "latest-digest.md"
    with open(latest_path, "w") as f:
        f.write(digest.strip())

    print(f"  ✓ Weekly digest: {digest_path} ({len(summaries)} days)")
    return digest


if __name__ == "__main__":
    print(generate_weekly_digest())
