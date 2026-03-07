"""
Options Flow Analysis - Institutional options positioning indicators.
Ported from streamlit-stocks-plus to work with NiceGUI.
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Dict, Any, Optional, Tuple


@lru_cache(maxsize=32)
def fetch_options_chain_cached(symbol: str, timestamp: str) -> Optional[Tuple]:
    """Cached fetching of options chain. timestamp is used to invalidate cache."""
    try:
        ticker = yf.Ticker(symbol)
        expirations = ticker.options
        
        if not expirations:
            return None
        
        stock_info = ticker.info
        current_price = stock_info.get('currentPrice') or stock_info.get('regularMarketPrice')
        
        # Get expirations within 90 days
        target_date = datetime.now() + timedelta(days=90)
        relevant_exps = [exp for exp in expirations if datetime.strptime(exp, '%Y-%m-%d') <= target_date]
        
        all_calls = []
        all_puts = []
        
        for exp_date in relevant_exps[:10]:
            try:
                chain = ticker.option_chain(exp_date)
                calls = chain.calls.copy()
                calls['expiration'] = exp_date
                calls['option_type'] = 'call'
                all_calls.append(calls)
                
                puts = chain.puts.copy()
                puts['expiration'] = exp_date
                puts['option_type'] = 'put'
                all_puts.append(puts)
            except Exception:
                continue
        
        calls_df = pd.concat(all_calls, ignore_index=True) if all_calls else pd.DataFrame()
        puts_df = pd.concat(all_puts, ignore_index=True) if all_puts else pd.DataFrame()
        
        return (calls_df.to_dict(), puts_df.to_dict(), current_price)
    except Exception:
        return None


def fetch_options_data(symbol: str):
    """Fetch options data with simple time-based cache invalidation."""
    # Cache key includes hour to refresh hourly
    timestamp = datetime.now().strftime('%Y-%m-%d-%H')
    result = fetch_options_chain_cached(symbol, timestamp)
    
    if result is None:
        return None, None, None
    
    calls_dict, puts_dict, price = result
    calls_df = pd.DataFrame(calls_dict) if calls_dict else pd.DataFrame()
    puts_df = pd.DataFrame(puts_dict) if puts_dict else pd.DataFrame()
    
    return calls_df, puts_df, price


def calculate_premium(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate total premium (dollar volume) for option contracts."""
    if df.empty:
        return df
    
    df = df.copy()
    
    if 'lastPrice' in df.columns:
        price = df['lastPrice']
    else:
        price = (df['bid'] + df['ask']) / 2
    
    df['premium'] = price * df['volume'].fillna(0) * 100
    return df


def calculate_max_pain(calls_df: pd.DataFrame, puts_df: pd.DataFrame, expiration: str) -> Optional[float]:
    """
    Calculate Maximum Pain for a specific expiration.
    Max Pain is the strike where total option holder losses are maximized.
    """
    try:
        # Filter to specific expiration
        exp_calls = calls_df[calls_df['expiration'] == expiration] if not calls_df.empty else pd.DataFrame()
        exp_puts = puts_df[puts_df['expiration'] == expiration] if not puts_df.empty else pd.DataFrame()
        
        if exp_calls.empty and exp_puts.empty:
            return None
        
        # Get all unique strikes
        all_strikes = set()
        if not exp_calls.empty:
            all_strikes.update(exp_calls['strike'].dropna().unique())
        if not exp_puts.empty:
            all_strikes.update(exp_puts['strike'].dropna().unique())
        
        if not all_strikes:
            return None
        
        strikes = sorted(all_strikes)
        
        # Calculate total pain at each strike price
        pain_at_strike = {}
        for strike in strikes:
            total_pain = 0
            
            # Call holder losses: OI * max(0, strike - current_strike) * 100
            if not exp_calls.empty:
                for _, row in exp_calls.iterrows():
                    if row['strike'] < strike:
                        total_pain += row.get('openInterest', 0) * (strike - row['strike']) * 100
            
            # Put holder losses: OI * max(0, current_strike - strike) * 100
            if not exp_puts.empty:
                for _, row in exp_puts.iterrows():
                    if row['strike'] > strike:
                        total_pain += row.get('openInterest', 0) * (row['strike'] - strike) * 100
            
            pain_at_strike[strike] = total_pain
        
        # Max pain is the strike with maximum pain (losses to holders)
        if pain_at_strike:
            max_pain_strike = max(pain_at_strike, key=pain_at_strike.get)
            return max_pain_strike
        
        return None
    except Exception:
        return None


def get_atm_iv(calls_df: pd.DataFrame, current_price: float, expiration: str) -> Optional[float]:
    """Get ATM implied volatility for nearest expiration."""
    try:
        if calls_df.empty or not current_price:
            return None
        
        # Filter to nearest expiration
        exp_calls = calls_df[calls_df['expiration'] == expiration]
        if exp_calls.empty:
            return None
        
        # Find strike closest to current price
        exp_calls = exp_calls.copy()
        exp_calls['strike_diff'] = abs(exp_calls['strike'] - current_price)
        atm_call = exp_calls.loc[exp_calls['strike_diff'].idxmin()]
        
        iv = atm_call.get('impliedVolatility', 0)
        return round(iv * 100, 1) if iv else None
    except Exception:
        return None


