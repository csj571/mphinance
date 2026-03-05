"""
Daily Momentum Picks — Gold 🥇, Silver 🥈, Bronze 🥉

Ranks ALL dossier tickers by a momentum-specific composite score
and returns the top 3. Unlike the general grade (A/B/C/D) which
blends technical + fundamental, this is PURE momentum:

Scoring factors (max 100):
  EMA Stack alignment:   25 pts  (FULL BULL=25, PARTIAL BULL=15, TANGLED=5)
  Trend direction:       15 pts  (Bullish=15, Bearish=0)
  RSI sweet spot:        15 pts  (40-65 = max, <30 or >70 = low)
  ADX trend strength:    15 pts  (>25 = trending, >40 = strong trend)
  Relative Volume:       10 pts  (>1.5x = high interest)
  Price vs EMA 21:       10 pts  (within 2% above = perfect pullback)
  Price change today:     5 pts  (positive movement)
  Institutional signal:   5 pts  (buying = bonus)
"""

import json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PICKS_FILE = PROJECT_ROOT / "docs" / "backtesting" / "daily_picks.json"


def _clamp(val, lo=0, hi=100):
    return max(lo, min(hi, val))


def score_momentum(payload: dict) -> dict:
    """Score a single ticker on pure momentum factors. Returns dict with score breakdown."""
    ta = payload.get("technical_analysis", {})
    osc = ta.get("oscillators", {})
    vol = ta.get("volume", {})
    scores_data = payload.get("scores", {})
    tt = payload.get("tickertrace", {})
    sig = tt.get("signal", {}) or {}

    price = payload.get("currentPrice", 0)
    change_pct = payload.get("priceChangePct", 0)
    ema_stack = ta.get("ema_stack", "UNKNOWN")
    trend = payload.get("trendOverall", "")
    rsi = float(osc.get("rsi_14") or 50)
    adx = float(osc.get("adx_14") or 0)
    rel_vol = float(vol.get("rel_vol") or 1.0)

    # EMA values for price-vs-EMA calc
    ema_21 = ta.get("ema", {}).get("21")

    breakdown = {}

    # 1. EMA Stack (25 pts)
    ema_pts = {"FULL BULLISH": 25, "PARTIAL BULLISH": 15, "TANGLED": 5,
               "PARTIAL BEARISH": 2, "FULL BEARISH": 0, "UNKNOWN": 5}
    breakdown["ema_stack"] = ema_pts.get(ema_stack, 5)

    # 2. Trend direction (15 pts)
    breakdown["trend"] = 15 if "Bullish" in trend else 0

    # 3. RSI sweet spot (15 pts) — momentum traders want 40-65 zone
    if 40 <= rsi <= 65:
        breakdown["rsi"] = 15
    elif 30 <= rsi < 40 or 65 < rsi <= 70:
        breakdown["rsi"] = 10
    elif rsi < 30:
        breakdown["rsi"] = 5   # oversold could bounce but risky
    else:
        breakdown["rsi"] = 2   # overbought >70

    # 4. ADX strength (15 pts)
    if adx >= 40:
        breakdown["adx"] = 15
    elif adx >= 30:
        breakdown["adx"] = 12
    elif adx >= 25:
        breakdown["adx"] = 8
    elif adx >= 15:
        breakdown["adx"] = 4
    else:
        breakdown["adx"] = 0

    # 5. Relative Volume (10 pts)
    if rel_vol >= 2.0:
        breakdown["rel_vol"] = 10
    elif rel_vol >= 1.5:
        breakdown["rel_vol"] = 8
    elif rel_vol >= 1.0:
        breakdown["rel_vol"] = 5
    else:
        breakdown["rel_vol"] = 2

    # 6. Price vs EMA 21 (10 pts) — want to be just above (pullback entry)
    if ema_21 and price:
        pct_from_ema = ((price - float(ema_21)) / float(ema_21)) * 100
        if 0 <= pct_from_ema <= 2:
            breakdown["price_vs_ema"] = 10  # Perfect pullback zone
        elif 0 <= pct_from_ema <= 5:
            breakdown["price_vs_ema"] = 7   # Healthy above
        elif pct_from_ema > 5:
            breakdown["price_vs_ema"] = 3   # Extended
        elif -2 <= pct_from_ema < 0:
            breakdown["price_vs_ema"] = 6   # Testing support
        else:
            breakdown["price_vs_ema"] = 1   # Below EMA 21
    else:
        breakdown["price_vs_ema"] = 5

    # 7. Today's price change (5 pts)
    if change_pct >= 3:
        breakdown["momentum"] = 5
    elif change_pct >= 1:
        breakdown["momentum"] = 4
    elif change_pct >= 0:
        breakdown["momentum"] = 2
    else:
        breakdown["momentum"] = 0

    # 8. Institutional signal (5 pts)
    direction = (sig.get("direction") or "").upper()
    breakdown["institutional"] = 5 if "BUY" in direction else 0

    total = sum(breakdown.values())

    return {
        "ticker": payload.get("ticker", ""),
        "score": total,
        "breakdown": breakdown,
        "price": price,
        "change_pct": change_pct,
        "grade": scores_data.get("grade", ""),
        "tech_score": scores_data.get("technical", 0),
        "ema_stack": ema_stack,
        "trend": trend,
        "rsi": round(rsi, 1),
        "adx": round(adx, 1),
        "rel_vol": round(rel_vol, 2),
    }


