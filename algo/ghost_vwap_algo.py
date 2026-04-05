#!/usr/bin/env python3
"""
👻 Ghost Alpha VWAP Reclaim — Automated Algo Trader

THE strategy from "The 5.8% Weekly Edge" Substack article, fully automated.

Architecture:
  9:15 AM ET  → Boot up, load daily.json from GitHub Pages
  9:25 AM ET  → Verify SPY ADX ≥ 20, skip day if not
  9:35 AM ET  → Start monitoring top 2 Grade A/B picks for VWAP reclaim
  SIGNAL      → Submit LIMIT BUY at bid price via Tradier
  FILLED      → Start trailing stop monitor (1.25x ATR, poll every 30s)
  3:55 PM ET  → Force-close any open positions (market sell)
  4:00 PM ET  → Log results to trade journal

Safety:
  - 50% of actual Tradier balance, split across 2 positions
  - $500 daily loss limit
  - Limit orders only (bid price)
  - No overnight holds (force-close 3:55 PM)
  - Wash sale rule: 30-day blacklist per ticker after a loss
  - 100% size bull trend / 70% size bear trend

Usage:
    python3 ghost_vwap_algo.py --live          # LIVE trading
    python3 ghost_vwap_algo.py                 # Dry-run mode (default)

© mphinance + Sam the Quant Ghost
"Don't pee upwind. Don't trade against the trend. Same energy."
"""

import argparse
import json
import os
import subprocess
import sys
import time
import traceback
from datetime import datetime, timedelta, date
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

# ── Local config ──────────────────────────────────────────────────
from config import (
    CAPITAL_FRACTION, MAX_POSITIONS, ATR_MULT, SPY_ADX_THRESHOLD,
    DAILY_LOSS_LIMIT, BEAR_CONVICTION, VALID_GRADES, WASH_SALE_DAYS,
    TRADIER_BASE, DAILY_JSON_URL, SAM_CHANNEL_ID,
    MONITOR_START_HOUR, MONITOR_START_MIN,
    EOD_CLOSE_HOUR, EOD_CLOSE_MIN, EOD_SHUTDOWN_HOUR, EOD_SHUTDOWN_MIN,
    VWAP_POLL_SECONDS, TRAIL_POLL_SECONDS,
    TRADE_JOURNAL_FILE, WASH_SALE_FILE,
)

ET = ZoneInfo("America/New_York")
SCRIPT_DIR = Path(__file__).resolve().parent

# ══════════════════════════════════════════════════════════════════
# SECRETS
# ══════════════════════════════════════════════════════════════════

def load_secrets():
    """Load from environment (set by systemd EnvironmentFile) or secrets.env."""
    token = os.environ.get("TRADIER_ACCESS_TOKEN") or os.environ.get("TRADIER_API_KEY")
    account = os.environ.get("TRADIER_ACCOUNT_ID")
    discord_token = os.environ.get("DISCORD_BOT_TOKEN")

    # Fallback: parse secrets.env in script directory
    if not token or not account:
        env_file = SCRIPT_DIR / "secrets.env"
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip().strip('"').strip("'")
                    os.environ.setdefault(k, v)
            token = os.environ.get("TRADIER_ACCESS_TOKEN") or os.environ.get("TRADIER_API_KEY")
            account = os.environ.get("TRADIER_ACCOUNT_ID")
            discord_token = os.environ.get("DISCORD_BOT_TOKEN")

    if not token or not account:
        log("❌ TRADIER_ACCESS_TOKEN and TRADIER_ACCOUNT_ID required")
        sys.exit(1)

    return token, account, discord_token


TRADIER_TOKEN = None
TRADIER_ACCOUNT = None
DISCORD_BOT_TOKEN = None


def tradier_headers():
    return {"Authorization": f"Bearer {TRADIER_TOKEN}", "Accept": "application/json"}


# ══════════════════════════════════════════════════════════════════
# LOGGING
# ══════════════════════════════════════════════════════════════════

def log(msg: str, level: str = "INFO"):
    ts = datetime.now(ET).strftime("%Y-%m-%d %H:%M:%S ET")
    prefix = {"INFO": "📊", "TRADE": "💰", "WARN": "⚠️", "ERROR": "❌", "SKIP": "🚫"}.get(level, "ℹ️")
    line = f"[{ts}] {prefix} {msg}"
    print(line, flush=True)
    return line


