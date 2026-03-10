"""
TickerTrace API client — institutional ETF activity data.

Calls the deployed TickerTrace API to get what institutions are buying/selling.
"""

import re
import httpx
from dossier.config import TICKERTRACE_API_BASE
from dossier.utils.retry import retry


# ── Junk ticker filter ──
# CUSIPs (e.g. "912797RS8"), money-market funds (FGXXX, SPAXX), and "OTHER"
_JUNK_RE = re.compile(
    r"^\d{3,}"          # starts with 3+ digits  → CUSIP
    r"|XXX$"            # ends in XXX            → money market (FGXXX, SPAXX)
    r"|^OTHER$"         # literal OTHER
    r"|^CASH$"          # literal CASH
    r"|^N/?A$",         # N/A
    re.IGNORECASE,
)


def _is_junk(ticker: str) -> bool:
    """Return True if the ticker is a CUSIP, money-market fund, or garbage."""
    if not ticker or not isinstance(ticker, str):
        return True
    return bool(_JUNK_RE.search(ticker.strip()))


def _filter_signals(items: list) -> list:
    """Remove junk tickers from a list of signal dicts (key: 'ticker')."""
    return [s for s in items if not _is_junk(s.get("ticker", ""))]


def _filter_divergences(items: list) -> list:
    """Remove junk tickers from divergence dicts."""
    return [d for d in items if not _is_junk(d.get("ticker", ""))]


@retry(max_retries=3, initial_delay=2.0)
def _get(endpoint: str, params: dict = None) -> dict:
    """Make a GET request to the TickerTrace API with automatic retry."""
    url = f"{TICKERTRACE_API_BASE}{endpoint}"
    with httpx.Client(timeout=15.0, follow_redirects=True) as client:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()


def get_signals() -> dict:
    """Full signal payload: buying/selling with conviction, sector flow, divergences."""
    return _get("/api/v1/signals")


def get_changes(direction: str = None, limit: int = 50) -> dict:
    params = {"limit": limit}
    if direction:
        params["direction"] = direction
    return _get("/api/v1/changes", params)


def get_sectors() -> dict:
    return _get("/api/v1/sectors")


def get_divergences() -> list:
    return _get("/api/v1/divergences")


def get_ticker_detail(ticker: str) -> dict:
    return _get(f"/api/v1/ticker/{ticker}")


def get_stats() -> dict:
    return _get("/api/v1/stats")


def fetch_institutional_data() -> dict:
    """Main entry point: fetch all institutional data needed for the report."""
    print("  Fetching TickerTrace institutional data...")

    try:
        payload = get_signals()
    except Exception as e:
        print(f"  [WARN] TickerTrace unavailable after retries: {e}")
        payload = {}
    if not payload:
        return {
            "as_of_date": "unknown",
            "stats": {},
            "top_buying": [],
            "top_selling": [],
            "sector_inflows": [],
            "sector_outflows": [],
            "divergences": [],
            "recent_changes": [],
        }

    signals = payload.get("signals", {})
    sector_flow = payload.get("sectorFlow", {})

    # Filter out CUSIPs, money-market tickers, and garbage from all lists
    buying = _filter_signals(signals.get("buying", []))
    selling = _filter_signals(signals.get("selling", []))
    divergences = _filter_divergences(payload.get("divergences", []))
    changes = _filter_signals(payload.get("changes", [])[:50])

    filtered_count = (
        len(signals.get("buying", [])) - len(buying)
        + len(signals.get("selling", [])) - len(selling)
        + len(payload.get("divergences", [])) - len(divergences)
    )
    if filtered_count:
        print(f"  Filtered {filtered_count} non-equity entries (CUSIPs, money markets)")

    return {
        "as_of_date": payload.get("asOfDate", "unknown"),
        "stats": payload.get("stats", {}),
        "top_buying": buying,
        "top_selling": selling,
        "sector_inflows": sector_flow.get("inflows", []),
        "sector_outflows": sector_flow.get("outflows", []),
        "divergences": divergences,
        "recent_changes": changes[:25],
    }

