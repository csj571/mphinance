#!/usr/bin/env python3
"""
Batch Scanner - Run all strategies and send results to Google Sheets

Usage:
    python batch_scanner.py                    # Run all strategies
    python batch_scanner.py --strategies "Momentum with Pullback,MEME Screen"
    python batch_scanner.py --dry-run          # Print results, don't send to Sheets
    
Cron Example (daily at 4pm):
    0 16 * * 1-5 cd /path/to/nice && .venv/bin/python batch_scanner.py >> logs/batch.log 2>&1
"""

import os
import sys
import json
import argparse
import requests
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Import strategies
from strategies import get_strategy_names, get_strategy

# Configuration
SHEETS_WEBHOOK = os.getenv("GOOGLE_SHEETS_WEBHOOK", "")

# Strategies to run (in order)
ALL_STRATEGIES = [
    "Momentum with Pullback",
    "Volatility Squeeze",
    "MEME Screen",
    "Small Cap Multibaggers",
    "Gamma Scan",
    "EMA Cross Momentum",
    "Bearish EMA Cross (Down)",
    # "Cash Secured Puts",  # Uncomment if you want CSP scan
]

# Priority columns per strategy (for cleaner Sheets output)
PRIORITY_COLS = {
    'Gamma Scan': ['close', 'sector', 'Expiration', 'TopWallStrike', 'TopWallOI', 'TopWallType', 'PctAway', 'WallSummary', 'TotalNearbyOI', 'ADX'],
    'MEME Screen': ['close', 'IV', 'volume', 'sector', 'change', 'market_cap_basic'],
    'Volatility Squeeze': ['close', 'sector', 'SqueezeRatio', 'Signals', 'ADX', 'RSI', 'relative_volume_10d_calc'],
    'Momentum with Pullback': ['close', 'sector', 'ADX', 'Stoch_K', 'RSI', 'SqueezeRatio'],
    'Small Cap Multibaggers': ['close', 'sector', 'market_cap_basic', 'gross_margin', 'revenue_growth', 'net_debt_ebitda'],
}

EXCLUDE_COLS = [
    'gross_margin', 'revenue_growth', 'earnings_per_share', 'total_revenue', 'net_income',
    'type', 'is_primary', 'EMA8|1W', 'EMA21|1W', 'EMA34|1W', 'EMA55|1W', 'EMA89|1W',
    'EMA8|1M', 'EMA21|1M', 'EMA34|1M', 'EMA55|1M', 'EMA89|1M', 'SMA50|1W', 'EMA200|1W', 'SMA50|1M', 'EMA200|1M'
]


def run_strategy(strategy_name: str, params: dict = None) -> pd.DataFrame:
    """Run a single strategy and return results DataFrame."""
    print(f"\n{'='*60}")
    print(f"📊 Running: {strategy_name}")
    print(f"{'='*60}")
    
    try:
        strategy = get_strategy(strategy_name)
        params = params or strategy.get_default_params()
        
        # Build and execute query
        query = strategy.build_query(params)
        count, df = query.get_scanner_data()
        
        print(f"  → Initial results: {count}")
        
        if count > 0 and not df.empty:
            # Post-process
            df = strategy.post_process(df, params)
            print(f"  → After post-process: {len(df)}")
            return df
        
        return pd.DataFrame()
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return pd.DataFrame()


