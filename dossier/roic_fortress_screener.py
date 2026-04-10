#!/usr/bin/env python3
"""
🏰 ROIC Fortress Screener — Quality-First Stock Scanner

"CPI day? FOMC? Tariff tweets? Doesn't matter when your portfolio owns
companies that print cash like the Fed prints excuses." — Sam

Built for macro uncertainty. Finds companies with:
  - High ROIC (Return on Invested Capital) 
  - Fat free cash flow yields
  - Low leverage (Debt/EBITDA)
  - Strong interest coverage
  - Expanding or stable margins  
  - Revenue growth despite headwinds

The Fortress Score (0-100) combines six axes:
  1. ROIC Efficiency      (25%) — How well mgmt deploys capital
  2. FCF Yield            (20%) — Real cash generation vs price  
  3. Balance Sheet        (15%) — Debt/EBITDA + interest coverage
  4. Margin Quality       (15%) — Operating margin level + stability
  5. Growth Durability    (15%) — Revenue growth + earnings trajectory
  6. Shareholder Return   (10%) — Buybacks + dividend safety

Tiers:
  🏰 FORTRESS  (80-100) — Bulletproof. Buy on dips, hold forever.
  🛡️  CASTLE    (65-79)  — Strong moat. Weather any storm.
  🏠 HOUSE     (50-64)  — Decent quality. Needs monitoring.
  🏚️  SHACK     (30-49)  — Questionable. Maybe for trading, not investing.
  💀 RUBBLE    (0-29)   — Capital destroyer. Run.

Usage:
    python -m dossier.roic_fortress_screener                        # Full market scan
    python -m dossier.roic_fortress_screener --tickers AAPL,MSFT    # Specific tickers  
    python -m dossier.roic_fortress_screener --sector Technology     # Sector filter
    python -m dossier.roic_fortress_screener --min-cap 10B          # Min market cap
    python -m dossier.roic_fortress_screener --top 25               # Top N results
    python -m dossier.roic_fortress_screener --json                 # Machine output
    python -m dossier.roic_fortress_screener --csv fortress.csv     # Save CSV

© mphinance + Sam the Quant Ghost — "Find the fortress, ignore the noise."
"""

import argparse
import json
import math
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np

try:
    import yfinance as yf
except ImportError:
    print("❌ pip install yfinance")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("❌ pip install requests")
    sys.exit(1)


# ─── Config ───────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Sam's quality quotes for output flavor
FORTRESS_QUOTES = [
    "God-tier balance sheets. Execute with conviction.",
    "Cash flow is the only truth. Everything else is narrative.",
    "ROIC doesn't lie. Management can. Pick accordingly.",
    "CPI hot? Cool. These companies don't care.",
    "Buffett said 'wonderful company at a fair price.' Sam says 'fortress at any price.'",
    "Debt is a feature in bull markets and a death sentence in bear markets.",
    "The best companies make money while you sleep. The worst lose it while you panic.",
]

RUBBLE_QUOTES = [
    "Nothing fortress-grade today. Cash is a position.",
    "The market isn't serving quality. Patience pays dividends. Literally.",
    "No fortresses found. Maybe try lowering your standards? Just kidding. Never do that.",
]


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 1 — TRADINGVIEW BULK UNIVERSE  ████
# ═══════════════════════════════════════════════════════════════════

TV_SCANNER_URL = "https://scanner.tradingview.com/america/scan"

TV_COLUMNS = [
    "name",                     # 0  ticker
    "description",              # 1  company name  
    "close",                    # 2  last price
    "change",                   # 3  % change today
    "volume",                   # 4  today's volume
    "average_volume_30d_calc",  # 5  30d avg volume
    "market_cap_basic",         # 6  market cap
    "sector",                   # 7  sector
    "earnings_per_share_basic_ttm",  # 8  EPS TTM
    "price_earnings_ttm",       # 9  P/E ratio
    "dividend_yield_recent",    # 10 dividend yield
    "Perf.Y",                   # 11 1-year performance
    "Perf.6M",                  # 12 6-month performance
    "Perf.3M",                  # 13 3-month performance
    "Recommend.All",            # 14 TV signal
    "RSI",                      # 15 RSI(14)
    "SMA200",                   # 16 SMA200
    "SMA50",                    # 17 SMA50
    "revenue_per_share_fq",     # 18 revenue per share
    "net_income_fq",            # 19 net income (quarterly)
]


