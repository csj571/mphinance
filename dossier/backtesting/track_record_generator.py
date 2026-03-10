#!/usr/bin/env python3
"""
Track Record Generator — Aggregate historical picks with forward returns.

Scans docs/api/dossier-*.json for historical picks, fetches forward returns
from Yahoo Finance, and generates docs/backtesting/track_record.json.

This powers the Track Record page (docs/track-record/index.html) which shows
win rate, avg returns, Sharpe ratio, and a cumulative return chart — the
strongest conversion tool for paid subscribers.

Usage:
    python3 dossier/backtesting/track_record_generator.py
    
Called by generate.py during the pipeline run.
"""

import json
import math
import sys
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
API_DIR = PROJECT_ROOT / "docs" / "api"
OUTPUT_PATH = PROJECT_ROOT / "docs" / "backtesting" / "track_record.json"

# Minimum days old before we validate (need 5+ trading days)
MIN_DAYS_FOR_VALIDATION = 7


def _get_forward_returns(ticker: str, pick_date: str, price_at_pick: float) -> dict:
    """Fetch forward returns (1d, 5d, 10d, 21d) from Yahoo Finance."""
    try:
        import yfinance as yf
        from dossier.utils.retry import retry

        dt = datetime.strptime(pick_date, "%Y-%m-%d")
        # Fetch 30 trading days after the pick
        start = dt
        end = dt + timedelta(days=35)

        ticker_obj = yf.Ticker(ticker)
        hist = ticker_obj.history(start=start.strftime("%Y-%m-%d"),
                                  end=end.strftime("%Y-%m-%d"))

        if hist.empty or len(hist) < 2:
            return {}

        prices = hist["Close"].tolist()
        returns = {}

        # Calculate forward returns at various horizons
        for label, offset in [("fwd_1d", 1), ("fwd_5d", 5), ("fwd_10d", 10), ("fwd_21d", 21)]:
            if len(prices) > offset:
                fwd_price = prices[offset]
                pct_return = round(((fwd_price - price_at_pick) / price_at_pick) * 100, 2)
                returns[label] = pct_return

        return returns

    except Exception as e:
        print(f"    [WARN] Forward return fetch failed for {ticker}: {e}")
        return {}


