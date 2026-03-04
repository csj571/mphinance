"""
VoPR Overlay — Enriches CSP candidates with volatility premium analytics.

Ports the key VoPR concepts (composite realized vol, VRP ratio, BS Greeks)
into a lightweight module that post-processes CSP deep dive results.
No external VoPR dependency — self-contained.
"""

import math
import numpy as np
import pandas as pd
from scipy.stats import norm
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# Black-Scholes Primitives
# ─────────────────────────────────────────────────────────────────────────────

def _d1_d2(S: float, K: float, T: float, r: float, sigma: float):
    """Return (d1, d2) for Black-Scholes."""
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return None, None
    sqrt_T = math.sqrt(T)
    d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * sqrt_T)
    d2 = d1 - sigma * sqrt_T
    return d1, d2


def bs_delta(S: float, K: float, T: float, r: float, sigma: float) -> Optional[float]:
    """Put delta — returns value in [-1, 0]."""
    d1, _ = _d1_d2(S, K, T, r, sigma)
    if d1 is None:
        return None
    return float(norm.cdf(d1) - 1.0)


def bs_theta(S: float, K: float, T: float, r: float, sigma: float) -> Optional[float]:
    """Put theta — daily decay in $ per share (negative = you earn)."""
    d1, d2 = _d1_d2(S, K, T, r, sigma)
    if d1 is None:
        return None
    disc = math.exp(-r * T)
    term1 = -(S * norm.pdf(d1) * sigma) / (2 * math.sqrt(T))
    annual_theta = term1 + r * K * disc * norm.cdf(-d2)
    return float(annual_theta / 365)  # daily


# ─────────────────────────────────────────────────────────────────────────────
# Composite Realized Volatility (4-model blend)
# ─────────────────────────────────────────────────────────────────────────────

def _close_to_close_vol(ohlcv: pd.DataFrame, period: int = 30) -> float:
    """Standard close-to-close HV. σ = stdev(log-returns) × √252"""
    closes = ohlcv['Close'].tail(period + 1)
    if len(closes) < 2:
        return 0.0
    log_returns = np.log(closes / closes.shift(1)).dropna()
    return float(log_returns.std() * math.sqrt(252))


def _parkinson_vol(ohlcv: pd.DataFrame, period: int = 30) -> float:
    """Parkinson (1980) — uses High-Low range. ~5x more efficient."""
    data = ohlcv.tail(period)
    if len(data) < 2:
        return 0.0
    hl = np.log(data['High'] / data['Low'])
    variance = (1 / (4 * len(data) * math.log(2))) * (hl**2).sum()
    return float(math.sqrt(variance * 252))


def _garman_klass_vol(ohlcv: pd.DataFrame, period: int = 30) -> float:
    """Garman-Klass (1980) — uses OHLC. Most efficient classical estimator."""
    data = ohlcv.tail(period)
    if len(data) < 2:
        return 0.0
    hl2 = np.log(data['High'] / data['Low'])**2
    co2 = np.log(data['Close'] / data['Open'])**2
    variance = (1 / len(data)) * (0.5 * hl2 - (2 * math.log(2) - 1) * co2).sum()
    return float(math.sqrt(abs(variance) * 252))


def _rogers_satchell_vol(ohlcv: pd.DataFrame, period: int = 30) -> float:
    """Rogers-Satchell (1991) — unbiased even with drift/trending stocks."""
    data = ohlcv.tail(period)
    if len(data) < 2:
        return 0.0
    hc = np.log(data['High'] / data['Close'])
    ho = np.log(data['High'] / data['Open'])
    lc = np.log(data['Low'] / data['Close'])
    lo = np.log(data['Low'] / data['Open'])
    variance = (1 / len(data)) * (hc * ho + lc * lo).sum()
    return float(math.sqrt(abs(variance) * 252))


def composite_realized_vol(
    ohlcv: pd.DataFrame,
    period: int = 30,
    weights: tuple = (0.15, 0.25, 0.35, 0.25),
) -> float:
    """
    Weighted blend of 4 realized vol estimators.
    Default weights favor Garman-Klass (most efficient) and Rogers-Satchell
    (handles trending stocks without bias).
    """
    vols = [
        _close_to_close_vol(ohlcv, period),
        _parkinson_vol(ohlcv, period),
        _garman_klass_vol(ohlcv, period),
        _rogers_satchell_vol(ohlcv, period),
    ]

    # Filter out zeros/nans
    valid = [(w, v) for w, v in zip(weights, vols) if v > 0 and math.isfinite(v)]
    if not valid:
        return 0.0

    total_weight = sum(w for w, _ in valid)
    return sum(w * v for w, v in valid) / total_weight


def classify_vol_regime(ohlcv: pd.DataFrame, period: int = 30) -> str:
    """
    Classify current vol regime by comparing recent vs. longer-term RV.
    Returns: 'LOW', 'RISING', 'HIGH', 'FALLING'
    """
    if len(ohlcv) < period * 2:
        return 'UNKNOWN'

    recent_rv = composite_realized_vol(ohlcv, period)
    longer_rv = composite_realized_vol(ohlcv, period * 2)

    if recent_rv == 0 or longer_rv == 0:
        return 'UNKNOWN'

    ratio = recent_rv / longer_rv

    if ratio > 1.15:
        return 'RISING' if recent_rv > 0.25 else 'HIGH'
    elif ratio < 0.85:
        return 'FALLING' if recent_rv > 0.20 else 'LOW'
    else:
        return 'HIGH' if recent_rv > 0.30 else 'LOW'


