# Momentum Phinance - Strategy Technical Specification

**Version:** 1.0  
**Date:** 2026-02-02  
**Purpose:** Technical handoff documentation for analysis and implementation of trading strategies.

---

## 1. System Architecture

The scanning system allows for modular strategy execution, driven by a central orchestrator (`batch_scanner.py` or the web UI).

*   **Orchestrator**: `batch_scanner.py`
    *   **Role**: Loads strategy modules, executes queries, manages results, and handles output (Google Sheets, Discord).
    *   **Configuration**: uses `strategies/__init__.py` to dynamically load strategy classes.
*   **Strategy Modules**: Located in `strategies/` directory.
    *   **Interface**: Each strategy inherits from `BaseStrategy` and implements:
        *   `build_query(params)`: Constructs the JSON query for the data provider (TradingView/Scanner).
        *   `post_process(df, params)`: Applies local Python logic, filters, and computed columns.
    *   **Data Flow**: Query -> Raw Data (DataFrame) -> Post-Processing -> Final Results.

### Core Libraries & Dependencies
*   **`pandas`**: Data manipulation and technical indicator calculation.
*   **`scipy`**: Advanced statistical calculations (e.g., linear regression for slopes).
*   **`yfinance`**: Validating data, fetching option chains, and getting additional fundamental data.
*   **`requests`**: HTTP requests to data providers and webhooks.

---

## 2. Strategy Breakdown

### A. Momentum with Pullback
*   **File**: `strategies/momentum.py`
*   **Concept**: Catch strong trends during a temporary weakness (pullback).
*   **Scan Logic (TradingView Query)**:
    *   **Universe**: US Market, Common Stock.
    *   **Price**: Close > EMA(50).
    *   **Trend**: EMA(8) > EMA(21) (Short-term trend is up).
    *   **Pullback**: High > EMA(8) AND Low < EMA(8) (Price is interacting with the 8-day moving average).
    *   **Volatility**: ADX(14) > 20 (Trend strength).
    *   **Momentum**: Stochastic %K(14, 3, 3) < 40 (Oversold condition in an uptrend).
*   **Post-Processing**:
    *   **Squeeze Check**: Calculates `SqueezeRatio` = ATR(14) / (ATR(55) / 2). If < 0.85, flagged as "Squeezed".
    *   **ATR Filter**: Rejects if price is too far extended (> 1 ATR from EMA8).

### B. Volatility Squeeze
*   **File**: `strategies/volatility_squeeze.py`
*   **Concept**: Identify periods of low volatility (coiling) that often precede explosive moves. Uses Keltner Channels inside Bollinger Bands logic.
*   **Scan Logic**:
    *   **Universe**: US Market, Common Stock.
    *   **Volatility**: ADX(14) < 30 (Trend is dormant/choppy).
    *   **Proximity**: Close is within 2.5% of EMA(20) (Price is tightening).
    *   **Volume**: Relative Volume > 0.5 (Not completely dead).
*   **Post-Processing**:
    *   **Squeeze Metric**: `SqueezeRatio` calculation (Custom implementation of BB/KC relationship).
    *   **Signal Grading**:
        *   **🔋 Deep Squeeze**: Ratio < 0.70 (High potential energy).
        *   **⚡ Mid Squeeze**: Ratio 0.70 - 0.85.
        *   **Loose**: Ratio > 0.85 (Filtered out).
    *   **Exclusion**: Removes stocks > 30% below 52-week high (avoids broken charts).

### C. Gamma Scan(Options Flow)
*   **File**: `strategies/gamma_scan.py`
*   **Concept**: Finds stocks where option market makers (dealers) are "pinned" or have significant exposure.
*   **Scan Logic**:
    *   **Source**: Filters for stocks with high option volume or specific technical setups.
*   **Post-Processing (Heavy)**:
    *   **Option Chain Fetch**: Uses `yfinance` to pull full option chains for nearest expirations.
    *   **Greeks Calculation**: Estimates Gamma Exposure (GEX) profiles (if data available).
    *   **Wall Detection**: Identifies "Call Walls" (Strike with max open interest) and "Put Walls".
    *   **Pinning**: Calculates distance from price to the "Wall". If < 1% away, flagged as "Pinned".

