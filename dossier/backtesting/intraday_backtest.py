#!/usr/bin/env python3
"""
👻 Intraday Backtest Engine — 2x Leveraged ETF Day Trading Strategy

Tests the EXACT strategy from "The $3K/Week Playbook" against real historical
5-minute candle data. Validates every parameter:

  1. Entry timing: 9:30 to 11:00 in 5-min increments
  2. Exit method: ATR trailing stop at 0.5x, 0.75x, 1.0x, 1.25x, 1.5x, 2.0x
  3. SPY ADX threshold: 15, 18, 20, 22, 25
  4. Signal count cap: 15, 20, 25, 30, 999 (no cap)
  5. Position sizing: multiple configs

Data: yfinance 5-minute candles (~60 trading days available)
ADX: Computed from daily/hourly candles via Wilder's smoothing

Usage:
    python3 -m dossier.backtesting.intraday_backtest
    python3 -m dossier.backtesting.intraday_backtest --quick
    python3 -m dossier.backtesting.intraday_backtest --save results.json
    python3 -m dossier.backtesting.intraday_backtest --sweep

© mphinance + Sam the Quant Ghost
Updated: 2026-04-03
"""

import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime, timedelta, time as dtime
from collections import defaultdict
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import pickle
import os

try:
    import yfinance as yf
except ImportError:
    print("pip install yfinance")
    sys.exit(1)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dossier.data_sources.leveraged_etf_map import (
    LEVERAGED_2X_MAP,
    get_all_underlyings,
)

EST = ZoneInfo("America/New_York")
CST = ZoneInfo("America/Chicago")


# ══════════════════════════════════════════════════════════════════════════════
# TECHNICAL INDICATORS (pure functions)
# ══════════════════════════════════════════════════════════════════════════════

def compute_atr(highs: list, lows: list, closes: list, period: int = 14) -> list:
    """Wilder's Average True Range."""
    if len(closes) < 2:
        return []
    trs = []
    for i in range(1, len(closes)):
        tr = max(highs[i] - lows[i],
                 abs(highs[i] - closes[i-1]),
                 abs(lows[i] - closes[i-1]))
        trs.append(tr)
    if len(trs) < period:
        return [sum(trs) / len(trs)] if trs else []

    atr = sum(trs[:period]) / period
    result = [atr]
    for i in range(period, len(trs)):
        atr = (atr * (period - 1) + trs[i]) / period
        result.append(atr)
    return result


def compute_adx(highs: list, lows: list, closes: list, period: int = 14) -> list:
    """Wilder's ADX with DI+/DI- direction. Returns list of (adx, di_plus, di_minus)."""
    if len(closes) < period * 2 + 1:
        return []
    tr_list, plus_dm, minus_dm = [], [], []
    for i in range(1, len(closes)):
        h, l, c_prev = highs[i], lows[i], closes[i-1]
        h_prev, l_prev = highs[i-1], lows[i-1]
        tr = max(h - l, abs(h - c_prev), abs(l - c_prev))
        tr_list.append(tr)
        up_move = h - h_prev
        down_move = l_prev - l
        plus_dm.append(up_move if up_move > down_move and up_move > 0 else 0)
        minus_dm.append(down_move if down_move > up_move and down_move > 0 else 0)

    if len(tr_list) < period:
        return []

    atr = sum(tr_list[:period])
    apdm = sum(plus_dm[:period])
    amdm = sum(minus_dm[:period])
    dx_list = []
    di_data = []

    for i in range(period, len(tr_list)):
        atr = atr - (atr / period) + tr_list[i]
        apdm = apdm - (apdm / period) + plus_dm[i]
        amdm = amdm - (amdm / period) + minus_dm[i]
        plus_di = (apdm / atr) * 100 if atr > 0 else 0
        minus_di = (amdm / atr) * 100 if atr > 0 else 0
        di_sum = plus_di + minus_di
        dx = abs(plus_di - minus_di) / di_sum * 100 if di_sum > 0 else 0
        dx_list.append(dx)
        di_data.append((plus_di, minus_di))

    if len(dx_list) < period:
        return []

    adx_val = sum(dx_list[:period]) / period
    result = [(adx_val, di_data[period-1][0], di_data[period-1][1])]
    for i in range(period, len(dx_list)):
        adx_val = (adx_val * (period - 1) + dx_list[i]) / period
        result.append((adx_val, di_data[i][0], di_data[i][1]))
    return result


def compute_relative_volume(volumes: list, lookback: int = 10) -> float:
    """Current volume / average of last N days."""
    if len(volumes) < lookback + 1:
        return 0.0
    avg = sum(volumes[-lookback-1:-1]) / lookback
    return volumes[-1] / avg if avg > 0 else 0.0


# ══════════════════════════════════════════════════════════════════════════════
# DATA FETCHING WITH CACHE
# ══════════════════════════════════════════════════════════════════════════════

import pickle
import os

CACHE_DIR = Path("/tmp/yfinance_intraday_cache")
CACHE_FILE = CACHE_DIR / "cache.pkl"

_DATA_CACHE = {}

def _init_cache():
    global _DATA_CACHE
    if not _DATA_CACHE and CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "rb") as f:
                _DATA_CACHE = pickle.load(f)
        except Exception:
            _DATA_CACHE = {}

def _save_cache():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "wb") as f:
        pickle.dump(_DATA_CACHE, f)

def _flatten_cols(df):
    """Flatten MultiIndex columns from yfinance >= 0.2.x."""
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)
    return df


