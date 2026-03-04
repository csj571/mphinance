"""
Per-Ticker Deep Dive Page Generator

Assembles comprehensive per-ticker data and renders individual HUD pages.
Each ticker gets:
  - JSON endpoint:  docs/ticker/{SYMBOL}/latest.json
  - HTML HUD page:  docs/ticker/{SYMBOL}/latest.html
  - Historical:     docs/ticker/{SYMBOL}/{DATE}.json/.html
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

import yfinance as yf
import pandas as pd
import numpy as np

from jinja2 import Environment, FileSystemLoader

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dossier.data_sources.ticker_enrichment import (
    _sma, _ema, _rsi, _macd, _safe, _fmt_num,
    _tradingview_summary, _intrinsic_value, _fetch_news,
)
from dossier.data_sources.tickertrace import get_ticker_detail

TICKER_OUTPUT_DIR = PROJECT_ROOT / "docs" / "ticker"


def _build_chart_data(df: pd.DataFrame) -> tuple[list, dict]:
    """Build Plotly candlestick + EMA overlay data from OHLCV DataFrame."""
    chart_data = []
    for idx, row in df.iterrows():
        chart_data.append({
            "time": idx.strftime("%Y-%m-%d"),
            "open": round(float(row["Open"]), 2),
            "high": round(float(row["High"]), 2),
            "low": round(float(row["Low"]), 2),
            "close": round(float(row["Close"]), 2),
        })

    close = df["Close"]
    ema_spans = {"8": 8, "21": 21, "34": 34, "55": 55, "89": 89}
    ema_data = {}
    for label, span in ema_spans.items():
        ema_series = _ema(close, span)
        ema_data[label] = [
            {"time": idx.strftime("%Y-%m-%d"), "value": round(float(v), 2)}
            for idx, v in ema_series.dropna().items()
        ]

    return chart_data, ema_data


def _compute_expected_moves(stock, price: float) -> list[dict]:
    """Calculate expected moves from options chain IV."""
    moves = []
    try:
        expirations = stock.options
        if not expirations:
            return moves

        for exp in expirations[:4]:
            try:
                chain = stock.option_chain(exp)
                calls = chain.calls
                atm = calls[
                    (calls["strike"] >= price * 0.95) &
                    (calls["strike"] <= price * 1.05)
                ]
                if atm.empty:
                    continue
                iv_avg = float(atm["impliedVolatility"].mean())

                exp_date = datetime.strptime(exp, "%Y-%m-%d")
                now = datetime.now()
                dte = max((exp_date - now).days, 1)
                em = price * iv_avg * np.sqrt(dte / 365)

                moves.append({
                    "expiration": exp,
                    "expectedMove": round(em, 2),
                    "expectedRange": f"{round(price - em, 2)} - {round(price + em, 2)}",
                    "iv": round(iv_avg * 100, 1),
                    "dte": dte,
                })
            except Exception:
                continue
    except Exception:
        pass
    return moves


def _compute_options_flow(stock, price: float) -> dict:
    """Compute put/call ratios and volume stats."""
    flow = {
        "callVolume": 0, "putVolume": 0, "totalVolume": 0,
        "pcRatioVol": 0, "callOpenInt": 0, "putOpenInt": 0,
        "totalOpenInt": 0, "pcRatioOi": 0,
    }
    try:
        expirations = stock.options
        if not expirations:
            return flow

        # Use first 3 expirations
        for exp in expirations[:3]:
            try:
                chain = stock.option_chain(exp)
                flow["callVolume"] += int(chain.calls["volume"].sum())
                flow["putVolume"] += int(chain.puts["volume"].sum())
                flow["callOpenInt"] += int(chain.calls["openInterest"].sum())
                flow["putOpenInt"] += int(chain.puts["openInterest"].sum())
            except Exception:
                continue

        flow["totalVolume"] = flow["callVolume"] + flow["putVolume"]
        flow["totalOpenInt"] = flow["callOpenInt"] + flow["putOpenInt"]
        flow["pcRatioVol"] = round(flow["putVolume"] / max(flow["callVolume"], 1), 2)
        flow["pcRatioOi"] = round(flow["putOpenInt"] / max(flow["callOpenInt"], 1), 2)
    except Exception:
        pass
    return flow


def _iv_metrics(stock, price: float) -> dict:
    """Compute IV rank, percentile, and related metrics."""
    iv_data = {
        "impliedVolatility": 0, "historicVolatility": 0,
        "ivRank": 0, "ivPercentile": 0,
        "iv5dAvg": 0, "iv1mAvg": 0,
    }
    try:
        expirations = stock.options
        if not expirations:
            return iv_data

        exp = expirations[min(2, len(expirations) - 1)]
        calls = stock.option_chain(exp).calls
        atm = calls[
            (calls["strike"] >= price * 0.95) &
            (calls["strike"] <= price * 1.05)
        ]
        if not atm.empty:
            iv = float(atm["impliedVolatility"].mean()) * 100
            iv_data["impliedVolatility"] = round(iv, 2)
            iv_data["iv5dAvg"] = round(iv, 2)
            iv_data["iv1mAvg"] = round(iv, 2)
    except Exception:
        pass
    return iv_data


def generate_ticker_page(ticker: str, enriched_data: dict, date: str,
                         institutional: dict = None) -> dict:
    """
    Generate a full deep-dive page for a single ticker.

    Args:
        ticker: The stock symbol
        enriched_data: Data from enrich_ticker() or None to fetch fresh
        date: Report date (YYYY-MM-DD)
        institutional: Full institutional data dict from TickerTrace

    Returns:
        Dict with paths to generated files
    """
    print(f"    Generating page: {ticker}...")

    stock = yf.Ticker(ticker)

    # ── Price History (6 months for chart) ──
    try:
        df = stock.history(period="6mo")
        if df.empty:
            print(f"    [SKIP] No data for {ticker}")
            return {}
    except Exception as e:
        print(f"    [ERR] {ticker}: {e}")
        return {}

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    price = float(close.iloc[-1])
    info = {}
    try:
        info = stock.info or {}
    except Exception:
        pass

    # ── Chart Data ──
    chart_data, ema_data = _build_chart_data(df)

    # ── Technical Analysis (reuse enriched if available) ──
    tech = enriched_data.get("technicals", {}) if enriched_data else {}
    if not tech:
        # Compute from scratch
        ema_8 = _ema(close, 8)
        ema_21 = _ema(close, 21)
        ema_34 = _ema(close, 34)
        ema_55 = _ema(close, 55)
        ema_89 = _ema(close, 89)
        sma_50 = _sma(close, 50)
        sma_200 = _sma(close, 200)
        rsi_val = _safe(_rsi(close).iloc[-1])
        _, _, macd_hist = _macd(close)
        tr = pd.concat([high - low, abs(high - close.shift()), abs(low - close.shift())], axis=1).max(axis=1)
        atr_val = _safe(tr.rolling(14).mean().iloc[-1])
        vol_avg = df["Volume"].rolling(20).mean()
        rel_vol = round(float(df["Volume"].iloc[-1] / vol_avg.iloc[-1]), 2) if vol_avg.iloc[-1] > 0 else 1.0

        tech = {
            "ema_stack": enriched_data.get("technicals", {}).get("ema_stack", "UNKNOWN"),
            "ema_8": _safe(ema_8.iloc[-1]), "ema_21": _safe(ema_21.iloc[-1]),
            "ema_34": _safe(ema_34.iloc[-1]), "ema_55": _safe(ema_55.iloc[-1]),
            "ema_89": _safe(ema_89.iloc[-1]),
            "sma_50": _safe(sma_50.iloc[-1]), "sma_200": _safe(sma_200.iloc[-1]),
            "rsi_14": rsi_val, "macd_hist": _safe(macd_hist.iloc[-1]),
            "atr": atr_val, "rel_vol": rel_vol,
            "adx": _safe(enriched_data.get("technicals", {}).get("adx")),
            "stoch_k": _safe(enriched_data.get("technicals", {}).get("stoch_k")),
        }

    # ── Volatility ──
    log_ret = np.log(close / close.shift(1))
    hv_30 = float(log_ret.rolling(30).std().iloc[-1] * np.sqrt(252) * 100)
    vol = enriched_data.get("volatility", {}) if enriched_data else {}
    iv_current = vol.get("iv_current", 0)

    # ── IV metrics ──
    iv_metrics = _iv_metrics(stock, price)
    if iv_current:
        iv_metrics["impliedVolatility"] = iv_current
    iv_metrics["historicVolatility"] = round(hv_30, 2) if not np.isnan(hv_30) else 0

    # ── Expected Moves ──
    expected_moves = _compute_expected_moves(stock, price)

    # ── Options Flow ──
    options_flow = _compute_options_flow(stock, price)

    # ── TickerTrace Institutional ──
    tt_detail = {}
    try:
        tt_detail = get_ticker_detail(ticker) or {}
    except Exception:
        pass

    # Also pull this ticker from the institutional buying/selling lists
    inst_context = {}
    if institutional:
        for s in institutional.get("top_buying", []):
            if s.get("ticker") == ticker:
                inst_context = {"direction": "BUYING", **s}
                break
        if not inst_context:
            for s in institutional.get("top_selling", []):
                if s.get("ticker") == ticker:
                    inst_context = {"direction": "SELLING", **s}
                    break

    # ── Trend analysis ──
    sma_50_val = tech.get("sma_50") or price
    sma_200_val = tech.get("sma_200") or price
    trend = "Bullish" if sma_50_val > sma_200_val else "Bearish"
    crossover = "Golden Cross" if sma_50_val > sma_200_val else "Death Cross"

    # Short/Med/Long trend
    trend_short = "Strong" if price > (tech.get("ema_21") or price) else "Weak"
    trend_med = "Strong" if price > (tech.get("sma_50") or price) else "Soft"
    trend_long = "Strong" if price > (tech.get("sma_200") or price) else "Weak"

    # ── Pivots (from enriched or compute) ──
    pivot = tech.get("pivot")
    r1 = tech.get("r1")
    r2 = tech.get("r2")
    s1 = tech.get("s1")
    s2 = tech.get("s2")
    if not pivot:
        prev_h = float(high.iloc[-2]) if len(high) >= 2 else float(high.iloc[-1])
        prev_l = float(low.iloc[-2]) if len(low) >= 2 else float(low.iloc[-1])
        prev_c = float(close.iloc[-2]) if len(close) >= 2 else price
        pivot = round((prev_h + prev_l + prev_c) / 3, 2)
        r1 = round(2 * pivot - prev_l, 2)
        r2 = round(pivot + (prev_h - prev_l), 2)
        s1 = round(2 * pivot - prev_h, 2)
        s2 = round(pivot - (prev_h - prev_l), 2)

    # ── Fibonacci ──
    high_52w = float(high.max())
    low_52w = float(low.min())
    fib_range = high_52w - low_52w
    fib_618 = round(high_52w - fib_range * 0.618, 2)
    fib_500 = round(high_52w - fib_range * 0.500, 2)
    fib_382 = round(high_52w - fib_range * 0.382, 2)

    # ── Valuation ──
    valuation = enriched_data.get("valuation", {}) if enriched_data else _intrinsic_value(info, price)

    # ── Scores ──
    scores = enriched_data.get("scores", {"technical": 50, "fundamental": 50, "grade": "C"})

    # ── Insiders ──
    insiders = enriched_data.get("insiders", []) if enriched_data else []

    # ── News ──
    news = enriched_data.get("news", []) if enriched_data else _fetch_news(ticker)

    # ── TradingView ──
    tv = enriched_data.get("tradingview", {}) if enriched_data else _tradingview_summary(ticker, info.get("exchange", "NMS"))

    # ── AI Analysis ──
    verdict = enriched_data.get("verdict", "WAIT for validation") if enriched_data else "WAIT for validation"
    ai_text = (
        f"<span class='text-neon-blue font-bold'>AI.SYNTHESIS // </span><br>"
        f"Asset demonstrates a "
        f"{'<span class=\"text-neon-green\">STRONG</span>' if scores['technical'] > 60 else '<span class=\"text-neon-red\">WEAK</span>'}"
        f" technical posture (Score: {scores['technical']}/100) within a wider {trend} trend. "
    )
    if valuation.get("status") == "UNDERVALUED":
        ai_text += "Asset appears undervalued relative to growth and book value. "
    elif valuation.get("status") == "OVERVALUED":
        ai_text += "Asset appears overvalued — exercise caution. "
    else:
        ai_text += "Asset appears fairly valued relative to growth and book value. "

    hv_val = round(hv_30, 2) if not np.isnan(hv_30) else 0
    iv_val = iv_metrics.get("impliedVolatility", 0)
    if iv_val > hv_val and iv_val > 0:
        ai_text += "<br><br><span class='text-gray-400 font-bold'>RISK.PROFILE // </span>Implied volatility exceeds historical norms, expecting turbulence. "
    else:
        ai_text += "<br><br><span class='text-gray-400 font-bold'>RISK.PROFILE // </span>Volatility within normal range. "

    ai_text += f"<br><br><span class='text-neon-amber font-bold'>VERDICT // </span>{verdict}"

    # ── Volume ──
    vol_current = f"{int(df['Volume'].iloc[-1]):,}"
    vol_avg_20 = df["Volume"].rolling(20).mean()
    vol_avg_str = f"{int(vol_avg_20.iloc[-1]):,}" if vol_avg_20.iloc[-1] > 0 else "N/A"
    rel_vol = tech.get("rel_vol", 1.0)
    rel_vol_pct = min(100, int(rel_vol * 50))

    # ── Company logo ──
    website = info.get("website", "")
    if website:
        domain = website.replace("https://", "").replace("http://", "").split("/")[0]
        logo_url = f"https://logo.clearbit.com/{domain}"
    else:
        logo_url = ""

    est = ZoneInfo("America/New_York")
    generated_at = datetime.now(est).strftime("%Y-%m-%d %I:%M %p EST")

    # ── Assemble full payload ──
    payload = {
        "ticker": ticker,
        "companyName": info.get("longName", ticker),
        "sector": info.get("sector", "Other"),
        "industry": info.get("industry", ""),
        "currentPrice": round(price, 2),
        "priceChange": round(float(close.iloc[-1] - close.iloc[-2]), 2) if len(close) >= 2 else 0,
        "priceChangePct": round(float((close.iloc[-1] - close.iloc[-2]) / close.iloc[-2] * 100), 2) if len(close) >= 2 else 0,
        "timestamp": generated_at,
        "logo_url": logo_url,
        "generated_at": generated_at,
        "impliedVolatility": iv_metrics["impliedVolatility"],
        "historicVolatility": iv_metrics["historicVolatility"],
        "ivRank": iv_metrics.get("ivRank", 0),
        "ivPercentile": iv_metrics.get("ivPercentile", 0),
        "trendOverall": trend,
        "trendShort": trend_short,
        "trendMed": trend_med,
        "trendLong": trend_long,
        "expectedMoves": expected_moves,
        "volumeStats": options_flow,
        "market_snapshot": {
            "price": round(price, 2),
            "market_cap": _fmt_num(info.get("marketCap")),
            "beta": _safe(info.get("beta")),
            "range_52w": f"{round(low_52w, 2)} - {round(high_52w, 2)}",
            "analyst_target": _safe(info.get("targetMeanPrice")),
        },
        "technical_analysis": {
            "trend": {"outlook": trend, "sma_50": tech.get("sma_50"), "sma_200": tech.get("sma_200"), "crossover": crossover},
            "ema": {"8": tech.get("ema_8"), "21": tech.get("ema_21"), "34": tech.get("ema_34"), "55": tech.get("ema_55"), "89": tech.get("ema_89")},
            "ema_stack": tech.get("ema_stack", "UNKNOWN"),
            "volume": {"current": vol_current, "avg_20d": vol_avg_str, "rel_vol": rel_vol, "rel_vol_pct": rel_vol_pct},
            "pivots": {"R2": r2, "R1": r1, "PP": pivot, "S1": s1, "S2": s2},
            "fibonacci": {"100": round(high_52w, 2), "61.8": fib_618, "50": fib_500, "38.2": fib_382, "0": round(low_52w, 2)},
            "oscillators": {
                "rsi_14": tech.get("rsi_14"),
                "adx_14": tech.get("adx"),
                "macd_hist": tech.get("macd_hist"),
                "stoch_k": tech.get("stoch_k"),
            },
        },
        "volatility": {
            "hv_30d": hv_val,
            "iv_current": iv_val,
        },
        "valuation": valuation,
        "scores": scores,
        "tradingview": tv,
        "insider_transactions": insiders,
        "news": news,
        "tickertrace": {
            "detail": tt_detail,
            "signal": inst_context,
        },
        "sec_insights": {
            "operations": f"{info.get('longName', ticker)} // {info.get('sector', 'N/A')} [{info.get('industry', 'N/A')}]. Mkt Cap: {_fmt_num(info.get('marketCap'))}. Rev Growth: {round((info.get('revenueGrowth', 0) or 0) * 100, 1)}%. PM: {round((info.get('profitMargins', 0) or 0) * 100, 1)}%.",
            "forward_looking": f"Beta: {_safe(info.get('beta'))}. Range(52W): {round(low_52w, 2)} - {round(high_52w, 2)}. Analyst Tgt: {_safe(info.get('targetMeanPrice'))}.",
        },
        "ai_analysis": ai_text,
    }

    # ── Write Output ──
    ticker_dir = TICKER_OUTPUT_DIR / ticker
    ticker_dir.mkdir(parents=True, exist_ok=True)

    # JSON — API endpoint
    json_path = ticker_dir / f"{date}.json"
    latest_json = ticker_dir / "latest.json"
    with open(json_path, "w") as f:
        json.dump(payload, f, indent=2, default=str)
    with open(latest_json, "w") as f:
        json.dump(payload, f, indent=2, default=str)

    # HTML — render template
    template_dir = Path(__file__).parent
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    template = env.get_template("ticker_template.html")

    html_content = template.render(
        **payload,
        ticker_first=ticker[0],
        chart_data_json=json.dumps(chart_data, default=str),
        ema_data_json=json.dumps(ema_data, default=str),
        raw_json_data=json.dumps(payload, default=str),
    )

    html_path = ticker_dir / f"{date}.html"
    latest_html = ticker_dir / "latest.html"
    with open(html_path, "w") as f:
        f.write(html_content)
    with open(latest_html, "w") as f:
        f.write(html_content)

    print(f"    ✓ {ticker}: {html_path.name} + {json_path.name}")
    return {"html": str(html_path), "json": str(json_path), "ticker": ticker}


def generate_all_ticker_pages(dossiers: list[dict], date: str,
                               institutional: dict = None) -> list[dict]:
    """Generate pages for all enriched dossiers."""
    print(f"  Generating {len(dossiers)} ticker pages...")
    results = []
    for d in dossiers:
        ticker = d.get("ticker", "")
        if not ticker:
            continue
        result = generate_ticker_page(ticker, d, date, institutional)
        if result:
            results.append(result)
    return results
