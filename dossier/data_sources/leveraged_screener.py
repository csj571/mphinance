"""
👻 Ghost 2x Leveraged ETF Daily Screener — Multi-Timeframe

Scans the 2x leveraged universe for today's best day trades.
Uses TradingView scanner API for all technicals (no yfinance).

Multi-TF: Daily / 1H / 15M — ADX, DI+/DI-, RSI, change% per timeframe.

Filters:
  - ADX ≥ 15 on 1H or 15M (lower TF shows trend building first)
  - DI+/DI- direction (BULL = DI+ > DI-, BEAR = DI- > DI+)
  - Relative volume ≥ 1.2x (daily)
  - ETF avg volume ≥ 500K (day trading needs liquidity)
  - RSI shown but NOT filtered (that's for entry timing)

Warnings (non-blocking):
  - ⚠️ EXTENDED: RSI > 80 or < 20 on any timeframe
  - 🔴 GAP: stock gapped > 2% at open
  - 🏷️ SECTOR: flags sector crowding when 3+ signals share a sector

Data flow:
  TradingView scanner → leveraged_etf_map → ETF volume (yfinance, cached)

Usage:
    python3 -m dossier.data_sources.leveraged_screener
    python3 -m dossier.data_sources.leveraged_screener --json
    python3 -m dossier.data_sources.leveraged_screener --top 10
    python3 -m dossier.data_sources.leveraged_screener --min-adx 10

© mphinance + Sam the Quant Ghost — "Double the leverage, double the fun, double the pain."
Updated: 2026-04-03
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from collections import Counter

from tradingview_screener import Query, Column

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dossier.data_sources.leveraged_etf_map import (
    LEVERAGED_2X_MAP,
    get_best_2x_etf,
    get_all_underlyings,
)


# ══════════════════════════════════════════════════════════════════════════════
# TRADINGVIEW COLUMNS — multi-timeframe
# ══════════════════════════════════════════════════════════════════════════════

# Base columns (daily)
TV_COLS = [
    "name", "close", "change", "gap",
    "premarket_change", "premarket_close", "premarket_gap",
    "postmarket_change", "postmarket_close",
    "relative_volume_10d_calc",
    "ADX", "ADX+DI", "ADX-DI", "RSI",
    "volume", "average_volume_10d_calc",
    "ATR", "Recommend.All",
    "EMA8", "EMA21",
    "sector",
]

# 1H (|60) and 15M (|15) overlays
TV_TF_COLS = [
    "ADX|60", "ADX+DI|60", "ADX-DI|60", "RSI|60", "change|60",
    "ADX|15", "ADX+DI|15", "ADX-DI|15", "RSI|15", "change|15",
]

ALL_TV_COLS = TV_COLS + TV_TF_COLS


# ══════════════════════════════════════════════════════════════════════════════
# FETCH FROM TRADINGVIEW
# ══════════════════════════════════════════════════════════════════════════════

def fetch_tv_data(tickers: list[str]) -> dict[str, dict]:
    """
    Pull all technicals for a list of tickers from TradingView
    in a single bulk request. Returns dict keyed by ticker symbol.
    """
    q = (Query()
         .select(*ALL_TV_COLS)
         .where(Column("name").isin(tickers))
         .set_markets("america")
         .limit(len(tickers) + 10))

    _, df = q.get_scanner_data()

    result = {}
    for _, row in df.iterrows():
        name = row.get("name")
        if not name:
            continue

        def _v(col, default=None):
            val = row.get(col)
            if val is None or (isinstance(val, float) and val != val):  # NaN check
                return default
            return val

        result[name] = {
            # Daily
            "price": _v("close", 0),
            "change_pct": _v("change", 0),
            "gap": _v("gap", 0),
            "pre_price": _v("premarket_close", 0),
            "pre_change": _v("premarket_change", 0),
            "pre_gap": _v("premarket_gap", 0),
            "post_price": _v("postmarket_close", 0),
            "post_change": _v("postmarket_change", 0),
            "rel_vol": _v("relative_volume_10d_calc", 0),
            "volume": _v("volume", 0),
            "avg_volume": _v("average_volume_10d_calc", 0),
            "atr": _v("ATR", 0),
            "recommend": _v("Recommend.All", 0),
            "ema8": _v("EMA8", 0),
            "ema21": _v("EMA21", 0),
            "sector": _v("sector", ""),
            # Daily technicals
            "D_adx": _v("ADX"),
            "D_dip": _v("ADX+DI"),
            "D_dim": _v("ADX-DI"),
            "D_rsi": _v("RSI"),
            # 1H technicals
            "1H_adx": _v("ADX|60"),
            "1H_dip": _v("ADX+DI|60"),
            "1H_dim": _v("ADX-DI|60"),
            "1H_rsi": _v("RSI|60"),
            "1H_chg": _v("change|60"),
            # 15M technicals
            "15M_adx": _v("ADX|15"),
            "15M_dip": _v("ADX+DI|15"),
            "15M_dim": _v("ADX-DI|15"),
            "15M_rsi": _v("RSI|15"),
            "15M_chg": _v("change|15"),
        }

    return result


# ══════════════════════════════════════════════════════════════════════════════
# ENRICH WITH ETF DATA + COMPUTE FLAGS
# ══════════════════════════════════════════════════════════════════════════════

def enrich_ticker(ticker: str, tv: dict) -> dict | None:
    """
    Take raw TradingView data for an underlying stock and enrich it with:
    - Best 2x ETF (bull + bear)
    - Trend direction per timeframe
    - Warning flags (extended RSI, gap, etc.)
    """
    if not tv or not tv.get("price"):
        return None

    # ── Extended Hours Overlay ──
    now_est = datetime.now(ZoneInfo("America/New_York"))
    is_premarket = now_est.hour >= 4 and (now_est.hour < 9 or (now_est.hour == 9 and now_est.minute < 30))
    is_afterhours = now_est.hour >= 16 and now_est.hour < 20
    
    ticker_display = ticker
    price = tv["price"]
    change_pct = tv["change_pct"]
    gap = tv.get("gap", 0) or 0
    
    if is_premarket and tv.get("pre_price"):
        price = tv["pre_price"]
        change_pct = tv["pre_change"]
        gap = tv.get("pre_gap", 0) or 0
        ticker_display = f"{ticker} [PRE]"
    elif is_afterhours and tv.get("post_price"):
        price = tv["post_price"]
        change_pct = tv["post_change"]
        ticker_display = f"{ticker} [AH]"

    # ── Resolve 2x ETFs ──
    bull_etf = get_best_2x_etf(ticker, direction="bull")
    bear_etf = get_best_2x_etf(ticker, direction="bear")

    if not bull_etf:
        return None

    # ── Per-TF trend direction ──
    def _trend(dip, dim):
        if dip is None or dim is None:
            return "—"
        return "BULL" if dip > dim else "BEAR"

    d_trend = _trend(tv.get("D_dip"), tv.get("D_dim"))
    h_trend = _trend(tv.get("1H_dip"), tv.get("1H_dim"))
    m_trend = _trend(tv.get("15M_dip"), tv.get("15M_dim"))

    # ── EMA stack ──
    ema8 = tv.get("ema8", 0) or 0
    ema21 = tv.get("ema21", 0) or 0
    ema_stack = "BULL" if ema8 > ema21 else "BEAR"

    # ── Best ADX across lower TFs (1H, 15M) ──
    adx_vals = {}
    for tf in ["1H", "15M"]:
        v = tv.get(f"{tf}_adx")
        if v is not None:
            adx_vals[tf] = v
    best_adx = max(adx_vals.values()) if adx_vals else None
    best_adx_tf = max(adx_vals, key=adx_vals.get) if adx_vals else None

    # ── Warnings ──
    warnings = []
    # RSI extension on any TF
    for tf in ["D", "1H", "15M"]:
        rsi = tv.get(f"{tf}_rsi")
        if rsi is not None:
            if rsi > 80:
                warnings.append(f"⚠️ RSI {tf}={rsi:.0f}")
            elif rsi < 20:
                warnings.append(f"⚠️ RSI {tf}={rsi:.0f}")

    # Gap warning
    gap = tv.get("gap", 0) or 0
    if abs(gap) > 2:
        warnings.append(f"{'📈' if gap > 0 else '📉'} GAP {gap:+.1f}%")

    # ── Multi-TF agreement ──
    trends = [d_trend, h_trend, m_trend]
    bull_count = trends.count("BULL")
    bear_count = trends.count("BEAR")
    if bull_count == 3:
        alignment = "🟢 ALL BULL"
    elif bear_count == 3:
        alignment = "🔴 ALL BEAR"
    elif bull_count >= 2:
        alignment = "🟡 MIXED↑"
    elif bear_count >= 2:
        alignment = "🟡 MIXED↓"
    else:
        alignment = "⚪ CHOPPY"

    return {
        "underlying": ticker_display,
        "price": round(price, 2) if price else 0,
        "change_pct": round(change_pct, 2) if change_pct else 0,
        "gap": round(gap, 2) if gap else 0,
        "rel_vol": round(tv.get("rel_vol", 0), 2),
        "atr": round(tv.get("atr", 0), 2),
        "atr_pct": round(tv.get("atr", 0) / price * 100, 2) if price else 0,
        "ema_stack": ema_stack,
        "sector": tv.get("sector", ""),
        # Per-TF
        "D_adx": round(tv.get("D_adx") or 0, 1),
        "D_rsi": round(tv.get("D_rsi") or 0, 1),
        "D_trend": d_trend,
        "1H_adx": round(tv.get("1H_adx") or 0, 1),
        "1H_rsi": round(tv.get("1H_rsi") or 0, 1),
        "1H_chg": round(tv.get("1H_chg") or 0, 2),
        "1H_trend": h_trend,
        "15M_adx": round(tv.get("15M_adx") or 0, 1),
        "15M_rsi": round(tv.get("15M_rsi") or 0, 1),
        "15M_chg": round(tv.get("15M_chg") or 0, 2),
        "15M_trend": m_trend,
        # Composite
        "best_adx": round(best_adx, 1) if best_adx else None,
        "best_adx_tf": best_adx_tf,
        "alignment": alignment,
        "warnings": warnings,
        # ETF
        "bull_etf": bull_etf["etf"],
        "bull_etf_vol": bull_etf["avg_volume"],
        "bear_etf": bear_etf["etf"] if bear_etf else None,
        "bear_etf_vol": bear_etf["avg_volume"] if bear_etf else 0,
        "has_bear": bear_etf is not None,
    }


# ══════════════════════════════════════════════════════════════════════════════
# FULL SCAN
# ══════════════════════════════════════════════════════════════════════════════

def run_daily_screen(
    min_adx: float = 15.0,
    min_rel_vol: float = 1.2,
    min_etf_volume: float = 500_000,
    top_n: int = 0,
) -> dict:
    """
    Scan the full 2x leveraged universe. One TradingView API call.
    """
    tickers = get_all_underlyings()
    print(f"  🔍 Scanning {len(tickers)} underlyings via TradingView (D/1H/15M)...")

    # ── Single bulk fetch ──
    tv_data = fetch_tv_data(tickers)
    found = len(tv_data)
    print(f"  ✓ TradingView returned data for {found}/{len(tickers)} tickers")

    # ── Enrich each ticker ──
    results = []
    for t in tickers:
        tv = tv_data.get(t)
        if not tv:
            continue
        enriched = enrich_ticker(t, tv)
        if enriched:
            results.append(enriched)

    # ── Apply filters ──
    passing = []
    for r in results:
        # ADX ≥ threshold on 1H or 15M (lower TF only)
        adx_ok = (r["best_adx"] is not None and r["best_adx"] >= min_adx)

        # Relative volume ≥ 1.2x
        rvol_ok = (r["rel_vol"] >= min_rel_vol)

        # ETF must have real liquidity for day trading
        etf_vol_ok = (r["bull_etf_vol"] >= min_etf_volume)

        if adx_ok and rvol_ok and etf_vol_ok:
            passing.append(r)

    filtered_out = len(results) - len(passing)

    # ── Market regime ──
    up_count = sum(1 for r in results if r["change_pct"] > 0)
    down_count = sum(1 for r in results if r["change_pct"] < 0)
    regime = "UP" if up_count > down_count else "DOWN"

    # ── Sector crowding check ──
    sector_counts = Counter(r["sector"] for r in passing if r["sector"])
    crowded_sectors = {s: c for s, c in sector_counts.items() if c >= 3}

    # ── Split by direction ──
    movers_up = sorted(
        [r for r in passing if r["change_pct"] > 0],
        key=lambda x: x["change_pct"], reverse=True,
    )
    movers_down = sorted(
        [r for r in passing if r["change_pct"] <= 0],
        key=lambda x: x["change_pct"],
    )

    if top_n > 0:
        movers_up = movers_up[:top_n]
        movers_down = movers_down[:top_n]

    cst = ZoneInfo("America/Chicago")
    scan_time = datetime.now(cst).strftime("%Y-%m-%d %I:%M %p CST")

    return {
        "scan_time": scan_time,
        "market_regime": regime,
        "universe_size": len(tickers),
        "data_received": found,
        "enriched": len(results),
        "passing_filters": len(passing),
        "filtered_out": filtered_out,
        "crowded_sectors": crowded_sectors,
        "filters": {
            "min_adx": min_adx,
            "min_rel_vol": min_rel_vol,
            "min_etf_volume": min_etf_volume,
        },
        "movers_up": movers_up,
        "movers_down": movers_down,
        "all_passing": passing,
    }


# ══════════════════════════════════════════════════════════════════════════════
# ANSI COLORS
# ══════════════════════════════════════════════════════════════════════════════

R = "\033[0m"
RED = "\033[91m"
GRN = "\033[92m"
YLW = "\033[93m"
CYN = "\033[96m"
GRY = "\033[90m"
BLD = "\033[1m"
WHT = "\033[97m"


# ══════════════════════════════════════════════════════════════════════════════
# PRETTY PRINT
# ══════════════════════════════════════════════════════════════════════════════

def _tf_color(trend: str) -> str:
    if trend == "BULL": return GRN
    if trend == "BEAR": return RED
    return GRY


def _print_table(title: str, rows: list[dict]):
    """Print multi-TF screener table with trend direction."""
    if not rows:
        print(f"\n  {title}: {GRY}(none){R}\n")
        return

    print(f"\n  {BLD}{title}{R}")
    print(f"  {'─' * 135}")
    # Header
    print(f"  {'':>8} {'':>7} {'':>6} {'':>5} {'':>5}"
          f"  │{'DAILY':^17}│{'1 HOUR':^17}│{'15 MIN':^17}│"
          f" {'':>8} {'':>12}")
    print(f"  {'Ticker':<8} {'Price':>7} {'Chg%':>6} {'RVol':>5} {'Gap%':>5}"
          f"  │{'ADX':>4} {'RSI':>4} {'Dir':>5} │{'ADX':>4} {'RSI':>4} {'Dir':>5} │"
          f"{'ADX':>4} {'RSI':>4} {'Dir':>5} │"
          f" {'Align':>12} {'→ 2x ETF':>10}")
    print(f"  {'─' * 135}")

    for r in rows:
        chg_c = GRN if r["change_pct"] > 0 else RED
        chg_str = f"{r['change_pct']:+.1f}%"
        rvol_str = f"{r['rel_vol']:.1f}x"
        gap_str = f"{r['gap']:+.1f}%" if abs(r['gap']) > 0.1 else "  — "

        # Per-TF with color
        d_c = _tf_color(r["D_trend"])
        h_c = _tf_color(r["1H_trend"])
        m_c = _tf_color(r["15M_trend"])

        # ETF recommendation based on lower-TF trend
        lower_trend = r.get("1H_trend", "—")
        if lower_trend == "BULL":
            etf_str = r["bull_etf"]
        elif lower_trend == "BEAR" and r["has_bear"]:
            etf_str = f"{r['bear_etf']}🐻"
        elif lower_trend == "BEAR":
            etf_str = f"{r['bull_etf']}⏳"  # wait for bounce
        else:
            etf_str = r["bull_etf"]

        print(f"  {BLD}{r['underlying']:<8}{R} {r['price']:>7.2f} "
              f"{chg_c}{chg_str:>6}{R} {rvol_str:>5} {gap_str:>5}"
              f"  │{r['D_adx']:>4.0f} {r['D_rsi']:>4.0f} {d_c}{r['D_trend']:>5}{R} │"
              f"{r['1H_adx']:>4.0f} {r['1H_rsi']:>4.0f} {h_c}{r['1H_trend']:>5}{R} │"
              f"{r['15M_adx']:>4.0f} {r['15M_rsi']:>4.0f} {m_c}{r['15M_trend']:>5}{R} │"
              f" {r['alignment']:>12} {CYN}{etf_str:>10}{R}")

        # Warning line (if any)
        if r["warnings"]:
            warn_str = "  ".join(r["warnings"])
            print(f"  {GRY}{'':>8} {warn_str}{R}")


def print_screen(scan: dict):
    """Pretty-print everything."""
    print(f"\n{'═' * 137}")
    print(f"  {CYN}{BLD}👻 GHOST 2x LEVERAGED SCREENER{R} — Multi-TF | {scan['scan_time']}")
    print(f"{'═' * 137}")

    regime_c = GRN if scan["market_regime"] == "UP" else RED
    regime_icon = "🟢" if scan["market_regime"] == "UP" else "🔴"
    print(f"  Market Regime: {regime_c}{regime_icon} {scan['market_regime']}{R}"
          f"  │  Universe: {scan['universe_size']}"
          f"  │  Data: {scan['data_received']}"
          f"  │  Passing: {CYN}{BLD}{scan['passing_filters']}{R}"
          f"  │  Filtered: {scan['filtered_out']}")
    print(f"  Filters: ADX ≥ {scan['filters']['min_adx']} (1H/15M) │ "
          f"RelVol ≥ {scan['filters']['min_rel_vol']}x │ "
          f"ETF Vol ≥ {scan['filters']['min_etf_volume']/1e3:.0f}K")

    # Sector crowding
    if scan.get("crowded_sectors"):
        sectors = ", ".join(f"{s}({c})" for s, c in scan["crowded_sectors"].items())
        print(f"  {YLW}⚠️  Sector Crowding: {sectors}{R}")

    if scan["market_regime"] == "UP":
        _print_table("🚀 STRONGEST MOVERS UP — Trade the 2x BULL", scan["movers_up"])
        _print_table("📉 DOWN BUT TRENDING — Bear ETF or bounce play", scan["movers_down"])
    else:
        _print_table("📉 BIGGEST DECLINERS — Bear ETF if available", scan["movers_down"])
        _print_table("🚀 GREEN IN RED TAPE — Relative strength plays", scan["movers_up"])

    print(f"\n{'═' * 137}")
    print(f"  {GRY}💡 ADX filter uses 1H + 15M only — daily ADX is too slow for day trading")
    print(f"  💡 Dir = DI+/DI- trend direction per timeframe (BULL = DI+ > DI-)")
    print(f"  💡 🐻 = bear ETF recommended | ⏳ = no bear ETF, wait for bounce")
    print(f"  💡 RSI shown for entry timing — not used as a filter{R}")
    print(f"{'═' * 137}\n")


# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="👻 Ghost 2x Leveraged Daily Screener (Multi-TF)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--min-adx", type=float, default=15.0,
                        help="Min ADX on 1H/15M (default: 15)")
    parser.add_argument("--min-rvol", type=float, default=1.2,
                        help="Min daily relative volume (default: 1.2)")
    parser.add_argument("--min-etf-vol", type=float, default=500_000,
                        help="Min ETF avg volume (default: 500K)")
    parser.add_argument("--top", type=int, default=0,
                        help="Show top N per category (0=all)")
    parser.add_argument("--json", action="store_true",
                        help="Output as JSON")
    args = parser.parse_args()

    scan = run_daily_screen(
        min_adx=args.min_adx,
        min_rel_vol=args.min_rvol,
        min_etf_volume=args.min_etf_vol,
        top_n=args.top,
    )

    if args.json:
        # Clean for JSON output
        for key in ["movers_up", "movers_down", "all_passing"]:
            for item in scan.get(key, []):
                item.pop("warnings", None)  # warnings have emoji, keep it clean
        print(json.dumps(scan, indent=2, default=str))
    else:
        print_screen(scan)