def discord_alert(msg: str):
    """Post trade alert to Discord #sam-mph via bot token."""
    if not DISCORD_BOT_TOKEN:
        return
    try:
        url = f"https://discord.com/api/v10/channels/{SAM_CHANNEL_ID}/messages"
        payload = json.dumps({"content": msg[:1950]})
        subprocess.run(
            ['curl', '-s', '-X', 'POST', url,
             '-H', f'Authorization: Bot {DISCORD_BOT_TOKEN}',
             '-H', 'Content-Type: application/json',
             '-d', payload],
            capture_output=True, text=True, timeout=10
        )
    except Exception:
        pass  # Non-critical


# ══════════════════════════════════════════════════════════════════
# TRADIER API
# ══════════════════════════════════════════════════════════════════

def tradier_get(endpoint: str, params: dict = None) -> dict | None:
    """GET request to Tradier API with retry."""
    url = f"{TRADIER_BASE}{endpoint}"
    for attempt in range(3):
        try:
            resp = requests.get(url, params=params, headers=tradier_headers(), timeout=15)
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code == 429:  # Rate limit
                time.sleep(2 ** attempt)
                continue
            log(f"Tradier GET {endpoint} → {resp.status_code}: {resp.text[:200]}", "WARN")
            return None
        except Exception as e:
            log(f"Tradier GET {endpoint} error: {e}", "WARN")
            time.sleep(1)
    return None


def tradier_post(endpoint: str, data: dict = None) -> dict | None:
    """POST request to Tradier API."""
    url = f"{TRADIER_BASE}{endpoint}"
    try:
        resp = requests.post(url, data=data, headers=tradier_headers(), timeout=15)
        if resp.status_code in (200, 201):
            return resp.json()
        log(f"Tradier POST {endpoint} → {resp.status_code}: {resp.text[:300]}", "WARN")
        return None
    except Exception as e:
        log(f"Tradier POST {endpoint} error: {e}", "ERROR")
        return None


def get_account_balance() -> float:
    """Get current account equity from Tradier."""
    data = tradier_get(f"/accounts/{TRADIER_ACCOUNT}/balances")
    if not data:
        return 0.0
    bal = data.get("balances", {})
    # For margin accounts, use 'equity'; for cash, use 'total_cash'
    equity = bal.get("equity", 0) or bal.get("total_cash", 0) or bal.get("total_equity", 0)
    return float(equity) if equity else 0.0


def get_positions() -> list[dict]:
    """Get current open positions."""
    data = tradier_get(f"/accounts/{TRADIER_ACCOUNT}/positions")
    if not data:
        return []
    pos = data.get("positions", {})
    if not pos or pos == "null":
        return []
    positions = pos.get("position", [])
    if isinstance(positions, dict):
        positions = [positions]
    return positions or []


def get_quote(symbol: str) -> dict | None:
    """Get real-time quote for a symbol."""
    data = tradier_get("/markets/quotes", {"symbols": symbol})
    if not data:
        return None
    quotes = data.get("quotes", {}).get("quote", {})
    if isinstance(quotes, list):
        quotes = quotes[0] if quotes else {}
    return quotes if quotes and quotes != "null" else None


def get_5m_candles(symbol: str) -> list[dict]:
    """Get today's 5-minute candles from Tradier timesales."""
    today = datetime.now(ET).strftime("%Y-%m-%d")
    data = tradier_get("/markets/timesales", {
        "symbol": symbol,
        "interval": "5min",
        "start": f"{today} 09:30",
        "end": f"{today} 16:00",
        "session_filter": "open",
    })
    if not data:
        return []
    series = data.get("series", {})
    if not series or series == "null":
        return []
    candles = series.get("data", [])
    if isinstance(candles, dict):
        candles = [candles]
    return candles or []


def get_market_clock() -> dict | None:
    """Check if market is open."""
    data = tradier_get("/markets/clock")
    if not data:
        return None
    return data.get("clock", {})


def submit_limit_buy(symbol: str, qty: int, price: float, dry_run: bool = True) -> dict | None:
    """Submit a limit buy order."""
    if dry_run:
        log(f"🔇 DRY RUN: Would BUY {qty} {symbol} @ ${price:.2f} (${qty * price:,.2f})", "TRADE")
        return {"order": {"id": "DRY_RUN", "status": "ok"}}

    data = {
        "class": "equity",
        "symbol": symbol,
        "side": "buy",
        "quantity": str(qty),
        "type": "limit",
        "price": f"{price:.2f}",
        "duration": "day",
    }
    result = tradier_post(f"/accounts/{TRADIER_ACCOUNT}/orders", data)
    if result:
        order_id = result.get("order", {}).get("id", "unknown")
        log(f"✅ BUY ORDER PLACED: {qty} {symbol} @ ${price:.2f} (Order #{order_id})", "TRADE")
        discord_alert(f"🟢 **BUY** {qty} {symbol} @ ${price:.2f} | Order #{order_id}")
    return result


