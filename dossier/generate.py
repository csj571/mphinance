#!/usr/bin/env python3
"""
Ghost Alpha Dossier — Daily Report Generator

Main orchestrator that runs the full pipeline using mphinance's existing
scanning strategies. Outputs HTML reports to docs/reports/ for GitHub Pages.

Pipeline stages:
  1. Market Pulse (SPY, QQQ, BTC, ETH, Gold, Treasuries)
  2. Run mphinance Strategies (Momentum, Squeeze, EMA Cross, Gamma)
  3. Fetch institutional data (TickerTrace API)
  4. Detect market regime (VIX + sector rotation)
  5. Track signal persistence (21-day rolling)
  6. Enrich top tickers (fundamentals, technicals, valuation)
  7. Generate AI narrative (Gemini)
  8. Render HTML report
  9. Update docs/index.html archive
 10. Git commit & push (optional)

Usage:
    python -m dossier.generate                     # Full pipeline
    python -m dossier.generate --dry-run           # No git push
    python -m dossier.generate --date 2026-03-03   # Specific date
    python -m dossier.generate --no-pdf            # Skip PDF
"""

import sys
import os
import argparse
import subprocess
from datetime import datetime, timezone
from pathlib import Path

# Ensure project root (mphinance/) is on path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dossier.config import CORE_WATCHLIST, MAX_DOSSIER_TICKERS, OUTPUT_DIR, SCANNER_STRATEGIES
from dossier.data_sources.tickertrace import _is_junk


def _run_mphinance_strategies() -> list[dict]:
    """
    Run mphinance's existing scanning strategies and normalize results
    into a list of scanner signal dicts for the dossier.
    """
    print("  Running mphinance strategies...")

    from strategies import get_strategy, get_strategy_names
    available = get_strategy_names()

    all_signals = []
    seen_tickers = set()

    for strategy_name in SCANNER_STRATEGIES:
        if strategy_name not in available:
            print(f"    [SKIP] Strategy not found: {strategy_name}")
            continue

        try:
            strategy = get_strategy(strategy_name)
            params = strategy.get_default_params()
            query = strategy.build_query(params)
            count, df = query.get_scanner_data()

            if count > 0 and not df.empty:
                df = strategy.post_process(df, params)
                print(f"    ✓ {strategy_name}: {len(df)} results")

                for _, row in df.head(15).iterrows():
                    symbol = str(row.get("name", ""))
                    if not symbol or symbol in seen_tickers:
                        continue
                    seen_tickers.add(symbol)

                    # Normalize into scanner signal format
                    close = row.get("close", 0)
                    rsi = row.get("RSI", row.get("RSI14", 50))
                    adx = row.get("ADX", row.get("ADX14", 0))

                    # Determine direction from strategy context
                    if strategy_name == "Bearish EMA Cross (Down)":
                        direction = "BEARISH"
                    elif strategy_name in ("Momentum with Pullback", "EMA Cross Momentum"):
                        direction = "BULLISH"
                    else:
                        # Neutral default, scored by technicals
                        direction = "BULLISH" if rsi and float(rsi) < 70 else "NEUTRAL"

                    # Score: simple heuristic from RSI + trend
                    score = 0.5
                    if direction == "BULLISH":
                        score = 0.65
                        if rsi and float(rsi) < 50:
                            score += 0.1  # Oversold bonus
                        if adx and float(adx) > 25:
                            score += 0.05  # Trending
                    elif direction == "BEARISH":
                        score = 0.3

                    # Rationale
                    rationale = [strategy_name.split()[0]]
                    if rsi:
                        rationale.append(f"RSI {int(float(rsi))}")
                    if adx and float(adx) > 20:
                        rationale.append(f"ADX {int(float(adx))}")

                    all_signals.append({
                        "symbol": symbol,
                        "direction": direction,
                        "score": min(1.0, round(score, 2)),
                        "rationale": rationale,
                        "strategy": strategy_name,
                        "price": round(float(close), 2) if close else 0,
                    })
            else:
                print(f"    ○ {strategy_name}: 0 results")
        except Exception as e:
            print(f"    [ERR] {strategy_name}: {e}")
            continue

    # Sort by score descending
    all_signals.sort(key=lambda x: x["score"], reverse=True)
    return all_signals


