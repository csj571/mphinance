"""
Market Pulse — Quick snapshot of major benchmarks.

Fetches current price, daily change, and key metrics for SPY, QQQ, BTC, ETH, etc.
"""

import yfinance as yf
from dossier.config import MARKET_PULSE
from dossier.utils.retry import retry


@retry(max_retries=2, initial_delay=1.5)
def _fetch_ticker_data(symbol: str) -> dict:
    """Fetch price data for a single ticker with retry."""
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period="5d")
    if hist.empty or len(hist) < 2:
        raise ValueError(f"Insufficient data for {symbol}")

    latest = float(hist["Close"].iloc[-1])
    prev = float(hist["Close"].iloc[-2])
    change = latest - prev
    pct = (change / prev) * 100

    first = float(hist["Close"].iloc[0])
    trend_5d = ((latest - first) / first) * 100

    name_map = {
        "SPY": "S&P 500", "QQQ": "Nasdaq 100", "IWM": "Russell 2000",
        "DIA": "Dow 30", "BTC-USD": "Bitcoin", "ETH-USD": "Ethereum",
        "GLD": "Gold", "TLT": "20Y Treasuries",
    }

    return {
        "symbol": symbol,
        "name": name_map.get(symbol, symbol),
        "price": round(latest, 2),
        "change": round(change, 2),
        "pct_change": round(pct, 2),
        "change_pct": round(pct, 2),
        "trend_5d": round(trend_5d, 2),
        "is_up": change >= 0,
    }


def fetch_market_pulse() -> list[dict]:
    """Fetch quick price data for all market pulse benchmarks."""
    print("  Fetching market pulse data...")
    results = []

    for symbol in MARKET_PULSE:
        try:
            data = _fetch_ticker_data(symbol)
            results.append(data)
        except Exception as e:
            print(f"    [WARN] Failed to fetch {symbol} after retries: {e}")
            continue

    return results