def submit_market_sell(symbol: str, qty: int, dry_run: bool = True) -> dict | None:
    """Submit a market sell order (EOD close)."""
    if dry_run:
        log(f"🔇 DRY RUN: Would SELL {qty} {symbol} at market", "TRADE")
        return {"order": {"id": "DRY_RUN", "status": "ok"}}

    data = {
        "class": "equity",
        "symbol": symbol,
        "side": "sell",
        "quantity": str(qty),
        "type": "market",
        "duration": "day",
    }
    result = tradier_post(f"/accounts/{TRADIER_ACCOUNT}/orders", data)
    if result:
        order_id = result.get("order", {}).get("id", "unknown")
        log(f"✅ SELL ORDER PLACED: {qty} {symbol} at market (Order #{order_id})", "TRADE")
        discord_alert(f"🔴 **SELL** {qty} {symbol} at market | Order #{order_id}")
    return result


def get_order_status(order_id: str) -> str:
    """Check order fill status."""
    data = tradier_get(f"/accounts/{TRADIER_ACCOUNT}/orders/{order_id}")
    if not data:
        return "unknown"
    order = data.get("order", {})
    return order.get("status", "unknown")


# ══════════════════════════════════════════════════════════════════
# VWAP CALCULATION
# ══════════════════════════════════════════════════════════════════

def compute_vwap(candles: list[dict]) -> list[float]:
    """Compute running VWAP from intraday candles."""
    cum_vol = 0.0
    cum_tp_vol = 0.0
    vwaps = []
    for c in candles:
        h = float(c.get("high", 0))
        l = float(c.get("low", 0))
        cl = float(c.get("close", 0))
        v = float(c.get("volume", 0))
        tp = (h + l + cl) / 3
        cum_vol += v
        cum_tp_vol += tp * v
        vwaps.append(cum_tp_vol / cum_vol if cum_vol > 0 else tp)
    return vwaps


# ══════════════════════════════════════════════════════════════════
# DAILY SCREENER
# ══════════════════════════════════════════════════════════════════

def fetch_daily_picks() -> dict | None:
    """Fetch today's screener — try GH Pages first, then local file."""
    # Try GitHub Pages
    try:
        resp = requests.get(DAILY_JSON_URL, timeout=15)
        if resp.status_code == 200:
            log("📡 Screener loaded from GitHub Pages")
            return resp.json()
    except Exception as e:
        log(f"GH Pages fetch error: {e}", "WARN")

    # Fallback: local file (synced by deploy or pipeline)
    local_paths = [
        SCRIPT_DIR / "daily.json",
        SCRIPT_DIR.parent / "docs" / "leveraged-screener" / "daily.json",
    ]
    for path in local_paths:
        if path.exists():
            try:
                data = json.loads(path.read_text())
                log(f"📂 Screener loaded from local file: {path}")
                return data
            except Exception:
                pass

    log("❌ Could not fetch daily screener from GH Pages or local file", "ERROR")
    return None


# ══════════════════════════════════════════════════════════════════
# WASH SALE TRACKER
# ══════════════════════════════════════════════════════════════════

def load_wash_sales() -> dict:
    """Load wash sale blacklist from disk."""
    path = SCRIPT_DIR / WASH_SALE_FILE
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            pass
    return {"blacklist": []}


def save_wash_sales(data: dict):
    path = SCRIPT_DIR / WASH_SALE_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str))


def add_wash_sale(ticker: str, underlying: str):
    """Add a ticker + underlying to wash sale blacklist for 30 days."""
    data = load_wash_sales()
    today = date.today().isoformat()
    resume = (date.today() + timedelta(days=WASH_SALE_DAYS)).isoformat()

    # Add both the ETF and underlying (substantially identical)
    for sym in set([ticker.upper(), underlying.upper()]):
        entry = {
            "ticker": sym,
            "loss_date": today,
            "resume_date": resume,
        }
        # Remove any existing entry for this ticker
        data["blacklist"] = [e for e in data["blacklist"] if e["ticker"] != sym]
        data["blacklist"].append(entry)
        log(f"🚫 WASH SALE: {sym} blacklisted until {resume}", "WARN")

    save_wash_sales(data)


def is_wash_sale_blocked(ticker: str, underlying: str) -> bool:
    """Check if a ticker is blocked by wash sale rule."""
    data = load_wash_sales()
    today = date.today().isoformat()

    # Clean expired entries
    active = [e for e in data["blacklist"] if e["resume_date"] > today]
    if len(active) != len(data["blacklist"]):
        data["blacklist"] = active
        save_wash_sales(data)

    blocked_tickers = set(e["ticker"] for e in active)
    return ticker.upper() in blocked_tickers or underlying.upper() in blocked_tickers