def generate_track_record() -> dict:
    """
    Aggregate all historical picks and compute performance.
    Returns the full track record dict.
    """
    print("  Building track record from historical picks...")

    entries = []
    seen_keys = set()  # Deduplicate by date+ticker

    # Scan dossier summary archives
    for api_file in sorted(API_DIR.glob("dossier-2*.json")):
        try:
            with open(api_file) as f:
                summary = json.load(f)

            date = summary.get("meta", {}).get("date", "")
            picks = summary.get("picks", {})

            for medal in ["gold", "silver", "bronze"]:
                pick = picks.get(medal)
                if not pick or not pick.get("ticker"):
                    continue

                key = f"{date}:{pick['ticker']}"
                if key in seen_keys:
                    continue
                seen_keys.add(key)

                entry = {
                    "date": date,
                    "ticker": pick["ticker"],
                    "score": pick.get("score", 0),
                    "grade": pick.get("grade", ""),
                    "medal": medal,
                    "entry_price": pick.get("entry", 0),
                    "target_price": pick.get("target", 0),
                    "stop_price": pick.get("stop", 0),
                    "is_pullback": False,
                }
                entries.append(entry)

        except Exception as e:
            print(f"    [WARN] Error reading {api_file}: {e}")
            continue

    # Also scan the current daily-picks.json for today's picks
    daily_picks_path = API_DIR / "daily-picks.json"
    if daily_picks_path.exists():
        try:
            with open(daily_picks_path) as f:
                daily = json.load(f)

            date = daily.get("date", "")
            for pick in daily.get("picks", [])[:3]:
                key = f"{date}:{pick['ticker']}"
                if key in seen_keys:
                    continue
                seen_keys.add(key)

                medal_map = {1: "gold", 2: "silver", 3: "bronze"}
                entries.append({
                    "date": date,
                    "ticker": pick["ticker"],
                    "score": pick.get("score", 0),
                    "grade": pick.get("grade", ""),
                    "medal": medal_map.get(pick.get("rank", 0), ""),
                    "entry_price": pick.get("price", 0),
                    "is_pullback": pick.get("is_pullback_setup", False),
                })
        except Exception as e:
            print(f"    [WARN] Error reading daily-picks.json: {e}")

    print(f"  Found {len(entries)} historical picks")

    # Fetch forward returns for picks old enough to validate
    now = datetime.now()
    validated_count = 0

    for entry in entries:
        try:
            pick_dt = datetime.strptime(entry["date"], "%Y-%m-%d")
            days_ago = (now - pick_dt).days

            if days_ago >= MIN_DAYS_FOR_VALIDATION:
                price = entry.get("entry_price", 0)
                if price > 0:
                    returns = _get_forward_returns(entry["ticker"], entry["date"], price)
                    entry.update(returns)
                    if returns:
                        validated_count += 1
        except Exception:
            continue

    print(f"  Validated {validated_count}/{len(entries)} picks with forward returns")

    # Compute stats
    stats = _compute_stats(entries)

    record = {
        "generated_at": datetime.now().isoformat(),
        "stats": stats,
        "entries": entries,
    }

    # Write output
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(record, f, indent=2)

    print(f"  ✓ Track record: {OUTPUT_PATH}")
    print(f"    Total picks: {stats['total_picks_tracked']}")
    print(f"    Validated: {stats['total_validated']}")
    if stats["total_validated"] > 0:
        print(f"    Win rate (5d): {stats['win_rate_5d']}%")
        print(f"    Avg 5d return: {stats['avg_5d_return']}%")
        print(f"    Sharpe (5d): {stats['sharpe_5d']}")

    return record


def _compute_stats(entries: list) -> dict:
    """Compute aggregate performance stats from validated entries."""
    validated = [e for e in entries if "fwd_5d" in e]
    total = len(entries)

    if not validated:
        return {
            "total_picks_tracked": total,
            "total_validated": 0,
            "win_rate_5d": 0,
            "avg_5d_return": 0,
            "avg_1d_return": 0,
            "sharpe_5d": 0,
            "best_pick": None,
            "worst_pick": None,
        }

    fwd_5d = [e["fwd_5d"] for e in validated]
    fwd_1d = [e["fwd_1d"] for e in validated if "fwd_1d" in e]

    wins = sum(1 for r in fwd_5d if r > 0)
    avg_5d = sum(fwd_5d) / len(fwd_5d)
    avg_1d = sum(fwd_1d) / len(fwd_1d) if fwd_1d else 0

    # Sharpe ratio (annualized from 5-day returns)
    if len(fwd_5d) > 1:
        mean = sum(fwd_5d) / len(fwd_5d)
        variance = sum((r - mean) ** 2 for r in fwd_5d) / (len(fwd_5d) - 1)
        std = math.sqrt(variance) if variance > 0 else 1
        sharpe = round((mean / std) * math.sqrt(252 / 5), 2)  # Annualized
    else:
        sharpe = 0

    # Best and worst picks
    best = max(validated, key=lambda e: e.get("fwd_5d", -999))
    worst = min(validated, key=lambda e: e.get("fwd_5d", 999))

    return {
        "total_picks_tracked": total,
        "total_validated": len(validated),
        "win_rate_5d": round((wins / len(validated)) * 100, 1),
        "avg_5d_return": round(avg_5d, 2),
        "avg_1d_return": round(avg_1d, 2),
        "sharpe_5d": sharpe,
        "best_pick": {"ticker": best["ticker"], "date": best["date"], "return": best["fwd_5d"]},
        "worst_pick": {"ticker": worst["ticker"], "date": worst["date"], "return": worst["fwd_5d"]},
    }


if __name__ == "__main__":
    generate_track_record()
