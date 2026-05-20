#!/usr/bin/env python3
"""Miners Wheel CSP Scanner — scans all miners from miners_wheel_list.md
for cash-secured put opportunities expiring 2026-05-29.

For each ticker:
1. Get current price
2. Check if 2026-05-29 expiration exists
3. Get the put chain
4. Find the strike just below current price
5. Get the bid (premium)
6. Calculate weekly RoC and annualized RoC
"""

import json
import time
from pathlib import Path

import httpx

# Tradier API config
API_BASE = "https://api.tradier.com/v1"
API_KEY = "GjMYgAD4ADrGxI78HVhJMjZMWSIU"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json",
}

TARGET_EXP = "2026-05-29"
DAYS_TO_EXP = 9  # May 20 (Wed) to May 29 (Thu)

TICKERS = [
    "NEM", "AEM", "WPM", "AU", "FNV", "GFI", "KGC", "PAAS", "RGLD", "CDE",
    "AGI", "HL", "HMY", "EQX", "IAG", "AG", "BVN", "EGO", "OR", "OGC",
    "TFPM", "BTG", "SSRM", "SKE", "ARIS", "NG", "PPTA", "SA", "TXG", "FSM",
    "SVM", "EXK", "DRD", "USAS", "MUX", "GOLD", "ASM", "VZLA", "ASA", "NFGC", "MTA",
]


def api_get(path: str, params: dict = None) -> dict | None:
    try:
        with httpx.Client(timeout=15.0) as c:
            r = c.get(f"{API_BASE}{path}", headers=HEADERS, params=params or {})
        if r.status_code == 200:
            return r.json()
        print(f"  [WARN] {path} -> HTTP {r.status_code}")
        return None
    except Exception as e:
        print(f"  [ERR] {path}: {e}")
        return None


def batch_quotes(symbols: list[str]) -> dict:
    """Get batch quotes for multiple symbols in one call."""
    data = api_get("/markets/quotes", {"symbols": ",".join(symbols)})
    if not data:
        return {}
    quotes = (data.get("quotes") or {}).get("quote") or []
    if isinstance(quotes, dict):
        quotes = [quotes]
    return {q["symbol"]: q for q in quotes if q and isinstance(q, dict)}


def list_expirations(symbol: str) -> list[str]:
    data = api_get("/markets/options/expirations",
                   {"symbol": symbol, "includeAllRoots": "true", "strikes": "false"})
    if not data:
        return []
    exps = (data.get("expirations") or {}).get("date") or []
    if isinstance(exps, str):
        return [exps]
    return exps


def get_chain(symbol: str, expiry: str) -> list[dict]:
    data = api_get("/markets/options/chains",
                   {"symbol": symbol, "expiration": expiry, "greeks": "true"})
    if not data:
        return []
    opts = (data.get("options") or {}).get("option") or []
    if isinstance(opts, dict):
        return [opts]
    return opts


