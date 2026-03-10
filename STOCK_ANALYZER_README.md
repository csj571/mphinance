# Stock Analyzer

ML-powered stock analysis module providing price predictions and market insights for the Single Ticker Audit view.

## Overview

Uses **Random Forest Regression** with technical indicators to:
- Predict price ranges (5-day horizon)
- Generate AI-powered market analysis
- Calculate feature importance for transparency

---

## Files

| File | Purpose |
|------|---------|
| `stock_analyzer.py` | Core ML prediction and analysis logic |
| Used by `main.py` | Called in `render_audit_view()` for Single Ticker Audit |

---

## Class: `StockAnalyzer`

### Usage

```python
from stock_analyzer import StockAnalyzer, generate_market_analysis

analyzer = StockAnalyzer()

# 1. Calculate technical indicators
data = analyzer.calculate_technical_indicators(ohlcv_df)

# 2. Train prediction model
model_info = analyzer.train_prediction_model(data, horizon=5)

# 3. Get price prediction
prediction = analyzer.predict_price_range(model_info, current_price=150.0)
# Returns: {'expected': 152.3, 'low': 148.5, 'high': 156.1, 'confidence': 0.72, ...}

# 4. Generate market analysis
insights = generate_market_analysis(data, ticker="AAPL")
# Returns: ["🟢 AAPL demonstrates strong upward movement (+1.25%)", ...]
```

---

## Technical Indicators Calculated

| Category | Indicators |
|----------|------------|
| **Moving Averages** | SMA(20), SMA(50), EMA(12), EMA(26) |
| **Momentum** | RSI(14), MACD, MACD Signal, MACD Histogram |
| **Volatility** | Bollinger Bands (20,2), ATR(14) |
| **Volume** | Volume SMA(20), Volume Ratio |
| **Oscillators** | Stochastic %K, %D |

---

## ML Features

The model uses these feature categories:
- **Lag Features**: Close, Volume, Returns (1, 2, 3, 5 days back)
- **Rolling Stats**: Mean/Std over 5, 10, 20 days
- **Position Features**: Price vs SMA20, Price vs SMA50
- **Volatility**: 10-day and 20-day return volatility

### Minimum Data Requirements
- **50 bars** minimum for training
- **30 bars** minimum after train/test split

---

## Prediction Output

```python
{
    'expected': 152.30,        # Mean prediction from all trees
    'low': 148.50,             # 1 std dev below
    'high': 156.10,            # 1 std dev above
    'expected_change_pct': 1.53,
    'low_change_pct': -0.99,
    'high_change_pct': 4.07,
    'confidence': 0.72,        # 0-1, inverse of relative uncertainty
    'horizon': 5               # Days ahead
}
```

---

## Market Analysis Output

The `generate_market_analysis()` function returns a list of emoji-annotated insights:

```
🚀 AAPL shows exceptional bullish momentum with a 3.45% surge
📈 Strong bullish alignment - price above both 20 and 50-day MAs
💡 RSI at 28.5 suggests oversold conditions - potential buying opportunity
⚡ MACD bullish crossover - momentum improving
🔥 Exceptional volume surge confirms strong conviction
```

### Insight Categories
- **Price Movement**: Bullish/bearish based on % change
- **RSI Status**: Overbought/oversold signals
- **MA Alignment**: Trend direction confirmation
- **Bollinger Bands**: Price extremes detection
- **MACD**: Momentum direction and crossovers
- **Volume**: Conviction strength

---

## Integration in UI

In `main.py` → `render_audit_view()`:

1. Fetches 6 months of daily data from yfinance
2. Calculates technical indicators
3. Trains prediction model (if enough data)
4. Displays prediction card with Low/Expected/High
5. Shows AI market insights panel