def preload_all_data():
    """Bulk download all needed data in just 3 yfinance requests to avoid rate limits."""
    _init_cache()
    
    underlyings = get_all_underlyings()
    from dossier.data_sources.leveraged_etf_map import LEVERAGED_2X_MAP
    etfs = []
    for u in underlyings:
        if u in LEVERAGED_2X_MAP:
            if LEVERAGED_2X_MAP[u].get("bull"): etfs.extend(LEVERAGED_2X_MAP[u]["bull"])
            if LEVERAGED_2X_MAP[u].get("bear"): etfs.extend(LEVERAGED_2X_MAP[u]["bear"])
    etfs = list(set(etfs))
    
    # Also fetch 5m data for underlyings as fallback when ETF data is missing
    all_5m_tickers = list(set(etfs + list(underlyings)))
    
    missing_1d = [t for t in underlyings if f"1d_{t}" not in _DATA_CACHE]
    missing_1h = ["SPY"] if "1h_SPY" not in _DATA_CACHE else []
    missing_5m = [t for t in all_5m_tickers if f"5m_{t}" not in _DATA_CACHE]
    
    if missing_1h:
        print(f"\n  [CACHE] Fetching 1h data for SPY...", flush=True)
        try:
            df_1h = yf.download("SPY", period="90d", interval="1h", progress=False, auto_adjust=True)
            if df_1h is not None and not df_1h.empty:
                _DATA_CACHE["1h_SPY"] = _flatten_cols(df_1h)
                _save_cache()
        except Exception as e:
            print(f"  [WARN] SPY 1h fetch failed: {e}")

    if missing_1d:
        print(f"\n  [CACHE] Bulk fetching 1d data for {len(missing_1d)} underlyings...", flush=True)
        try:
            df_1d = yf.download(" ".join(missing_1d), period="120d", interval="1d", progress=False, auto_adjust=True)
            if df_1d is not None and not df_1d.empty:
                if len(missing_1d) == 1:
                    _DATA_CACHE[f"1d_{missing_1d[0]}"] = _flatten_cols(df_1d)
                elif isinstance(df_1d.columns, pd.MultiIndex):
                    for t in missing_1d:
                        if t in df_1d.columns.get_level_values(1):
                            df_t = df_1d.xs(t, level=1, axis=1).dropna(how='all')
                            if not df_t.empty:
                                _DATA_CACHE[f"1d_{t}"] = df_t
                            else:
                                _DATA_CACHE[f"1d_{t}"] = None
                        else:
                            _DATA_CACHE[f"1d_{t}"] = None
            _save_cache()
        except Exception as e:
            print(f"  [WARN] Bulk 1d fetch failed: {e}")
            for t in missing_1d:
                if f"1d_{t}" not in _DATA_CACHE:
                    _DATA_CACHE[f"1d_{t}"] = None

    if missing_5m:
        print(f"\n  [CACHE] Bulk fetching 5m data for {len(missing_5m)} ETFs...", flush=True)
        try:
            chunk_size = 50
            for i in range(0, len(missing_5m), chunk_size):
                chunk = missing_5m[i:i+chunk_size]
                print(f"    -> Chunk {i//chunk_size + 1}/{len(missing_5m)//chunk_size + 1}: {len(chunk)} ETFs...", flush=True)
                df_5m = yf.download(" ".join(chunk), period="60d", interval="5m", progress=False, auto_adjust=True)
                if df_5m is not None and not df_5m.empty:
                    if len(chunk) == 1:
                        _DATA_CACHE[f"5m_{chunk[0]}"] = _flatten_cols(df_5m)
                    elif isinstance(df_5m.columns, pd.MultiIndex):
                        for t in chunk:
                            if t in df_5m.columns.get_level_values(1):
                                df_t = df_5m.xs(t, level=1, axis=1).dropna(how='all')
                                if not df_t.empty:
                                    _DATA_CACHE[f"5m_{t}"] = df_t
                                else:
                                    _DATA_CACHE[f"5m_{t}"] = None
                            else:
                                _DATA_CACHE[f"5m_{t}"] = None
                _save_cache()
        except Exception as e:
            print(f"  [WARN] Bulk 5m fetch failed: {e}")
            for t in missing_5m:
                if f"5m_{t}" not in _DATA_CACHE:
                    _DATA_CACHE[f"5m_{t}"] = None


def fetch_5m_data(ticker: str) -> pd.DataFrame | None:
    """Fetch 5-minute candles (max ~60 days from yfinance)."""
    _init_cache()
    key = f"5m_{ticker}"
    if key in _DATA_CACHE:
        return _DATA_CACHE[key]
    try:
        df = yf.download(ticker, period="60d", interval="5m",
                         progress=False, auto_adjust=True)
        if df is None or df.empty:
            return None
        df = _flatten_cols(df)
        _DATA_CACHE[key] = df
        _save_cache()
        return df
    except Exception as e:
        print(f"  [WARN] 5m fetch failed for {ticker}: {e}")
        return None


def fetch_1h_data(ticker: str) -> pd.DataFrame | None:
    """Fetch 1-hour candles (max ~730 days from yfinance)."""
    _init_cache()
    key = f"1h_{ticker}"
    if key in _DATA_CACHE:
        return _DATA_CACHE[key]
    try:
        df = yf.download(ticker, period="90d", interval="1h",
                         progress=False, auto_adjust=True)
        if df is None or df.empty:
            return None
        df = _flatten_cols(df)
        _DATA_CACHE[key] = df
        _save_cache()
        return df
    except Exception as e:
        print(f"  [WARN] 1h fetch failed for {ticker}: {e}")
        return None


def fetch_daily_data(ticker: str, days: int = 120) -> pd.DataFrame | None:
    """Fetch daily candles."""
    _init_cache()
    key = f"1d_{ticker}"
    if key in _DATA_CACHE:
        return _DATA_CACHE[key]
    try:
        df = yf.download(ticker, period=f"{days}d", interval="1d",
                         progress=False, auto_adjust=True)
        if df is None or df.empty:
            return None
        df = _flatten_cols(df)
        _DATA_CACHE[key] = df
        _save_cache()
        return df
    except Exception as e:
        print(f"  [WARN] daily fetch failed for {ticker}: {e}")
        return None


# ══════════════════════════════════════════════════════════════════════════════
# SPY REGIME FILTER
# ══════════════════════════════════════════════════════════════════════════════

