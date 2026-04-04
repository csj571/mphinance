"""
2x Leveraged ETF Mapper

Maps underlying stocks to their available 2x leveraged ETFs (bull & bear).
When multiple 2x ETFs exist for the same stock (e.g. NVDL vs NVDU vs NVDX),
picks the one with the highest average volume.

Providers tracked: Direxion, GraniteShares, REX Shares (T-REX), Defiance ETFs

Usage:
    from dossier.data_sources.leveraged_etf_map import (
        get_2x_etf, get_best_2x_etf, screen_leveraged_universe,
    )

    # Quick lookup
    etfs = get_2x_etf("NVDA")
    # {'bull': ['NVDU', 'NVDL', 'NVDX'], 'bear': ['NVD', 'NVDQ']}

    # Volume-weighted best pick
    best = get_best_2x_etf("NVDA")
    # {'underlying': 'NVDA', 'etf': 'NVDL', 'avg_volume': 48000000, ...}

    # Screen a list of tickers
    results = screen_leveraged_universe(["NVDA", "AAPL", "WMT", "PLTR"])
    # Returns only tickers that have 2x ETFs, sorted by ETF volume

Updated: 2026-04-03
"""

import sys
from pathlib import Path

# ══════════════════════════════════════════════════════════════════════════════
# MASTER MAP: underlying → list of 2x bull ETFs and 2x bear ETFs
#
# Sources:
#   [D]  = Direxion
#   [G]  = GraniteShares
#   [R]  = REX Shares / T-REX / Tuttle Capital
#   [Df] = Defiance ETFs
#
# Only includes SINGLE-STOCK 2x ETFs, not index/sector/commodity products
#
# Format: "UNDERLYING": {"bull": [...], "bear": [...]}
# ══════════════════════════════════════════════════════════════════════════════

