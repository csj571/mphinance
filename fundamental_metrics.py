"""
Fundamental Metrics - Key financial health indicators for stocks.
"""

import yfinance as yf
from typing import Dict, Any, Optional


def get_fundamental_metrics(ticker: str) -> Dict[str, Any]:
    """
    Fetch key fundamental metrics for a stock using yfinance.
    
    Returns dict with:
        - valuation: P/E, P/S, P/B, EV/EBITDA
        - profitability: ROIC, ROE, Gross Margin, Operating Margin
        - financial_health: Current Ratio, Debt/Equity, FCF
        - growth: Revenue Growth, Earnings Growth
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Helper to safely get values
        def safe_get(key, default=None, formatter=None):
            val = info.get(key, default)
            if val is None:
                return default
            if formatter and val is not None:
                return formatter(val)
            return val
        
        def pct(v):
            return f"{v*100:.1f}%" if v else "-"
        
        def ratio(v):
            return f"{v:.2f}" if v else "-"
        
        def money(v):
            if v is None:
                return "-"
            if abs(v) >= 1e9:
                return f"${v/1e9:.1f}B"
            elif abs(v) >= 1e6:
                return f"${v/1e6:.0f}M"
            else:
                return f"${v:,.0f}"
        
        return {
            'ticker': ticker,
            'company_name': info.get('longName', ticker),
            'sector': info.get('sector', '-'),
            'industry': info.get('industry', '-'),
            
            # Current Price Info
            'price': info.get('currentPrice') or info.get('regularMarketPrice'),
            'market_cap': safe_get('marketCap', formatter=money),
            'fifty_two_week_high': info.get('fiftyTwoWeekHigh'),
            'fifty_two_week_low': info.get('fiftyTwoWeekLow'),
            
            # Valuation
            'pe_ratio': safe_get('trailingPE', formatter=ratio),
            'forward_pe': safe_get('forwardPE', formatter=ratio),
            'ps_ratio': safe_get('priceToSalesTrailing12Months', formatter=ratio),
            'pb_ratio': safe_get('priceToBook', formatter=ratio),
            'ev_ebitda': safe_get('enterpriseToEbitda', formatter=ratio),
            'peg_ratio': safe_get('pegRatio', formatter=ratio),
            
            # Profitability
            'gross_margin': safe_get('grossMargins', formatter=pct),
            'operating_margin': safe_get('operatingMargins', formatter=pct),
            'profit_margin': safe_get('profitMargins', formatter=pct),
            'roe': safe_get('returnOnEquity', formatter=pct),
            'roa': safe_get('returnOnAssets', formatter=pct),
            
            # Financial Health
            'current_ratio': safe_get('currentRatio', formatter=ratio),
            'debt_to_equity': safe_get('debtToEquity', formatter=ratio),
            'free_cash_flow': safe_get('freeCashflow', formatter=money),
            'operating_cash_flow': safe_get('operatingCashflow', formatter=money),
            'total_debt': safe_get('totalDebt', formatter=money),
            'total_cash': safe_get('totalCash', formatter=money),
            
            # Growth
            'revenue_growth': safe_get('revenueGrowth', formatter=pct),
            'earnings_growth': safe_get('earningsGrowth', formatter=pct),
            'revenue_per_share': safe_get('revenuePerShare', formatter=ratio),
            
            # Dividends
            'dividend_yield': safe_get('dividendYield', formatter=pct),
            'payout_ratio': safe_get('payoutRatio', formatter=pct),
            
            # Analyst
            'target_price': info.get('targetMeanPrice'),
            'recommendation': info.get('recommendationKey', '-').upper(),
            'num_analysts': info.get('numberOfAnalystOpinions', 0),
            
            'error': None
        }
        
    except Exception as e:
        return {
            'ticker': ticker,
            'error': str(e)
        }


def get_key_metrics_summary(ticker: str) -> Dict[str, Any]:
    """
    Get a condensed summary of key metrics for display cards.
    """
    metrics = get_fundamental_metrics(ticker)
    
    if metrics.get('error'):
        return metrics
    
    return {
        'ticker': ticker,
        'company_name': metrics['company_name'],
        'cards': [
            {'label': 'Market Cap', 'value': metrics['market_cap']},
            {'label': 'P/E Ratio', 'value': metrics['pe_ratio']},
            {'label': 'Gross Margin', 'value': metrics['gross_margin']},
            {'label': 'ROE', 'value': metrics['roe']},
            {'label': 'Free Cash Flow', 'value': metrics['free_cash_flow']},
            {'label': 'Debt/Equity', 'value': metrics['debt_to_equity']},
            {'label': 'Revenue Growth', 'value': metrics['revenue_growth']},
            {'label': 'Dividend Yield', 'value': metrics['dividend_yield']},
        ],
        'full_metrics': metrics
    }


if __name__ == '__main__':
    # Test
    result = get_fundamental_metrics('AAPL')
    print(f"\n{result['company_name']} ({result['ticker']})")
    print(f"Sector: {result['sector']} | Industry: {result['industry']}")
    print(f"\nValuation:")
    print(f"  P/E: {result['pe_ratio']} | P/S: {result['ps_ratio']} | P/B: {result['pb_ratio']}")
    print(f"\nProfitability:")
    print(f"  Gross Margin: {result['gross_margin']} | ROE: {result['roe']}")
    print(f"\nFinancial Health:")
    print(f"  FCF: {result['free_cash_flow']} | D/E: {result['debt_to_equity']}")
