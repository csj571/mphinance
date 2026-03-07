"""
Backtest Engine — Validates momentum picks against actual price returns.

Uses existing date-stamped JSONs + yfinance forward price data to measure:
  - Did higher-scored tickers produce better returns?
  - Win rate: % of picks that were green after 1/5/10/21 days
  - Average return by tier (Gold/Silver/Bronze vs rest)
  - Pullback setup performance vs non-pullback
"""

import json
import yfinance as yf
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TICKER_DIR = PROJECT_ROOT / "docs" / "ticker"
BACKTEST_OUTPUT = PROJECT_ROOT / "docs" / "backtesting" / "backtest_results.json"


def _get_forward_returns(ticker: str, entry_date: str, entry_price: float) -> dict:
    """Fetch actual price returns at 1, 5, 10, 21 days forward from entry_date."""
    try:
        start = datetime.strptime(entry_date, "%Y-%m-%d")
        end = start + timedelta(days=35)  # Buffer for weekends/holidays

        hist = yf.Ticker(ticker).history(start=start, end=end)
        if hist.empty:
            return {}

        close = hist["Close"]
        results = {}
        for days in [1, 5, 10, 21]:
            # Find the closest trading day
            target_idx = min(days, len(close) - 1)
            if target_idx > 0:
                fwd_price = float(close.iloc[target_idx])
                ret = ((fwd_price - entry_price) / entry_price) * 100
                results[f"return_{days}d"] = round(ret, 2)
                results[f"price_{days}d"] = round(fwd_price, 2)

        return results
    except Exception as e:
        print(f"    [WARN] Forward returns for {ticker}: {e}")
        return {}


def run_backtest(max_tickers: int = 21) -> dict:
    """
    Backtest all scored tickers using existing JSON snapshots.

    For each ticker with a date-stamped JSON:
    1. Load the snapshot, score it with current momentum algorithm
    2. Fetch yfinance forward returns from that date
    3. Compare scores vs actual returns

    Returns comprehensive results dict.
    """
    from dossier.momentum_picks import score_momentum

    print("  ── BACKTEST ENGINE ──")
    entries = []

    # Collect all date-stamped snapshots
    if not TICKER_DIR.exists():
        print("  [WARN] No ticker directory found")
        return {"error": "No data"}

    for ticker_dir in sorted(TICKER_DIR.iterdir()):
        if not ticker_dir.is_dir():
            continue
        ticker = ticker_dir.name

        # Find all date-stamped JSONs
        for json_file in sorted(ticker_dir.glob("2026-*.json")):
            try:
                with open(json_file) as f:
                    payload = json.load(f)

                date_str = json_file.stem  # e.g., "2026-03-03"
                price = payload.get("currentPrice", 0)
                if not price:
                    continue

                # Score with current algorithm
                scored = score_momentum(payload)

                entries.append({
                    "ticker": ticker,
                    "date": date_str,
                    "entry_price": price,
                    "score": scored["score"],
                    "raw_score": scored.get("raw_score", scored["score"]),
                    "quality_score": scored.get("quality_score", 100),
                    "grade": scored["grade"],
                    "ema_stack": scored["ema_stack"],
                    "is_pullback": scored.get("is_pullback_setup", False),
                    "rsi": scored["rsi"],
                    "adx": scored["adx"],
                })
            except Exception as e:
                print(f"    [WARN] {ticker}/{json_file.stem}: {e}")

    print(f"  Found {len(entries)} scored snapshots")

    if not entries:
        return {"error": "No scored entries", "entries": []}

    # Fetch forward returns
    print("  Fetching forward returns from yfinance...")
    for entry in entries:
        returns = _get_forward_returns(
            entry["ticker"], entry["date"], entry["entry_price"]
        )
        entry.update(returns)

    # ── Analysis ──
    print("  Analyzing results...")

    # Tier analysis: top 3 (Gold/Silver/Bronze) vs rest
    sorted_by_score = sorted(entries, key=lambda x: x["score"], reverse=True)
    top3 = sorted_by_score[:3]
    rest = sorted_by_score[3:]

    def _avg_return(group, period):
        vals = [e.get(f"return_{period}d") for e in group if e.get(f"return_{period}d") is not None]
        return round(sum(vals) / len(vals), 2) if vals else None

    def _win_rate(group, period):
        vals = [e.get(f"return_{period}d") for e in group if e.get(f"return_{period}d") is not None]
        if not vals:
            return None
        winners = sum(1 for v in vals if v > 0)
        return round(winners / len(vals) * 100, 1)

    # Pullback vs non-pullback
    pullbacks = [e for e in entries if e.get("is_pullback")]
    non_pullbacks = [e for e in entries if not e.get("is_pullback")]

    # Score bands
    high_score = [e for e in entries if e["score"] >= 70]
    mid_score = [e for e in entries if 40 <= e["score"] < 70]
    low_score = [e for e in entries if e["score"] < 40]

    results = {
        "run_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "total_snapshots": len(entries),
        "tickers_analyzed": len(set(e["ticker"] for e in entries)),
        "tier_analysis": {
            "top3": {
                "tickers": [e["ticker"] for e in top3],
                "avg_score": round(sum(e["score"] for e in top3) / len(top3), 1) if top3 else 0,
                "avg_return_1d": _avg_return(top3, 1),
                "avg_return_5d": _avg_return(top3, 5),
                "avg_return_10d": _avg_return(top3, 10),
                "avg_return_21d": _avg_return(top3, 21),
                "win_rate_5d": _win_rate(top3, 5),
            },
            "rest": {
                "count": len(rest),
                "avg_score": round(sum(e["score"] for e in rest) / len(rest), 1) if rest else 0,
                "avg_return_1d": _avg_return(rest, 1),
                "avg_return_5d": _avg_return(rest, 5),
                "avg_return_10d": _avg_return(rest, 10),
                "avg_return_21d": _avg_return(rest, 21),
                "win_rate_5d": _win_rate(rest, 5),
            },
        },
        "pullback_analysis": {
            "pullback_setups": {
                "count": len(pullbacks),
                "avg_return_5d": _avg_return(pullbacks, 5),
                "avg_return_10d": _avg_return(pullbacks, 10),
                "win_rate_5d": _win_rate(pullbacks, 5),
            },
            "non_pullback": {
                "count": len(non_pullbacks),
                "avg_return_5d": _avg_return(non_pullbacks, 5),
                "avg_return_10d": _avg_return(non_pullbacks, 10),
                "win_rate_5d": _win_rate(non_pullbacks, 5),
            },
        },
        "score_band_analysis": {
            "high_70_plus": {
                "count": len(high_score),
                "avg_return_5d": _avg_return(high_score, 5),
                "win_rate_5d": _win_rate(high_score, 5),
            },
            "mid_40_70": {
                "count": len(mid_score),
                "avg_return_5d": _avg_return(mid_score, 5),
                "win_rate_5d": _win_rate(mid_score, 5),
            },
            "low_under_40": {
                "count": len(low_score),
                "avg_return_5d": _avg_return(low_score, 5),
                "win_rate_5d": _win_rate(low_score, 5),
            },
        },
        "entries": entries,
    }

    # Save results
    BACKTEST_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(BACKTEST_OUTPUT, "w") as f:
        json.dump(results, f, indent=2)
    print(f"  ✓ Results saved to {BACKTEST_OUTPUT}")

    return results


