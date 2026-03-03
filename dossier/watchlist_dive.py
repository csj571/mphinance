"""
Watchlist Deep Dive Generator

Reads tickers from watchlist.txt, generates a full deep-dive markdown
report for each one using yfinance data + Gemini AI narrative.

Usage:
    python -m dossier.watchlist_dive           # all tickers in watchlist.txt
    python -m dossier.watchlist_dive PLTR NVDA  # specific tickers
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

import yfinance as yf
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dossier.config import GEMINI_API_KEY, AI_MODEL
from dossier.data_sources.ticker_enrichment import (
    _sma, _ema, _rsi, _macd, _safe, _fmt_num,
    _tradingview_summary, _intrinsic_value, _fetch_news,
)

OUTPUT_DIR = PROJECT_ROOT / "docs" / "watchlist"
WATCHLIST_FILE = PROJECT_ROOT / "watchlist.txt"


def _read_watchlist() -> list[str]:
    """Read tickers from watchlist.txt, skip comments and blanks."""
    if not WATCHLIST_FILE.exists():
        return []
    tickers = []
    for line in WATCHLIST_FILE.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            tickers.append(line.upper())
    return list(dict.fromkeys(tickers))  # dedupe, preserve order


def _gemini_deep_dive(ticker: str, data: dict) -> str:
    """Ask Gemini to write a full deep-dive narrative in Sam's voice."""
    if not GEMINI_API_KEY:
        return ""

    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(AI_MODEL)
    except Exception as e:
        print(f"    [WARN] Gemini init: {e}")
        return ""

    prompt = f"""You are Sam the Quant Ghost — a sharp, witty quantitative analyst who writes 
deep-dive stock reports that retail traders love. Write a FULL deep-dive report for {ticker} 
using the data below. Use this exact structure:

## [{ticker}] Deep Dive: [Create a catchy thesis title]
**Date:** {data['date']}
**Price:** ~${data['price']} | **Verdict:** [Your verdict]

[1-2 sentence hook]

### The Core Thesis
[What the market sees vs reality. 2-3 paragraphs.]

### 📊 The Numbers You Need
[Revenue, margins, growth rates. Use the fundamentals data.]

### 🚀 The Bull Case
[3-4 catalysts with specifics]

### ⚠️ The Bear Case: Risks
[2-3 real risks]

### 📉 The Technicals
[Use the technical data below — EMAs, RSI, support/resistance, pivots]

### 📝 Trading Playbook
**Scenario A — The Breakout (Bullish):**
**Scenario B — The Dip Buy (Preferred):**  
**Scenario C — Trend Failure (Hedge):**

### 🏁 Final Verdict
[One-liner + price target]

---

DATA:
- Price: ${data['price']}, Change: {data['change_pct']}%
- Market Cap: {data['market_cap']}, Beta: {data['beta']}
- 52W Range: {data['range_52w']}
- Sector: {data['sector']}, Industry: {data['industry']}
- Revenue Growth: {data['rev_growth']}%, Profit Margin: {data['profit_margin']}%
- P/E: {data['pe']}, Forward P/E: {data['fwd_pe']}
- EMA Stack: {data['ema_stack']} (8: ${data['ema_8']}, 21: ${data['ema_21']}, 34: ${data['ema_34']})
- SMA 50: ${data['sma_50']}, SMA 200: ${data['sma_200']}
- Trend: {data['trend']} ({data['crossover']})
- RSI(14): {data['rsi']}, ADX: {data['adx']}
- Pivots: R2=${data['r2']}, R1=${data['r1']}, PP=${data['pivot']}, S1=${data['s1']}, S2=${data['s2']}
- ATR: {data['atr']}, Rel Vol: {data['rel_vol']}x
- Analyst Target: ${data['analyst_target']}
- TradingView: {data['tv_rec']}
- Valuation: {data['val_status']} (Gap: {data['val_gap']}%), Target: ${data['val_target']}

Write the full report now. Be direct, opinionated, data-driven. Use markdown formatting.
Reference specific price levels and numbers. No generic filler.
Sign off: "— Ghost out. 👻"
"""

    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"    [WARN] Gemini failed: {e}")
        return ""