LEVERAGED_2X_MAP = {

    # ═══════════════════════════════════════════════════════════════════════
    # MEGA-CAP TECH
    # ═══════════════════════════════════════════════════════════════════════
    "AAPL": {
        "bull": ["AAPU", "AAPB", "AAPX"],      # [D] [G] [R]
        "bear": [],
    },
    "MSFT": {
        "bull": ["MSFU", "MSFL", "MSFX"],       # [D] [G] [R]
        "bear": [],
    },
    "NVDA": {
        "bull": ["NVDU", "NVDL", "NVDX"],       # [D] [G] [R]
        "bear": ["NVD", "NVDQ"],                 # [G] [R]
    },
    "GOOGL": {
        "bull": ["GGLL", "GOOX"],                # [D] [R]
        "bear": [],
    },
    "AMZN": {
        "bull": ["AMZU", "AMZZ"],                # [D] [G]
        "bear": [],
    },
    "META": {
        "bull": ["METU", "FBL"],                 # [D] [G]
        "bear": [],
    },
    "TSLA": {
        "bull": ["TSLL", "TSLR", "TSLT"],        # [D] [G] [R]
        "bear": ["TSDD", "TSLZ"],                # [G] [R]
    },
    "NFLX": {
        "bull": ["NFXL", "NFLU"],                # [D] [R]
        "bear": [],
    },
    "ORCL": {
        "bull": ["ORCU", "ORCX"],                # [D] [Df]
        "bear": [],
    },

    # ═══════════════════════════════════════════════════════════════════════
    # SEMICONDUCTORS
    # ═══════════════════════════════════════════════════════════════════════
    "AMD": {
        "bull": ["AMUU", "AMDL"],                # [D] [G]
        "bear": [],
    },
    "AVGO": {
        "bull": ["AVL", "AVGU", "AVGX"],         # [D] [G] [Df]
        "bear": [],
    },
    "MU": {
        "bull": ["MUU", "MULL"],                 # [D] [G]
        "bear": [],
    },
    "ASML": {
        "bull": ["ASMU"],                         # [D]
        "bear": [],
    },
    "TSM": {
        "bull": ["TSMX", "TSMU"],                # [D] [G]
        "bear": [],
    },
    "SMCI": {
        "bull": ["SMCL", "SMCX"],                # [G] [Df]
        "bear": [],
    },
    "INTC": {
        "bull": ["LINT", "INTW"],                 # [D] [G]
        "bear": [],
    },
    "ARM": {
        "bull": ["ARMU"],                         # [R]
        "bear": [],
    },
    "QCOM": {
        "bull": ["QCMU"],                         # [D]
        "bear": [],
    },
    "MRVL": {
        "bull": ["MRVU"],                         # [D]
        "bear": [],
    },
    "TXN": {
        "bull": ["TXNU"],                         # [D]
        "bear": [],
    },
    "APH": {
        "bull": ["APHU"],                         # [R]
        "bear": [],
    },

    # ═══════════════════════════════════════════════════════════════════════
    # SOFTWARE & CLOUD
    # ═══════════════════════════════════════════════════════════════════════
    "ADBE": {
        "bull": ["ADBU"],                         # [D]
        "bear": [],
    },
    "NOW": {
        "bull": ["NOWL"],                         # [G]
        "bear": [],
    },
    "CRWD": {
        "bull": ["CRWL"],                         # [G]
        "bear": [],
    },
    "SNOW": {
        "bull": ["SNOU"],                         # [R]
        "bear": [],
    },
    "PLTR": {
        "bull": ["PLTU", "PTIR"],                # [D] [G]
        "bear": [],
    },
    "SHOP": {
        "bull": ["SHPU"],                         # [D]
        "bear": [],
    },
    "TTD": {
        "bull": ["TTDU"],                         # [R]
        "bear": [],
    },
    "ANET": {
        "bull": ["ANEL"],                         # [Df]
        "bear": [],
    },

    # ═══════════════════════════════════════════════════════════════════════
    # CRYPTO-ADJACENT
    # ═══════════════════════════════════════════════════════════════════════
    "COIN": {
        "bull": ["CONL", "CONX"],                # [G] [D]
        "bear": [],
    },
    "MSTR": {
        "bull": ["MSTU", "MSTX"],                # [R] [Df]
        "bear": ["MSTZ"],                         # [R]
    },
    "RIOT": {
        "bull": ["RIOX"],                         # [Df]
        "bear": [],
    },
    "BITF": {
        "bull": ["BTFL"],                         # [Df]
        "bear": [],
    },
    "IREN": {
        "bull": ["IRE"],                          # [Df]
        "bear": [],
    },

    # ═══════════════════════════════════════════════════════════════════════
    # AI & QUANTUM
    # ═══════════════════════════════════════════════════════════════════════
    "IONQ": {
        "bull": ["IONX"],                         # [Df]
        "bear": [],
    },
    "RGTI": {
        "bull": ["RGTX"],                         # [Df]
        "bear": [],
    },
    "SOUN": {
        "bull": ["SOUX"],                         # [Df]
        "bear": [],
    },

    # ═══════════════════════════════════════════════════════════════════════
    # FINTECH & CONSUMER
    # ═══════════════════════════════════════════════════════════════════════
    "SOFI": {
        "bull": ["SOFA", "SOFX"],                # [D] [Df]
        "bear": [],
    },
    "PYPL": {
        "bull": ["PALU"],                         # [D]
        "bear": [],
    },
    "HOOD": {
        "bull": ["HODU", "ROBN", "HOOX"],         # [D] [R] [Df]
        "bear": [],
    },
    "AFRM": {
        "bull": ["AFRU"],                         # [R]
        "bear": [],
    },
    "HIMS": {
        "bull": ["HIMZ"],                         # [Df]
        "bear": [],
    },
    "OSCR": {
        "bull": ["OSCX"],                         # [Df]
        "bear": [],
    },
    "CVNA": {
        "bull": ["CVNX"],                         # [Df]
        "bear": [],
    },

    # ═══════════════════════════════════════════════════════════════════════
    # AEROSPACE & DEFENSE
    # ═══════════════════════════════════════════════════════════════════════
    "BA": {
        "bull": ["BOEU"],                         # [D]
        "bear": [],
    },
    "LMT": {
        "bull": ["LMTL"],                         # [D]
        "bear": [],
    },
    "AXON": {
        "bull": ["AXUP"],                         # [R]
        "bear": [],
    },
    "RKLB": {
        "bull": ["RKLX"],                         # [Df]
        "bear": [],
    },
    "AVAV": {
        "bull": ["AVXX"],                         # [Df]
        "bear": [],
    },
    "KTOS": {
        "bull": ["KTUP"],                         # [R]
        "bear": [],
    },

    # ═══════════════════════════════════════════════════════════════════════
    # ENERGY & INDUSTRIAL
    # ═══════════════════════════════════════════════════════════════════════
    "XOM": {
        "bull": ["XOMX"],                         # [D]
        "bear": [],
    },
    "VST": {
        "bull": ["VSTL"],                         # [Df]
        "bear": [],
    },
    "SMR": {
        "bull": ["SMUP"],                         # [R]
        "bear": [],
    },
    "OKLO": {
        "bull": ["OKLL"],                         # [Df]
        "bear": [],
    },
    "MP": {
        "bull": ["MPL"],                          # [Df]
        "bear": [],
    },

    # ═══════════════════════════════════════════════════════════════════════
    # HEALTHCARE & PHARMA
    # ═══════════════════════════════════════════════════════════════════════
    "LLY": {
        "bull": ["ELIL", "LLYX"],                # [D] [Df]
        "bear": [],
    },
    "UNH": {
        "bull": ["UNHU"],                         # [D]
        "bear": [],
    },
    "NVO": {
        "bull": ["NVOX"],                         # [Df]
        "bear": [],
    },

    # ═══════════════════════════════════════════════════════════════════════
    # NETWORKING & ENTERPRISE
    # ═══════════════════════════════════════════════════════════════════════
    "CSCO": {
        "bull": ["CSCL"],                         # [D]
        "bear": [],
    },
    "DELL": {
        "bull": ["DLLL"],                         # [G]
        "bear": [],
    },
    "CRWV": {
        "bull": ["CRWU"],                         # [R]
        "bear": [],
    },

    # ═══════════════════════════════════════════════════════════════════════
    # MEGA-CAP VALUE & DIVERSIFIED
    # ═══════════════════════════════════════════════════════════════════════
    "BRK.B": {
        "bull": ["BRKU"],                         # [D]
        "bear": [],
    },
    "BABA": {
        "bull": ["BABU", "BABX"],                # [D] [G]
        "bear": [],
    },
    "PDD": {
        "bull": ["PDDL"],                         # [G]
        "bear": [],
    },

    # ═══════════════════════════════════════════════════════════════════════
    # GAMING, SOCIAL, MEME
    # ═══════════════════════════════════════════════════════════════════════
    "GME": {
        "bull": ["GMEU"],                         # [R]
        "bear": [],
    },
    "RBLX": {
        "bull": ["RBLU"],                         # [R]
        "bear": [],
    },
    "DKNG": {
        "bull": ["DKUP", "DKNX"],                # [R] [Df]
        "bear": [],
    },
    "DJT": {
        "bull": ["DJTU"],                         # [R]
        "bear": [],
    },
    "RDDT": {
        "bull": ["RDTL"],                         # [G]
        "bear": [],
    },

    # ═══════════════════════════════════════════════════════════════════════
    # MISC SMALL/MID-CAP WITH 2x
    # ═══════════════════════════════════════════════════════════════════════
    "UBER": {
        "bull": ["UBRL"],                         # [G]
        "bear": [],
    },
    "VRT": {
        "bull": ["VRTL"],                         # [G]
        "bear": [],
    },
    "ONDS": {
        "bull": ["ONDL"],                         # [Df]
        "bear": [],
    },
}