def compute_spy_hourly_adx() -> dict:
    """
    Compute SPY's 1-hour ADX for each trading date.
    Returns: {date_str: {"adx": float, "di_plus": float, "di_minus": float, "trend": str}}
    """
    df = fetch_1h_data("SPY")
    if df is None or len(df) < 40:
        print("  [WARN] Not enough SPY hourly data for ADX")
        return {}

    highs = df["High"].values.tolist()
    lows = df["Low"].values.tolist()
    closes = df["Close"].values.tolist()

    adx_vals = compute_adx(highs, lows, closes, period=14)
    if not adx_vals:
        return {}

    # Map ADX values back to dates (last bar of each day)
    # ADX array starts after 2*period warmup bars
    offset = len(closes) - len(adx_vals)
    result = {}

    for i, (adx, dip, dim) in enumerate(adx_vals):
        bar_idx = i + offset
        if bar_idx >= len(df):
            break
        dt = df.index[bar_idx]
        date_str = dt.strftime("%Y-%m-%d") if hasattr(dt, 'strftime') else str(dt)[:10]
        trend = "BULL" if dip > dim else "BEAR"
        # Keep the latest value for each date (end-of-day ADX)
        result[date_str] = {
            "adx": round(adx, 1),
            "di_plus": round(dip, 1),
            "di_minus": round(dim, 1),
            "trend": trend,
        }

    return result


# ══════════════════════════════════════════════════════════════════════════════
# STOCK SELECTION: Which underlyings to trade each day
# ══════════════════════════════════════════════════════════════════════════════

def compute_daily_rankings() -> dict:
    """
    For each trading date, compute ADX + relative volume for all underlyings
    and rank them. Returns {date_str: [list of {ticker, adx, rel_vol, di_plus, di_minus} sorted by ADX desc]}
    """
    tickers = get_all_underlyings()
    print(f"\n  📊 Fetching daily data for {len(tickers)} underlyings...")

    all_daily = {}
    fetched = 0
    for t in tickers:
        df = fetch_daily_data(t, days=120)
        if df is not None and len(df) >= 40:
            all_daily[t] = df
            fetched += 1
    print(f"  ✓ Got daily data for {fetched}/{len(tickers)} underlyings")

    # Find common trading dates
    all_dates = set()
    for t, df in all_daily.items():
        for dt in df.index:
            all_dates.add(dt.strftime("%Y-%m-%d") if hasattr(dt, 'strftime') else str(dt)[:10])

    rankings = {}

    for t, df in all_daily.items():
        highs = df["High"].values.tolist()
        lows = df["Low"].values.tolist()
        closes = df["Close"].values.tolist()
        volumes = df["Volume"].values.tolist()

        adx_vals = compute_adx(highs, lows, closes, period=14)
        if not adx_vals:
            continue

        offset = len(closes) - len(adx_vals)

        for i, (adx, dip, dim) in enumerate(adx_vals):
            bar_idx = i + offset
            if bar_idx >= len(df):
                break
            dt = df.index[bar_idx]
            date_str = dt.strftime("%Y-%m-%d") if hasattr(dt, 'strftime') else str(dt)[:10]

            # Relative volume (need at least 11 days of data up to this point)
            vol_slice = volumes[:bar_idx + 1]
            rel_vol = compute_relative_volume(vol_slice, lookback=10)

            if date_str not in rankings:
                rankings[date_str] = []

            rankings[date_str].append({
                "ticker": t,
                "adx": round(adx, 1),
                "di_plus": round(dip, 1),
                "di_minus": round(dim, 1),
                "rel_vol": round(rel_vol, 2),
                "trend": "BULL" if dip > dim else "BEAR",
                "price": round(closes[bar_idx], 2),
            })

    # Sort each day's rankings by ADX descending
    for date_str in rankings:
        rankings[date_str].sort(key=lambda x: x["adx"], reverse=True)

    return rankings


def pick_top_n(
    rankings: dict,
    date_str: str,
    n: int = 3,
    min_adx: float = 25.0,
    min_rel_vol: float = 1.0,
    min_etf_volume: float = 500_000,
) -> list[dict]:
    """
    Pick the top N underlyings for a given date based on ADX ranking.
    Always trades BULL side (leveraged ETFs are a long-side intraday play).
    Marks conviction based on trend direction for position sizing.
    Falls back to trading the underlying directly if no bull ETF exists.
    """
    day_data = rankings.get(date_str, [])
    if not day_data:
        return []

    candidates = []
    for r in day_data:
        # Filter: ADX must be above threshold
        if r["adx"] < min_adx:
            continue
        # Filter: relative volume
        if r["rel_vol"] < min_rel_vol:
            continue

        etfs = LEVERAGED_2X_MAP.get(r["ticker"])
        bull_etf = etfs["bull"][0] if etfs and etfs.get("bull") else None

        # Always trade bull side — fallback to underlying if no ETF
        trade_ticker = bull_etf or r["ticker"]
        is_leveraged = bull_etf is not None

        # Must have SOME tradeable instrument
        if not trade_ticker:
            continue

        # Conviction: bull-trend days get full size, bear-trend days get 70%
        # (daily downtrend means higher risk of breakdown, size down)
        is_bear = r["trend"] == "BEAR"
        conviction = 0.7 if is_bear else 1.0

        candidates.append({
            **r,
            "bull_etf": bull_etf,
            "trade_ticker": trade_ticker,
            "is_leveraged": is_leveraged,
            "conviction": conviction,
        })

    return candidates[:n]


# ══════════════════════════════════════════════════════════════════════════════
# TRADE SIMULATION
# ══════════════════════════════════════════════════════════════════════════════

