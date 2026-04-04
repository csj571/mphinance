#!/usr/bin/env python3
"""
Leveraged ETF Daily Screener

Generates a daily graded list of 2x leveraged ETF opportunities.
Runs as part of the 5AM dossier pipeline. Outputs:
  - docs/leveraged-screener/daily.html  (self-contained page)
  - docs/leveraged-screener/daily.json  (API/widget consumption)

Grading:
  A = ADX >= 30 + below VWAP + rel_vol >= 1.5  (strongest trend + dip setup)
  B = ADX >= 25 + rel_vol >= 1.0               (solid trend)
  C = ADX >= 20                                 (moderate trend)
  D = Below thresholds                          (weak/avoid)

Usage:
    python -m dossier.data_sources.leveraged_daily_screener
    python -m dossier.data_sources.leveraged_daily_screener --dry-run
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure project root on path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def _compute_adx(highs, lows, closes, period=14):
    """Compute ADX from arrays of high, low, close prices."""
    if len(highs) < period * 2:
        return 0.0

    def _ema_val(data, p):
        if not data:
            return 0
        val = data[0]
        mult = 2.0 / (p + 1)
        for d in data[1:]:
            val = d * mult + val * (1 - mult)
        return val

    plus_dm = []
    minus_dm = []
    tr_list = []

    for i in range(1, len(highs)):
        up = highs[i] - highs[i - 1]
        down = lows[i - 1] - lows[i]
        plus_dm.append(up if (up > down and up > 0) else 0)
        minus_dm.append(down if (down > up and down > 0) else 0)
        tr_list.append(max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1])
        ))

    if len(tr_list) < period:
        return 0.0

    # Smoothed TR, +DM, -DM (Wilder's smoothing)
    atr = sum(tr_list[:period])
    plus = sum(plus_dm[:period])
    minus = sum(minus_dm[:period])

    dx_list = []
    for i in range(period, len(tr_list)):
        atr = atr - atr / period + tr_list[i]
        plus = plus - plus / period + plus_dm[i]
        minus = minus - minus / period + minus_dm[i]

        if atr == 0:
            continue
        plus_di = 100 * plus / atr
        minus_di = 100 * minus / atr
        if plus_di + minus_di == 0:
            continue
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        dx_list.append(dx)

    if not dx_list:
        return 0.0

    # ADX = EMA of DX
    adx = sum(dx_list[:period]) / period if len(dx_list) >= period else sum(dx_list) / len(dx_list)
    for i in range(period, len(dx_list)):
        adx = (adx * (period - 1) + dx_list[i]) / period

    return round(adx, 1)


def _compute_rsi(closes, period=14):
    """Compute RSI from close prices."""
    if len(closes) < period + 1:
        return 50.0
    gains = []
    losses = []
    for i in range(1, len(closes)):
        d = closes[i] - closes[i - 1]
        gains.append(max(0, d))
        losses.append(max(0, -d))
    avg_g = sum(gains[:period]) / period
    avg_l = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        avg_g = (avg_g * (period - 1) + gains[i]) / period
        avg_l = (avg_l * (period - 1) + losses[i]) / period
    if avg_l == 0:
        return 100.0
    rs = avg_g / avg_l
    return round(100 - (100 / (1 + rs)), 1)


def _grade(adx, rsi, rel_vol, below_vwap):
    """Assign A/B/C/D grade based on technicals."""
    if adx >= 30 and below_vwap and rel_vol >= 1.5:
        return "A"
    if adx >= 25 and rel_vol >= 1.0:
        return "B"
    if adx >= 20:
        return "C"
    return "D"


def generate_daily_screener(date_str: str = None, dry_run: bool = False):
    """Generate daily screener HTML + JSON."""
    import yfinance as yf
    from dossier.data_sources.leveraged_etf_map import (
        LEVERAGED_2X_MAP,
        get_best_2x_etf,
    )

    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")

    print(f"  Generating leveraged ETF screener for {date_str}...")

    # ── Step 1: Check SPY ADX regime ──
    try:
        spy_hist = yf.Ticker("SPY").history(period="3mo", interval="1h")
        if not spy_hist.empty and len(spy_hist) >= 30:
            spy_h = spy_hist["High"].tolist()[-60:]
            spy_l = spy_hist["Low"].tolist()[-60:]
            spy_c = spy_hist["Close"].tolist()[-60:]
            spy_adx = _compute_adx(spy_h, spy_l, spy_c)
        else:
            spy_adx = 25.0  # Default if data unavailable
    except Exception:
        spy_adx = 25.0

    is_trade_day = spy_adx >= 20.0
    no_trade_msg = ""
    if not is_trade_day:
        no_trade_msg = f"⚠️ SPY ADX is {spy_adx:.1f} (below 20) — market lacks directional conviction. Sit on hands today."

    # ── Step 2: Score all underlyings ──
    picks = []
    underlyings = list(LEVERAGED_2X_MAP.keys())
    print(f"    Scanning {len(underlyings)} underlyings...")

    # Batch download daily data
    try:
        import warnings
        warnings.filterwarnings("ignore")
        data = yf.download(underlyings, period="3mo", group_by="ticker", progress=False, threads=True)
    except Exception as e:
        print(f"    [ERR] Batch download failed: {e}")
        data = None

    for ticker in underlyings:
        try:
            if data is not None and ticker in data.columns.get_level_values(0):
                df = data[ticker].dropna()
            else:
                df = yf.Ticker(ticker).history(period="3mo")

            if df.empty or len(df) < 20:
                continue

            closes = df["Close"].tolist()
            highs = df["High"].tolist()
            lows = df["Low"].tolist()
            volumes = df["Volume"].tolist()

            # Compute signals
            adx = _compute_adx(highs, lows, closes)
            rsi = _compute_rsi(closes)

            # Relative volume (today vs 20d avg)
            avg_vol_20 = sum(volumes[-20:]) / 20 if len(volumes) >= 20 else sum(volumes) / len(volumes)
            today_vol = volumes[-1] if volumes else 0
            rel_vol = round(today_vol / avg_vol_20, 2) if avg_vol_20 > 0 else 0

            # Price vs VWAP approximation (use daily typical price as proxy for daily screener)
            # True intraday VWAP only available in real-time
            price = closes[-1]
            typical_price = (highs[-1] + lows[-1] + closes[-1]) / 3
            below_vwap = price < typical_price

            # Change
            prev_close = closes[-2] if len(closes) >= 2 else price
            change_pct = round(((price - prev_close) / prev_close) * 100, 2)

            # Grade
            grade = _grade(adx, rsi, rel_vol, below_vwap)

            # Get best 2x ETF
            best_etf = get_best_2x_etf(ticker, direction="bull", use_cache=True)
            etf_ticker = best_etf["etf"] if best_etf else "—"
            etf_vol = best_etf.get("avg_volume", 0) if best_etf else 0

            picks.append({
                "underlying": ticker,
                "etf": etf_ticker,
                "price": round(price, 2),
                "change_pct": change_pct,
                "adx": adx,
                "rsi": rsi,
                "rel_vol": rel_vol,
                "below_vwap": below_vwap,
                "grade": grade,
                "etf_avg_volume": etf_vol,
            })
        except Exception as e:
            continue

    # Sort: A first, then B, C, D. Within grade, sort by ADX descending
    grade_order = {"A": 0, "B": 1, "C": 2, "D": 3}
    picks.sort(key=lambda x: (grade_order.get(x["grade"], 9), -x["adx"]))

    top_picks = [p for p in picks if p["grade"] in ("A", "B")][:5]

    print(f"    Graded: A={sum(1 for p in picks if p['grade']=='A')}, "
          f"B={sum(1 for p in picks if p['grade']=='B')}, "
          f"C={sum(1 for p in picks if p['grade']=='C')}, "
          f"D={sum(1 for p in picks if p['grade']=='D')}")

    # ── Step 3: Write JSON ──
    output_dir = PROJECT_ROOT / "docs" / "leveraged-screener"
    output_dir.mkdir(parents=True, exist_ok=True)

    result = {
        "date": date_str,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "spy_adx": spy_adx,
        "is_trade_day": is_trade_day,
        "no_trade_message": no_trade_msg,
        "top_picks": top_picks,
        "all_picks": picks,
        "summary": {
            "total_scanned": len(picks),
            "grade_a": sum(1 for p in picks if p["grade"] == "A"),
            "grade_b": sum(1 for p in picks if p["grade"] == "B"),
            "grade_c": sum(1 for p in picks if p["grade"] == "C"),
            "grade_d": sum(1 for p in picks if p["grade"] == "D"),
        },
    }

    json_path = output_dir / "daily.json"
    with open(json_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"    ✓ JSON: {json_path}")

    # ── Step 4: Write HTML ──
    html = _render_daily_html(result)
    html_path = output_dir / "daily.html"
    with open(html_path, "w") as f:
        f.write(html)
    print(f"    ✓ HTML: {html_path} ({len(html):,} bytes)")

    return result


def _render_daily_html(data: dict) -> str:
    """Render the daily screener as a self-contained HTML page."""
    date = data["date"]
    spy_adx = data["spy_adx"]
    is_trade = data["is_trade_day"]
    no_trade = data["no_trade_message"]
    picks = data["all_picks"]
    top = data["top_picks"]
    summary = data["summary"]

    grade_colors = {
        "A": "#00ff41",
        "B": "#00d4ff",
        "C": "#f0b400",
        "D": "#555",
    }

    # Build top picks section
    top_html = ""
    if is_trade and top:
        cards = ""
        for i, p in enumerate(top[:3]):
            gc = grade_colors[p["grade"]]
            chg_class = "positive" if p["change_pct"] >= 0 else "negative"
            chg_sign = "+" if p["change_pct"] >= 0 else ""
            vwap_str = "Below VWAP ✓" if p["below_vwap"] else "Above VWAP"
            cards += f'''
        <div class="pick-card" style="border-left: 3px solid {gc}">
          <div class="pick-rank">#{i+1}</div>
          <div class="pick-ticker">{p["underlying"]}</div>
          <div class="pick-etf">→ {p["etf"]}</div>
          <div class="pick-meta">
            <span>ADX {p["adx"]}</span>
            <span>RSI {p["rsi"]}</span>
            <span class="{chg_class}">{chg_sign}{p["change_pct"]}%</span>
          </div>
          <div class="pick-grade" style="color:{gc}">{p["grade"]}</div>
          <div class="pick-vwap">{vwap_str}</div>
        </div>'''
        top_html = f'''
    <div class="top-picks">
      <div class="section-title">🏆 Today's Top Picks</div>
      <div class="picks-grid">{cards}
      </div>
    </div>'''
    elif not is_trade:
        top_html = f'''
    <div class="no-trade-box">
      <div class="no-trade-icon">⚠️</div>
      <div class="no-trade-text">{no_trade}</div>
      <div class="no-trade-sub">The VWAP Reclaim strategy requires SPY ADX ≥ 20 for directional conviction. Today does not qualify.</div>
    </div>'''

    # Build table rows
    rows = ""
    for p in picks:
        gc = grade_colors[p["grade"]]
        chg_class = "positive" if p["change_pct"] >= 0 else "negative"
        chg_sign = "+" if p["change_pct"] >= 0 else ""
        vwap_icon = "🔽" if p["below_vwap"] else "🔼"
        vol_class = "positive" if p["rel_vol"] >= 1.5 else "neutral" if p["rel_vol"] >= 1.0 else ""

        rows += f'''
      <tr>
        <td><span class="grade-badge" style="background:{gc}">{p["grade"]}</span></td>
        <td class="ticker-cell"><a href="https://www.tradingview.com/symbols/{p["underlying"]}" target="_blank">{p["underlying"]}</a></td>
        <td class="etf-cell">{p["etf"]}</td>
        <td>${p["price"]:,.2f}</td>
        <td class="{chg_class}">{chg_sign}{p["change_pct"]}%</td>
        <td style="font-weight:600">{p["adx"]}</td>
        <td>{p["rsi"]}</td>
        <td class="{vol_class}">{p["rel_vol"]}x</td>
        <td>{vwap_icon}</td>
      </tr>'''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Ghost Alpha | Daily Leveraged ETF Screener — {date}</title>
<meta name="description" content="Daily graded leveraged ETF screener. A/B/C/D ranked by ADX, RSI, VWAP position, and relative volume.">
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;700&family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
<style>
:root {{
  --bg: #0a0a0f; --bg2: #111118; --bg3: #1a1a24;
  --border: #2a2a3a; --text: #e0e0e8; --text2: #8888a0;
  --green: #00ff41; --red: #ff4444; --gold: #f0b400; --cyan: #00d4ff;
}}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text); }}
.header {{ padding: 30px 24px 20px; text-align: center; border-bottom: 1px solid var(--border); }}
.header h1 {{
  font-family: 'JetBrains Mono', monospace; font-size: 1.2em;
  text-transform: uppercase; letter-spacing: 3px; color: var(--cyan);
}}
.header .date {{ font-family: 'JetBrains Mono', monospace; font-size: 0.75em; color: var(--text2); margin-top: 4px; }}
.header .spy-badge {{
  display: inline-block; margin-top: 8px; padding: 4px 12px; border-radius: 4px;
  font-family: 'JetBrains Mono', monospace; font-size: 0.7em;
  background: {"rgba(0,255,65,0.1)" if is_trade else "rgba(255,68,68,0.1)"};
  border: 1px solid {"var(--green)" if is_trade else "var(--red)"};
  color: {"var(--green)" if is_trade else "var(--red)"};
}}
.nav {{ display: flex; gap: 12px; justify-content: center; margin-top: 12px; }}
.nav a {{
  font-family: 'JetBrains Mono', monospace; font-size: 0.65em; color: var(--text2);
  text-decoration: none; padding: 3px 10px; border: 1px solid var(--border); border-radius: 3px;
}}
.nav a:hover {{ border-color: var(--green); color: var(--green); }}
.container {{ max-width: 1100px; margin: 0 auto; padding: 20px 16px; }}
.summary-grid {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; margin: 16px 0; }}
.summary-card {{
  background: var(--bg2); border: 1px solid var(--border); border-radius: 6px;
  padding: 12px; text-align: center;
}}
.summary-card .label {{ font-size: 0.6em; color: var(--text2); text-transform: uppercase; letter-spacing: 1px; }}
.summary-card .value {{ font-family: 'JetBrains Mono', monospace; font-size: 1.4em; font-weight: 700; }}

.top-picks {{ margin: 20px 0; }}
.section-title {{ font-family: 'JetBrains Mono', monospace; font-size: 0.75em; color: var(--cyan); text-transform: uppercase; letter-spacing: 2px; margin-bottom: 12px; }}
.picks-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; }}
.pick-card {{
  background: var(--bg2); border: 1px solid var(--border); border-radius: 6px; padding: 16px; position: relative;
}}
.pick-rank {{ font-family: 'JetBrains Mono', monospace; font-size: 0.6em; color: var(--text2); }}
.pick-ticker {{ font-size: 1.4em; font-weight: 700; color: var(--text); }}
.pick-etf {{ font-family: 'JetBrains Mono', monospace; font-size: 0.75em; color: var(--cyan); margin: 4px 0; }}
.pick-meta {{ display: flex; gap: 8px; font-size: 0.7em; color: var(--text2); }}
.pick-grade {{ position: absolute; top: 12px; right: 14px; font-family: 'JetBrains Mono', monospace; font-size: 1.6em; font-weight: 700; }}
.pick-vwap {{ font-size: 0.65em; color: var(--green); margin-top: 4px; }}

.no-trade-box {{
  background: rgba(255,68,68,0.05); border: 1px solid rgba(255,68,68,0.3);
  border-radius: 8px; padding: 30px; text-align: center; margin: 20px 0;
}}
.no-trade-icon {{ font-size: 2em; margin-bottom: 8px; }}
.no-trade-text {{ font-size: 1em; font-weight: 600; color: var(--red); }}
.no-trade-sub {{ font-size: 0.8em; color: var(--text2); margin-top: 8px; }}

table {{ width: 100%; border-collapse: collapse; font-size: 0.8em; margin-top: 20px; }}
th {{ text-align: left; padding: 10px 8px; border-bottom: 2px solid var(--border); color: var(--text2);
  font-family: 'JetBrains Mono', monospace; font-size: 0.7em; text-transform: uppercase; letter-spacing: 1px; }}
td {{ padding: 8px; border-bottom: 1px solid rgba(42,42,58,0.4); }}
tr:hover {{ background: rgba(0,212,255,0.03); }}
.grade-badge {{
  display: inline-block; padding: 2px 8px; border-radius: 3px;
  font-family: 'JetBrains Mono', monospace; font-size: 0.8em; font-weight: 700;
  color: #000; min-width: 24px; text-align: center;
}}
.ticker-cell a {{ color: var(--gold); text-decoration: none; font-weight: 600; }}
.ticker-cell a:hover {{ color: var(--green); }}
.etf-cell {{ font-family: 'JetBrains Mono', monospace; color: var(--cyan); font-size: 0.85em; }}
.positive {{ color: var(--green); }}
.negative {{ color: var(--red); }}
.neutral {{ color: var(--gold); }}
.footer {{ text-align: center; padding: 30px; border-top: 1px solid var(--border); margin-top: 30px; }}
.footer p {{ font-family: 'JetBrains Mono', monospace; font-size: 0.6em; color: var(--text2); }}
.footer a {{ color: var(--cyan); text-decoration: none; }}

/* grading legend */
.legend {{ display: flex; gap: 16px; justify-content: center; margin: 12px 0; flex-wrap: wrap; }}
.legend-item {{ display: flex; align-items: center; gap: 4px; font-size: 0.7em; color: var(--text2); }}

@media (max-width: 600px) {{
  .summary-grid {{ grid-template-columns: repeat(3, 1fr); }}
  table {{ font-size: 0.7em; }}
}}
</style>
</head>
<body>

<div class="header">
  <h1>☢️ Leveraged ETF Daily Screener</h1>
  <div class="date">{date} · Ghost Alpha VWAP Reclaim Strategy</div>
  <div class="spy-badge">SPY ADX: {spy_adx:.1f} {"— TRADE DAY ✓" if is_trade else "— NO TRADE ✗"}</div>
  <div class="nav">
    <a href="index.html">📊 Backtest Results</a>
    <a href="https://mphinance.github.io/mphinance/">📑 Dossier</a>
    <a href="https://mphinance.com">🏠 Home</a>
  </div>
</div>

<div class="container">

  <div class="summary-grid">
    <div class="summary-card"><div class="label">Scanned</div><div class="value" style="color:var(--text)">{summary["total_scanned"]}</div></div>
    <div class="summary-card"><div class="label">Grade A</div><div class="value" style="color:#00ff41">{summary["grade_a"]}</div></div>
    <div class="summary-card"><div class="label">Grade B</div><div class="value" style="color:#00d4ff">{summary["grade_b"]}</div></div>
    <div class="summary-card"><div class="label">Grade C</div><div class="value" style="color:#f0b400">{summary["grade_c"]}</div></div>
    <div class="summary-card"><div class="label">Grade D</div><div class="value" style="color:#555">{summary["grade_d"]}</div></div>
  </div>

  <div class="legend">
    <div class="legend-item"><span class="grade-badge" style="background:#00ff41">A</span> ADX≥30 + Below VWAP + Vol≥1.5x</div>
    <div class="legend-item"><span class="grade-badge" style="background:#00d4ff">B</span> ADX≥25 + Vol≥1.0x</div>
    <div class="legend-item"><span class="grade-badge" style="background:#f0b400">C</span> ADX≥20</div>
    <div class="legend-item"><span class="grade-badge" style="background:#555">D</span> Below thresholds</div>
  </div>

  {top_html}

  <div class="section-title" style="margin-top:24px">📋 Full Universe ({len(picks)} ETF pairs)</div>

  <table>
    <thead>
      <tr>
        <th>Grade</th>
        <th>Underlying</th>
        <th>2x ETF</th>
        <th>Price</th>
        <th>Change</th>
        <th>ADX(14)</th>
        <th>RSI(14)</th>
        <th>Rel Vol</th>
        <th>VWAP</th>
      </tr>
    </thead>
    <tbody>{rows}
    </tbody>
  </table>
</div>

<div class="footer">
  <p>Generated {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")} · <a href="https://mphinance.com">Momentum Phinance</a></p>
  <p style="margin-top:4px; font-size:0.5em; color:#444">Not financial advice. Past performance ≠ future results.</p>
</div>

</body>
</html>'''


def get_top_pick(date_str: str = None) -> dict | None:
    """Get today's #1 leveraged ETF pick for the dossier report.
    Reads from daily.json if it exists, otherwise generates fresh."""
    json_path = PROJECT_ROOT / "docs" / "leveraged-screener" / "daily.json"

    if json_path.exists():
        with open(json_path) as f:
            data = json.load(f)
        if data.get("top_picks"):
            return data["top_picks"][0]
        return None

    # Generate fresh
    result = generate_daily_screener(date_str)
    if result.get("top_picks"):
        return result["top_picks"][0]
    return None


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Leveraged ETF Daily Screener")
    parser.add_argument("--date", type=str, help="Date (YYYY-MM-DD)")
    parser.add_argument("--dry-run", action="store_true", help="Print results only")
    args = parser.parse_args()

    result = generate_daily_screener(date_str=args.date, dry_run=args.dry_run)
    print(f"\n  Summary: {result['summary']}")
    print(f"  SPY ADX: {result['spy_adx']:.1f} ({'TRADE' if result['is_trade_day'] else 'NO TRADE'})")
    if result["top_picks"]:
        print(f"  Top pick: {result['top_picks'][0]['underlying']} → {result['top_picks'][0]['etf']} (Grade {result['top_picks'][0]['grade']})")