def generate_deep_dive(ticker: str) -> str:
    """Generate a full deep-dive markdown for a single ticker."""
    print(f"  📊 {ticker}...")
    stock = yf.Ticker(ticker)

    try:
        df = stock.history(period="6mo")
        if df.empty:
            print(f"    [SKIP] No data")
            return ""
    except Exception as e:
        print(f"    [ERR] {e}")
        return ""

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    price = float(close.iloc[-1])

    info = {}
    try:
        info = stock.info or {}
    except Exception:
        pass

    est = ZoneInfo("America/New_York")
    date_str = datetime.now(est).strftime("%Y-%m-%d")

    # ── Technicals ──
    ema_8 = _safe(_ema(close, 8).iloc[-1])
    ema_21 = _safe(_ema(close, 21).iloc[-1])
    ema_34 = _safe(_ema(close, 34).iloc[-1])
    ema_55 = _safe(_ema(close, 55).iloc[-1])
    ema_89 = _safe(_ema(close, 89).iloc[-1])
    sma_50 = _safe(_sma(close, 50).iloc[-1])
    sma_200 = _safe(_sma(close, 200).iloc[-1])
    rsi_val = _safe(_rsi(close).iloc[-1])
    _, _, macd_hist = _macd(close)

    # EMA Stack
    e8, e21, e34, e55, e89 = ema_8, ema_21, ema_34, ema_55, ema_89
    if all([e8, e21, e34, e55, e89]):
        if e8 > e21 > e34 > e55 > e89:
            ema_stack = "FULL BULLISH"
        elif e8 > e21 > e34:
            ema_stack = "PARTIAL BULLISH"
        elif e89 > e55 > e34 > e21 > e8:
            ema_stack = "FULL BEARISH"
        else:
            ema_stack = "TANGLED"
    else:
        ema_stack = "UNKNOWN"

    # Pivots
    prev_h = float(high.iloc[-2]) if len(high) >= 2 else float(high.iloc[-1])
    prev_l = float(low.iloc[-2]) if len(low) >= 2 else float(low.iloc[-1])
    prev_c = float(close.iloc[-2]) if len(close) >= 2 else price
    pivot = round((prev_h + prev_l + prev_c) / 3, 2)
    r1 = round(2 * pivot - prev_l, 2)
    r2 = round(pivot + (prev_h - prev_l), 2)
    s1 = round(2 * pivot - prev_h, 2)
    s2 = round(pivot - (prev_h - prev_l), 2)

    # ATR
    tr = pd.concat([high - low, abs(high - close.shift()), abs(low - close.shift())], axis=1).max(axis=1)
    atr_val = _safe(tr.rolling(14).mean().iloc[-1])

    # ADX (simplified)
    dm_plus = high.diff()
    dm_minus = -low.diff()
    dm_plus = dm_plus.where((dm_plus > dm_minus) & (dm_plus > 0), 0)
    dm_minus = dm_minus.where((dm_minus > dm_plus) & (dm_minus > 0), 0)
    atr_14 = tr.rolling(14).mean()
    di_plus = 100 * dm_plus.rolling(14).mean() / atr_14
    di_minus = 100 * dm_minus.rolling(14).mean() / atr_14
    dx = 100 * abs(di_plus - di_minus) / (di_plus + di_minus)
    adx = _safe(dx.rolling(14).mean().iloc[-1])

    # Volume
    vol_avg = df["Volume"].rolling(20).mean()
    rel_vol = round(float(df["Volume"].iloc[-1] / vol_avg.iloc[-1]), 2) if vol_avg.iloc[-1] > 0 else 1.0

    trend = "Bullish" if (sma_50 or 0) > (sma_200 or 0) else "Bearish"
    crossover = "Golden Cross" if (sma_50 or 0) > (sma_200 or 0) else "Death Cross"

    # Valuation
    valuation = _intrinsic_value(info, price)

    # TradingView
    tv = _tradingview_summary(ticker, info.get("exchange", ""))
    tv_rec = tv.get("summary", {}).get("RECOMMENDATION", "N/A") if tv else "N/A"

    change_pct = round((price - float(close.iloc[-2])) / float(close.iloc[-2]) * 100, 2) if len(close) >= 2 else 0

    data = {
        "date": date_str, "price": round(price, 2), "change_pct": change_pct,
        "market_cap": _fmt_num(info.get("marketCap")),
        "beta": _safe(info.get("beta")),
        "range_52w": f"{round(float(low.min()), 2)} - {round(float(high.max()), 2)}",
        "sector": info.get("sector", "N/A"), "industry": info.get("industry", "N/A"),
        "rev_growth": round((info.get("revenueGrowth", 0) or 0) * 100, 1),
        "profit_margin": round((info.get("profitMargins", 0) or 0) * 100, 1),
        "pe": _safe(info.get("trailingPE")), "fwd_pe": _safe(info.get("forwardPE")),
        "ema_stack": ema_stack, "ema_8": ema_8, "ema_21": ema_21, "ema_34": ema_34,
        "sma_50": sma_50, "sma_200": sma_200,
        "trend": trend, "crossover": crossover,
        "rsi": rsi_val, "adx": adx,
        "pivot": pivot, "r1": r1, "r2": r2, "s1": s1, "s2": s2,
        "atr": atr_val, "rel_vol": rel_vol,
        "analyst_target": _safe(info.get("targetMeanPrice")),
        "tv_rec": tv_rec,
        "val_status": valuation.get("status", "N/A"),
        "val_gap": valuation.get("gap_pct", 0),
        "val_target": valuation.get("target_price", "N/A"),
    }

    # ── Gemini AI Deep Dive ──
    ai_content = _gemini_deep_dive(ticker, data)

    if ai_content:
        md_content = ai_content
    else:
        # Fallback: structured template with raw data
        md_content = f"""## [{ticker}] Deep Dive
**Date:** {date_str} | **Price:** ${data['price']} ({data['change_pct']:+.2f}%)

### Market Snapshot
| Metric | Value |
|--------|-------|
| Market Cap | {data['market_cap']} |
| Sector | {data['sector']} |
| Beta | {data['beta']} |
| 52W Range | {data['range_52w']} |
| Analyst Target | ${data['analyst_target']} |
| TradingView | {data['tv_rec']} |

### Technicals
- **EMA Stack:** {data['ema_stack']}
- **Trend:** {data['trend']} ({data['crossover']})
- EMAs: 8=${data['ema_8']}, 21=${data['ema_21']}, 34=${data['ema_34']}
- SMA 50=${data['sma_50']}, SMA 200=${data['sma_200']}
- RSI(14): {data['rsi']} | ADX: {data['adx']}
- Pivots: R2=${data['r2']}, R1=${data['r1']}, PP=${data['pivot']}, S1=${data['s1']}, S2=${data['s2']}
- ATR: {data['atr']} | Rel Vol: {data['rel_vol']}x

### Valuation
- **Status:** {data['val_status']} (Gap: {data['val_gap']:+.1f}%)
- **Target:** ${data['val_target']}

### Fundamentals
- Revenue Growth: {data['rev_growth']}%
- Profit Margin: {data['profit_margin']}%
- P/E: {data['pe']} | Forward P/E: {data['fwd_pe']}

---
*Generated by Ghost Alpha Dossier // {date_str}*
"""

    # ── Write Output ──
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    md_path = OUTPUT_DIR / f"{ticker}_deep_dive.md"
    with open(md_path, "w") as f:
        f.write(md_content)

    # Also write JSON for API consumption
    json_path = OUTPUT_DIR / f"{ticker}_deep_dive.json"
    with open(json_path, "w") as f:
        json.dump(data, f, indent=2, default=str)

    # Render as styled HTML page
    html_path = OUTPUT_DIR / f"{ticker}_deep_dive.html"
    _render_html(ticker, md_content, data, html_path)

    print(f"    ✓ {md_path.name} + {html_path.name}")
    return str(md_path)


