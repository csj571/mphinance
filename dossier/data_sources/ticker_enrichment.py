"""
Ticker Enrichment — Comprehensive per-ticker data assembly.

Fetches fundamentals, technicals, valuation, options, insiders,
TradingView signals, and news for a single ticker.
"""

import yfinance as yf
import pandas as pd
import numpy as np
import feedparser


# ─── Technical Indicator Functions ────────────────────────────────

def _sma(series, window):
    return series.rolling(window=window).mean()

def _ema(series, span):
    return series.ewm(span=span, adjust=False).mean()

def _rsi(series, window=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def _macd(series, fast=12, slow=26, signal=9):
    ema_fast = _ema(series, fast)
    ema_slow = _ema(series, slow)
    macd = ema_fast - ema_slow
    signal_line = _ema(macd, signal)
    hist = macd - signal_line
    return macd, signal_line, hist


# ─── TradingView Summary ─────────────────────────────────────────

def _tradingview_summary(ticker: str, exchange: str) -> dict:
    """Get TradingView technical analysis summary."""
    try:
        from tradingview_ta import TA_Handler, Interval
        exchange_map = {
            "NMS": "NASDAQ", "NYQ": "NYSE", "NGM": "NASDAQ",
            "ASE": "AMEX", "PCX": "ARCA",
        }
        tv_exchange = exchange_map.get(exchange, "NASDAQ")
        handler = TA_Handler(
            symbol=ticker, screener="america",
            exchange=tv_exchange, interval=Interval.INTERVAL_1_DAY,
        )
        analysis = handler.get_analysis()
        return {
            "recommendation": analysis.summary.get("RECOMMENDATION", "N/A"),
            "buy": analysis.summary.get("BUY", 0),
            "sell": analysis.summary.get("SELL", 0),
            "neutral": analysis.summary.get("NEUTRAL", 0),
        }
    except Exception:
        return {"recommendation": "N/A", "buy": 0, "sell": 0, "neutral": 0}


# ─── Valuation Model ─────────────────────────────────────────────

def _intrinsic_value(info: dict, current_price: float) -> dict:
    """Multi-model consensus valuation: Graham + Lynch + Analyst."""
    eps = info.get("trailingEps", 0) or 0
    bvps = info.get("bookValue", 0) or 0
    rev_growth = info.get("revenueGrowth", 0) or 0
    analyst_target = float(info.get("targetMeanPrice", 0) or 0)

    graham = 0
    if eps > 0 and bvps > 0:
        try:
            graham = float(np.sqrt(22.5 * eps * bvps))
        except Exception:
            pass

    lynch = 0
    if eps > 0 and rev_growth > 0:
        lynch = eps * (rev_growth * 100)

    is_profitable = eps > 0
    has_analyst = analyst_target > 0
    final_value = 0
    method_str = "UNKNOWN"

    if is_profitable:
        candidates = []
        methods = []
        if graham > 0:
            candidates.append(graham)
            methods.append("Graham")
        if lynch > 0:
            candidates.append(lynch)
            methods.append("Lynch")
        if has_analyst:
            candidates.append(analyst_target)
            methods.append("Analyst")
        if candidates:
            final_value = sum(candidates) / len(candidates)
            method_str = "BLENDED (" + "+".join(methods) + ")"
        else:
            method_str = "INSUFFICIENT DATA"
    else:
        if has_analyst:
            final_value = analyst_target
            method_str = "ANALYST CONSENSUS"

    gap = 0
    status = "UNKNOWN"
    if final_value > 0:
        gap = ((final_value - current_price) / current_price) * 100
        if gap > 20:
            status = "UNDERVALUED"
        elif gap < -20:
            status = "OVERVALUED"
        else:
            status = "FAIR VALUE"

    return {
        "status": status,
        "gap_pct": round(gap, 1),
        "target_price": round(final_value, 2),
        "method": method_str,
    }


# ─── News Fetcher ────────────────────────────────────────────────

def _fetch_news(ticker: str) -> list[dict]:
    """Get ticker-specific news from Yahoo Finance RSS."""
    items = []
    try:
        feed = feedparser.parse(
            f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}"
        )
        for entry in feed.entries[:5]:
            items.append({
                "title": entry.get("title", "No Title"),
                "link": entry.get("link", ""),
                "summary": (entry.get("summary", "") or "")[:150],
                "source": "Yahoo Finance",
            })
    except Exception:
        pass
    return items


