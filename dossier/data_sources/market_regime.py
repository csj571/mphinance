"""
Market Regime Detection — VIX + Sector Rotation + Breadth.

Determines the current market environment for tactical positioning.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from dossier.config import VIX_REGIMES, SECTOR_ETFS


def detect_vix_regime() -> dict:
    """Fetch VIX level and classify the current market regime."""
    print("  Detecting VIX regime...")
    try:
        vix = yf.Ticker("^VIX")
        hist = vix.history(period="5d")
        if hist.empty:
            return {"vix_level": 0, "regime_name": "Unknown", "regime_desc": "No VIX data"}

        vix_level = round(float(hist["Close"].iloc[-1]), 2)

        regime_name = "Unknown"
        regime_desc = ""
        for key, regime in VIX_REGIMES.items():
            if vix_level < regime["max"]:
                regime_name = regime["name"]
                regime_desc = regime["desc"]
                break

        return {
            "vix_level": vix_level,
            "regime_name": regime_name,
            "regime_desc": regime_desc,
        }
    except Exception as e:
        print(f"  [WARN] VIX fetch failed: {e}")
        return {"vix_level": 0, "regime_name": "Unknown", "regime_desc": str(e)}


def get_sector_rotation() -> list[dict]:
    """Fetch sector ETF performance across 1d, 5d, 20d timeframes."""
    print("  Fetching sector rotation data...")
    results = []

    for etf in SECTOR_ETFS:
        try:
            ticker = yf.Ticker(etf)
            hist = ticker.history(period="1mo")
            if hist.empty or len(hist) < 2:
                continue

            close = hist["Close"]
            current = float(close.iloc[-1])

            pct_1d = round(((current / float(close.iloc[-2])) - 1) * 100, 2) if len(close) >= 2 else 0
            pct_5d = round(((current / float(close.iloc[-min(5, len(close))])) - 1) * 100, 2) if len(close) >= 5 else 0
            pct_20d = round(((current / float(close.iloc[0])) - 1) * 100, 2)

            results.append({
                "sector": etf,
                "1d": pct_1d,
                "5d": pct_5d,
                "20d": pct_20d,
            })
        except Exception as e:
            print(f"  [WARN] Failed to fetch {etf}: {e}")
            continue

    results.sort(key=lambda x: x["5d"], reverse=True)
    return results


def fetch_market_breadth() -> dict:
    """
    Market breadth indicators using S&P 500 proxy.

    Calculates:
    - % of major ETFs above their 200-day SMA (proxy for market breadth)
    - Advance/decline ratio from sector performance
    - Composite breadth score (0-100)
    """
    print("  Calculating market breadth...")

    # Use a basket of 20 representative large-cap stocks + sector ETFs as breadth proxy
    # (fetching all 500 S&P stocks would be too slow for a daily pipeline)
    breadth_basket = [
        "SPY", "QQQ", "IWM", "DIA",  # Major indices
        "XLK", "XLF", "XLE", "XLV", "XLI", "XLC", "XLY", "XLP", "XLU", "XLB", "XLRE",  # Sectors
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA",  # Mega caps
    ]

    above_200sma = 0
    above_50sma = 0
    total_checked = 0
    advancing = 0
    declining = 0

    for symbol in breadth_basket:
        try:
            hist = yf.Ticker(symbol).history(period="1y")
            if hist.empty or len(hist) < 50:
                continue

            close = hist["Close"]
            current = float(close.iloc[-1])
            total_checked += 1

            # Above 200 SMA?
            if len(close) >= 200:
                sma200 = float(close.rolling(200).mean().iloc[-1])
                if current > sma200:
                    above_200sma += 1

            # Above 50 SMA?
            sma50 = float(close.rolling(50).mean().iloc[-1])
            if current > sma50:
                above_50sma += 1

            # Advancing vs declining (5-day return)
            if len(close) >= 5:
                ret_5d = (current / float(close.iloc[-5])) - 1
                if ret_5d > 0:
                    advancing += 1
                else:
                    declining += 1

        except Exception:
            continue

    if total_checked == 0:
        return {
            "pct_above_200sma": 0,
            "pct_above_50sma": 0,
            "advance_decline_ratio": 1.0,
            "breadth_score": 50,
            "breadth_label": "Neutral",
            "total_checked": 0,
        }

    pct_200 = round(above_200sma / total_checked * 100, 1)
    pct_50 = round(above_50sma / total_checked * 100, 1)
    ad_ratio = round(advancing / max(declining, 1), 2)

    # Composite breadth score (0-100)
    # Weighted: 40% above-200SMA, 30% above-50SMA, 30% A/D ratio (capped at 2.0)
    score = (pct_200 * 0.4) + (pct_50 * 0.3) + (min(ad_ratio, 2.0) / 2.0 * 100 * 0.3)
    score = round(min(100, max(0, score)), 1)

    if score >= 70:
        label = "Strong"
    elif score >= 50:
        label = "Neutral"
    elif score >= 30:
        label = "Weak"
    else:
        label = "Bearish"

    return {
        "pct_above_200sma": pct_200,
        "pct_above_50sma": pct_50,
        "advance_decline_ratio": ad_ratio,
        "breadth_score": score,
        "breadth_label": label,
        "total_checked": total_checked,
    }


def fetch_market_regime() -> dict:
    """Main entry point: get full market regime data."""
    vix = detect_vix_regime()
    sectors = get_sector_rotation()
    breadth = fetch_market_breadth()

    return {
        "vix": vix,
        "sector_rotation": sectors,
        "sector_leaders": [s["sector"] for s in sectors[:3]],
        "sector_laggards": [s["sector"] for s in sectors[-3:]],
        "breadth": breadth,
    }

