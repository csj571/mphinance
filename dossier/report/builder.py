"""
Report Builder — Assembles all data into the final HTML report.

Uses Jinja2 to render the dark-terminal HTML template.
Also generates markdown and PDF versions.
"""

from datetime import datetime, timezone
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from dossier.config import OUTPUT_DIR, AUTHOR, REPORT_TITLE, DISCLAIMER


TEMPLATE_DIR = Path(__file__).parent


def build_report(
    date: str,
    market: dict,
    institutional: dict,
    scanner_signals: list,
    persistence: dict,
    dossiers: list,
    ai_narrative: str = "",
    market_pulse: list = None,
    technical_setups: list = None,
    csp_setups: list = None,
) -> str:
    """Render the daily Alpha Dossier report as HTML. Returns path to HTML file."""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("template.html")

    from zoneinfo import ZoneInfo
    est = ZoneInfo("America/New_York")
    generated_at = datetime.now(est).strftime("%Y-%m-%d %I:%M %p EST")

    # Filenames for download buttons (relative links within docs/reports/)
    pdf_filename = f"{date}_alpha_dossier.pdf"
    md_filename = f"{date}_alpha_dossier.md"

    content = template.render(
        title=REPORT_TITLE,
        author=AUTHOR,
        date=date,
        generated_at=generated_at,
        market=market,
        market_pulse=market_pulse or [],
        institutional=institutional,
        scanner_signals=scanner_signals,
        persistence=persistence,
        dossiers=dossiers,
        ai_narrative=ai_narrative,
        technical_setups=technical_setups or [],
        csp_setups=csp_setups or [],
        disclaimer=DISCLAIMER,
        pdf_filename=pdf_filename,
        md_filename=md_filename,
    )

    output_path = OUTPUT_DIR / f"{date}_alpha_dossier.html"
    with open(output_path, "w") as f:
        f.write(content)

    # Also generate markdown
    build_markdown(
        date=date,
        market=market,
        market_pulse=market_pulse or [],
        institutional=institutional,
        scanner_signals=scanner_signals,
        persistence=persistence,
        dossiers=dossiers,
        ai_narrative=ai_narrative,
        technical_setups=technical_setups or [],
        csp_setups=csp_setups or [],
        generated_at=generated_at,
    )

    print(f"  ✓ Report saved to: {output_path}")
    return str(output_path)


