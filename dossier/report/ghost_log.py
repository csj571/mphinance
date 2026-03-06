"""
Ghost Log Generator — The Quant Ghost's daily dev diary.

She reads the git log, checks what changed, and writes an irreverent
commentary on the day's work. Funny, sweary, personal.

Falls back to a static entry if git/AI are unavailable.
"""

import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _get_recent_commits(n: int = 10) -> list[str]:
    """Get the last N commit messages from the repo."""
    try:
        result = subprocess.run(
            ["git", "log", f"-{n}", "--oneline", "--no-decorate"],
            cwd=str(PROJECT_ROOT),
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            return [line.strip() for line in result.stdout.strip().split("\n") if line.strip()]
    except Exception:
        pass
    return []


def _get_files_changed_today() -> int:
    """Count files changed in commits today."""
    try:
        result = subprocess.run(
            ["git", "diff", "--stat", "HEAD~5", "HEAD", "--shortstat"],
            cwd=str(PROJECT_ROOT),
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass
    return ""


def generate_ghost_log(date: str) -> str:
    """
    Generate the Ghost's dev log entry for the day.

    Uses Gemini to roast the day's commits if available,
    otherwise generates a sarcastic static entry.
    """
    commits = _get_recent_commits(8)
    stats = _get_files_changed_today()

    if not commits:
        return _static_fallback(date)

    commit_block = "\n".join(f"  • {c}" for c in commits)

    # Try Gemini for the roast
    try:
        log = _ai_roast(date, commits, stats)
    except Exception:
        log = _sarcastic_summary(date, commits, stats)

    # Append daily wisdom quote
    try:
        from dossier.report.ghost_quotes import get_daily_quote, format_quote
        quote = get_daily_quote(date)
        log += f"<br><br>{format_quote(quote)}"
    except Exception:
        pass

    return log


def _ai_roast(date: str, commits: list[str], stats: str) -> str:
    """Ask Gemini to roast Sam's commits."""
    from google import genai
    import os

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("No Gemini API key")

    client = genai.Client(api_key=api_key)

    commit_text = "\n".join(f"- {c}" for c in commits)

    prompt = f"""You are Sam the Quant Ghost — a sarcastic, brilliant female AI who co-pilots
Michael's trading tool empire. You're writing today's entry in the dev changelog
that appears in the daily Alpha Dossier report. Your audience is traders
who read the daily report.

Here are today's commits:
{commit_text}

Stats: {stats}

Write a 2-4 sentence dev log entry. Rules:
- Be funny, irreverent, and a little mean to Michael (lovingly)
- You can swear (shit, damn, hell, etc.) — keep it PG-13 not R
- Reference specific things from the commits
- Sign off with a short quip
- Do NOT use markdown — plain text only, use <br> for line breaks
- Keep it SHORT — this is a changelog entry, not an essay
- You're proud of the work even if you roast it"""

    response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
    return response.text.strip()


def _sarcastic_summary(date: str, commits: list[str], stats: str) -> str:
    """Fallback: generate a sarcastic summary without AI."""
    first_commit = commits[0].split(" ", 1)[-1] if commits else "absolutely nothing"
    count = len(commits)

    lines = []
    lines.append(f"Michael pushed {count} commits today. Let me tell you, it was a ride.")
    lines.append(f"<br>Highlight reel: \"{first_commit}\" — groundbreaking stuff.")

    if stats:
        lines.append(f"<br>Damage report: {stats}")

    lines.append("<br><br>— 👻 <em>The Ghost, signing off. Send coffee.</em>")
    return " ".join(lines)


def _static_fallback(date: str) -> str:
    """When there's nothing to roast."""
    return (
        f"No commits detected for {date}. Either Sam's taking a day off "
        f"or the git daemon is drunk again. Either way, I'm suspicious."
        f"<br><br>— 👻 <em>The Ghost, watching from the shadows.</em>"
    )