# ── Reverse map: ETF ticker → underlying ──────────────────────────────────
_REVERSE_MAP = {}
for _underlying, _etfs in LEVERAGED_2X_MAP.items():
    for _ticker in _etfs.get("bull", []) + _etfs.get("bear", []):
        _REVERSE_MAP[_ticker] = _underlying


def get_all_underlyings() -> list[str]:
    """Return sorted list of all stocks that have a 2x leveraged ETF."""
    return sorted(LEVERAGED_2X_MAP.keys())


def get_2x_etf(ticker: str) -> dict | None:
    """
    Look up all 2x ETFs for a given underlying stock.

    Returns:
        {"bull": ["NVDU", "NVDL", ...], "bear": ["NVD"]}
        or None if no 2x ETF exists.
    """
    return LEVERAGED_2X_MAP.get(ticker.upper())


def get_underlying(etf_ticker: str) -> str | None:
    """Reverse lookup: given a 2x ETF ticker, return the underlying stock."""
    return _REVERSE_MAP.get(etf_ticker.upper())


def has_2x_etf(ticker: str) -> bool:
    """Quick check: does this stock have any 2x leveraged ETF?"""
    return ticker.upper() in LEVERAGED_2X_MAP


def _fetch_avg_volume(ticker: str) -> float:
    """Fetch 20-day average volume for a ticker via yfinance."""
    try:
        import yfinance as yf
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1mo")
        if hist.empty:
            return 0.0
        return float(hist["Volume"].tail(20).mean())
    except Exception:
        return 0.0


