"""
Substack Teaser Generator — Turns the Summary API into subscriber-facing content.

Reads docs/api/dossier-summary.json and generates a polished Substack-ready
teaser email in docs/substack/dossier/teaser-{date}.md

This is the bridge between "pipeline generated data" and "subscriber revenue."

Usage (called by generate.py or manually):
    from dossier.report.substack_teaser import generate_teaser
    generate_teaser()  # reads latest summary API, writes teaser markdown
"""

import json
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
API_PATH = PROJECT_ROOT / "docs" / "api" / "dossier-summary.json"
TEASER_DIR = PROJECT_ROOT / "docs" / "substack" / "dossier"


def generate_teaser(summary: dict = None) -> str:
    """
    Generate a Substack teaser from the dossier summary.
    Returns the markdown and writes to docs/substack/dossier/.
    """
    if summary is None:
        if not API_PATH.exists():
            print("  [WARN] No dossier-summary.json found — skipping teaser")
            return ""
        with open(API_PATH) as f:
            summary = json.load(f)

    date = summary.get("meta", {}).get("date", datetime.now().strftime("%Y-%m-%d"))
    market = summary.get("market", {})
    picks = summary.get("picks", {})
    signals = summary.get("signals", {})
    sam = summary.get("sam", {})
    narrative = summary.get("narrative", {})
    report_url_base = summary.get("meta", {}).get("report_url", "https://mphinance.github.io/mphinance/")
    report_url = f"{report_url_base}?utm_source=substack&utm_medium=email&utm_campaign=dossier-{date}"

    # ── Build the teaser ──
    regime_map = {
        "🟢": "Risk On", "🟡": "Transition", "🔴": "Elevated", "💀": "Danger Zone"
    }
    regime_emoji = market.get("regime_emoji", "🟡")
    regime_label = regime_map.get(regime_emoji, market.get("regime", "Unknown"))

    spy_chg = market.get("spy", {}).get("change_pct", 0)
    spy_dir = "▲" if spy_chg >= 0 else "▼"
    vix = market.get("vix", 0)

    # Gold pick section
    gold = picks.get("gold")
    gold_section = ""
    if gold:
        ticker = gold.get("ticker", "")
        score = gold.get("score", 0)
        grade = gold.get("grade", "")
        upside = gold.get("upside_pct", 0)
        entry = gold.get("entry", 0)
        target = gold.get("target", 0)
        stop = gold.get("stop", 0)

        gold_section = f"""
## 🥇 Gold Pick: {ticker}

| Metric | Value |
|--------|-------|
| **Score** | {score}/100 ({grade}) |
| **Entry** | ${entry:.2f} |
| **Target** | ${target:.2f} ({upside:.1f}% upside) |
| **Stop** | ${stop:.2f} |

*This is the highest-scoring setup from today's 16-stage analysis pipeline.*
"""

    # Silver & Bronze mentions
    runners_up = ""
    silver = picks.get("silver")
    bronze = picks.get("bronze")
    if silver or bronze:
        runners_up = "\n### Runners Up\n"
        if silver:
            runners_up += f"- 🥈 **{silver['ticker']}** — Score: {silver.get('score', 0)}/100\n"
        if bronze:
            runners_up += f"- 🥉 **{bronze['ticker']}** — Score: {bronze.get('score', 0)}/100\n"

    # Signal summary
    signal_count = signals.get("count", 0)
    grades = signals.get("grade_distribution", {})
    grade_str = ", ".join(f"{g}: {c}" for g, c in sorted(grades.items())) if grades else "none"

    # Sam's quote
    quote = sam.get("quote", "")

    # Compose the teaser
    teaser = f"""# Ghost Alpha Dossier — {date}

> {regime_emoji} **{regime_label}** · SPY {spy_dir} {abs(spy_chg):.1f}% · VIX {vix:.1f}

---

{narrative.get('one_liner', 'Your daily dose of institutional-grade market intelligence.')}

{gold_section}
{runners_up}

## 📊 Today's Numbers

- **{signal_count} scanner signals** across 6 strategies
- **Grade distribution:** {grade_str}
- **SPY:** {spy_dir} {abs(spy_chg):.1f}% | **VIX:** {vix:.1f}

---

## 👻 Sam Says

> *"{quote}"*

---

**[📋 Read the Full Dossier →]({report_url})**

Every section. Every chart. Every signal. The full 16-stage analysis.

---

*Ghost Alpha Dossier is generated daily at 5AM CST by a 16-stage pipeline that scans the entire market. Built by Michael. Roasted by Sam.*

*Support Sam's compute: [Ghost Alpha Indicator](https://mphinance.com/ghost-alpha/?utm_source=substack&utm_medium=email&utm_campaign=ghost-alpha) — $8 one-time.*
"""

    # Write the teaser
    TEASER_DIR.mkdir(parents=True, exist_ok=True)
    teaser_path = TEASER_DIR / f"teaser-{date}.md"
    with open(teaser_path, "w") as f:
        f.write(teaser.strip())

    # Also write as latest teaser
    latest_path = TEASER_DIR / "latest-teaser.md"
    with open(latest_path, "w") as f:
        f.write(teaser.strip())

    print(f"  ✓ Substack teaser: {teaser_path}")
    return teaser


if __name__ == "__main__":
    print(generate_teaser())