# ══════════════════════════════════════════════════════════════════
# TRADE JOURNAL
# ══════════════════════════════════════════════════════════════════

def load_journal() -> dict:
    path = SCRIPT_DIR / TRADE_JOURNAL_FILE
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            pass
    return {"trades": [], "daily_summaries": []}


def save_journal(data: dict):
    path = SCRIPT_DIR / TRADE_JOURNAL_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str))


def log_trade(trade: dict):
    """Append a trade to the journal."""
    journal = load_journal()
    journal["trades"].append(trade)
    save_journal(journal)


def get_today_pnl() -> float:
    """Sum today's realized P&L from journal."""
    journal = load_journal()
    today = date.today().isoformat()
    return sum(t.get("pnl_dollars", 0) for t in journal["trades"] if t.get("date") == today)


# ══════════════════════════════════════════════════════════════════
# CORE TRADING LOGIC
# ══════════════════════════════════════════════════════════════════

class ActivePosition:
    """Tracks one active intraday position."""
    def __init__(self, symbol: str, underlying: str, entry_price: float,
                 shares: int, atr: float, conviction: float, dry_run: bool):
        self.symbol = symbol
        self.underlying = underlying
        self.entry_price = entry_price
        self.shares = shares
        self.atr = atr
        self.conviction = conviction
        self.dry_run = dry_run
        self.running_high = entry_price
        self.trail_distance = atr * ATR_MULT
        self.entry_time = datetime.now(ET).strftime("%H:%M")
        self.exit_price = None
        self.exit_time = None
        self.exit_reason = None

    def check_trailing_stop(self, current_price: float) -> bool:
        """Update running high and check if stop is hit. Returns True if should exit."""
        if current_price > self.running_high:
            self.running_high = current_price
        stop_level = self.running_high - self.trail_distance
        if current_price <= stop_level:
            self.exit_price = stop_level
            self.exit_time = datetime.now(ET).strftime("%H:%M")
            self.exit_reason = "trail_stop"
            return True
        return False

    def force_close(self, current_price: float):
        """EOD forced exit."""
        self.exit_price = current_price
        self.exit_time = datetime.now(ET).strftime("%H:%M")
        self.exit_reason = "eod_close"

    @property
    def pnl_dollars(self) -> float:
        if self.exit_price is None:
            return 0.0
        return (self.exit_price - self.entry_price) * self.shares

    @property
    def pnl_pct(self) -> float:
        if self.exit_price is None or self.entry_price == 0:
            return 0.0
        return ((self.exit_price - self.entry_price) / self.entry_price) * 100

    def to_dict(self) -> dict:
        return {
            "date": date.today().isoformat(),
            "symbol": self.symbol,
            "underlying": self.underlying,
            "entry_price": round(self.entry_price, 2),
            "exit_price": round(self.exit_price, 2) if self.exit_price else None,
            "shares": self.shares,
            "pnl_dollars": round(self.pnl_dollars, 2),
            "pnl_pct": round(self.pnl_pct, 2),
            "entry_time": self.entry_time,
            "exit_time": self.exit_time,
            "exit_reason": self.exit_reason,
            "atr": round(self.atr, 4),
            "trail_distance": round(self.trail_distance, 4),
            "conviction": self.conviction,
            "dry_run": self.dry_run,
        }


def compute_daily_atr(symbol: str) -> float:
    """Compute 14-day ATR from Tradier daily history."""
    end = datetime.now(ET).strftime("%Y-%m-%d")
    start = (datetime.now(ET) - timedelta(days=30)).strftime("%Y-%m-%d")
    data = tradier_get("/markets/history", {
        "symbol": symbol, "interval": "daily", "start": start, "end": end,
    })
    if not data:
        return 0.0
    history = data.get("history", {})
    if not history or history == "null":
        return 0.0
    days = history.get("day", [])
    if isinstance(days, dict):
        days = [days]
    if len(days) < 15:
        return 0.0

    # Wilder's ATR
    trs = []
    for i in range(1, len(days)):
        h = float(days[i].get("high", 0))
        l = float(days[i].get("low", 0))
        c_prev = float(days[i-1].get("close", 0))
        tr = max(h - l, abs(h - c_prev), abs(l - c_prev))
        trs.append(tr)

    if len(trs) < 14:
        return sum(trs) / len(trs) if trs else 0.0

    atr = sum(trs[:14]) / 14
    for i in range(14, len(trs)):
        atr = (atr * 13 + trs[i]) / 14
    return atr


