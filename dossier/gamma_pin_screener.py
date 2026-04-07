#!/usr/bin/env python3
"""
👻 Gamma Pin Distance Screener v3 — OI Sandwich Finder

Finds stocks OUTSIDE their OI "sandwich zone" on OpEx day.

The sandwich = the zone between the put-OI centroid (floor) and the
call-OI centroid (ceiling). When price is outside this zone, gamma
exposure pulls it back in. The further outside = the bigger the snap.

Key insight (from Michael): individual OI walls are misleading because
they're spread legs. The ZONE matters — where put OI dominates vs
where call OI dominates. The gravitational center is where both converge.

Architecture:
  Stage 1 → TradingView bulk API: fetch ~2000 liquid US stocks
  Stage 2 → Tradier options chain: get OI by strike for expiration date
  Stage 3 → OI sandwich zone calculation (put centroid / call centroid / gravity)
  Stage 4 → Rank by "Overextension" — distance outside the pin zone

Usage:
    python3 -m dossier.gamma_pin_screener                         # Full scan
    python3 -m dossier.gamma_pin_screener --tickers SOFI,AMD,TSLA # Specific
    python3 -m dossier.gamma_pin_screener --top 50                # Top 50
    python3 -m dossier.gamma_pin_screener --json                  # Machine output

© mphinance + Sam the Quant Ghost  — "The pin always wins. Except when it doesn't."
"""

import argparse
import json
import math
import os
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import requests

