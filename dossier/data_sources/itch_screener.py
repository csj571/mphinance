#!/usr/bin/env python3
"""
Itch Slot Screener (REX / Roundhill)

Scans the universe of underlying stocks for single-stock income ETFs.
Grades them based on momentum, relative strength, and trend.
Helps answer "which Itch Slot ETF should I buy this month?"
"""

import math
from datetime import datetime
import pandas as pd
import yfinance as yf

# Map of underlying -> (REX ticker, Roundhill ticker)
# If a ticker isn't available in one family, it's None.
ITCH_UNIVERSE = {
    "NVDA": ("NVII", "NVDW"),
    "TSLA": ("TSII", "TSLW"),
    "PLTR": ("PLTI", "PLTW"),
    "COIN": ("COII", "COIW"),
    "LLY":  ("LLII", None),
    "HOOD": ("HOII", "HOOW"),
    "WMT":  ("WMTI", None),
    "MSTR": ("MSII", "MSTW"),
    "CRWV": ("CWII", None),
    "AAPL": (None, "AAPW"),
    "AMD":  (None, "AMDW"),
    "AMZN": (None, "AMZW"),
    "ARM":  (None, "ARMW"),
    "AVGO": (None, "AVGW"),
    "BABA": (None, "BABW"),
    "BRK-B": (None, "BRKW"), # yfinance uses BRK-B instead of BRK.B
    "COST": (None, "COSW"),
    "GOOGL": (None, "GOOW"),
    "META": (None, "METW"),
    "MSFT": (None, "MSFW"),
    "NFLX": (None, "NFLW"),
    "UBER": (None, "UBEW"),
    "UNH":  (None, "UNHW"),
}

def calculate_rsi(prices, period=14):
    if len(prices) < period + 1:
        return 50.0
    deltas = prices.diff().dropna()
    gains = deltas.clip(lower=0)
    losses = -1 * deltas.clip(upper=0)
    
    # Simple moving average for regular RSI
    avg_gain = gains.rolling(window=period, min_periods=period).mean()
    avg_loss = losses.rolling(window=period, min_periods=period).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1] if not rsi.empty and not pd.isna(rsi.iloc[-1]) else 50.0

def score_underlying(ticker: str) -> dict:
    df = yf.Ticker(ticker).history(period="1y")
    if df.empty or len(df) < 20:
        return None
    
    current = df["Close"].iloc[-1]
    high_52w = df["High"].max()
    low_52w = df["Low"].min()
    
    # 1. Relative Strength (where is it in 52wk range?) (0-100)
    range_52 = high_52w - low_52w
    rel_str = ((current - low_52w) / range_52 * 100) if range_52 > 0 else 50
    
    # 2. Distance from High (penalty for deep drawdowns)
    off_high_pct = ((current - high_52w) / high_52w) * 100
    
    # 3. Simple Momentum (20-day return)
    price_20d_ago = df["Close"].iloc[-20] if len(df) >= 20 else df["Close"].iloc[0]
    mom_20d = ((current - price_20d_ago) / price_20d_ago) * 100
    
    # 4. RSI (14)
    rsi = calculate_rsi(df["Close"])
    
    # Grade Calculation (Max 100)
    # We want: strong relative strength, positive momentum, not overly extended (RSI < 80)
    score = 0
    
    # Rel Str (Up to 40 pts)
    score += min(rel_str * 0.4, 40)
    
    # Off High (Up to 30 pts) - 0% off = 30 pts, -30% off = 0 pts
    off_high_score = max(30 + off_high_pct, 0) # off_high_pct is negative
    score += off_high_score
    
    # Momentum (Up to 20 pts)
    if mom_20d > 10: score += 20
    elif mom_20d > 5: score += 15
    elif mom_20d > 0: score += 10
    
    # RSI (Up to 10 pts)
    if 50 <= rsi <= 75: score += 10
    elif rsi > 75: score += 5 # Overbought penalty
    elif rsi > 40: score += 5
    
    # Assign Grade
    if score >= 85: grade = "A"
    elif score >= 70: grade = "B"
    elif score >= 50: grade = "C"
    else: grade = "D"
    
    # Which structure to pick?
    # Trending / High Conviction -> REX (Growth + Income)
    # Choppy / Sideways -> Roundhill (Max Income via Swaps)
    # If RSI > 60 and Mom > 5% -> Trending
    regime = "TRENDING" if (rsi > 55 and mom_20d > 2) else "CHOP/DOWN"
    
    rex_t, rnd_t = ITCH_UNIVERSE[ticker]
    
    if regime == "TRENDING" and rex_t:
        recommended = f"REX ({rex_t})"
    elif rnd_t:
        recommended = f"Roundhill ({rnd_t})"
    elif rex_t:
        recommended = f"REX ({rex_t})" # Fallback
    else:
        recommended = "None"
        
    # Check for earnings within 7 days (simplified using upcoming week approximation, skipping actual API for speed)
    # In live we'd check tradier earnings
        
    return {
        "ticker": ticker,
        "price": current,
        "rel_str": rel_str,
        "off_high": off_high_pct,
        "mom_20d": mom_20d,
        "rsi": rsi,
        "score": score,
        "grade": grade,
        "regime": regime,
        "recommended": recommended,
        "options": (rex_t, rnd_t)
    }

def main():
    print("Scraping universe...")
    results = []
    
    import warnings
    warnings.filterwarnings('ignore')
    
    for t in ITCH_UNIVERSE.keys():
        s = score_underlying(t)
        if s:
            results.append(s)
            
    # Sort by score desc
    results.sort(key=lambda x: x["score"], reverse=True)
    
    print("\n" + "="*95)
    print(" 🛠️  THE ITCH SLOT SCREENER  🛠️ ")
    print("="*95)
    print(f"{'TICKER':<7} {'PRICE':>8} {'SCORE':>6} {'GRADE':>5} {'REL_STR':>7} {'OFF_HI':>8} {'MOM(20d)':>9} {'RSI':>6} {'REGIME':>10}  {'SELECTION'}")
    print("-" * 95)
    
    for r in results:
        g = r["grade"]
        if g == "A": gc = "🟢"
        elif g == "B": gc = "🔵"
        elif g == "C": gc = "🟡"
        else: gc = "🔴"
            
        print(f"{r['ticker']:<7} ${r['price']:>7.2f} {r['score']:>6.1f} {gc}{g:>2} {r['rel_str']:>6.1f}% {r['off_high']:>7.1f}% {r['mom_20d']:>8.1f}% {r['rsi']:>6.1f} {r['regime']:>10}  {r['recommended']}")

if __name__ == "__main__":
    main()