def simulate_trade(
    etf_ticker: str,
    date_str: str,
    entry_offset_min: int = 30,
    atr_mult: float = 1.0,
    underlying_atr: float = None,
    position_size: float = 9000.0,
) -> dict | None:
    """
    Simulate a single day trade on a 2x ETF.

    Args:
        etf_ticker: The 2x ETF to trade (e.g., "SMCL")
        date_str: Trading date "YYYY-MM-DD"
        entry_offset_min: Minutes after market open to enter (0 = 9:30, 30 = 10:00)
        atr_mult: Trailing stop distance as multiple of daily ATR
        underlying_atr: If provided, use this ATR instead of computing from ETF
        position_size: Dollar amount to allocate

    Returns:
        Dict with trade details or None if no data
    """
    df_5m = fetch_5m_data(etf_ticker)
    if df_5m is None or df_5m.empty:
        return None

    # Get the ETF's daily ATR for trailing stop calculation
    df_daily = fetch_daily_data(etf_ticker, days=120)
    if df_daily is None or len(df_daily) < 20:
        return None

    # Find the daily ATR as of this date
    daily_highs = df_daily["High"].values.tolist()
    daily_lows = df_daily["Low"].values.tolist()
    daily_closes = df_daily["Close"].values.tolist()
    atr_series = compute_atr(daily_highs, daily_lows, daily_closes, period=14)

    # Find the ATR value for our date
    date_idx = None
    for i, dt in enumerate(df_daily.index):
        d = dt.strftime("%Y-%m-%d") if hasattr(dt, 'strftime') else str(dt)[:10]
        if d == date_str:
            date_idx = i
            break
    if date_idx is None:
        # Try the previous day (ATR would be known from prior close)
        return None

    atr_offset = len(daily_closes) - len(atr_series)
    atr_idx = date_idx - atr_offset
    if atr_idx < 0 or atr_idx >= len(atr_series):
        return None
    daily_atr = atr_series[atr_idx]

    # Filter 5m candles to just this date
    day_candles = []
    for idx in range(len(df_5m)):
        dt = df_5m.index[idx]
        d = dt.strftime("%Y-%m-%d") if hasattr(dt, 'strftime') else str(dt)[:10]
        if d == date_str:
            # Convert to ET for time comparison
            if dt.tzinfo is not None:
                dt_et = dt.astimezone(EST)
            else:
                dt_et = dt
            day_candles.append({
                "time": dt_et,
                "open": float(df_5m["Open"].iloc[idx]),
                "high": float(df_5m["High"].iloc[idx]),
                "low": float(df_5m["Low"].iloc[idx]),
                "close": float(df_5m["Close"].iloc[idx]),
                "volume": float(df_5m["Volume"].iloc[idx]),
            })

    if len(day_candles) < 10:
        return None

    # ── Find entry candle ──
    market_open = dtime(9, 30)
    entry_minutes = entry_offset_min
    entry_hour = 9 + (30 + entry_minutes) // 60
    entry_min = (30 + entry_minutes) % 60
    entry_time = dtime(entry_hour, entry_min)

    entry_candle = None
    entry_idx = None
    for i, c in enumerate(day_candles):
        ct = c["time"].time()
        if ct.hour == entry_time.hour and ct.minute == entry_time.minute:
            entry_candle = c
            entry_idx = i
            break
        # Allow 5m tolerance
        if ct >= entry_time and entry_candle is None:
            entry_candle = c
            entry_idx = i
            break

    if entry_candle is None:
        return None

    # Entry price = open of the entry candle (market order at that time)
    entry_price = entry_candle["open"]
    if entry_price <= 0:
        return None

    shares = position_size / entry_price

    # ── Trailing stop simulation ──
    trail_distance = daily_atr * atr_mult
    running_high = entry_price
    exit_price = None
    exit_time = None
    exit_reason = "eod"  # default: close at end of day

    mfe = 0.0  # Max Favorable Excursion (%)
    mae = 0.0  # Max Adverse Excursion (%)

    # Track the open dip (how much did it drop from open before our entry)
    day_open = day_candles[0]["open"]
    dip_from_open = ((entry_price - day_open) / day_open) * 100 if day_open > 0 else 0

    for i in range(entry_idx, len(day_candles)):
        c = day_candles[i]
        # Update running high
        if c["high"] > running_high:
            running_high = c["high"]

        # Check trailing stop hit (using low of candle)
        stop_level = running_high - trail_distance
        if c["low"] <= stop_level and i > entry_idx:
            exit_price = stop_level  # Assume fill at stop level
            exit_time = c["time"].strftime("%H:%M")
            exit_reason = "trail_stop"
            break

        # Track MFE/MAE
        bar_pnl_pct = ((c["high"] - entry_price) / entry_price) * 100
        bar_loss_pct = ((c["low"] - entry_price) / entry_price) * 100
        mfe = max(mfe, bar_pnl_pct)
        mae = min(mae, bar_loss_pct)

    # If no stop hit, exit at close of last candle (EOD)
    if exit_price is None:
        exit_price = day_candles[-1]["close"]
        exit_time = day_candles[-1]["time"].strftime("%H:%M")
        exit_reason = "eod"

    pnl_pct = ((exit_price - entry_price) / entry_price) * 100
    pnl_dollars = pnl_pct / 100 * position_size

    return {
        "etf": etf_ticker,
        "date": date_str,
        "entry_time": entry_candle["time"].strftime("%H:%M"),
        "entry_price": round(entry_price, 2),
        "exit_price": round(exit_price, 2),
        "exit_time": exit_time,
        "exit_reason": exit_reason,
        "daily_atr": round(daily_atr, 2),
        "trail_distance": round(trail_distance, 2),
        "atr_mult": atr_mult,
        "pnl_pct": round(pnl_pct, 2),
        "pnl_dollars": round(pnl_dollars, 2),
        "mfe_pct": round(mfe, 2),
        "mae_pct": round(mae, 2),
        "dip_from_open": round(dip_from_open, 2),
        "position_size": position_size,
        "shares": round(shares, 2),
    }


# ══════════════════════════════════════════════════════════════════════════════
# FULL BACKTEST RUN
# ══════════════════════════════════════════════════════════════════════════════

