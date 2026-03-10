#!/usr/bin/env python3
"""
👻 Sam's Leveraged ETF Scanner
Pulls all leveraged ETFs from TradingView's scanner API, maps underlying
assets, and outputs a clean JSON for algo trading integration.

Usage:
    python leveraged_etf_scanner.py                  # Full scan, print summary
    python leveraged_etf_scanner.py --json            # Output raw JSON
    python leveraged_etf_scanner.py --csv             # Save CSV
    python leveraged_etf_scanner.py --underlying TSLA # Filter by underlying
    python leveraged_etf_scanner.py --bull-only        # Only bull/long ETFs
    python leveraged_etf_scanner.py --bear-only        # Only bear/short ETFs
    python leveraged_etf_scanner.py --min-volume 500000 # Min avg volume filter
"""

import re
import json
import csv
import sys
import argparse
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    print("pip install requests")
    sys.exit(1)


# ─── Known underlying mappings (regex on description is unreliable for some) ───
KNOWN_UNDERLYINGS = {
    # S&P 500
    "SPXL": ("S&P 500", "3x", "bull"), "SPXS": ("S&P 500", "3x", "bear"),
    "UPRO": ("S&P 500", "3x", "bull"), "SDS": ("S&P 500", "2x", "bear"),
    "SSO": ("S&P 500", "2x", "bull"), "SH": ("S&P 500", "1x", "bear"),
    "SPXU": ("S&P 500", "3x", "bear"),
    # Nasdaq-100
    "TQQQ": ("Nasdaq-100", "3x", "bull"), "SQQQ": ("Nasdaq-100", "3x", "bear"),
    "QLD": ("Nasdaq-100", "2x", "bull"), "QID": ("Nasdaq-100", "2x", "bear"),
    "PSQ": ("Nasdaq-100", "1x", "bear"),
    # Dow Jones
    "UDOW": ("Dow Jones", "3x", "bull"), "SDOW": ("Dow Jones", "3x", "bear"),
    "DDM": ("Dow Jones", "2x", "bull"), "DXD": ("Dow Jones", "2x", "bear"),
    # Russell 2000
    "TNA": ("Russell 2000", "3x", "bull"), "TZA": ("Russell 2000", "3x", "bear"),
    "UWM": ("Russell 2000", "2x", "bull"), "TWM": ("Russell 2000", "2x", "bear"),
    "URTY": ("Russell 2000", "3x", "bull"), "SRTY": ("Russell 2000", "3x", "bear"),
    # Semiconductors
    "SOXL": ("Semiconductors", "3x", "bull"), "SOXS": ("Semiconductors", "3x", "bear"),
    "USD": ("Semiconductors", "2x", "bull"),
    # Tech
    "TECL": ("Technology", "3x", "bull"), "TECS": ("Technology", "3x", "bear"),
    # Financials
    "FAS": ("Financials", "3x", "bull"), "FAZ": ("Financials", "3x", "bear"),
    # Energy
    "ERX": ("Energy", "2x", "bull"), "ERY": ("Energy", "2x", "bear"),
    "GUSH": ("Oil & Gas E&P", "2x", "bull"), "DRIP": ("Oil & Gas E&P", "2x", "bear"),
    "UCO": ("Crude Oil", "2x", "bull"), "SCO": ("Crude Oil", "2x", "bear"),
    # Gold / Silver / Miners
    "NUGT": ("Gold Miners", "2x", "bull"), "DUST": ("Gold Miners", "2x", "bear"),
    "JNUG": ("Junior Gold Miners", "2x", "bull"), "JDST": ("Junior Gold Miners", "2x", "bear"),
    "UGL": ("Gold", "2x", "bull"), "GLL": ("Gold", "2x", "bear"),
    "AGQ": ("Silver", "2x", "bull"), "ZSL": ("Silver", "2x", "bear"),
    # Biotech
    "LABU": ("Biotech", "3x", "bull"), "LABD": ("Biotech", "3x", "bear"),
    # Retail
    "RETL": ("Retail", "3x", "bull"),
    # China
    "YINN": ("China Large-Cap", "3x", "bull"), "YANG": ("China Large-Cap", "3x", "bear"),
    "CWEB": ("China Internet", "2x", "bull"),
    # Bonds / Treasuries
    "TMF": ("20+ Year Treasury", "3x", "bull"), "TMV": ("20+ Year Treasury", "3x", "bear"),
    "TBT": ("20+ Year Treasury", "2x", "bear"), "UBT": ("20+ Year Treasury", "2x", "bull"),
    "TYD": ("7-10 Year Treasury", "3x", "bull"), "TYO": ("7-10 Year Treasury", "3x", "bear"),
    # Volatility
    "UVXY": ("VIX Short-Term", "1.5x", "bull"), "SVXY": ("VIX Short-Term", "0.5x", "bear"),
    "UVIX": ("VIX Short-Term", "2x", "bull"),
    # Single-Stock Leveraged (Direxion / GraniteShares / Defiance)
    "TSLL": ("TSLA", "2x", "bull"), "TSLS": ("TSLA", "1x", "bear"),
    "NVDL": ("NVDA", "2x", "bull"), "NVDU": ("NVDA", "2x", "bull"),
    "NVDD": ("NVDA", "1x", "bear"), "NVDS": ("NVDA", "1x", "bear"),
    "AAPU": ("AAPL", "2x", "bull"), "AAPD": ("AAPL", "1x", "bear"),
    "AMZU": ("AMZN", "2x", "bull"), "AMZD": ("AMZN", "1x", "bear"),
    "MSFU": ("MSFT", "2x", "bull"), "MSFD": ("MSFT", "1x", "bear"),
    "GGLL": ("GOOGL", "2x", "bull"),
    "METV": ("META", "2x", "bull"),
    "CONL": ("COIN", "2x", "bull"),
    "BITX": ("Bitcoin", "2x", "bull"),
    "MSTU": ("MSTR", "2x", "bull"), "MSTX": ("MSTR", "2x", "bull"),
    "FNGU": ("FANG+", "3x", "bull"), "FNGD": ("FANG+", "3x", "bear"),
}