def get_best_2x_etf(
    ticker: str,
    direction: str = "bull",
    use_cache: bool = True,
    _cache: dict = {},
) -> dict | None:
    """
    For a given underlying stock, find the 2x ETF with the highest
    average volume. Returns the best pick with volume data.

    Args:
        ticker: Underlying stock symbol (e.g. "NVDA")
        direction: "bull" or "bear"
        use_cache: Cache volume lookups across calls

    Returns:
        {
            "underlying": "NVDA",
            "etf": "NVDL",
            "direction": "bull",
            "avg_volume": 48000000,
            "all_options": [
                {"ticker": "NVDL", "avg_volume": 48000000},
                {"ticker": "NVDU", "avg_volume": 12000000},
                {"ticker": "NVDX", "avg_volume": 5000000},
            ]
        }
        or None if no 2x ETF exists for that direction.
    """
    ticker = ticker.upper()
    etf_data = LEVERAGED_2X_MAP.get(ticker)
    if not etf_data:
        return None

    candidates = etf_data.get(direction, [])
    if not candidates:
        return None

    # Single candidate — skip volume lookup
    if len(candidates) == 1:
        vol = 0.0
        if use_cache and candidates[0] in _cache:
            vol = _cache[candidates[0]]
        else:
            vol = _fetch_avg_volume(candidates[0])
            if use_cache:
                _cache[candidates[0]] = vol
        return {
            "underlying": ticker,
            "etf": candidates[0],
            "direction": direction,
            "avg_volume": vol,
            "all_options": [{"ticker": candidates[0], "avg_volume": vol}],
        }

    # Multiple candidates — rank by volume
    scored = []
    for etf in candidates:
        if use_cache and etf in _cache:
            vol = _cache[etf]
        else:
            vol = _fetch_avg_volume(etf)
            if use_cache:
                _cache[etf] = vol
        scored.append({"ticker": etf, "avg_volume": vol})

    scored.sort(key=lambda x: x["avg_volume"], reverse=True)
    best = scored[0]

    return {
        "underlying": ticker,
        "etf": best["ticker"],
        "direction": direction,
        "avg_volume": best["avg_volume"],
        "all_options": scored,
    }


