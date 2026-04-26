# Quantitative Screener Upgrades - Session Log

This document records the comprehensive quantitative logic overhaul performed on the four major TraderDaddy Pro screeners: Leveraged, CSP, LEAPS, and Gamma.

## 1. 2x Leveraged ETF Screener (V2 Multi-Mode)
- **Eliminated Early Termination**: The screener now scores all setups via the `EdgeScore` instead of relying heavily on "stop at first yes" logic.
- **Removed Stale Logic**: Reversal mode was previously stripped from the codebase; we audited the code to remove all leftover documentation/comments referring to "Reversal" setups.
- **Ignition Tuning**: Reduced the MACD weighting in the ignition score (as 15m MACD crossovers are noisy) and re-weighted ADX expansion to better capture authentic momentum surges.
- **Alignment**: Audited all 8 user-configurable parameters to ensure the `getDefaultParams` defaults perfectly match the slider `defaultValue` configurations on the frontend.

## 2. CSP (Cash Secured Puts) Screener
- **Stop at First Bug Fixed**: The screener used to stop evaluating as soon as it found the *first* valid expiration. It now evaluates *all* expirations within the DTE limits and picks the absolute highest-scoring put contract.
- **Advanced EdgeScore Matrix**: Replaced the original logic with a 4-factor normalized EdgeScore:
  - Premium Quality (40%): Maps IV from 25-80% to a 0-100 score. Heavily penalizes IV > 120% (binary event risk).
  - ROC Efficiency (25%): Normalizes weekly return up to 2.5%.
  - Technical Setup (20%): Rewards RSI 40-60. Penalizes extreme oversold/overbought and high ADX (strong directional risk).
  - Liquidity Quality (15%): Evaluates bid/ask spread (rejects >30% spread) and open interest (requires 10+).
- **RSI Default Safety**: Narrowed the default RSI acceptable range from 20-80 to a safer 30-70 out-of-the-box setting.
- **Dead Code Cleanup**: Deleted the unused `fetchStockInfo` function which was wasting lines and carrying a potential Tradier API rate-limit risk.

## 3. LEAPS Screener (Reverse VoPR)
- **Stop at First Bug Fixed**: Same as CSP; now scores all expirations across the 180-730 DTE range and selects the most efficient contract.
- **From Safe to Explosive**: Changed the underlying TradingView query from sorting by `market_cap_basic` (which returned massive, slow-moving mega-caps) to sorting by `Volatility.M` (Monthly Volatility). This surfaces explosive, asymmetric, high-beta setups first.
- **Precision Delta Targets**: 
  - Stock Replacement mode target delta raised to 0.75-0.90 to ensure true ITM intrinsic value.
  - Leveraged Directional target delta raised to 0.35-0.50 to give a realistic probability of profit.
- **Trend Alignment**: Hard-coded safety blocks to prevent buying LEAPS against the trend (ADX > 20 and RSI > 45 required for calls).
- **Advanced EdgeScore Matrix**:
  - Extrinsic Efficiency (40%): Penalizes high extrinsic premium heavily.
  - Capital Efficiency (30%): Delta per dollar spent.
  - Theta Decay Efficiency (20%): Low decay per unit of delta exposure.
  - Liquidity Quality (10%): Spread and Open Interest (raised min OI to 200).
- **Default Parameter Alignment**:
  - Reduced `max_extrinsic_pct` from 0.30 to 0.20 to enforce strict PMCC guidelines.
  - Fixed a critical UI bug where the `min_volume` config defaulted to 500k but the actual runtime default was 250k. Now cleanly aligned at 250k.

## 4. Gamma Scan Screener
- **Un-Pinned the Logic**: The screener used to enforce a `< 2%` proximity threshold, which surfaced stocks already "pinned" at hard gamma resistance walls. Replaced this with a "Gamma Zone" (`min_pct_away` and `max_pct_away`).
- **Default Gamma Zone**: Defaults to 3% to 8% away from the wall, providing actual runway for a momentum squeeze setup.
- **Trend Minimum**: Raised the default ADX minimum from 15 to 20 to confirm stronger trends.
- **Squeeze Score Algorithm**: Replaced naive sorting by total Open Interest (which always bumped SPY/QQQ to the top) with a customized `Squeeze Score`:
  - `(Top Wall OI * 100) / Average Daily Volume`
  - Plus an ADX bonus up to +20.
  - This surfaces stocks where the gamma wall is massive relative to their normal liquidity, presenting the highest probability of violent market maker hedging.