### D. Gravity Squeeze
*   **File**: `strategies/gravity_squeeze.py`
*   **Concept**: Combines "Gravity" (high volume, low price movement) with volatility compression (Squeeze). Buying pressure is disguised as accumulation.
*   **Scan Logic**:
    *   **Pattern**: Custom "Gravity" filter (Volume / High-Low Range). High ratio = hidden accumulation.
    *   **Technical**: Close > EMA(21).
*   **Post-Processing**:
    *   **Gravity Anomaly**: z-score of the Volume/Range ratio. High score > 2.0 = Significant anomaly.
    *   **Candle Sparks**: Detects long lower wicks (rejection of lows) combined with squeeze metrics.

### E. Coiled Springs (Advanced)
*   **File**: `strategies/coiled_springs.py`
*   **Concept**: A multi-factor grading system for breakout candidates.
*   **Scan Logic**: Broad filter for consolidation patterns.
*   **Post-Processing (Scoring System)**:
    *   **Score Categories (0-100 pts)**:
        *   **Tightness**: 30pts (Based on Bollinger Band Width).
        *   **Trend**: 20pts (Location relative to major EMAs).
        *   **Volume**: 20pts (Accumulation/Distribution signs).
        *   **Momentum**: 30pts (RSI/MACD positioning).
    *   **Output**: Ranks stocks by "Coil Score". Grades A (>80) to F (<50).

### F. Small Cap Multibaggers (Fundamental)
*   **File**: `strategies/small_cap_multibaggers.py`
*   **Concept**: Fundamental growth screen for small caps.
*   **Scan Logic**:
    *   **Market Cap**: $50M - $2B.
    *   **Growth**: Revenue Growth > 30% YoY.
    *   **Profitability**: Gross Margin > 40%.
    *   **Value**: Price/Sales < 10 (Avoid overvalued hype).

### G. Cash Secured Puts (The Wheel)
*   **File**: `strategies/cash_secured_puts.py`
*   **Concept**: Finds income-generating option setups (selling puts) on bullish trends.
*   **Scan Logic**:
    *   **Trend**: Super bullish (EMA8 > EMA21 > EMA50).
    *   **Safety**: RSI < 70 (Not overbought yet).
*   **Post-Processing**:
    *   **Chain Analysis**: Fetches option chain.
    *   **Strike Selection**: Finds strikes at delta ~0.30 or Support levels (EMA50).
    *   **Yield Calc**: Annualized Return on Capital (ROC) > 15%.
    *   **Filter**: Ensures no earnings event in next 7 days.

### H. MEME Screen
*   **File**: `strategies/meme_scanner.py`
*   **Concept**: High social sentiment/High volatility plays.
*   **Scan Logic**:
    *   **Volume**: Relative Volume > 3.0 (3x normal volume).
    *   **Volatility**: IV Rank > 50.
*   **Post-Processing**:
    *   Sorts purely by Implied Volatility (IV) and Volume Velocity. "Dangerous" scanner.

---

## 3. Key Computed Fields (Glossary)

*   **`SqueezeRatio`**: `ATR(14) / (ATR(55) / 2)`.
    *   Logic: Keltner Channels (ATR based) are normally wider than Bollinger Bands (StdDev based). When KCs go *inside* BBs, volatility is compressed.
*   **`Gravity`**: `Volume / (High - Low)`.
    *   Logic: Millions of shares traded but price didn't move? Someone absorbed all that liquidity.
*   **`Relative Volume (RVOL)`**: `Current Volume / Average Volume(20)`.
*   **`TopWall`**: Strike price with the highest call Open Interest. Acts as a magnet or resistance.

---

## 4. Usage Data & Export

All strategies export data in a standardized JSON format compatible with:
1.  **Google Sheets**: Via Apps Script Webhook (automatically creates tabs).
2.  **Discord**: Formatted embeds with charts/tables.
3.  **Local CSV**: For backtesting or import into other tools.