def print_backtest_summary(results: dict):
    """Pretty-print backtest results."""
    if "error" in results:
        print(f"  Backtest error: {results['error']}")
        return

    print(f"\n  {'='*60}")
    print(f"  BACKTEST RESULTS — {results['total_snapshots']} snapshots, {results['tickers_analyzed']} tickers")
    print(f"  {'='*60}")

    tier = results.get("tier_analysis", {})
    t3 = tier.get("top3", {})
    rest = tier.get("rest", {})

    print(f"\n  ── TIER ANALYSIS ──")
    print(f"  Top 3 ({', '.join(t3.get('tickers', []))}): avg score {t3.get('avg_score')}")
    print(f"    5d return: {t3.get('avg_return_5d')}%  |  Win rate: {t3.get('win_rate_5d')}%")
    print(f"    10d: {t3.get('avg_return_10d')}%  |  21d: {t3.get('avg_return_21d')}%")
    print(f"  Rest ({rest.get('count')}): avg score {rest.get('avg_score')}")
    print(f"    5d return: {rest.get('avg_return_5d')}%  |  Win rate: {rest.get('win_rate_5d')}%")

    pb = results.get("pullback_analysis", {})
    pb_setups = pb.get("pullback_setups", {})
    pb_non = pb.get("non_pullback", {})
    print(f"\n  ── PULLBACK ANALYSIS ──")
    print(f"  Pullback setups ({pb_setups.get('count')}): 5d avg {pb_setups.get('avg_return_5d')}%  Win: {pb_setups.get('win_rate_5d')}%")
    print(f"  Non-pullback ({pb_non.get('count')}):    5d avg {pb_non.get('avg_return_5d')}%  Win: {pb_non.get('win_rate_5d')}%")

    bands = results.get("score_band_analysis", {})
    print(f"\n  ── SCORE BANDS ──")
    for band_name, band_data in bands.items():
        print(f"  {band_name}: {band_data.get('count')} tickers  |  5d: {band_data.get('avg_return_5d')}%  Win: {band_data.get('win_rate_5d')}%")

    # Individual entries
    print(f"\n  ── INDIVIDUAL RESULTS ──")
    for e in sorted(results.get("entries", []), key=lambda x: x["score"], reverse=True):
        r5 = e.get('return_5d')
        r5_str = f"{r5:+.1f}%" if r5 is not None else "N/A"
        pb_flag = " ⚡PB" if e.get("is_pullback") else ""
        print(f"  {e['ticker']:6s} {e['date']}  Score:{e['score']:3d}  5d:{r5_str:>7s}  {e['ema_stack']:18s}  RSI:{e['rsi']}  ADX:{e['adx']}{pb_flag}")