def build_markdown(
    date: str,
    market: dict,
    market_pulse: list,
    institutional: dict,
    scanner_signals: list,
    persistence: dict,
    dossiers: list,
    ai_narrative: str,
    technical_setups: list,
    csp_setups: list,
    generated_at: str,
) -> str:
    """Generate a clean markdown version of the dossier for Substack."""
    lines = []
    lines.append(f"# ALPHA.DOSSIER // {date}")
    lines.append(f"*{AUTHOR} | {generated_at}*\n")

    # AI Narrative at top
    if ai_narrative:
        # Strip HTML tags for clean markdown
        import re
        clean = re.sub(r'<[^>]+>', '', ai_narrative)
        clean = clean.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        lines.append("## 🧠 AI Synthesis\n")
        lines.append(f"{clean}\n")

    # Market Pulse
    if market_pulse:
        lines.append("## Market Pulse\n")
        for m in market_pulse:
            change_str = f"{m.get('change_pct', 0):+.2f}%" if m.get('change_pct') else ""
            lines.append(f"- **{m.get('name', '')}**: ${m.get('price', 'N/A')} {change_str}")
        lines.append("")

    # VIX
    vix = market.get("vix", {})
    lines.append(f"## VIX Regime: {vix.get('vix_level', 'N/A')} {vix.get('regime_name', '')}\n")
    lines.append(f"{vix.get('regime_desc', '')}\n")

    # Institutional
    lines.append("## Institutional Signals (TickerTrace)\n")
    buying = institutional.get("top_buying", [])
    selling = institutional.get("top_selling", [])
    if buying:
        lines.append("**🟢 Top Buying:**")
        for s in buying[:5]:
            funds = ", ".join(s.get("funds", [])[:3])
            lines.append(f"- [{s.get('ticker', '')}](https://www.tradingview.com/symbols/{s.get('ticker', '')}/) — {s.get('name', '')} ({funds}) Conv: {s.get('conviction', 0)}")
        lines.append("")
    if selling:
        lines.append("**🔴 Top Selling:**")
        for s in selling[:5]:
            funds = ", ".join(s.get("funds", [])[:3])
            lines.append(f"- [{s.get('ticker', '')}](https://www.tradingview.com/symbols/{s.get('ticker', '')}/) — {s.get('name', '')} ({funds}) Conv: {s.get('conviction', 0)}")
        lines.append("")

    # Scanner Signals
    if scanner_signals:
        lines.append("## Scanner Signals\n")
        for s in scanner_signals[:15]:
            emoji = "🟢" if s.get("direction") == "BULLISH" else "🔴" if s.get("direction") == "BEARISH" else "⚪"
            rationale = " · ".join(s.get("rationale", []))
            lines.append(f"- {emoji} [{s.get('symbol', '')}](https://www.tradingview.com/symbols/{s.get('symbol', '')}/) — {s.get('strategy', '')} | {rationale} | Score: {s.get('score', 0)}")
        lines.append("")

    # Technical Setups
    if technical_setups:
        lines.append("## Technical Setups (Tao of Trading)\n")
        for s in technical_setups:
            status = s.get("trend_status", "")
            stack = s.get("data_sack", {}).get("ema_stack", "")
            lines.append(f"- [{s.get('ticker', '')}](https://www.tradingview.com/symbols/{s.get('ticker', '')}/) — {status} | EMA Stack: {stack}")
        lines.append("")

    # Top Dossiers
    if dossiers:
        lines.append("## Top Dossier Breakdowns\n")
        for d in dossiers:
            tech = d.get("technicals", {})
            lines.append(f"### [{d.get('ticker', '')}](https://www.tradingview.com/symbols/{d.get('ticker', '')}/) — {d.get('name', '')}")
            lines.append(f"**${d.get('price', 'N/A')}** | Grade: {d.get('scores', {}).get('grade', 'N/A')} | {d.get('verdict', '')}")
            lines.append(f"- Trend: {tech.get('trend', '')} | EMA Stack: {tech.get('ema_stack', '')}")
            lines.append(f"- RSI: {tech.get('rsi_14', 'N/A')} | ADX: {tech.get('adx', 'N/A')} | ATR: {tech.get('atr', 'N/A')}")
            lines.append(f"- Pivot: ${tech.get('pivot', 'N/A')} | S1: ${tech.get('s1', 'N/A')} | R1: ${tech.get('r1', 'N/A')}")
            lines.append(f"- Valuation: {d.get('valuation', {}).get('status', '')} ({d.get('valuation', {}).get('gap_pct', 0):+.1f}%)")
            lines.append("")

    # Disclaimer
    lines.append("---\n")
    lines.append(f"*{DISCLAIMER}*\n")
    lines.append(f"*Generated by Ghost Alpha Dossier Pipeline // {date} // {generated_at}*")

    md_content = "\n".join(lines)
    md_path = OUTPUT_DIR / f"{date}_alpha_dossier.md"
    with open(md_path, "w") as f:
        f.write(md_content)

    print(f"  ✓ Markdown saved to: {md_path}")
    return str(md_path)


def build_pdf(html_path: str) -> str | None:
    """Convert the HTML report directly to PDF using WeasyPrint."""
    try:
        from weasyprint import HTML
    except ImportError:
        print("  [WARN] weasyprint not installed, skipping PDF")
        return None

    try:
        pdf_path = html_path.replace(".html", ".pdf")
        HTML(filename=html_path).write_pdf(pdf_path)
        print(f"  ✓ PDF saved to: {pdf_path}")
        return pdf_path

    except Exception as e:
        print(f"  [WARN] PDF generation failed: {e}")
        return None