def pick_daily_momentum(ticker_payloads: list[dict], date: str) -> dict:
    """
    Rank all tickers and return Gold 🥇, Silver 🥈, Bronze 🥉 picks.

    Args:
        ticker_payloads: List of full ticker payload dicts (from enrichment)
        date: Report date string

    Returns:
        Dict with 'picks' (top 3), 'all_ranked' (full list), 'date'
    """
    scored = []
    for payload in ticker_payloads:
        try:
            result = score_momentum(payload)
            if result["ticker"]:
                scored.append(result)
        except Exception as e:
            print(f"    [WARN] Momentum scoring failed for {payload.get('ticker', '?')}: {e}")

    # Sort by momentum score descending
    scored.sort(key=lambda x: x["score"], reverse=True)

    # Assign medals
    medals = ["🥇 GOLD", "🥈 SILVER", "🥉 BRONZE"]
    picks = []
    for i, s in enumerate(scored[:3]):
        s["medal"] = medals[i]
        s["rank"] = i + 1
        picks.append(s)

    result = {
        "date": date,
        "picks": picks,
        "all_ranked": scored,
    }

    # Persist daily picks
    _save_picks(result, date)

    return result


def _save_picks(result: dict, date: str):
    """Append today's picks to the rolling picks file."""
    try:
        PICKS_FILE.parent.mkdir(parents=True, exist_ok=True)

        history = []
        if PICKS_FILE.exists():
            with open(PICKS_FILE) as f:
                history = json.load(f)

        # Remove existing entry for this date
        history = [h for h in history if h.get("date") != date]

        # Add today's picks (compact version)
        compact = {
            "date": date,
            "gold": {"ticker": result["picks"][0]["ticker"], "score": result["picks"][0]["score"]} if len(result["picks"]) > 0 else None,
            "silver": {"ticker": result["picks"][1]["ticker"], "score": result["picks"][1]["score"]} if len(result["picks"]) > 1 else None,
            "bronze": {"ticker": result["picks"][2]["ticker"], "score": result["picks"][2]["score"]} if len(result["picks"]) > 2 else None,
        }
        history.append(compact)

        # Keep last 90 days
        history = history[-90:]

        with open(PICKS_FILE, "w") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"    [WARN] Daily picks save failed: {e}")


def format_picks_text(picks_data: dict) -> str:
    """Format picks as plain text for report inclusion."""
    if not picks_data or not picks_data.get("picks"):
        return "No momentum picks today."

    lines = ["DAILY MOMENTUM PICKS", "=" * 40]
    for p in picks_data["picks"]:
        lines.append(
            f"{p['medal']}: {p['ticker']} "
            f"(Score: {p['score']}/100, "
            f"Grade: {p['grade']}, "
            f"{p['ema_stack']}, "
            f"RSI: {p['rsi']}, "
            f"${p['price']:.2f} [{p['change_pct']:+.1f}%])"
        )
    return "\n".join(lines)