def _is_leveraged_description(desc):
    """Check if an ETF description indicates it's leveraged."""
    d = desc.upper()
    leveraged_keywords = [
        "2X", "3X", "1.5X", "-1X", "-2X", "-3X",
        "ULTRA", "ULTRAPRO", "ULTRASHORT",
        "LEVERAGED", "BULL 2", "BULL 3", "BEAR 1", "BEAR 2", "BEAR 3",
        "DAILY BULL", "DAILY BEAR",
        "TRIPLE", "DOUBLE",
        "2X LONG", "2X SHORT", "3X LONG", "3X SHORT",
        "T-REX", "LEVERAGE SHARES",
    ]
    return any(kw in d for kw in leveraged_keywords)


def fetch_tradingview_leveraged_etfs():
    """
    Query TradingView Scanner API for all ETFs, then filter client-side
    for leveraged funds. TV has no leveraged-specific filter field, so we
    pull the full ETF universe (~5000) and match on description keywords.
    """
    url = "https://scanner.tradingview.com/america/scan"

    payload = {
        "filter": [
            {"left": "type", "operation": "in_range", "right": ["fund"]},
            {"left": "subtype", "operation": "in_range", "right": ["etf"]},
        ],
        "options": {"lang": "en"},
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": [
            "name",                # 0 - ticker
            "description",         # 1 - fund name
            "close",               # 2 - last price
            "change",              # 3 - $ change
            "change_abs",          # 4 - % change
            "volume",              # 5 - today's volume
            "average_volume_30d_calc", # 6 - 30d avg vol
            "market_cap_basic",    # 7 - AUM proxy
            "Perf.W",              # 8 - weekly perf %
            "Perf.1M",             # 9 - monthly perf %
            "Perf.3M",             # 10 - 3mo perf %
            "RSI",                 # 11 - RSI(14)
            "Recommend.All",       # 12 - TV signal rating
        ],
        "sort": {"sortBy": "average_volume_30d_calc", "sortOrder": "desc"},
        "range": [0, 5000],
    }

    resp = requests.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    rows = data.get("data", [])

    results = []
    for item in rows:
        d = item.get("d", [])
        if len(d) < 13:
            continue

        symbol = d[0] or ""
        description = d[1] or ""

        # Client-side leveraged filter: known symbols OR description keywords
        if symbol not in KNOWN_UNDERLYINGS and not _is_leveraged_description(description):
            continue

        price = d[2]
        change = d[3]
        change_pct = d[4]
        volume = d[5]
        avg_vol_30d = d[6]
        market_cap = d[7]
        perf_w = d[8]
        perf_1m = d[9]
        perf_3m = d[10]
        rsi = d[11]
        tv_signal = d[12]

        # Skip entries with no price
        if not symbol or price is None or price <= 0:
            continue

        # Resolve underlying
        underlying, leverage, direction = resolve_underlying(symbol, description)

        results.append({
            "symbol": symbol,
            "description": description,
            "underlying": underlying,
            "leverage": leverage,
            "direction": direction,
            "price": round(price, 2) if price else None,
            "change_pct": round(change_pct, 2) if change_pct else None,
            "volume": int(volume) if volume else 0,
            "avg_volume_30d": int(avg_vol_30d) if avg_vol_30d else 0,
            "aum": int(market_cap) if market_cap else 0,
            "perf_1w_pct": round(perf_w, 2) if perf_w else None,
            "perf_1m_pct": round(perf_1m, 2) if perf_1m else None,
            "perf_3m_pct": round(perf_3m, 2) if perf_3m else None,
            "rsi_14": round(rsi, 1) if rsi else None,
            "tv_signal": round(tv_signal, 3) if tv_signal else None,
        })

    return results


