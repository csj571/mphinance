
from tradingview_screener import Query, col
from typing import Dict, Any, List
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import numpy as np
from .base import BaseStrategy

class CashSecuredPutsStrategy(BaseStrategy):
    """
    Cash Secured Puts Strategy (The Funnel Approach)
    Stage 1: Broad Sweep (TradingView) - Technicals & liquidity
    Stage 2: Logic Check - EMA/ATR filter
    Stage 3: Deep Dive - Options chain analysis (Earnings, ROC, Liquidity)
    """
    
    name = "Cash Secured Puts"
    description = "Finds high-quality CSP candidates using a multi-stage funnel."
    
    select_columns = [
        'name', 'description', 'close', 'change', 'volume', 
        'market_cap_basic', 'type', 'subtype',
        'ADX', 'ATR', 'RSI',
        'EMA20', 'SMA50', 'SMA200', 'average_volume_10d_calc'
    ]
    
    def get_default_params(self) -> Dict[str, Any]:
        return {
            'min_price': 5.0,
            'max_price': 200.0,
            'min_vol': 150000,
            'max_adx': 45.0,
            'min_roc': 1.0, # 1% Return on Capital
            'strike_otm_pct': 0.10, # 10% OTM
            'check_golden_cross': False,
            'check_near_ema': False,
            'min_opt_vol': 100,
            'weekly_options_only': False
        }
    
    def get_param_config(self) -> List[Dict[str, Any]]:
        return [
            {'name': 'min_price', 'label': 'Min Price', 'type': 'number', 'min': 1, 'max': 500, 'step': 1},
            {'name': 'max_price', 'label': 'Max Price', 'type': 'number', 'min': 10, 'max': 1000, 'step': 10},
            {'name': 'max_adx', 'label': 'Max ADX (Trend)', 'type': 'number', 'min': 10, 'max': 60, 'step': 1},
            {'name': 'min_roc', 'label': 'Min ROC % (Weekly)', 'type': 'number', 'min': 0.5, 'max': 5.0, 'step': 0.1},
            {'name': 'strike_otm_pct', 'label': 'Strike Distance (OTM %)', 'type': 'number', 'min': 0.05, 'max': 0.30, 'step': 0.01},
        ]
    
    def build_query(self, params: Dict[str, Any]) -> Query:
        min_p = params.get('min_price', 5.0)
        max_p = params.get('max_price', 200.0)
        min_v = params.get('min_vol', 150000)
        max_adx = params.get('max_adx', 45.0)
        
        conditions = [
            # Stage 1: Broad Sweep
            col('exchange').isin(['NASDAQ', 'NYSE', 'AMEX']),
            col('type') == 'stock',
            col('subtype') == 'common', # No ETFs/Funds per user "Market Cap & Type" check preference usually implies common stock
            
            # Liquidity & Price
            col('close').between(min_p, max_p),
            col('volume') >= min_v,
            
            # Trend Strength (Not trending too hard against us)
            col('ADX') < max_adx,
            
            # Technical Health
            col('RSI').between(30, 70), # Not overbought/oversold
        ]

        if params.get('check_golden_cross', False):
             conditions.append(col('SMA50') > col('SMA200'))
        
        query = (
            Query()
            .select(*self.select_columns)
            .where(*conditions)
            .limit(100) # Limit processed candidates to save time in Deep Dive
        )
        return query
    
    def post_process(self, df: pd.DataFrame, params: Dict[str, Any] = None) -> pd.DataFrame:
        if df.empty:
            return df
            
        # Stage 2: Local Logic Check (EMA/ATR Filter)
        # "Is the distance from the 20 EMA less than 1 ATR?"
        # Logic: Filter out stocks exploding/crashing violently
        
        # Ensure we have necessary columns
        if params.get('check_near_ema', False) and 'EMA20' in df.columns and 'ATR' in df.columns:
            df['dist_to_ema20'] = (df['close'] - df['EMA20']).abs()
            df = df[df['dist_to_ema20'] < df['ATR']]
            
        return df

    def deep_dive(self, df: pd.DataFrame, params: Dict[str, Any] = None) -> pd.DataFrame:
        """
        Stage 3: The Deep Dive (yfinance)
        Downloads option chains to verify specific trades.
        """
        if df.empty:
            return df

        params = params or self.get_default_params()
        min_roc = params.get('min_roc', 1.0) / 100.0
        target_otm = params.get('strike_otm_pct', 0.10)
        trade_type = params.get('trade_type', 'CSP') # CSP or Spread
        min_opt_vol = params.get('min_opt_vol', 100)
        weekly_only = params.get('weekly_options_only', False)
        
        valid_trades = []
        
        print(f"Starting Deep Dive on {len(df)} candidates...")
        
        for index, row in df.iterrows():
            ticker = row['name']
            price = row['close']
            
            try:
                stock = yf.Ticker(ticker)
                
                # 1. Earnings Check
                # Skip if earnings in next 7 days (simplified safety check)
                
                # 2. Expiration Check (Target: ~7-14 days for Weekly, or just next available weekly)
                expirations = stock.options
                if not expirations:
                    continue
                    
                # Find suitable expiration (e.g., 7 to 45 days out)
                good_exps = []
                today = datetime.now()
                for exp_date_str in expirations:
                    exp_date = datetime.strptime(exp_date_str, '%Y-%m-%d')
                    days_out = (exp_date - today).days
                    if 7 <= days_out <= 30:
                        good_exps.append(exp_date_str)
                
                if not good_exps:
                    continue
                
                # "Stop at Yes" logic
                found_trade = False
                for exp in good_exps:
                    if found_trade: break
                    
                    # Download Puts
                    chain = stock.option_chain(exp)
                    puts = chain.puts
                    
                    # 3. Strike Selection (e.g., 10-20% below price)
                    target_strike = price * (1 - target_otm)
                    
                    # Find put closest to target strike, but below it (safe)
                    puts_otm = puts[puts['strike'] <= target_strike]
                    if puts_otm.empty:
                        continue
                        
                    # Get the closest one (highest strike that is <= target)
                    best_put = puts_otm.iloc[-1]
                    short_strike = best_put['strike']
                    short_prem = (best_put['bid'] + best_put['ask']) / 2
                    
                    if short_prem <= 0:
                        continue
                    
                    trade_details = {}
                    
                    if trade_type == 'Spread':
                        # Find Long Put (Protection) - Look for next strike below
                        long_puts = puts[puts['strike'] < short_strike]
                        if long_puts.empty:
                             continue
                        
                        # Find a strike that is 1-3 strikes away
                        # Simple logic: Take the immediate next strike or one with reasonable volume
                        long_put = long_puts.iloc[-1] # Put right below Short Put
                        long_strike = long_put['strike']
                        long_prem = (long_put['bid'] + long_put['ask']) / 2
                        
                        width = short_strike - long_strike
                        net_credit = short_prem - long_prem
                        max_risk = width - net_credit
                        
                        if max_risk <= 0 or net_credit <= 0:
                            continue
                            
                        # ROC for Spread = Credit / Max Risk
                        roc_nominal = net_credit / max_risk
                        
                        trade_details = {
                            'Trade_Type': 'Spread',
                            'Trade_Strike': f"{short_strike}/{long_strike}p",
                            'Trade_Prem': net_credit,
                            'Trade_Width': width,
                            'Trade_MaxRisk': max_risk
                        }
                    else:
                        # CSP Logic
                        roc_nominal = short_prem / short_strike
                         
                        trade_details = {
                            'Trade_Type': 'CSP',
                            'Trade_Strike': short_strike,
                            'Trade_Prem': short_prem,
                            'Trade_Width': 0,
                            'Trade_MaxRisk': short_strike - short_prem
                        }
                    
                    # Calculate Weekly ROC
                    exp_date = datetime.strptime(exp, '%Y-%m-%d')
                    days_out = max((exp_date - today).days, 1)
                    weeks_out = days_out / 7.0
                    
                    weekly_roc = roc_nominal / weeks_out
                    
                    if weekly_roc >= min_roc:
                        # 5. Liquidity check (Short leg is primary concern)
                        if best_put['volume'] > min_opt_vol or best_put['openInterest'] > 50:
                            # Found a winner!
                            row['Trade_Exp'] = exp
                            row['Trade_Strike'] = trade_details['Trade_Strike']
                            row['Trade_Prem'] = trade_details['Trade_Prem']
                            row['Trade_ROC_W'] = weekly_roc * 100 # %
                            row['DaysOut'] = days_out
                            row['Trade_Type'] = trade_details['Trade_Type']
                            
                            valid_trades.append(row)
                            found_trade = True
            
            except Exception as e:
                # print(f"Error checking {ticker}: {e}") # Reduce log noise
                continue
                
        if not valid_trades:
            return pd.DataFrame()
        
        result = pd.DataFrame(valid_trades)
        
        # Stage 4: VoPR Overlay — enrich with volatility premium analytics
        try:
            from strategies.vopr_overlay import enrich_csp
            print(f"  Running VoPR overlay on {len(result)} candidates...")
            result = enrich_csp(result)
            print(f"  ✓ VoPR enrichment complete")
        except ImportError:
            print("  [WARN] VoPR overlay not available, skipping enrichment")
        except Exception as e:
            print(f"  [WARN] VoPR overlay failed: {e}")
            
        return result