def send_to_sheets(df: pd.DataFrame, strategy_name: str) -> bool:
    """Send results to Google Sheets."""
    if not SHEETS_WEBHOOK:
        print("  ⚠️ GOOGLE_SHEETS_WEBHOOK not configured")
        return False
    
    if df.empty:
        print("  → No data to send")
        return True
    
    # Calculate week ending
    today = datetime.now()
    days_until_sunday = (6 - today.weekday()) % 7
    week_ending = today + timedelta(days=days_until_sunday) if days_until_sunday > 0 else today
    week_ending_str = week_ending.strftime('%Y-%m-%d')
    
    # Build ordered columns
    priority = PRIORITY_COLS.get(strategy_name, [])
    ordered_cols = [c for c in priority if c in df.columns]
    for c in df.columns:
        if c not in ordered_cols and c not in ['name', 'description'] and c not in EXCLUDE_COLS:
            ordered_cols.append(c)
    
    # Build payload
    sheets_data = []
    for _, row in df.iterrows():
        record = {
            'Symbol': str(row.get('name', '')),
            'Company': str(row.get('description', ''))[:50],
            'WeekEnding': week_ending_str,
        }
        
        for col in ordered_cols:
            val = row[col]
            if pd.isna(val):
                record[col] = ''
            elif isinstance(val, float):
                record[col] = round(val, 4) if abs(val) < 1000000 else f"{val:.0f}"
            else:
                record[col] = str(val)
        
        sheets_data.append(record)
    
    payload = {
        "data": sheets_data,
        "timestamp": datetime.now().isoformat(),
        "strategy": strategy_name
    }
    
    try:
        resp = requests.post(SHEETS_WEBHOOK, json=payload, timeout=30)
        if resp.status_code == 200:
            print(f"  ✅ Sent {len(sheets_data)} rows to Sheets")
            return True
        else:
            print(f"  ❌ Sheets error: {resp.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Sheets exception: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Batch Scanner - Run all strategies")
    parser.add_argument("--strategies", type=str, help="Comma-separated list of strategies to run")
    parser.add_argument("--dry-run", action="store_true", help="Don't send to Sheets, just print results")
    parser.add_argument("--list", action="store_true", help="List available strategies")
    args = parser.parse_args()
    
    if args.list:
        print("Available strategies:")
        for name in get_strategy_names():
            print(f"  - {name}")
        return
    
    # Determine which strategies to run
    if args.strategies:
        strategies = [s.strip() for s in args.strategies.split(",")]
    else:
        strategies = ALL_STRATEGIES
    
    print(f"\n🚀 Batch Scanner Started: {datetime.now().isoformat()}")
    print(f"   Strategies: {len(strategies)}")
    print(f"   Sheets Webhook: {'✓ Configured' if SHEETS_WEBHOOK else '✗ Not configured'}")
    print(f"   Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    
    results_summary = {}
    
    for strategy_name in strategies:
        if strategy_name not in get_strategy_names():
            print(f"\n⚠️ Unknown strategy: {strategy_name}")
            continue
        
        df = run_strategy(strategy_name)
        results_summary[strategy_name] = len(df)
        
        if not df.empty:
            if args.dry_run:
                print(f"\n  [DRY RUN] Would send {len(df)} rows:")
                print(df[['name', 'close']].head(10).to_string())
            else:
                send_to_sheets(df, strategy_name)
    
    # ── CBOE Options Alerts ──
    print(f"\n{'='*60}")
    print(f"🔔 Running: CBOE Options Alerts")
    print(f"{'='*60}")
    try:
        from cboe_weekly_scanner import scan as cboe_scan
        cboe_result = cboe_scan(dry_run=args.dry_run, output_json=True)

        # Build a DataFrame from the diff for Sheets
        new_rows = []
        for category, label in [
            ("optionable", "Newly Optionable"),
            ("weekly_etfs", "New Weekly ETF"),
            ("weekly_equities", "New Weekly Equity"),
        ]:
            for ticker, name in cboe_result["diff"][category]["new"].items():
                new_rows.append({
                    "name": ticker,
                    "description": name,
                    "close": "",
                    "Type": label,
                })
        for category, label in [
            ("optionable", "Options Removed"),
            ("weekly_etfs", "Weekly ETF Removed"),
            ("weekly_equities", "Weekly Equity Removed"),
        ]:
            for ticker, name in cboe_result["diff"][category]["removed"].items():
                new_rows.append({
                    "name": ticker,
                    "description": name,
                    "close": "",
                    "Type": label,
                })

        cboe_count = len(new_rows)
        results_summary["CBOE Options Alerts"] = cboe_count

        if new_rows:
            cboe_df = pd.DataFrame(new_rows)
            if args.dry_run:
                print(f"\n  [DRY RUN] Would send {cboe_count} options alerts:")
                print(cboe_df.to_string(index=False))
            else:
                send_to_sheets(cboe_df, "CBOE Options Alerts")
        else:
            print("  ✅ No new options changes detected")

    except Exception as e:
        print(f"  ❌ CBOE scan error: {e}")
        results_summary["CBOE Options Alerts"] = 0

    # Summary
    print(f"\n{'='*60}")
    print("📋 SUMMARY")
    print(f"{'='*60}")
    for name, count in results_summary.items():
        status = "✅" if count > 0 else "○"
        print(f"  {status} {name}: {count} results")
    
    print(f"\n✓ Completed at {datetime.now().isoformat()}")


if __name__ == "__main__":
    main()