# ─── Format Helpers ───────────────────────────────────────────────

def _fmt_num(num) -> str:
    if num is None:
        return "N/A"
    try:
        num = float(num)
        if num >= 1_000_000_000:
            return f"${num / 1_000_000_000:.2f}B"
        elif num >= 1_000_000:
            return f"${num / 1_000_000:.2f}M"
        else:
            return f"${num:,.0f}"
    except (ValueError, TypeError):
        return str(num)


def _safe(val, decimals=2):
    """Safely round a value, returning None for NaN/Inf."""
    if val is None:
        return None
    try:
        f = float(val)
        if np.isnan(f) or np.isinf(f):
            return None
        return round(f, decimals)
    except (ValueError, TypeError):
        return None


# ─── Main Enrichment Function ────────────────────────────────────

def enrich_ticker(ticker: str) -> dict | None:
    """
    Full enrichment for a single ticker.

    Returns a comprehensive data dict with fundamentals, technicals,
    valuation, options IV, insider activity, TradingView summary,
    news, scoring & verdict.
    """
    print(f"    Enriching {ticker}...")
    stock = yf.Ticker(ticker)

    # ── Price History ──
    try:
        df = stock.history(period="1y")
        if df.empty:
            print(f"    [WARN] No price data for {ticker}")
            return None
    except Exception as e:
        print(f"    [ERR] {ticker} history: {e}")
        return None

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    latest = df.iloc[-1]
    price = float(latest["Close"])

    # ── Technicals ──
    ema_8 = _ema(close, 8)
    ema_21 = _ema(close, 21)
    ema_34 = _ema(close, 34)
    ema_55 = _ema(close, 55)
    ema_89 = _ema(close, 89)
    sma_50 = _sma(close, 50)
    sma_200 = _sma(close, 200)
    rsi = _rsi(close)
    macd_line, signal_line, macd_hist = _macd(close)

    # TRAMA (34)
    trama_ema1 = _ema(close, 34)
    trama_ema2 = _ema(trama_ema1, 34)
    trama_34 = 2 * trama_ema1 - trama_ema2

    # ATR
    tr = pd.concat([
        high - low,
        abs(high - close.shift()),
        abs(low - close.shift()),
    ], axis=1).max(axis=1)
    atr = tr.rolling(14).mean()

    # Stochastic %K
    lowest_low = low.rolling(14).min()
    highest_high = high.rolling(14).max()
    stoch_k = 100 * ((close - lowest_low) / (highest_high - lowest_low))

    # ADX
    plus_dm = high.diff()
    minus_dm = -low.diff()
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
    tr_smooth = tr.rolling(14).sum()
    plus_di = 100 * (plus_dm.rolling(14).sum() / tr_smooth)
    minus_di = 100 * (minus_dm.rolling(14).sum() / tr_smooth)
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(14).mean()

    # Squeeze Ratio
    atr_val = float(atr.iloc[-1])
    atr_5d = float(tr.rolling(5).mean().iloc[-1])
    squeeze_ratio = round(atr_val / (atr_5d * 2), 3) if atr_5d > 0 else 1.0

    # Historical Volatility
    log_ret = np.log(close / close.shift(1))
    hv_30 = float(log_ret.rolling(30).std().iloc[-1] * np.sqrt(252) * 100)

    # Relative Volume
    vol_avg = df["Volume"].rolling(20).mean()
    rel_vol = float(df["Volume"].iloc[-1] / vol_avg.iloc[-1]) if vol_avg.iloc[-1] > 0 else 1.0
    vol_avg_20 = int(vol_avg.iloc[-1]) if vol_avg.iloc[-1] > 0 else 0

    # ── EMA Stack Status ──
    e8 = _safe(ema_8.iloc[-1])
    e21 = _safe(ema_21.iloc[-1])
    e34 = _safe(ema_34.iloc[-1])
    e55 = _safe(ema_55.iloc[-1])
    e89 = _safe(ema_89.iloc[-1])
    if e8 and e21 and e34 and e55 and e89:
        if e8 > e21 > e34 > e55 > e89:
            ema_stack = "FULL BULLISH"
        elif e8 > e21 > e34:
            ema_stack = "PARTIAL BULLISH"
        elif e89 > e55 > e34 > e21 > e8:
            ema_stack = "FULL BEARISH"
        elif e34 > e21 > e8:
            ema_stack = "PARTIAL BEARISH"
        else:
            ema_stack = "TANGLED"
    else:
        ema_stack = "UNKNOWN"

    # ── Pivot Points (Classic) ──
    prev_h = float(high.iloc[-2]) if len(high) >= 2 else float(high.iloc[-1])
    prev_l = float(low.iloc[-2]) if len(low) >= 2 else float(low.iloc[-1])
    prev_c = float(close.iloc[-2]) if len(close) >= 2 else price
    pivot = (prev_h + prev_l + prev_c) / 3
    r1 = 2 * pivot - prev_l
    r2 = pivot + (prev_h - prev_l)
    s1 = 2 * pivot - prev_h
    s2 = pivot - (prev_h - prev_l)

    # ── Fibonacci Retracement (using 52-week range) ──
    high_52w = float(high.max())
    low_52w = float(low.min())
    fib_range = high_52w - low_52w
    fib_618 = high_52w - fib_range * 0.618
    fib_500 = high_52w - fib_range * 0.500
    fib_382 = high_52w - fib_range * 0.382

    # ── Options IV ──
    iv = 0
    try:
        expirations = stock.options
        if expirations:
            exp = expirations[min(2, len(expirations) - 1)]
            calls = stock.option_chain(exp).calls
            atm = calls[
                (calls["strike"] >= price * 0.95) &
                (calls["strike"] <= price * 1.05)
            ]
            if not atm.empty:
                iv = round(float(atm["impliedVolatility"].mean() * 100), 2)
    except Exception:
        pass

    # ── Fundamentals ──
    info = {}
    try:
        info = stock.info or {}
    except Exception:
        pass

    # ── Insider Activity ──
    insider_data = []
    try:
        insiders = stock.insider_transactions
        if isinstance(insiders, pd.DataFrame) and not insiders.empty:
            for _, row in insiders.head(5).iterrows():
                date_val = row.get("Start Date") or row.get("Date")
                date_str = date_val.strftime("%Y-%m-%d") if isinstance(date_val, pd.Timestamp) else str(date_val)
                val = row.get("Value")
                insider_data.append({
                    "date": date_str,
                    "insider": row.get("Insider", "Unknown"),
                    "type": row.get("Transaction", "Unknown"),
                    "value": _fmt_num(val) if isinstance(val, (int, float)) else str(val),
                })
    except Exception:
        pass

    # ── TradingView ──
    exchange = info.get("exchange", "NMS")
    tv = _tradingview_summary(ticker, exchange)

    # ── Valuation ──
    valuation = _intrinsic_value(info, price)

    # ── News ──
    news = _fetch_news(ticker)

    # ── Scoring ──
    sma_50_val = _safe(sma_50.iloc[-1]) or price
    sma_200_val = _safe(sma_200.iloc[-1]) or price
    rsi_val = _safe(rsi.iloc[-1])

    tech_score = 50
    if sma_50_val > sma_200_val:
        tech_score += 20
    else:
        tech_score -= 20
    if price > sma_50_val:
        tech_score += 10
    else:
        tech_score -= 10
    if price > sma_200_val:
        tech_score += 10
    else:
        tech_score -= 10
    if rsi_val:
        if 40 < rsi_val < 60:
            tech_score += 5
        elif 30 < rsi_val <= 40 or 60 <= rsi_val < 70:
            tech_score += 10
        elif rsi_val >= 70 or rsi_val <= 30:
            tech_score -= 5
    tech_score = max(0, min(100, tech_score))

    fund_score = 50
    if (info.get("profitMargins") or 0) > 0.1:
        fund_score += 10
    if (info.get("revenueGrowth") or 0) > 0.05:
        fund_score += 10
    insider_sentiment = sum(
        1 if "Purchase" in i.get("type", "") else -1 if "Sale" in i.get("type", "") else 0
        for i in insider_data
    )
    if insider_sentiment > 0:
        fund_score += 10
    elif insider_sentiment < 0:
        fund_score -= 5
    tgt = info.get("targetMeanPrice")
    if tgt and float(tgt) > price:
        fund_score += 10
    fund_score = max(0, min(100, fund_score))

    avg_score = (tech_score + fund_score) / 2
    grade = "A" if avg_score > 80 else "B" if avg_score > 60 else "C" if avg_score > 40 else "D"

    # ── Verdict ──
    if tech_score > 60 and valuation["status"] != "OVERVALUED":
        verdict = "ACCUMULATE on dips"
    elif tech_score < 40:
        verdict = "DISTRIBUTE into strength"
    else:
        verdict = "WAIT for validation"

    trend = "Bullish" if sma_50_val > sma_200_val else "Bearish"
    crossover = "Golden Cross" if sma_50_val > sma_200_val else "Death Cross"

    return {
        "ticker": ticker,
        "name": info.get("longName", ticker),
        "sector": info.get("sector", "N/A"),
        "industry": info.get("industry", "N/A"),
        "price": round(price, 2),
        "market_cap": _fmt_num(info.get("marketCap")),
        "pe_ratio": _safe(info.get("trailingPE")),
        "fwd_pe": _safe(info.get("forwardPE")),
        "revenue_growth": _safe((info.get("revenueGrowth") or 0) * 100, 1),
        "profit_margin": _safe((info.get("profitMargins") or 0) * 100, 1),
        "beta": _safe(info.get("beta")),
        "range_52w": f"${info.get('fiftyTwoWeekLow', 0)} — ${info.get('fiftyTwoWeekHigh', 0)}",
        "analyst_target": _safe(info.get("targetMeanPrice")),
        "technicals": {
            "trend": trend,
            "crossover": crossover,
            "ema_stack": ema_stack,
            "ema_8": e8,
            "ema_21": e21,
            "ema_34": e34,
            "ema_55": e55,
            "ema_89": e89,
            "sma_50": _safe(sma_50.iloc[-1]),
            "sma_200": _safe(sma_200.iloc[-1]),
            "trama_34": _safe(trama_34.iloc[-1]),
            "rsi_14": rsi_val,
            "macd_hist": _safe(macd_hist.iloc[-1]),
            "stoch_k": _safe(stoch_k.iloc[-1]),
            "adx": _safe(adx.iloc[-1]),
            "atr": _safe(atr.iloc[-1]),
            "squeeze_ratio": squeeze_ratio,
            "rel_vol": round(rel_vol, 2),
            "vol_avg_20": f"{vol_avg_20:,}",
            # Pivot Points
            "pivot": _safe(pivot),
            "r1": _safe(r1),
            "r2": _safe(r2),
            "s1": _safe(s1),
            "s2": _safe(s2),
            # Fibonacci
            "fib_618": _safe(fib_618),
            "fib_500": _safe(fib_500),
            "fib_382": _safe(fib_382),
        },
        "volatility": {
            "hv_30d": round(hv_30, 2) if not np.isnan(hv_30) else None,
            "iv_current": iv,
            "iv_hv_spread": round(iv - hv_30, 2) if iv and not np.isnan(hv_30) else None,
        },
        "valuation": valuation,
        "tradingview": tv,
        "insiders": insider_data,
        "news": news[:3],
        "scores": {
            "technical": tech_score,
            "fundamental": fund_score,
            "grade": grade,
        },
        "verdict": verdict,
    }
