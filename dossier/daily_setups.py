"""
Daily Trading Setups — 3 Styles for Every Trader

Generates daily picks across three trading categories:

🥇 DAY TRADE (Breakout)
   - High ADX (>25), surge in relative volume (>1.5x)
   - Price breaking above key resistance or EMA stack
   - RSI accelerating (45-70), positive MACD histogram
   - Best for: Intraday momentum riders who want in/out same day

🥈 SWING TRADE (Momentum Pullback)
   - Full/partial bullish EMA stack
   - Pulling back to EMA 21 support (Bounce 2.0 pattern)
   - Stoch %K < 40 (oversold on the pullback), ADX > 25 (still trending)
   - Best for: 3-10 day holds catching the bounce

🥉 CSP (Cash-Secured Put / Wheel)
   - Strong underlying trend (EMA aligned)
   - Elevated IV relative to HV (vol premium exists)
   - VoPR grade A/B (premium worth selling)
   - Specific strike/expiry/premium from options chain analysis
   - Best for: Theta gang, premium sellers, wheel runners

Data sources:
   - Momentum scoring: dossier/momentum_picks.py
   - CSP scanning:     dossier/data_sources/csp_setups.py
   - VoPR overlay:     strategies/vopr_overlay.py

Output: docs/api/daily-setups.json (served via GH Pages)
"""

import json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def classify_setup_style(scored_pick: dict) -> str:
    """
    Classify a momentum-scored ticker into DAY TRADE vs SWING TRADE.

    Day Trade (Breakout):
      - High rel_vol (>1.3x) — volume surge signals institutional participation
      - Higher RSI (>50) — already moving, not waiting for bounce
      - Positive MACD — momentum accelerating NOW
      - Price above EMA 21 by >2% — already broken out, not pulling back

    Swing Trade (Pullback):
      - Near EMA 21 (within 3%) — sitting at support
      - Stoch %K < 50 — pulled back into oversold territory
      - Is a pullback setup (Bounce 2.0 pattern)
      - ADX > 25 — underlying trend still strong
    """
    bd = scored_pick.get("breakdown", {})

    # Pullback setups are definitively swing trades
    if scored_pick.get("is_pullback_setup"):
        return "swing"

    # High volume + already moving = breakout/day trade
    rel_vol = scored_pick.get("rel_vol", 1.0)
    rsi = scored_pick.get("rsi", 50)
    stoch_k = scored_pick.get("stoch_k", 50)
    macd_pts = bd.get("macd", 0)
    price_ema_pts = bd.get("price_vs_ema", 5)

    # Day trade signals: volume surge + already above EMA + RSI momentum
    day_trade_score = 0
    if rel_vol >= 1.5:
        day_trade_score += 3
    elif rel_vol >= 1.2:
        day_trade_score += 1
    if rsi >= 55:
        day_trade_score += 2
    if macd_pts >= 4:
        day_trade_score += 2
    if price_ema_pts <= 6:  # Extended above EMA = breakout territory
        day_trade_score += 1

    # Swing signals: pulled back + stoch oversold
    swing_score = 0
    if stoch_k < 45:
        swing_score += 3
    if price_ema_pts >= 8:  # Near EMA 21 support
        swing_score += 2
    if scored_pick.get("adx", 0) >= 25:
        swing_score += 1

    return "day_trade" if day_trade_score > swing_score else "swing"


