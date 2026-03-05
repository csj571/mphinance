"""
screens_backtest.py — Backtest momentum scoring against Screens_v2 historical data.

Reads the Screens_v2 Excel file, scores each historical scan row using the
current momentum algorithm, then fetches yfinance forward returns (1/5/10/21 day)
to see how well our scoring predicts future performance.

Key insight: Screens_v2 has ~37 days of scanner data (Jan 26 → Mar 4 2026)
across 8 strategies. Each row has full technicals at scan time.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

import pandas as pd
import numpy as np

# Add project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from dossier.momentum_picks import score_momentum
from dossier.quality_filter import check_quality


SCREENS_FILE = PROJECT_ROOT.parent / "Screens_v2 (1).xlsx"
RESULTS_DIR = PROJECT_ROOT / "docs" / "backtesting"

# Sheets with enough momentum-scoring data
SCORABLE_SHEETS = [
    "Momentum with Pullback",
    "EMA Cross Momentum",
    "Volatility Squeeze",
    "Gravity Squeeze",
    "Bearish EMA Cross (Down)",
]


def _normalize_row(row: pd.Series, sheet_name: str) -> dict:
    """Convert an Excel row into a ticker payload dict compatible with score_momentum.
    
    score_momentum reads from:
      - technical_analysis.ema_stack
      - technical_analysis.oscillators.{rsi_14, adx_14, stoch_k, macd_hist}
      - technical_analysis.volume.rel_vol
      - technical_analysis.ema.{21}
      - currentPrice, priceChangePct, trendOverall
      - fundamentals.{market_cap, sector, name}
    """
    # Map column names — some sheets use Stoch.K, others Stoch_K
    stoch_k = row.get("Stoch_K") or row.get("Stoch.K") or 50
    stoch_d = row.get("Stoch_D") or row.get("Stoch.D") or 50
    rel_vol = row.get("relative_volume_10d_calc") or 1.0

    # EMA values
    ema8 = float(row.get("EMA8", 0) or 0)
    ema21 = float(row.get("EMA21", 0) or 0)
    ema34 = float(row.get("EMA34", 0) or 0)
    ema55 = float(row.get("EMA55", 0) or 0)
    ema89 = float(row.get("EMA89", 0) or 0)
    close = float(row.get("close", 0) or 0)

    # Determine EMA stack alignment
    emas = [ema8, ema21, ema34, ema55, ema89]
    if all(e > 0 for e in emas):
        if ema8 > ema21 > ema34 > ema55 > ema89:
            ema_stack = "FULL BULLISH"
        elif ema8 > ema21 and ema21 > ema55:
            ema_stack = "PARTIAL BULLISH"
        elif ema89 > ema55 > ema34 > ema21 > ema8:
            ema_stack = "FULL BEARISH"
        elif ema89 > ema55 and ema55 > ema21:
            ema_stack = "PARTIAL BEARISH"
        else:
            ema_stack = "TANGLED"
    else:
        ema_stack = "UNKNOWN"

    # Determine trend from EMA alignment
    trend = "Bullish" if ema_stack in ("FULL BULLISH", "PARTIAL BULLISH") else "Bearish"

    # Build payload matching score_momentum's expected structure
    payload = {
        "ticker": str(row.get("Symbol", "")),
        "currentPrice": close,
        "priceChangePct": float(row.get("change", 0) or 0),
        "trendOverall": trend,
        "fundamentals": {
            "market_cap": float(row.get("market_cap_basic", 0) or 0),
            "sector": str(row.get("sector", "") or ""),
            "name": str(row.get("Company", "") or ""),
        },
        "technical_analysis": {
            "ema_stack": ema_stack,
            "oscillators": {
                "adx_14": float(row.get("ADX", 0) or 0),
                "rsi_14": float(row.get("RSI", 50) or 50),
                "stoch_k": float(stoch_k) if stoch_k else 50,
                "stoch_d": float(stoch_d) if stoch_d else 50,
                "macd_hist": None,  # Not in screen data
            },
            "volume": {
                "rel_vol": float(rel_vol) if rel_vol else 1.0,
            },
            "ema": {
                "8": ema8,
                "21": ema21,
                "34": ema34,
                "55": ema55,
                "89": ema89,
            },
        },
        "scores": {},
        "tickertrace": {},
        "source_screen": sheet_name,
    }
    return payload


def _fetch_forward_returns(symbols: list, dates_map: dict) -> dict:
    """Fetch forward returns from yfinance for each (symbol, date) pair.
    
    Returns: {(symbol, date_str): {1: pct, 5: pct, 10: pct, 21: pct}}
    """
    import yfinance as yf
    
    # Find the overall date range needed
    all_dates = []
    for pairs in dates_map.values():
        all_dates.extend(pairs)
    if not all_dates:
        return {}
    
    min_date = min(all_dates)
    max_date = max(all_dates) + timedelta(days=25)
    
    results = {}
    unique_symbols = list(set(symbols))
    
    print(f"    Fetching {len(unique_symbols)} tickers from yfinance ({min_date} → {max_date})...")
    
    batch_size = 50
    for batch_start in range(0, len(unique_symbols), batch_size):
        batch = unique_symbols[batch_start:batch_start + batch_size]
        batch_str = " ".join(batch)
        try:
            data = yf.download(batch_str, start=str(min_date), end=str(max_date),
                              progress=False, group_by='ticker', auto_adjust=True)
            
            for sym in batch:
                if len(batch) == 1:
                    prices = data["Close"] if "Close" in data.columns else None
                else:
                    prices = data[sym]["Close"] if sym in data.columns.get_level_values(0) else None
                
                if prices is None or prices.empty:
                    continue
                
                for scan_date in dates_map.get(sym, []):
                    # Find the close on scan date
                    scan_idx = prices.index.searchsorted(pd.Timestamp(scan_date))
                    if scan_idx >= len(prices):
                        continue
                    base_price = prices.iloc[scan_idx]
                    if pd.isna(base_price) or base_price <= 0:
                        continue
                    
                    fwd = {}
                    for horizon in [1, 5, 10, 21]:
                        target_idx = scan_idx + horizon
                        if target_idx < len(prices):
                            target_price = prices.iloc[target_idx]
                            if not pd.isna(target_price) and target_price > 0:
                                fwd[horizon] = round(((target_price / base_price) - 1) * 100, 2)
                    
                    if fwd:
                        results[(sym, str(scan_date))] = fwd
        except Exception as e:
            print(f"    [WARN] yfinance batch failed: {e}")
    
    print(f"    Got forward returns for {len(results)} (ticker, date) pairs")
    return results


def run_screens_backtest(excel_path: str = None):
    """Run the full backtest against Screens_v2 data."""
    path = Path(excel_path) if excel_path else SCREENS_FILE
    if not path.exists():
        print(f"[ERROR] Screens file not found: {path}")
        return None
    
    print(f"  ── SCREENS BACKTEST ENGINE ──")
    print(f"  File: {path.name}")
    
    xls = pd.ExcelFile(path)
    
    # Collect all scored entries
    all_scored = []
    dates_map = defaultdict(list)  # sym -> [dates]
    
    for sheet in SCORABLE_SHEETS:
        if sheet not in xls.sheet_names:
            print(f"    [SKIP] Sheet '{sheet}' not found")
            continue
        
        df = pd.read_excel(xls, sheet_name=sheet)
        df["ScanDate"] = pd.to_datetime(df["ScanTime"]).dt.date
        
        print(f"  Scoring {sheet}: {len(df)} rows, {df['Symbol'].nunique()} tickers...")
        
        for _, row in df.iterrows():
            try:
                payload = _normalize_row(row, sheet)
                if not payload["ticker"] or payload["currentPrice"] <= 0:
                    continue
                
                scored = score_momentum(payload)
                if scored["ticker"]:
                    scored["scan_date"] = str(row["ScanDate"])
                    scored["source_screen"] = sheet
                    scored["scan_close"] = float(row.get("close", 0) or 0)
                    scored["current_price"] = float(row.get("CurrentPrice", 0) or 0)
                    all_scored.append(scored)
                    
                    dates_map[scored["ticker"]].append(row["ScanDate"])
            except Exception as e:
                pass  # Skip bad rows silently
    
    print(f"  Scored {len(all_scored)} total entries across {len(set(s['ticker'] for s in all_scored))} tickers")
    
    # Dedupe dates_map
    for sym in dates_map:
        dates_map[sym] = list(set(dates_map[sym]))
    
    # Fetch forward returns
    all_symbols = list(dates_map.keys())
    forward_returns = _fetch_forward_returns(all_symbols, dates_map)
    
    # Merge forward returns into scored entries
    entries_with_returns = 0
    for s in all_scored:
        key = (s["ticker"], s["scan_date"])
        fwd = forward_returns.get(key, {})
        s["fwd_1d"] = fwd.get(1)
        s["fwd_5d"] = fwd.get(5)
        s["fwd_10d"] = fwd.get(10)
        s["fwd_21d"] = fwd.get(21)
        if s["fwd_5d"] is not None:
            entries_with_returns += 1
    
    print(f"  Matched {entries_with_returns}/{len(all_scored)} entries with forward returns")
    
    # ── ANALYSIS ──
    results = _analyze_results(all_scored)
    results["total_scored"] = len(all_scored)
    results["entries_with_returns"] = entries_with_returns
    results["date_range"] = {
        "start": min(s["scan_date"] for s in all_scored),
        "end": max(s["scan_date"] for s in all_scored),
    }
    
    # Save results
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / "screens_backtest.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"  ✓ Results saved to {out_path}")
    
    return results


def _analyze_results(scored: list) -> dict:
    """Analyze backtest results across multiple dimensions."""
    # Filter to entries with 5d return data
    with_returns = [s for s in scored if s.get("fwd_5d") is not None]
    if not with_returns:
        return {"error": "No entries with forward return data"}
    
    def _stats(entries, horizon="fwd_5d"):
        vals = [e[horizon] for e in entries if e.get(horizon) is not None]
        if not vals:
            return {"count": 0}
        wins = [v for v in vals if v > 0]
        return {
            "count": len(vals),
            "avg_return": round(np.mean(vals), 2),
            "median_return": round(np.median(vals), 2),
            "win_rate": round(len(wins) / len(vals) * 100, 1),
            "best": round(max(vals), 2),
            "worst": round(min(vals), 2),
            "std": round(np.std(vals), 2),
        }
    
    results = {}
    
    # 1. Score bands
    high = [s for s in with_returns if s["score"] >= 70]
    mid = [s for s in with_returns if 40 <= s["score"] < 70]
    low = [s for s in with_returns if s["score"] < 40]
    
    results["score_bands"] = {
        "high_70_plus": {h: _stats(high, h) for h in ["fwd_1d", "fwd_5d", "fwd_10d", "fwd_21d"]},
        "mid_40_70": {h: _stats(mid, h) for h in ["fwd_1d", "fwd_5d", "fwd_10d", "fwd_21d"]},
        "low_under_40": {h: _stats(low, h) for h in ["fwd_1d", "fwd_5d", "fwd_10d", "fwd_21d"]},
    }
    
    # 2. Pullback vs Non-pullback
    pullbacks = [s for s in with_returns if s.get("is_pullback_setup")]
    non_pullbacks = [s for s in with_returns if not s.get("is_pullback_setup")]
    
    results["pullback_analysis"] = {
        "pullback_setups": {h: _stats(pullbacks, h) for h in ["fwd_1d", "fwd_5d", "fwd_10d", "fwd_21d"]},
        "non_pullback": {h: _stats(non_pullbacks, h) for h in ["fwd_1d", "fwd_5d", "fwd_10d", "fwd_21d"]},
    }
    
    # 3. By source screen
    by_screen = defaultdict(list)
    for s in with_returns:
        by_screen[s.get("source_screen", "unknown")].append(s)
    
    results["by_screen"] = {}
    for screen, entries in by_screen.items():
        results["by_screen"][screen] = _stats(entries, "fwd_5d")
    
    # 4. EMA stack alignment
    by_ema = defaultdict(list)
    for s in with_returns:
        by_ema[s.get("ema_stack", "UNKNOWN")].append(s)
    
    results["by_ema_stack"] = {}
    for stack, entries in by_ema.items():
        results["by_ema_stack"][stack] = _stats(entries, "fwd_5d")
    
    # 5. Top picks simulation (gold pick each unique date)
    by_date = defaultdict(list)
    for s in with_returns:
        by_date[s["scan_date"]].append(s)
    
    gold_picks = []
    for date, entries in sorted(by_date.items()):
        entries.sort(key=lambda x: x["score"], reverse=True)
        if entries:
            gold_picks.append(entries[0])
    
    results["gold_picks_simulation"] = {
        "total_days": len(gold_picks),
        "stats": {h: _stats(gold_picks, h) for h in ["fwd_1d", "fwd_5d", "fwd_10d", "fwd_21d"]},
        "picks": [
            {
                "date": p["scan_date"],
                "ticker": p["ticker"],
                "score": p["score"],
                "fwd_5d": p.get("fwd_5d"),
                "fwd_10d": p.get("fwd_10d"),
                "is_pullback": p.get("is_pullback_setup", False),
                "ema_stack": p.get("ema_stack", ""),
            }
            for p in gold_picks
        ],
    }
    
    # 6. Detailed entries (top 50 by score for reference)
    top_scored = sorted(with_returns, key=lambda x: x["score"], reverse=True)[:50]
    results["top_50_entries"] = [
        {
            "ticker": s["ticker"],
            "scan_date": s["scan_date"],
            "score": s["score"],
            "source_screen": s.get("source_screen", ""),
            "ema_stack": s.get("ema_stack", ""),
            "is_pullback": s.get("is_pullback_setup", False),
            "rsi": s.get("rsi", 0),
            "adx": s.get("adx", 0),
            "fwd_1d": s.get("fwd_1d"),
            "fwd_5d": s.get("fwd_5d"),
            "fwd_10d": s.get("fwd_10d"),
            "fwd_21d": s.get("fwd_21d"),
        }
        for s in top_scored
    ]
    
    return results


def print_screens_summary(results: dict):
    """Print a formatted summary of screens backtest results."""
    if not results:
        return
    
    print(f"\n  {'='*70}")
    print(f"  SCREENS BACKTEST RESULTS")
    print(f"  {results.get('date_range', {}).get('start', '?')} → {results.get('date_range', {}).get('end', '?')}")
    print(f"  {results.get('total_scored', 0)} scored | {results.get('entries_with_returns', 0)} with returns")
    print(f"  {'='*70}")
    
    # Score bands
    print(f"\n  ── SCORE BANDS (5-day returns) ──")
    for band_name, band_data in results.get("score_bands", {}).items():
        d = band_data.get("fwd_5d", {})
        if d.get("count", 0) > 0:
            print(f"  {band_name:15s}: {d['count']:3d} entries | avg {d['avg_return']:+.1f}% | win {d['win_rate']:.0f}% | med {d['median_return']:+.1f}%")
    
    # Pullback
    print(f"\n  ── PULLBACK vs NON-PULLBACK (5-day) ──")
    for label, key in [("Pullback setups", "pullback_setups"), ("Non-pullback", "non_pullback")]:
        d = results.get("pullback_analysis", {}).get(key, {}).get("fwd_5d", {})
        if d.get("count", 0) > 0:
            print(f"  {label:18s}: {d['count']:3d} entries | avg {d['avg_return']:+.1f}% | win {d['win_rate']:.0f}%")
    
    # By screen
    print(f"\n  ── BY SOURCE SCREEN (5-day) ──")
    for screen, d in sorted(results.get("by_screen", {}).items(), key=lambda x: x[1].get("avg_return", 0), reverse=True):
        if d.get("count", 0) > 0:
            print(f"  {screen:30s}: {d['count']:3d} | avg {d['avg_return']:+.1f}% | win {d['win_rate']:.0f}%")
    
    # By EMA stack
    print(f"\n  ── BY EMA STACK (5-day) ──")
    for stack, d in sorted(results.get("by_ema_stack", {}).items(), key=lambda x: x[1].get("avg_return", 0), reverse=True):
        if d.get("count", 0) > 0:
            print(f"  {stack:20s}: {d['count']:3d} | avg {d['avg_return']:+.1f}% | win {d['win_rate']:.0f}%")
    
    # Gold picks
    gold = results.get("gold_picks_simulation", {})
    gold_stats_5d = gold.get("stats", {}).get("fwd_5d", {})
    if gold_stats_5d.get("count", 0) > 0:
        print(f"\n  ── GOLD PICK SIMULATION ({gold.get('total_days', 0)} days) ──")
        print(f"  5d:  avg {gold_stats_5d['avg_return']:+.1f}% | win {gold_stats_5d['win_rate']:.0f}% | best {gold_stats_5d['best']:+.1f}% | worst {gold_stats_5d['worst']:+.1f}%")
        gold_10d = gold.get("stats", {}).get("fwd_10d", {})
        if gold_10d.get("count", 0) > 0:
            print(f"  10d: avg {gold_10d['avg_return']:+.1f}% | win {gold_10d['win_rate']:.0f}%")
        gold_21d = gold.get("stats", {}).get("fwd_21d", {})
        if gold_21d.get("count", 0) > 0:
            print(f"  21d: avg {gold_21d['avg_return']:+.1f}% | win {gold_21d['win_rate']:.0f}%")
    
    # Top gold picks
    print(f"\n  ── INDIVIDUAL GOLD PICKS ──")
    for p in gold.get("picks", [])[:15]:
        pb = " ⚡PB" if p.get("is_pullback") else "     "
        fwd5 = f"{p['fwd_5d']:+.1f}%" if p.get("fwd_5d") is not None else "  N/A"
        fwd10 = f"{p['fwd_10d']:+.1f}%" if p.get("fwd_10d") is not None else "  N/A"
        print(f"  {p.get('date', '?'):10s}  {p['ticker']:6s}  Score:{p['score']:3d}  5d:{fwd5:>7s}  10d:{fwd10:>7s}  {p.get('ema_stack',''):18s}{pb}")


if __name__ == "__main__":
    results = run_screens_backtest()
    if results:
        print_screens_summary(results)
