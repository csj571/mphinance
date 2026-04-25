"""
Daily Cuts — 3-Tier Setup Generator

Selects the absolute best Momentum trade, CSP, and Leveraged ETF play
and assigns them a conviction tier: Prime, Choice, or Select.

Used for the streamlined Substack / Dossier HTML report.
"""

def assign_momentum_tier(score: float, grade: str = "") -> str:
    """Assign Prime, Choice, or Select based on momentum score and grade."""
    if score >= 75 or grade == "A":
        return "Prime"
    elif score >= 55 or grade == "B":
        return "Choice"
    return "Select"

def assign_csp_tier(vopr_grade: str, vrp_ratio: float = 0.0) -> str:
    """Assign Prime, Choice, or Select based on VoPR grade and VRP ratio."""
    if vopr_grade in ["A+", "A"]:
        return "Prime"
    elif vopr_grade in ["A-", "B+", "B"]:
        return "Choice"
    return "Select"

def assign_leveraged_tier(grade: str, adx: float = 0.0) -> str:
    """Assign Prime, Choice, or Select based on VWAP reclaim grade and ADX."""
    if grade == "A" and adx >= 25:
        return "Prime"
    elif grade in ["A", "B"] and adx >= 20:
        return "Choice"
    return "Select"

def build_daily_cuts(daily_setups_data: dict, leveraged_top_pick: dict = None) -> dict:
    """
    Extracts the top setups from the daily setups data and assigns tiers.
    """
    cuts = {}

    # 1. Momentum Trade (highest score from day_trade or swing)
    momentum_candidates = []
    if "day_trade" in daily_setups_data and daily_setups_data["day_trade"].get("picks"):
        momentum_candidates.extend(daily_setups_data["day_trade"]["picks"])
    if "swing" in daily_setups_data and daily_setups_data["swing"].get("picks"):
        momentum_candidates.extend(daily_setups_data["swing"]["picks"])
    
    if momentum_candidates:
        # Sort by score descending
        momentum_candidates.sort(key=lambda x: x.get("score", 0), reverse=True)
        top_momentum = momentum_candidates[0]
        tier = assign_momentum_tier(top_momentum.get("score", 0), top_momentum.get("grade", ""))
        cuts["momentum"] = {
            "ticker": top_momentum.get("ticker"),
            "tier": tier,
            "type": "Momentum",
            "price": top_momentum.get("price"),
            "score": top_momentum.get("score"),
            "why": top_momentum.get("why"),
            "tv_url": f"https://www.tradingview.com/symbols/{top_momentum.get('ticker')}/chart/",
            "is_pullback": top_momentum.get("is_pullback", False)
        }

    # 2. CSP (Cash-Secured Put)
    if "csp" in daily_setups_data and daily_setups_data["csp"].get("picks"):
        top_csp = daily_setups_data["csp"]["picks"][0]
        vopr = top_csp.get("vopr_grade", "")
        vrp = top_csp.get("vrp_ratio", 0.0)
        tier = assign_csp_tier(vopr, vrp)
        trade = top_csp.get("trade", {}) or {}
        
        cuts["csp"] = {
            "ticker": top_csp.get("ticker"),
            "tier": tier,
            "type": "Cash-Secured Put",
            "price": top_csp.get("price"),
            "strike": trade.get("strike", ""),
            "expiration": trade.get("expiration", ""),
            "premium": trade.get("premium", 0),
            "vopr_grade": vopr,
            "why": top_csp.get("why"),
            "tv_url": f"https://www.tradingview.com/symbols/{top_csp.get('ticker')}/chart/"
        }

    # 3. Leveraged ETF
    if leveraged_top_pick:
        grade = leveraged_top_pick.get("grade", "")
        adx = leveraged_top_pick.get("adx", 0)
        tier = assign_leveraged_tier(grade, adx)
        cuts["leveraged"] = {
            "ticker": leveraged_top_pick.get("underlying"),
            "etf": leveraged_top_pick.get("etf"),
            "tier": tier,
            "type": "Leveraged VWAP Reclaim",
            "grade": grade,
            "adx": adx,
            "change_pct": leveraged_top_pick.get("change_pct", 0),
            "tv_url": f"https://www.tradingview.com/symbols/{leveraged_top_pick.get('underlying')}/chart/"
        }

    return cuts
