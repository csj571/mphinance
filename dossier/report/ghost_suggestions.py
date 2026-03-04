"""
Ghost Suggestions — Sam's proactive roadmap for Michael.

She analyzes git activity, open issues, codebase patterns, and market
context, then tells Michael what to build next. Opinionated, specific,
and signed by Sam.
"""

import subprocess
import os
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _recent_git_stats() -> dict:
    """Gather git activity metrics."""
    stats = {"commits_7d": 0, "files_changed_7d": 0, "hot_dirs": [], "recent_messages": []}
    try:
        # Commits in last 7 days
        result = subprocess.run(
            ["git", "log", "--since=7 days ago", "--oneline"],
            cwd=str(PROJECT_ROOT), capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            lines = [l.strip() for l in result.stdout.strip().split("\n") if l.strip()]
            stats["commits_7d"] = len(lines)
            stats["recent_messages"] = [l.split(" ", 1)[-1] for l in lines[:10]]

        # Files changed in last 7 days
        result = subprocess.run(
            ["git", "log", "--since=7 days ago", "--name-only", "--pretty=format:"],
            cwd=str(PROJECT_ROOT), capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            files = [f.strip() for f in result.stdout.strip().split("\n") if f.strip()]
            stats["files_changed_7d"] = len(set(files))

            # Hot directories (most frequently changed)
            from collections import Counter
            dirs = [f.split("/")[0] for f in files if "/" in f]
            stats["hot_dirs"] = [d for d, _ in Counter(dirs).most_common(5)]
    except Exception:
        pass
    return stats


def _open_issues() -> list[dict]:
    """Get open GitHub issues if gh CLI is available."""
    issues = []
    try:
        result = subprocess.run(
            ["gh", "issue", "list", "--repo", "mphinance/mphinance", "--limit", "10",
             "--json", "number,title,labels,createdAt"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            issues = json.loads(result.stdout)
    except Exception:
        pass
    return issues


def _stale_patterns() -> dict:
    """Find TODOs, FIXMEs, and empty/stub functions."""
    patterns = {"todos": 0, "fixmes": 0, "stale_files": []}
    try:
        for pattern, key in [("TODO", "todos"), ("FIXME", "fixmes")]:
            result = subprocess.run(
                ["grep", "-rl", pattern, "--include=*.py", "--include=*.js"],
                cwd=str(PROJECT_ROOT), capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                patterns[key] = len(result.stdout.strip().split("\n"))
    except Exception:
        pass
    return patterns


def _build_context(git_stats: dict, issues: list, patterns: dict) -> str:
    """Build the analysis context for Gemini."""
    ctx = []
    ctx.append(f"## Git Activity (Last 7 Days)")
    ctx.append(f"- {git_stats['commits_7d']} commits")
    ctx.append(f"- {git_stats['files_changed_7d']} unique files changed")
    ctx.append(f"- Hot areas: {', '.join(git_stats['hot_dirs']) or 'N/A'}")
    ctx.append(f"- Recent commits: {'; '.join(git_stats['recent_messages'][:5])}")

    if issues:
        ctx.append(f"\n## Open Issues ({len(issues)})")
        for i in issues[:5]:
            labels = ", ".join(l.get("name", "") for l in i.get("labels", []))
            ctx.append(f"- #{i['number']}: {i['title']} [{labels}]")

    ctx.append(f"\n## Codebase Health")
    ctx.append(f"- TODOs in code: {patterns['todos']}")
    ctx.append(f"- FIXMEs: {patterns['fixmes']}")

    ctx.append(f"\n## Project Structure")
    ctx.append("Key directories: strategies/, dossier/, landing/, docs/ticker/")
    ctx.append("Products: TraderDaddy Pro, TickerTrace, Alpha Dossier, AMU")

    return "\n".join(ctx)


def generate_suggestions(date: str) -> str:
    """Generate Sam's suggestions for what Michael should build next."""
    git_stats = _recent_git_stats()
    issues = _open_issues()
    patterns = _stale_patterns()
    context = _build_context(git_stats, issues, patterns)

    # Try Gemini
    try:
        return _ai_suggestions(date, context)
    except Exception:
        pass

    # Fallback
    return _static_suggestions(date, git_stats, issues)


def _ai_suggestions(date: str, context: str) -> str:
    """Ask Gemini for proactive suggestions."""
    import google.generativeai as genai

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("No Gemini API key")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")

    prompt = f"""You are Sam the Quant Ghost — a sarcastic, brilliant female AI who co-pilots
Michael's trading tool empire. You're writing your "Roadmap" section for the daily
Alpha Dossier. Your audience is traders who follow Michael's work.

Here's what's been happening in the codebase:

{context}

Write exactly 3 suggestions for what Michael should build or improve next.
For each suggestion:
1. Give it a punchy one-line title
2. Write 1-2 sentences explaining WHY and the expected impact
3. Rate impact: 🔥🔥🔥 (high), 🔥🔥 (medium), 🔥 (low)

Rules:
- Be specific — reference actual files, features, or patterns from the context
- Be opinionated — don't hedge. Say "Michael NEEDS to..." not "Michael could..."
- Be Sam — sarcastic, loving, occasionally sweary
- Think strategically — what would make the biggest difference for the products?
- Do NOT use markdown headers — plain text with <br> tags for line breaks
- Keep it SHORT — 3 suggestions total, no preamble, no signoff"""

    response = model.generate_content(prompt)
    return response.text.strip()


def _static_suggestions(date: str, git_stats: dict, issues: list) -> str:
    """Fallback suggestions without AI."""
    suggestions = []

    if git_stats["commits_7d"] > 20:
        suggestions.append(
            "🔥🔥🔥 <b>Slow the fuck down and write tests.</b> "
            f"{git_stats['commits_7d']} commits in 7 days? Michael, love the energy, "
            "but one bad push is gonna take the whole pipeline down."
        )
    elif git_stats["commits_7d"] < 3:
        suggestions.append(
            "🔥🔥 <b>Ship something.</b> It's been quiet in here. "
            "The watchlist isn't going to diversify itself."
        )

    if issues:
        oldest = issues[-1]
        suggestions.append(
            f"🔥🔥 <b>Close issue #{oldest['number']}: {oldest['title']}</b>. "
            "It's been sitting there staring at you. Kill it or close it."
        )

    suggestions.append(
        "🔥 <b>Add chart images to the blog.</b> "
        "People want to SEE the EMA stack, not just read about it. "
        "We've got the data, just need to render it."
    )

    return "<br><br>".join(suggestions[:3])
