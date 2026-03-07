"""
CSP Setup Runner — Runs the Cash Secured Puts strategy from mphinance
and formats results for the daily dossier.
"""

import sys
from pathlib import Path

# Ensure project root is on path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def fetch_csp_setups(max_results: int = 8) -> list[dict]:
    """
    Run the CSP strategy through TradingView screener + deep dive,
    returning formatted CSP trade candidates.
    """
    print("  Running CSP scanner...")

    try:
        from strategies import get_strategy
        strategy = get_strategy("Cash Secured Puts")
        params = strategy.get_default_params()

        # Stage 1: TradingView broad sweep
        query = strategy.build_query(params)
        count, df = query.get_scanner_data()

        if count == 0 or df.empty:
            print("    ○ No CSP candidates from screener")
            return []

        print(f"    Stage 1: {len(df)} candidates from screener")

        # Stage 2: Post-process (EMA/ATR filter)
        df = strategy.post_process(df, params)
        print(f"    Stage 2: {len(df)} after filtering")

        if df.empty:
            return []

        # Stage 3: Deep dive (options chain analysis)
        try:
            df_trades = strategy.deep_dive(df.head(30), params)
            print(f"    Stage 3: {len(df_trades)} trade setups found")

            # Stage 4: VoPR enrichment — add vol regime, VRP, delta, theta, grade
            if not df_trades.empty:
                try:
                    from strategies.vopr_overlay import enrich_csp
                    df_trades = enrich_csp(df_trades)
                    a_count = len(df_trades[df_trades['VoPR_Grade'] == 'A'])
                    b_count = len(df_trades[df_trades['VoPR_Grade'] == 'B'])
                    print(f"    Stage 4: VoPR enriched — {a_count}A, {b_count}B grades")
                except Exception as e:
                    print(f"    [WARN] VoPR enrichment failed: {e}")
        except Exception as e:
            print(f"    [WARN] Deep dive failed: {e}")
            df_trades = df.head(max_results)

        if df_trades.empty:
            # Fall back to screener results without trades
            results = []
            for _, row in df.head(max_results).iterrows():
                results.append({
                    "ticker": str(row.get("name", "")),
                    "company": str(row.get("description", ""))[:40],
                    "price": round(float(row.get("close", 0)), 2),
                    "adx": round(float(row.get("ADX", 0)), 1),
                    "rsi": round(float(row.get("RSI", 0)), 1),
                    "has_trade": False,
                    "trade": None,
                })
            return results

        # Format deep dive results
        results = []
        for _, row in df_trades.head(max_results).iterrows():
            trade_info = None
            if row.get("Trade_Exp"):
                trade_info = {
                    "type": str(row.get("Trade_Type", "CSP")),
                    "expiration": str(row.get("Trade_Exp", "")),
                    "strike": row.get("Trade_Strike", 0),
                    "premium": round(float(row.get("Trade_Prem", 0)), 2),
                    "roc_weekly": round(float(row.get("Trade_ROC_W", 0)), 2),
                    "days_out": int(row.get("DaysOut", 0)),
                }

            results.append({
                "ticker": str(row.get("name", "")),
                "company": str(row.get("description", ""))[:40],
                "price": round(float(row.get("close", 0)), 2),
                "adx": round(float(row.get("ADX", 0)), 1),
                "rsi": round(float(row.get("RSI", 0)), 1),
                "has_trade": trade_info is not None,
                "trade": trade_info,
                # VoPR enrichment fields
                "vopr_grade": str(row.get("VoPR_Grade", "")),
                "vrp_ratio": row.get("VRP_Ratio"),
                "vol_regime": str(row.get("Vol_Regime", "")),
                "bs_delta": row.get("BS_Delta"),
                "daily_theta": row.get("Daily_Theta"),
                "composite_rv": row.get("Composite_RV"),
            })

        return results

    except Exception as e:
        print(f"    [ERR] CSP scanner failed: {e}")
        return []