# ─────────────────────────────────────────────────────────────────────────────
# VRP (Volatility Risk Premium) Ratio
# ─────────────────────────────────────────────────────────────────────────────

def vrp_ratio(iv: float, rv: float) -> float:
    """
    IV / RV ratio — measures how rich implied vol is vs. realized.
    > 1.2  = IV is rich → great for selling premium
    < 0.8  = IV is cheap → avoid selling
    """
    if rv <= 0 or not math.isfinite(rv):
        return 0.0
    return iv / rv


def vopr_grade(vrp: float, regime: str, delta: Optional[float]) -> str:
    """
    Composite grade for a CSP candidate.
    A = Everything lined up: rich IV, calm/falling vol, safe delta
    B = Decent setup, one minor concern
    C = Marginal — proceed with caution
    F = Don't touch it
    """
    score = 0

    # VRP scoring (0-40 pts)
    if vrp >= 1.5:
        score += 40
    elif vrp >= 1.2:
        score += 30
    elif vrp >= 1.0:
        score += 15
    # else: 0

    # Regime scoring (0-30 pts)
    regime_scores = {'LOW': 30, 'FALLING': 25, 'UNKNOWN': 15, 'RISING': 5, 'HIGH': 0}
    score += regime_scores.get(regime, 10)

    # Delta scoring (0-30 pts) — more negative = higher risk
    if delta is not None:
        abs_d = abs(delta)
        if abs_d <= 0.10:
            score += 30  # Very safe
        elif abs_d <= 0.15:
            score += 25
        elif abs_d <= 0.20:
            score += 20
        elif abs_d <= 0.30:
            score += 10
        # else: 0 (too risky)
    else:
        score += 15  # Unknown, give benefit of doubt

    if score >= 80:
        return 'A'
    elif score >= 60:
        return 'B'
    elif score >= 40:
        return 'C'
    else:
        return 'F'


# ─────────────────────────────────────────────────────────────────────────────
# Main enrichment function
# ─────────────────────────────────────────────────────────────────────────────

def enrich_csp(df: pd.DataFrame, risk_free_rate: float = 0.05) -> pd.DataFrame:
    """
    Enrich a CSP deep dive DataFrame with VoPR metrics.

    Expects columns: name/ticker, close/price, Trade_Strike, Trade_Prem,
                     DaysOut, Trade_Exp

    Adds columns: VRP_Ratio, Vol_Regime, Composite_RV, BS_Delta,
                  Daily_Theta, VoPR_Grade
    """
    if df.empty:
        return df

    import yfinance as yf

    enriched = df.copy()

    # Initialize new columns
    for col in ['VRP_Ratio', 'Vol_Regime', 'Composite_RV', 'BS_Delta', 'Daily_Theta', 'VoPR_Grade']:
        enriched[col] = None

    for idx, row in enriched.iterrows():
        ticker = row.get('name', row.get('ticker', ''))
        price = float(row.get('close', row.get('price', 0)))
        strike = float(row.get('Trade_Strike', 0))
        days_out = int(row.get('DaysOut', 30))

        if not ticker or price <= 0 or strike <= 0:
            continue

        try:
            # Fetch OHLCV for vol calculations
            stock = yf.Ticker(ticker)
            ohlcv = stock.history(period='3mo')

            if ohlcv.empty or len(ohlcv) < 10:
                continue

            # Composite Realized Vol
            rv = composite_realized_vol(ohlcv)
            regime = classify_vol_regime(ohlcv)

            # Get ATM IV estimate from the premium we already have
            T = days_out / 365.0
            premium = float(row.get('Trade_Prem', 0))

            # Rough IV estimate: back-solve from premium/strike ratio
            # (For a proper solution we'd use the full BS solver, but this
            # gives a decent approximation for OTM puts)
            if premium > 0 and T > 0:
                # Brenner-Subrahmanyam approximation
                approx_iv = premium * math.sqrt(2 * math.pi / T) / price
                approx_iv = max(0.05, min(approx_iv, 3.0))  # clamp
            else:
                approx_iv = rv * 1.1 if rv > 0 else 0.25  # fallback

            # VRP
            vrp = vrp_ratio(approx_iv, rv)

            # BS Greeks
            delta = bs_delta(price, strike, T, risk_free_rate, approx_iv)
            theta = bs_theta(price, strike, T, risk_free_rate, approx_iv)

            # Grade
            grade = vopr_grade(vrp, regime, delta)

            enriched.at[idx, 'Composite_RV'] = round(rv * 100, 1)  # as %
            enriched.at[idx, 'Vol_Regime'] = regime
            enriched.at[idx, 'VRP_Ratio'] = round(vrp, 2)
            enriched.at[idx, 'BS_Delta'] = round(delta, 3) if delta else None
            enriched.at[idx, 'Daily_Theta'] = round(theta, 4) if theta else None
            enriched.at[idx, 'VoPR_Grade'] = grade

        except Exception as e:
            print(f"  [VoPR] Error enriching {ticker}: {e}")
            continue

    # Sort by grade then ROC
    grade_order = {'A': 0, 'B': 1, 'C': 2, 'F': 3, None: 4}
    enriched['_grade_sort'] = enriched['VoPR_Grade'].map(grade_order)
    enriched = enriched.sort_values(
        ['_grade_sort', 'Trade_ROC_W'],
        ascending=[True, False]
    ).drop(columns='_grade_sort', errors='ignore')

    return enriched
