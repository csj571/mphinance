#!/usr/bin/env python3
"""
👻 Gamma Pin Backtest — Did the sandwich predict the pin?

Reads saved gamma-pin-scan.json files and checks what actually happened
on OpEx day. Uses Tradier historical data for price verification.

Usage:
    python3 -m dossier.backtesting.gamma_pin_backtest                    # Backtest latest
    python3 -m dossier.backtesting.gamma_pin_backtest --file gamma-pin-2026-03-20.json
    python3 -m dossier.backtesting.gamma_pin_backtest --all              # All archived scans

Output: docs/api/gamma-backtest-results.json

© mphinance + Sam the Quant Ghost — "Trust, but verify. Especially your own screener."
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests

# ── Paths ──
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
API_DIR = PROJECT_ROOT / "docs" / "api"
HISTORY_DIR = API_DIR / "gamma-history"
RESULTS_PATH = API_DIR / "gamma-backtest-results.json"

# ── Colors ──
R = "\033[0m"
RED = "\033[91m"
GRN = "\033[92m"
YLW = "\033[93m"
CYN = "\033[96m"
BLD = "\033[1m"
GRY = "\033[90m"


def _get_tradier_key() -> str:
    key = os.getenv("TRADIER_API_KEY")
    if key:
        return key
    env_paths = [
        Path.home() / "Antigravity" / "alpha-momentum" / ".env",
        Path.home() / "Antigravity" / "mphinance" / "tightspread" / ".env",
    ]
    for p in env_paths:
        if p.exists():
            for line in p.read_text().splitlines():
                if line.startswith("TRADIER_API_KEY="):
                    val = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if val:
                        return val
    print("❌ TRADIER_API_KEY not found.")
    sys.exit(1)


def fetch_price_history(symbol: str, start: str, end: str, key: str) -> list[dict]:
    """Fetch daily OHLCV from Tradier."""
    try:
        resp = requests.get(
            "https://api.tradier.com/v1/markets/history",
            params={"symbol": symbol, "interval": "daily", "start": start, "end": end},
            headers={"Authorization": f"Bearer {key}", "Accept": "application/json"},
            timeout=10,
        )
        if resp.status_code != 200:
            return []
        hist = resp.json().get("history", {})
        if not hist:
            return []
        days = hist.get("day", [])
        return [days] if isinstance(days, dict) else (days or [])
    except Exception:
        return []


def backtest_scan(scan_data: dict, key: str, min_snap: float = 35.0) -> dict:
    """
    Backtest a single gamma pin scan against actual OpEx day prices.
    
    Returns scorecard with per-ticker results and aggregate stats.
    """
    scan_date = scan_data.get("scan_date", "")[:10]
    target_expiry = scan_data.get("target_expiry", "")
    version = scan_data.get("screener_version", "v3")
    results = scan_data.get("results", [])

    if not target_expiry:
        return {"error": "No target_expiry in scan data"}

    # Fetch window: day before OpEx → 2 days after
    opex_date = datetime.strptime(target_expiry, "%Y-%m-%d")
    fetch_start = (opex_date - timedelta(days=2)).strftime("%Y-%m-%d")
    fetch_end = (opex_date + timedelta(days=5)).strftime("%Y-%m-%d")

    # Filter to overextended with meaningful snap scores
    candidates = [r for r in results if r.get("overext_dir") != "PINNED" and r.get("snap_score", 0) >= min_snap]

    ticker_results = []
    wins_1d = 0
    wins_2d = 0
    total = 0
    total_move_1d = 0

    for r in candidates:
        ticker = r["ticker"]
        pre_price = r["price"]
        direction = r["overext_dir"]
        gravity = r["gravity"]
        snap = r["snap_score"]
        grav_quality = r.get("grav_quality", "UNKNOWN")

        days = fetch_price_history(ticker, fetch_start, fetch_end, key)
        if len(days) < 2:
            continue

        # Find OpEx day and day-after closes
        opex_close = None
        post_close = None
        pre_close = None
        for i, d in enumerate(days):
            if d["date"] == target_expiry:
                opex_close = d["close"]
                if i > 0:
                    pre_close = days[i - 1]["close"]
                if i + 1 < len(days):
                    post_close = days[i + 1]["close"]
                break

        if opex_close is None:
            # OpEx might be a holiday — use closest available day
            for d in days:
                if d["date"] >= target_expiry:
                    opex_close = d["close"]
                    break
            if opex_close is None:
                continue

        # Use pre_close from scan if we don't have the day before
        if pre_close is None:
            pre_close = pre_price

        change_1d = (opex_close - pre_price) / pre_price * 100
        change_2d = ((post_close - pre_price) / pre_price * 100) if post_close else None

        # Did price move TOWARD gravity?
        if direction == "BELOW":
            win_1d = opex_close > pre_price
            win_2d = post_close > pre_price if post_close else False
        else:  # ABOVE
            win_1d = opex_close < pre_price
            win_2d = post_close < pre_price if post_close else False

        if win_1d:
            wins_1d += 1
        if win_2d:
            wins_2d += 1
        total += 1
        total_move_1d += abs(change_1d)

        ticker_results.append({
            "ticker": ticker,
            "direction": direction,
            "snap_score": snap,
            "grav_quality": grav_quality,
            "pre_price": pre_price,
            "gravity": gravity,
            "grav_dist_pct": r.get("grav_dist_pct", 0),
            "opex_close": opex_close,
            "post_close": post_close,
            "change_1d_pct": round(change_1d, 2),
            "change_2d_pct": round(change_2d, 2) if change_2d is not None else None,
            "win_1d": win_1d,
            "win_2d": win_2d,
        })

        time.sleep(0.15)  # Rate limit

    # Split by direction
    above_results = [r for r in ticker_results if r["direction"] == "ABOVE"]
    below_results = [r for r in ticker_results if r["direction"] == "BELOW"]

    # Split by gravity quality
    high_q = [r for r in ticker_results if r["grav_quality"] in ("HIGH", "MODERATE")]
    low_q = [r for r in ticker_results if r["grav_quality"] in ("LOW", "GARBAGE")]

    return {
        "scan_date": scan_date,
        "target_expiry": target_expiry,
        "screener_version": version,
        "backtest_date": datetime.now().isoformat(),
        # Aggregate
        "total_candidates": len(candidates),
        "total_scored": total,
        "win_rate_1d_pct": round(wins_1d / total * 100, 1) if total else 0,
        "win_rate_2d_pct": round(wins_2d / total * 100, 1) if total else 0,
        "avg_abs_move_1d_pct": round(total_move_1d / total, 2) if total else 0,
        # Direction breakdown
        "above_count": len(above_results),
        "above_win_1d": sum(1 for r in above_results if r["win_1d"]),
        "above_win_rate_1d": round(sum(1 for r in above_results if r["win_1d"]) / len(above_results) * 100, 1) if above_results else 0,
        "below_count": len(below_results),
        "below_win_1d": sum(1 for r in below_results if r["win_1d"]),
        "below_win_rate_1d": round(sum(1 for r in below_results if r["win_1d"]) / len(below_results) * 100, 1) if below_results else 0,
        # Quality breakdown
        "high_quality_count": len(high_q),
        "high_quality_win_1d": sum(1 for r in high_q if r["win_1d"]),
        "high_quality_win_rate": round(sum(1 for r in high_q if r["win_1d"]) / len(high_q) * 100, 1) if high_q else 0,
        "low_quality_count": len(low_q),
        "low_quality_win_1d": sum(1 for r in low_q if r["win_1d"]),
        "low_quality_win_rate": round(sum(1 for r in low_q if r["win_1d"]) / len(low_q) * 100, 1) if low_q else 0,
        # Per-ticker detail
        "ticker_results": ticker_results,
    }


def print_scorecard(bt: dict):
    """Pretty-print the backtest results."""
    print(f"\n{'═' * 80}")
    print(f"  {CYN}{BLD}👻 GAMMA PIN BACKTEST{R}")
    print(f"  {GRY}Scan: {bt['scan_date']} → OpEx: {bt['target_expiry']} | "
          f"Version: {bt['screener_version']}{R}")
    print(f"{'═' * 80}")

    wr1 = bt["win_rate_1d_pct"]
    wr2 = bt["win_rate_2d_pct"]
    wr1_c = GRN if wr1 >= 55 else YLW if wr1 >= 45 else RED
    wr2_c = GRN if wr2 >= 55 else YLW if wr2 >= 45 else RED

    print(f"\n  📊 {BLD}SCORECARD{R}")
    print(f"     1-Day Win Rate:  {wr1_c}{wr1:.1f}%{R} ({bt['total_scored']} tickers)")
    print(f"     2-Day Win Rate:  {wr2_c}{wr2:.1f}%{R}")
    print(f"     Avg |Move| 1D:   {bt['avg_abs_move_1d_pct']:.2f}%")

    print(f"\n  📐 {BLD}DIRECTION BREAKDOWN{R}")
    above_wr = bt["above_win_rate_1d"]
    below_wr = bt["below_win_rate_1d"]
    print(f"     ABOVE (short):   {GRN if above_wr >= 50 else RED}{above_wr:.1f}%{R} "
          f"({bt['above_win_1d']}/{bt['above_count']})")
    print(f"     BELOW (long):    {GRN if below_wr >= 50 else RED}{below_wr:.1f}%{R} "
          f"({bt['below_win_1d']}/{bt['below_count']})")

    print(f"\n  🎯 {BLD}GRAVITY QUALITY{R}")
    hq_wr = bt["high_quality_win_rate"]
    lq_wr = bt["low_quality_win_rate"]
    print(f"     HIGH/MODERATE:   {GRN if hq_wr >= 50 else RED}{hq_wr:.1f}%{R} "
          f"({bt['high_quality_win_1d']}/{bt['high_quality_count']})")
    print(f"     LOW/GARBAGE:     {GRN if lq_wr >= 50 else RED}{lq_wr:.1f}%{R} "
          f"({bt['low_quality_win_1d']}/{bt['low_quality_count']})")

    # Per-ticker table
    print(f"\n  {BLD}{'TICKER':<7} {'DIR':>6} {'SNAP':>5} {'GQ':>8} {'PRE$':>8} {'GRAV$':>8} "
          f"{'OPEX$':>8} {'1D Δ':>7} {'1D':>4} {'2D':>4}{R}")
    print(f"  {'─' * 75}")
    for r in sorted(bt["ticker_results"], key=lambda x: x["snap_score"], reverse=True):
        w1 = f"{GRN}✅{R}" if r["win_1d"] else f"{RED}❌{R}"
        w2 = f"{GRN}✅{R}" if r["win_2d"] else f"{RED}❌{R}"
        gq_c = GRN if r["grav_quality"] in ("HIGH", "MODERATE") else RED
        print(f"  {r['ticker']:<7} {r['direction']:>6} {r['snap_score']:>5.1f} "
              f"{gq_c}{r['grav_quality']:>8}{R} "
              f"${r['pre_price']:>7.2f} ${r['gravity']:>7.2f} "
              f"${r['opex_close']:>7.2f} {r['change_1d_pct']:>+6.1f}% {w1} {w2}")

    print(f"\n{'═' * 80}")
    print(f"  {GRY}👻 Sam says: \"Past performance doesn't guarantee future results.")
    print(f"     But past FAILURES definitely guarantee future improvements.\"{R}\n")


def main():
    parser = argparse.ArgumentParser(description="👻 Gamma Pin Backtest")
    parser.add_argument("--file", type=str, help="Specific scan file to backtest")
    parser.add_argument("--all", action="store_true", help="Backtest all archived scans")
    parser.add_argument("--min-snap", type=float, default=35.0,
                        help="Min snap score to include (default: 35)")
    parser.add_argument("--json", action="store_true", help="Output JSON only")
    args = parser.parse_args()

    key = _get_tradier_key()
    all_results = []

    if args.file:
        scan_path = HISTORY_DIR / args.file if not Path(args.file).is_absolute() else Path(args.file)
        if not scan_path.exists():
            # Try API dir
            scan_path = API_DIR / args.file
        if not scan_path.exists():
            print(f"❌ File not found: {args.file}")
            sys.exit(1)
        with open(scan_path) as f:
            scan = json.load(f)
        bt = backtest_scan(scan, key, args.min_snap)
        all_results.append(bt)

    elif args.all:
        if not HISTORY_DIR.exists():
            print(f"❌ No history directory: {HISTORY_DIR}")
            sys.exit(1)
        for scan_file in sorted(HISTORY_DIR.glob("gamma-pin-*.json")):
            print(f"  📂 Backtesting: {scan_file.name}...")
            with open(scan_file) as f:
                scan = json.load(f)
            bt = backtest_scan(scan, key, args.min_snap)
            all_results.append(bt)

    else:
        # Default: backtest the latest scan
        latest = API_DIR / "gamma-pin-scan.json"
        if not latest.exists():
            print("❌ No gamma-pin-scan.json found. Run the screener first.")
            sys.exit(1)
        with open(latest) as f:
            scan = json.load(f)
        bt = backtest_scan(scan, key, args.min_snap)
        all_results.append(bt)

    # Output
    if args.json:
        print(json.dumps(all_results, indent=2, default=str))
    else:
        for bt in all_results:
            if "error" in bt:
                print(f"  ❌ {bt['error']}")
            else:
                print_scorecard(bt)

    # Save results
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(all_results, indent=2, default=str))
    print(f"  {GRY}💾 Saved to {RESULTS_PATH}{R}")


if __name__ == "__main__":
    main()
