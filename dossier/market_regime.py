import yfinance as yf
import json
import time

def detect_regime():
    """
    Classifies the current market environment based on VIX metrics and SPY price action.
    """
    tickers_to_fetch = ['^VIX', '^VIX3M', '^VVIX', 'SPY']
    
    data = {}
    for t in tickers_to_fetch:
        try:
            ticker = yf.Ticker(t)
            hist = ticker.history(period='1y')
            if hist.empty:
                # Try a smaller period if 1y fails
                hist = ticker.history(period='1mo')
            data[t] = hist
        except Exception as e:
            print(f"Warning: Could not fetch data for {t}: {e}")
            data[t] = None

    # --- VIX Level & Change ---
    vix_hist = data.get('^VIX')
    if vix_hist is not None and not vix_hist.empty:
        vix_current = vix_hist['Close'].iloc[-1]
        # 5 trading days ago
        vix_5d_ago = vix_hist['Close'].iloc[-6] if len(vix_hist) >= 6 else vix_hist['Close'].iloc[0]
        vix_change_5d = vix_current - vix_5d_ago
    else:
        vix_current = 20.0
        vix_change_5d = 0.0

    # --- VIX3M (Ratio for backwardation check) ---
    vix3m_hist = data.get('^VIX3M')
    vix3m_current = vix3m_hist['Close'].iloc[-1] if vix3m_hist is not None and not vix3m_hist.empty else 20.0
    vix_vix3m_ratio = vix_current / vix3m_current if vix3m_current > 0 else 1.0

    # --- VVIX (Vol of Vol) ---
    vvix_hist = data.get('^VVIX')
    vvix_current = vvix_hist['Close'].iloc[-1] if vvix_hist is not None and not vvix_hist.empty else 100.0

    # --- SPY vs SMAs ---
    spy_hist = data.get('SPY')
    spy_vs_sma200 = 0.0
    spy_current = 0.0
    if spy_hist is not None and not spy_hist.empty:
        spy_current = spy_hist['Close'].iloc[-1]
        if len(spy_hist) >= 200:
            sma200 = spy_hist['Close'].rolling(window=200).mean().iloc[-1]
            spy_vs_sma200 = (spy_current - sma200) / sma200 * 100
        else:
            spy_vs_sma200 = 0.0

    # --- Regime Classification ---
    if vix_current > 35:
        regime = "PANIC"
    elif vix_current > 25:
        regime = "FEAR"
    elif vix_current > 20:
        regime = "ELEVATED"
    elif vix_current >= 15:
        regime = "NORMAL"
    else:
        regime = "CALM"

    # --- Context & Suggestions ---
    context = f"VIX {regime.lower()} at {vix_current:.1f} ({vix_change_5d:+.1f} this week). "
    context += f"SPY {spy_vs_sma200:+.1f}% vs 200 SMA."
    
    if vix_vix3m_ratio > 1.0:
        context += " WARNING: VIX/VIX3M ratio > 1.0 (Inversion/Fear)."
    if vvix_current > 120:
        context += " WARNING: VVIX > 120 (Unstable Volatility)."

    suggestions = suggest_hedges(regime, [])

    return {
        "regime": regime,
        "vix": round(vix_current, 2),
        "vix_change_5d": round(vix_change_5d, 2),
        "vix_vix3m_ratio": round(vix_vix3m_ratio, 2),
        "spy_vs_sma200": round(spy_vs_sma200, 2),
        "hedge_suggestions": suggestions,
        "market_context": context
    }

def suggest_hedges(regime, picks):
    suggestions = []
    if regime == "PANIC":
        suggestions.append("CRISIS: Protect capital, look for long-term bottoms, cash is a position.")
    elif regime == "FEAR":
        suggestions.append("FEAR: Reduce position sizes to 50%, add VIX calls or SPY puts.")
    elif regime == "ELEVATED":
        suggestions.append("CAUTION: Reduce position sizes, tighten stops, consider protective puts.")
    elif regime == "NORMAL":
        suggestions.append("HEALTHY: Standard position sizing, focus on high-quality momentum.")
    elif regime == "CALM":
        suggestions.append("BULLISH: Market favorable for momentum, can be more aggressive.")

    if picks and regime in ["ELEVATED", "FEAR", "PANIC"]:
        for pick in picks:
            suggestions.append(f"HEDGE: Consider protective puts on {pick}")

    return suggestions

if __name__ == "__main__":
    result = detect_regime()
    print(json.dumps(result, indent=2))