def run_backtest(
    entry_offset_min: int = 30,
    atr_mult: float = 1.0,
    spy_adx_threshold: float = 20.0,
    signal_count_cap: int = 999,
    total_capital: float = 27000.0,
    max_positions: int = 5,
    min_pick_adx: float = 15.0,
    min_rel_vol: float = 0.8,
    verbose: bool = True,
    # Legacy compat — ignored if total_capital is set
    position_sizes: tuple = None,
) -> dict:
    """
    Run the full day trading backtest.

    Direction-aware with dynamic position sizing:
      1. Check SPY hourly ADX (regime filter)
      2. Pick top N underlyings by daily ADX (N = dynamic based on signal quality)
      3. Trade bull ETF on bull days, bear ETF on bear days, underlying as fallback
      4. Deploy full capital across positions
      5. Track P&L
    """
    # Dynamic sizing: divide capital equally across positions
    if position_sizes is None:
        position_sizes = tuple([total_capital // 3] * 3)

    if verbose:
        print(f"\n{'═' * 80}")
        print(f"  👻 INTRADAY BACKTEST v2 — Direction-Aware 2x ETF Strategy")
        print(f"{'═' * 80}")
        print(f"  Entry: +{entry_offset_min}m from open | ATR mult: {atr_mult}x")
        print(f"  SPY ADX threshold: {spy_adx_threshold} | Signal cap: {signal_count_cap}")
        print(f"  Capital: ${total_capital:,.0f} | Max positions: {max_positions}")
        print(f"{'═' * 80}")

    # ── Step 0: Preload all data to prevent network sequential bottlenecks ──
    preload_all_data()

    # ── Step 1: Compute SPY regime for each date ──
    if verbose:
        print("\n  🔍 Computing SPY hourly ADX (regime filter)...")
    spy_regime = compute_spy_hourly_adx()
    if verbose:
        print(f"  ✓ SPY regime data for {len(spy_regime)} dates")

    # ── Step 2: Compute daily rankings for all underlyings ──
    if verbose:
        print("\n  📊 Computing daily ADX rankings for stock selection...")
    rankings = compute_daily_rankings()
    if verbose:
        print(f"  ✓ Rankings for {len(rankings)} dates")

    # ── Step 3: Get common dates (where we have both SPY + rankings) ──
    common_dates = sorted(set(spy_regime.keys()) & set(rankings.keys()))
    if verbose:
        print(f"\n  📅 {len(common_dates)} tradeable dates: {common_dates[0]} → {common_dates[-1]}")

    # ── Step 4: Walk through each day ──
    all_trades = []
    daily_results = []
    skipped_days = {"low_adx": 0, "too_many_signals": 0, "no_picks": 0, "no_data": 0}
    etf_data_cache = set()  # Track which ETFs we've already tried to fetch

    for date_str in common_dates:
        spy = spy_regime[date_str]
        day_ranking = rankings.get(date_str, [])

        # ── Regime filter: SPY hourly ADX ──
        if spy["adx"] < spy_adx_threshold:
            skipped_days["low_adx"] += 1
            daily_results.append({
                "date": date_str,
                "status": "skipped",
                "reason": f"SPY ADX {spy['adx']} < {spy_adx_threshold}",
                "spy_adx": spy["adx"],
                "pnl": 0,
                "trades": [],
            })
            continue

        # ── Signal count cap ──
        # Count how many underlyings have ADX > 20 (our "signals")
        signal_count = sum(1 for r in day_ranking if r["adx"] >= 20)
        if signal_count > signal_count_cap:
            skipped_days["too_many_signals"] += 1
            daily_results.append({
                "date": date_str,
                "status": "skipped",
                "reason": f"Signal overflow: {signal_count} > {signal_count_cap}",
                "spy_adx": spy["adx"],
                "signal_count": signal_count,
                "pnl": 0,
                "trades": [],
            })
            continue

        # ── Dynamic pick count based on signal breadth ──
        # Strong trend days (many high-ADX setups) → take more positions
        high_adx_count = sum(1 for r in day_ranking if r["adx"] >= 25)
        if high_adx_count >= 5:
            n_positions = min(max_positions, 5)
        elif high_adx_count >= 3:
            n_positions = min(max_positions, 4)
        else:
            n_positions = 3

        # Fetch more candidates than we need — fallthrough on no-data
        picks = pick_top_n(rankings, date_str, n=n_positions + 4,
                          min_adx=min_pick_adx, min_rel_vol=min_rel_vol)
        if not picks:
            skipped_days["no_picks"] += 1
            daily_results.append({
                "date": date_str,
                "status": "skipped",
                "reason": "No qualifying picks",
                "spy_adx": spy["adx"],
                "pnl": 0,
                "trades": [],
            })
            continue

        # ── Dynamic position sizing: divide capital equally ──
        per_position = total_capital / n_positions

        # ── Simulate trades with fallthrough ──
        day_trades = []
        day_pnl = 0.0
        trades_filled = 0

        for pick in picks:
            if trades_filled >= n_positions:
                break

            # Use pre-selected trade ticker (bull ETF or underlying fallback)
            trade_ticker = pick.get("trade_ticker", pick.get("bull_etf"))
            is_leveraged = pick.get("is_leveraged", True)
            conviction = pick.get("conviction", 1.0)

            if not trade_ticker:
                continue

            # Pre-fetch data if we haven't yet
            if trade_ticker not in etf_data_cache:
                if verbose:
                    lev_label = "2x" if is_leveraged else "1x"
                    conv_label = "" if conviction >= 1.0 else f" [{conviction:.0%}]"
                    print(f"  📥 Fetching {trade_ticker} ({lev_label} {pick['ticker']}){conv_label}...",
                          end=" ", flush=True)
                fetch_5m_data(trade_ticker)
                fetch_daily_data(trade_ticker, days=120)
                etf_data_cache.add(trade_ticker)
                if verbose:
                    print("✓")

            # Adjust position size:
            # 1. Conviction scaling (70% on bear-trend days)
            # 2. Unleveraged underlying gets 2x size to approximate 2x ETF dollar-move
            base_size = per_position * conviction
            effective_size = base_size if is_leveraged else base_size * 2

            trade = simulate_trade(
                etf_ticker=trade_ticker,
                date_str=date_str,
                entry_offset_min=entry_offset_min,
                atr_mult=atr_mult,
                position_size=effective_size,
            )

            if trade:
                trade["underlying"] = pick["ticker"]
                trade["underlying_adx"] = pick["adx"]
                trade["underlying_rel_vol"] = pick["rel_vol"]
                trade["conviction"] = conviction
                trade["is_leveraged"] = is_leveraged
                trade["grade"] = "A" if trades_filled == 0 else "B" if trades_filled == 1 else "C"
                day_trades.append(trade)
                day_pnl += trade["pnl_dollars"]
                all_trades.append(trade)
                trades_filled += 1
            # If trade is None (no data), silently skip to next pick (fallthrough)

        if not day_trades:
            skipped_days["no_data"] += 1
            daily_results.append({
                "date": date_str,
                "status": "skipped",
                "reason": "No tradeable data for any candidate",
                "spy_adx": spy["adx"],
                "pnl": 0,
                "trades": [],
            })
            continue

        daily_results.append({
            "date": date_str,
            "status": "traded",
            "spy_adx": spy["adx"],
            "spy_trend": spy["trend"],
            "signal_count": signal_count,
            "pnl": round(day_pnl, 2),
            "trades": day_trades,
            "picks": [p["ticker"] for p in picks],
        })

        if verbose:
            win_count = sum(1 for t in day_trades if t["pnl_dollars"] > 0)
            emoji = "🟢" if day_pnl > 0 else "🔴" if day_pnl < 0 else "⚪"
            trade_labels = []
            for t in day_trades:
                conv = "" if t.get("conviction", 1.0) >= 1.0 else "⚠"
                lev = "" if t.get("is_leveraged", True) else "(1x)"
                trade_labels.append(f"{conv}{t['underlying']}→{t['etf']}{lev}")
            print(f"  {emoji} {date_str} | SPY ADX {spy['adx']:4.0f} | "
                  f"${day_pnl:+8.0f} | {win_count}/{len(day_trades)} wins | "
                  f"{', '.join(trade_labels)}")

    # ── Compute summary statistics ──
    traded_days = [d for d in daily_results if d["status"] == "traded"]
    skipped = [d for d in daily_results if d["status"] == "skipped"]

    if not all_trades:
        return {
            "params": {
                "entry_offset_min": entry_offset_min,
                "atr_mult": atr_mult,
                "spy_adx_threshold": spy_adx_threshold,
                "signal_count_cap": signal_count_cap,
                "position_sizes": list(position_sizes),
            },
            "error": "No trades executed",
            "skipped_days": skipped_days,
        }

    total_pnl = sum(t["pnl_dollars"] for t in all_trades)
    winning_trades = [t for t in all_trades if t["pnl_dollars"] > 0]
    losing_trades = [t for t in all_trades if t["pnl_dollars"] < 0]
    winning_days = [d for d in traded_days if d["pnl"] > 0]
    losing_days = [d for d in traded_days if d["pnl"] < 0]
    flat_days = [d for d in traded_days if d["pnl"] == 0]

    # Avoided losses (sum of hypothetical losses on skipped days)
    # We can't know this without running trades, but we track it for reporting

    avg_win = np.mean([t["pnl_dollars"] for t in winning_trades]) if winning_trades else 0
    avg_loss = np.mean([t["pnl_dollars"] for t in losing_trades]) if losing_trades else 0

    # Per-week P&L
    weekly_pnl = defaultdict(float)
    for d in traded_days:
        # Get week number
        dt = datetime.strptime(d["date"], "%Y-%m-%d")
        week_key = dt.strftime("%Y-W%U")
        weekly_pnl[week_key] += d["pnl"]

    weeks_above_3k = sum(1 for w, pnl in weekly_pnl.items() if pnl >= 3000)

    summary = {
        "params": {
            "entry_offset_min": entry_offset_min,
            "atr_mult": atr_mult,
            "spy_adx_threshold": spy_adx_threshold,
            "signal_count_cap": signal_count_cap,
            "total_capital": total_capital,
            "max_positions": max_positions,
            "position_sizes": list(position_sizes),
            "min_pick_adx": min_pick_adx,
        },
        "date_range": f"{common_dates[0]} → {common_dates[-1]}",
        "total_trading_days": len(common_dates),
        "days_traded": len(traded_days),
        "days_skipped": len(skipped),
        "skipped_breakdown": skipped_days,
        "total_trades": len(all_trades),
        "total_pnl": round(total_pnl, 2),
        "trade_win_rate": round(len(winning_trades) / len(all_trades) * 100, 1),
        "day_win_rate": round(len(winning_days) / len(traded_days) * 100, 1) if traded_days else 0,
        "avg_daily_pnl": round(total_pnl / len(traded_days), 2) if traded_days else 0,
        "avg_winning_trade": round(avg_win, 2),
        "avg_losing_trade": round(avg_loss, 2),
        "profit_factor": round(abs(sum(t["pnl_dollars"] for t in winning_trades) /
                                   sum(t["pnl_dollars"] for t in losing_trades)), 2)
                         if losing_trades and sum(t["pnl_dollars"] for t in losing_trades) != 0 else float('inf'),
        "max_daily_pnl": round(max(d["pnl"] for d in traded_days), 2) if traded_days else 0,
        "min_daily_pnl": round(min(d["pnl"] for d in traded_days), 2) if traded_days else 0,
        "avg_mfe": round(np.mean([t["mfe_pct"] for t in all_trades]), 2),
        "avg_mae": round(np.mean([t["mae_pct"] for t in all_trades]), 2),
        "avg_dip_from_open": round(np.mean([t["dip_from_open"] for t in all_trades]), 2),
        "weekly_pnl": {k: round(v, 2) for k, v in sorted(weekly_pnl.items())},
        "weeks_above_3k": weeks_above_3k,
        "total_weeks": len(weekly_pnl),
        "winning_days": len(winning_days),
        "losing_days": len(losing_days),
        "flat_days": len(flat_days),
        "daily_results": daily_results,
        "all_trades": all_trades,
    }

    if verbose:
        _print_summary(summary)

    return summary


def _print_summary(s: dict):
    """Pretty-print backtest summary."""
    print(f"\n{'═' * 80}")
    print(f"  📊 BACKTEST RESULTS")
    print(f"{'═' * 80}")
    print(f"  Date range:     {s['date_range']}")
    print(f"  Trading days:   {s['days_traded']} traded / {s['days_skipped']} skipped / {s['total_trading_days']} total")
    print(f"  Total trades:   {s['total_trades']}")
    print(f"")
    print(f"  💰 Total P&L:   ${s['total_pnl']:+,.0f}")
    print(f"  📈 Trade W/R:   {s['trade_win_rate']:.0f}%")
    print(f"  📅 Day W/R:     {s['day_win_rate']:.0f}% ({s['winning_days']}W / {s['losing_days']}L / {s['flat_days']}F)")
    print(f"  📊 Avg daily:   ${s['avg_daily_pnl']:+,.0f}")
    print(f"  🏆 Best day:    ${s['max_daily_pnl']:+,.0f}")
    print(f"  💀 Worst day:   ${s['min_daily_pnl']:+,.0f}")
    print(f"  📈 Avg win:     ${s['avg_winning_trade']:+,.0f}")
    print(f"  📉 Avg loss:    ${s['avg_losing_trade']:+,.0f}")
    print(f"  ⚖️  Profit fac:  {s['profit_factor']:.2f}")
    print(f"  📈 Avg MFE:     {s['avg_mfe']:+.1f}%")
    print(f"  📉 Avg MAE:     {s['avg_mae']:.1f}%")
    print(f"  📉 Avg dip:     {s['avg_dip_from_open']:.1f}%")
    print(f"")
    print(f"  💵 Weekly P&L:")
    for week, pnl in sorted(s["weekly_pnl"].items()):
        bar = "█" * max(1, int(abs(pnl) / 200))
        emoji = "🟢" if pnl >= 3000 else "🟡" if pnl > 0 else "🔴"
        print(f"     {week}: ${pnl:+8,.0f} {emoji} {bar}")
    print(f"  Weeks ≥ $3K:    {s['weeks_above_3k']}/{s['total_weeks']}")

    print(f"\n  Skipped breakdown:")
    for reason, count in s["skipped_breakdown"].items():
        print(f"     {reason}: {count} days")
    print(f"{'═' * 80}\n")


# ══════════════════════════════════════════════════════════════════════════════
# PARAMETER SWEEP
# ══════════════════════════════════════════════════════════════════════════════

def run_parameter_sweep(verbose: bool = False) -> dict:
    """
    Test all parameter combinations and find the optimal config.
    Caches data so subsequent runs are fast.
    """
    print(f"\n{'═' * 80}")
    print(f"  🔬 PARAMETER SWEEP — Testing all combinations")
    print(f"{'═' * 80}")

    # Phase 1: Pre-computing shared data (one-time)...
    print("\n  Phase 1: Pre-computing shared data (one-time)...")
    preload_all_data()

    # Parameters to sweep
    entry_offsets = [0, 15, 25, 30, 35, 45, 60, 90]  # minutes after open
    atr_mults = [0.5, 0.75, 1.0, 1.25, 1.5]
    spy_thresholds = [15.0, 20.0, 25.0]
    signal_caps = [30, 40, 50, 60, 999]

    # Capital deployment configs (total capital, max positions)
    capital_configs = {
        "full_27k_x5": {"total_capital": 27000, "max_positions": 5},
        "full_27k_x4": {"total_capital": 27000, "max_positions": 4},
        "full_27k_x3": {"total_capital": 27000, "max_positions": 3},
        "medium_18k_x3": {"total_capital": 18000, "max_positions": 3},
        "safe_12k_x3": {"total_capital": 12000, "max_positions": 3},
    }

    # Phase 1: Run with default sizing to find best entry/exit/filter params
    print("\n  Phase 2: Entry timing sweep...")
    entry_results = {}
    for offset in entry_offsets:
        print(f"    Testing +{offset}m entry...", end=" ", flush=True)
        r = run_backtest(entry_offset_min=offset, atr_mult=1.0,
                         spy_adx_threshold=20, signal_count_cap=999,
                         verbose=False)
        entry_results[offset] = {
            "total_pnl": r.get("total_pnl", 0),
            "trade_win_rate": r.get("trade_win_rate", 0),
            "day_win_rate": r.get("day_win_rate", 0),
            "profit_factor": r.get("profit_factor", 0),
            "avg_daily_pnl": r.get("avg_daily_pnl", 0),
            "days_traded": r.get("days_traded", 0),
            "total_trades": r.get("total_trades", 0),
        }
        print(f"${r.get('total_pnl', 0):+,.0f} | {r.get('trade_win_rate', 0):.0f}%W | PF {r.get('profit_factor', 0):.2f}")

    best_entry = max(entry_results.items(), key=lambda x: x[1]["total_pnl"])
    print(f"  ✓ Best entry: +{best_entry[0]}m (${best_entry[1]['total_pnl']:+,.0f})")

    # Phase 2: ATR multiplier sweep (using best entry timing)
    print(f"\n  Phase 3: ATR trailing stop sweep (using +{best_entry[0]}m entry)...")
    atr_results = {}
    for mult in atr_mults:
        print(f"    Testing {mult}x ATR...", end=" ", flush=True)
        r = run_backtest(entry_offset_min=best_entry[0], atr_mult=mult,
                        spy_adx_threshold=20, signal_count_cap=999,
                        verbose=False)
        atr_results[mult] = {
            "total_pnl": r.get("total_pnl", 0),
            "trade_win_rate": r.get("trade_win_rate", 0),
            "day_win_rate": r.get("day_win_rate", 0),
            "profit_factor": r.get("profit_factor", 0),
            "avg_daily_pnl": r.get("avg_daily_pnl", 0),
            "avg_mfe": r.get("avg_mfe", 0),
            "avg_mae": r.get("avg_mae", 0),
        }
        print(f"${r.get('total_pnl', 0):+,.0f} | {r.get('trade_win_rate', 0):.0f}%W | PF {r.get('profit_factor', 0):.2f}")

    best_atr = max(atr_results.items(), key=lambda x: x[1]["total_pnl"])
    print(f"  ✓ Best ATR: {best_atr[0]}x (${best_atr[1]['total_pnl']:+,.0f})")

    # Phase 3: SPY ADX threshold sweep
    print(f"\n  Phase 4: SPY ADX threshold sweep (using +{best_entry[0]}m, {best_atr[0]}x ATR)...")
    spy_results = {}
    for thresh in spy_thresholds:
        print(f"    Testing ADX ≥ {thresh}...", end=" ", flush=True)
        r = run_backtest(entry_offset_min=best_entry[0], atr_mult=best_atr[0],
                        spy_adx_threshold=thresh, signal_count_cap=999,
                        verbose=False)
        spy_results[thresh] = {
            "total_pnl": r.get("total_pnl", 0),
            "trade_win_rate": r.get("trade_win_rate", 0),
            "day_win_rate": r.get("day_win_rate", 0),
            "profit_factor": r.get("profit_factor", 0),
            "days_traded": r.get("days_traded", 0),
            "days_skipped": r.get("days_skipped", 0),
        }
        print(f"${r.get('total_pnl', 0):+,.0f} | {r.get('trade_win_rate', 0):.0f}%W | "
              f"{r.get('days_traded', 0)} days traded | PF {r.get('profit_factor', 0):.2f}")

    best_spy = max(spy_results.items(), key=lambda x: x[1]["total_pnl"])
    print(f"  ✓ Best SPY ADX threshold: {best_spy[0]} (${best_spy[1]['total_pnl']:+,.0f})")

    # Phase 4: Signal cap sweep
    print(f"\n  Phase 5: Signal count cap sweep...")
    cap_results = {}
    for cap in signal_caps:
        cap_label = "none" if cap >= 999 else str(cap)
        print(f"    Testing cap = {cap_label}...", end=" ", flush=True)
        r = run_backtest(entry_offset_min=best_entry[0], atr_mult=best_atr[0],
                        spy_adx_threshold=best_spy[0], signal_count_cap=cap,
                        verbose=False)
        cap_results[cap] = {
            "total_pnl": r.get("total_pnl", 0),
            "trade_win_rate": r.get("trade_win_rate", 0),
            "day_win_rate": r.get("day_win_rate", 0),
            "days_traded": r.get("days_traded", 0),
        }
        print(f"${r.get('total_pnl', 0):+,.0f} | {r.get('trade_win_rate', 0):.0f}%W | {r.get('days_traded', 0)} days")

    best_cap = max(cap_results.items(), key=lambda x: x[1]["total_pnl"])

    # Phase 5: Capital deployment sweep (using all best params)
    print(f"\n  Phase 6: Capital deployment sweep...")
    sizing_results = {}
    for name, cfg in capital_configs.items():
        print(f"    Testing {name} ${cfg['total_capital']:,} x{cfg['max_positions']}...", end=" ", flush=True)
        r = run_backtest(entry_offset_min=best_entry[0], atr_mult=best_atr[0],
                        spy_adx_threshold=best_spy[0],
                        signal_count_cap=best_cap[0],
                        total_capital=cfg["total_capital"],
                        max_positions=cfg["max_positions"],
                        verbose=False)
        sizing_results[name] = {
            "total_capital": cfg["total_capital"],
            "max_positions": cfg["max_positions"],
            "total_pnl": r.get("total_pnl", 0),
            "trade_win_rate": r.get("trade_win_rate", 0),
            "profit_factor": r.get("profit_factor", 0),
            "total_trades": r.get("total_trades", 0),
            "days_traded": r.get("days_traded", 0),
        }
        print(f"${r.get('total_pnl', 0):+,.0f} | {r.get('trade_win_rate', 0):.0f}%W | PF {r.get('profit_factor', 0):.2f} | {r.get('total_trades', 0)} trades")

    best_sizing = max(sizing_results.items(), key=lambda x: x[1]["total_pnl"])
    best_capital = capital_configs[best_sizing[0]]["total_capital"]
    best_max_pos = capital_configs[best_sizing[0]]["max_positions"]

    # ── Final run with optimal params ──
    print(f"\n{'═' * 80}")
    print(f"  🏆 OPTIMAL PARAMETERS FOUND")
    print(f"{'═' * 80}")
    print(f"  Entry:     +{best_entry[0]}m from open")
    print(f"  Exit:      {best_atr[0]}x daily ATR trailing stop")
    print(f"  SPY ADX:   ≥ {best_spy[0]}")
    print(f"  Signal cap: {best_cap[0] if best_cap[0] < 999 else 'none'}")
    print(f"  Capital:   ${best_capital:,} across {best_max_pos} positions")
    print(f"\n  Running final detailed backtest...")

    final = run_backtest(
        entry_offset_min=best_entry[0],
        atr_mult=best_atr[0],
        spy_adx_threshold=best_spy[0],
        signal_count_cap=best_cap[0],
        total_capital=best_capital,
        max_positions=best_max_pos,
        verbose=True,
    )

    return {
        "entry_timing": entry_results,
        "atr_multiplier": atr_results,
        "spy_threshold": spy_results,
        "signal_cap": cap_results,
        "position_sizing": sizing_results,
        "optimal_params": {
            "entry_offset_min": best_entry[0],
            "atr_mult": best_atr[0],
            "spy_adx_threshold": best_spy[0],
            "signal_count_cap": best_cap[0],
        },
        "final_backtest": final,
    }


# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="👻 Intraday Backtest v2 — Direction-Aware 2x ETF Day Trading",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--entry", type=int, default=35,
                        help="Entry offset minutes from open (default: 35 = 10:05 AM)")
    parser.add_argument("--atr", type=float, default=1.25,
                        help="ATR trailing stop multiplier (default: 1.25)")
    parser.add_argument("--spy-adx", type=float, default=20.0,
                        help="SPY ADX threshold (default: 20)")
    parser.add_argument("--signal-cap", type=int, default=999,
                        help="Max signals before sitting out (default: 999 = no cap)")
    parser.add_argument("--capital", type=float, default=27000.0,
                        help="Total capital to deploy (default: 27000)")
    parser.add_argument("--max-positions", type=int, default=5,
                        help="Max concurrent positions (default: 5)")
    parser.add_argument("--sweep", action="store_true",
                        help="Run full parameter sweep")
    parser.add_argument("--quick", action="store_true",
                        help="Quick run with defaults")
    parser.add_argument("--save", type=str,
                        help="Save results to JSON file")
    args = parser.parse_args()

    start_time = time.time()

    if args.sweep:
        results = run_parameter_sweep(verbose=True)
    else:
        results = run_backtest(
            entry_offset_min=args.entry,
            atr_mult=args.atr,
            spy_adx_threshold=args.spy_adx,
            signal_count_cap=args.signal_cap,
            total_capital=args.capital,
            max_positions=args.max_positions,
            verbose=True,
        )

    elapsed = time.time() - start_time
    print(f"\n  ⏱️  Completed in {elapsed:.0f}s")

    if args.save:
        save_path = Path(args.save)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        # Strip large arrays for JSON size
        save_data = {k: v for k, v in results.items()
                     if k not in ("daily_results", "all_trades")}
        if "final_backtest" in results:
            fb = results["final_backtest"]
            save_data["final_backtest"] = {k: v for k, v in fb.items()
                                           if k not in ("daily_results", "all_trades")}
            save_data["final_backtest"]["trade_count"] = len(fb.get("all_trades", []))
            save_data["final_backtest"]["traded_days_count"] = fb.get("days_traded", 0)
        with open(save_path, "w") as f:
            json.dump(save_data, f, indent=2, default=str)
        print(f"  💾 Saved to {save_path}")
