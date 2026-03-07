"""
Signal Persistence Tracker — 21-day rolling window.

Tracks which tickers appear in scans over time to identify:
- Lifers: 20+ consecutive days (strong institutional commitment)
- High Conviction: 10-19 days (sustained interest)
- New Signals: 1-3 days

Storage: GCS bucket (cloud) with local filesystem fallback (dev).
"""

import json
from datetime import datetime, timedelta
from dossier.config import PERSISTENCE_DIR


PERSISTENCE_FILE = PERSISTENCE_DIR / "signal_history.json"
# GCS path is relative — used when running in Cloud Run
GCS_PATH = "dossier/persistence/data/signal_history.json"
WINDOW_DAYS = 21


def _load_history() -> dict:
    """Load signal history from GCS, falling back to local file."""
    # Try GCS first
    try:
        from gcp.storage import gcs_read_json
        data = gcs_read_json(GCS_PATH, fallback_local=False)
        if data is not None:
            return data
    except ImportError:
        pass

    # Local fallback
    if PERSISTENCE_FILE.exists():
        try:
            with open(PERSISTENCE_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def _save_history(history: dict):
    """Save signal history to both GCS and local file."""
    # Write to GCS (also writes local as backup)
    try:
        from gcp.storage import gcs_write_json
        gcs_write_json(GCS_PATH, history, also_local=True)
        return
    except ImportError:
        pass

    # Pure local fallback
    PERSISTENCE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PERSISTENCE_FILE, "w") as f:
        json.dump(history, f, indent=2)


def _prune_old_dates(history: dict, today: str) -> dict:
    cutoff = datetime.strptime(today, "%Y-%m-%d") - timedelta(days=WINDOW_DAYS)
    cutoff_str = cutoff.strftime("%Y-%m-%d")

    pruned = {}
    for ticker, dates in history.items():
        valid = [d for d in dates if d >= cutoff_str]
        if valid:
            pruned[ticker] = valid
    return pruned


def update_persistence(tickers: list[str], date: str) -> dict:
    """
    Record today's scan tickers and return persistence classifications.

    Returns dict with lifers, high_conviction, new_signals, summary.
    """
    history = _load_history()
    history = _prune_old_dates(history, date)

    for ticker in tickers:
        if ticker not in history:
            history[ticker] = []
        if date not in history[ticker]:
            history[ticker].append(date)
            history[ticker].sort()

    _save_history(history)

    lifers = []
    high_conviction = []
    new_signals = []

    for ticker, dates in history.items():
        days = len(dates)

        if dates:
            sorted_dates = sorted(dates, reverse=True)
            streak = 1
            for i in range(1, len(sorted_dates)):
                d1 = datetime.strptime(sorted_dates[i - 1], "%Y-%m-%d")
                d2 = datetime.strptime(sorted_dates[i], "%Y-%m-%d")
                if (d1 - d2).days <= 3:
                    streak += 1
                else:
                    break
        else:
            streak = 0

        entry = {"ticker": ticker, "days": days, "streak": streak}

        if days >= 20:
            lifers.append(entry)
        elif days >= 10:
            high_conviction.append(entry)
        elif days <= 3:
            new_signals.append(entry)

    lifers.sort(key=lambda x: x["days"], reverse=True)
    high_conviction.sort(key=lambda x: x["days"], reverse=True)
    new_signals.sort(key=lambda x: x["days"], reverse=True)

    return {
        "lifers": lifers,
        "high_conviction": high_conviction,
        "new_signals": new_signals,
        "summary": {
            "lifers": len(lifers),
            "high_conviction": len(high_conviction),
            "new_signals": len(new_signals),
            "total_tracked": len(history),
        },
    }
