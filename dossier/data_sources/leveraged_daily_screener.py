#!/usr/bin/env python3
"""
Leveraged ETF Daily Screener — V2 (Point-Based Scoring)

Generates a daily graded list of 2x leveraged ETF opportunities.
Runs as part of the 5AM dossier pipeline. Outputs:
  - docs/leveraged-screener/daily.html  (self-contained page)
  - docs/leveraged-screener/daily.json  (API/widget consumption)

Scoring (max 17 pts):
  ADX Strength:     0-4 pts  (15+ to 30+)
  ADX Delta:        0-3 pts  (trend acceleration, 5-bar lookback)
  ATR Squeeze:      0-3 pts  (coiled volatility / squeeze fire)
  Relative Volume:  0-3 pts  (1.0x to 2.0x+)
  RSI Oversold:     0-3 pts  (< 40 to < 30)
  Below VWAP:       0-1 pt   (dip entry)

Grading:
  A = 14+ pts (82%)   — strong conviction setup
  B = 10+ pts (59%)   — solid setup
  C =  6+ pts (35%)   — moderate / emerging
  D = below 6         — weak / avoid

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


def _compute_adx(highs, lows, closes, period=14, delta_lookback=5):
    """Compute ADX with trend acceleration data.

    Returns dict with:
      adx        - current ADX value
      adx_prev   - ADX value `delta_lookback` bars ago (for delta calc)
      adx_delta  - adx - adx_prev (positive = strengthening trend)
      plus_di    - current +DI
      minus_di   - current -DI
      tr_list    - raw True Range list (for ATR squeeze calc downstream)
    """
    empty = {"adx": 0.0, "adx_prev": 0.0, "adx_delta": 0.0,
             "plus_di": 0.0, "minus_di": 0.0, "tr_list": []}

    if len(highs) < period * 2:
        return empty

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
        return {**empty, "tr_list": tr_list}

    # Smoothed TR, +DM, -DM (Wilder's smoothing)
    atr = sum(tr_list[:period])
    plus = sum(plus_dm[:period])
    minus = sum(minus_dm[:period])

    dx_list = []
    adx_history = []  # Track ADX at each bar for delta calculation
    last_plus_di = 0.0
    last_minus_di = 0.0

    for i in range(period, len(tr_list)):
        atr = atr - atr / period + tr_list[i]
        plus = plus - plus / period + plus_dm[i]
        minus = minus - minus / period + minus_dm[i]

        if atr == 0:
            continue
        last_plus_di = 100 * plus / atr
        last_minus_di = 100 * minus / atr
        if last_plus_di + last_minus_di == 0:
            continue
        dx = 100 * abs(last_plus_di - last_minus_di) / (last_plus_di + last_minus_di)
        dx_list.append(dx)

    if not dx_list:
        return {**empty, "tr_list": tr_list}

    # ADX = smoothed average of DX, tracking history for delta
    adx = sum(dx_list[:period]) / period if len(dx_list) >= period else sum(dx_list) / len(dx_list)
    adx_history.append(adx)
    for i in range(period, len(dx_list)):
        adx = (adx * (period - 1) + dx_list[i]) / period
        adx_history.append(adx)

    # ADX delta: current vs N bars ago
    adx_current = round(adx, 1)
    if len(adx_history) > delta_lookback:
        adx_prev = round(adx_history[-(delta_lookback + 1)], 1)
    else:
        adx_prev = round(adx_history[0], 1)

    return {
        "adx": adx_current,
        "adx_prev": adx_prev,
        "adx_delta": round(adx_current - adx_prev, 1),
        "plus_di": round(last_plus_di, 1),
        "minus_di": round(last_minus_di, 1),
        "tr_list": tr_list,
    }


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


def _compute_atr_squeeze(tr_list, atr_period=14, baseline_period=50):
    """Compute ATR squeeze ratio and fire signal from True Range list.

    Returns dict with:
      sqz_ratio  - current ATR / ATR baseline (< 0.75 = coiled)
      sqz_fire   - True if squeeze just fired (crossed 0.75 from below)
      atr        - current ATR(14) value
      atr_base   - ATR baseline (50-period avg)
    """
    if len(tr_list) < baseline_period + atr_period:
        return {"sqz_ratio": 1.0, "sqz_fire": False, "atr": 0.0, "atr_base": 0.0}

    # Compute rolling ATR values
    atr_values = []
    for i in range(atr_period, len(tr_list) + 1):
        window = tr_list[i - atr_period:i]
        atr_values.append(sum(window) / atr_period)

    if len(atr_values) < 2:
        return {"sqz_ratio": 1.0, "sqz_fire": False, "atr": 0.0, "atr_base": 0.0}

    current_atr = atr_values[-1]

    # Baseline = 50-period average of ATR values
    baseline_window = atr_values[-baseline_period:] if len(atr_values) >= baseline_period else atr_values
    atr_baseline = sum(baseline_window) / len(baseline_window)

    sqz_ratio = current_atr / atr_baseline if atr_baseline > 0 else 1.0

    # Fire detection: did sqz_ratio cross 0.75 from below in the last bar?
    sqz_fire = False
    if len(atr_values) >= 2:
        prev_atr = atr_values[-2]
        prev_ratio = prev_atr / atr_baseline if atr_baseline > 0 else 1.0
        sqz_fire = prev_ratio < 0.75 and sqz_ratio >= 0.75

    return {
        "sqz_ratio": round(sqz_ratio, 3),
        "sqz_fire": sqz_fire,
        "atr": round(current_atr, 4),
        "atr_base": round(atr_baseline, 4),
    }


def _calculate_score(adx, adx_delta, sqz_ratio, sqz_fire, rsi, rel_vol, below_vwap):
    """Point-based scoring system for LETF setups.

    Max score: 17 points across 6 categories.
    Designed to catch consolidation breakouts (high adx_delta, low ADX)
    as well as established trends (high ADX).
    """
    score = 0
    reasons = []

    # Category 1: ADX Strength (0-4 pts)
    if adx >= 30:
        score += 4; reasons.append(f"ADX {adx} (strong trend)")
    elif adx >= 25:
        score += 3; reasons.append(f"ADX {adx} (solid trend)")
    elif adx >= 20:
        score += 2; reasons.append(f"ADX {adx} (moderate trend)")
    elif adx >= 15:
        score += 1; reasons.append(f"ADX {adx} (emerging trend)")

    # Category 2: ADX Delta / Trend Acceleration (0-3 pts)
    if adx_delta >= 7:
        score += 3; reasons.append(f"ADX Δ+{adx_delta} (rapid acceleration)")
    elif adx_delta >= 5:
        score += 2; reasons.append(f"ADX Δ+{adx_delta} (accelerating)")
    elif adx_delta >= 3:
        score += 1; reasons.append(f"ADX Δ+{adx_delta} (building)")

    # Category 3: ATR Squeeze (0-3 pts)
    if sqz_fire:
        score += 3; reasons.append(f"SQUEEZE FIRE 🔥 (ratio {sqz_ratio:.2f})")
    elif sqz_ratio < 0.70:
        score += 2; reasons.append(f"Tightly coiled ({sqz_ratio:.2f})")
    elif sqz_ratio < 0.80:
        score += 1; reasons.append(f"Coiling ({sqz_ratio:.2f})")

    # Category 4: Relative Volume (0-3 pts)
    if rel_vol >= 2.0:
        score += 3; reasons.append(f"Vol {rel_vol}x (surge)")
    elif rel_vol >= 1.5:
        score += 2; reasons.append(f"Vol {rel_vol}x (elevated)")
    elif rel_vol >= 1.0:
        score += 1; reasons.append(f"Vol {rel_vol}x (normal)")

    # Category 5: RSI Oversold (0-3 pts)
    if rsi < 30:
        score += 3; reasons.append(f"RSI {rsi} (deeply oversold)")
    elif rsi < 35:
        score += 2; reasons.append(f"RSI {rsi} (oversold)")
    elif rsi < 40:
        score += 1; reasons.append(f"RSI {rsi} (approaching oversold)")

    # Category 6: Below VWAP (0-1 pt)
    if below_vwap:
        score += 1; reasons.append("Below VWAP (dip entry)")

    return score, reasons


def _assign_grade(score):
    """Map point score to letter grade.

    Thresholds scaled to max of 17:
      A = 14+ (82%) — strong conviction
      B = 10+ (59%) — solid setup
      C =  6+ (35%) — moderate/emerging
      D = below 6   — weak/avoid
    """
    if score >= 14:
        return "A"
    if score >= 10:
        return "B"
    if score >= 6:
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
            spy_adx = _compute_adx(spy_h, spy_l, spy_c)["adx"]
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
        data = yf.download(underlyings, period="6mo", group_by="ticker", progress=False, threads=True)
    except Exception as e:
        print(f"    [ERR] Batch download failed: {e}")
        data = None

    for ticker in underlyings:
        try:
            if data is not None and ticker in data.columns.get_level_values(0):
                df = data[ticker].dropna()
            else:
                df = yf.Ticker(ticker).history(period="6mo")

            if df.empty or len(df) < 20:
                continue

            closes = df["Close"].tolist()
            highs = df["High"].tolist()
            lows = df["Low"].tolist()
            volumes = df["Volume"].tolist()

            # Compute signals — V2: enriched ADX + ATR squeeze
            adx_data = _compute_adx(highs, lows, closes)
            adx = adx_data["adx"]
            adx_delta = adx_data["adx_delta"]
            rsi = _compute_rsi(closes)

            # ATR Squeeze detection
            sqz_data = _compute_atr_squeeze(adx_data["tr_list"])
            sqz_ratio = sqz_data["sqz_ratio"]
            sqz_fire = sqz_data["sqz_fire"]

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

            # V2: Point-based scoring
            score, reasons = _calculate_score(
                adx, adx_delta, sqz_ratio, sqz_fire, rsi, rel_vol, below_vwap
            )
            grade = _assign_grade(score)

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
                "adx_delta": adx_delta,
                "rsi": rsi,
                "rel_vol": rel_vol,
                "below_vwap": below_vwap,
                "sqz_ratio": sqz_ratio,
                "sqz_fire": sqz_fire,
                "score": score,
                "grade": grade,
                "reasons": reasons,
                "etf_avg_volume": etf_vol,
            })
        except Exception as e:
            continue

    # Sort: A first, then B, C, D. Within grade, sort by score descending
    grade_order = {"A": 0, "B": 1, "C": 2, "D": 3}
    picks.sort(key=lambda x: (grade_order.get(x["grade"], 9), -x["score"]))

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
    generated_at = data.get("generated_at", "")
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
            <span>ADX {p["adx"]} (Δ{("+" if p.get("adx_delta",0) >= 0 else "")}{p.get("adx_delta",0)})</span>
            <span>RSI {p["rsi"]}</span>
            <span class="{chg_class}">{chg_sign}{p["change_pct"]}%</span>
          </div>
          <div class="pick-grade" style="color:{gc}">{p["grade"]}</div>
          <div class="pick-score">Score: {p.get("score", 0)}/17{" 🔥" if p.get("sqz_fire") else ""}</div>
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
        adx_d = p.get("adx_delta", 0)
        delta_class = "positive" if adx_d >= 5 else "neutral" if adx_d >= 3 else ""
        delta_sign = "+" if adx_d >= 0 else ""
        sqz_r = p.get("sqz_ratio", 1.0)
        sqz_class = "positive" if p.get("sqz_fire") else "neutral" if sqz_r < 0.80 else ""
        sqz_icon = "🔥" if p.get("sqz_fire") else f"{sqz_r:.2f}"
        score_val = p.get("score", 0)

        rows += f'''
      <tr>
        <td><span class="grade-badge" style="background:{gc}">{p["grade"]}</span></td>
        <td class="ticker-cell"><a href="https://www.tradingview.com/symbols/{p["underlying"]}" target="_blank">{p["underlying"]}</a></td>
        <td class="etf-cell">{p["etf"]}</td>
        <td>${p["price"]:,.2f}</td>
        <td class="{chg_class}">{chg_sign}{p["change_pct"]}%</td>
        <td style="font-weight:600">{p["adx"]}</td>
        <td class="{delta_class}">{delta_sign}{adx_d}</td>
        <td>{p["rsi"]}</td>
        <td class="{vol_class}">{p["rel_vol"]}x</td>
        <td class="{sqz_class}">{sqz_icon}</td>
        <td>{vwap_icon}</td>
        <td style="font-weight:600">{score_val}</td>
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
.pick-score {{ font-family: 'JetBrains Mono', monospace; font-size: 0.65em; color: var(--cyan); margin-top: 4px; }}

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

  <div id="freshness-banner" data-generated="{generated_at}" style="display:none;margin:0 0 16px;padding:10px 14px;border-radius:6px;font-family:'JetBrains Mono',monospace;font-size:0.75em;text-align:center;"></div>

  <div class="summary-grid">
    <div class="summary-card"><div class="label">Scanned</div><div class="value" style="color:var(--text)">{summary["total_scanned"]}</div></div>
    <div class="summary-card"><div class="label">Grade A</div><div class="value" style="color:#00ff41">{summary["grade_a"]}</div></div>
    <div class="summary-card"><div class="label">Grade B</div><div class="value" style="color:#00d4ff">{summary["grade_b"]}</div></div>
    <div class="summary-card"><div class="label">Grade C</div><div class="value" style="color:#f0b400">{summary["grade_c"]}</div></div>
    <div class="summary-card"><div class="label">Grade D</div><div class="value" style="color:#555">{summary["grade_d"]}</div></div>
  </div>

  <div class="legend">
    <div class="legend-item"><span class="grade-badge" style="background:#00ff41">A</span> 14+/17 pts (strong conviction)</div>
    <div class="legend-item"><span class="grade-badge" style="background:#00d4ff">B</span> 10+/17 pts (solid setup)</div>
    <div class="legend-item"><span class="grade-badge" style="background:#f0b400">C</span> 6+/17 pts (emerging)</div>
    <div class="legend-item"><span class="grade-badge" style="background:#555">D</span> Below 6 pts (weak)</div>
    <div class="legend-item">🔥 = ATR Squeeze Fire</div>
    <div class="legend-item">Δ+ = ADX Accelerating</div>
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
        <th>ADX Δ</th>
        <th>RSI(14)</th>
        <th>Rel Vol</th>
        <th>Squeeze</th>
        <th>VWAP</th>
        <th>Score</th>
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

<script>
// Freshness banner — render server-set generated_at, warn if stale.
// "Stale" = generated > 25h ago (cron runs Mon–Fri 10:00 UTC; >25h means
// today's run didn't land, weekends excluded).
(function() {{
  var el = document.getElementById('freshness-banner');
  if (!el) return;
  var iso = el.getAttribute('data-generated');
  if (!iso) return;
  var gen = new Date(iso);
  if (isNaN(gen.getTime())) return;
  var ageMs = Date.now() - gen.getTime();
  var ageH = ageMs / 36e5;
  var dow = new Date().getUTCDay(); // 0 = Sun, 6 = Sat
  var weekend = (dow === 0 || dow === 6);
  if (ageH > 25 && !weekend) {{
    el.style.display = 'block';
    el.style.background = 'rgba(229,57,53,0.15)';
    el.style.border = '1px solid #e53935';
    el.style.color = '#ff7a76';
    el.textContent = '⚠️ STALE — last refresh ' + Math.floor(ageH) + 'h ago. Today\\'s pipeline may have failed. Check https://github.com/mphinance/mphinance/issues?q=is:open+label:pipeline-failure';
  }} else if (ageH > 12) {{
    el.style.display = 'block';
    el.style.background = 'rgba(240,180,0,0.10)';
    el.style.border = '1px solid #f0b400';
    el.style.color = '#f0b400';
    el.textContent = '⏱ Last refresh ' + Math.floor(ageH) + 'h ago' + (weekend ? ' (weekend — pipeline does not run)' : '') + '.';
  }}
}})();
</script>

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
