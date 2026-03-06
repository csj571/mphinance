"""
Ghost Chart Generator — Renders Michael's signature EMA stack charts as static PNGs.

Uses mplfinance for all candlestick and volume rendering. Standardized
for cloud execution (Cloud Run Jobs).

Chart outputs:
- EMA Stack: 8, 21, 34, 55, 89
- SMA 50, 100, 200 (institutional levels)
- Volume bars
- HUD-style dark theme

Output: PNG images saved to docs/ticker/{TICKER}/chart.png
"""

import mplfinance as mpf
import matplotlib
matplotlib.use("Agg")
import matplotlib.lines as mlines

import yfinance as yf
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CHART_DIR = PROJECT_ROOT / "docs" / "ticker"

# ── Michael's EMA Stack Colors ──
EMA_CONFIG = {
    8:  {"color": "#22d3ee", "width": 1.5},   # Cyan (fastest)
    21: {"color": "#4ade80", "width": 1.5},   # Green
    34: {"color": "#facc15", "width": 1.2},   # Yellow
    55: {"color": "#fb923c", "width": 1.2},   # Orange
    89: {"color": "#f87171", "width": 1.2},   # Red (slowest)
}

SMA_CONFIG = {
    50:  {"color": "#6366f1", "width": 1.0, "linestyle": "--"},   # Purple dashed
    100: {"color": "#a855f7", "width": 1.0, "linestyle": "--"},  # Violet dashed
    200: {"color": "#ec4899", "width": 1.0, "linestyle": "--"},  # Pink dashed
}

# ── HUD Dark Theme (shared with dossier/charts.py) ──
GHOST_STYLE = mpf.make_mpf_style(
    base_mpf_style="nightclouds",
    marketcolors=mpf.make_marketcolors(
        up="#22c55e", down="#ef4444",
        edge={"up": "#22c55e80", "down": "#ef444480"},
        wick={"up": "#22c55e80", "down": "#ef444480"},
        volume={"up": "#22c55e40", "down": "#ef444440"},
    ),
    facecolor="#0a0a0a",
    edgecolor="#1a1a1a",
    figcolor="#0a0a0a",
    gridcolor="#1a1a1a",
    gridstyle=":",
    y_on_right=True,
    rc={
        "font.size": 8,
        "axes.labelsize": 8,
        "axes.titlesize": 12,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
    },
)


def generate_chart(ticker: str, period: str = "6mo", save_dir: Path = None) -> str:
    """
    Generate a candlestick chart PNG with EMA/SMA stack overlay.

    Uses mplfinance for rendering — no raw matplotlib or Plotly.
    Returns the path to the saved PNG, or empty string on failure.
    """
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period)
        if df.empty or len(df) < 20:
            return ""
    except Exception as e:
        print(f"  [WARN] Chart data fetch failed for {ticker}: {e}")
        return ""

    # ── Build addplot overlays ──
    addplots = []

    # EMAs
    for span, config in EMA_CONFIG.items():
        if len(df) >= span:
            ema = df["Close"].ewm(span=span, adjust=False).mean()
            addplots.append(mpf.make_addplot(
                ema, color=config["color"], width=config["width"],
            ))

    # SMAs
    for window, config in SMA_CONFIG.items():
        if len(df) >= window:
            sma = df["Close"].rolling(window=window, min_periods=1).mean()
            addplots.append(mpf.make_addplot(
                sma, color=config["color"], width=config["width"],
                linestyle=config["linestyle"],
            ))

    # ── Output path ──
    if save_dir is None:
        save_dir = CHART_DIR / ticker
    save_dir.mkdir(parents=True, exist_ok=True)
    chart_path = save_dir / "chart.png"

    # ── Render with mplfinance ──
    fig, axes = mpf.plot(
        df,
        type="candle",
        style=GHOST_STYLE,
        addplot=addplots if addplots else None,
        volume=True,
        title=f"\n{ticker} // EMA Stack + Institutional Levels",
        figsize=(12, 6),
        returnfig=True,
        tight_layout=True,
        panel_ratios=(3, 1),
    )

    # ── Legend ──
    ax = axes[0]
    handles = []
    for span, config in EMA_CONFIG.items():
        if len(df) >= span:
            handles.append(mlines.Line2D([], [], color=config["color"],
                                          label=f"EMA {span}"))
    for window, config in SMA_CONFIG.items():
        if len(df) >= window:
            handles.append(mlines.Line2D([], [], color=config["color"],
                                          linestyle=config["linestyle"],
                                          label=f"SMA {window}"))

    ax.legend(handles=handles, loc="upper left", fontsize=7, ncol=4,
              facecolor="#111", edgecolor="#333", labelcolor="#aaa",
              framealpha=0.3)

    # ── Watermark ──
    ax.text(0.99, 0.01, "ghost.alpha // mphinance",
            transform=ax.transAxes, fontsize=7, color="#333",
            ha="right", va="bottom", style="italic")

    # ── Last price annotation ──
    close = df["Close"]
    if len(close) >= 2:
        last_price = close.iloc[-1]
        change_pct = ((close.iloc[-1] / close.iloc[-2]) - 1) * 100
        price_color = "#22c55e" if change_pct >= 0 else "#ef4444"
        # Position annotation at end of chart
        ax.annotate(
            f"${last_price:.2f} ({change_pct:+.1f}%)",
            xy=(len(df) - 1, last_price),
            xytext=(15, 15), textcoords="offset points",
            color=price_color, fontsize=9, fontweight="bold",
            fontfamily="monospace",
            arrowprops=dict(arrowstyle="->", color=price_color, lw=0.8),
            bbox=dict(boxstyle="round,pad=0.3", facecolor="#111",
                     edgecolor=price_color, alpha=0.8),
        )

    # ── Save ──
    fig.savefig(str(chart_path), dpi=150, bbox_inches="tight",
                facecolor="#0a0a0a", edgecolor="none")
    matplotlib.pyplot.close(fig)

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
