"""
Ghost Alpha Dossier — Configuration

All tunable parameters in one place.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ─── Paths ────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent  # mphinance/
DOSSIER_ROOT = Path(__file__).resolve().parent          # mphinance/dossier/
OUTPUT_DIR = PROJECT_ROOT / "docs" / "reports"
PERSISTENCE_DIR = DOSSIER_ROOT / "persistence" / "data"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
PERSISTENCE_DIR.mkdir(parents=True, exist_ok=True)

# ─── Branding ─────────────────────────────────────────────────────
REPORT_TITLE = "GHOST ALPHA DOSSIER"
AUTHOR = "Sam the Quant Ghost"
DISCLAIMER = (
    "This report is for informational and educational purposes only. "
    "Not financial advice. Trade at your own risk. Past performance "
    "does not guarantee future results."
)

# ─── API Keys ─────────────────────────────────────────────────────
TICKERTRACE_API_BASE = os.getenv("TICKERTRACE_API_BASE", "https://api.tickertrace.com/api")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
AI_MODEL = os.getenv("AI_MODEL", "gemini-2.5-flash")

# ─── Watchlists ───────────────────────────────────────────────────

# Market pulse benchmarks (always shown at top of report)
MARKET_PULSE = [
    "SPY", "QQQ", "IWM", "DIA",   # US Indices
    "BTC-USD", "ETH-USD",          # Crypto
    "GLD", "TLT",                  # Safe havens
]

# Core watchlist — always scanned and enriched
CORE_WATCHLIST = [
    # Mega-cap tech
    "AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "TSLA",
    # Semis
    "AMD", "AVGO", "TSM", "MRVL", "QCOM",
    # Financials
    "JPM", "GS", "V", "MA",
    # Growth / Momentum favorites
    "PLTR", "COIN", "HOOD", "SOFI",
    # Energy / Resources
    "XOM", "OXY",
]

# Sector ETFs for rotation analysis
SECTOR_ETFS = [
    "XLK", "XLF", "XLE", "XLV", "XLI",
    "XLC", "XLRE", "XLP", "XLU", "XLB", "XLY",
]

# Max tickers to enrich for detailed dossiers (top N from scanners)
MAX_DOSSIER_TICKERS = 8

# ─── VIX Regimes ─────────────────────────────────────────────────
VIX_REGIMES = {
    "zen":   {"max": 15, "name": "🟢 Zen",   "desc": "Low vol — trend-following mode"},
    "calm":  {"max": 20, "name": "🔵 Calm",  "desc": "Normal — balanced setups"},
    "storm": {"max": 30, "name": "⚡ Storm", "desc": "Elevated vol — mean reversion setups"},
    "chaos": {"max": 999,"name": "🔴 Chaos", "desc": "Extreme vol — cash is king, hedge"},
}

# ─── Scanner Strategies to Run ────────────────────────────────────
# These map to mphinance/strategies/ — run during the scanner stage
SCANNER_STRATEGIES = [
    "Momentum with Pullback",
    "Volatility Squeeze",
    "EMA Cross Momentum",
    "Gamma Scan",
]
