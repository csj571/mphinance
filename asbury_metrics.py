"""
Asbury 6 Market Health Metrics

Quantitative daily gauge of US equity market internal strength.
Ported from streamlit-stocks-plus to work with NiceGUI.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from functools import lru_cache


# Simple cache for data fetching (expires when app restarts)
@lru_cache(maxsize=32)
def fetch_ticker_data_cached(ticker: str, start_date: str, end_date: str):
    """Fetches historical data for a given ticker with caching."""
    return yf.download(ticker, start=start_date, end=end_date, progress=False)


def fetch_ticker_data(ticker: str, start_date: str, end_date: str):
    """Fetches historical data for a given ticker."""
    data = fetch_ticker_data_cached(ticker, start_date, end_date)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    
    # Check for empty data
    if data.empty or len(data) < 20:
        raise ValueError(f"Not enough data for {ticker} - the market gods are napping 😴")
    
    return data


def calculate_market_breadth(spy_data):
    """
    Market Breadth: Measures participation across the market.
    Positive signal when recent volume is above average and price is making new highs.
    """
    avg_volume_20 = spy_data['Volume'].rolling(window=20).mean().iloc[-1]
    current_volume = spy_data['Volume'].iloc[-1]
    high_20 = spy_data['High'].rolling(window=20).max().iloc[-1]
    current_price = spy_data['Close'].iloc[-1]

    volume_ratio = current_volume / avg_volume_20
    price_ratio = current_price / high_20

    is_positive = volume_ratio > 1.0 and price_ratio > 0.98

    return {
        'name': 'Market Breadth',
        'value': f'{volume_ratio:.2f}x avg vol, {price_ratio*100:.1f}% of 20d high',
        'status': 'Positive' if is_positive else 'Negative',
        'description': 'Strong participation' if is_positive else 'Narrow participation'
    }


def calculate_volume_strength(spy_data):
    """Volume: Tracks trading activity and conviction."""
    avg_volume_50 = spy_data['Volume'].rolling(window=50).mean().iloc[-1]
    recent_avg_volume_5 = spy_data['Volume'].rolling(window=5).mean().iloc[-1]
    volume_ratio = recent_avg_volume_5 / avg_volume_50

    is_positive = volume_ratio > 1.10

    return {
        'name': 'Volume',
        'value': f'{volume_ratio:.2f}x (5d/50d)',
        'status': 'Positive' if is_positive else 'Negative',
        'description': 'High conviction' if is_positive else 'Low conviction'
    }


def calculate_relative_performance(spy_data, iwm_data):
    """Relative Performance: Compares small caps vs large caps."""
    spy_return = (spy_data['Close'].iloc[-1] / spy_data['Close'].iloc[-20] - 1) * 100
    iwm_return = (iwm_data['Close'].iloc[-1] / iwm_data['Close'].iloc[-20] - 1) * 100
    relative_performance = iwm_return - spy_return

    is_positive = relative_performance > 0

    return {
        'name': 'Relative Performance',
        'value': f'IWM {iwm_return:+.1f}% vs SPY {spy_return:+.1f}%',
        'status': 'Positive' if is_positive else 'Negative',
        'description': 'Small caps leading (risk-on)' if is_positive else 'Large caps defensive'
    }


def calculate_asset_flows(spy_data, tlt_data):
    """Asset Flows: Reflects capital movement between stocks and bonds."""
    spy_return = (spy_data['Close'].iloc[-1] / spy_data['Close'].iloc[-10] - 1) * 100
    tlt_return = (tlt_data['Close'].iloc[-1] / tlt_data['Close'].iloc[-10] - 1) * 100

    is_positive = spy_return > tlt_return

    return {
        'name': 'Asset Flows',
        'value': f'SPY {spy_return:+.1f}% vs TLT {tlt_return:+.1f}%',
        'status': 'Positive' if is_positive else 'Negative',
        'description': 'Capital flowing to equities' if is_positive else 'Flight to safety'
    }


def calculate_volatility(vix_data):
    """Volatility (VIX): Gauges expected market volatility and fear."""
    current_vix = vix_data['Close'].iloc[-1]
    vix_20d_avg = vix_data['Close'].rolling(window=20).mean().iloc[-1]

    is_positive = current_vix < 20 and current_vix < vix_20d_avg

    return {
        'name': 'VIX',
        'value': f'{current_vix:.2f} (20d avg: {vix_20d_avg:.2f})',
        'status': 'Positive' if is_positive else 'Negative',
        'description': 'Low fear, stable' if is_positive else 'Elevated uncertainty'
    }


def calculate_price_roc(spy_data):
    """Price Rate of Change: Measures momentum of price moves."""
    roc_20 = ((spy_data['Close'].iloc[-1] / spy_data['Close'].iloc[-20]) - 1) * 100
    roc_10 = ((spy_data['Close'].iloc[-1] / spy_data['Close'].iloc[-10]) - 1) * 100

    is_positive = roc_20 > 0 and roc_10 > (roc_20 / 2)

    return {
        'name': 'Price ROC',
        'value': f'20d: {roc_20:+.2f}%, 10d: {roc_10:+.2f}%',
        'status': 'Positive' if is_positive else 'Negative',
        'description': 'Strong momentum' if is_positive else 'Weak momentum'
    }


def get_asbury_6_signals():
    """
    Main function that fetches market data and calculates all six Asbury 6 signals.
    
    Returns:
        dict with 'metrics', 'signal' (BUY/CASH/NEUTRAL), 'positive_count', 
        'negative_count', 'timestamp'
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')

        spy_data = fetch_ticker_data('SPY', start_str, end_str)
        iwm_data = fetch_ticker_data('IWM', start_str, end_str)
        tlt_data = fetch_ticker_data('TLT', start_str, end_str)
        vix_data = fetch_ticker_data('^VIX', start_str, end_str)

        metrics = [
            calculate_market_breadth(spy_data),
            calculate_volume_strength(spy_data),
            calculate_relative_performance(spy_data, iwm_data),
            calculate_asset_flows(spy_data, tlt_data),
            calculate_volatility(vix_data),
            calculate_price_roc(spy_data)
        ]

        positive_count = sum(1 for m in metrics if m['status'] == 'Positive')
        negative_count = sum(1 for m in metrics if m['status'] == 'Negative')

        if positive_count >= 4:
            signal = 'BUY'
        elif negative_count >= 4:
            signal = 'CASH'
        else:
            signal = 'NEUTRAL'

        return {
            'metrics': metrics,
            'signal': signal,
            'positive_count': positive_count,
            'negative_count': negative_count,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    except Exception as e:
        return {
            'error': str(e),
            'metrics': [],
            'signal': 'ERROR',
            'positive_count': 0,
            'negative_count': 0,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }


if __name__ == '__main__':
    result = get_asbury_6_signals()
    print(f"\nAsbury 6 Market Health Check - {result['timestamp']}")
    print(f"Overall Signal: {result['signal']} ({result['positive_count']} Positive, {result['negative_count']} Negative)\n")
    
    for metric in result['metrics']:
        status_icon = '✅' if metric['status'] == 'Positive' else '❌'
        print(f"{status_icon} {metric['name']}: {metric['value']}")
        print(f"   {metric['description']}\n")