def monitor_vwap_reclaim(symbol: str, timeout_minutes: int = 360) -> dict | None:
    """
    Poll 5m candles until VWAP reclaim is detected.

    Returns dict with entry signal info, or None if no signal by timeout.
    """
    log(f"👁️  Monitoring {symbol} for VWAP reclaim...")
    start = time.time()
    was_below_vwap = False

    while (time.time() - start) < (timeout_minutes * 60):
        now = datetime.now(ET)

        # Stop monitoring at 3:30 PM (need time for trade + trail)
        if now.hour >= 15 and now.minute >= 30:
            log(f"⏰ Past 3:30 PM — stopping VWAP monitor for {symbol}", "SKIP")
            return None

        candles = get_5m_candles(symbol)
        if not candles or len(candles) < 3:
            time.sleep(VWAP_POLL_SECONDS)
            continue

        vwaps = compute_vwap(candles)
        last_close = float(candles[-1].get("close", 0))
        last_vwap = vwaps[-1] if vwaps else 0

        if last_close < last_vwap:
            if not was_below_vwap:
                log(f"  📉 {symbol} dipped below VWAP ({last_close:.2f} < {last_vwap:.2f})")
            was_below_vwap = True

        elif was_below_vwap and last_close > last_vwap:
            # VWAP RECLAIM DETECTED!
            log(f"  🔥 VWAP RECLAIM! {symbol} closed {last_close:.2f} > VWAP {last_vwap:.2f}", "TRADE")
            return {
                "symbol": symbol,
                "price": last_close,
                "vwap": last_vwap,
                "time": datetime.now(ET).strftime("%H:%M"),
            }

        time.sleep(VWAP_POLL_SECONDS)

    log(f"⏰ No VWAP reclaim for {symbol} within {timeout_minutes}m", "SKIP")
    return None


def trail_and_manage(position: ActivePosition, dry_run: bool) -> ActivePosition:
    """Monitor trailing stop until exit or EOD."""
    log(f"📈 Trailing stop active for {position.symbol}: "
        f"Entry ${position.entry_price:.2f}, Trail ${position.trail_distance:.4f}")

    while True:
        now = datetime.now(ET)

        # EOD force close at 3:55 PM
        if now.hour >= EOD_CLOSE_HOUR and now.minute >= EOD_CLOSE_MIN:
            quote = get_quote(position.symbol)
            current = float(quote.get("last", position.entry_price)) if quote else position.entry_price
            position.force_close(current)
            submit_market_sell(position.symbol, position.shares, dry_run)
            log(f"🔔 EOD CLOSE: {position.symbol} @ ${current:.2f} "
                f"P&L: ${position.pnl_dollars:+.2f} ({position.pnl_pct:+.1f}%)", "TRADE")
            break

        # Check current price
        quote = get_quote(position.symbol)
        if not quote:
            time.sleep(TRAIL_POLL_SECONDS)
            continue

        current = float(quote.get("last", 0))
        if current <= 0:
            time.sleep(TRAIL_POLL_SECONDS)
            continue

        # Check trailing stop
        if position.check_trailing_stop(current):
            submit_market_sell(position.symbol, position.shares, dry_run)
            log(f"🛑 TRAILING STOP HIT: {position.symbol} @ ${current:.2f} "
                f"(stop @ ${position.running_high - position.trail_distance:.2f}) "
                f"P&L: ${position.pnl_dollars:+.2f} ({position.pnl_pct:+.1f}%)", "TRADE")
            break

        time.sleep(TRAIL_POLL_SECONDS)

    return position


# ══════════════════════════════════════════════════════════════════
# MAIN LOOP
# ══════════════════════════════════════════════════════════════════