def _render_html(ticker: str, md_content: str, data: dict, output_path: Path):
    """Convert markdown deep dive to a styled HTML page."""
    import re

    # Simple markdown → HTML conversion
    html_body = md_content

    # Headers
    html_body = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html_body, flags=re.MULTILINE)
    html_body = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html_body, flags=re.MULTILINE)

    # Bold
    html_body = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html_body)
    # Italic
    html_body = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html_body)

    # Unordered lists
    lines = html_body.split('\n')
    in_list = False
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if re.match(r'^[\-\*]\s+', stripped):
            if not in_list:
                new_lines.append('<ul>')
                in_list = True
            item = re.sub(r'^[\-\*]\s+', '', stripped)
            new_lines.append(f'<li>{item}</li>')
        elif re.match(r'^\d+\.\s+', stripped):
            if not in_list:
                new_lines.append('<ol>')
                in_list = True
            item = re.sub(r'^\d+\.\s+', '', stripped)
            new_lines.append(f'<li>{item}</li>')
        else:
            if in_list:
                new_lines.append('</ul>' if any('<ul>' in l for l in new_lines[-20:]) else '</ol>')
                in_list = False
            if stripped == '---':
                new_lines.append('<hr>')
            elif stripped == '':
                new_lines.append('')
            elif not stripped.startswith('<h'):
                new_lines.append(f'<p>{stripped}</p>' if stripped else '')
            else:
                new_lines.append(stripped)
    if in_list:
        new_lines.append('</ul>')
    html_body = '\n'.join(new_lines)

    # Tables
    html_body = re.sub(
        r'<p>\|(.+)\|</p>',
        lambda m: '<tr>' + ''.join(f'<td>{c.strip()}</td>' for c in m.group(1).split('|')) + '</tr>',
        html_body
    )
    html_body = re.sub(r'<tr><td>-+</td>.*?</tr>', '', html_body)
    html_body = re.sub(r'(<tr>.*?</tr>\s*)+', lambda m: '<table>' + m.group(0) + '</table>', html_body, flags=re.DOTALL)

    est = ZoneInfo("America/New_York")
    generated_at = datetime.now(est).strftime("%Y-%m-%d %I:%M %p EST")

    change_class = "text-neon-green" if data.get("change_pct", 0) >= 0 else "text-neon-red"
    trend_class = "text-neon-green" if data.get("trend") == "Bullish" else "text-neon-red"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{ticker} Deep Dive | ALPHA.DOSSIER</title>
    <meta name="description" content="Full deep-dive analysis for {ticker} — thesis, technicals, bull/bear case, trading playbook.">
    <link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {{
            theme: {{
                extend: {{
                    fontFamily: {{ 'mono': ['"JetBrains Mono"', 'monospace'], 'tech': ['"Share Tech Mono"', 'monospace'] }},
                    colors: {{ 'neon-green': '#00ff41', 'neon-red': '#ff3e3e', 'neon-blue': '#00f3ff', 'neon-amber': '#ffb000', 'hud-black': '#0a0a0a' }}
                }}
            }}
        }}
    </script>
    <style>
        body {{ background-color: #050505; color: #e0e0e0; font-family: 'JetBrains Mono', monospace;
            background-image: linear-gradient(rgba(18,16,16,0) 50%, rgba(0,0,0,0.25) 50%),
            linear-gradient(90deg, rgba(255,0,0,0.06), rgba(0,255,0,0.02), rgba(0,0,255,0.06));
            background-size: 100% 2px, 3px 100%; }}
        .hud-panel {{ background: rgba(10,10,10,0.8); border: 1px solid #333; box-shadow: 0 0 10px rgba(0,0,0,0.5); backdrop-filter: blur(4px); }}
        .content h2 {{ font-size: 1.5rem; font-weight: 900; color: #fff; margin: 2rem 0 1rem; padding-bottom: 0.5rem; border-bottom: 2px solid #333;
            font-family: 'Share Tech Mono', monospace; text-transform: uppercase; letter-spacing: 0.05em; }}
        .content h3 {{ font-size: 1.1rem; font-weight: 700; color: #ffb000; margin: 1.5rem 0 0.75rem; letter-spacing: 0.03em; }}
        .content p {{ color: #c0c0c0; line-height: 1.8; margin: 0.5rem 0; font-size: 0.85rem; }}
        .content strong {{ color: #ffffff; }}
        .content em {{ color: #00f3ff; font-style: normal; }}
        .content ul, .content ol {{ margin: 0.5rem 0 0.5rem 1.5rem; color: #c0c0c0; font-size: 0.85rem; line-height: 2; }}
        .content li {{ margin: 0.3rem 0; }}
        .content hr {{ border: none; border-top: 1px solid #333; margin: 2rem 0; }}
        .content table {{ width: 100%; border-collapse: collapse; margin: 1rem 0; font-size: 0.8rem; }}
        .content td {{ padding: 0.5rem 0.75rem; border: 1px solid #333; color: #c0c0c0; }}
        .content tr:first-child td {{ font-weight: bold; color: #888; background: rgba(255,255,255,0.03); }}
    </style>
</head>
<body class="min-h-screen p-4 md:p-8">
    <div class="max-w-4xl mx-auto space-y-6">

        <!-- NAV BAR -->
        <div class="flex justify-between items-center">
            <a href="../index.html" class="font-tech text-neon-green text-sm tracking-widest hover:text-white transition-colors">← ALPHA://HUD</a>
            <div class="flex gap-3">
                <a href="{ticker}_deep_dive.md" download class="px-2 py-1 bg-gray-800 text-[10px] text-gray-400 border border-gray-700 hover:text-white hover:border-gray-500 transition-colors uppercase font-mono rounded">↓ RAW MD</a>
                <a href="{ticker}_deep_dive.json" class="px-2 py-1 bg-gray-800 text-[10px] text-gray-400 border border-gray-700 hover:text-white hover:border-gray-500 transition-colors uppercase font-mono rounded">↓ JSON</a>
            </div>
        </div>

        <!-- HEADER -->
        <div class="hud-panel p-6 rounded-sm border-l-4 border-neon-amber">
            <div class="flex justify-between items-center">
                <div>
                    <h1 class="text-2xl md:text-3xl font-black font-tech tracking-widest text-white">
                        <a href="https://www.tradingview.com/symbols/{ticker}/" target="_blank" class="hover:text-neon-blue transition-colors">{ticker}</a>
                        <span class="text-neon-amber ml-2">DEEP.DIVE</span>
                    </h1>
                    <p class="text-[10px] text-gray-500 uppercase tracking-[0.3em] mt-1">
                        {data.get('sector', 'N/A')} · {data.get('industry', 'N/A')}
                    </p>
                </div>
                <div class="text-right space-y-1">
                    <div class="text-2xl font-bold font-mono text-white">${data.get('price', 'N/A')}</div>
                    <div class="{change_class} text-sm font-mono">{data.get('change_pct', 0):+.2f}%</div>
                </div>
            </div>

            <!-- Quick Stats Bar -->
            <div class="flex flex-wrap gap-4 mt-4 pt-3 border-t border-gray-800 text-[10px] font-mono">
                <span class="text-gray-500">MCAP <span class="text-white">{data.get('market_cap', 'N/A')}</span></span>
                <span class="text-gray-500">EMA <span class="{trend_class}">{data.get('ema_stack', 'N/A')}</span></span>
                <span class="text-gray-500">RSI <span class="text-white">{data.get('rsi', 'N/A')}</span></span>
                <span class="text-gray-500">ADX <span class="text-white">{data.get('adx', 'N/A')}</span></span>
                <span class="text-gray-500">TV <span class="text-neon-blue">{data.get('tv_rec', 'N/A')}</span></span>
                <span class="text-gray-500">VAL <span class="{('text-neon-green' if 'UNDER' in str(data.get('val_status', '')) else 'text-neon-red')}">{data.get('val_status', 'N/A')}</span></span>
            </div>
        </div>

        <!-- CONTENT -->
        <div class="hud-panel p-6 md:p-8 rounded-sm content">
            {html_body}
        </div>

        <!-- FOOTER -->
        <div class="text-center py-4 space-y-1">
            <div class="text-[9px] text-gray-700 font-mono uppercase tracking-widest">
                Ghost Alpha Dossier // Watchlist Deep Dive // {generated_at}
            </div>
        </div>
    </div>
</body>
</html>"""

    with open(output_path, "w") as f:
        f.write(html)


def main():
    parser = argparse.ArgumentParser(description="Watchlist Deep Dive Generator")
    parser.add_argument("tickers", nargs="*", help="Specific tickers (overrides watchlist.txt)")
    args = parser.parse_args()

    tickers = args.tickers if args.tickers else _read_watchlist()
    if not tickers:
        print("No tickers in watchlist.txt and none provided. Add tickers to watchlist.txt!")
        return

    print(f"🔍 WATCHLIST DEEP DIVE — {len(tickers)} tickers")
    print("=" * 50)

    results = []
    for t in tickers:
        path = generate_deep_dive(t.upper())
        if path:
            results.append(path)

    print(f"\n✅ Generated {len(results)}/{len(tickers)} deep dives")
    print(f"   Output: {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
