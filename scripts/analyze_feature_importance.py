import pandas as pd
import yfinance as yf
import json
import time
import os
import glob
from sklearn.ensemble import RandomForestClassifier
from datetime import datetime, timedelta

# Constants
PROJECT_ROOT = "/home/sam/Antigravity/empty/mphinance"
HISTORY_DIR = os.path.join(PROJECT_ROOT, "data/screens_history")
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "docs/backtesting/feature_importance.json")

def load_all_history():
    files = glob.glob(os.path.join(HISTORY_DIR, "*.csv"))
    all_dfs = []
    for f in files:
        if "Fake_Strategy_History" in f:
            continue
        try:
            # use on_bad_lines='skip' to avoid crashing on malformed rows
            df = pd.read_csv(f, on_bad_lines='skip')
            # Normalize column names just in case
            df['scan_date'] = pd.to_datetime(df['timestamp']).dt.date
            all_dfs.append(df)
        except Exception as e:
            print(f"Error loading {f}: {e}")
    
    if not all_dfs:
        return pd.DataFrame()
    return pd.concat(all_dfs, ignore_index=True)

def extract_features(df):
    features = pd.DataFrame()
    
    # Ensure columns are numeric
    tech_cols = ['EMA8', 'EMA21', 'EMA34', 'EMA55', 'EMA89', 'ADX', 'RSI', 'Stoch_K', 'close', 'relative_volume_10d_calc']
    for col in tech_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Drop rows that failed conversion
    df.dropna(subset=tech_cols, inplace=True)

    # 1. EMA Alignment (Full Bullish)
    # EMA8 > EMA21 > EMA34 > EMA55 > EMA89
    features['ema_aligned'] = (
        (df['EMA8'] > df['EMA21']) & 
        (df['EMA21'] > df['EMA34']) & 
        (df['EMA34'] > df['EMA55']) & 
        (df['EMA55'] > df['EMA89'])
    ).astype(int)
    
    # 2. ADX Strong
    features['adx_strong'] = (df['ADX'] > 25).astype(int)
    features['adx_val'] = df['ADX']
    
    # 3. RSI
    features['rsi_val'] = df['RSI']
    features['rsi_oversold'] = (df['RSI'] < 40).astype(int)
    features['rsi_overbought'] = (df['RSI'] > 70).astype(int)
    
    # 4. Stochastic K
    features['stoch_oversold'] = (df['Stoch_K'] < 40).astype(int)
    features['stoch_val'] = df['Stoch_K']
    
    # 5. Relative Vol
    features['rel_vol'] = df['relative_volume_10d_calc']
    
    # 6. Price vs EMA21
    features['pct_from_ema21'] = (df['close'] - df['EMA21']) / df['EMA21'] * 100
    
    return features

def fetch_forward_returns(df):
    unique_tickers = df['ticker'].unique()
    # Tickers in CSV might have exchange prefix (e.g., NYSE:MMM)
    ticker_map = {t: t.split(':')[-1] for t in unique_tickers}
    yf_tickers = list(ticker_map.values())
    
    start_date = df['scan_date'].min()
    end_date = df['scan_date'].max() + timedelta(days=20)
    
    print(f"Fetching data for {len(yf_tickers)} tickers from {start_date} to {end_date}...")
    
    # Batch fetch to avoid rate limits
    batch_size = 50
    all_hist = {}
    for i in range(0, len(yf_tickers), batch_size):
        batch = yf_tickers[i:i+batch_size]
        print(f"Processing batch {i//batch_size + 1}...")
        try:
            data = yf.download(batch, start=start_date, end=end_date, interval='1d', progress=False, group_by='ticker')
            for t in batch:
                if len(batch) == 1:
                    all_hist[t] = data
                else:
                    all_hist[t] = data[t]
        except Exception as e:
            print(f"Error fetching batch: {e}")
        time.sleep(1)
        
    returns = []
    for _, row in df.iterrows():
        ticker_yf = ticker_map[row['ticker']]
        scan_dt = pd.to_datetime(row['scan_date'])
        
        fwd_return = 0
        if ticker_yf in all_hist:
            hist = all_hist[ticker_yf]
            if not hist.empty:
                # Get price at scan date or next available
                prices_after = hist[hist.index >= scan_dt]
                if len(prices_after) >= 6:
                    entry_price = prices_after['Close'].iloc[0]
                    exit_price = prices_after['Close'].iloc[5] # 5 trading days later
                    fwd_return = (exit_price - entry_price) / entry_price
                else:
                    fwd_return = None
            else:
                fwd_return = None
        else:
            fwd_return = None
        returns.append(fwd_return)
        
    return returns

def main():
    print("Loading history...")
    df = load_all_history()
    if df.empty:
        print("No data found.")
        return
    
    # Drop rows with missing crucial technicals
    df = df.dropna(subset=['ADX', 'RSI', 'Stoch_K', 'EMA8', 'EMA21', 'EMA34', 'EMA55', 'EMA89', 'close'])
    
    print(f"Extracted {len(df)} rows with technicals.")
    
    print("Calculating features...")
    X = extract_features(df)
    
    print("Fetching forward returns...")
    fwd_returns = fetch_forward_returns(df)
    df['fwd_5d'] = fwd_returns
    
    # Prepare training data
    data = pd.concat([X, df[['fwd_5d']]], axis=1)
    data = data.dropna()
    
    if len(data) < 20:
        print(f"Not enough data for ML: {len(data)} samples.")
        return

    X_train = data.drop(columns=['fwd_5d'])
    y_train = (data['fwd_5d'] > 0).astype(int) # Target: did it go up?
    
    print(f"Training RandomForest on {len(data)} samples...")
    rf = RandomForestClassifier(n_estimators=100, random_state=42)
    rf.fit(X_train, y_train)
    
    importances = rf.feature_importances_
    feature_names = X_train.columns
    
    ranked = sorted(zip(feature_names, importances), key=lambda x: x[1], reverse=True)
    
    result = {
        "features_ranked": [{"name": n, "importance": round(float(i), 4)} for n, i in ranked],
        "accuracy": round(float(rf.score(X_train, y_train)), 2), # Note: this is training accuracy
        "n_samples": len(data),
        "date_range": f"{df['scan_date'].min()} to {df['scan_date'].max()}"
    }
    
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(result, f, indent=2)
        
    print(f"Feature importance analysis complete. Saved to {OUTPUT_FILE}")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
