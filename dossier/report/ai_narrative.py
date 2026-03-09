"""
AI Narrative Generator — Gemini-powered market commentary.

Written in the voice of Sam the Quant Ghost.
"""

from dossier.config import GEMINI_API_KEY, AI_MODEL


def generate_narrative(
    market: dict,
    institutional: dict,
    scanner_signals: list,
    persistence: dict,
    dossiers: list,
) -> str:
    """Generate an AI narrative from the day's data using Gemini."""
    if not GEMINI_API_KEY:
        return _fallback_narrative(market, institutional, scanner_signals, persistence, dossiers)

    try:
        from google import genai
        client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        print(f"  [WARN] Gemini init failed: {e}")
        return _fallback_narrative(market, institutional, scanner_signals, persistence, dossiers)

    top_buying = [s["ticker"] for s in institutional.get("top_buying", [])[:5]]
    top_selling = [s["ticker"] for s in institutional.get("top_selling", [])[:5]]
    bullish = [s["symbol"] for s in scanner_signals if s.get("direction") == "BULLISH"][:5]
    lifers = [l["ticker"] for l in persistence.get("lifers", [])]
    vix = market.get("vix", {})
    sectors = market.get("sector_rotation", [])[:3]
    dossier_summaries = []
    for d in dossiers[:3]:
        dossier_summaries.append(
            f"{d['ticker']}: Grade {d['scores']['grade']}, "
            f"Tech {d['scores']['technical']}/100, "
            f"Fund {d['scores']['fundamental']}/100, "
            f"{d['valuation']['status']} ({d['valuation']['gap_pct']}%), "
            f"Verdict: {d['verdict']}"
        )

    prompt = f"""You are Sam the Quant Ghost — a sharp, witty quantitative analyst 
who writes daily market intelligence reports. Write a concise 2-3 paragraph synthesis 
of today's market data. Be direct, opinionated, and use trader-speak. 
Reference specific tickers and numbers. No fluff.

TODAY'S DATA:
- VIX: {vix.get('vix_level', 'N/A')} ({vix.get('regime_name', 'Unknown')})
- Sector leaders (5D): {', '.join(s['sector'] for s in sectors)}
- Institutions BUYING: {', '.join(top_buying) or 'Nothing notable'}
- Institutions SELLING: {', '.join(top_selling) or 'Nothing notable'}
- Scanner BULLISH: {', '.join(bullish) or 'None'}
- Lifers (20+ day persistence): {', '.join(lifers) or 'None'}
- Top dossiers: {'; '.join(dossier_summaries) or 'N/A'}

Write the synthesis now. Keep it under 200 words. Use markdown formatting.
Sign off as "— Ghost out. 👻"
"""

    try:
        response = client.models.generate_content(model=AI_MODEL, contents=prompt)
        narrative = response.text.strip()
        print("  ✓ AI narrative generated")
        return narrative
    except Exception as e:
        print(f"  [WARN] Gemini generation failed: {e}")
        return _fallback_narrative(market, institutional, scanner_signals, persistence, dossiers)


def _fallback_narrative(market, institutional, scanner_signals, persistence, dossiers) -> str:
    """Data-driven narrative when AI is unavailable."""
    vix = market.get("vix", {})
    regime = vix.get("regime_name", "Unknown")
    vix_level = vix.get("vix_level", 0)

    buying_count = len(institutional.get("top_buying", []))
    selling_count = len(institutional.get("top_selling", []))
    bullish_count = sum(1 for s in scanner_signals if s.get("direction") == "BULLISH")
    total_signals = len(scanner_signals)
    lifer_count = persistence.get("summary", {}).get("lifers", 0)

    top_buyer = institutional.get("top_buying", [{}])[0].get("ticker", "N/A") if institutional.get("top_buying") else "N/A"

    return (
        f"**Regime check:** VIX at {vix_level} puts us in {regime} mode. "
        f"Institutions are active — {buying_count} buying signals vs {selling_count} selling. "
        f"Top institutional conviction: **{top_buyer}**.\n\n"
        f"Scanner picked up {bullish_count}/{total_signals} bullish setups today. "
        f"{'Persistence tells the real story — ' + str(lifer_count) + ' lifers in the 21-day window.' if lifer_count else 'No lifers yet — signals are fresh.'} "
        f"Stay sharp, execute the playbook.\n\n"
        f"— Ghost out. 👻"
    )