## Constellation Upgrades
- Rewrote `run_constellation.js` to support a single, high-powered Architect Agent (GPT-4o) running two distinct evaluation passes:
  1. **Trading Logic Review**: Pure mathematical evaluation of thresholds, indicators, and risk setups.
  2. **Code Quality Review**: Pure TypeScript type safety, runtime error risk, and performance audit.
- Added automatic version saving to `run_constellation.js` so past variants are preserved (e.g., `constellation_v3_two_pass_architect.js`).
- Added the Bullish Pullback screener (`BullishPullbackScreener.ts` + `tvScreener.py`) to the Constellation review payload (now reviews 5 screeners).

---

## 5. CSP Screener — Gamma Support Floor (Session 2)
- **Put OI Concentration Detection**: Added a new `detectSupportFloor()` method that scans put Open Interest in the 3-8% OTM zone below the strike to identify potential market maker hedging support levels.
- **EdgeScore Bonus**: Adds up to +10 points to the EdgeScore when significant put OI concentration is detected (>2,000 contracts), rewarding setups where dealer gamma activity creates a natural price floor.
- **UI Surface**: Exposed `supportFloor` and `supportOI` fields on the `CSPCandidate` interface so the frontend can display "Support Floor: $X (Y OI)" when present.

## 6. Bullish Pullback Screener — Full Tao of Trading Rewrite (Session 2)
- **Eliminated Python Wrapper**: Replaced the legacy `BullishPullbackScreener.ts` which shelled out to `tvScreener.py` (only checked `EMA8 > EMA21`) with a delegation to the `MomentumScreener` engine.
- **Full EMA Stack**: Now enforces the complete Simon Ree "Tao of Trading" stack: `EMA 8 > 21 > 34 > 55 > 89` (Daily) + `EMA 8 > 21 > 34` (Weekly).
- **7-Factor EdgeScore (0-100)**: Inherits the Momentum screener's Entry Quality Score:
  - Pullback Depth (25%): Stochastic %K positioning
  - ATR Distance (20%): Proximity to EMA21 support
  - Trend Strength (20%): ADX confirmation
  - Stoch Crossover (10%): K > D timing signal
  - RSI Confluence (10%): Supporting pullback thesis
  - Volume Confirmation (10%): Relative volume spike
  - Trend Consistency (5%): Monthly + quarterly performance alignment
- **Backward Compatibility**: The `bullish-pullback` ID is preserved across the UI, Help pages, and AI tool registry. The screener class delegates to `MomentumScreener` and overrides only the `screenerId` in the result.

## 7. The Daily Cuts — Orchestrator & Schedule UI (Session 2)
- **New Screener**: Created `DailyCutsScreener.ts`, an orchestration layer that internally runs the `LeveragedScreener`, `CSPScreener`, and `LEAPSScreener`.
- **Tiering**: Automatically slices each screener's top 3 results into `Prime`, `Choice`, and `Select` tiers, injecting `dailyCutCategory` and `dailyCutTier` metadata.
- **24-Hour Cache**: Results are cached under a `screener:daily-cuts:YYYY-MM-DD` Redis key. Once generated, the playbook is locked for the entire day — perfect for sharing as a daily report.
- **Registration**: Registered in `ScreenerManager` via `index.ts` under the `daily-cuts` ID.
- **Frontend — DailyCutsView.tsx**: New component that renders a time-blocked schedule UI:
  - Pre-Market & Open (4-10am EST): 2x LETF Momentum picks
  - The Morning Dip (10am-12pm EST): Cash Secured Put picks
  - Afternoon Positioning (12-4pm EST): LEAPS picks
  - Dynamically highlights the currently active trading window with a pulsing "ACTIVE WINDOW" indicator
  - Renders tiered cards with embedded trade setup strings and watchlist add buttons
- **Frontend — page.tsx**: Modified to intercept `screenerId === 'daily-cuts'`, hide the standard Run/Export controls, and show a "Generate Today's Playbook" CTA button with a custom loading state.