def build_daily_setups(ticker_payloads: list[dict], date: str,
                       csp_data: list[dict] | None = None) -> dict:
    """
    Build the complete 3-style daily setups from pipeline data.

    Args:
        ticker_payloads: Full dossier payloads (same input as momentum_picks)
        date: Report date string
        csp_data: Pre-fetched CSP results from csp_setups.fetch_csp_setups()

    Returns:
        Dict with day_trade, swing, csp categories + metadata
    """
    from dossier.momentum_picks import score_momentum

    # Score all tickers
    scored = []
    for payload in ticker_payloads:
        try:
            result = score_momentum(payload)
            if result["ticker"]:
                result["style"] = classify_setup_style(result)
                # Add extra context for the setup card
                result["company"] = payload.get("companyName", "")
                result["sector"] = payload.get("sector", "")
                scored.append(result)
        except Exception as e:
            print(f"    [WARN] Setup scoring failed for {payload.get('ticker', '?')}: {e}")

    scored.sort(key=lambda x: x["score"], reverse=True)

    # Split into categories
    day_trades = [s for s in scored if s["style"] == "day_trade"]
    swings = [s for s in scored if s["style"] == "swing"]

    # Format each category's top pick
    def format_pick(p: dict, rank: int, why: str) -> dict:
        """Format a pick for the API output."""
        return {
            "rank": rank,
            "ticker": p["ticker"],
            "company": p.get("company", ""),
            "sector": p.get("sector", ""),
            "score": p["score"],
            "price": p["price"],
            "change_pct": p.get("change_pct", 0),
            "grade": p.get("grade", ""),
            "ema_stack": p.get("ema_stack", ""),
            "trend": p.get("trend", ""),
            "rsi": p.get("rsi", 0),
            "adx": p.get("adx", 0),
            "stoch_k": p.get("stoch_k", 0),
            "rel_vol": p.get("rel_vol", 1.0),
            "is_pullback": p.get("is_pullback_setup", False),
            "why": why,
            "tradingview": f"https://www.tradingview.com/symbols/{p['ticker']}/chart/",
        }

    # ── DAY TRADE PICKS (top 3 breakouts) ──
    dt_picks = []
    for i, p in enumerate(day_trades[:3]):
        why_parts = []
        if p.get("rel_vol", 1) >= 1.5:
            why_parts.append(f"Volume surge ({p['rel_vol']:.1f}x avg)")
        if p.get("rsi", 0) >= 55:
            why_parts.append(f"RSI momentum at {p['rsi']}")
        if p.get("adx", 0) >= 30:
            why_parts.append(f"Strong trend (ADX {p['adx']})")
        if p.get("ema_stack", "").startswith("FULL"):
            why_parts.append("Full EMA alignment")
        why = "; ".join(why_parts) if why_parts else "Breakout candidate with strong technicals"
        dt_picks.append(format_pick(p, i + 1, why))

    # ── SWING TRADE PICKS (top 3 pullbacks) ──
    sw_picks = []
    for i, p in enumerate(swings[:3]):
        why_parts = []
        if p.get("is_pullback_setup"):
            why_parts.append("Bounce 2.0 setup (EMA+ADX+Stoch)")
        if p.get("stoch_k", 50) < 40:
            why_parts.append(f"Stoch oversold ({p['stoch_k']})")
        if p.get("adx", 0) >= 25:
            why_parts.append(f"Trending (ADX {p['adx']})")
        if p.get("ema_stack", "").startswith("FULL"):
            why_parts.append("Full EMA stack")
        why = "; ".join(why_parts) if why_parts else "Pullback into support in uptrend"
        sw_picks.append(format_pick(p, i + 1, why))

    # ── CSP PICKS (top 3 wheel candidates) ──
    csp_picks = []
    if csp_data:
        for i, c in enumerate(csp_data[:3]):
            trade = c.get("trade", {}) or {}
            why_parts = []
            if c.get("vopr_grade"):
                why_parts.append(f"VoPR Grade {c['vopr_grade']}")
            if c.get("vrp_ratio"):
                why_parts.append(f"VRP ratio {c['vrp_ratio']:.2f}")
            if trade.get("roc_weekly"):
                why_parts.append(f"ROC {trade['roc_weekly']:.1f}%/wk")
            if c.get("vol_regime"):
                why_parts.append(f"Vol regime: {c['vol_regime']}")
            why = "; ".join(why_parts) if why_parts else "Premium selling opportunity"

            csp_picks.append({
                "rank": i + 1,
                "ticker": c["ticker"],
                "company": c.get("company", ""),
                "price": c.get("price", 0),
                "adx": c.get("adx", 0),
                "rsi": c.get("rsi", 0),
                "vopr_grade": c.get("vopr_grade", ""),
                "vrp_ratio": c.get("vrp_ratio"),
                "vol_regime": c.get("vol_regime", ""),
                "trade": trade,
                "why": why,
                "tradingview": f"https://www.tradingview.com/symbols/{c['ticker']}/chart/",
            })

    # ── Regime context ──
    regime_data = {}
    try:
        from dossier.market_regime import detect_regime
        regime_data = detect_regime()
    except Exception:
        pass

    # ── Build output ──
    setups = {
        "date": date,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "market_regime": {
            "regime": regime_data.get("regime", "UNKNOWN"),
            "vix": regime_data.get("vix", 0),
            "note": _regime_note(regime_data.get("regime", "UNKNOWN")),
        },
        "day_trade": {
            "title": "🥇 Day Trade — Breakout",
            "description": "Intraday momentum plays with volume confirmation. Get in, ride the move, get out.",
            "picks": dt_picks,
            "count": len(dt_picks),
        },
        "swing": {
            "title": "🥈 Swing Trade — Momentum Pullback",
            "description": "3-10 day holds. Trend is up, stock pulled back to support. Bounce 2.0 setups.",
            "picks": sw_picks,
            "count": len(sw_picks),
        },
        "csp": {
            "title": "🥉 Cash-Secured Put — Wheel",
            "description": "Premium selling with an edge. Strong stocks you'd own anyway, sell puts at support.",
            "picks": csp_picks,
            "count": len(csp_picks),
        },
        "total_analyzed": len(scored),
        "methodology": {
            "scoring": "9-factor ML-calibrated momentum composite (Stoch>ADX>RelVol>RSI>EMA21 proximity)",
            "classification": "Day trade = volume surge + RSI momentum. Swing = pullback to EMA + stoch oversold.",
            "csp": "TradingView screener → EMA/ATR filter → options chain → VoPR enrichment",
        },
    }

    # Save to API endpoint
    _save_setups(setups)

    return setups


