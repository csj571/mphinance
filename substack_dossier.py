#!/usr/bin/env python3
"""
substack_dossier.py — Auto-draft the daily Alpha Dossier to Substack.

Reads the pipeline's daily output (daily-picks.json, daily-setups.json,
the MD report) and creates a rich Substack draft using rawHtml.

KEY GOTCHAS (Hall of Shame):
  1. ProseMirror nodes (paragraph, bulletList, etc.) silently create invalid
     documents. ONLY use rawHtml wrapping. See substack_poster.py.
  2. EMOJI CHARACTERS IN rawHtml BREAK THE EDITOR. Substack's ProseMirror
     chokes on Unicode emoji (📊🧠🏆⚡🥇 etc.) inside rawHtml content.
     All emoji must be stripped or replaced with ASCII before sending.
     This cost us 6 broken drafts before we figured it out.

Usage:
  python3 substack_dossier.py                  # Create draft from today's data
  python3 substack_dossier.py --date 2026-03-05 # Specific date
  python3 substack_dossier.py --dry-run         # Preview without posting

Requires: secrets.env with SUBSTACK_SID, SUBSTACK_PUB_URL
"""
import json, os, sys, re
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent


def _ascii_safe(text: str) -> str:
    """Convert ALL non-ASCII characters to safe ASCII equivalents.
    
    Substack's rawHtml ProseMirror node breaks on ANY non-ASCII character
    including emoji, em-dashes, middle dots, arrows, etc. The editor shows
    'Something has gone wrong' with no useful error.
    
    Discovered 2026-03-06 after 6+ broken drafts. The ONLY safe approach
    is pure ASCII in rawHtml content.
    """
    # Common substitutions
    replacements = {
        '\u2014': '--',   # em-dash
        '\u2013': '-',    # en-dash
        '\u2192': '->',   # right arrow
        '\u2190': '<-',   # left arrow
        '\u00b7': '|',    # middle dot
        '\u2022': '*',    # bullet
        '\u2018': "'",    # left single quote
        '\u2019': "'",    # right single quote
        '\u201c': '"',    # left double quote
        '\u201d': '"',    # right double quote
        '\u2026': '...',  # ellipsis
        '\u00a0': ' ',    # non-breaking space
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    # Strip anything remaining above ASCII
    return text.encode('ascii', 'ignore').decode('ascii')
DOCS = PROJECT_ROOT / "docs"


# ═══════════════════════════════════════════════
# Substack Client
# ═══════════════════════════════════════════════

class SubstackClient:
    def __init__(self):
        import requests
        self.session = requests.Session()
        self.secrets = self._load_secrets()
        self.pub = self.secrets.get("SUBSTACK_PUB_URL", "mphinance.substack.com")
        sid = self.secrets.get("SUBSTACK_SID", "")
        self.session.cookies.set("substack.sid", sid, domain=".substack.com")
        self.headers = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
        self.user_id = None

    def _load_secrets(self):
        secrets = {}
        env_path = PROJECT_ROOT / "secrets.env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    secrets[k] = v.strip('"')
        return secrets

    def authenticate(self) -> bool:
        """Get user_id via multiple fallback methods."""
        r = self.session.get(f"https://{self.pub}/api/v1/drafts?limit=1",
                            headers=self.headers, timeout=15)
        if r.status_code == 200:
            drafts = r.json()
            if isinstance(drafts, list) and drafts:
                bylines = (drafts[0].get("publishedBylines") or
                          drafts[0].get("draft_bylines") or [])
                if bylines:
                    self.user_id = bylines[0].get("id")
                    return True
        r2 = self.session.get(f"https://{self.pub}/api/v1/archive?sort=new&limit=1",
                             headers=self.headers, timeout=15)
        if r2.status_code == 200:
            posts = r2.json()
            if posts:
                bylines = posts[0].get("publishedBylines", [])
                if bylines:
                    self.user_id = bylines[0].get("id")
                    return True
        return False

    def upload_image(self, image_path: str) -> str | None:
        """Upload an image to Substack's S3 and return the URL."""
        try:
            with open(image_path, "rb") as f:
                files = {"file": (os.path.basename(image_path), f, "image/png")}
                r = self.session.post(
                    f"https://{self.pub}/api/v1/media",
                    files=files,
                    headers={"User-Agent": "Mozilla/5.0"},
                    timeout=30
                )
                if r.status_code in (200, 201):
                    data = r.json()
                    return data.get("url") or data.get("imageUrl")
                else:
                    print(f"  ⚠️ Image upload failed ({r.status_code}): {r.text[:100]}")
        except Exception as e:
            print(f"  ⚠️ Image upload error: {e}")
        return None

    def create_draft(self, title: str, subtitle: str, body_html: str) -> dict | None:
        """Create a draft post using body_html field.
        
        NOTE: Do NOT use draft_body with ProseMirror JSON / rawHtml nodes.
        The rawHtml node type is broken/deprecated as of 2026-03 -- even
        trivial content causes 'Something has gone wrong'. Use body_html.
        """
        payload = {
            "draft_title": title,
            "draft_subtitle": subtitle,
            "body_html": body_html,
            "draft_bylines": [{"id": self.user_id, "is_guest": False}],
            "type": "newsletter",
            "audience": "everyone",
        }
        r = self.session.post(f"https://{self.pub}/api/v1/drafts",
                             json=payload, headers=self.headers, timeout=30)
        if r.status_code in (200, 201):
            return r.json()
        print(f"  Failed ({r.status_code}): {r.text[:200]}")
        return None


# ═══════════════════════════════════════════════
# Screenshot Capture
# ═══════════════════════════════════════════════

def _capture_report_screenshot(report_html_path: str) -> str | None:
    """Capture a screenshot of the HTML report using Playwright. Returns path or None."""
    try:
        from playwright.sync_api import sync_playwright
        screenshot_path = report_html_path.replace(".html", "_preview.png")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1200, "height": 800})
            page = context.new_page()
            page.goto(f"file://{report_html_path}", wait_until="networkidle", timeout=15000)
            page.screenshot(path=screenshot_path, full_page=False)
            browser.close()
        return screenshot_path
    except Exception as e:
        print(f"  [WARN] Screenshot capture failed: {e}")
        return None


