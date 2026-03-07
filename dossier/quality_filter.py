"""
Quality Filter — Pre-screens tickers before momentum scoring.

Detects and penalizes:
  - SPACs and blank-check companies
  - Acquisition targets with pinned prices
  - Junk biotech (tiny cap + no revenue + no EPS)
  - Shell companies (no employees, no revenue, no sector)
  - Low liquidity stocks

Returns a quality dict with flags and a 0-100 quality score.
The momentum scorer applies this as a multiplier.
"""

import re


# Keywords that indicate SPAC/blank-check
SPAC_KEYWORDS = [
    "acquisition", "blank check", "special purpose",
    "merger", "holdings corp", "capital corp",
]

# Sectors where zero-revenue is a red flag (not all — some sectors like biotech
# might legitimately have clinical-stage companies, but those need extra scrutiny)
JUNK_BIO_SECTORS = ["healthcare", "biotechnology"]
JUNK_BIO_INDUSTRIES = [
    "biotechnology", "pharmaceuticals", "drug manufacturers",
    "diagnostics & research",
]

# ETF provider prefixes/keywords — we don't want to score ETFs as momentum picks
ETF_KEYWORDS = [
    "ishares", "vanguard", "spdr", "proshares", "invesco",
    "direxion", "wisdomtree", "schwab", "first trust",
    "ark ", "global x", " etf", " fund", "exchange traded",
]

# Common ETF ticker patterns (3-4 letter tickers ending in specific patterns)
ETF_TICKER_SUFFIXES = ["X", "Q", "J", "K"]

# ADR indicators
ADR_KEYWORDS = [
    "adr", "american depositary", "sponsored adr",
    "unsponsored adr", "depositary receipt",
]