def run_trading_day(dry_run: bool = True):
    """Execute one full trading day."""
    today_str = date.today().isoformat()
    mode = "🔇 DRY RUN" if dry_run else "🔴 LIVE"

    log(f"{'═' * 60}")
    log(f"👻 Ghost Alpha VWAP Reclaim — {mode}")
    log(f"Date: {today_str}")
    log(f"{'═' * 60}")

    # ── Step 0: Check wash sale blacklist ──
    wash_data = load_wash_sales()
    active_bans = [e for e in wash_data.get("blacklist", []) if e["resume_date"] > today_str]
    if active_bans:
        log(f"🚫 Wash sale blacklist: {', '.join(e['ticker'] + '→' + e['resume_date'] for e in active_bans)}")

    # ── Step 1: Get account balance ──
    balance = get_account_balance()
    if balance <= 0:
        log("❌ Could not fetch account balance or balance is $0", "ERROR")
        return
    trading_capital = balance * CAPITAL_FRACTION
    position_size = trading_capital / MAX_POSITIONS
    log(f"💰 Account balance: ${balance:,.2f} → Trading capital (50%): ${trading_capital:,.2f}")
    log(f"   Position size: ${position_size:,.2f} × {MAX_POSITIONS} positions")

    # ── Step 2: Fetch daily screener ──
    screener = fetch_daily_picks()
    if not screener:
        log("❌ Could not fetch daily screener — aborting", "ERROR")
        return

    screener_date = screener.get("date", "")
    if screener_date != today_str:
        log(f"⚠️  Screener date ({screener_date}) != today ({today_str}) — using anyway", "WARN")

    # ── Step 3: SPY ADX regime filter ──
    spy_adx = screener.get("spy_adx", 0)
    is_trade_day = screener.get("is_trade_day", False)

    if not is_trade_day or spy_adx < SPY_ADX_THRESHOLD:
        msg = screener.get("no_trade_message", f"SPY ADX {spy_adx} < {SPY_ADX_THRESHOLD}")
        log(f"🚫 NO TRADE DAY: {msg}", "SKIP")
        discord_alert(f"🚫 **NO TRADE DAY** — {msg}\nSPY ADX: {spy_adx}")
        return

    log(f"✅ TRADE DAY: SPY ADX = {spy_adx}")

    # ── Step 4: Select top picks ──
    top_picks = screener.get("top_picks", [])
    valid_picks = [p for p in top_picks if p.get("grade") in VALID_GRADES]

    # Filter out wash sale blocked tickers
    tradeable = []
    for pick in valid_picks:
        etf = pick.get("etf", "")
        underlying = pick.get("underlying", "")
        if is_wash_sale_blocked(etf, underlying):
            log(f"🚫 WASH SALE BLOCK: {etf} ({underlying}) — skipping", "SKIP")
            continue
        tradeable.append(pick)

    if not tradeable:
        log("🚫 No valid Grade A/B picks (or all blocked by wash sales)", "SKIP")
        discord_alert("🚫 **NO PICKS** — No Grade A/B setups or all wash-sale blocked")
        return

    targets = tradeable[:MAX_POSITIONS]
    log(f"🎯 Targets: {', '.join(p['etf'] + '(' + p['underlying'] + ' ' + p['grade'] + ')' for p in targets)}")

    # Determine bull/bear trend for conviction sizing
    # SPY trend: if DI+ > DI- in screener data, it's bullish
    # Fallback: check if SPY closed green today
    spy_quote = get_quote("SPY")
    spy_bullish = True
    if spy_quote:
        spy_open = float(spy_quote.get("open", 0))
        spy_last = float(spy_quote.get("last", 0))
        spy_bullish = spy_last >= spy_open
    conviction = 1.0 if spy_bullish else BEAR_CONVICTION
    log(f"📊 SPY trend: {'BULL 🟢' if spy_bullish else 'BEAR 🔴'} → conviction: {conviction:.0%}")

    discord_alert(
        f"👻 **VWAP ALGO — TRADING DAY**\n"
        f"SPY ADX: {spy_adx} | Trend: {'🟢 BULL' if spy_bullish else '🔴 BEAR'}\n"
        f"Capital: ${trading_capital:,.0f} | Per position: ${position_size:,.0f}\n"
        f"Targets: {', '.join(p['etf'] for p in targets)}\n"
        f"Mode: {mode}"
    )

    # ── Step 5: Wait for market open + warmup ──
    now = datetime.now(ET)
    monitor_start = now.replace(hour=MONITOR_START_HOUR, minute=MONITOR_START_MIN, second=0)
    if now < monitor_start:
        wait_secs = (monitor_start - now).total_seconds()
        log(f"⏳ Waiting {wait_secs:.0f}s for monitor start ({MONITOR_START_HOUR}:{MONITOR_START_MIN:02d} ET)...")
        time.sleep(wait_secs)

    # ── Step 6: Monitor for VWAP reclaim signals ──
    active_positions: list[ActivePosition] = []
    positions_filled = 0

    for pick in targets:
        # Check daily loss limit
        current_pnl = get_today_pnl()
        if current_pnl <= DAILY_LOSS_LIMIT:
            log(f"🛑 DAILY LOSS LIMIT HIT: ${current_pnl:,.2f} ≤ ${DAILY_LOSS_LIMIT}", "WARN")
            discord_alert(f"🛑 **DAILY LOSS LIMIT** — P&L ${current_pnl:,.2f} hit ${DAILY_LOSS_LIMIT} floor")
            break

        etf = pick["etf"]
        underlying = pick["underlying"]

        # Compute ATR for trailing stop
        atr = compute_daily_atr(etf)
        if atr <= 0:
            log(f"⚠️  Could not compute ATR for {etf} — skipping", "WARN")
            continue

        log(f"{'─' * 40}")
        log(f"🎯 Target: {etf} (2x {underlying}) | ATR: ${atr:.4f} | Trail: ${atr * ATR_MULT:.4f}")

        # Monitor for VWAP reclaim
        signal = monitor_vwap_reclaim(etf)
        if not signal:
            continue

        # Get current bid for limit order
        quote = get_quote(etf)
        if not quote:
            log(f"⚠️  No quote for {etf} — skipping", "WARN")
            continue

        bid_price = float(quote.get("bid", 0))
        if bid_price <= 0:
            bid_price = float(quote.get("last", 0))
        if bid_price <= 0:
            log(f"⚠️  Invalid bid price for {etf}", "WARN")
            continue

        # Calculate position
        effective_size = position_size * conviction
        shares = int(effective_size / bid_price)
        if shares <= 0:
            log(f"⚠️  Position too small for {etf} at ${bid_price:.2f}", "WARN")
            continue

        # Submit order
        order_result = submit_limit_buy(etf, shares, bid_price, dry_run)
        if not order_result:
            log(f"⚠️  Order failed for {etf}", "WARN")
            continue

        # For live: wait for fill (max 60s)
        order_id = order_result.get("order", {}).get("id", "")
        entry_price = bid_price

        if not dry_run and order_id and order_id != "DRY_RUN":
            log(f"⏳ Waiting for fill on order #{order_id}...")
            fill_start = time.time()
            filled = False
            while time.time() - fill_start < 60:
                status = get_order_status(order_id)
                if status == "filled":
                    filled = True
                    log(f"✅ Order #{order_id} FILLED")
                    break
                elif status in ("rejected", "canceled", "expired"):
                    log(f"❌ Order #{order_id} {status}", "WARN")
                    break
                time.sleep(3)

            if not filled:
                log(f"⏰ Order #{order_id} not filled in 60s — canceling", "WARN")
                # Cancel unfilled order
                tradier_post(f"/accounts/{TRADIER_ACCOUNT}/orders/{order_id}/cancel")
                continue

        # Create position tracker
        pos = ActivePosition(
            symbol=etf,
            underlying=underlying,
            entry_price=entry_price,
            shares=shares,
            atr=atr,
            conviction=conviction,
            dry_run=dry_run,
        )
        active_positions.append(pos)
        positions_filled += 1

        log(f"📗 POSITION OPEN: {shares} {etf} @ ${entry_price:.2f} "
            f"(${shares * entry_price:,.2f}) — Trail: ${atr * ATR_MULT:.4f}")

    # ── Step 7: Monitor trailing stops ──
    if active_positions:
        log(f"\n{'═' * 40}")
        log(f"📈 Managing {len(active_positions)} active positions...")

        for pos in active_positions:
            pos = trail_and_manage(pos, dry_run)

            # Log the trade
            trade_data = pos.to_dict()
            log_trade(trade_data)

            pnl_emoji = "🟢" if pos.pnl_dollars >= 0 else "🔴"
            log(f"{pnl_emoji} CLOSED: {pos.symbol} | "
                f"P&L: ${pos.pnl_dollars:+.2f} ({pos.pnl_pct:+.1f}%) | "
                f"Exit: {pos.exit_reason}", "TRADE")

            discord_alert(
                f"{pnl_emoji} **{pos.symbol}** closed via {pos.exit_reason}\n"
                f"Entry: ${pos.entry_price:.2f} → Exit: ${pos.exit_price:.2f}\n"
                f"P&L: **${pos.pnl_dollars:+.2f}** ({pos.pnl_pct:+.1f}%)\n"
                f"Shares: {pos.shares} | Conviction: {pos.conviction:.0%}"
            )

            # Wash sale check: if this trade lost, blacklist the ticker
            if pos.pnl_dollars < 0:
                add_wash_sale(pos.symbol, pos.underlying)

    # ── Step 8: EOD Summary ──
    day_pnl = get_today_pnl()
    trades_today = [t for t in load_journal()["trades"] if t.get("date") == date.today().isoformat()]
    wins = sum(1 for t in trades_today if t.get("pnl_dollars", 0) > 0)
    losses = sum(1 for t in trades_today if t.get("pnl_dollars", 0) < 0)

    summary = (
        f"\n{'═' * 60}\n"
        f"👻 EOD SUMMARY — {date.today().isoformat()}\n"
        f"{'═' * 60}\n"
        f"  Trades: {len(trades_today)} ({wins}W / {losses}L)\n"
        f"  Day P&L: ${day_pnl:+,.2f}\n"
        f"  Mode: {mode}\n"
        f"{'═' * 60}"
    )
    log(summary)

    discord_alert(
        f"👻 **EOD SUMMARY** — {date.today().isoformat()}\n"
        f"Trades: {len(trades_today)} ({wins}W/{losses}L)\n"
        f"Day P&L: **${day_pnl:+,.2f}**\n"
        f"Mode: {mode}"
    )


