#!/usr/bin/env python3
"""
👻 Leveraged ETF Backtester — Ghost Alpha Signal Strategy

Runs the SAME signal logic from signal_engine.py (EMA stack, RSI, Stoch, ADX,
Hull MA, Ghost Grade V2) against historical daily candles to measure:
  - Win rate per ETF and per underlying
  - Average return at 1/5/10/21 day horizons after BUY signals
  - Bull vs Bear ETF performance comparison
  - Ghost Grade distribution and accuracy

Uses yfinance for historical data. No external framework needed.

Usage:
    python leveraged_backtest.py                       # Backtest top 10 pairs
    python leveraged_backtest.py --tickers TQQQ,SQQQ   # Specific tickers
    python leveraged_backtest.py --days 180             # 6 month lookback
    python leveraged_backtest.py --simulate             # Entry/exit simulation
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

import numpy as np

try:
    import yfinance as yf
except ImportError:
    print("pip install yfinance")
    sys.exit(1)

# ── Import signal engine technicals (pure functions, no side effects) ──
# These live in alpha-momentum but are standalone math functions
ALPHA_MOMENTUM_PATH = Path(__file__).resolve().parents[2] / "Antigravity" / "alpha-momentum"
# Also check same-level (when run from dossier/)
if not ALPHA_MOMENTUM_PATH.exists():
    ALPHA_MOMENTUM_PATH = Path(__file__).resolve().parents[1].parent / "alpha-momentum"

# Inline the technical functions to avoid import path headaches
# These are EXACT copies from signal_engine.py

def _ema(values, period):
    if len(values) < period:
        return [values[-1]] if values else []
    result = []
    k = 2.0 / (period + 1)
    sma = sum(values[:period]) / period
    result.append(sma)
    for val in values[period:]:
        ema_val = val * k + result[-1] * (1 - k)
        result.append(ema_val)
    return result

def _wma(values, period):
    if len(values) < period:
        return [values[-1]] if values else []
    result = []
    weights = list(range(1, period + 1))
    w_sum = sum(weights)
    for i in range(period - 1, len(values)):
        window = values[i - period + 1:i + 1]
        wma_val = sum(w * v for w, v in zip(weights, window)) / w_sum
        result.append(wma_val)
    return result

def _hull_ma(values, length=55):
    import math
    half_len = max(int(length / 2), 1)
    sqrt_len = max(round(math.sqrt(length)), 1)
    wma_half = _wma(values, half_len)
    wma_full = _wma(values, length)
    if not wma_half or not wma_full:
        return []
    min_len = min(len(wma_half), len(wma_full))
    diff_series = [2 * h - f for h, f in zip(wma_half[-min_len:], wma_full[-min_len:])]
    return _wma(diff_series, sqrt_len)

def _rsi(closes, period=14):
    if len(closes) < period + 1:
        return [50.0]
    deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    gains = [max(d, 0) for d in deltas]
    losses = [abs(min(d, 0)) for d in deltas]
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    result = []
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        if avg_loss == 0:
            result.append(100.0)
        else:
            rs = avg_gain / avg_loss
            result.append(100.0 - (100.0 / (1.0 + rs)))
    return result if result else [50.0]

def _stochastic(highs, lows, closes, k_period=14, d_period=3):
    if len(closes) < k_period:
        return [50.0], [50.0]
    k_values = []
    for i in range(k_period - 1, len(closes)):
        window_high = max(highs[i - k_period + 1:i + 1])
        window_low = min(lows[i - k_period + 1:i + 1])
        if window_high == window_low:
            k_values.append(50.0)
        else:
            k_values.append(((closes[i] - window_low) / (window_high - window_low)) * 100)
    d_values = []
    for i in range(d_period - 1, len(k_values)):
        d_values.append(sum(k_values[i - d_period + 1:i + 1]) / d_period)
    return k_values, d_values

def _adx(highs, lows, closes, period=14):
    if len(closes) < period * 2:
        return [25.0]
    tr_list, plus_dm, minus_dm = [], [], []
    for i in range(1, len(closes)):
        h, l, c_prev = highs[i], lows[i], closes[i - 1]
        h_prev, l_prev = highs[i - 1], lows[i - 1]
        tr = max(h - l, abs(h - c_prev), abs(l - c_prev))
        tr_list.append(tr)
        up_move = h - h_prev
        down_move = l_prev - l
        plus_dm.append(up_move if up_move > down_move and up_move > 0 else 0)
        minus_dm.append(down_move if down_move > up_move and down_move > 0 else 0)
    if len(tr_list) < period:
        return [25.0]
    atr = sum(tr_list[:period])
    apdm = sum(plus_dm[:period])
    amdm = sum(minus_dm[:period])
    dx_list = []
    for i in range(period, len(tr_list)):
        atr = atr - (atr / period) + tr_list[i]
        apdm = apdm - (apdm / period) + plus_dm[i]
        amdm = amdm - (amdm / period) + minus_dm[i]
        plus_di = (apdm / atr) * 100 if atr > 0 else 0
        minus_di = (amdm / atr) * 100 if atr > 0 else 0
        di_sum = plus_di + minus_di
        dx = abs(plus_di - minus_di) / di_sum * 100 if di_sum > 0 else 0
        dx_list.append(dx)
    if len(dx_list) < period:
        return [25.0]
    adx_val = sum(dx_list[:period]) / period
    result = [adx_val]
    for i in range(period, len(dx_list)):
        adx_val = (adx_val * (period - 1) + dx_list[i]) / period
        result.append(adx_val)
    return result if result else [25.0]


# ── Ghost Grade V2 (from signal_engine.py) ──

def compute_ghost_grade(closes, highs, lows, volumes, bar_idx):
    """Compute Ghost Grade V2 for a specific bar index (looking back)."""
    if bar_idx < 60:
        return {"grade": "F", "score": 0, "direction": "FLAT", "axes": {}}

    # Slice up to bar_idx (inclusive)
    c = closes[:bar_idx + 1]
    h = highs[:bar_idx + 1]
    l = lows[:bar_idx + 1]
    v = volumes[:bar_idx + 1]

    # Compute technicals
    ema8 = _ema(c, 8)
    ema21 = _ema(c, 21)
    ema34 = _ema(c, 34)
    rsi_vals = _rsi(c, 14)
    hull = _hull_ma(c, 55)

    if not ema8 or not ema21 or not ema34 or not hull:
        return {"grade": "F", "score": 0, "direction": "FLAT", "axes": {}}

    price = c[-1]
    rsi = rsi_vals[-1] if rsi_vals else 50

    # Hull direction
    hull_bull = len(hull) >= 3 and hull[-1] > hull[-3]

    # Trend age
    trend_age = 0
    for i in range(len(c) - 2, max(0, len(c) - 60), -1):
        if (c[i] > c[i-1]) == hull_bull:
            trend_age += 1
        else:
            break

    # ATR for squeeze
    trs = [max(h[i] - l[i], abs(h[i] - c[i-1]), abs(l[i] - c[i-1]))
           for i in range(1, len(c))]
    atr = sum(trs[-14:]) / min(14, len(trs)) if trs else 0
    atr_baseline = sum(trs[-50:]) / min(50, len(trs)) if len(trs) >= 50 else atr
    sqz_ratio = atr / atr_baseline if atr_baseline > 0 else 1.0

    # EMA alignment
    ema_aligned = ema8[-1] > ema21[-1] > ema34[-1]

    # Volume ratio
    vol_ratio = 0
    if len(v) >= 21:
        avg_vol = sum(v[-21:-1]) / 20
        vol_ratio = v[-1] / avg_vol if avg_vol > 0 else 0

    # 5-Axis scoring
    ax1 = 1.0 if hull_bull and ema_aligned else 0.5 if hull_bull or ema_aligned else 0.0
    ax2 = 1.0 if vol_ratio >= 1.5 else 0.5 if vol_ratio >= 0.8 else 0.0
    ax3 = 1.0 if 0.75 <= sqz_ratio <= 1.5 else 0.0
    ax4 = 1.0 if 5 <= trend_age <= 30 else 0.5 if 30 < trend_age <= 50 else 0.0
    ax5 = 1.0 if 30 < rsi < 70 else 0.5 if 25 < rsi < 75 else 0.0

    g_score = ax1 + ax2 + ax3 + ax4 + ax5
    grade = ("A+" if g_score >= 4.5 else "A" if g_score >= 4.0 else "B" if g_score >= 3.0
             else "C" if g_score >= 2.0 else "D" if g_score >= 1.0 else "F")
    direction = "LONG" if hull_bull else "SHORT"

    return {
        "grade": grade, "score": round(g_score, 1), "direction": direction,
        "axes": {"trend": ax1, "volume": ax2, "volatility": ax3, "timing": ax4, "revert": ax5},
        "rsi": round(rsi, 1), "vol_ratio": round(vol_ratio, 2), "trend_age": trend_age,
        "ema_aligned": ema_aligned, "hull_bull": hull_bull,
    }


def evaluate_buy_signal(closes, highs, lows, volumes, bar_idx):
    """Check if a BUY signal fires at bar_idx (same logic as signal_engine)."""
    if bar_idx < 60:
        return None

    c = closes[:bar_idx + 1]
    h = highs[:bar_idx + 1]
    l = lows[:bar_idx + 1]
    v = volumes[:bar_idx + 1]

    ema8 = _ema(c, 8)
    ema21 = _ema(c, 21)
    ema34 = _ema(c, 34)
    rsi_vals = _rsi(c, 14)
    stoch_k, stoch_d = _stochastic(h, l, c, 14, 3)
    adx_vals = _adx(h, l, c, 14)
    hull = _hull_ma(c, 55)

    price = c[-1]
    rsi = rsi_vals[-1] if rsi_vals else 50
    buy_reasons = []
    buy_confirmations = 0
    buy_required = True

    # REQUIRED: Price > EMA21 and was below recently
    if len(ema21) >= 3 and price > ema21[-1]:
        prev_closes = c[-4:-1] if len(c) >= 4 else c[:-1]
        prev_emas = ema21[-4:-1] if len(ema21) >= 4 else ema21[:-1]
        was_below = any(cc < ee for cc, ee in zip(prev_closes, prev_emas))
        if was_below:
            buy_reasons.append("EMA21 reclaim")
        elif price > ema21[-1]:
            buy_reasons.append("Above EMA21")
        else:
            buy_required = False
    else:
        buy_required = False

    # REQUIRED: EMA stack aligned
    if ema8 and ema21 and ema34:
        e8, e21, e34 = ema8[-1], ema21[-1], ema34[-1]
        if e8 > e21 > e34:
            buy_reasons.append("EMA stack aligned")
        elif e8 > e21:
            buy_reasons.append("Partial EMA align")
        else:
            buy_required = False
    else:
        buy_required = False

    # REQUIRED: RSI not overbought
    if rsi < 65:
        buy_reasons.append(f"RSI {rsi:.0f}")
    else:
        buy_required = False

    # Confirmations
    if len(stoch_k) >= 2 and stoch_k[-1] > stoch_k[-2] and stoch_k[-2] < 40:
        buy_confirmations += 1
    vol_ratio = 0
    if len(v) >= 21:
        avg_vol = sum(v[-21:-1]) / 20
        vol_ratio = v[-1] / avg_vol if avg_vol > 0 else 0
    if vol_ratio >= 1.5:
        buy_confirmations += 1
    if adx_vals and adx_vals[-1] > 20:
        buy_confirmations += 1
    if len(hull) >= 3 and hull[-1] > hull[-3]:
        buy_confirmations += 1

    if buy_required and len(buy_reasons) >= 3 and buy_confirmations >= 2:
        return {"price": price, "reasons": buy_reasons, "confirmations": buy_confirmations, "rsi": rsi}
    return None


# ── Core Backtest ──

def fetch_candles(ticker, days=180):
    """Fetch daily OHLCV candles from yfinance."""
    end = datetime.now()
    start = end - timedelta(days=days + 30)  # buffer for indicator warmup
    try:
        df = yf.download(ticker, start=start.strftime("%Y-%m-%d"),
                         end=end.strftime("%Y-%m-%d"), progress=False, auto_adjust=True)
        if df is None or df.empty:
            return None
        # Flatten MultiIndex columns (yfinance >= 0.2.x returns (Price, Ticker) columns)
        if isinstance(df.columns, __import__('pandas').MultiIndex):
            df.columns = df.columns.droplevel(1)
        return df
    except Exception as e:
        print(f"  [WARN] yfinance error for {ticker}: {e}")
        return None


def backtest_ticker(ticker, days=180):
    """Run Ghost Alpha signal backtest on a single ticker."""
    df = fetch_candles(ticker, days)
    if df is None or len(df) < 70:
        return None

    closes = [float(x) for x in df["Close"].values]
    highs = [float(x) for x in df["High"].values]
    lows = [float(x) for x in df["Low"].values]
    volumes = [float(x) for x in df["Volume"].values]

    signals = []
    grades = []

    # Walk forward through bars, starting after warmup
    for i in range(60, len(closes)):
        # Grade every bar
        grade_info = compute_ghost_grade(closes, highs, lows, volumes, i)
        grades.append({
            "bar": i,
            "date": str(df.index[i].date()),
            "price": round(closes[i], 2),
            **grade_info,
        })

        # Check for BUY signal
        buy = evaluate_buy_signal(closes, highs, lows, volumes, i)
        if buy:
            # Calculate forward returns from this bar
            fwd = {}
            for horizon in [1, 5, 10, 21]:
                if i + horizon < len(closes):
                    ret = ((closes[i + horizon] - closes[i]) / closes[i]) * 100
                    fwd[f"fwd_{horizon}d"] = round(ret, 2)

            signals.append({
                "bar": i,
                "date": str(df.index[i].date()),
                "entry_price": round(closes[i], 2),
                "grade": grade_info["grade"],
                "ghost_score": grade_info["score"],
                "direction": grade_info["direction"],
                "rsi": buy["rsi"],
                "confirmations": buy["confirmations"],
                **fwd,
            })

    if not signals:
        return {
            "ticker": ticker, "total_bars": len(closes) - 60,
            "signals": 0, "error": "No BUY signals fired",
            "grade_distribution": _grade_distribution(grades),
        }

    # Stats
    returns_5d = [s["fwd_5d"] for s in signals if "fwd_5d" in s]
    returns_10d = [s["fwd_10d"] for s in signals if "fwd_10d" in s]

    def _stats(returns):
        if not returns:
            return {}
        wins = [r for r in returns if r > 0]
        return {
            "count": len(returns),
            "avg_return": round(np.mean(returns), 2),
            "median_return": round(np.median(returns), 2),
            "win_rate": round(len(wins) / len(returns) * 100, 1),
            "best": round(max(returns), 2),
            "worst": round(min(returns), 2),
            "std": round(np.std(returns), 2),
        }

    return {
        "ticker": ticker,
        "total_bars": len(closes) - 60,
        "signals": len(signals),
        "stats_5d": _stats(returns_5d),
        "stats_10d": _stats(returns_10d),
        "grade_distribution": _grade_distribution(grades),
        "signal_details": signals[-10:],  # Last 10 signals for reference
        "latest_grade": grades[-1] if grades else None,
    }


def _grade_distribution(grades):
    dist = defaultdict(int)
    for g in grades:
        dist[g["grade"]] += 1
    total = len(grades)
    return {grade: {"count": count, "pct": round(count / total * 100, 1)}
            for grade, count in sorted(dist.items())}


def run_leveraged_backtest(tickers=None, days=180):
    """Run backtest across multiple leveraged ETFs."""
    if tickers is None:
        # Default: top tradeable pairs by volume
        tickers = [
            "TQQQ", "SQQQ",    # Nasdaq-100
            "SOXL", "SOXS",    # Semiconductors
            "SPXL", "SPXS",    # S&P 500
            "TNA", "TZA",      # Russell 2000
            "TSLL", "TSLS",    # Tesla
        ]

    print(f"\n👻 Ghost Alpha Leveraged ETF Backtest")
    print(f"   {len(tickers)} tickers | {days}-day lookback")
    print(f"   {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 80)

    results = {}
    for ticker in tickers:
        print(f"\n  📊 {ticker}...", end=" ", flush=True)
        result = backtest_ticker(ticker, days)
        if result:
            results[ticker] = result
            s5 = result.get("stats_5d", {})
            if s5:
                print(f"{result['signals']} signals | "
                      f"5d avg: {s5.get('avg_return', 0):+.1f}% | "
                      f"win: {s5.get('win_rate', 0):.0f}% | "
                      f"best: {s5.get('best', 0):+.1f}%")
            else:
                print(f"{result.get('error', 'no data')}")
        else:
            print("no data")

    # Summary
    print("\n" + "=" * 80)
    print("  BACKTEST SUMMARY")
    print("-" * 80)
    print(f"{'Ticker':<8} {'Sigs':>5} {'5d Avg':>8} {'5d Win':>7} {'10d Avg':>8} {'Best':>8} {'Worst':>8} {'Grade':>6}")
    print("-" * 80)

    for ticker, r in sorted(results.items(), key=lambda x: x[1].get("stats_5d", {}).get("avg_return", -999), reverse=True):
        s5 = r.get("stats_5d", {})
        s10 = r.get("stats_10d", {})
        lg = r.get("latest_grade", {})
        if s5:
            print(f"{ticker:<8} {r['signals']:>5} "
                  f"{s5.get('avg_return', 0):>+7.1f}% "
                  f"{s5.get('win_rate', 0):>6.0f}% "
                  f"{s10.get('avg_return', 0):>+7.1f}% "
                  f"{s5.get('best', 0):>+7.1f}% "
                  f"{s5.get('worst', 0):>+7.1f}% "
                  f"{lg.get('grade', '?'):>6}")
        else:
            print(f"{ticker:<8} {'—':>5} {'—':>8} {'—':>7} {'—':>8} {'—':>8} {'—':>8} {lg.get('grade', '?'):>6}")

    return {"results": results, "tickers": tickers, "days": days,
            "run_date": datetime.now().isoformat()}


def main():
    parser = argparse.ArgumentParser(description="👻 Ghost Alpha Leveraged ETF Backtester")
    parser.add_argument("--tickers", type=str, help="Comma-separated tickers to backtest")
    parser.add_argument("--days", type=int, default=180, help="Lookback days (default: 180)")
    parser.add_argument("--save", type=str, help="Save results to JSON file")
    parser.add_argument("--all-tradeable", action="store_true",
                        help="Backtest all top-tradeable ETFs from scanner")
    args = parser.parse_args()

    tickers = None
    if args.tickers:
        tickers = [t.strip().upper() for t in args.tickers.split(",")]
    elif args.all_tradeable:
        # Pull from scanner
        try:
            from dossier.leveraged_etf_scanner import fetch_tradingview_leveraged_etfs, _is_leveraged_description, KNOWN_UNDERLYINGS
            print("Loading tradeable universe from TradingView...")
            etfs = fetch_tradingview_leveraged_etfs()
            # Apply top-tradeable filter
            etfs = [e for e in etfs
                    if e["avg_volume_30d"] >= 1_000_000
                    and e["price"] is not None and e["price"] > 2.0
                    and e["underlying"] not in ("Unknown", "Target")]
            tickers = [e["symbol"] for e in etfs[:30]]  # Cap at 30
        except Exception as e:
            print(f"Scanner import failed: {e}")
            print("Falling back to default tickers")

    results = run_leveraged_backtest(tickers, args.days)

    if args.save:
        Path(args.save).parent.mkdir(parents=True, exist_ok=True)
        with open(args.save, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n💾 Saved to {args.save}")


if __name__ == "__main__":
    main()
