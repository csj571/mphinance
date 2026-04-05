"""
Ghost Alpha VWAP Reclaim — Strategy Configuration

All parameters from the Substack article + optimal_config.json.
Capital is dynamic: 50% of actual Tradier account balance.

© mphinance + Sam the Quant Ghost
"""

# ── Strategy Parameters ──────────────────────────────────────────
CAPITAL_FRACTION = 0.50          # Use 50% of actual Tradier balance
MAX_POSITIONS = 2                # Max concurrent positions
ATR_MULT = 1.25                  # Trailing stop: 1.25x daily ATR
SPY_ADX_THRESHOLD = 20.0         # No trade if SPY ADX < 20
DAILY_LOSS_LIMIT = -500          # Stop trading if daily P&L < -$500
BEAR_CONVICTION = 0.70           # 70% size on bear-trend days
MIN_GRADE = "B"                  # Only trade Grade A or B picks
VALID_GRADES = ("A", "B")

# ── Timing (Eastern Time) ────────────────────────────────────────
MARKET_OPEN_HOUR = 9
MARKET_OPEN_MIN = 30
BOOT_HOUR = 9
BOOT_MIN = 15
MONITOR_START_HOUR = 9
MONITOR_START_MIN = 35            # Start VWAP monitoring 5 min after open
EOD_CLOSE_HOUR = 15
EOD_CLOSE_MIN = 55                # Force close at 3:55 PM ET
EOD_SHUTDOWN_HOUR = 16
EOD_SHUTDOWN_MIN = 5              # Shutdown loop at 4:05 PM ET
VWAP_POLL_SECONDS = 60            # Check for VWAP reclaim every 60s
TRAIL_POLL_SECONDS = 30           # Check trailing stop every 30s

# ── Wash Sale Rule ───────────────────────────────────────────────
WASH_SALE_DAYS = 30               # Can't trade same ticker for 30 days after a loss

# ── Tradier API ──────────────────────────────────────────────────
TRADIER_BASE = "https://api.tradier.com/v1"

# ── Daily Screener ───────────────────────────────────────────────
DAILY_JSON_URL = "https://mphinance.github.io/mphinance/leveraged-screener/daily.json"

# ── Discord ──────────────────────────────────────────────────────
SAM_CHANNEL_ID = "1408076378225643540"  # #sam-mph

# ── Files ────────────────────────────────────────────────────────
TRADE_JOURNAL_FILE = "data/trade_journal.json"
WASH_SALE_FILE = "data/wash_sales.json"