def get_options_flow(symbol: str) -> Dict[str, Any]:
    """
    Get options flow analysis for a symbol.
    
    Returns dict with:
        - Premium metrics (call/put totals, net premium)
        - Volume metrics
        - Put/Call ratios
        - Unusual activity
        - Sentiment interpretation
        - IV (implied volatility)
        - Max Pain
    """
    try:
        calls_df, puts_df, current_price = fetch_options_data(symbol)
        
        if calls_df is None and puts_df is None:
            return {'error': f'No options data for {symbol}'}
        
        if (calls_df is None or calls_df.empty) and (puts_df is None or puts_df.empty):
            return {'error': 'Could not fetch options data'}
        
        # Get nearest expiration for IV and Max Pain
        nearest_expiration = None
        if not calls_df.empty and 'expiration' in calls_df.columns:
            nearest_expiration = calls_df['expiration'].min()
        elif not puts_df.empty and 'expiration' in puts_df.columns:
            nearest_expiration = puts_df['expiration'].min()
        
        # Calculate IV and Max Pain
        iv = None
        max_pain = None
        if nearest_expiration:
            iv = get_atm_iv(calls_df, current_price, nearest_expiration)
            max_pain = calculate_max_pain(calls_df, puts_df, nearest_expiration)
        
        # Add premium calculation
        if calls_df is not None and not calls_df.empty:
            calls_df = calculate_premium(calls_df)
        else:
            calls_df = pd.DataFrame()
            
        if puts_df is not None and not puts_df.empty:
            puts_df = calculate_premium(puts_df)
        else:
            puts_df = pd.DataFrame()
        
        # Calculate metrics
        total_call_premium = calls_df['premium'].sum() if not calls_df.empty else 0
        total_put_premium = puts_df['premium'].sum() if not puts_df.empty else 0
        total_call_volume = calls_df['volume'].sum() if not calls_df.empty else 0
        total_put_volume = puts_df['volume'].sum() if not puts_df.empty else 0
        
        net_premium = total_call_premium - total_put_premium
        
        # Ratios
        pc_volume_ratio = total_put_volume / max(total_call_volume, 1)
        pc_premium_ratio = total_put_premium / max(total_call_premium, 1)
        
        # Unusual activity (Volume > 1.5x Open Interest)
        unusual_calls = pd.DataFrame()
        unusual_puts = pd.DataFrame()
        
        if not calls_df.empty and 'openInterest' in calls_df.columns:
            unusual_calls = calls_df[calls_df['volume'] > 1.5 * calls_df['openInterest']]
        if not puts_df.empty and 'openInterest' in puts_df.columns:
            unusual_puts = puts_df[puts_df['volume'] > 1.5 * puts_df['openInterest']]
        
        # Sentiment determination
        if net_premium > 0:
            if pc_premium_ratio < 0.7:
                sentiment = 'STRONGLY BULLISH'
                sentiment_desc = 'Heavy call buying, significant net premium to calls'
            else:
                sentiment = 'BULLISH'
                sentiment_desc = 'Positive net premium flow favoring calls'
        else:
            if pc_premium_ratio > 1.5:
                sentiment = 'STRONGLY BEARISH'
                sentiment_desc = 'Heavy put buying, significant net premium to puts'
            else:
                sentiment = 'BEARISH'
                sentiment_desc = 'Negative net premium flow favoring puts'
        
        # Volume bias
        if pc_volume_ratio > 1.2:
            volume_bias = 'Put-heavy'
        elif pc_volume_ratio < 0.8:
            volume_bias = 'Call-heavy'
        else:
            volume_bias = 'Balanced'
        
        return {
            'symbol': symbol,
            'current_price': current_price,
            
            # IV and Max Pain
            'iv': iv,
            'max_pain': max_pain,
            'nearest_expiration': nearest_expiration,
            
            # Premium metrics
            'total_call_premium': total_call_premium,
            'total_put_premium': total_put_premium,
            'net_premium': net_premium,
            
            # Volume metrics
            'total_call_volume': int(total_call_volume),
            'total_put_volume': int(total_put_volume),
            
            # Ratios
            'pc_volume_ratio': pc_volume_ratio,
            'pc_premium_ratio': pc_premium_ratio,
            
            # Unusual activity
            'unusual_calls': len(unusual_calls),
            'unusual_puts': len(unusual_puts),
            
            # Sentiment
            'sentiment': sentiment,
            'sentiment_description': sentiment_desc,
            'volume_bias': volume_bias,
            'premium_bias': 'Put-heavy' if pc_premium_ratio > 1 else 'Call-heavy',
            
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'error': None
        }
        
    except Exception as e:
        return {'error': str(e)}


def format_premium(value: float) -> str:
    """Format premium values for display."""
    if abs(value) >= 1e9:
        return f"${value/1e9:.1f}B"
    elif abs(value) >= 1e6:
        return f"${value/1e6:.1f}M"
    elif abs(value) >= 1e3:
        return f"${value/1e3:.0f}K"
    else:
        return f"${value:,.0f}"


if __name__ == '__main__':
    result = get_options_flow('SPY')
    
    if result.get('error'):
        print(f"Error: {result['error']}")
    else:
        print(f"\n{result['symbol']} Options Flow @ ${result['current_price']:.2f}")
        print(f"Timestamp: {result['timestamp']}")
        print(f"\nPremium Flow:")
        print(f"  Call Premium: {format_premium(result['total_call_premium'])}")
        print(f"  Put Premium: {format_premium(result['total_put_premium'])}")
        print(f"  Net Premium: {format_premium(result['net_premium'])}")
        print(f"\nRatios:")
        print(f"  P/C Volume: {result['pc_volume_ratio']:.2f}")
        print(f"  P/C Premium: {result['pc_premium_ratio']:.2f}")
        print(f"\nSentiment: {result['sentiment']}")
        print(f"  {result['sentiment_description']}")