def screen_leveraged_universe(
    tickers: list[str] | None = None,
    direction: str = "bull",
    min_avg_volume: float = 0,
) -> list[dict]:
    """
    Screen a list of tickers (or the full map) and return only those
    with 2x leveraged ETFs, sorted by ETF volume (highest first).

    Args:
        tickers: List of underlying stock symbols. If None, screens
                 the entire LEVERAGED_2X_MAP universe.
        direction: "bull" or "bear"
        min_avg_volume: Minimum ETF average volume to include (default: 0)

    Returns:
        List of dicts sorted by avg_volume descending:
        [
            {
                "underlying": "NVDA",
                "etf": "NVDL",
                "direction": "bull",
                "avg_volume": 48000000,
                "all_options": [...]
            },
            ...
        ]
    """
    if tickers is None:
        tickers = list(LEVERAGED_2X_MAP.keys())
    else:
        tickers = [t.upper() for t in tickers]

    results = []
    for t in tickers:
        best = get_best_2x_etf(t, direction=direction)
        if best and best["avg_volume"] >= min_avg_volume:
            results.append(best)

    results.sort(key=lambda x: x["avg_volume"], reverse=True)
    return results


def print_universe(direction: str = "bull"):
    """Pretty-print the full leveraged universe with volume data."""
    print(f"\n{'═' * 70}")
    print(f"  2x LEVERAGED ETF UNIVERSE — {direction.upper()} SIDE")
    print(f"{'═' * 70}")
    print(f"  {'Underlying':<10} {'Best 2x ETF':<12} {'Avg Volume':>14}  {'All Options'}")
    print(f"  {'─' * 10} {'─' * 12} {'─' * 14}  {'─' * 25}")

    results = screen_leveraged_universe(direction=direction)
    for r in results:
        opts = ", ".join(
            f"{o['ticker']}({o['avg_volume']/1e6:.1f}M)"
            for o in r["all_options"]
        )
        vol_str = f"{r['avg_volume']/1e6:.1f}M" if r["avg_volume"] > 0 else "N/A"
        print(f"  {r['underlying']:<10} {r['etf']:<12} {vol_str:>14}  {opts}")

    print(f"\n  Total: {len(results)} stocks with 2x {direction} ETFs")
    print(f"{'═' * 70}\n")


# ── CLI ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="2x Leveraged ETF Mapper")
    parser.add_argument("tickers", nargs="*", help="Tickers to look up (default: full universe)")
    parser.add_argument("--direction", choices=["bull", "bear"], default="bull")
    parser.add_argument("--min-volume", type=float, default=0, help="Min avg volume filter")
    parser.add_argument("--list", action="store_true", help="List all underlyings")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if args.list:
        underlyings = get_all_underlyings()
        print(f"\n{len(underlyings)} stocks with 2x ETFs:")
        for t in underlyings:
            etfs = LEVERAGED_2X_MAP[t]
            bulls = ", ".join(etfs.get("bull", [])) or "—"
            bears = ", ".join(etfs.get("bear", [])) or "—"
            print(f"  {t:<8} Bull: {bulls:<24} Bear: {bears}")
        sys.exit(0)

    if args.json:
        import json
        tickers = args.tickers if args.tickers else None
        results = screen_leveraged_universe(
            tickers=tickers,
            direction=args.direction,
            min_avg_volume=args.min_volume,
        )
        print(json.dumps(results, indent=2))
    elif args.tickers:
        # Lookup specific tickers
        for t in args.tickers:
            t = t.upper()
            if has_2x_etf(t):
                best = get_best_2x_etf(t, direction=args.direction)
                if best:
                    opts = ", ".join(
                        f"{o['ticker']}({o['avg_volume']/1e6:.1f}M)"
                        for o in best["all_options"]
                    )
                    print(f"  {t} → Best 2x: {best['etf']} "
                          f"(vol: {best['avg_volume']/1e6:.1f}M) | All: {opts}")
                else:
                    print(f"  {t} → No {args.direction} 2x ETF")
            else:
                print(f"  {t} → No 2x ETF available")
    else:
        print_universe(direction=args.direction)