def check_quality(payload: dict) -> dict:
    """
    Evaluate ticker quality. Returns dict with:
      - quality_score: 0-100 (100 = clean, 0 = total junk)
      - flags: dict of boolean flags
      - reason: human-readable explanation
    """
    flags = {
        "is_spac": False,
        "is_pinned": False,
        "is_junk_bio": False,
        "is_shell": False,
        "is_low_liquidity": False,
        "is_penny": False,
        "is_etf": False,
        "is_adr": False,
        "is_recent_ipo": False,
    }
    reasons = []
    penalty = 0  # Points to subtract from 100

    ticker = payload.get("ticker", "")
    name = (payload.get("companyName") or payload.get("name") or "").lower()
    sector = (payload.get("sector") or "").lower()
    industry = (payload.get("industry") or "").lower()
    price = payload.get("currentPrice") or payload.get("price") or 0

    # Extract fundamentals from various JSON shapes
    snapshot = payload.get("market_snapshot", {})
    fundamentals = payload.get("fundamentals", {})
    ta = payload.get("technical_analysis", {})
    vol_data = ta.get("volume", {})
    scores = payload.get("scores", {})

    # Market cap — try multiple locations
    mcap_raw = (
        snapshot.get("market_cap")
        or fundamentals.get("marketCap")
        or fundamentals.get("market_cap")
        or ""
    )
    mcap = _parse_market_cap(mcap_raw)

    # Revenue/EPS indicators
    revenue_growth = fundamentals.get("revenueGrowth") or fundamentals.get("revenue_growth") or 0
    profit_margin = fundamentals.get("profitMargins") or fundamentals.get("profit_margin") or 0
    eps = fundamentals.get("trailingEps") or fundamentals.get("eps") or 0

    # Volume
    avg_vol = vol_data.get("avg_vol_20d") or vol_data.get("avg_vol") or 0
    if isinstance(avg_vol, str):
        avg_vol = _parse_vol_string(avg_vol)

    rel_vol = vol_data.get("rel_vol") or 1.0

    # ── ETF Detection ──
    for kw in ETF_KEYWORDS:
        if kw in name:
            flags["is_etf"] = True
            penalty += 80  # Heavy penalty — ETFs shouldn't be in momentum picks
            reasons.append(f"ETF detected: '{kw}' in name")
            break
    # Also check quoteType if available
    quote_type = (payload.get("quoteType") or "").lower()
    if quote_type == "etf" and not flags["is_etf"]:
        flags["is_etf"] = True
        penalty += 80
        reasons.append("ETF detected via quoteType")

    # ── ADR Detection ──
    for kw in ADR_KEYWORDS:
        if kw in name:
            flags["is_adr"] = True
            penalty += 20  # Moderate penalty — ADRs can be ok but data is unreliable
            reasons.append(f"ADR detected: '{kw}' in name")
            break

    # ── Recent IPO Detection ──
    ipo_date_str = payload.get("ipoDate") or fundamentals.get("ipoDate") or ""
    if ipo_date_str:
        try:
            from datetime import datetime
            ipo_date = datetime.strptime(str(ipo_date_str)[:10], "%Y-%m-%d")
            days_since_ipo = (datetime.now() - ipo_date).days
            if days_since_ipo < 180:  # < 6 months
                flags["is_recent_ipo"] = True
                penalty += 30
                reasons.append(f"Recent IPO ({days_since_ipo}d ago) — unreliable technicals")
            elif days_since_ipo < 365:  # < 1 year
                penalty += 10
                reasons.append(f"IPO less than 1 year ago ({days_since_ipo}d)")
        except (ValueError, TypeError):
            pass

    # ── SPAC Detection ──
    for kw in SPAC_KEYWORDS:
        if kw in name:
            flags["is_spac"] = True
            penalty += 60
            reasons.append(f"SPAC indicator: '{kw}' in name")
            break

    # ── Penny Stock Detection ──
    if price < 3.0:
        flags["is_penny"] = True
        penalty += 40
        reasons.append(f"Penny stock: ${price:.2f}")
    elif price < 5.0:
        penalty += 15
        reasons.append(f"Low-priced: ${price:.2f}")

    # ── Pinned Price Detection ──
    # If price change is basically zero for what should be a trading day
    change_pct = abs(payload.get("priceChangePct", 0) or 0)
    if change_pct < 0.05 and price > 5:
        # Could be pinned acquisition target — flag but small penalty
        flags["is_pinned"] = True
        penalty += 15
        reasons.append(f"Price appears pinned (change: {change_pct:.2f}%)")

    # ── Junk Bio Detection ──
    if (sector in JUNK_BIO_SECTORS or industry in JUNK_BIO_INDUSTRIES):
        is_clinical_stage = False
        # Clinical stage: tiny cap + no profits + no revenue growth
        if mcap and mcap < 500_000_000:  # < $500M
            if not eps or eps <= 0:
                if not revenue_growth or revenue_growth <= 0:
                    is_clinical_stage = True

        if is_clinical_stage:
            flags["is_junk_bio"] = True
            penalty += 45
            reasons.append(f"Clinical-stage bio: MCap {_fmt_cap(mcap)}, no EPS, no rev growth")

    # ── Shell Company Detection ──
    if not sector or sector in ["n/a", "none", ""]:
        if not industry or industry in ["n/a", "none", ""]:
            if mcap and mcap < 100_000_000:  # < $100M
                flags["is_shell"] = True
                penalty += 70
                reasons.append("Shell: No sector, no industry, tiny cap")
            elif not mcap:
                # Can't determine cap either — suspicious
                penalty += 20
                reasons.append("Unknown sector/industry, no market cap data")

    # ── Low Liquidity ──
    if avg_vol and avg_vol < 200_000:
        flags["is_low_liquidity"] = True
        penalty += 25
        reasons.append(f"Low liquidity: avg vol {avg_vol:,.0f}")
    elif avg_vol and avg_vol < 500_000:
        penalty += 10
        reasons.append(f"Thin volume: avg vol {avg_vol:,.0f}")

    # ── Grade sanity check ──
    # If overall grade is D AND the stock trips any flag, extra penalty
    grade = scores.get("grade", "")
    if grade == "D" and any(flags.values()):
        penalty += 10
        reasons.append("Grade D + quality flags → extra penalty")

    quality_score = max(0, min(100, 100 - penalty))

    return {
        "quality_score": quality_score,
        "flags": flags,
        "reasons": reasons,
        "has_issues": any(flags.values()),
        "ticker": ticker,
    }


def _parse_market_cap(raw) -> float | None:
    """Parse market cap from various formats: '$1.23B', 1234567890, etc."""
    if isinstance(raw, (int, float)):
        return float(raw) if raw > 0 else None
    if not raw or not isinstance(raw, str):
        return None
    raw = raw.strip().upper().replace("$", "").replace(",", "")
    try:
        if raw.endswith("T"):
            return float(raw[:-1]) * 1_000_000_000_000
        elif raw.endswith("B"):
            return float(raw[:-1]) * 1_000_000_000
        elif raw.endswith("M"):
            return float(raw[:-1]) * 1_000_000
        elif raw.endswith("K"):
            return float(raw[:-1]) * 1_000
        else:
            return float(raw)
    except (ValueError, TypeError):
        return None


def _parse_vol_string(raw: str) -> int:
    """Parse volume strings like '1,234,567' or '1.2M'."""
    raw = raw.strip().upper().replace(",", "")
    try:
        if raw.endswith("M"):
            return int(float(raw[:-1]) * 1_000_000)
        elif raw.endswith("K"):
            return int(float(raw[:-1]) * 1_000)
        return int(float(raw))
    except (ValueError, TypeError):
        return 0


def _fmt_cap(mcap) -> str:
    if not mcap:
        return "N/A"
    if mcap >= 1e12:
        return f"${mcap/1e12:.1f}T"
    if mcap >= 1e9:
        return f"${mcap/1e9:.1f}B"
    if mcap >= 1e6:
        return f"${mcap/1e6:.0f}M"
    return f"${mcap:,.0f}"
