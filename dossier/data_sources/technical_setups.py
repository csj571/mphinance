"""
Technical Setups — EMA Stack Analysis & Bounce 2.0 Setup Detection

Based on the Tao of Trading methodology:
- EMA Stack: 8 → 21 → 34 → 55 → 89 alignment
- Trend Status: Sailing (above SMA 200) / Sinking (below)
- Buy Zone: Price within 0.2x ATR of EMA 21
- Bounce 2.0: Stacked EMAs + ADX ≥ 20 + Stoch ≤ 40
- Squeeze Ratio: ATR(14) vs Weekly ATR compression
"""

import yfinance as yf
import pandas as pd
import numpy as np


def _ema(series, span):
    return series.ewm(span=span, adjust=False).mean()


def _sma(series, window):
    return series.rolling(window=window).mean()


def _rsi(series, window=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def _stochastic(high, low, close, k_period=14, d_period=3):
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()
    k = 100 * ((close - lowest_low) / (highest_high - lowest_low))
    d = k.rolling(window=d_period).mean()
    return k, d


def _trama(series, length=34):
    """Trend-following Regularized Adaptive Moving Average."""
    ema1 = _ema(series, length)
    ema2 = _ema(ema1, length)
    return 2 * ema1 - ema2


def _safe(val, decimals=2):
    if val is None:
        return None
    try:
        f = float(val)
        if np.isnan(f) or np.isinf(f):
            return None
        return round(f, decimals)
    except (ValueError, TypeError):
        return None


def analyze_setup(ticker: str) -> dict | None:
    """
    Full technical setup analysis for a single ticker.

    Returns the Tao of Trading technical stack:
    - EMA Stack status and values
    - Trend status (Sailing/Sinking)
    - Buy Zone detection
    - Bounce 2.0 qualification
    - Technical Data Sack (all indicators)
    """
    print(f"    Analyzing setup: {ticker}...")

    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="6mo")
        if df.empty or len(df) < 90:
            return None
    except Exception as e:
        print(f"    [ERR] {ticker}: {e}")
        return None

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]
    price = float(close.iloc[-1])

    # ── EMA Stack ──
    ema_8 = _ema(close, 8)
    ema_21 = _ema(close, 21)
    ema_34 = _ema(close, 34)
    ema_55 = _ema(close, 55)
    ema_89 = _ema(close, 89)
    sma_50 = _sma(close, 50)
    sma_200 = _sma(close, 200) if len(close) >= 200 else _sma(close, len(close))
    trama_34 = _trama(close, 34)

    e8 = _safe(ema_8.iloc[-1])
    e21 = _safe(ema_21.iloc[-1])
    e34 = _safe(ema_34.iloc[-1])
    e55 = _safe(ema_55.iloc[-1])
    e89 = _safe(ema_89.iloc[-1])
    s50 = _safe(sma_50.iloc[-1])
    s200 = _safe(sma_200.iloc[-1])
    t34 = _safe(trama_34.iloc[-1])

    # EMA Stack Status
    if e8 and e21 and e34 and e55 and e89:
        if e8 > e21 > e34 > e55 > e89:
            ema_stack = "FULL BULLISH"
            ema_stack_desc = "8 → 21 → 34 → 55 → 89 alignment"
        elif e8 > e21 > e34:
            ema_stack = "PARTIAL BULLISH"
            ema_stack_desc = "8 → 21 → 34 aligned, outer diverging"
        elif e89 > e55 > e34 > e21 > e8:
            ema_stack = "FULL BEARISH"
            ema_stack_desc = "89 → 55 → 34 → 21 → 8 alignment"
        elif e34 > e21 > e8:
            ema_stack = "PARTIAL BEARISH"
            ema_stack_desc = "Inner EMAs bearish stacked"
        else:
            ema_stack = "TANGLED"
            ema_stack_desc = "No clear alignment"
    else:
        ema_stack = "INSUFFICIENT DATA"
        ema_stack_desc = "Not enough history"

    # ── Trend Status ──
    if s200:
        if price > s200:
            trend_status = "SAILING"
            trend_desc = f"Above SMA 200 (${s200})"
        else:
            trend_status = "SINKING"
            trend_desc = f"Below SMA 200 (${s200})"
    else:
        trend_status = "UNKNOWN"
        trend_desc = "Insufficient data for SMA 200"

    # ── ATR ──
    tr = pd.concat([
        high - low,
        abs(high - close.shift()),
        abs(low - close.shift()),
    ], axis=1).max(axis=1)
    atr_14 = float(tr.rolling(14).mean().iloc[-1])

    # ── Buy Zone (within 0.2x ATR of EMA 21) ──
    if e21 and atr_14:
        dist_to_ema21 = abs(price - e21)
        in_buy_zone = dist_to_ema21 <= (0.2 * atr_14)
        buy_zone_desc = f"EMA21: ${e21}"
    else:
        in_buy_zone = False
        buy_zone_desc = "N/A"

    # Keltner Channels (1, 2, 3 ATR around EMA 21)
    keltner = None
    if e21 and atr_14:
        keltner = {
            "upper_1": _safe(e21 + atr_14),
            "lower_1": _safe(e21 - atr_14),
            "upper_2": _safe(e21 + 2 * atr_14),
            "lower_2": _safe(e21 - 2 * atr_14),
            "upper_3": _safe(e21 + 3 * atr_14),
            "lower_3": _safe(e21 - 3 * atr_14),
        }

    # ── Indicators ──
    rsi_14 = _safe(_rsi(close, 14).iloc[-1])
    rsi_2 = _safe(_rsi(close, 2).iloc[-1])

    macd_line = _ema(close, 12) - _ema(close, 26)
    macd_signal = _ema(macd_line, 9)
    macd_hist = macd_line - macd_signal
    macd_val = _safe(macd_hist.iloc[-1], 4)

    stoch_k, stoch_d = _stochastic(high, low, close)
    stoch_k_val = _safe(stoch_k.iloc[-1])

    # ADX
    plus_dm = high.diff()
    minus_dm = -low.diff()
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
    tr_smooth = tr.rolling(14).sum()
    plus_di = 100 * (plus_dm.rolling(14).sum() / tr_smooth)
    minus_di = 100 * (minus_dm.rolling(14).sum() / tr_smooth)
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx_val = _safe(dx.rolling(14).mean().iloc[-1])

    # Squeeze Ratio
    atr_weekly_equiv = float(tr.rolling(5).mean().iloc[-1])  # 5-day approx
    squeeze_ratio = round(atr_14 / (atr_weekly_equiv * 2), 3) if atr_weekly_equiv > 0 else 1.0

    # Volume
    vol_current = int(volume.iloc[-1])
    vol_avg_10d = float(volume.rolling(10).mean().iloc[-1])
    rel_vol = round(vol_current / vol_avg_10d, 2) if vol_avg_10d > 0 else 1.0

    # Change
    prev_close = float(close.iloc[-2]) if len(close) >= 2 else price
    change = round(price - prev_close, 4)

    # Info
    info = {}
    try:
        info = stock.info or {}
    except Exception:
        pass

    # ── Bounce 2.0 Qualification ──
    # Criteria: Stacked EMAs + ADX >= 20 + Stoch K <= 40
    bounce_2_qualified = (
        ema_stack in ("FULL BULLISH", "PARTIAL BULLISH")
        and adx_val is not None and adx_val >= 20
        and stoch_k_val is not None and stoch_k_val <= 40
    )

    bounce_2_bearish = (
        ema_stack in ("FULL BEARISH", "PARTIAL BEARISH")
        and adx_val is not None and adx_val >= 20
        and stoch_k_val is not None and stoch_k_val >= 60
    )

    # ── Risk/Reward (based on Keltner Channels) ──
    risk_reward = None
    if keltner and in_buy_zone and atr_14:
        risk = abs(price - keltner["lower_1"])
        reward = abs(keltner["upper_2"] - price)
        if risk > 0:
            risk_reward = round(reward / risk, 2)

    return {
        "ticker": ticker,
        "name": info.get("longName", ticker),
        "sector": info.get("sector", "N/A"),
        "price": round(price, 2),
        "change": change,

        # EMA Stack
        "ema_stack": ema_stack,
        "ema_stack_desc": ema_stack_desc,

        # Trend Status
        "trend_status": trend_status,
        "trend_desc": trend_desc,

        # Buy Zone
        "in_buy_zone": in_buy_zone,
        "buy_zone_desc": buy_zone_desc,

        # Bounce 2.0
        "bounce_2_bullish": bounce_2_qualified,
        "bounce_2_bearish": bounce_2_bearish,

        # Technical Data Sack
        "data_sack": {
            "volume": f"{vol_current / 1_000_000:.2f}M" if vol_current >= 1_000_000 else f"{vol_current / 1_000:.0f}K",
            "rel_vol_10d": rel_vol,
            "squeeze_ratio": squeeze_ratio,
            "risk_reward": risk_reward,
            "adx_14": adx_val,
            "rsi_14": rsi_14,
            "rsi_2": rsi_2,
            "macd": macd_val,
            "stoch_k": stoch_k_val,
            "ema_8": e8,
            "ema_21": e21,
            "ema_34": e34,
            "ema_55": e55,
            "ema_89": e89,
            "sma_50": s50,
            "ema_200": s200,
            "trama_34": t34,
            "atr": _safe(atr_14),
        },

        # Keltner
        "keltner": keltner,
    }


def generate_setups(tickers: list[str], max_setups: int = 6) -> list[dict]:
    """
    Analyze tickers and return the best setups, prioritizing:
    1. Bounce 2.0 qualified (Tao of Trading sweet spot)
    2. Buy Zone entries
    3. Full Bullish EMA stacks
    """
    print(f"  Analyzing {len(tickers)} tickers for setups...")
    setups = []

    for ticker in tickers[:max_setups * 2]:  # Oversample to filter
        result = analyze_setup(ticker)
        if result:
            setups.append(result)

    # Prioritize: Bounce 2.0 first, then Buy Zone, then Full Bullish
    def setup_priority(s):
        score = 0
        if s["bounce_2_bullish"]:
            score += 100
        if s["in_buy_zone"]:
            score += 50
        if s["ema_stack"] == "FULL BULLISH":
            score += 25
        elif s["ema_stack"] == "PARTIAL BULLISH":
            score += 10
        if s["trend_status"] == "SAILING":
            score += 15
        return -score  # Negative for ascending sort

    setups.sort(key=setup_priority)
    return setups[:max_setups]