def _update_index_page():
    """Scan docs/reports/ and docs/ticker/ and regenerate the docs/index.html archive page."""
    from datetime import datetime as _dt
    docs_dir = OUTPUT_DIR.parent  # docs/
    reports_dir = OUTPUT_DIR       # docs/reports/
    watchlist_dir = docs_dir / "ticker"

    reports = []
    if reports_dir.exists():
        for f in sorted(reports_dir.iterdir(), reverse=True):
            if f.suffix == ".html":
                reports.append({
                    "filename": f.name,
                    "date": f.stem.replace("_alpha_dossier", ""),
                    "path": f"reports/{f.name}",
                })

    watchlist = []
    if watchlist_dir.exists():
        for ticker_folder in sorted(watchlist_dir.iterdir()):
            if ticker_folder.is_dir():
                dd = ticker_folder / "deep_dive.md"
                if dd.exists():
                    ticker = ticker_folder.name
                    mtime = _dt.fromtimestamp(dd.stat().st_mtime).strftime("%Y-%m-%d")
                    watchlist.append({
                        "ticker": ticker,
                        "html_path": f"ticker/{ticker}/deep_dive.html",
                        "md_path": f"ticker/{ticker}/deep_dive.md",
                        "json_path": f"ticker/{ticker}/deep_dive.json",
                        "date": mtime,
                    })

    index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ALPHA.DOSSIER // Archive</title>
    <link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {{
            theme: {{
                extend: {{
                    fontFamily: {{
                        'mono': ['"JetBrains Mono"', 'monospace'],
                        'tech': ['"Share Tech Mono"', 'monospace'],
                    }},
                    colors: {{
                        'neon-green': '#00ff41',
                        'neon-red': '#ff3e3e',
                        'neon-blue': '#00f3ff',
                        'neon-amber': '#ffb000',
                    }}
                }}
            }}
        }}
    </script>
    <style>
        body {{
            background-color: #050505;
            color: #e0e0e0;
            font-family: 'JetBrains Mono', monospace;
            background-image:
                linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%),
                linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06));
            background-size: 100% 2px, 3px 100%;
        }}
        .hud-panel {{
            background: rgba(10, 10, 10, 0.8);
            border: 1px solid #333;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.5);
            backdrop-filter: blur(4px);
        }}
        .report-link {{ transition: all 0.2s; }}
        .report-link:hover {{ transform: translateX(4px); border-color: #00f3ff; }}
    </style>
</head>
<body class="min-h-screen p-4 md:p-8">
    <div class="max-w-4xl mx-auto space-y-6">
        <div style="background:linear-gradient(90deg,#1a1a2e,#16213e);border:1px solid #0f3460;padding:8px 16px;text-align:center;font-size:10px;font-family:'JetBrains Mono',monospace;border-radius:2px">
            <a href="https://www.traderdaddy.pro/register?ref=8DUEMWAJ" target="_blank" style="color:#00f3ff;letter-spacing:0.1em;text-transform:uppercase;text-decoration:none">🚀 Try TraderDaddy Pro — AI-Powered Trading Dashboard</a>
        </div>
        <div class="hud-panel p-6 rounded-sm border-l-4 border-neon-blue">
            <h1 class="text-2xl md:text-3xl font-black font-tech tracking-widest text-white uppercase italic">
                ALPHA.DOSSIER <span class="text-neon-blue">●</span> ARCHIVE
            </h1>
            <p class="text-[10px] text-gray-500 uppercase tracking-[0.3em] mt-1">
                Daily Intelligence Reports // Ghost Alpha Pipeline
            </p>
        </div>

        <div class="hud-panel p-4 rounded-sm">
            <div class="text-[10px] text-gray-500 uppercase tracking-widest mb-4 border-b border-gray-800 pb-2">
                REPORTS <span class="text-neon-blue">// {len(reports)} TOTAL</span>
            </div>
            <div class="space-y-2">
"""

    if reports:
        for i, r in enumerate(reports):
            is_latest = " border-neon-green" if i == 0 else " border-gray-800"
            latest_badge = '<span class="text-neon-green text-[9px] ml-2 font-bold">LATEST</span>' if i == 0 else ""
            index_html += f"""                <a href="{r['path']}" class="report-link block bg-black/40 border{is_latest} rounded px-4 py-3 text-sm hover:bg-gray-900/50">
                    <span class="text-neon-blue font-bold">{r['date']}</span>
                    <span class="text-gray-500 ml-3">Alpha Dossier</span>
                    {latest_badge}
                </a>
"""
    else:
        index_html += '                <div class="text-gray-600 text-sm italic p-4">No reports generated yet. Run the pipeline first.</div>\n'

    index_html += """            </div>
        </div>
"""

    # ── Watchlist Deep Dives Section ──
    if watchlist:
        index_html += f"""
        <div class="hud-panel p-4 rounded-sm border-l-4 border-neon-amber">
            <div class="text-[10px] text-gray-500 uppercase tracking-widest mb-4 border-b border-gray-800 pb-2">
                🔍 WATCHLIST.DEEP.DIVES <span class="text-neon-amber">// {len(watchlist)} TICKERS</span>
            </div>
            <div class="grid grid-cols-2 md:grid-cols-3 gap-2">
"""
        for w in watchlist:
            index_html += f"""                <div class="report-link bg-black/40 border border-gray-800 rounded px-4 py-3 flex items-center justify-between">
                    <div class="flex items-center gap-3">
                        <a href="{w['html_path']}" class="text-neon-amber font-bold text-sm hover:text-white transition-colors">{w['ticker']}</a>
                        <span class="text-[9px] text-gray-600">{w['date']}</span>
                    </div>
                    <div class="flex gap-2">
                        <a href="https://www.tradingview.com/symbols/{w['ticker']}/" target="_blank" class="text-[9px] text-gray-400 border border-gray-700 px-1.5 py-0.5 rounded hover:text-neon-blue hover:border-neon-blue/30 transition-colors">TV</a>
                        <a href="{w['md_path']}" download class="text-[9px] text-gray-400 border border-gray-700 px-1.5 py-0.5 rounded hover:text-white hover:border-gray-500 transition-colors">MD</a>
                        <a href="{w['json_path']}" class="text-[9px] text-gray-400 border border-gray-700 px-1.5 py-0.5 rounded hover:text-white hover:border-gray-500 transition-colors">JSON</a>
                    </div>
                </div>
"""
        index_html += """            </div>
        </div>
"""

    index_html += """
        <div class="text-center py-4">
            <div class="text-[9px] text-gray-700 font-mono uppercase tracking-widest">
                Ghost Alpha Dossier Pipeline // mphinance
            </div>
        </div>
    </div>
</body>
</html>
"""

    index_path = docs_dir / "index.html"
    with open(index_path, "w") as f:
        f.write(index_html)
    print(f"  ✓ Index updated: {index_path} ({len(reports)} reports, {len(watchlist)} watchlist)")


def run_pipeline(date: str, dry_run: bool = False, generate_pdf: bool = True):
    """Execute the full Alpha Dossier pipeline."""

    print("=" * 72)
    print(f"  🔮 GHOST ALPHA DOSSIER — PIPELINE START")
    print(f"  Date: {date}")
    print(f"  Mode: {'DRY RUN' if dry_run else 'FULL'}")
    print("=" * 72)

    # ── Stage 1: Market Pulse ──
    print("\n[1/9] MARKET PULSE")
    from dossier.data_sources.market_pulse import fetch_market_pulse
    market_pulse = fetch_market_pulse()
    print(f"  {len(market_pulse)} benchmarks fetched")

    # ── Stage 2: Strategy Scanner ──
    print("\n[2/9] STRATEGY SCANNER")
    scanner_signals = _run_mphinance_strategies()

    # Also scan core watchlist with a simple technical check
    from dossier.data_sources.ticker_enrichment import _sma, _rsi, _ema
    import yfinance as yf

    for ticker in CORE_WATCHLIST:
        if ticker in [s["symbol"] for s in scanner_signals]:
            continue
        try:
            hist = yf.Ticker(ticker).history(period="3mo")
            if hist.empty:
                continue
            close = hist["Close"]
            sma50 = _sma(close, 50).iloc[-1]
            sma200 = _sma(close, 200).iloc[-1] if len(close) >= 200 else sma50
            rsi_val = _rsi(close).iloc[-1]
            price = float(close.iloc[-1])

            rationale = []
            score = 0.4
            direction = "NEUTRAL"

            if price > sma200:
                rationale.append("Above SMA200")
                score += 0.1
            if rsi_val and 30 < rsi_val < 50:
                rationale.append(f"RSI {int(rsi_val)}")
                score += 0.1
                direction = "BULLISH"
            elif rsi_val:
                rationale.append(f"RSI {int(rsi_val)}")

            ema21 = _ema(close, 21).iloc[-1]
            if abs(price - ema21) / price < 0.02:
                rationale.append("Near EMA21 support")
                score += 0.05

            scanner_signals.append({
                "symbol": ticker,
                "direction": direction,
                "score": min(1.0, round(score, 2)),
                "rationale": rationale,
                "strategy": "Core Watchlist",
                "price": round(price, 2),
            })
        except Exception:
            continue

    scanner_signals.sort(key=lambda x: x["score"], reverse=True)
    print(f"  Total signals: {len(scanner_signals)}")

    scanned_tickers = [s["symbol"] for s in scanner_signals]

    # ── Stage 3: Institutional Data ──
    print("\n[3/9] TICKERTRACE INSTITUTIONAL DATA")
    from dossier.data_sources.tickertrace import fetch_institutional_data
    institutional = fetch_institutional_data()

    # ── Stage 4: Market Regime ──
    print("\n[4/9] MARKET REGIME")
    from dossier.data_sources.market_regime import fetch_market_regime
    market = fetch_market_regime()

    # ── Stage 5: Persistence ──
    print("\n[5/9] SIGNAL PERSISTENCE")
    from dossier.persistence.tracker import update_persistence
    persistence = update_persistence(scanned_tickers, date)
    print(f"  Lifers: {persistence['summary']['lifers']}")
    print(f"  High Conviction: {persistence['summary']['high_conviction']}")
    print(f"  New Signals: {persistence['summary']['new_signals']}")

    # ── Stage 6: Technical Setups ──
    print("\n[6/11] TECHNICAL SETUPS (Tao of Trading)")
    from dossier.data_sources.technical_setups import generate_setups
    # Analyze top strategy picks for setup quality
    setup_tickers = [s["symbol"] for s in scanner_signals if s["strategy"] != "Core Watchlist"][:8]
    # Fill with institutional buying tickers
    inst_buy_tickers = [s["ticker"] for s in institutional.get("top_buying", [])[:4]]
    setup_tickers = [t for t in dict.fromkeys(setup_tickers + inst_buy_tickers) if not _is_junk(t)][:10]
    technical_setups = generate_setups(setup_tickers, max_setups=6)
    print(f"  {len(technical_setups)} setups analyzed")

    # ── Stage 7: CSP Setups ──
    print("\n[7/11] CSP SETUPS")
    from dossier.data_sources.csp_setups import fetch_csp_setups
    csp_setups = fetch_csp_setups(max_results=8)
    print(f"  {len(csp_setups)} CSP candidates")

    # ── Stage 8: Ticker Enrichment ──
    print(f"\n[8/11] TICKER ENRICHMENT (top {MAX_DOSSIER_TICKERS})")
    from dossier.data_sources.ticker_enrichment import enrich_ticker

    # Prioritize strategy-found tickers + institutional buying
    strategy_tickers = [s["symbol"] for s in scanner_signals if s["strategy"] != "Core Watchlist"][:5]
    inst_tickers = [s["ticker"] for s in institutional.get("top_buying", [])[:3]]
    enrichment_order = [t for t in dict.fromkeys(
        strategy_tickers + inst_tickers + scanned_tickers[:MAX_DOSSIER_TICKERS]
    ) if not _is_junk(t)]

    dossiers = []
    for ticker in enrichment_order[:MAX_DOSSIER_TICKERS]:
        data = enrich_ticker(ticker)
        if data:
            dossiers.append(data)
    print(f"  {len(dossiers)} dossiers enriched")

    # ── Stage 9: AI Narrative ──
    print("\n[9/11] AI NARRATIVE")
    from dossier.report.ai_narrative import generate_narrative
    ai_narrative = generate_narrative(market, institutional, scanner_signals, persistence, dossiers)

    # ── Stage 10: Report Generation ──
    print("\n[10/11] REPORT GENERATION")
    from dossier.report.builder import build_report, build_pdf

    report_path = build_report(
        date=date,
        market=market,
        market_pulse=market_pulse,
        institutional=institutional,
        scanner_signals=scanner_signals,
        persistence=persistence,
        dossiers=dossiers,
        ai_narrative=ai_narrative,
        technical_setups=technical_setups,
        csp_setups=csp_setups,
    )

    pdf_path = None
    if generate_pdf:
        pdf_path = build_pdf(report_path)

    # ── Stage 11: Ticker Deep-Dive Pages ──
    print("\n[11/13] TICKER PAGES")
    try:
        from dossier.pages.ticker_page import generate_all_ticker_pages
        ticker_pages = generate_all_ticker_pages(dossiers, date, institutional)
        print(f"  ✓ Generated {len(ticker_pages)} ticker pages")
    except Exception as e:
        print(f"  [WARN] Ticker pages failed: {e}")
        ticker_pages = []

    # ── Stage 12: Update Index ──
    print("\n[12/13] INDEX UPDATE")
    _update_index_page()

    # ── Stage 13: Git Push ──
    if not dry_run:
        print("\n[13/13] GIT PUSH")
        print("  Committing to Git...")
        try:
            subprocess.run(["git", "add", "docs/", "dossier/persistence/"],
                           cwd=str(PROJECT_ROOT), check=True)
            subprocess.run(
                ["git", "commit", "-m", f"📊 Alpha Dossier {date}"],
                cwd=str(PROJECT_ROOT), check=True
            )
            subprocess.run(["git", "push"], cwd=str(PROJECT_ROOT), check=True)
            print("  ✓ Pushed to GitHub")
        except subprocess.CalledProcessError as e:
            print(f"  [WARN] Git push failed: {e}")
    else:
        print("\n[SKIP] Dry run — skipping git push")

    # ── Summary ──
    print("\n" + "=" * 72)
    print("  ✅ PIPELINE COMPLETE")
    print(f"  Report: {report_path}")
    if pdf_path:
        print(f"  PDF:    {pdf_path}")
    print(f"  Pulse:  {len(market_pulse)} benchmarks")
    print(f"  Signals: {len(scanner_signals)}")
    print(f"  Dossiers: {len(dossiers)}")
    print(f"  Ticker Pages: {len(ticker_pages)}")
    print(f"  VIX: {market['vix']['vix_level']} ({market['vix']['regime_name']})")
    print("=" * 72)

    return report_path


def main():
    parser = argparse.ArgumentParser(description="Ghost Alpha Dossier — Daily Report Generator")
    parser.add_argument("--date", type=str, default=None, help="Report date (YYYY-MM-DD)")
    parser.add_argument("--dry-run", action="store_true", help="Skip git push")
    parser.add_argument("--no-pdf", action="store_true", help="Skip PDF generation")
    args = parser.parse_args()

    date = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    run_pipeline(date=date, dry_run=args.dry_run, generate_pdf=not args.no_pdf)


if __name__ == "__main__":
    main()