def resolve_underlying(symbol, description):
    """Map a leveraged ETF to its underlying asset, leverage factor, and direction."""
    # Check known mappings first
    if symbol in KNOWN_UNDERLYINGS:
        return KNOWN_UNDERLYINGS[symbol]

    desc_upper = description.upper()

    # Detect direction
    direction = "bull"
    for bear_word in ["BEAR", "SHORT", "INVERSE", "DECLINE", "DECL"]:
        if bear_word in desc_upper:
            direction = "bear"
            break

    # Detect leverage
    leverage = "2x"  # default
    lev_match = re.search(r"(\d(?:\.\d+)?)[xX]", description)
    if lev_match:
        leverage = f"{lev_match.group(1)}x"
    elif "ULTRAPRO" in desc_upper or "TRIPLE" in desc_upper:
        leverage = "3x"
    elif "ULTRA" in desc_upper or "DOUBLE" in desc_upper:
        leverage = "2x"

    # Extract underlying from description
    # Pattern: "Daily [ASSET] [Bull/Bear] [2X]" (Direxion style)
    match = re.search(
        r"DAILY\s+(.*?)\s+(?:BULL|BEAR|LONG|SHORT|TARGET)",
        desc_upper
    )
    if match:
        underlying = match.group(1).strip()
        underlying = re.sub(r"\d+[xX].*$", "", underlying).strip()
        if underlying:
            return underlying.title(), leverage, direction

    # Pattern: "UltraPro Short [ASSET]" or "Ultra [ASSET]"
    match = re.search(r"(?:ULTRAPRO|ULTRA)\s+(?:SHORT\s+)?(.*?)(?:\s+ETF)?$", desc_upper)
    if match:
        underlying = match.group(1).strip()
        if underlying:
            return underlying.title(), leverage, direction

    # Pattern: "[ASSET] Bull/Bear [2X] Shares"
    match = re.search(r"^(.*?)\s+(?:BULL|BEAR)\s+\d", desc_upper)
    if match:
        underlying = match.group(1).strip()
        # Remove provider name prefixes
        for prefix in ["DIREXION", "GRANITESHARES", "PROSHARES", "DEFIANCE"]:
            underlying = re.sub(f"^{prefix}\\s+(?:DAILY\\s+)?", "", underlying)
        if underlying:
            return underlying.title(), leverage, direction

    return "Unknown", leverage, direction


def format_volume(vol):
    """Format volume with K/M suffix."""
    if not vol:
        return "0"
    if vol >= 1_000_000:
        return f"{vol / 1_000_000:.1f}M"
    if vol >= 1_000:
        return f"{vol / 1_000:.0f}K"
    return str(vol)


def format_aum(aum):
    """Format AUM with M/B suffix."""
    if not aum:
        return "N/A"
    if aum >= 1_000_000_000:
        return f"${aum / 1_000_000_000:.1f}B"
    if aum >= 1_000_000:
        return f"${aum / 1_000_000:.0f}M"
    return f"${aum:,.0f}"