def scan():
    print(f"🔍 Miners Wheel CSP Scanner")
    print(f"   Target Expiration: {TARGET_EXP} ({DAYS_TO_EXP} calendar days)")
    print(f"   Tickers: {len(TICKERS)}")
    print()

    # Batch quotes for all tickers
    print("📊 Fetching quotes...")
    quotes = batch_quotes(TICKERS)
    print(f"   Got {len(quotes)} quotes")
    print()

    results = []
    skipped = []

    for i, ticker in enumerate(TICKERS):
        q = quotes.get(ticker)
        if not q:
            skipped.append((ticker, "no quote data"))
            continue

        price = q.get("last") or q.get("close")
        if not price or float(price) <= 0:
            skipped.append((ticker, "no price"))
            continue
        price = float(price)

        # Check expirations
        exps = list_expirations(ticker)
        if TARGET_EXP not in exps:
            # Show nearest alternatives
            close_exps = [e for e in exps if e >= "2026-05-23" and e <= "2026-06-05"]
            alt = ", ".join(close_exps[:3]) if close_exps else "none near"
            skipped.append((ticker, f"no {TARGET_EXP} exp (near: {alt})"))
            time.sleep(0.1)
            continue

        # Get put chain
        chain = get_chain(ticker, TARGET_EXP)
        if not chain:
            skipped.append((ticker, "empty chain"))
            time.sleep(0.1)
            continue

        # Filter puts only
        puts = [c for c in chain if c.get("option_type") == "put"]
        if not puts:
            skipped.append((ticker, "no puts in chain"))
            time.sleep(0.1)
            continue

        # Find strike just below current price
        strikes_below = [p for p in puts if float(p.get("strike", 0)) <= price]
        if not strikes_below:
            skipped.append((ticker, f"no strike <= ${price:.2f}"))
            time.sleep(0.1)
            continue

        # Get the highest strike still at or below price (1 strike OTM)
        best_put = max(strikes_below, key=lambda p: float(p.get("strike", 0)))

        strike = float(best_put.get("strike", 0))
        bid = float(best_put.get("bid", 0) or 0)
        ask = float(best_put.get("ask", 0) or 0)
        mid = (bid + ask) / 2
        oi = int(best_put.get("open_interest", 0) or 0)
        volume = int(best_put.get("volume", 0) or 0)

        greeks = best_put.get("greeks") or {}
        delta = float(greeks.get("delta", 0) or 0)
        iv = float(greeks.get("mid_iv") or greeks.get("smv_vol") or 0)

        if bid <= 0:
            skipped.append((ticker, f"${strike:.0f} put bid=$0"))
            time.sleep(0.1)
            continue

        # Calculate RoC
        # Cash needed to secure put = strike * 100
        # Premium received = bid * 100
        # Weekly RoC = (bid / strike) * (7 / days_to_exp) * 100
        weekly_roc = (bid / strike) * (7 / DAYS_TO_EXP) * 100
        annual_roc = weekly_roc * 52
        otm_pct = (price - strike) / price * 100

        results.append({
            "ticker": ticker,
            "name": q.get("description", ""),
            "price": round(price, 2),
            "strike": strike,
            "bid": bid,
            "ask": ask,
            "mid": round(mid, 3),
            "oi": oi,
            "volume": volume,
            "delta": round(delta, 3) if delta else 0,
            "iv": round(iv * 100, 1) if iv and iv < 5 else round(iv, 1) if iv else 0,
            "weekly_roc": round(weekly_roc, 3),
            "annual_roc": round(annual_roc, 1),
            "otm_pct": round(otm_pct, 1),
            "cash_needed": int(strike * 100),
        })

        print(f"  ✓ {ticker:>6} ${price:>8.2f} -> ${strike:.2f}P bid=${bid:.2f} "
              f"wkRoC={weekly_roc:.2f}% ann={annual_roc:.0f}%")

        time.sleep(0.12)  # be kind to the API

    # Sort by annualized RoC
    results.sort(key=lambda r: r["annual_roc"], reverse=True)

    # Print summary
    print(f"\n{'='*95}")
    print(f"{'MINERS WHEEL CSP SCAN — ' + TARGET_EXP:^95}")
    print(f"{'='*95}")
    print(f"{'#':>3} {'Ticker':>6} {'Price':>8} {'Strike':>7} {'Bid':>6} {'OTM%':>6} "
          f"{'WkRoC':>7} {'Annual':>8} {'Delta':>7} {'IV%':>6} {'OI':>6} {'Cash':>7}")
    print(f"{'-'*95}")

    for i, r in enumerate(results, 1):
        print(f"{i:>3} {r['ticker']:>6} ${r['price']:>7.2f} ${r['strike']:>6.2f} "
              f"${r['bid']:>5.2f} {r['otm_pct']:>5.1f}% {r['weekly_roc']:>6.3f}% "
              f"{r['annual_roc']:>7.1f}% {r['delta']:>6.3f} {r['iv']:>5.1f}% "
              f"{r['oi']:>5} ${r['cash_needed']:>6}")

    print(f"\n📋 Results: {len(results)} tradeable | {len(skipped)} skipped")
    print("\nSkipped:")
    for t, reason in skipped:
        print(f"   ⊘ {t}: {reason}")

    # Save JSON
    output = {
        "scan_date": "2026-05-20",
        "target_expiration": TARGET_EXP,
        "days_to_expiration": DAYS_TO_EXP,
        "results": results,
        "skipped": [{"ticker": t, "reason": r} for t, r in skipped],
    }
    output_path = Path(__file__).parent.parent / "data" / "miners_csp_scan.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2))
    print(f"\n💾 Saved to {output_path}")

    return results


if __name__ == "__main__":
    scan()
