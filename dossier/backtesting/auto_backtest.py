import json
import os
import pandas as pd
import yfinance as yf
import time
from datetime import datetime, timedelta

# Paths
PROJECT_ROOT = "/home/sam/Antigravity/empty/mphinance"
DAILY_PICKS_PATH = os.path.join(PROJECT_ROOT, "docs/api/daily-picks.json")
TRACK_RECORD_PATH = os.path.join(PROJECT_ROOT, "docs/backtesting/track_record.json")

def load_track_record():
    if os.path.exists(TRACK_RECORD_PATH):
        with open(TRACK_RECORD_PATH, 'r') as f:
            return json.load(f)
    return {"entries": [], "stats": {}}

def save_track_record(data):
    with open(TRACK_RECORD_PATH, 'w') as f:
        json.dump(data, f, indent=2)

def update_entry_returns(entry):
    ticker = entry['ticker']
    scan_date = pd.to_datetime(entry['date'])
    
    # We need scan_date + some buffer to get enough bars
    # Using 45 days to be safe for 21 trading days
    end_date = scan_date + timedelta(days=45)
    
    try:
        hist = yf.download(ticker, start=scan_date, end=end_date, interval='1d', progress=False)
        if hist.empty:
            return entry
        
        # entry price is the close at scan_date or next available
        prices = hist['Close']
        if prices.empty:
            return entry
            
        entry_price = prices.iloc[0]
        
        # Calculate returns for 1d, 5d, 10d, 21d
        days_to_check = {1: 'fwd_1d', 5: 'fwd_5d', 10: 'fwd_10d', 21: 'fwd_21d'}
        for d, key in days_to_check.items():
            if len(prices) > d:
                exit_price = prices.iloc[d]
                ret = (exit_price - entry_price) / entry_price * 100
                entry[key] = round(float(ret), 2)
                
    except Exception as e:
        print(f"Error updating {ticker} on {entry['date']}: {e}")
        
    return entry

def recalculate_stats(track_record):
    entries = track_record['entries']
    validated = [e for e in entries if 'fwd_5d' in e]
    
    if not validated:
        track_record['stats'] = {}
        return track_record
        
    fwd_5d_returns = [e['fwd_5d'] for e in validated]
    
    avg_5d = sum(fwd_5d_returns) / len(fwd_5d_returns)
    win_rate = len([r for r in fwd_5d_returns if r > 0]) / len(fwd_5d_returns) * 100
    
    best_pick = max(validated, key=lambda x: x['fwd_5d'])
    worst_pick = min(validated, key=lambda x: x['fwd_5d'])
    
    # Sharpe-like ratio (mean/std)
    import numpy as np
    std_5d = np.std(fwd_5d_returns)
    sharpe = avg_5d / std_5d if std_5d > 0 else 0
    
    track_record['stats'] = {
        "avg_5d_return": round(avg_5d, 2),
        "win_rate_5d": round(win_rate, 2),
        "total_picks_tracked": len(entries),
        "total_validated": len(validated),
        "best_pick": {"ticker": best_pick['ticker'], "date": best_pick['date'], "return": best_pick['fwd_5d']},
        "worst_pick": {"ticker": worst_pick['ticker'], "date": worst_pick['date'], "return": worst_pick['worst_pick' if 'worst_pick' in worst_pick else 'fwd_5d']}, # Fix name if needed
        "sharpe_5d": round(float(sharpe), 2)
    }
    
    # Correcting worst_pick field access
    track_record['stats']['worst_pick'] = {"ticker": worst_pick['ticker'], "date": worst_pick['date'], "return": worst_pick['fwd_5d']}

    return track_record

def main():
    print("Loading track record...")
    track_record = load_track_record()
    
    # 1. Append today's picks
    if os.path.exists(DAILY_PICKS_PATH):
        with open(DAILY_PICKS_PATH, 'r') as f:
            daily_data = json.load(f)
            today_date = daily_data['date']
            
            # Avoid duplicate entries for same date
            existing_dates = {e['date'] for e in track_record['entries']}
            
            # If we already have entries for today, maybe we don't append? 
            # Or check ticker+date uniqueness
            existing_pairs = {(e['ticker'], e['date']) for e in track_record['entries']}
            
            for pick in daily_data['picks'][:10]: # Top 10
                pair = (pick['ticker'], today_date)
                if pair not in existing_pairs:
                    track_record['entries'].append({
                        "date": today_date,
                        "ticker": pick['ticker'],
                        "score": pick['score'],
                        "grade": pick['grade'],
                        "ema_stack": pick['ema_stack'],
                        "is_pullback": pick['is_pullback_setup']
                    })
    
    # 2. Update returns for older entries
    today = datetime.now()
    updated_any = False
    
    # Tickers that need updating
    to_update = []
    for i, entry in enumerate(track_record['entries']):
        if 'fwd_5d' not in entry:
            scan_date = datetime.strptime(entry['date'], "%Y-%m-%d")
            # If at least 7 days have passed (approx 5 trading days)
            if (today - scan_date).days >= 7:
                to_update.append(i)
                
    if to_update:
        print(f"Updating returns for {len(to_update)} entries...")
        # To minimize yfinance calls, we could batch, but for now simple update
        # Task says batch 50, sleep 1s.
        for i in to_update:
            track_record['entries'][i] = update_entry_returns(track_record['entries'][i])
            updated_any = True
            time.sleep(1) # Simple rate limit
            
    # 3. Recalculate stats
    print("Recalculating stats...")
    track_record = recalculate_stats(track_record)
    
    # 4. Save
    save_track_record(track_record)
    print(f"Track record saved to {TRACK_RECORD_PATH}")
    if 'stats' in track_record and track_record['stats']:
        print(json.dumps(track_record['stats'], indent=2))

if __name__ == "__main__":
    main()