def main():
    global TRADIER_TOKEN, TRADIER_ACCOUNT, DISCORD_BOT_TOKEN

    parser = argparse.ArgumentParser(
        description="👻 Ghost Alpha VWAP Reclaim — Automated Algo Trader"
    )
    parser.add_argument("--live", action="store_true",
                        help="Enable LIVE trading (default: dry-run)")
    parser.add_argument("--once", action="store_true",
                        help="Run once and exit (don't loop)")
    args = parser.parse_args()

    dry_run = not args.live

    # Load secrets
    TRADIER_TOKEN, TRADIER_ACCOUNT, DISCORD_BOT_TOKEN = load_secrets()

    mode_str = "🔴 LIVE MODE" if args.live else "🔇 DRY RUN MODE"
    log(f"{'═' * 60}")
    log(f"👻 Ghost Alpha VWAP Reclaim — {mode_str}")
    log(f"   Tradier Account: {TRADIER_ACCOUNT}")
    log(f"   Capital: 50% of balance | Positions: {MAX_POSITIONS}")
    log(f"   ATR Trail: {ATR_MULT}x | SPY ADX Threshold: {SPY_ADX_THRESHOLD}")
    log(f"   Daily Loss Limit: ${DAILY_LOSS_LIMIT}")
    log(f"   Wash Sale Period: {WASH_SALE_DAYS} days")
    log(f"   Discord Alerts: {'✅' if DISCORD_BOT_TOKEN else '❌'}")
    log(f"{'═' * 60}")

    # Verify API connectivity
    balance = get_account_balance()
    if balance > 0:
        log(f"✅ Tradier connected — Balance: ${balance:,.2f}")
    else:
        log("❌ Could not connect to Tradier — check API key", "ERROR")
        sys.exit(1)

    if args.once:
        run_trading_day(dry_run)
        return

    # ── Main loop: run every weekday ──
    while True:
        now = datetime.now(ET)
        weekday = now.weekday()  # 0=Mon, 6=Sun

        if weekday >= 5:  # Weekend
            next_monday = now + timedelta(days=(7 - weekday))
            next_monday = next_monday.replace(hour=9, minute=10, second=0, microsecond=0)
            wait = (next_monday - now).total_seconds()
            log(f"📅 Weekend — sleeping until Monday 9:10 AM ET ({wait/3600:.1f}h)")
            time.sleep(wait)
            continue

        # Before market hours — sleep until 9:15 AM
        if now.hour < 9 or (now.hour == 9 and now.minute < 15):
            target = now.replace(hour=9, minute=15, second=0, microsecond=0)
            wait = (target - now).total_seconds()
            log(f"⏳ Pre-market — sleeping {wait:.0f}s until 9:15 AM ET")
            time.sleep(max(wait, 1))
            continue

        # After market close — sleep until next day
        if now.hour >= EOD_SHUTDOWN_HOUR and now.minute >= EOD_SHUTDOWN_MIN:
            tomorrow = now + timedelta(days=1)
            tomorrow = tomorrow.replace(hour=9, minute=10, second=0, microsecond=0)
            # Skip to Monday if Friday
            if tomorrow.weekday() >= 5:
                days_to_monday = 7 - tomorrow.weekday()
                tomorrow += timedelta(days=days_to_monday)
            wait = (tomorrow - now).total_seconds()
            log(f"🌙 Market closed — sleeping until {tomorrow.strftime('%A')} 9:10 AM ET ({wait/3600:.1f}h)")
            time.sleep(wait)
            continue

        # ── Trading hours: run the day ──
        try:
            run_trading_day(dry_run)
        except Exception as e:
            log(f"❌ CRITICAL ERROR: {e}", "ERROR")
            traceback.print_exc()
            discord_alert(f"❌ **ALGO CRASH**: {str(e)[:300]}")

        # Sleep until next day
        tomorrow = now + timedelta(days=1)
        tomorrow = tomorrow.replace(hour=9, minute=10, second=0, microsecond=0)
        if tomorrow.weekday() >= 5:
            days_to_monday = 7 - tomorrow.weekday()
            tomorrow += timedelta(days=days_to_monday)
        wait = (tomorrow - now).total_seconds()
        log(f"💤 Day complete — sleeping until {tomorrow.strftime('%A')} 9:10 AM ET")
        time.sleep(max(wait, 60))


if __name__ == "__main__":
    main()