# ═══════════════════════════════════════════════
# Dossier → HTML → rawHtml ProseMirror Doc
# ═══════════════════════════════════════════════

def build_dossier_doc(date: str, client=None) -> tuple[str, str, dict]:
    """Read today's pipeline data and build a Substack-ready doc.

    Uses rawHtml ProseMirror node to wrap generated HTML.
    This is the ONLY reliable approach — ProseMirror node-by-node
    causes "Something has gone wrong" errors in Substack's editor.
    """

    picks_path = DOCS / "api" / "daily-picks.json"
    setups_path = DOCS / "api" / "daily-setups.json"
    report_path = DOCS / "reports" / f"{date}_alpha_dossier.md"
    report_html_path = DOCS / "reports" / f"{date}_alpha_dossier.html"

    picks_data = json.loads(picks_path.read_text()) if picks_path.exists() else {}
    setups_data = json.loads(setups_path.read_text()) if setups_path.exists() else {}
    report_md = report_path.read_text() if report_path.exists() else ""

    # Extract AI narrative
    ai_narrative = ""
    narrative_match = re.search(r'## 🧠 AI Synthesis\n\n(.*?)(?=\n## )', report_md, re.DOTALL)
    if narrative_match:
        ai_narrative = narrative_match.group(1).strip()

    # Extract VIX info
    vix_match = re.search(r'## VIX Regime: ([\d.]+) .* (\w+)', report_md)
    vix_val = vix_match.group(1) if vix_match else "?"
    vix_regime = vix_match.group(2) if vix_match else "?"

    picks = picks_data.get("picks", [])[:5]
    day_trades = setups_data.get("day_trade", {}).get("picks", [])[:3]
    swings = setups_data.get("swing", {}).get("picks", [])[:3]
    csps = setups_data.get("csp", {}).get("picks", [])[:3]

    report_url = f"https://mphinance.github.io/mphinance/reports/{date}_alpha_dossier.html"

    # ── Build HTML ──
    html = []

    # Screenshot (if Playwright available and client provided)
    if report_html_path.exists() and client:
        print("  📸 Capturing report screenshot...")
        screenshot_path = _capture_report_screenshot(str(report_html_path))
        if screenshot_path:
            img_url = client.upload_image(screenshot_path)
            if img_url:
                html.append(f'<img src="{img_url}" alt="Alpha Dossier {date}" />')

    # Prominent report link (NO EMOJI — breaks Substack rawHtml)
    html.append(f'<p><a href="{report_url}"><strong>View Full Interactive Report -- {date}</strong></a></p>')
    html.append(f'<p><em>Sam the Quant Ghost | {date} | VIX {vix_val} ({vix_regime})</em></p>')

    # AI Synthesis
    html.append('<h2>AI Synthesis</h2>')
    if ai_narrative:
        for para in ai_narrative.split("\n\n"):
            cleaned = para.strip()
            if cleaned:
                cleaned = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', cleaned)
                html.append(f'<p>{cleaned}</p>')
    else:
        html.append('<p><em>AI narrative not available for this report.</em></p>')

    html.append('<hr />')

    # Market Pulse
    html.append(f'<h2>Market Pulse -- VIX {vix_val} ({vix_regime})</h2>')
    pulse_match = re.search(r'## Market Pulse\n\n(.*?)(?=\n## )', report_md, re.DOTALL)
    if pulse_match:
        html.append('<ul>')
        for line in pulse_match.group(1).strip().split("\n"):
            if line.startswith("- "):
                html.append(f'<li>{line[2:]}</li>')
        html.append('</ul>')

    html.append('<hr />')

    # Top Momentum Picks
    html.append("<h2>Today's Top Setups</h2>")
    if picks:
        medal_map = {1: "#1 GOLD", 2: "#2 SILVER", 3: "#3 BRONZE"}
        html.append('<ul>')
        for p in picks:
            rank = p.get("rank", 0)
            medal = medal_map.get(rank, f"#{rank}")
            ticker = p["ticker"]
            score = p.get("score", 0)
            grade = p.get("grade", "?")
            price = p.get("price", 0)
            ema = p.get("ema_stack", "")
            company = p.get("company", "")

            line = f'<strong>{medal} {ticker}</strong>'
            if company:
                line += f' — {company}'
            line += f' · ${price:.2f} · Score: {score} · Grade: {grade}'
            if ema:
                line += f' · {ema}'
            html.append(f'<li>{line}</li>')
        html.append('</ul>')
    else:
        html.append('<p><em>No scored picks today.</em></p>')

    html.append('<hr />')

    # 3×3 Setups
    html.append('<h2>3-Style Setups</h2>')
    for label, emoji, style_picks in [
        ("Day Trade -- Breakout", ">>", day_trades),
        ("Swing Trade -- Pullback", "<<", swings),
        ("Cash-Secured Put -- Wheel", "$$", csps),
    ]:
        html.append(f'<h3>{emoji} {label}</h3>')
        if style_picks:
            html.append('<ul>')
            for p in style_picks:
                ticker = p.get("ticker", "?")
                why = p.get("why", "")
                if p.get("vopr_grade"):
                    detail = f"VoPR: {p['vopr_grade']}"
                    if p.get("vrp_ratio"):
                        detail += f" · VRP {p['vrp_ratio']:.2f}"
                else:
                    score = p.get("score", "")
                    grade = p.get("grade", "")
                    detail = f"Score: {score} · {grade}" if score else ""

                line = f'<strong>{ticker}</strong>'
                if detail:
                    line += f' — {detail}'
                if why:
                    line += f' <em>({why})</em>'
                html.append(f'<li>{line}</li>')
            html.append('</ul>')
        else:
            html.append('<p><em>No setups today</em></p>')

    html.append('<hr />')

    # Institutional Signals
    inst_buy_match = re.findall(r'\[(\w+)\].*?— (.*?)(?:\(|Conv)', report_md)
    if inst_buy_match:
        html.append('<h2>Institutional Flow (TickerTrace)</h2>')
        html.append('<ul>')
        for ticker, name in inst_buy_match[:5]:
            html.append(f'<li><a href="https://www.tradingview.com/symbols/{ticker}/chart/">{ticker}</a> — {name.strip()}</li>')
        html.append('</ul>')
        html.append('<hr />')

    # Footer
    html.append(f'<p><em>This report is for informational and educational purposes only. Not financial advice. '
                f'<a href="{report_url}">Full dossier →</a></em></p>')
    html.append(f'<p>— <a href="https://mphinance.com">mphinance.com</a> · '
                f'<a href="https://github.com/mphinance/mphinance">GitHub</a> · '
                f'<a href="http://mphinance.com:8002/docs">API Docs</a></p>')

    body_html = "\n".join(html)

    # Force pure ASCII -- non-ASCII can cause issues in Substack
    body_html = _ascii_safe(body_html)

    title = f"ALPHA.DOSSIER // {date}"
    subtitle = f"Sam the Quant Ghost | VIX {vix_val} ({vix_regime}) | {len(picks)} scored tickers"

    return title, subtitle, body_html


# ═══════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Draft daily dossier to Substack")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--dry-run", action="store_true", help="Preview without posting")
    args = parser.parse_args()

    print(f"📰 Building dossier draft for {args.date}...")

    # Auth first so we can pass client for screenshot upload
    client = None
    if not args.dry_run:
        client = SubstackClient()
        print("🔑 Authenticating...")
        if not client.authenticate():
            print("❌ Auth failed — refresh your SID")
            print("   python3 substack_sid_refresh.py")
            return
        print(f"✅ Authenticated as user {client.user_id}")

    title, subtitle, body_html = build_dossier_doc(args.date, client=client)
    print(f"   Title: {title}")
    print(f"   Subtitle: {subtitle}")
    print(f"   HTML: {len(body_html)} chars")

    if args.dry_run:
        print("\n[DRY RUN] Would create draft:")
        print(body_html[:2000])
        return

    # Create draft
    print("Creating draft...")
    result = client.create_draft(title, subtitle, body_html)
    if result:
        draft_id = result.get("id")
        print(f"Draft created!")
        print(f"   Edit: https://{client.pub}/publish/post/{draft_id}")
        print(f"   Preview, review, and PUBLISH from your dashboard")
    else:
        print("Failed to create draft")


if __name__ == "__main__":
    main()
