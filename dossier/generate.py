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
    """Scan docs/reports/ and docs/ticker/ and regenerate the docs/index.html archive page.
    Also copies the latest report to docs/reports/latest.html for a stable permalink."""
    import shutil
    import json as _json
    from datetime import datetime as _dt
    from collections import defaultdict

    docs_dir = OUTPUT_DIR.parent  # docs/
    reports_dir = OUTPUT_DIR       # docs/reports/
    watchlist_dir = docs_dir / "ticker"

    reports = []
    if reports_dir.exists():
        for f in sorted(reports_dir.iterdir(), reverse=True):
            if f.suffix == ".html" and f.stem != "latest":
                reports.append({
                    "filename": f.name,
                    "date": f.stem.replace("_alpha_dossier", ""),
                    "path": f"reports/{f.name}",
                })

    # ── Copy latest report to docs/reports/latest.html ──
    if reports:
        latest_src = reports_dir / reports[0]["filename"]
        latest_dst = reports_dir / "latest.html"
        shutil.copy2(latest_src, latest_dst)
        print(f"  ✓ Latest report copied → {latest_dst}")

    # ── Gather watchlist with sector data from JSON ──
    watchlist = []
    if watchlist_dir.exists():
        for ticker_folder in sorted(watchlist_dir.iterdir()):
            if ticker_folder.is_dir():
                dd_json = ticker_folder / "deep_dive.json"
                dd_md = ticker_folder / "deep_dive.md"
                if dd_md.exists():
                    ticker = ticker_folder.name
                    mtime = _dt.fromtimestamp(dd_md.stat().st_mtime).strftime("%Y-%m-%d")

                    # Read sector from JSON if available
                    sector = "Other"
                    industry = ""
                    price = ""
                    if dd_json.exists():
                        try:
                            with open(dd_json, "r") as jf:
                                jdata = _json.load(jf)
                                sector = jdata.get("sector", "Other") or "Other"
                                industry = jdata.get("industry", "")
                                p = jdata.get("price", "")
                                price = f"${p:.2f}" if isinstance(p, (int, float)) else ""
                        except Exception:
                            pass

                    watchlist.append({
                        "ticker": ticker,
                        "html_path": f"ticker/{ticker}/deep_dive.html",
                        "md_path": f"ticker/{ticker}/deep_dive.md",
                        "json_path": f"ticker/{ticker}/deep_dive.json",
                        "date": mtime,
                        "sector": sector,
                        "industry": industry,
                        "price": price,
                    })

    # ── Group by sector ──
    sectors = defaultdict(list)
    for w in watchlist:
        sectors[w["sector"]].append(w)

    # Sort sectors by count descending, "Other" at the end
    sorted_sectors = sorted(
        sectors.items(),
        key=lambda x: (x[0] == "Other", -len(x[1]), x[0])
    )

    # Sector emoji/color mapping
    sector_styles = {
        "Technology": ("#00f3ff", "💻"),
        "Healthcare": ("#00ff88", "🏥"),
        "Financial Services": ("#ffb000", "🏦"),
        "Consumer Cyclical": ("#ff6b6b", "🛍️"),
        "Consumer Defensive": ("#a855f7", "🛒"),
        "Energy": ("#ff8c00", "⚡"),
        "Industrials": ("#888", "🏭"),
        "Basic Materials": ("#cd7f32", "⛏️"),
        "Communication Services": ("#00d4ff", "📡"),
        "Real Estate": ("#4caf50", "🏠"),
        "Utilities": ("#6b6bff", "💡"),
    }

    # ── Build latest report date for hero section ──
    latest_date = reports[0]["date"] if reports else "—"

    index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-KTHVTFX699"></script>
    <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-KTHVTFX699');</script>
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
        .archive-link {{ transition: all 0.15s; display: flex; padding: 6px 10px; border-radius: 3px; text-decoration: none; }}
        .archive-link:hover {{ background: rgba(0, 243, 255, 0.06); }}
        .latest-cta {{
            display: block;
            background: linear-gradient(135deg, rgba(0, 255, 65, 0.08), rgba(0, 243, 255, 0.05));
            border: 1px solid #00ff41;
            border-radius: 4px;
            padding: 32px 28px;
            text-decoration: none;
            transition: all 0.3s;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
            position: relative;
            overflow: hidden;
        }}
        .latest-cta:hover {{
            border-color: #00f3ff;
            box-shadow: 0 0 30px rgba(0, 255, 65, 0.15), 0 0 60px rgba(0, 243, 255, 0.08);
            transform: translateY(-2px);
        }}
        .latest-cta::before {{
            content: '';
            position: absolute;
            top: 0; left: -100%;
            width: 100%; height: 100%;
            background: linear-gradient(90deg, transparent, rgba(0, 255, 65, 0.05), transparent);
            animation: shimmer 3s infinite;
        }}
        @keyframes shimmer {{ 100% {{ left: 100%; }} }}
        .pulse-dot {{
            display: inline-block;
            width: 8px; height: 8px;
            background: #00ff41;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }}
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; box-shadow: 0 0 4px #00ff41; }}
            50% {{ opacity: 0.4; box-shadow: 0 0 12px #00ff41; }}
        }}
        .sector-header {{
            cursor: pointer;
            transition: all 0.2s;
            user-select: none;
        }}
        .sector-header:hover {{
            border-color: #00f3ff !important;
        }}
        .sector-content {{
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease-out;
        }}
        .sector-content.open {{
            max-height: 2000px;
            transition: max-height 0.5s ease-in;
        }}
        .view-badge {{
            font-size: 8px;
            color: #555;
            background: rgba(255,255,255,0.03);
            padding: 2px 6px;
            border-radius: 3px;
            border: 1px solid #222;
        }}
    </style>
</head>
<body class="min-h-screen p-4 md:p-8">
    <div class="max-w-5xl mx-auto space-y-5">
        <div style="background:linear-gradient(90deg,#1a1a2e,#16213e);border:1px solid #0f3460;padding:8px 16px;text-align:center;font-size:10px;font-family:'JetBrains Mono',monospace;border-radius:2px">
            <a href="https://www.traderdaddy.pro/register?ref=8DUEMWAJ" target="_blank" style="color:#00f3ff;letter-spacing:0.1em;text-transform:uppercase;text-decoration:none">🚀 Try TraderDaddy Pro — AI-Powered Trading Dashboard</a>
        </div>
        <div class="hud-panel p-6 rounded-sm border-l-4 border-neon-blue">
            <div class="flex justify-between items-center">
                <div>
                    <h1 class="text-2xl md:text-3xl font-black font-tech tracking-widest text-white uppercase italic">
                        ALPHA.DOSSIER <span class="text-neon-blue">●</span> ARCHIVE
                    </h1>
                    <p class="text-[10px] text-gray-500 uppercase tracking-[0.3em] mt-1">
                        Daily Intelligence Reports // Ghost Alpha Pipeline
                    </p>
                </div>
                <div class="text-right">
                    <div class="text-[9px] text-gray-600 uppercase">Page Views</div>
                    <div class="text-sm text-neon-blue font-bold font-mono" id="index-views">—</div>
                </div>
            </div>
        </div>
"""

    # ── Two-column: Hero CTA (left) + Archive sidebar (right) ──
    if reports:
        index_html += f"""
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="md:col-span-2">
                <a href="reports/latest.html" class="latest-cta">
                    <div class="flex items-center gap-3 mb-3">
                        <span class="pulse-dot"></span>
                        <span class="text-[10px] text-neon-green uppercase tracking-[0.3em] font-bold">Latest Report</span>
                    </div>
                    <div class="text-2xl md:text-3xl font-bold text-white font-tech tracking-wider mb-2">
                        Alpha Dossier
                    </div>
                    <div class="text-lg text-neon-blue font-tech">{latest_date}</div>
                    <div class="text-[10px] text-gray-500 mt-4 uppercase tracking-widest">
                        Click to read the full intelligence report →
                    </div>
                    <div class="text-[9px] text-gray-700 mt-2">
                        Permalink: /reports/latest.html
                    </div>
                </a>
            </div>
            <div class="md:col-span-1">
                <div class="hud-panel p-4 rounded-sm h-full">
                    <div class="text-[10px] text-gray-500 uppercase tracking-widest mb-3 border-b border-gray-800 pb-2">
                        📁 Archive <span class="text-neon-blue">// {len(reports)}</span>
                    </div>
                    <div class="space-y-1 max-h-64 overflow-y-auto pr-1" style="scrollbar-width:thin;scrollbar-color:#333 transparent">
"""
        for i, r in enumerate(reports):
            dot_color = "text-neon-green" if i == 0 else "text-gray-700"
            index_html += f"""                        <a href="{r['path']}" class="archive-link flex items-center gap-2">
                            <span class="{dot_color} text-[6px]">●</span>
                            <span class="text-neon-blue text-xs">{r['date']}</span>
                        </a>
"""
        index_html += """                    </div>
                </div>
            </div>
        </div>
"""
    else:
        index_html += '        <div class="hud-panel p-6 rounded-sm text-gray-600 text-sm italic">No reports generated yet. Run the pipeline first.</div>\n'

    # ── Watchlist Deep Dives — Grouped by Sector ──
    if watchlist:
        index_html += f"""
        <div class="hud-panel p-4 rounded-sm border-l-4 border-neon-amber">
            <div class="flex justify-between items-center mb-4 border-b border-gray-800 pb-2">
                <div class="text-[10px] text-gray-500 uppercase tracking-widest">
                    🔍 WATCHLIST.DEEP.DIVES <span class="text-neon-amber">// {len(watchlist)} TICKERS · {len(sorted_sectors)} SECTORS</span>
                </div>
                <button onclick="toggleAll()" class="text-[9px] text-gray-600 border border-gray-700 px-2 py-0.5 rounded hover:text-neon-blue hover:border-neon-blue/30 transition-colors" id="toggle-btn">
                    Expand All
                </button>
            </div>
"""
        for sector_name, tickers in sorted_sectors:
            color, emoji = sector_styles.get(sector_name, ("#888", "📦"))
            index_html += f"""
            <div class="mb-2">
                <div class="sector-header flex items-center justify-between bg-black/30 border border-gray-800 rounded px-4 py-2"
                     onclick="toggleSector(this)" style="border-left: 3px solid {color}">
                    <div class="flex items-center gap-2">
                        <span>{emoji}</span>
                        <span class="text-xs font-bold text-white">{sector_name}</span>
                        <span class="text-[9px] text-gray-600">{len(tickers)} ticker{"s" if len(tickers) != 1 else ""}</span>
                    </div>
                    <span class="text-[10px] text-gray-600 sector-arrow">▸</span>
                </div>
                <div class="sector-content">
                    <div class="grid grid-cols-2 md:grid-cols-3 gap-2 pt-2 pb-3">
"""
            for w in sorted(tickers, key=lambda x: x["ticker"]):
                index_html += f"""                        <div class="report-link bg-black/40 border border-gray-800 rounded px-4 py-3 flex items-center justify-between">
                            <div class="flex items-center gap-2">
                                <a href="{w['html_path']}" class="text-neon-amber font-bold text-sm hover:text-white transition-colors">{w['ticker']}</a>
                                <span class="text-[8px] text-gray-700">{w['price']}</span>
                                <span class="view-badge" data-ticker="{w['ticker']}">—</span>
                            </div>
                            <div class="flex gap-2">
                                <a href="https://www.tradingview.com/symbols/{w['ticker']}/chart/" target="_blank" class="text-[9px] text-gray-400 border border-gray-700 px-1.5 py-0.5 rounded hover:text-neon-blue hover:border-neon-blue/30 transition-colors">TV</a>
                                <a href="{w['md_path']}" download class="text-[9px] text-gray-400 border border-gray-700 px-1.5 py-0.5 rounded hover:text-white hover:border-gray-500 transition-colors">MD</a>
                                <a href="{w['json_path']}" class="text-[9px] text-gray-400 border border-gray-700 px-1.5 py-0.5 rounded hover:text-white hover:border-gray-500 transition-colors">JSON</a>
                            </div>
                        </div>
"""
            index_html += """                    </div>
                </div>
            </div>
"""
        index_html += """        </div>
"""

    # ── Page View Analytics Summary ──
    index_html += """
        <div class="hud-panel p-4 rounded-sm">
            <div class="text-[10px] text-gray-500 uppercase tracking-widest mb-3 border-b border-gray-800 pb-2">
                📊 ANALYTICS.PULSE <span class="text-neon-blue">// LOCAL TRACKING</span>
            </div>
            <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
                <div class="bg-black/40 border border-gray-800 rounded p-3">
                    <div class="text-[9px] text-gray-600 uppercase">Index Views</div>
                    <div class="text-lg font-bold text-neon-blue font-mono" id="stat-index">—</div>
                </div>
                <div class="bg-black/40 border border-gray-800 rounded p-3">
                    <div class="text-[9px] text-gray-600 uppercase">Report Views</div>
                    <div class="text-lg font-bold text-neon-green font-mono" id="stat-reports">—</div>
                </div>
                <div class="bg-black/40 border border-gray-800 rounded p-3">
                    <div class="text-[9px] text-gray-600 uppercase">Ticker Pages</div>
                    <div class="text-lg font-bold text-neon-amber font-mono" id="stat-tickers">—</div>
                </div>
                <div class="bg-black/40 border border-gray-800 rounded p-3">
                    <div class="text-[9px] text-gray-600 uppercase">Top Ticker</div>
                    <div class="text-lg font-bold text-white font-mono" id="stat-top">—</div>
                </div>
            </div>
        </div>
"""

    index_html += """
        <div class="text-center py-4">
            <div class="text-[9px] text-gray-700 font-mono uppercase tracking-widest">
                Ghost Alpha Dossier Pipeline // mphinance
            </div>
        </div>
    </div>

    <script>
    // ── Page View Tracking (localStorage) ──
    (function() {
        const STORAGE_KEY = 'ghost_dossier_analytics';
        let analytics = {};
        try { analytics = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}'); } catch(e) {}

        // Track this page
        const page = 'index';
        analytics[page] = (analytics[page] || 0) + 1;
        localStorage.setItem(STORAGE_KEY, JSON.stringify(analytics));

        // Display index views
        const el = document.getElementById('index-views');
        if (el) el.textContent = analytics[page];
        const statEl = document.getElementById('stat-index');
        if (statEl) statEl.textContent = analytics[page];

        // Aggregate stats
        let reportViews = 0, tickerViews = 0, topTicker = '', topCount = 0;
        for (const [k, v] of Object.entries(analytics)) {
            if (k.startsWith('report:')) reportViews += v;
            if (k.startsWith('ticker:')) {
                tickerViews += v;
                if (v > topCount) { topCount = v; topTicker = k.replace('ticker:', ''); }
            }
        }
        const rEl = document.getElementById('stat-reports');
        if (rEl) rEl.textContent = reportViews || '—';
        const tEl = document.getElementById('stat-tickers');
        if (tEl) tEl.textContent = tickerViews || '—';
        const topEl = document.getElementById('stat-top');
        if (topEl) topEl.textContent = topTicker || '—';

        // Show per-ticker view counts
        document.querySelectorAll('.view-badge[data-ticker]').forEach(badge => {
            const t = badge.dataset.ticker;
            const views = analytics['ticker:' + t] || 0;
            badge.textContent = views ? views + '👁' : '';
        });
    })();

    // ── Sector Toggle ──
    function toggleSector(header) {
        const content = header.nextElementSibling;
        const arrow = header.querySelector('.sector-arrow');
        content.classList.toggle('open');
        arrow.textContent = content.classList.contains('open') ? '▾' : '▸';
    }

    function toggleAll() {
        const sections = document.querySelectorAll('.sector-content');
        const btn = document.getElementById('toggle-btn');
        const allOpen = Array.from(sections).every(s => s.classList.contains('open'));
        sections.forEach(s => {
            if (allOpen) s.classList.remove('open');
            else s.classList.add('open');
        });
        document.querySelectorAll('.sector-arrow').forEach(a => a.textContent = allOpen ? '▸' : '▾');
        btn.textContent = allOpen ? 'Expand All' : 'Collapse All';
    }

    // Auto-expand first sector
    const firstContent = document.querySelector('.sector-content');
    if (firstContent) {
        firstContent.classList.add('open');
        firstContent.previousElementSibling.querySelector('.sector-arrow').textContent = '▾';
    }
    </script>
</body>
</html>
"""

    index_path = docs_dir / "index.html"
    with open(index_path, "w") as f:
        f.write(index_html)
    print(f"  ✓ Index updated: {index_path} ({len(reports)} reports, {len(watchlist)} watchlist, {len(sorted_sectors)} sectors)")


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
    # Fallback to core watchlist if no strategy/institutional tickers
    if not setup_tickers:
        setup_tickers = CORE_WATCHLIST[:6]
        print("  (falling back to Core Watchlist for setups)")
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

    # ── Stage 8a: Market Regime Detection ──
    print("\n[8a/14] MARKET REGIME DETECTION")
    market_regime = {}
    try:
        from dossier.market_regime import detect_regime
        market_regime = detect_regime()
        regime = market_regime.get("regime", "UNKNOWN")
        vix = market_regime.get("vix", 0)
        print(f"  Regime: {regime} (VIX {vix:.1f})")
        print(f"  {market_regime.get('market_context', '')}")
        for s in market_regime.get("hedge_suggestions", []):
            print(f"  → {s}")
    except Exception as e:
        print(f"  [WARN] Market regime detection failed: {e}")

    # ── Stage 8b: Momentum Picks ──
    print("\n[8b/14] DAILY MOMENTUM PICKS")
    momentum_picks = {}
    try:
        from dossier.momentum_picks import pick_daily_momentum, format_picks_text
        # Build payloads from dossier data for scoring
        # We need ticker pages' JSON format — use what we have
        from dossier.pages.ticker_page import TICKER_OUTPUT_DIR
        import json as _picks_json
        
        payloads_for_scoring = []
        for d in dossiers:
            ticker = d.get("ticker", "")
            latest_json = TICKER_OUTPUT_DIR / ticker / "latest.json"
            if latest_json.exists():
                try:
                    with open(latest_json) as pf:
                        payloads_for_scoring.append(_picks_json.load(pf))
                except Exception:
                    pass
        
        # If no existing JSONs (first run), score from enriched data directly
        if not payloads_for_scoring:
            for d in dossiers:
                tech = d.get("technicals", {})
                scores = d.get("scores", {})
                payloads_for_scoring.append({
                    "ticker": d.get("ticker", ""),
                    "currentPrice": d.get("price", 0),
                    "priceChangePct": d.get("change_pct", 0),
                    "trendOverall": "Bullish" if tech.get("ema_stack", "").startswith("FULL BULL") else "Bearish",
                    "technical_analysis": {
                        "ema_stack": tech.get("ema_stack", "UNKNOWN"),
                        "ema": {"21": tech.get("ema_21")},
                        "oscillators": {"rsi_14": tech.get("rsi_14"), "adx_14": tech.get("adx")},
                        "volume": {"rel_vol": tech.get("rel_vol", 1.0)},
                    },
                    "scores": scores,
                    "tickertrace": d.get("tickertrace", {}),
                })
        
        momentum_picks = pick_daily_momentum(payloads_for_scoring, date)
        picks_text = format_picks_text(momentum_picks)
        print(f"  {picks_text}")
    except Exception as e:
        print(f"  [WARN] Momentum picks failed: {e}")

    # ── Stage 8d: Daily Trading Setups (3-Style) ──
    print("\n[8d/14] DAILY TRADING SETUPS (Day Trade / Swing / CSP)")
    daily_setups_data = {}
    try:
        from dossier.daily_setups import build_daily_setups, format_setups_text
        # Reuse payloads from momentum scoring
        daily_setups_data = build_daily_setups(
            payloads_for_scoring if 'payloads_for_scoring' in dir() else [],
            date,
            csp_data=csp_setups,
        )
        setups_text = format_setups_text(daily_setups_data)
        print(f"  {setups_text}")
    except Exception as e:
        print(f"  [WARN] Daily setups failed: {e}")

    # ── Stage 8c: Chart Generation ──
    print("\n[8c/14] CHART GENERATION")
    try:
        from dossier.charts import generate_charts_for_dossier
        chart_tickers = [d["ticker"] for d in dossiers[:5]]
        charts = generate_charts_for_dossier(chart_tickers, output_dir=str(OUTPUT_DIR.parent / "charts"), max_charts=5)
        # Attach chart paths to dossier data
        chart_map = {c["ticker"]: c["path"] for c in charts}
        for d in dossiers:
            d["chart_path"] = chart_map.get(d["ticker"], "")
        print(f"  {len(charts)} charts generated")
    except Exception as e:
        print(f"  [WARN] Chart generation failed: {e}")
        charts = []

    # ── Stage 9: AI Narrative ──
    print("\n[9/14] AI NARRATIVE")
    from dossier.report.ai_narrative import generate_narrative
    ai_narrative = generate_narrative(market, institutional, scanner_signals, persistence, dossiers)

    # ── Stage 9b: Ghost Dev Log ──
    print("\n[9b/11] GHOST DEV LOG")
    try:
        from dossier.report.ghost_log import generate_ghost_log
        ghost_log = generate_ghost_log(date)
        preview = ghost_log[:80].replace('<br>', ' ').replace('<em>', '').replace('</em>', '')
        print(f"  👻 {preview}...")
    except Exception as e:
        print(f"  [WARN] Ghost log failed: {e}")
        ghost_log = ""

    # ── Stage 9c: Ghost Suggestions ──
    print("\n[9c/13] GHOST SUGGESTIONS")
    try:
        from dossier.report.ghost_suggestions import generate_suggestions
        ghost_suggestions = generate_suggestions(date)
        preview = ghost_suggestions[:80].replace('<br>', ' ').replace('<b>', '').replace('</b>', '')
        print(f"  🗺️ {preview}...")
    except Exception as e:
        print(f"  [WARN] Ghost suggestions failed: {e}")
        ghost_suggestions = ""

    # ── Stage 10: Report Generation ──
    print("\n[10/13] REPORT GENERATION")
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
        ghost_log=ghost_log,
        ghost_suggestions=ghost_suggestions,
        momentum_picks=momentum_picks,
        market_regime=market_regime,
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

    # ── Stage 11b: Auto-Watchlist Discovery ──
    print("\n[11b/13] AUTO-WATCHLIST (A-grade only)")
    try:
        watchlist_path = PROJECT_ROOT / "watchlist.txt"
        existing = set()
        if watchlist_path.exists():
            existing = set(l.strip().upper() for l in watchlist_path.read_text().splitlines() if l.strip())

        ticker_dir = PROJECT_ROOT / "docs" / "ticker"
        has_page = set()
        if ticker_dir.exists():
            has_page = set(d.name for d in ticker_dir.iterdir() if d.is_dir())

        new_adds = []
        for d in dossiers:
            ticker = d.get("ticker", "").upper()
            grade = d.get("scores", {}).get("grade", "")
            if grade == "A" and ticker and ticker not in existing and ticker not in has_page:
                new_adds.append(ticker)

        if new_adds:
            with open(watchlist_path, "a") as f:
                for t in new_adds:
                    f.write(f"{t}\n")
            print(f"  🆕 Auto-added {len(new_adds)} A-grade tickers: {', '.join(new_adds)}")
        else:
            print(f"  ✓ No new A-grade discoveries (checked {len(dossiers)} dossiers)")
    except Exception as e:
        print(f"  [WARN] Auto-watchlist failed: {e}")

    # ── Stage 12: Update Index ──
    print("\n[12/13] INDEX UPDATE")
    _update_index_page()

    # ── Stage 12b: Blog Entry ──
    print("\n[12b/13] GHOST BLOG UPDATE")
    try:
        import json as _json
        blog_path = PROJECT_ROOT / "docs" / "blog" / "blog_entries.json"
        entries = []
        if blog_path.exists():
            with open(blog_path) as bf:
                entries = _json.load(bf)

        # Determine period based on current hour (UTC)
        from datetime import datetime as _dtm
        _h = _dtm.utcnow().hour
        _period = "morning" if _h < 14 else ("midday" if _h < 20 else "evening")
        _entry_key = f"{date}-{_period}"

        # Don't duplicate entries for the same period
        if not any(e.get("entry_key") == _entry_key for e in entries):
            # Pick a chart ticker — prefer gold pick if available
            chart_ticker = ""
            if momentum_picks and momentum_picks.get("picks"):
                chart_ticker = momentum_picks["picks"][0]["ticker"]
            elif scanner_signals:
                chart_ticker = scanner_signals[0]["symbol"]

            entries.append({
                "date": date,
                "entry_key": _entry_key,
                "period": _period,
                "ghost_log": ghost_log,
                "suggestions": ghost_suggestions,
                "commits": len([l for l in subprocess.run(
                    ["git", "log", "--since=7 days ago", "--oneline"],
                    cwd=str(PROJECT_ROOT), capture_output=True, text=True
                ).stdout.strip().split("\n") if l.strip()]),
                "files_changed": len(set(l.strip() for l in subprocess.run(
                    ["git", "log", "--since=7 days ago", "--name-only", "--pretty=format:"],
                    cwd=str(PROJECT_ROOT), capture_output=True, text=True
                ).stdout.strip().split("\n") if l.strip())),
                "chart_ticker": chart_ticker,
            })

            with open(blog_path, "w") as bf:
                _json.dump(entries, bf, indent=2)
            print(f"  ✓ Blog entry added for {_entry_key} (chart: {chart_ticker})")
        else:
            print(f"  ✓ Blog entry already exists for {_entry_key}")
    except Exception as e:
        print(f"  [WARN] Blog update failed: {e}")

    # ── Stage 13: Git Push ──
    if not dry_run:
        print("\n[13/14] GIT PUSH")
        print("  Committing to Git...")
        try:
            subprocess.run(["git", "add", "docs/", "dossier/persistence/", "landing/blog/"],
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

    # ── Stage 14: Substack Draft ──
    if not dry_run:
        print("\n[14/14] SUBSTACK DRAFT")
        try:
            from substack_dossier import build_dossier_doc, SubstackClient
            client = SubstackClient()
            if client.authenticate():
                title, subtitle, doc = build_dossier_doc(date, client=client)
                result = client.create_draft(title, subtitle, doc)
                if result:
                    draft_id = result.get("id")
                    print(f"  ✓ Substack draft created! Edit: https://{client.pub}/publish/post/{draft_id}")
                else:
                    print("  [WARN] Substack draft creation failed")
            else:
                print("  [WARN] Substack auth failed — refresh SID")
        except Exception as e:
            print(f"  [WARN] Substack draft failed: {e}")

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
    if momentum_picks and momentum_picks.get("picks"):
        gold = momentum_picks["picks"][0]
        print(f"  🥇 GOLD PICK: {gold['ticker']} (Score: {gold['score']}/100)")
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