def _regime_note(regime: str) -> str:
    """Human-readable regime advice."""
    notes = {
        "CALM": "✅ Low volatility — full size, all strategies go",
        "NORMAL": "✅ Normal conditions — favor pullback entries",
        "ELEVATED": "🟡 Elevated vol — tighten stops, prefer CSPs (sell premium)",
        "FEAR": "⚠️ High VIX — reduce size, CSPs are premium-rich",
        "PANIC": "🔴 Extreme fear — cash is king, sell premium only if brave",
    }
    return notes.get(regime, "ℹ️ Unknown regime — trade with caution")


def _save_setups(setups: dict):
    """Write to docs/api/daily-setups.json for GH Pages."""
    try:
        api_dir = PROJECT_ROOT / "docs" / "api"
        api_dir.mkdir(parents=True, exist_ok=True)
        api_path = api_dir / "daily-setups.json"
        with open(api_path, "w") as f:
            json.dump(setups, f, indent=2)
        print(f"    ✓ Daily setups API: docs/api/daily-setups.json")
        print(f"      Day trades: {setups['day_trade']['count']}, "
              f"Swings: {setups['swing']['count']}, "
              f"CSPs: {setups['csp']['count']}")
    except Exception as e:
        print(f"    [WARN] Daily setups save failed: {e}")


def format_setups_text(setups: dict) -> str:
    """Format setups for the daily dossier report text."""
    lines = ["", "DAILY TRADING SETUPS", "=" * 60]

    for category in ["day_trade", "swing", "csp"]:
        cat = setups.get(category, {})
        lines.append(f"\n{cat.get('title', category.upper())}")
        lines.append(f"  {cat.get('description', '')}")
        lines.append("-" * 50)

        picks = cat.get("picks", [])
        if not picks:
            lines.append("  (No setups today)")
            continue

        for p in picks:
            ticker = p.get("ticker", "?")
            price = p.get("price", 0)
            score = p.get("score", "")
            why = p.get("why", "")

            if category == "csp":
                trade = p.get("trade", {}) or {}
                strike = trade.get("strike", "?")
                exp = trade.get("expiration", "?")
                prem = trade.get("premium", 0)
                grade = p.get("vopr_grade", "?")
                lines.append(
                    f"  #{p['rank']}  {ticker}  ${price:.2f}  "
                    f"VoPR:{grade}  Sell ${strike}P exp {exp} @ ${prem:.2f}"
                )
            else:
                lines.append(
                    f"  #{p['rank']}  {ticker}  ${price:.2f}  "
                    f"Score:{score}  Grade:{p.get('grade', '?')}"
                )
            lines.append(f"       ↳ {why}")

    regime = setups.get("market_regime", {})
    if regime.get("note"):
        lines.append(f"\n{regime['note']}")

    return "\n".join(lines)
