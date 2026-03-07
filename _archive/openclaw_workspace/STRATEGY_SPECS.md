# OpenClaw Strategy Manifesto
## Technical Functionality & Requirements

This document details the exact technical logic, indicators, and scan parameters for the 12 core Momentum Phinance strategies being ported to OpenClaw.

---

## 1. Momentum Strategies

### Momentum with Pullback
**Goal:** Find strong trends (TAO Stack) currently pausing or pulling back.
- **Scanner Logic:**
  - **TAO Stack:** EMA 8 > 21 > 34 > 55 > 89 (Daily, Weekly, Monthly alignment preferred).
  - **Trend Strength:** ADX between 20 and 100.
  - **Pullback:** Price > EMA 21 but close to it (within 1 ATR).
  - **Uptrend Floor:** SMA 50 > EMA 200.
- **Key Indicators:** EMA (8, 21, 34, 55, 89), ADX, ATR.

### EMA Cross Momentum
**Goal:** Catch the beginning of a new trend leg.
- **Scanner Logic:**
  - **Signal:** EMA 8 crosses ABOVE EMA 34.
  - **Freshness:** "Cross Spread" (distance between 8/34) must be < 2%.
  - **Validation:** Rel Vol > 1.2, ADX > 20.
  - **Context:** Price > EMA 200.
- **Key Indicators:** EMA (8, 34, 200), Rel Vol.

### Gamma Scan
**Goal:** Identify momentum stocks approaching high Open Interest (OI) options levels ("Gamma Walls").
- **Scanner Logic:**
  - **Base:** Strong Momemtum (TAO Stack + ADX > 15).
  - **Gamma Filter:** Price is within 2% of a major OI strike (>1000 OI).
  - **Execution:** Checks nearby calls/puts for "Magnets" or "Resistance".
- **Key Indicators:** Options Chain (OI, Strikes), TAO Stack.

---

## 2. Volatility Strategies

### Volatility Squeeze ("The Snap")
**Goal:** Detect expansion from a period of low volatility compression.
- **Scanner Logic:**
  - **Compression:** Normalized ATR (NATR) Fast EMA(8) < Slow EMA(34) for 5+ days.
  - **The Snap:** Fast EMA crosses ABOVE Slow EMA (Volatility expansion).
  - **Trend:** Price > EMA 34 (uptrending).
- **Key Indicators:** NATR, EMA(8) of NATR, EMA(34) of NATR.

### Gravity Squeeze
**Goal:** Find hidden accumulation (high volume, low price movement).
- **Scanner Logic:**
  - **Squeeze Ratio:** Daily ATR < (Weekly ATR / 2) -> "Coiling".
  - **Gravity Anomaly:** High Volume / Small Price Range.
  - **Sparks:** Hammers, Dojis, or "Gravity Coils" (RVOL > 1.5 with < 2% range).
- **Key Indicators:** ATR (D/W), Volume, OHLC patterns.

### Gravity Well
**Goal:** Specific watchlist monitor for "Coiled Springs".
- **Scanner Logic:**
  - **Bollinger Squeeze:** Bandwidth is tight (< 10-15%).
  - **Gravity Score:** Abnormal volume density in the squeeze.
- **Target List:** Specific tickers (STKH, DNN, RGTI, etc.) or broader search.

### Retail Whiff
**Goal:** Identify Small/Micro-caps coiling or exploding.
- **Scanner Logic:**
  - **Universe:** Market Cap < $2B, Price < $20.
  - **Coil:** Bollinger Bandwidth < 15% AND Squeeze Ratio < 0.65.
  - **Whiff (Explosion):** RVOL > 2.5 OR (RVOL > 1.5 + Price > 5%).
- **Key Indicators:** Bollinger Bands, RVOL, Small Cap filters.

---

## 3. Reversion & Shorting

### Bearish EMA Cross (Down)
**Goal:** Catch the start of a downtrend.
- **Scanner Logic:**
  - **Signal:** EMA 8 crosses BELOW EMA 34.
  - **Freshness:** Cross Spread < 2%.
  - **Validation:** Price < EMA 200, Stoch K > 50 (Not oversold yet).
- **Key Indicators:** EMA (8, 34, 200), Stochastic.

---

## 4. Fundamental & Income

### Small Cap Multibaggers
**Goal:** High-quality growth small caps.
- **Scanner Logic:**
  - **Cap:** $10M - $1B.
  - **Growth:** Revenue Growth (YoY) > 15%.
  - **Health:** Gross Margin 30-100%, Positive FCF, Positive EBITDA.
  - **Leverage:** Net Debt / EBITDA between 0x and 2x.

### Cash Secured Puts (CSP)
**Goal:** Safe income on quality stocks.
- **Scanner Logic:**
  - **Funnel 1 (Sweep):** Price > $5, ADX < 45 (No crash), RSI 30-70.
  - **Funnel 2 (Logic):** Price within 1 ATR of EMA 20 (Mean reversion check).
  - **Funnel 3 (Deep Dive):**
    - Sell Puts 10% OTM.
    - Check for > 1% Return on Capital (Weekly annualized).
    - Ensure option liquidity.

### MEME Screen
**Goal:** High Volatility / High Volume speculative plays.
- **Scanner Logic:**
  - **Step 1:** Top 200 stocks by Volume.
  - **Step 2:** Sort by Implied Volatility (IV) descending.
  - **Step 3:** Take top 30.
- **Key Indicators:** Volume, Implied Volatility.
