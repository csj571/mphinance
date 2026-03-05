import pandas as pd
import pandas_ta as ta
import yfinance as yf
import time
import json

def enrich_ticker(ticker: str, period="1y") -> dict:
    """
    Enriches ticker data with technical indicators using pandas-ta.
    """
    try:
        # Fetching data for a single ticker usually returns a flat DataFrame unless we use a list
        df = yf.download(ticker, period=period, interval='1d', progress=False)
        if df.empty:
            return None
        
        # Flatten MultiIndex if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.droplevel(1)
            
        # Ensure only 1 ticker is in columns (sometimes yf returns redundant)
        df = df.loc[:, ~df.columns.duplicated()]

        # Indicators
        df.ta.squeeze(append=True)
        df.ta.supertrend(append=True)
        df.ta.bbands(append=True)
        df.ta.atr(append=True)
        df.ta.rsi(append=True)
        df.ta.ichimoku(append=True)
        
        # Band width
        u_cols = [c for c in df.columns if c.startswith('BBU_')]
        l_cols = [c for c in df.columns if c.startswith('BBL_')]
        m_cols = [c for c in df.columns if c.startswith('BBM_')]
        if u_cols and l_cols and m_cols:
            df['BB_WIDTH'] = (df[u_cols[0]] - df[l_cols[0]]) / df[m_cols[0]]

        latest = df.tail(1)
        
        def gv(col_prefix, default=0):
            cols = [c for c in df.columns if c.startswith(col_prefix)]
            if not cols: return default
            val = latest[cols[0]].iloc[0]
            return round(float(val), 4) if pd.notnull(val) else default

        res = {
            "ticker": ticker,
            "price": round(float(latest['Close'].iloc[0]), 2),
            "squeeze": {
                "on": bool(latest[[c for c in df.columns if c.startswith('SQZ_ON')][0]].iloc[0]) if [c for c in df.columns if c.startswith('SQZ_ON')] else False,
                "off": bool(latest[[c for c in df.columns if c.startswith('SQZ_OFF')][0]].iloc[0]) if [c for c in df.columns if c.startswith('SQZ_OFF')] else False,
                "val": gv('SQZ_')
            },
            "supertrend": {
                "dir": int(latest[[c for c in df.columns if c.startswith('SUPERTd')][0]].iloc[0]) if [c for c in df.columns if c.startswith('SUPERTd')] else 0,
                "val": gv('SUPERT_')
            },
            "bbands": {
                "width": round(float(latest['BB_WIDTH'].iloc[0]), 4) if 'BB_WIDTH' in latest else 0,
                "upper": gv('BBU'),
                "lower": gv('BBL')
            },
            "atr": gv('ATR'),
            "rsi": gv('RSI'),
            "ichimoku": {
                "tenkan": gv('ITS_'),
                "kijun": gv('IKS_'),
                "senkou_a": gv('ISA_'),
                "senkou_b": gv('ISB_')
            }
        }
        return res
        
    except Exception as e:
        print(f"Error enriching {ticker}: {e}")
        return None

def batch_enrich(tickers: list) -> dict:
    results = {}
    for t in tickers:
        print(f"Enriching {t}...")
        res = enrich_ticker(t)
        if res:
            results[t] = res
        time.sleep(0.5)
    return results

if __name__ == "__main__":
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    result = enrich_ticker(ticker)
    if result:
        print(json.dumps(result, indent=2, default=str))
