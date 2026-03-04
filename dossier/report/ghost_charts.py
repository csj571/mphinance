"""
Ghost Chart Generator — Renders Michael's signature EMA stack charts as static PNGs.

Uses matplotlib to generate candlestick charts with:
- EMA 8, 21, 34, 55, 89 (Michael's momentum stack)
- SMA 50, 100, 200 (institutional levels)
- HUD-style dark theme matching the dossier aesthetic

Output: PNG images saved to docs/ticker/{TICKER}/chart.png
"""

import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CHART_DIR = PROJECT_ROOT / "docs" / "ticker"


def _ema(series, span):
    return series.ewm(span=span, adjust=False).mean()


def _sma(series, window):
    return series.rolling(window=window, min_periods=1).mean()


def generate_chart(ticker: str, period: str = "6mo", save_dir: Path = None) -> str:
    """
    Generate a chart PNG for a ticker with the full EMA/SMA stack.

    Returns the path to the saved PNG, or empty string on failure.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
        from matplotlib.patches import FancyBboxPatch
        import yfinance as yf
    except ImportError as e:
        print(f"  [WARN] Chart gen missing dep: {e}")
        return ""

    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        if df.empty or len(df) < 20:
            return ""
    except Exception as e:
        print(f"  [WARN] Chart data fetch failed for {ticker}: {e}")
        return ""

    close = df["Close"]
    dates = df.index

    # ── Calculate overlays ──
    emas = {
        "EMA 8": (_ema(close, 8), "#22d3ee", 1.5),    # cyan
        "EMA 21": (_ema(close, 21), "#4ade80", 1.5),   # green
        "EMA 34": (_ema(close, 34), "#facc15", 1.2),   # yellow
        "EMA 55": (_ema(close, 55), "#fb923c", 1.2),   # orange
        "EMA 89": (_ema(close, 89), "#f87171", 1.2),   # red
    }
    smas = {
        "SMA 50": (_sma(close, 50), "#6366f1", 1.0, "--"),   # purple dashed
        "SMA 100": (_sma(close, 100), "#a855f7", 1.0, "--"), # violet dashed
        "SMA 200": (_sma(close, 200), "#ec4899", 1.0, "--"), # pink dashed
    }

    # ── HUD Dark Theme ──
    fig, ax = plt.subplots(1, 1, figsize=(12, 6), facecolor="#0a0a0a")
    ax.set_facecolor("#0a0a0a")

    # Candlesticks (simplified — just close line + fill for speed)
    up = df[df["Close"] >= df["Open"]]
    down = df[df["Close"] < df["Open"]]

    ax.bar(up.index, up["Close"] - up["Open"], bottom=up["Open"],
           color="#22c55e", alpha=0.8, width=0.6)
    ax.bar(up.index, up["High"] - up["Close"], bottom=up["Close"],
           color="#22c55e", alpha=0.5, width=0.1)
    ax.bar(up.index, up["Low"] - up["Open"], bottom=up["Open"],
           color="#22c55e", alpha=0.5, width=0.1)

    ax.bar(down.index, down["Close"] - down["Open"], bottom=down["Open"],
           color="#ef4444", alpha=0.8, width=0.6)
    ax.bar(down.index, down["High"] - down["Open"], bottom=down["Open"],
           color="#ef4444", alpha=0.5, width=0.1)
    ax.bar(down.index, down["Low"] - down["Close"], bottom=down["Close"],
           color="#ef4444", alpha=0.5, width=0.1)

    # ── Plot EMAs ──
    for label, (series, color, width) in emas.items():
        ax.plot(dates, series, color=color, linewidth=width, alpha=0.85, label=label)

    # ── Plot SMAs ──
    for label, (series, color, width, style) in smas.items():
        ax.plot(dates, series, color=color, linewidth=width, linestyle=style,
                alpha=0.6, label=label)

    # ── Styling ──
    ax.set_title(f"{ticker} // EMA Stack + Institutional Levels",
                 fontsize=14, color="#00f3ff", fontfamily="monospace",
                 fontweight="bold", pad=15)

    ax.tick_params(colors="#555", labelsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_color("#333")
    ax.spines["left"].set_color("#333")
    ax.grid(True, alpha=0.1, color="#333")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=2))
    plt.xticks(rotation=45, ha="right")

    # Legend
    leg = ax.legend(loc="upper left", fontsize=7, framealpha=0.3,
                    facecolor="#111", edgecolor="#333", labelcolor="#aaa",
                    ncol=4)

    # Watermark
    ax.text(0.99, 0.01, "ghost.alpha // mphinance",
            transform=ax.transAxes, fontsize=7, color="#333",
            ha="right", va="bottom", fontfamily="monospace")

    # Last price annotation
    last_price = close.iloc[-1]
    last_date = dates[-1]
    change_pct = ((close.iloc[-1] / close.iloc[-2]) - 1) * 100 if len(close) >= 2 else 0
    price_color = "#22c55e" if change_pct >= 0 else "#ef4444"
    ax.annotate(
        f"${last_price:.2f} ({change_pct:+.1f}%)",
        xy=(last_date, last_price),
        xytext=(15, 15), textcoords="offset points",
        color=price_color, fontsize=9, fontfamily="monospace", fontweight="bold",
        arrowprops=dict(arrowstyle="->", color=price_color, lw=0.8),
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#111", edgecolor=price_color, alpha=0.8),
    )

    plt.tight_layout()

    # ── Save ──
    if save_dir is None:
        save_dir = CHART_DIR / ticker
    save_dir.mkdir(parents=True, exist_ok=True)
    chart_path = save_dir / "chart.png"
    fig.savefig(chart_path, dpi=150, bbox_inches="tight",
                facecolor="#0a0a0a", edgecolor="none")
    plt.close(fig)

    return str(chart_path)


def generate_charts_for_watchlist(tickers: list[str]) -> dict[str, str]:
    """Generate charts for all watchlist tickers. Returns {ticker: path}."""
    results = {}
    for t in tickers:
        path = generate_chart(t)
        if path:
            results[t] = path
            print(f"  📊 {t}: {path}")
    return results
