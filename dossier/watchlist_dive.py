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

TICKER_DIR = PROJECT_ROOT / "docs" / "ticker"
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
    sma_20 = _safe(_sma(close, 20).iloc[-1])
    sma_50 = _safe(_sma(close, 50).iloc[-1])
    sma_100 = _safe(_sma(close, 100).iloc[-1])
    sma_200 = _safe(_sma(close, 200).iloc[-1])
    rsi_val = _safe(_rsi(close).iloc[-1])
    macd_line, macd_signal, macd_hist = _macd(close)
    macd_val = _safe(macd_line.iloc[-1])
    macd_sig = _safe(macd_signal.iloc[-1])
    macd_hist_val = _safe(macd_hist.iloc[-1])

    # Stochastic %K/%D
    low_14 = low.rolling(14).min()
    high_14 = high.rolling(14).max()
    stoch_k = _safe(((close.iloc[-1] - low_14.iloc[-1]) / (high_14.iloc[-1] - low_14.iloc[-1]) * 100) if (high_14.iloc[-1] - low_14.iloc[-1]) > 0 else 50)
    stoch_d = _safe(((close - low_14) / (high_14 - low_14) * 100).rolling(3).mean().iloc[-1])

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
    atr_20 = _safe(tr.rolling(20).mean().iloc[-1])

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

    # ── 52-Week Range + Position ──
    w52_low = round(float(low.min()), 2)
    w52_high = round(float(high.max()), 2)
    w52_pos = round((price - w52_low) / (w52_high - w52_low) * 100, 1) if w52_high > w52_low else 50.0

    # ── Fibonacci Retracements (52-week range) ──
    fib_range = w52_high - w52_low
    fib_618 = round(w52_high - fib_range * 0.618, 2)
    fib_500 = round(w52_high - fib_range * 0.500, 2)
    fib_382 = round(w52_high - fib_range * 0.382, 2)
    fib_236 = round(w52_high - fib_range * 0.236, 2)

    # ── Keltner Channels ──
    kelt_mid = sma_20 or price
    kelt_upper = round(kelt_mid + 2 * (atr_20 or 0), 2) if atr_20 else None
    kelt_lower = round(kelt_mid - 2 * (atr_20 or 0), 2) if atr_20 else None

    # ── Historical Volatility (close-to-close 30D) ──
    log_returns = np.log(close / close.shift(1)).dropna()
    hv_30 = round(float(log_returns.rolling(30).std().iloc[-1] * np.sqrt(252) * 100), 2) if len(log_returns) >= 30 else None

    # ── IV from options chain ──
    iv_current = None
    iv_rank = None
    iv_percentile = None
    try:
        opts = stock.options
        if opts:
            nearest_exp = opts[0]
            chain_data = stock.option_chain(nearest_exp)
            calls = chain_data.calls
            # ATM IV: closest strike to current price
            if not calls.empty and "impliedVolatility" in calls.columns:
                atm_idx = (calls["strike"] - price).abs().idxmin()
                iv_current = round(float(calls.loc[atm_idx, "impliedVolatility"]) * 100, 2)

            # IV Rank/Percentile: compare to range of IVs across all strikes
            all_ivs = pd.concat([calls.get("impliedVolatility", pd.Series()), chain_data.puts.get("impliedVolatility", pd.Series())]).dropna()
            if len(all_ivs) > 5 and iv_current:
                iv_min = float(all_ivs.min()) * 100
                iv_max = float(all_ivs.max()) * 100
                iv_rank = round((iv_current - iv_min) / (iv_max - iv_min) * 100, 1) if iv_max > iv_min else 50.0
                iv_percentile = round(float((all_ivs * 100 <= iv_current / 100).sum() / len(all_ivs) * 100), 1)
    except Exception:
        pass

    # ── Trend Signals (short/med/long) ──
    def _trend_signal(fast, slow):
        if fast is None or slow is None:
            return "N/A"
        return "↑ Bullish" if fast > slow else "↓ Bearish"

    trend_short = _trend_signal(ema_8, ema_21)
    trend_med = _trend_signal(ema_21, sma_50)
    trend_long = _trend_signal(sma_50, sma_200)

    # Valuation
    valuation = _intrinsic_value(info, price)

    # TradingView
    tv = _tradingview_summary(ticker, info.get("exchange", ""))
    tv_rec = tv.get("summary", {}).get("RECOMMENDATION", "N/A") if tv else "N/A"

    change_pct = round((price - float(close.iloc[-2])) / float(close.iloc[-2]) * 100, 2) if len(close) >= 2 else 0

    # ── VoPR Scanner Integration ──
    vopr_data = {}
    try:
        import sys as _sys
        _sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "VoPR"))
        from scanner.scanner import run_auto_scan
        vopr_results = run_auto_scan(ticker, min_dte=14, max_dte=50, top_n=2)
        if vopr_results:
            first = vopr_results[0]
            vopr_data = {
                "vrp_ratio": round(first.get("vrp_ratio", 0), 2),
                "vrp_flag": first.get("vrp_flag", False),
                "atm_iv": round(first.get("atm_iv", 0) * 100, 2),
                "realized_vol": round(hv_30 or 0, 2),
                "expected_move": first.get("expected_move", {}),
                "spot": first.get("spot", price),
                "expiry": first.get("expiry", ""),
                "dte": first.get("dte", 0),
                "keltner": first.get("keltner", {}),
            }
            # Get top strikes
            results_df = first.get("results")
            if results_df is not None and not results_df.empty:
                top_strikes = results_df.head(5).to_dict("records")
                vopr_data["top_strikes"] = top_strikes
            print(f"    ✓ VoPR: VRP={vopr_data['vrp_ratio']}x, IV={vopr_data['atm_iv']}%")
    except Exception as e:
        print(f"    [INFO] VoPR skipped: {e}")

    data = {
        "date": date_str, "price": round(price, 2), "change_pct": change_pct,
        "market_cap": _fmt_num(info.get("marketCap")),
        "beta": _safe(info.get("beta")),
        "range_52w": f"{w52_low} - {w52_high}",
        "w52_low": w52_low, "w52_high": w52_high, "w52_pos": w52_pos,
        "sector": info.get("sector", "N/A"), "industry": info.get("industry", "N/A"),
        "rev_growth": round((info.get("revenueGrowth", 0) or 0) * 100, 1),
        "profit_margin": round((info.get("profitMargins", 0) or 0) * 100, 1),
        "pe": _safe(info.get("trailingPE")), "fwd_pe": _safe(info.get("forwardPE")),
        "ema_stack": ema_stack, "ema_8": ema_8, "ema_21": ema_21, "ema_34": ema_34,
        "sma_20": sma_20, "sma_50": sma_50, "sma_100": sma_100, "sma_200": sma_200,
        "trend": trend, "crossover": crossover,
        "trend_short": trend_short, "trend_med": trend_med, "trend_long": trend_long,
        "rsi": rsi_val, "adx": adx,
        "stoch_k": stoch_k, "stoch_d": stoch_d,
        "macd": macd_val, "macd_signal": macd_sig, "macd_hist": macd_hist_val,
        "pivot": pivot, "r1": r1, "r2": r2, "s1": s1, "s2": s2,
        "atr": atr_val, "rel_vol": rel_vol,
        "iv": iv_current, "hv": hv_30,
        "iv_rank": iv_rank, "iv_percentile": iv_percentile,
        "fib_236": fib_236, "fib_382": fib_382, "fib_500": fib_500, "fib_618": fib_618,
        "kelt_upper": kelt_upper, "kelt_mid": round(kelt_mid, 2), "kelt_lower": kelt_lower,
        "analyst_target": _safe(info.get("targetMeanPrice")),
        "tv_rec": tv_rec,
        "val_status": valuation.get("status", "N/A"),
        "val_gap": valuation.get("gap_pct", 0),
        "val_target": valuation.get("target_price", "N/A"),
        "vopr": vopr_data,
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
    ticker_dir = TICKER_DIR / ticker
    ticker_dir.mkdir(parents=True, exist_ok=True)
    md_path = ticker_dir / "deep_dive.md"
    with open(md_path, "w") as f:
        f.write(md_content)

    # Also write JSON for API consumption
    json_path = ticker_dir / "deep_dive.json"
    with open(json_path, "w") as f:
        json.dump(data, f, indent=2, default=str)

    # Render as styled HTML page
    html_path = ticker_dir / "deep_dive.html"
    _render_html(ticker, md_content, data, html_path)

    print(f"    ✓ {md_path.name} + {html_path.name}")
    return str(md_path)


def _render_html(ticker: str, md_content: str, data: dict, output_path: Path):
    """Convert markdown deep dive to a styled HTML page with technical gearbox."""
    import re

    # Simple markdown -> HTML conversion
    html_body = md_content
    html_body = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html_body, flags=re.MULTILINE)
    html_body = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html_body, flags=re.MULTILINE)
    html_body = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html_body)
    html_body = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html_body)

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

    html_body = re.sub(
        r'<p>\|(.+)\|</p>',
        lambda m: '<tr>' + ''.join(f'<td>{c.strip()}</td>' for c in m.group(1).split('|')) + '</tr>',
        html_body
    )
    html_body = re.sub(r'<tr><td>-+</td>.*?</tr>', '', html_body)
    html_body = re.sub(r'(<tr>.*?</tr>\s*)+', lambda m: '<table>' + m.group(0) + '</table>', html_body, flags=re.DOTALL)

    est = ZoneInfo("America/New_York")
    generated_at = datetime.now(est).strftime("%Y-%m-%d %I:%M %p EST")

    chg = data.get("change_pct", 0)
    change_cls = "pos" if chg >= 0 else "neg"
    trend_cls = "pos" if data.get("trend") == "Bullish" else "neg"

    def _v(val, fmt=".2f", prefix="$", fb="N/A"):
        if val is None: return fb
        return f"{prefix}{val:{fmt}}" if prefix else f"{val:{fmt}}"

    def _c(val, thresh=0):
        if val is None: return "dim"
        return "pos" if val >= thresh else "neg"

    def _rz(val):
        if val is None: return ("N/A", "dim")
        if val >= 70: return (f"{val:.0f}", "neg")
        if val <= 30: return (f"{val:.0f}", "pos")
        return (f"{val:.0f}", "neutral")

    def _ta(label):
        if "Bullish" in str(label): return ("&#x2191;", "pos")
        if "Bearish" in str(label): return ("&#x2193;", "neg")
        return ("&#x2013;", "dim")

    rsi_txt, rsi_cls = _rz(data.get("rsi"))
    ts_a, ts_c = _ta(data.get("trend_short", ""))
    tm_a, tm_c = _ta(data.get("trend_med", ""))
    tl_a, tl_c = _ta(data.get("trend_long", ""))
    w52_pos = data.get("w52_pos", 50)
    price = data.get("price", 0)

    def _ma_dist(ma_val):
        if ma_val is None or ma_val == 0: return ("+0.0%", "dim")
        d = (price - ma_val) / ma_val * 100
        return (f"{d:+.1f}%", "pos" if d >= 0 else "neg")

    d20, d20c = _ma_dist(data.get("sma_20"))
    d50, d50c = _ma_dist(data.get("sma_50"))
    d100, d100c = _ma_dist(data.get("sma_100"))
    d200, d200c = _ma_dist(data.get("sma_200"))

    # VoPR section (optional)
    vopr = data.get("vopr", {})
    vopr_html = ""
    if vopr and vopr.get("vrp_ratio"):
        vrp = vopr.get("vrp_ratio", 0)
        vrp_c = "pos" if vrp >= 1.2 else ("neutral" if vrp >= 1.0 else "neg")
        em = vopr.get("expected_move", {})
        strikes_rows = ""
        for s in vopr.get("top_strikes", [])[:5]:
            ot = s.get("option_type", s.get("type", "?"))
            strikes_rows += f'<tr><td>{ot.upper()}</td><td>${s.get("strike",0):.0f}</td><td>{s.get("delta",0):.3f}</td><td>{s.get("theta",0):.3f}</td><td>${s.get("mid",s.get("premium",0)):.2f}</td></tr>'
        vopr_html = f'''
            <div class="gb-panel gb-full">
                <div class="gb-title">&#x26A1; VoPR EDGE SCANNER</div>
                <div class="osc-row">
                    <div class="gb-card"><div class="label">VRP Ratio</div><div class="val {vrp_c}">{vrp:.2f}x</div></div>
                    <div class="gb-card"><div class="label">ATM IV (Chain)</div><div class="val">{vopr.get("atm_iv","N/A")}%</div></div>
                    <div class="gb-card"><div class="label">Expected Move</div><div class="val">{_v(em.get("expected_move"), ".2f", "$")}</div></div>
                    <div class="gb-card"><div class="label">DTE</div><div class="val sm">{vopr.get("dte","N/A")}</div></div>
                </div>
                <div class="gb-sub">Exp: {vopr.get("expiry","N/A")} | Range: {_v(em.get("lower"),".2f","$")} &#x2014; {_v(em.get("upper"),".2f","$")}</div>'''
        if strikes_rows:
            vopr_html += f'''
                <table class="stk-tbl"><tr><th>Type</th><th>Strike</th><th>&#x394;</th><th>&#x398;</th><th>Mid</th></tr>{strikes_rows}</table>'''
        vopr_html += '</div>'

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{ticker} Deep Dive | ALPHA.DOSSIER</title>
<meta name="description" content="Full deep-dive analysis for {ticker}.">
<link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#050505;color:#e0e0e0;font-family:'JetBrains Mono',monospace;
  background-image:linear-gradient(rgba(18,16,16,0) 50%,rgba(0,0,0,.25) 50%),linear-gradient(90deg,rgba(255,0,0,.06),rgba(0,255,0,.02),rgba(0,0,255,.06));
  background-size:100% 2px,3px 100%}}
