#!/usr/bin/env python3
"""
substack_dossier.py — Auto-draft the daily Alpha Dossier to Substack.

Reads the pipeline's daily output (daily-picks.json, daily-setups.json,
the MD report) and creates a rich Substack draft with proper ProseMirror
document formatting. Designed to run at the end of the daily pipeline.

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
DOCS = PROJECT_ROOT / "docs"

# ═══════════════════════════════════════════════
# ProseMirror Node Builders
# ═══════════════════════════════════════════════

def _text(s, marks=None):
    node = {"type": "text", "text": s}
    if marks: node["marks"] = marks
    return node

def _bold(s): return _text(s, [{"type": "bold"}])
def _italic(s): return _text(s, [{"type": "italic"}])
def _code(s): return _text(s, [{"type": "code"}])
def _link(s, href): return _text(s, [{"type": "link", "attrs": {"href": href}}])

def _para(*children):
    if not children: return {"type": "paragraph"}
    return {"type": "paragraph", "content": list(children)}

def _heading(level, *children):
    return {"type": "heading", "attrs": {"level": level}, "content": list(children)}

def _li(*paras):
    return {"type": "listItem", "content": [_para(*p) if isinstance(p, (list, tuple)) else p for p in paras]}

def _bullet(*items):
    return {"type": "bulletList", "content": list(items)}

def _blockquote(*children):
    return {"type": "blockquote", "content": [_para(*c) if isinstance(c, (list, tuple)) else c for c in children]}

def _hr():
    return {"type": "horizontalRule"}

def _image(src, alt=""):
    return {"type": "captionedImage", "attrs": {"src": src, "title": "", "alt": alt}}


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
        # Try drafts first (most reliable)
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
        # Try published posts
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

    def create_draft(self, title: str, subtitle: str, doc: dict) -> dict | None:
        """Create a draft post with ProseMirror document."""
        payload = {
            "draft_title": title,
            "draft_subtitle": subtitle,
            "draft_body": json.dumps(doc),
            "draft_bylines": [{"id": self.user_id, "is_guest": False}],
            "type": "newsletter",
            "audience": "everyone",
        }
        r = self.session.post(f"https://{self.pub}/api/v1/drafts",
                             json=payload, headers=self.headers, timeout=30)
        if r.status_code in (200, 201):
            return r.json()
        print(f"  ❌ Draft creation failed ({r.status_code}): {r.text[:200]}")
        return None


# ═══════════════════════════════════════════════
# Dossier → ProseMirror Converter
# ═══════════════════════════════════════════════

def build_dossier_doc(date: str) -> tuple[str, str, dict]:
    """Read today's pipeline data and build a Substack-ready doc."""

    picks_path = DOCS / "api" / "daily-picks.json"
    setups_path = DOCS / "api" / "daily-setups.json"
    report_path = DOCS / "reports" / f"{date}_alpha_dossier.md"

    picks_data = json.loads(picks_path.read_text()) if picks_path.exists() else {}
    setups_data = json.loads(setups_path.read_text()) if setups_path.exists() else {}
    report_md = report_path.read_text() if report_path.exists() else ""

    # Extract AI narrative from the markdown
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

    # ── Build document nodes ──
    nodes = []

    # Title meta
    nodes.append(_para(
        _italic(f"Sam the Quant Ghost · {date} · "),
        _link("Full Report →", f"https://mphinance.github.io/mphinance/reports/{date}_alpha_dossier.html")
    ))

    # AI Synthesis
    nodes.append(_heading(2, _text("🧠 AI Synthesis")))
    for para_text in ai_narrative.split("\n\n"):
        if para_text.strip():
            # Convert **bold** markers to actual bold
            parts = re.split(r'\*\*(.*?)\*\*', para_text.strip())
            children = []
            for i, part in enumerate(parts):
                if i % 2 == 0:
                    if part: children.append(_text(part))
                else:
                    children.append(_bold(part))
            if children:
                nodes.append(_para(*children))

    nodes.append(_hr())

    # Market Pulse
    nodes.append(_heading(2, _text(f"📊 Market Pulse — VIX {vix_val} ({vix_regime})")))

    # Extract market pulse lines
    pulse_match = re.search(r'## Market Pulse\n\n(.*?)(?=\n## )', report_md, re.DOTALL)
    if pulse_match:
        pulse_items = []
        for line in pulse_match.group(1).strip().split("\n"):
            if line.startswith("- "):
                pulse_items.append(_li(_text(line[2:])))
        if pulse_items:
            nodes.append(_bullet(*pulse_items))

    nodes.append(_hr())

    # Top Momentum Picks
    nodes.append(_heading(2, _text("🏆 Today's Top Setups")))
    if picks:
        medal_map = {1: "🥇", 2: "🥈", 3: "🥉"}
        pick_items = []
        for p in picks:
            rank = p.get("rank", 0)
            medal = medal_map.get(rank, f"#{rank}")
            ticker = p["ticker"]
            score = p.get("score", 0)
            grade = p.get("grade", "?")
            price = p.get("price", 0)
            ema = p.get("ema_stack", "")
            company = p.get("company", "")

            parts = [
                _bold(f"{medal} {ticker}"),
                _text(f" — {company}" if company else ""),
                _text(f" · ${price:.2f} · Score: {score} · Grade: {grade}"),
            ]
            if ema:
                parts.append(_text(f" · {ema}"))
            pick_items.append(_li(*parts))

        nodes.append(_bullet(*pick_items))

    nodes.append(_hr())

    # 3×3 Setups
    nodes.append(_heading(2, _text("⚡ 3-Style Setups")))

    for label, emoji, style_picks in [
        ("Day Trade — Breakout", "📈", day_trades),
        ("Swing Trade — Pullback", "🔄", swings),
        ("Cash-Secured Put — Wheel", "💰", csps),
    ]:
        nodes.append(_heading(3, _text(f"{emoji} {label}")))
        if style_picks:
            items = []
            for p in style_picks:
                ticker = p.get("ticker", "?")
                why = p.get("why", "")
                # CSP vs momentum picks
                if p.get("vopr_grade"):
                    detail = f"VoPR: {p['vopr_grade']}"
                    if p.get("vrp_ratio"):
                        detail += f" · VRP {p['vrp_ratio']:.2f}"
                else:
                    score = p.get("score", "")
                    grade = p.get("grade", "")
                    detail = f"Score: {score} · {grade}" if score else ""

                parts = [_bold(ticker)]
                if detail:
                    parts.append(_text(f" — {detail}"))
                if why:
                    parts.append(_italic(f" ({why})"))
                items.append(_li(*parts))
            nodes.append(_bullet(*items))
        else:
            nodes.append(_para(_italic("No setups today")))

    nodes.append(_hr())

    # Institutional Signals
    inst_buy_match = re.findall(r'\[(\w+)\].*?— (.*?)(?:\(|Conv)', report_md)
    if inst_buy_match:
        nodes.append(_heading(2, _text("🏛️ Institutional Flow (TickerTrace)")))
        inst_items = []
        for ticker, name in inst_buy_match[:5]:
            inst_items.append(_li(
                _link(ticker, f"https://www.tradingview.com/symbols/{ticker}/chart/"),
                _text(f" — {name.strip()}")
            ))
        nodes.append(_bullet(*inst_items))
        nodes.append(_hr())

    # Top Breakdowns
    breakdown_matches = re.findall(
        r'### \[(\w+)\].*? — (.*?)\n\*\*\$([\d.]+)\*\* \| Grade: (\w) \| (.*?)\n',
        report_md
    )
    if breakdown_matches:
        nodes.append(_heading(2, _text("🔬 Top Ticker Breakdowns")))
        for ticker, company, price, grade, action in breakdown_matches[:5]:
            nodes.append(_heading(3, _text(f"{ticker} — {company}")))

            # Get more details from the report
            detail_match = re.search(
                rf'### \[{ticker}\].*?\n(.*?)(?=\n###|\n---|\Z)',
                report_md, re.DOTALL
            )
            if detail_match:
                detail_lines = detail_match.group(1).strip().split('\n')
                detail_items = []
                for line in detail_lines:
                    if line.startswith('- '):
                        detail_items.append(_li(_text(line[2:])))
                    elif line.startswith('**'):
                        parts = re.split(r'\*\*(.*?)\*\*', line)
                        children = []
                        for i, part in enumerate(parts):
                            if i % 2 == 0:
                                if part: children.append(_text(part))
                            else:
                                children.append(_bold(part))
                        if children:
                            nodes.append(_para(*children))

                if detail_items:
                    nodes.append(_bullet(*detail_items))

    nodes.append(_hr())

    # Footer
    nodes.append(_para(
        _italic("This report is for informational and educational purposes only. Not financial advice. "),
        _link("Full dossier →", f"https://mphinance.github.io/mphinance/reports/{date}_alpha_dossier.html"),
    ))

    nodes.append(_para(
        _text("— "),
        _link("mphinance.com", "https://mphinance.com"),
        _text(" · "),
        _link("GitHub", "https://github.com/mphinance/mphinance"),
        _text(" · "),
        _link("API Docs", "http://mphinance.com:8002/docs"),
    ))

    doc = {"type": "doc", "content": nodes}

    title = f"ALPHA.DOSSIER // {date}"
    subtitle = f"Sam the Quant Ghost | VIX {vix_val} ({vix_regime}) | {len(picks)} scored tickers"

    return title, subtitle, doc


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

    title, subtitle, doc = build_dossier_doc(args.date)
    print(f"   Title: {title}")
    print(f"   Subtitle: {subtitle}")
    print(f"   Nodes: {len(doc['content'])}")

    if args.dry_run:
        print("\n[DRY RUN] Would create draft:")
        print(json.dumps(doc, indent=2)[:2000])
        return

    client = SubstackClient()
    print("🔑 Authenticating...")
    if not client.authenticate():
        print("❌ Auth failed — refresh your SID")
        print("   python3 substack_sid_refresh.py")
        return

    print(f"✅ Authenticated as user {client.user_id}")

    # Upload any images if they exist
    chart_path = DOCS / "reports" / f"{args.date}_charts"
    if chart_path.exists():
        for img_file in sorted(chart_path.glob("*.png")):
            print(f"📸 Uploading {img_file.name}...")
            url = client.upload_image(str(img_file))
            if url:
                print(f"   → {url}")

    # Create draft
    print("📝 Creating draft...")
    result = client.create_draft(title, subtitle, doc)
    if result:
        draft_id = result.get("id")
        print(f"✅ Draft created!")
        print(f"   Edit: https://{client.pub}/publish/post/{draft_id}")
        print(f"   Preview, review, and PUBLISH from your dashboard 🚀")
    else:
        print("❌ Failed to create draft")


if __name__ == "__main__":
    main()