def _tv_fetch_universe(min_cap: float = 2_000_000_000) -> list[dict]:
    """
    Fetch the US equity universe from TradingView.
    Pre-filters for established companies (positive EPS, min cap).
    """
    payload = {
        "filter": [
            {"left": "type", "operation": "in_range", "right": ["stock"]},
            {"left": "subtype", "operation": "in_range",
             "right": ["common", "foreign-issuer"]},
            {"left": "exchange", "operation": "in_range",
             "right": ["NYSE", "NASDAQ", "AMEX"]},
            {"left": "average_volume_30d_calc", "operation": "greater", "right": 200_000},
            {"left": "close", "operation": "greater", "right": 5},
            {"left": "market_cap_basic", "operation": "greater", "right": min_cap},
            # Only profitable companies — fortress candidates need earnings
            {"left": "earnings_per_share_basic_ttm", "operation": "greater", "right": 0},
        ],
        "options": {"lang": "en"},
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": TV_COLUMNS,
        "sort": {"sortBy": "market_cap_basic", "sortOrder": "desc"},
        "range": [0, 5000],
    }

    resp = requests.post(TV_SCANNER_URL, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    rows = data.get("data", [])

    results = []
    for item in rows:
        d = item.get("d", [])
        if len(d) < len(TV_COLUMNS):
            continue
        ticker = d[0]
        if not ticker or d[2] is None:
            continue

        results.append({
            "ticker": ticker,
            "name": d[1] or ticker,
            "price": d[2],
            "change_pct": d[3] or 0,
            "volume": d[4] or 0,
            "avg_vol_30d": d[5] or 0,
            "market_cap": d[6] or 0,
            "sector": d[7] or "Unknown",
            "eps_ttm": d[8] or 0,
            "pe_ratio": d[9],
            "div_yield": d[10],
            "perf_1y": d[11],
            "perf_6m": d[12],
            "perf_3m": d[13],
            "tv_signal": d[14],
            "rsi": d[15],
            "sma_200": d[16],
            "sma_50": d[17],
            "rev_per_share": d[18],
            "net_income_q": d[19],
        })

    return results


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 2 — QUALITY PRE-FILTER  ████
# ═══════════════════════════════════════════════════════════════════

def quality_prefilter(stocks: list[dict], sector_filter: str | None = None,
                      verbose: bool = True) -> list[dict]:
    """
    Pre-filter for quality candidates. Only companies worth deep-scanning.
    """
    total = len(stocks)
    if verbose:
        print(f"\n  ┌─ QUALITY FUNNEL: {total} profitable US stocks loaded")

    # Sector filter if specified
    if sector_filter:
        prev = len(stocks)
        sector_lower = sector_filter.lower()
        stocks = [s for s in stocks if sector_lower in (s.get("sector") or "").lower()]
        if verbose:
            print(f"  ├─ Sector: '{sector_filter}' ──────────→ {len(stocks)} survive ({prev - len(stocks)} cut)")

    # P/E sanity — no P/E > 200 (wildly speculative) or negative
    prev = len(stocks)
    stocks = [s for s in stocks if (
        s.get("pe_ratio") is not None 
        and 0 < s["pe_ratio"] <= 200
    )]
    if verbose:
        print(f"  ├─ P/E 0-200 (no moon shots) ──────→ {len(stocks)} survive ({prev - len(stocks)} cut)")

    # Must have meaningful EPS  
    prev = len(stocks)
    stocks = [s for s in stocks if s.get("eps_ttm", 0) > 0.10]
    if verbose:
        print(f"  ├─ EPS > $0.10 (real earnings) ────→ {len(stocks)} survive ({prev - len(stocks)} cut)")

    # Above SMA 200 — quality companies in uptrends only
    prev = len(stocks)
    stocks = [s for s in stocks if (
        s.get("sma_200") is not None
        and s["price"] >= s["sma_200"] * 0.85  # Allow 15% below — value zone
    )]
    if verbose:
        print(f"  ├─ Within 15% of SMA 200 ─────────→ {len(stocks)} survive ({prev - len(stocks)} cut)")

    if verbose:
        pct = (1 - len(stocks) / total) * 100 if total > 0 else 0
        print(f"  └─ FUNNEL COMPLETE: {len(stocks)} candidates ({pct:.0f}% eliminated)\n")

    return stocks


# ═══════════════════════════════════════════════════════════════════
# ████  STAGE 3 — DEEP FUNDAMENTAL SCAN  ████
# ═══════════════════════════════════════════════════════════════════

def _safe_get(d: dict, key: str, default=0):
    """Safely get a value, returning default for None/NaN."""
    val = d.get(key, default)
    if val is None:
        return default
    try:
        f = float(val)
        if np.isnan(f) or np.isinf(f):
            return default
        return f
    except (ValueError, TypeError):
        return default


def _calc_roic(info: dict, bs: dict, income: dict) -> float | None:
    """
    Calculate ROIC = NOPAT / Invested Capital
    
    NOPAT = Operating Income * (1 - Tax Rate)
    Invested Capital = Total Equity + Total Debt - Cash
    """
    op_income = _safe_get(info, "operatingMargins", 0) * _safe_get(info, "totalRevenue", 0)
    
    # Try direct operating income from income statement
    if op_income == 0:
        op_income = _safe_get(income, "Operating Income", 0)
    if op_income == 0:
        op_income = _safe_get(income, "EBIT", 0)
        
    if op_income <= 0:
        return None
    
    # Effective tax rate
    tax_provision = _safe_get(income, "Tax Provision", 0)
    pretax_income = _safe_get(income, "Pretax Income", 0)
    if pretax_income > 0 and tax_provision > 0:
        tax_rate = min(tax_provision / pretax_income, 0.40)  # Cap at 40%
    else:
        tax_rate = 0.21  # Assume US statutory rate
    
    nopat = op_income * (1 - tax_rate)
    
    # Invested capital components
    total_equity = _safe_get(bs, "Stockholders Equity", 0)
    if total_equity == 0:
        total_equity = _safe_get(bs, "Total Stockholders Equity", 0)
    
    total_debt = _safe_get(bs, "Total Debt", 0)
    if total_debt == 0:
        total_debt = (_safe_get(bs, "Long Term Debt", 0) + 
                      _safe_get(bs, "Current Debt", 0))
    
    cash = _safe_get(bs, "Cash And Cash Equivalents", 0)
    if cash == 0:
        cash = _safe_get(bs, "Cash Cash Equivalents And Short Term Investments", 0)
    
    invested_capital = total_equity + total_debt - cash
    
    if invested_capital <= 0:
        return None
    
    return (nopat / invested_capital) * 100  # Return as percentage


def _calc_fcf_yield(info: dict, cf: dict, market_cap: float) -> float | None:
    """FCF Yield = Free Cash Flow / Market Cap."""
    fcf = _safe_get(info, "freeCashflow", 0)
    if fcf == 0:
        fcf = _safe_get(cf, "Free Cash Flow", 0)
    
    if fcf <= 0 or market_cap <= 0:
        return None
    
    return (fcf / market_cap) * 100


def _calc_debt_ebitda(bs: dict, income: dict) -> float | None:
    """Net Debt / EBITDA — lower is better."""
    total_debt = _safe_get(bs, "Total Debt", 0)
    if total_debt == 0:
        total_debt = (_safe_get(bs, "Long Term Debt", 0) + 
                      _safe_get(bs, "Current Debt", 0))
    
    cash = _safe_get(bs, "Cash And Cash Equivalents", 0)
    if cash == 0:
        cash = _safe_get(bs, "Cash Cash Equivalents And Short Term Investments", 0)
    
    net_debt = total_debt - cash
    
    ebitda = _safe_get(income, "EBITDA", 0)
    if ebitda == 0:
        ebit = _safe_get(income, "EBIT", 0)
        da = _safe_get(income, "Reconciled Depreciation", 0)
        ebitda = ebit + da
    
    if ebitda <= 0:
        return None
    
    return net_debt / ebitda


def _calc_interest_coverage(income: dict) -> float | None:
    """EBIT / Interest Expense."""
    ebit = _safe_get(income, "EBIT", 0)
    interest = abs(_safe_get(income, "Interest Expense", 0))
    
    if interest <= 0:
        return 999.0  # No debt = infinite coverage
    
    if ebit <= 0:
        return 0.0
    
    return ebit / interest


def _calc_buyback_yield(info: dict, market_cap: float) -> float:
    """Share buyback yield based on change in shares outstanding."""
    # yfinance doesn't directly give buyback data easily, 
    # but we can estimate from sharesOutstanding changes
    shares = _safe_get(info, "sharesOutstanding", 0)
    float_shares = _safe_get(info, "floatShares", 0)
    
    # If company is buying back shares, float < outstanding
    # This is a rough proxy — real buyback data needs quarterly comparison
    if shares > 0 and float_shares > 0:
        return max(0, (1 - float_shares / shares)) * 100
    return 0


def deep_scan_fundamentals(ticker: str, tv_data: dict | None = None) -> dict | None:
    """
    Full fundamental deep scan for fortress scoring.
    Pulls balance sheet, income statement, and cash flow data.
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info or {}
        
        # Bail if we can't get basic info
        if not info.get("marketCap"):
            return None
        
        market_cap = float(info.get("marketCap", 0))
        price = float(info.get("currentPrice") or info.get("regularMarketPrice") or 
                      (tv_data or {}).get("price", 0))
        
        if price <= 0 or market_cap <= 0:
            return None
        
        # Pull financial statements
        bs = {}
        income = {}
        cf = {}
        
        try:
            balance_sheet = stock.balance_sheet
            if balance_sheet is not None and not balance_sheet.empty:
                bs = balance_sheet.iloc[:, 0].to_dict()  # Most recent
        except Exception:
            pass
            
        try:
            income_stmt = stock.income_stmt
            if income_stmt is not None and not income_stmt.empty:
                income = income_stmt.iloc[:, 0].to_dict()
        except Exception:
            pass
            
        try:
            cashflow = stock.cashflow
            if cashflow is not None and not cashflow.empty:
                cf = cashflow.iloc[:, 0].to_dict()
        except Exception:
            pass
        
        # ── Core Metrics ──
        roic = _calc_roic(info, bs, income)
        fcf_yield = _calc_fcf_yield(info, cf, market_cap)
        debt_ebitda = _calc_debt_ebitda(bs, income)
        interest_cov = _calc_interest_coverage(income)
        
        # Operating margin from yfinance info
        op_margin = _safe_get(info, "operatingMargins", 0) * 100
        gross_margin = _safe_get(info, "grossMargins", 0) * 100
        profit_margin = _safe_get(info, "profitMargins", 0) * 100
        
        # Growth
        rev_growth = _safe_get(info, "revenueGrowth", 0) * 100
        earnings_growth = _safe_get(info, "earningsGrowth", 0) * 100  
        
        # Dividend
        div_yield = _safe_get(info, "dividendYield", 0) * 100
        payout_ratio = _safe_get(info, "payoutRatio", 0) * 100
        
        # P/E and PEG
        pe = _safe_get(info, "trailingPE", 0)
        fwd_pe = _safe_get(info, "forwardPE", 0)
        peg = _safe_get(info, "pegRatio", 0)
        
        # Book value
        pb = _safe_get(info, "priceToBook", 0)
        
        # ROCE (Return on Capital Employed)  
        ebit = _safe_get(income, "EBIT", 0)
        total_assets = _safe_get(bs, "Total Assets", 0)
        current_liab = _safe_get(bs, "Current Liabilities", 0)
        capital_employed = total_assets - current_liab
        roce = (ebit / capital_employed * 100) if capital_employed > 0 and ebit > 0 else None
        
        # ROE
        roe = _safe_get(info, "returnOnEquity", 0) * 100
        
        # ═══════════════════════════════════════════════════════
        # ████  FORTRESS SCORING  ████
        # ═══════════════════════════════════════════════════════

        scores = {}
        
        # Axis 1: ROIC Efficiency (25%)
        if roic is not None:
            if roic >= 25:
                scores["roic"] = 100
            elif roic >= 20:
                scores["roic"] = 90
            elif roic >= 15:
                scores["roic"] = 75
            elif roic >= 10:
                scores["roic"] = 55
            elif roic >= 5:
                scores["roic"] = 30
            else:
                scores["roic"] = 10
        else:
            scores["roic"] = 0
        
        # Axis 2: FCF Yield (20%)
        if fcf_yield is not None:
            if fcf_yield >= 8:
                scores["fcf"] = 100
            elif fcf_yield >= 6:
                scores["fcf"] = 90
            elif fcf_yield >= 4:
                scores["fcf"] = 75
            elif fcf_yield >= 2.5:
                scores["fcf"] = 55
            elif fcf_yield >= 1:
                scores["fcf"] = 30
            else:
                scores["fcf"] = 10
        else:
            scores["fcf"] = 0
        
        # Axis 3: Balance Sheet (15%)
        bs_score = 50  # Start neutral
        
        if debt_ebitda is not None:
            if debt_ebitda <= 0:       # Net cash
                bs_score += 40
            elif debt_ebitda <= 1.0:
                bs_score += 30
            elif debt_ebitda <= 2.0:
                bs_score += 15
            elif debt_ebitda <= 3.5:
                bs_score += 0
            elif debt_ebitda <= 5.0:
                bs_score -= 15
            else:
                bs_score -= 30
        
        if interest_cov is not None:
            if interest_cov >= 20:
                bs_score += 15
            elif interest_cov >= 10:
                bs_score += 10
            elif interest_cov >= 5:
                bs_score += 5
            elif interest_cov >= 2:
                bs_score -= 5
            else:
                bs_score -= 20
        
        scores["balance_sheet"] = max(0, min(100, bs_score))
        
        # Axis 4: Margin Quality (15%)
        margin_score = 0
        if op_margin >= 30:
            margin_score = 100
        elif op_margin >= 20:
            margin_score = 80
        elif op_margin >= 15:
            margin_score = 65
        elif op_margin >= 10:
            margin_score = 45
        elif op_margin >= 5:
            margin_score = 25
        else:
            margin_score = 10
        
        # Bonus for fat gross margins (pricing power)
        if gross_margin >= 60:
            margin_score = min(100, margin_score + 10)
        
        scores["margins"] = margin_score
        
        # Axis 5: Growth Durability (15%)
        growth_score = 50
        if rev_growth >= 20:
            growth_score += 35
        elif rev_growth >= 10:
            growth_score += 25
        elif rev_growth >= 5:
            growth_score += 15
        elif rev_growth >= 0:
            growth_score += 0
        else:
            growth_score -= 20
        
        if earnings_growth >= 20:
            growth_score += 15
        elif earnings_growth >= 5:
            growth_score += 10
        elif earnings_growth < -10:
            growth_score -= 15
        
        scores["growth"] = max(0, min(100, growth_score))
        
        # Axis 6: Shareholder Return (10%)
        sr_score = 30  # Base
        if div_yield > 0:
            if payout_ratio <= 60:
                sr_score += 25  # Sustainable dividend
            elif payout_ratio <= 80:
                sr_score += 15
            else:
                sr_score += 5  # Stretched
            
            if div_yield >= 2:
                sr_score += 15
            elif div_yield >= 1:
                sr_score += 10
        
        # Check for apparent buyback activity
        buyback = _calc_buyback_yield(info, market_cap)
        if buyback > 1:
            sr_score += 15
        
        scores["shareholder_return"] = max(0, min(100, sr_score))
        
        # ── WEIGHTED FORTRESS SCORE ──
        weights = {
            "roic": 0.25,
            "fcf": 0.20,
            "balance_sheet": 0.15,
            "margins": 0.15,
            "growth": 0.15,
            "shareholder_return": 0.10,
        }
        
        fortress_score = sum(scores[k] * weights[k] for k in weights)
        fortress_score = round(fortress_score, 1)
        
        # Determine tier
        if fortress_score >= 80:
            tier = "FORTRESS"
            tier_emoji = "🏰"
        elif fortress_score >= 65:
            tier = "CASTLE"
            tier_emoji = "🛡️"
        elif fortress_score >= 50:
            tier = "HOUSE"
            tier_emoji = "🏠"
        elif fortress_score >= 30:
            tier = "SHACK"
            tier_emoji = "🏚️"
        else:
            tier = "RUBBLE"
            tier_emoji = "💀"
        
        # CPI Resilience assessment
        cpi_ready = (
            (roic is not None and roic >= 12)
            and (op_margin >= 15)
            and (debt_ebitda is not None and debt_ebitda <= 3)
            and (interest_cov is not None and interest_cov >= 5)
        )
        
        return {
            "ticker": ticker,
            "name": info.get("longName") or info.get("shortName") or ticker,
            "sector": info.get("sector", "Unknown"),
            "industry": info.get("industry", "Unknown"),
            "price": round(price, 2),
            "market_cap": market_cap,
            "market_cap_fmt": _fmt_cap(market_cap),
            # Core metrics
            "roic": round(roic, 1) if roic is not None else None,
            "roce": round(roce, 1) if roce is not None else None,  
            "roe": round(roe, 1) if roe else None,
            "fcf_yield": round(fcf_yield, 1) if fcf_yield is not None else None,
            "debt_ebitda": round(debt_ebitda, 1) if debt_ebitda is not None else None,
            "interest_coverage": round(interest_cov, 1) if interest_cov is not None else None,
            # Margins
            "gross_margin": round(gross_margin, 1),
            "op_margin": round(op_margin, 1),
            "profit_margin": round(profit_margin, 1),
            # Growth
            "rev_growth": round(rev_growth, 1),
            "earnings_growth": round(earnings_growth, 1),
            # Valuation
            "pe": round(pe, 1) if pe else None,
            "fwd_pe": round(fwd_pe, 1) if fwd_pe else None,
            "peg": round(peg, 2) if peg else None,
            "pb": round(pb, 2) if pb else None,
            # Shareholder return
            "div_yield": round(div_yield, 2) if div_yield else None,
            "payout_ratio": round(payout_ratio, 1) if payout_ratio else None,
            # Fortress scoring
            "scores": scores,
            "fortress_score": fortress_score,
            "tier": tier,
            "tier_emoji": tier_emoji,
            "cpi_ready": cpi_ready,
            # TV pre-screen data
            "perf_3m": (tv_data or {}).get("perf_3m"),
            "perf_1y": (tv_data or {}).get("perf_1y"),
            "rsi": (tv_data or {}).get("rsi"),
        }
        
    except Exception as e:
        return None


# ═══════════════════════════════════════════════════════════════════
# ████  OUTPUT FORMATTING  ████
# ═══════════════════════════════════════════════════════════════════

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


def _fmt_pct(val, plus_sign=True) -> str:
    if val is None:
        return "  N/A"
    sign = "+" if val >= 0 and plus_sign else ""
    return f"{sign}{val:.1f}%"


def _tier_color(tier: str) -> str:
    """ANSI color for tier."""
    colors = {
        "FORTRESS": "\033[96m",   # Cyan
        "CASTLE": "\033[92m",     # Green
        "HOUSE": "\033[93m",      # Yellow
        "SHACK": "\033[91m",      # Red
        "RUBBLE": "\033[31m",     # Dark red
    }
    return f"{colors.get(tier, '')}{tier}\033[0m"


def _score_bar(score: float, width: int = 20) -> str:
    """Visual score bar."""
    filled = int(score / 100 * width)
    empty = width - filled
    if score >= 80:
        color = "\033[96m"
    elif score >= 65:
        color = "\033[92m"
    elif score >= 50:
        color = "\033[93m"
    else:
        color = "\033[91m"
    return f"{color}{'█' * filled}{'░' * empty}\033[0m {score:.0f}"


def _format_result(r: dict, rank: int) -> str:
    """Format a single ticker result for terminal output."""
    name = r.get("name", r["ticker"])
    if len(name) > 28:
        name = name[:25] + "..."
    
    line1 = (f"  {rank:>2}. {r['tier_emoji']} {r['ticker']:<6} {name:<28} "
             f"│ {_tier_color(r['tier'])} ({r['fortress_score']}/100)")
    
    line2 = (f"       │ ROIC: {_fmt_pct(r['roic'], False):>7}  "
             f"FCF Yield: {_fmt_pct(r['fcf_yield'], False):>7}  "
             f"Debt/EBITDA: {r['debt_ebitda'] if r['debt_ebitda'] is not None else 'N/A':>5}x  "
             f"Int Cov: {r['interest_coverage'] if r['interest_coverage'] is not None else 'N/A':>5}x")
    
    line3 = (f"       │ Gross: {_fmt_pct(r['gross_margin'], False):>6}  "
             f"Op: {_fmt_pct(r['op_margin'], False):>6}  "
             f"Rev Grw: {_fmt_pct(r['rev_growth']):>7}  "
             f"P/E: {r['pe'] or 'N/A':>5}  "
             f"Cap: {r['market_cap_fmt']:>7}")
    
    # Score breakdown
    s = r["scores"]
    line4 = (f"       │ Axes: "
             f"R:{_score_bar(s['roic'], 8)} "
             f"F:{_score_bar(s['fcf'], 8)} "
             f"B:{_score_bar(s['balance_sheet'], 8)} "
             f"M:{_score_bar(s['margins'], 8)} "
             f"G:{_score_bar(s['growth'], 8)} "
             f"S:{_score_bar(s['shareholder_return'], 8)}")
    
    cpi_tag = " \033[96m⚡ CPI-READY\033[0m" if r.get("cpi_ready") else ""
    
    return f"{line1}{cpi_tag}\n{line2}\n{line3}\n{line4}"


def print_results(results: list[dict], scan_stats: dict, top_n: int = 50):
    """Print formatted fortress scanner output."""
    import random
    
    fortresses = [r for r in results if r["tier"] == "FORTRESS"]
    castles = [r for r in results if r["tier"] == "CASTLE"]
    houses = [r for r in results if r["tier"] == "HOUSE"]
    cpi_ready = [r for r in results if r.get("cpi_ready")]
    
    print(f"\n{'═'*78}")
    print(f"🏰 ROIC FORTRESS SCREENER — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"   📊 Universe: {scan_stats.get('total', 0)} stocks → "
          f"Filtered: {scan_stats.get('filtered', 0)} → "
          f"Deep scanned: {scan_stats.get('scanned', 0)}")
    print(f"{'═'*78}")
    
    # ── CPI Readiness Summary ──
    if cpi_ready:
        print(f"\n⚡ CPI-READY COMPANIES: {len(cpi_ready)} stocks can weather any macro number")
        print(f"   (ROIC≥12%, OpMargin≥15%, Debt/EBITDA≤3x, IntCov≥5x)\n")
    
    # ── Fortresses ──
    if fortresses:
        print(f"\n🏰 FORTRESS TIER (80-100) — {len(fortresses)} companies\n")
        for i, r in enumerate(fortresses[:top_n], 1):
            print(_format_result(r, i))
            print()
    else:
        print(f"\n💀 {random.choice(RUBBLE_QUOTES)}\n")
    
    # ── Castles ──
    if castles:
        castle_start = len(fortresses) + 1
        print(f"\n🛡️  CASTLE TIER (65-79) — {len(castles)} companies\n")
        for i, r in enumerate(castles[:max(0, top_n - len(fortresses))], castle_start):
            print(_format_result(r, i))
            print()
    
    # ── Sector Distribution ──
    sectors = {}
    for r in results:
        if r["fortress_score"] >= 65:  # Castle+ only
            s = r.get("sector", "Unknown")
            sectors[s] = sectors.get(s, 0) + 1
    
    if sectors:
        print(f"\n📊 Sector Distribution (Castle+ tier):")
        for s, count in sorted(sectors.items(), key=lambda x: -x[1]):
            bar = "█" * count
            print(f"   {s:<25} {bar} ({count})")
    
    # ── Stats summary ──
    print(f"\n{'═'*78}")
    print(f"   📈 Grade Distribution: "
          f"🏰 {len(fortresses)} Fortress  "
          f"🛡️ {len(castles)} Castle  "
          f"🏠 {len(houses)} House  "
          f"🏚️ {len([r for r in results if r['tier'] == 'SHACK'])} Shack  "
          f"💀 {len([r for r in results if r['tier'] == 'RUBBLE'])} Rubble")
    print(f"   ⚡ CPI-Ready: {len(cpi_ready)} companies")
    print(f"   ⏱  Scan time: {scan_stats.get('elapsed', 0):.1f}s")
    
    quote = random.choice(FORTRESS_QUOTES) if fortresses else random.choice(RUBBLE_QUOTES)
    print(f"\n   👻 Sam says: \"{quote}\"")
    print(f"{'═'*78}\n")


def output_json(results: list[dict], scan_stats: dict):
    """Machine-readable JSON output."""
    output = {
        "scan_date": datetime.now().isoformat(),
        "scan_stats": scan_stats,
        "total_scanned": len(results),
        "fortresses": [r for r in results if r["tier"] == "FORTRESS"],
        "castles": [r for r in results if r["tier"] == "CASTLE"],
        "cpi_ready": [r for r in results if r.get("cpi_ready")],
        "all_results": results,
    }
    print(json.dumps(output, indent=2, default=str))


def _save_csv(results: list[dict], filepath: str):
    """Save results to CSV."""
    import csv
    rows = []
    for r in results:
        rows.append({
            "ticker": r["ticker"],
            "name": r.get("name", ""),
            "sector": r.get("sector", ""),
            "industry": r.get("industry", ""),
            "price": r.get("price"),
            "market_cap": r.get("market_cap"),
            "fortress_score": r.get("fortress_score"),
            "tier": r.get("tier"),
            "cpi_ready": r.get("cpi_ready"),
            "roic": r.get("roic"),
            "roce": r.get("roce"),
            "roe": r.get("roe"),
            "fcf_yield": r.get("fcf_yield"),
            "debt_ebitda": r.get("debt_ebitda"),
            "interest_coverage": r.get("interest_coverage"),
            "gross_margin": r.get("gross_margin"),
            "op_margin": r.get("op_margin"),
            "profit_margin": r.get("profit_margin"),
            "rev_growth": r.get("rev_growth"),
            "earnings_growth": r.get("earnings_growth"),
            "pe": r.get("pe"),
            "fwd_pe": r.get("fwd_pe"),
            "peg": r.get("peg"),
            "pb": r.get("pb"),
            "div_yield": r.get("div_yield"),
            "payout_ratio": r.get("payout_ratio"),
        })
    if rows:
        with open(filepath, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        print(f"💾 Saved {len(rows)} results to {filepath}")


def _save_api_output(results: list[dict], scan_stats: dict):
    """Save output for the docs/api pipeline."""
    output_dir = PROJECT_ROOT / "docs" / "api" / "fortress"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    payload = {
        "scan_date": datetime.now().isoformat(),
        "scan_stats": scan_stats,
        "results": results[:100],  # Top 100
    }
    
    with open(output_dir / "latest.json", "w") as f:
        json.dump(payload, f, indent=2, default=str)
    
    print(f"📡 API output saved to {output_dir / 'latest.json'}")


def _parse_cap_string(s: str) -> float:
    """Parse market cap string like '2B', '10B', '500M'."""
    s = s.strip().upper().replace("$", "").replace(",", "")
    try:
        if s.endswith("T"):
            return float(s[:-1]) * 1e12
        elif s.endswith("B"):
            return float(s[:-1]) * 1e9
        elif s.endswith("M"):
            return float(s[:-1]) * 1e6
        elif s.endswith("K"):
            return float(s[:-1]) * 1e3
        else:
            return float(s)
    except (ValueError, TypeError):
        return 2_000_000_000  # Default $2B


# ═══════════════════════════════════════════════════════════════════
# ████  CLI MAIN  ████
# ═══════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="🏰 ROIC Fortress Screener — Quality-first stock scanner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Full market scan:           python -m dossier.roic_fortress_screener
  Specific tickers:           python -m dossier.roic_fortress_screener --tickers AAPL,MSFT,GOOGL
  Technology sector:          python -m dossier.roic_fortress_screener --sector Technology
  Large caps only:            python -m dossier.roic_fortress_screener --min-cap 50B
  Top 15 results:             python -m dossier.roic_fortress_screener --top 15
  JSON output:                python -m dossier.roic_fortress_screener --json
  Save CSV:                   python -m dossier.roic_fortress_screener --csv fortress.csv
        """,
    )
    parser.add_argument("--tickers", type=str, help="Comma-separated tickers (skip universe)")
    parser.add_argument("--sector", type=str, help="Filter by sector (e.g., Technology, Healthcare)")
    parser.add_argument("--min-cap", type=str, default="2B", help="Minimum market cap (default: 2B)")
    parser.add_argument("--top", type=int, default=50, help="Show top N results (default: 50)")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--csv", type=str, help="Save results to CSV file")
    parser.add_argument("--cpi-only", action="store_true", help="Show only CPI-ready companies")
    args = parser.parse_args()
    
    t0 = time.time()
    scan_stats = {"total": 0, "filtered": 0, "scanned": 0}
    
    min_cap = _parse_cap_string(args.min_cap)
    
    if args.tickers:
        # ── Direct ticker list ──
        tickers_to_scan = [t.strip().upper() for t in args.tickers.split(",")]
        tv_lookup = {}
        scan_stats = {"total": len(tickers_to_scan), "filtered": len(tickers_to_scan), 
                      "scanned": 0, "mode": "direct"}
        print(f"🏰 Direct fortress scan: {len(tickers_to_scan)} tickers\n")
    else:
        # ── Full market scan via TradingView ──
        print("🏰 FORTRESS SCAN — Loading profitable US equities...\n")
        
        print(f"  ⚡ Stage 1: TradingView bulk API (MCap ≥ {_fmt_cap(min_cap)})...")
        raw_stocks = _tv_fetch_universe(min_cap)
        scan_stats["total"] = len(raw_stocks)
        print(f"     → {len(raw_stocks)} profitable stocks loaded\n")
        
        print("  🔍 Stage 2: Quality pre-filter...")
        survivors = quality_prefilter(raw_stocks, sector_filter=args.sector)
        scan_stats["filtered"] = len(survivors)
        scan_stats["mode"] = "market"
        
        tickers_to_scan = [s["ticker"] for s in survivors]
        tv_lookup = {s["ticker"]: s for s in survivors}
    
    # ── Stage 3: Deep fundamental scan ──
    print(f"  🧪 Stage 3: Deep fundamental scan ({len(tickers_to_scan)} tickers)...")
    results = []
    errors = 0
    batch_size = 25
    
    for i, ticker in enumerate(tickers_to_scan):
        pct = (i + 1) / len(tickers_to_scan) * 100
        print(f"\r     [{i+1}/{len(tickers_to_scan)}] {ticker:<6} ({pct:.0f}%)", end="", flush=True)
        result = deep_scan_fundamentals(ticker, tv_lookup.get(ticker))
        if result:
            results.append(result)
        else:
            errors += 1
        
        # Be nice to yfinance
        if (i + 1) % batch_size == 0 and i + 1 < len(tickers_to_scan):
            time.sleep(0.3)
    
    print(f"\r     ✅ Scanned {len(results)} tickers ({errors} errors)" + " " * 30)
    
    elapsed = time.time() - t0
    scan_stats["scanned"] = len(results)
    scan_stats["errors"] = errors
    scan_stats["elapsed"] = round(elapsed, 1)
    
    if not results:
        print("\n❌ No valid results. Check your filter settings.")
        return
    
    # Sort by fortress score
    results.sort(key=lambda x: x["fortress_score"], reverse=True)
    
    # CPI-only filter
    if args.cpi_only:
        results = [r for r in results if r.get("cpi_ready")]
        if not results:
            print("\n❌ No CPI-ready companies found with current filters.")
            return
    
    if args.json:
        output_json(results, scan_stats)
    else:
        print_results(results, scan_stats, top_n=args.top)
    
    if args.csv:
        _save_csv(results, args.csv)
    
    _save_api_output(results, scan_stats)


if __name__ == "__main__":
    main()