.w{{max-width:960px;margin:0 auto;padding:1rem}}
.hud{{background:rgba(10,10,10,.85);border:1px solid #333;margin-bottom:.75rem}}
a{{color:inherit;text-decoration:none}}
.pos{{color:#00ff41}}.neg{{color:#ff3e3e}}.neutral{{color:#ffb000}}.dim{{color:#555}}.accent{{color:#00f3ff}}

.nav{{display:flex;justify-content:space-between;align-items:center;padding:.5rem 0;margin-bottom:.5rem}}
.nav a{{font-family:'Share Tech Mono',monospace;font-size:.75rem;letter-spacing:.15em;color:#00ff41}}
.nav a:hover{{color:#fff}}
.nav-b{{display:flex;gap:.5rem}}
.nav-b a{{color:#666;border:1px solid #333;padding:2px 8px;font-size:9px;text-transform:uppercase}}
.nav-b a:hover{{color:#fff;border-color:#666}}

.hdr{{padding:1.25rem;border-left:4px solid #ffb000;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:.75rem}}
.hdr h1{{font-family:'Share Tech Mono',monospace;font-size:1.75rem;font-weight:900;letter-spacing:.15em;color:#fff}}
.hdr .amb{{color:#ffb000}}
.hdr .sub{{font-size:9px;color:#555;text-transform:uppercase;letter-spacing:.3em;margin-top:4px}}
.hdr .pr{{font-size:1.75rem;font-weight:bold;color:#fff;text-align:right}}
.hdr .ch{{font-size:.85rem;text-align:right}}

.gb{{border-left:4px solid #00f3ff}}
.gb-h{{padding:.75rem 1.25rem;border-bottom:1px solid #222;font-family:'Share Tech Mono',monospace;font-size:10px;text-transform:uppercase;letter-spacing:.2em;color:#555}}
.gb-h span{{color:#00f3ff}}
.gb-b{{padding:1rem 1.25rem}}

.vol-row{{display:grid;grid-template-columns:repeat(4,1fr);gap:.5rem;margin-bottom:.75rem}}
.gb-card{{background:rgba(255,255,255,.02);border:1px solid #222;padding:.6rem .75rem;text-align:center}}
.label{{font-size:9px;color:#555;text-transform:uppercase;letter-spacing:.1em;margin-bottom:4px}}
.val{{font-size:1.1rem;font-weight:bold}}.val.sm{{font-size:.85rem}}

.gb-panel{{background:rgba(255,255,255,.015);border:1px solid #1a1a1a;padding:.75rem;margin-bottom:.5rem}}
.gb-full{{margin-bottom:.75rem}}
.gb-title{{font-size:9px;color:#ffb000;text-transform:uppercase;letter-spacing:.15em;margin-bottom:.5rem;font-weight:bold}}
.gb-sub{{font-size:9px;color:#444;margin-top:.4rem}}

.trend-g{{display:grid;grid-template-columns:repeat(3,1fr);gap:.5rem;text-align:center}}
.trend-a{{font-size:1.5rem;line-height:1}}
.trend-l{{font-size:8px;color:#555;text-transform:uppercase;letter-spacing:.1em;margin-top:2px}}

.ma-g{{display:grid;grid-template-columns:repeat(4,1fr);gap:.5rem}}
.ma-i{{text-align:center}}
.ma-p{{font-size:8px;color:#555;text-transform:uppercase}}
.ma-v{{font-size:.8rem;font-weight:bold;color:#e0e0e0}}
.ma-d{{font-size:9px}}

.osc-row{{display:grid;grid-template-columns:repeat(4,1fr);gap:.5rem;margin-bottom:.5rem}}

.rng-bar{{background:#111;height:6px;border-radius:3px;position:relative;margin:.5rem 0}}
.rng-fill{{height:100%;border-radius:3px;background:linear-gradient(90deg,#ff3e3e,#ffb000,#00ff41)}}
.rng-dot{{position:absolute;top:-3px;width:12px;height:12px;border-radius:50%;background:#fff;border:2px solid #00f3ff;transform:translateX(-50%)}}
.rng-lbl{{display:flex;justify-content:space-between;font-size:9px;color:#555}}

.lvl-row{{display:grid;grid-template-columns:repeat(2,1fr);gap:.5rem;margin-bottom:.5rem}}
.lvl-g{{display:grid;grid-template-columns:repeat(2,1fr);gap:.35rem}}
.lvl-m{{text-align:center}}
.lvl-k{{font-size:8px;color:#555;text-transform:uppercase;letter-spacing:.1em}}
.lvl-v{{font-size:.8rem;font-weight:bold;color:#e0e0e0}}

.stk-tbl{{width:100%;border-collapse:collapse;margin-top:.5rem;font-size:10px}}
.stk-tbl th{{color:#555;text-align:left;padding:4px 6px;border-bottom:1px solid #222;font-weight:normal;text-transform:uppercase;font-size:8px}}
.stk-tbl td{{padding:4px 6px;color:#c0c0c0;border-bottom:1px solid #111}}

.ct h2{{font-size:1.3rem;font-weight:900;color:#fff;margin:1.8rem 0 .8rem;padding-bottom:.4rem;border-bottom:2px solid #333;
  font-family:'Share Tech Mono',monospace;text-transform:uppercase;letter-spacing:.05em}}
.ct h3{{font-size:1rem;font-weight:700;color:#ffb000;margin:1.2rem 0 .6rem;letter-spacing:.03em}}
.ct p{{color:#c0c0c0;line-height:1.75;margin:.4rem 0;font-size:.8rem}}
.ct strong{{color:#fff}}.ct em{{color:#00f3ff;font-style:normal}}
.ct ul,.ct ol{{margin:.4rem 0 .4rem 1.5rem;color:#c0c0c0;font-size:.8rem;line-height:1.9}}
.ct li{{margin:.25rem 0}}
.ct hr{{border:none;border-top:1px solid #333;margin:1.5rem 0}}
.ct table{{width:100%;border-collapse:collapse;margin:.75rem 0;font-size:.75rem}}
.ct td{{padding:.4rem .6rem;border:1px solid #222;color:#c0c0c0}}
.ct tr:first-child td{{font-weight:bold;color:#888;background:rgba(255,255,255,.03)}}
.ft{{text-align:center;padding:1.5rem 0;font-size:8px;color:#333;text-transform:uppercase;letter-spacing:.2em}}

@media(max-width:640px){{
  .vol-row,.osc-row{{grid-template-columns:repeat(2,1fr)}}
  .ma-g{{grid-template-columns:repeat(2,1fr)}}
  .lvl-row{{grid-template-columns:1fr}}
  .hdr{{flex-direction:column}}.hdr .pr{{text-align:left}}
}}
</style>
</head>
<body>
<div class="w">

<div class="nav">
  <a href="../../index.html">&#x2190; ALPHA://HUD</a>
  <div class="nav-b"><a href="deep_dive.md" download>&#x2193; MD</a><a href="deep_dive.json">&#x2193; JSON</a></div>
</div>

<div class="hud hdr">
  <div>
    <h1><a href="https://www.tradingview.com/symbols/{ticker}/" target="_blank">{ticker}</a> <span class="amb">DEEP.DIVE</span></h1>
    <div class="sub">{data.get("sector","N/A")} &#xB7; {data.get("industry","N/A")} &#xB7; {data.get("date","")}</div>
  </div>
  <div>
    <div class="pr">${data.get("price","N/A")}</div>
    <div class="ch {change_cls}">{chg:+.2f}%</div>
  </div>
</div>

<!-- GEARBOX -->
<div class="hud gb">
  <div class="gb-h">&#x2699; TECHNICAL.GEARBOX <span>// FULL DIAGNOSTICS</span></div>
  <div class="gb-b">

    <div class="vol-row">
      <div class="gb-card"><div class="label">Implied Vol</div><div class="val accent">{_v(data.get("iv"),".1f","",fb="N/A")}%</div></div>
      <div class="gb-card"><div class="label">Historic Vol 30D</div><div class="val">{_v(data.get("hv"),".1f","",fb="N/A")}%</div></div>
      <div class="gb-card"><div class="label">IV Rank</div><div class="val {_c(data.get("iv_rank"),50)}">{_v(data.get("iv_rank"),".0f","",fb="N/A")}</div></div>
      <div class="gb-card"><div class="label">IV Percentile</div><div class="val">{_v(data.get("iv_percentile"),".0f","",fb="N/A")}%</div></div>
    </div>

    <div class="gb-panel">
      <div class="gb-title">Trend // {data.get("trend","N/A")} Market</div>
      <div class="trend-g">
        <div><div class="trend-a {ts_c}">{ts_a}</div><div class="trend-l">Short-Term</div><div style="font-size:8px;color:#444">EMA 8/21</div></div>
        <div><div class="trend-a {tm_c}">{tm_a}</div><div class="trend-l">Mid-Term</div><div style="font-size:8px;color:#444">EMA 21/SMA 50</div></div>
        <div><div class="trend-a {tl_c}">{tl_a}</div><div class="trend-l">Long-Term</div><div style="font-size:8px;color:#444">SMA 50/200</div></div>
      </div>
      <div class="gb-sub" style="text-align:center;margin-top:8px">
        EMA Stack: <span class="{trend_cls}">{data.get("ema_stack","N/A")}</span> &#xB7;
        TradingView: <span class="accent">{data.get("tv_rec","N/A")}</span> &#xB7; {data.get("crossover","")}
      </div>
    </div>

    <div class="gb-panel">
      <div class="gb-title">Moving Averages</div>
      <div class="ma-g">
        <div class="ma-i"><div class="ma-p">SMA 20</div><div class="ma-v">{_v(data.get("sma_20"))}</div><div class="ma-d {d20c}">{d20}</div></div>
        <div class="ma-i"><div class="ma-p">SMA 50</div><div class="ma-v">{_v(data.get("sma_50"))}</div><div class="ma-d {d50c}">{d50}</div></div>
        <div class="ma-i"><div class="ma-p">SMA 100</div><div class="ma-v">{_v(data.get("sma_100"))}</div><div class="ma-d {d100c}">{d100}</div></div>
        <div class="ma-i"><div class="ma-p">SMA 200</div><div class="ma-v">{_v(data.get("sma_200"))}</div><div class="ma-d {d200c}">{d200}</div></div>
      </div>
    </div>

    <div class="osc-row">
      <div class="gb-card"><div class="label">RSI (14)</div><div class="val {rsi_cls}">{rsi_txt}</div></div>
      <div class="gb-card"><div class="label">Stoch %K/%D</div><div class="val sm">{_v(data.get("stoch_k"),".0f","")}/{_v(data.get("stoch_d"),".0f","")}</div></div>
      <div class="gb-card"><div class="label">MACD Hist</div><div class="val sm {_c(data.get("macd_hist"))}">{_v(data.get("macd_hist"),"+.2f","")}</div></div>
      <div class="gb-card"><div class="label">ADX (14)</div><div class="val sm">{_v(data.get("adx"),".1f","")}</div></div>
    </div>

    <div class="gb-panel">
      <div class="gb-title">52-Week Range</div>
      <div class="rng-lbl"><span>${data.get("w52_low","N/A")}</span><span>${price} ({w52_pos:.0f}%)</span><span>${data.get("w52_high","N/A")}</span></div>
      <div class="rng-bar"><div class="rng-fill" style="width:{w52_pos:.0f}%"></div><div class="rng-dot" style="left:{w52_pos:.0f}%"></div></div>
    </div>

    <div class="lvl-row">
      <div class="gb-panel">
        <div class="gb-title">Fibonacci Levels</div>
        <div class="lvl-g">
          <div class="lvl-m"><div class="lvl-k">0.236</div><div class="lvl-v">{_v(data.get("fib_236"))}</div></div>
          <div class="lvl-m"><div class="lvl-k">0.382</div><div class="lvl-v">{_v(data.get("fib_382"))}</div></div>
          <div class="lvl-m"><div class="lvl-k">0.500</div><div class="lvl-v">{_v(data.get("fib_500"))}</div></div>
          <div class="lvl-m"><div class="lvl-k">0.618</div><div class="lvl-v">{_v(data.get("fib_618"))}</div></div>
        </div>
      </div>
      <div class="gb-panel">
        <div class="gb-title">Keltner / Pivots</div>
        <div class="lvl-g">
          <div class="lvl-m"><div class="lvl-k">Kelt Upper</div><div class="lvl-v">{_v(data.get("kelt_upper"))}</div></div>
          <div class="lvl-m"><div class="lvl-k">Kelt Lower</div><div class="lvl-v">{_v(data.get("kelt_lower"))}</div></div>
          <div class="lvl-m"><div class="lvl-k">ATR (14)</div><div class="lvl-v">{_v(data.get("atr"))}</div></div>
          <div class="lvl-m"><div class="lvl-k">Rel Vol</div><div class="lvl-v">{_v(data.get("rel_vol"),".2f","")}x</div></div>
        </div>
        <div class="gb-sub" style="margin-top:6px;text-align:center">
          R2={_v(data.get("r2"))} &#xB7; R1={_v(data.get("r1"))} &#xB7; PP={_v(data.get("pivot"))} &#xB7; S1={_v(data.get("s1"))} &#xB7; S2={_v(data.get("s2"))}
        </div>
      </div>
    </div>

    {vopr_html}

  </div>
</div>

<div class="hud" style="padding:1.5rem 2rem"><div class="ct">{html_body}</div></div>

<div class="ft">Ghost Alpha Dossier // Watchlist Deep Dive // {generated_at}</div>
</div>
</body>
</html>'''

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
    print(f"   Output: {TICKER_DIR}/")


if __name__ == "__main__":
    main()