# ─── API Key ──────────────────────────────────────────────────────
def _get_tradier_key() -> str:
    key = os.getenv("TRADIER_API_KEY")
    if key:
        return key
    env_paths = [
        Path.home() / "Antigravity" / "alpha-momentum" / ".env",
        Path.home() / "Antigravity" / "mphinance" / "tightspread" / ".env",
        Path.home() / "tradier-desktop" / ".env",
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

TRADIER_KEY = None

def _tradier_headers():
    global TRADIER_KEY
    if TRADIER_KEY is None:
        TRADIER_KEY = _get_tradier_key()
    return {"Authorization": f"Bearer {TRADIER_KEY}", "Accept": "application/json"}


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 1 — TRADINGVIEW BULK SCANNER  ████
# ═══════════════════════════════════════════════════════════════════

TV_SCANNER_URL = "https://scanner.tradingview.com/america/scan"
TV_COLUMNS = [
    "name", "description", "close", "change",
    "volume", "average_volume_30d_calc", "market_cap_basic",
    "ATR", "ADX", "sector",
]

def tv_fetch_stocks(min_price=5.0, min_avg_vol=500_000, min_cap=500_000_000) -> list[dict]:
    payload = {
        "filter": [
            {"left": "type", "operation": "in_range", "right": ["stock"]},
            {"left": "subtype", "operation": "in_range",
             "right": ["common", "foreign-issuer"]},
            {"left": "exchange", "operation": "in_range",
             "right": ["NYSE", "NASDAQ", "AMEX"]},
            {"left": "average_volume_30d_calc", "operation": "greater", "right": min_avg_vol},
            {"left": "close", "operation": "greater", "right": min_price},
            {"left": "market_cap_basic", "operation": "greater", "right": min_cap},
        ],
        "options": {"lang": "en"},
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": TV_COLUMNS,
        "sort": {"sortBy": "average_volume_30d_calc", "sortOrder": "desc"},
        "range": [0, 5000],
    }
    resp = requests.post(TV_SCANNER_URL, json=payload, timeout=30)
    resp.raise_for_status()
    results = []
    for item in resp.json().get("data", []):
        d = item.get("d", [])
        if len(d) < len(TV_COLUMNS) or not d[0] or d[2] is None:
            continue
        results.append({
            "ticker": d[0], "name": d[1] or d[0], "price": d[2],
            "change_pct": d[3] or 0, "volume": d[4] or 0,
            "avg_vol_30d": d[5] or 0, "market_cap": d[6] or 0,
            "atr": d[7] or 0, "adx": d[8] or 0, "sector": d[9] or "",
        })
    return results


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 2 — TRADIER OPTIONS CHAIN  ████
# ═══════════════════════════════════════════════════════════════════

TRADIER_BASE = "https://api.tradier.com/v1"

def get_options_expirations(symbol: str) -> list[str]:
    try:
        resp = requests.get(
            f"{TRADIER_BASE}/markets/options/expirations",
            params={"symbol": symbol, "includeAllRoots": "true"},
            headers=_tradier_headers(), timeout=10)
        if resp.status_code != 200:
            return []
        exps = resp.json().get("expirations", {})
        if not exps:
            return []
        dates = exps.get("date", [])
        return [dates] if isinstance(dates, str) else (dates or [])
    except Exception:
        return []

def get_options_chain(symbol: str, expiration: str) -> list[dict]:
    try:
        resp = requests.get(
            f"{TRADIER_BASE}/markets/options/chains",
            params={"symbol": symbol, "expiration": expiration, "greeks": "false"},
            headers=_tradier_headers(), timeout=10)
        if resp.status_code != 200:
            return []
        od = resp.json().get("options", {})
        if not od or od == "null":
            return []
        chain = od.get("option", [])
        return [chain] if isinstance(chain, dict) else (chain or [])
    except Exception:
        return []

def find_nearest_expiration(expirations: list[str], target_date: str) -> str | None:
    if not expirations:
        return None
    target = datetime.strptime(target_date, "%Y-%m-%d").date()
    best, best_diff = None, float("inf")
    for exp_str in expirations:
        try:
            diff = abs((datetime.strptime(exp_str, "%Y-%m-%d").date() - target).days)
            if diff < best_diff:
                best_diff, best = diff, exp_str
        except ValueError:
            continue
    return best if best_diff <= 3 else None


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 3 — OI SANDWICH ZONE ANALYSIS  ████
# ═══════════════════════════════════════════════════════════════════

def analyze_oi_sandwich(chain: list[dict], current_price: float) -> dict | None:
    """
    OI Sandwich Analysis — The Core Algorithm.

    Instead of individual "walls," we compute:
    1. Call Centroid — OI-weighted average strike of calls = ceiling pressure
    2. Put Centroid  — OI-weighted average strike of puts  = floor pressure
    3. OI Gravity Center — combined OI-weighted midpoint = the pin
    4. Pin Zone — the [put_centroid, call_centroid] sandwich
    5. Overextension — how far price is outside the sandwich

    We also compute the OI density in "zones" around the price to show
    WHERE the mass is concentrated (matching Michael's mental model).
    """
    call_oi_all = defaultdict(int)
    put_oi_all = defaultdict(int)

    for opt in chain:
        strike = opt.get("strike")
        oi = opt.get("open_interest", 0) or 0
        opt_type = opt.get("option_type", "").lower()
        if strike is None or oi <= 0:
            continue
        if opt_type == "call":
            call_oi_all[strike] += oi
        elif opt_type == "put":
            put_oi_all[strike] += oi

    if not call_oi_all and not put_oi_all:
        return None

    total_call_oi = sum(call_oi_all.values())
    total_put_oi = sum(put_oi_all.values())

    if total_call_oi == 0 and total_put_oi == 0:
        return None

    # ── Filter to Near-the-Money (NTM) strikes ──
    # Far-OTM lottery tickets distort centroids. Only use strikes within
    # ±15% of current price for the sandwich zone calculation.
    # This focuses on where the REAL hedging action is.
    ntm_range = current_price * 0.15
    ntm_low = current_price - ntm_range
    ntm_high = current_price + ntm_range

    call_oi = {k: v for k, v in call_oi_all.items() if ntm_low <= k <= ntm_high}
    put_oi = {k: v for k, v in put_oi_all.items() if ntm_low <= k <= ntm_high}

    # Fall back to all strikes if NTM filter is too aggressive
    ntm_call_oi = sum(call_oi.values())
    ntm_put_oi = sum(put_oi.values())
    if ntm_call_oi < total_call_oi * 0.1:
        call_oi = dict(call_oi_all)
        ntm_call_oi = total_call_oi
    if ntm_put_oi < total_put_oi * 0.1:
        put_oi = dict(put_oi_all)
        ntm_put_oi = total_put_oi

    # ── Centroids (NTM-filtered) ──
    # OI-weighted average strike for calls and puts separately.
    # This gives us the center of mass for each side near the money.
    call_centroid = (sum(k * v for k, v in call_oi.items()) / ntm_call_oi
                     if ntm_call_oi > 0 else current_price)
    put_centroid = (sum(k * v for k, v in put_oi.items()) / ntm_put_oi
                    if ntm_put_oi > 0 else current_price)

    # The sandwich zone: [floor, ceiling]
    sandwich_floor = min(put_centroid, call_centroid)
    sandwich_ceiling = max(put_centroid, call_centroid)
    sandwich_width = sandwich_ceiling - sandwich_floor
    sandwich_width_pct = (sandwich_width / current_price * 100) if current_price > 0 else 0

    # ── Overall gravity center (NTM-filtered) ──
    ntm_total = ntm_call_oi + ntm_put_oi
    gravity = ((sum(k * v for k, v in call_oi.items()) +
                sum(k * v for k, v in put_oi.items())) / ntm_total
               if ntm_total > 0 else current_price)

    # Keep full-chain totals for reporting
    total_oi = total_call_oi + total_put_oi

    # ── Overextension ──
    # How far is price outside the sandwich?
    if current_price > sandwich_ceiling:
        overext = current_price - sandwich_ceiling
        overext_pct = overext / current_price * 100
        overext_dir = "ABOVE"  # price above ceiling → expect pull DOWN
    elif current_price < sandwich_floor:
        overext = sandwich_floor - current_price
        overext_pct = overext / current_price * 100
        overext_dir = "BELOW"  # price below floor → expect pull UP
    else:
        overext = 0.0
        overext_pct = 0.0
        overext_dir = "PINNED"  # inside sandwich → already in gravity well

    # ── Distance from gravity center ──
    grav_dist = current_price - gravity
    grav_dist_pct = abs(grav_dist) / current_price * 100 if current_price > 0 else 0
    grav_dir = "ABOVE" if grav_dist > 0 else "BELOW"

    # ── Max Pain (uses FULL chain, not NTM-filtered) ──
    all_strikes = sorted(set(list(call_oi_all.keys()) + list(put_oi_all.keys())))
    strike_pain = {}
    for sp in all_strikes:
        pain = 0.0
        for k, oi in call_oi_all.items():
            pain += max(sp - k, 0) * oi * 100
        for k, oi in put_oi_all.items():
            pain += max(k - sp, 0) * oi * 100
        strike_pain[sp] = pain
    max_pain = min(strike_pain, key=strike_pain.get) if strike_pain else current_price

    # ── Strike-by-strike OI breakdown (FULL chain for display) ──
    combined_oi = defaultdict(int)
    for k, v in call_oi_all.items():
        combined_oi[k] += v
    for k, v in put_oi_all.items():
        combined_oi[k] += v

    # Find top NTM strikes by combined OI (within ±20% for wall display)
    ntm_display_low = current_price * 0.80
    ntm_display_high = current_price * 1.20
    ntm_combined = {k: v for k, v in combined_oi.items()
                    if ntm_display_low <= k <= ntm_display_high}
    sorted_combined = sorted(ntm_combined.items(), key=lambda x: x[1], reverse=True)

    # Wall summary: show as ↓C$200(15K) | ↑P$200(24K) format
    wall_parts = []
    for strike, _ in sorted_combined[:6]:
        c = call_oi_all.get(strike, 0)
        p = put_oi_all.get(strike, 0)
        direction = "↑" if strike > current_price else "↓"
        if c >= p and c > 0:
            wall_parts.append(f"{direction}C${strike:g}({_fmt_oi_raw(c)})")
        elif p > 0:
            wall_parts.append(f"{direction}P${strike:g}({_fmt_oi_raw(p)})")

    # ── OI Distribution: what % of NTM OI sits in the sandwich ──
    oi_in_zone = 0
    for k, v in call_oi.items():
        if sandwich_floor <= k <= sandwich_ceiling:
            oi_in_zone += v
    for k, v in put_oi.items():
        if sandwich_floor <= k <= sandwich_ceiling:
            oi_in_zone += v
    zone_concentration = (oi_in_zone / ntm_total * 100) if ntm_total > 0 else 0

    pcr = total_put_oi / total_call_oi if total_call_oi > 0 else 0

    return {
        # Sandwich zone
        "sandwich_floor": round(sandwich_floor, 2),
        "sandwich_ceiling": round(sandwich_ceiling, 2),
        "sandwich_width": round(sandwich_width, 2),
        "sandwich_width_pct": round(sandwich_width_pct, 1),
        "zone_concentration": round(zone_concentration, 1),
        # Centroids
        "call_centroid": round(call_centroid, 2),
        "put_centroid": round(put_centroid, 2),
        # Gravity
        "gravity": round(gravity, 2),
        "grav_dist_pct": round(grav_dist_pct, 2),
        "grav_dir": grav_dir,
        # Overextension (THE key metric)
        "overext_pct": round(overext_pct, 2),
        "overext_dir": overext_dir,
        "overext_dollars": round(overext, 2),
        # Max pain
        "max_pain": max_pain,
        # Wall structure
        "wall_summary": " | ".join(wall_parts),
        "top_strikes": sorted_combined[:10],
        # Totals
        "total_call_oi": total_call_oi,
        "total_put_oi": total_put_oi,
        "total_oi": total_oi,
        "put_call_ratio": round(pcr, 2),
    }


def _fmt_oi_raw(n: int) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{n/1_000:.0f}K"
    return str(n)


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 4 — SCANNING + RANKING  ████
# ═══════════════════════════════════════════════════════════════════

def scan_ticker(ticker: str, price: float, target_expiry: str,
                tv_data: dict = None) -> dict | None:
    expirations = get_options_expirations(ticker)
    if not expirations:
        return None

    exp_date = find_nearest_expiration(expirations, target_expiry)
    if not exp_date:
        return None

    chain = get_options_chain(ticker, exp_date)
    if not chain:
        return None

    gamma = analyze_oi_sandwich(chain, price)
    if not gamma:
        return None

    atr = (tv_data or {}).get("atr", 0)
    atr_overext = gamma["overext_dollars"] / atr if atr and atr > 0 else 0

    # ── Snap Score ──
    # Combines multiple factors that predict actual OpEx day movement:
    #   1. Overextension % (primary — how far outside the sandwich)
    #   2. OI concentration (higher = stronger gravitational pull)
    #   3. ATR-normalized overextension (accounts for how much the stock normally moves)
    #   4. Total OI magnitude (more OI = bigger gamma effect = stronger pin)
    #
    # A stock with 5% overextension + massive OI + tight sandwich
    # is a much better play than one with 10% overextension + thin OI.
    oi_score = min(math.log10(gamma["total_oi"] + 1), 6) / 6  # 0-1, log-scaled
    concentration_score = gamma["zone_concentration"] / 100     # 0-1
    overext_score = min(gamma["overext_pct"] / 15, 1.0)        # 0-1, capped at 15%

    snap_score = (
        overext_score * 0.40 +          # Distance outside sandwich
        oi_score * 0.25 +               # OI magnitude (gamma impact)
        concentration_score * 0.20 +    # How tight the sandwich is
        min(atr_overext / 5, 1.0) * 0.15  # ATR-normalized stretch
    ) * 100

    return {
        "ticker": ticker,
        "name": (tv_data or {}).get("name", ticker),
        "price": round(price, 2),
        # Sandwich
        "sandwich_floor": gamma["sandwich_floor"],
        "sandwich_ceiling": gamma["sandwich_ceiling"],
        "sandwich_width_pct": gamma["sandwich_width_pct"],
        "zone_concentration": gamma["zone_concentration"],
        # Gravity
        "gravity": gamma["gravity"],
        "grav_dist_pct": gamma["grav_dist_pct"],
        "grav_dir": gamma["grav_dir"],
        # Overextension
        "overext_pct": gamma["overext_pct"],
        "overext_dir": gamma["overext_dir"],
        "overext_dollars": gamma["overext_dollars"],
        # Snap Score
        "snap_score": round(snap_score, 1),
        # Max pain
        "max_pain": gamma["max_pain"],
        # Walls
        "wall_summary": gamma["wall_summary"],
        "top_strikes": gamma["top_strikes"],
        # Totals
        "total_call_oi": gamma["total_call_oi"],
        "total_put_oi": gamma["total_put_oi"],
        "total_oi": gamma["total_oi"],
        "put_call_ratio": gamma["put_call_ratio"],
        # ATR
        "atr": round(atr, 2) if atr else None,
        "atr_overext": round(atr_overext, 1),
        # Meta
        "expiration": exp_date,
        "sector": (tv_data or {}).get("sector", ""),
        "change_pct": round((tv_data or {}).get("change_pct", 0), 2),
        "market_cap": (tv_data or {}).get("market_cap", 0),
        "avg_vol": (tv_data or {}).get("avg_vol_30d", 0),
    }


# ═══════════════════════════════════════════════════════════════════
# ████  OUTPUT FORMATTING  ████
# ═══════════════════════════════════════════════════════════════════

R = "\033[0m"
RED = "\033[91m"
GRN = "\033[92m"
YLW = "\033[93m"
BLU = "\033[94m"
CYN = "\033[96m"
MAG = "\033[95m"
GRY = "\033[90m"
BLD = "\033[1m"
WHT = "\033[97m"

def _fmt_oi(n: int) -> str:
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
    elif n >= 1_000: return f"{n/1_000:.0f}K"
    return str(n)

def _fmt_cap(n: float) -> str:
    if n >= 1e12: return f"${n/1e12:.1f}T"
    elif n >= 1e9: return f"${n/1e9:.0f}B"
    elif n >= 1e6: return f"${n/1e6:.0f}M"
    return f"${n:,.0f}"

def _fmt_s(s) -> str:
    """Format strike – no decimals if whole."""
    if s is None: return "—"
    if s == int(s): return f"${int(s)}"
    return f"${s:.2f}"

def _snap_color(score: float) -> str:
    if score >= 50: return CYN + BLD
    elif score >= 35: return CYN
    elif score >= 25: return YLW
    return WHT


def print_results(results: list[dict], scan_stats: dict):
    """Print sandwich-based scanner output."""
    # Split into overextended (outside sandwich) and pinned (inside)
    overextended = [r for r in results if r["overext_dir"] != "PINNED"]
    pinned = [r for r in results if r["overext_dir"] == "PINNED"]

    print(f"\n{'═'*100}")
    print(f"  {CYN}{BLD}👻 GAMMA PIN SCREENER v3{R} — OI Sandwich Finder")
    print(f"  {GRY}OpEx: {scan_stats.get('target_expiry', '?')} | "
          f"Scanned: {scan_stats.get('scanned', 0)} | "
          f"Overextended: {len(overextended)} | "
          f"Pinned: {len(pinned)} | "
          f"Time: {scan_stats.get('elapsed', 0):.0f}s{R}")
    print(f"{'═'*100}")

    if not results:
        print(f"\n  {RED}💀 No gamma data found.{R}\n")
        return

    # ── RUBBER BANDS — stocks OUTSIDE the sandwich ──
    if overextended:
        print(f"\n  {BLD}{CYN}🔥 RUBBER BANDS{R} — Price OUTSIDE the OI Sandwich (overextended)")
        print(f"  {GRY}These have room to move. The sandwich pulls them back on OpEx.{R}\n")
        print(f"  {BLD}{'#':>3}  {'TICKER':<7} {'PRICE':>8} "
              f"{'FLOOR':>8} {'CEIL':>8} {'GRAVITY':>8} "
              f"{'OVER%':>6} {'DIR':>5} {'SNAP':>5} "
              f"{'PCR':>5} {'OI':>7} {'CAP':>7}{R}")
        print(f"  {'─'*95}")

        for i, r in enumerate(overextended, 1):
            sc = _snap_color(r["snap_score"])
            dir_c = RED if r["overext_dir"] == "ABOVE" else GRN
            dir_arrow = "▼" if r["overext_dir"] == "ABOVE" else "▲"

            pcr = r["put_call_ratio"]
            pcr_c = RED if pcr > 1.5 else YLW if pcr > 1.0 else GRN if pcr < 0.5 else WHT
            cap = _fmt_cap(r["market_cap"]) if r["market_cap"] else ""

            print(f"  {sc}{i:>3}{R}  {BLD}{r['ticker']:<7}{R}"
                  f"${r['price']:>7.2f} "
                  f"{GRN}{_fmt_s(r['sandwich_floor']):>8}{R} "
                  f"{RED}{_fmt_s(r['sandwich_ceiling']):>8}{R} "
                  f"{YLW}{_fmt_s(r['gravity']):>8}{R} "
                  f"{dir_c}{r['overext_pct']:>5.1f}%{dir_arrow}{R}"
                  f"{sc}{r['snap_score']:>5.0f}{R} "
                  f"{pcr_c}{pcr:>5.2f}{R} "
                  f"{_fmt_oi(r['total_oi']):>7} "
                  f"{GRY}{cap:>7}{R}")

            # Detail line
            if i <= 20:
                chg = r.get("change_pct", 0)
                chg_c = GRN if chg > 0 else RED if chg < 0 else WHT
                name = r["name"][:28]
                ws = r.get("wall_summary", "")
                atr_s = f"ATR×{r['atr_overext']:.1f}" if r.get("atr_overext") else ""
                conc = f"Zone:{r['zone_concentration']:.0f}%OI"

                print(f"       {GRY}{name} | {chg_c}{chg:+.1f}%{R} "
                      f"{GRY}| {conc} | {atr_s} | MaxPain:{_fmt_s(r['max_pain'])}{R}")
                print(f"       {GRY}{ws}{R}")

    # ── PINNED — stocks INSIDE the sandwich (for reference) ──
    if pinned and scan_stats.get("show_pinned", True):
        print(f"\n  {GRY}{'─'*95}{R}")
        print(f"  {GRY}{BLD}📌 PINNED{R} {GRY}— Price INSIDE the sandwich (low movement expected){R}\n")
        print(f"  {GRY}{'#':>3}  {'TICKER':<7} {'PRICE':>8} "
              f"{'FLOOR':>8} {'CEIL':>8} {'GRAVITY':>8} "
              f"{'→GRAV%':>7} {'W%':>5} {'SNAP':>5} "
              f"{'PCR':>5} {'OI':>7}{R}")
        print(f"  {GRY}{'─'*95}{R}")

        # Sort pinned by distance to gravity (interesting ones first)
        pinned_sorted = sorted(pinned, key=lambda r: r["grav_dist_pct"], reverse=True)
        for i, r in enumerate(pinned_sorted[:10], 1):
            pcr = r["put_call_ratio"]
            pcr_c = RED if pcr > 1.5 else YLW if pcr > 1.0 else GRN if pcr < 0.5 else GRY
            grav_c = YLW if r["grav_dist_pct"] > 2 else GRY

            print(f"  {GRY}{i:>3}  {r['ticker']:<7}"
                  f"${r['price']:>7.2f} "
                  f"{_fmt_s(r['sandwich_floor']):>8} "
                  f"{_fmt_s(r['sandwich_ceiling']):>8} "
                  f"{_fmt_s(r['gravity']):>8} "
                  f"{grav_c}{r['grav_dist_pct']:>6.1f}%{R}{GRY} "
                  f"{r['sandwich_width_pct']:>4.1f}% "
                  f"{r['snap_score']:>4.0f} "
                  f"{pcr_c}{pcr:>5.2f}{R}{GRY} "
                  f"{_fmt_oi(r['total_oi']):>7}{R}")

    # ── Summary ──
    print(f"\n  {'─'*95}")
    print(f"  {BLD}📊 Summary:{R}")
    print(f"     Overextended (rubber bands): {CYN}{BLD}{len(overextended)}{R}")
    print(f"     Pinned (inside sandwich):    {GRY}{len(pinned)}{R}")

    if overextended:
        above = [r for r in overextended if r["overext_dir"] == "ABOVE"]
        below = [r for r in overextended if r["overext_dir"] == "BELOW"]
        avg_oe = sum(r["overext_pct"] for r in overextended) / len(overextended)
        print(f"     Avg overextension: {avg_oe:.1f}%")

        if above:
            top = sorted(above, key=lambda x: x["snap_score"], reverse=True)[:3]
            names = ", ".join(f"{r['ticker']}({r['overext_pct']:.1f}%▼)" for r in top)
            print(f"     {RED}▼ Best shorts (above sandwich):{R} {names}")

        if below:
            top = sorted(below, key=lambda x: x["snap_score"], reverse=True)[:3]
            names = ", ".join(f"{r['ticker']}({r['overext_pct']:.1f}%▲)" for r in top)
            print(f"     {GRN}▲ Best longs (below sandwich):{R}  {names}")

    print(f"\n{'═'*100}")
    print(f"  {GRY}👻 Sam says: \"The sandwich always wins. Price runs, but OI is gravity.\"{R}")
    print(f"  {GRY}   FLOOR = put centroid | CEILING = call centroid | GRAVITY = combined center{R}")
    print(f"  {GRY}   SNAP = composite score (overextension × OI mass × zone tightness × ATR){R}\n")


def output_json(results: list[dict], scan_stats: dict):
    clean = []
    for r in results:
        cr = {k: v for k, v in r.items() if k not in ("top_strikes",)}
        cr["top_strikes"] = [(s, oi) for s, oi in r.get("top_strikes", [])]
        clean.append(cr)
    output = {
        "scan_date": datetime.now().isoformat(),
        "scan_stats": scan_stats,
        "total": len(clean),
        "overextended": [r for r in clean if r["overext_dir"] != "PINNED"],
        "pinned": [r for r in clean if r["overext_dir"] == "PINNED"],
        "results": clean,
    }
    print(json.dumps(output, indent=2, default=str))


# ═══════════════════════════════════════════════════════════════════
# ████  CLI MAIN  ████
# ═══════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="👻 Gamma Pin Screener v3 — OI Sandwich Finder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--tickers", type=str,
                        help="Comma-separated tickers (skip TV scan)")
    parser.add_argument("--expiry", type=str, default="2026-03-20",
                        help="Target expiration YYYY-MM-DD (default: 2026-03-20)")
    parser.add_argument("--top", type=int, default=30,
                        help="Show top N results (default: 30)")
    parser.add_argument("--min-oi", type=int, default=500,
                        help="Min total OI to include (default: 500)")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--max-stocks", type=int, default=200,
                        help="Max stocks to scan (default: 200)")
    parser.add_argument("--sort", type=str, default="snap",
                        choices=["snap", "overext", "gravity"],
                        help="Sort: snap (composite), overext (distance), gravity (from center)")
    parser.add_argument("--all", action="store_true",
                        help="Show all results (including pinned in detail)")
    args = parser.parse_args()

    t0 = time.time()
    target_expiry = args.expiry

    print(f"\n  {CYN}{BLD}👻 GAMMA PIN SCREENER v3{R} — OI Sandwich Finder")
    print(f"  {GRY}Target OpEx: {target_expiry} | Sort: {args.sort}{R}\n")

    # ── Stage 1: Stock universe ──
    if args.tickers:
        tickers_raw = [t.strip().upper() for t in args.tickers.split(",")]
        print(f"  ⚡ Direct scan: {len(tickers_raw)} tickers")

        tv_lookup = {}
        try:
            resp = requests.get(
                f"{TRADIER_BASE}/markets/quotes",
                params={"symbols": ",".join(tickers_raw)},
                headers=_tradier_headers(), timeout=10)
            if resp.status_code == 200:
                quotes = resp.json().get("quotes", {}).get("quote", [])
                if isinstance(quotes, dict): quotes = [quotes]
                for q in quotes:
                    sym = q.get("symbol", "")
                    tv_lookup[sym] = {
                        "ticker": sym, "name": q.get("description", sym),
                        "price": float(q.get("last") or q.get("close", 0)),
                        "change_pct": float(q.get("change_percentage", 0)),
                        "volume": int(q.get("volume", 0)),
                        "avg_vol_30d": int(q.get("average_volume", 0)),
                        "market_cap": 0, "atr": 0, "adx": 0, "sector": "",
                    }
        except Exception as e:
            print(f"  {RED}⚠ Quote error: {e}{R}")

        tickers_to_scan = [(t, tv_lookup.get(t, {}).get("price", 0), tv_lookup.get(t))
                           for t in tickers_raw if tv_lookup.get(t, {}).get("price", 0) > 0]
    else:
        print(f"  ⚡ Stage 1: TradingView bulk scan...")
        stocks = tv_fetch_stocks()
        print(f"     → {len(stocks)} liquid US stocks loaded")
        stocks.sort(key=lambda s: s["avg_vol_30d"], reverse=True)
        scan_list = stocks[:args.max_stocks]
        print(f"     → Scanning top {len(scan_list)} by volume\n")
        tickers_to_scan = [(s["ticker"], s["price"], s) for s in scan_list]

    # ── Stage 2+3: Options scan ──
    print(f"  🔍 Stage 2: Scanning options chains...")
    results = []
    skipped = 0

    for i, (ticker, price, tv_data) in enumerate(tickers_to_scan):
        pct = (i + 1) / len(tickers_to_scan) * 100
        print(f"\r     [{i+1}/{len(tickers_to_scan)}] {ticker:<6} ({pct:.0f}%)", end="", flush=True)

        result = scan_ticker(ticker, price, target_expiry, tv_data)
        if result and (result["total_oi"] >= args.min_oi):
            results.append(result)
        else:
            skipped += 1

        if (i + 1) % 30 == 0 and i + 1 < len(tickers_to_scan):
            time.sleep(1.0)

    print(f"\r     ✅ {len(results)} stocks analyzed ({skipped} skipped)" + " " * 20)

    elapsed = time.time() - t0
    scan_stats = {
        "target_expiry": target_expiry,
        "scanned": len(tickers_to_scan),
        "valid": len(results),
        "skipped": skipped,
        "elapsed": elapsed,
        "sort": args.sort,
        "show_pinned": args.all or (args.tickers is not None),
    }

    if not results:
        print(f"\n  {RED}❌ No data. Check expiry date.{R}\n")
        return

    # ── Stage 4: Sort ──
    if args.sort == "snap":
        results.sort(key=lambda r: r["snap_score"], reverse=True)
    elif args.sort == "overext":
        results.sort(key=lambda r: r["overext_pct"], reverse=True)
    elif args.sort == "gravity":
        results.sort(key=lambda r: r["grav_dist_pct"], reverse=True)

    results = results[:args.top]

    print(f"\n  ⏱  Total time: {elapsed:.1f}s")

    if args.json:
        output_json(results, scan_stats)
    else:
        print_results(results, scan_stats)

    # Save API output
    out_path = Path(__file__).resolve().parent.parent / "docs" / "api" / "gamma-pin-scan.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    clean = []
    for r in results[:50]:
        cr = {k: v for k, v in r.items() if k not in ("top_strikes",)}
        cr["top_strikes"] = [(s, oi) for s, oi in r.get("top_strikes", [])]
        clean.append(cr)
    api_output = {"scan_date": datetime.now().isoformat(), "target_expiry": target_expiry, "results": clean}
    out_path.write_text(json.dumps(api_output, indent=2, default=str))
    print(f"  {GRY}💾 Saved to {out_path}{R}\n")


if __name__ == "__main__":
    main()