def print_summary(etfs, args):
    """Print a formatted summary table."""
    # Apply filters
    filtered = etfs
    if args.underlying:
        query = args.underlying.upper()
        filtered = [e for e in filtered if query in e["underlying"].upper()]
    if args.bull_only:
        filtered = [e for e in filtered if e["direction"] == "bull"]
    if args.bear_only:
        filtered = [e for e in filtered if e["direction"] == "bear"]
    if args.min_volume:
        filtered = [e for e in filtered if e["avg_volume_30d"] >= args.min_volume]

    if not filtered:
        print("No ETFs match your filters.")
        return filtered

    # Header
    print(f"\n👻 Sam's Leveraged ETF Scanner — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"   Found {len(filtered)} leveraged ETFs" +
          (f" (filtered from {len(etfs)} total)" if len(filtered) != len(etfs) else ""))
    print("=" * 110)
    print(f"{'Symbol':<8} {'Dir':<5} {'Lev':<4} {'Price':>8} {'Chg%':>7} "
          f"{'AvgVol':>8} {'AUM':>10} {'RSI':>5} {'1W%':>7} {'1M%':>7} {'Underlying':<20}")
    print("-" * 110)

    for e in filtered:
        dir_icon = "🟢" if e["direction"] == "bull" else "🔴"
        chg = f"{e['change_pct']:+.1f}%" if e["change_pct"] is not None else "N/A"
        rsi = f"{e['rsi_14']:.0f}" if e["rsi_14"] else "—"
        w1 = f"{e['perf_1w_pct']:+.1f}%" if e["perf_1w_pct"] is not None else "—"
        m1 = f"{e['perf_1m_pct']:+.1f}%" if e["perf_1m_pct"] is not None else "—"

        print(f"{e['symbol']:<8} {dir_icon:<5} {e['leverage']:<4} "
              f"${e['price']:>7.2f} {chg:>7} "
              f"{format_volume(e['avg_volume_30d']):>8} "
              f"{format_aum(e['aum']):>10} "
              f"{rsi:>5} {w1:>7} {m1:>7} {e['underlying']:<20}")

    print("=" * 110)

    # Underlying breakdown
    underlyings = {}
    for e in filtered:
        u = e["underlying"]
        if u not in underlyings:
            underlyings[u] = {"bull": [], "bear": []}
        underlyings[u][e["direction"]].append(e["symbol"])

    print(f"\n📊 Underlying Asset Pairs ({len(underlyings)} unique):")
    for u in sorted(underlyings.keys()):
        bulls = ", ".join(underlyings[u]["bull"]) or "—"
        bears = ", ".join(underlyings[u]["bear"]) or "—"
        print(f"  {u:<25} 🟢 {bulls:<30} 🔴 {bears}")

    return filtered


def save_csv(etfs, filepath):
    """Save ETF list to CSV."""
    if not etfs:
        return
    keys = etfs[0].keys()
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(etfs)
    print(f"\n💾 Saved {len(etfs)} ETFs to {filepath}")


def save_json(etfs, filepath):
    """Save ETF list to JSON."""
    output = {
        "scan_date": datetime.now().isoformat(),
        "total_count": len(etfs),
        "etfs": etfs,
    }
    with open(filepath, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n💾 Saved {len(etfs)} ETFs to {filepath}")


def main():
    parser = argparse.ArgumentParser(description="👻 Sam's Leveraged ETF Scanner")
    parser.add_argument("--json", action="store_true", help="Output JSON to stdout")
    parser.add_argument("--csv", action="store_true", help="Save results to CSV")
    parser.add_argument("--save-json", type=str, help="Save results to JSON file")
    parser.add_argument("--underlying", type=str, help="Filter by underlying asset")
    parser.add_argument("--bull-only", action="store_true", help="Only bull/long ETFs")
    parser.add_argument("--bear-only", action="store_true", help="Only bear/short/inverse ETFs")
    parser.add_argument("--min-volume", type=int, help="Minimum 30d avg volume filter")
    parser.add_argument("--pairs-only", action="store_true",
                        help="Only show underlyings with both bull AND bear ETFs")
    parser.add_argument("--top-tradeable", action="store_true",
                        help="Algo-ready filter: vol>1M, price>$2, known underlying, paired bull+bear")
    args = parser.parse_args()

    print("🔍 Scanning TradingView for leveraged ETFs...")
    etfs = fetch_tradingview_leveraged_etfs()
    print(f"✅ Retrieved {len(etfs)} leveraged ETFs")

    # --top-tradeable: combined filter for algo-ready universe
    if args.top_tradeable:
        etfs = [e for e in etfs
                if e["avg_volume_30d"] >= 1_000_000
                and e["price"] is not None and e["price"] > 2.0
                and e["underlying"] not in ("Unknown", "Target")]
        # Force pairs-only
        has = {}
        for e in etfs:
            u = e["underlying"]
            if u not in has:
                has[u] = set()
            has[u].add(e["direction"])
        paired = {u for u, dirs in has.items() if len(dirs) == 2}
        etfs = [e for e in etfs if e["underlying"] in paired]

    if args.pairs_only and not args.top_tradeable:
        # Find underlyings with both directions
        has = {}
        for e in etfs:
            u = e["underlying"]
            if u not in has:
                has[u] = set()
            has[u].add(e["direction"])
        paired = {u for u, dirs in has.items() if len(dirs) == 2}
        etfs = [e for e in etfs if e["underlying"] in paired]

    if args.json:
        import json as j
        print(j.dumps(etfs, indent=2))
        return

    filtered = print_summary(etfs, args)

    if args.csv:
        save_csv(filtered, "leveraged_etfs.csv")

    if args.save_json:
        save_json(filtered, args.save_json)


if __name__ == "__main__":
    main()

