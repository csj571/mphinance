"""
Signal History Archiver — extracts key signals from ticker payload for backtesting.

Writes one CSV row per (ticker, date) to docs/backtesting/signal_history.csv.
This is the lightweight backtest input — no need to parse full latest.json files.

CSV columns:
  date, ticker, price, change_pct, grade, tech_score, fund_score,
  trend, ema_stack, rsi, adx, valuation_status, gap_pct, fair_value,
  iv, hv, call_vol, put_vol, pc_ratio, inst_direction, inst_conviction
"""

import csv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BACKTEST_DIR = PROJECT_ROOT / "docs" / "backtesting"
SIGNAL_CSV = BACKTEST_DIR / "signal_history.csv"

CSV_FIELDS = [
    "date", "ticker", "price", "change_pct",
    "grade", "tech_score", "fund_score",
    "trend", "ema_stack", "rsi", "adx",
    "valuation_status", "gap_pct", "fair_value",
    "iv", "hv",
    "call_vol", "put_vol", "pc_ratio",
    "inst_direction", "inst_conviction",
]


def _safe(val, default=""):
    """Safely coerce value to string, handling None and NaN."""
    if val is None:
        return default
    try:
        import math
        if isinstance(val, float) and math.isnan(val):
            return default
    except (TypeError, ValueError):
        pass
    return val


def extract_signals(payload: dict, date: str) -> dict:
    """Extract key backtest signals from a full ticker payload."""
    ta = payload.get("technical_analysis", {})
    osc = ta.get("oscillators", {})
    scores = payload.get("scores", {})
    val = payload.get("valuation", {})
    vs = payload.get("volumeStats", {})
    tt = payload.get("tickertrace", {})
    sig = tt.get("signal", {}) or {}

    return {
        "date": date,
        "ticker": payload.get("ticker", ""),
        "price": payload.get("currentPrice", 0),
        "change_pct": payload.get("priceChangePct", 0),
        "grade": scores.get("grade", ""),
        "tech_score": scores.get("technical", ""),
        "fund_score": scores.get("fundamental", ""),
        "trend": payload.get("trendOverall", ""),
        "ema_stack": ta.get("ema_stack", ""),
        "rsi": _safe(osc.get("rsi_14")),
        "adx": _safe(osc.get("adx_14")),
        "valuation_status": val.get("status", ""),
        "gap_pct": _safe(val.get("gap_pct")),
        "fair_value": _safe(val.get("target_price")),
        "iv": payload.get("impliedVolatility", 0),
        "hv": payload.get("historicVolatility", 0),
        "call_vol": vs.get("callVolume", 0),
        "put_vol": vs.get("putVolume", 0),
        "pc_ratio": vs.get("pcRatioVol", 0),
        "inst_direction": sig.get("direction", ""),
        "inst_conviction": _safe(sig.get("conviction")),
    }


def archive_signal(payload: dict, date: str):
    """
    Extract signals from a ticker payload and append to signal_history.csv.

    Idempotent — skips if (date, ticker) already exists.
    """
    BACKTEST_DIR.mkdir(parents=True, exist_ok=True)

    signals = extract_signals(payload, date)
    ticker = signals["ticker"]
    if not ticker:
        return

    # Check for existing entry (avoid duplicates on re-runs)
    if SIGNAL_CSV.exists():
        with open(SIGNAL_CSV, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("date") == date and row.get("ticker") == ticker:
                    return  # Already archived

    # Write header if file doesn't exist
    write_header = not SIGNAL_CSV.exists()

    with open(SIGNAL_CSV, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow(signals)

    print(f"    📊 Archived signal: {ticker} ({date})")


def archive_all_signals(payloads: list[dict], date: str):
    """Archive signals for a batch of ticker payloads."""
    for payload in payloads:
        try:
            archive_signal(payload, date)
        except Exception as e:
            print(f"    [WARN] Signal archive failed for {payload.get('ticker', '?')}: {e}")
