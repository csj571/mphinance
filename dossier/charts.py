"""
Chart Generator — Candlestick charts with Michael's EMA stack.

Generates publication-quality candlestick charts with:
- EMA Stack: 8, 21, 34, 55, 89
- SMA 50 / SMA 200
- Volume bars
- Dark HUD theme matching the dossier aesthetic

Used by the dossier pipeline (generate.py) to embed charts
in the daily report and ghost blog.

Usage:
    from dossier.charts import generate_chart
    path = generate_chart("AAPL", output_dir="docs/charts/")
"""

import mplfinance as mpf
import yfinance as yf
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for server/CI

from pathlib import Path


# ── Michael's signature EMA stack colors ──
EMA_COLORS = {
    8: "#00ff41",    # Neon green (fastest)
    21: "#00f3ff",   # Neon cyan
    34: "#a855f7",   # Purple
    55: "#ffb000",   # Amber
    89: "#ff6b6b",   # Coral (slowest)
}

SMA_STYLES = {
    50: {"color": "#444444", "linestyle": "--"},
    200: {"color": "#666666", "linestyle": "-"},
}

# Dark HUD theme
GHOST_STYLE = mpf.make_mpf_style(
    base_mpf_style="nightclouds",
    marketcolors=mpf.make_marketcolors(
        up="#00ff41", down="#ff3e3e",
        edge={"up": "#00ff4180", "down": "#ff3e3e80"},
        wick={"up": "#00ff4180", "down": "#ff3e3e80"},
        volume={"up": "#00ff4140", "down": "#ff3e3e40"},
    ),
    facecolor="#0a0a0a",
    edgecolor="#1a1a1a",
    figcolor="#050505",
    gridcolor="#1a1a1a",
    gridstyle=":",
    y_on_right=True,
    rc={
        "font.size": 8,
        "axes.labelsize": 8,
        "axes.titlesize": 10,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
    },
)


def generate_chart(
    ticker: str,
    period: str = "3mo",
    output_dir: str = "docs/charts",
    width: int = 12,
    height: int = 6,
) -> str | None:
    """
    Generate a candlestick chart with EMA stack overlay.

    Returns the path to the saved PNG, or None on failure.
    """
    print(f"    📊 Generating chart: {ticker}...")

    try:
        df = yf.Ticker(ticker).history(period=period)
        if df.empty or len(df) < 30:
            print(f"    [SKIP] {ticker}: insufficient data ({len(df)} bars)")
            return None
    except Exception as e:
        print(f"    [ERR] {ticker}: {e}")
        return None

    # ── Calculate EMAs ──
    addplots = []
    for span, color in EMA_COLORS.items():
        if len(df) >= span:
            ema = df["Close"].ewm(span=span, adjust=False).mean()
            addplots.append(mpf.make_addplot(
                ema, color=color, width=0.8,
                label=f"EMA {span}",
            ))

    # SMA 50 / 200
    for window, style in SMA_STYLES.items():
        if len(df) >= window:
            sma = df["Close"].rolling(window=window).mean()
            addplots.append(mpf.make_addplot(
                sma, color=style["color"],
                linestyle=style["linestyle"], width=0.6,
                label=f"SMA {window}",
            ))

    # ── Output path ──
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{ticker.upper()}_chart.png"

    # ── Render ──
    fig, axes = mpf.plot(
        df,
        type="candle",
        style=GHOST_STYLE,
        addplot=addplots if addplots else None,
        volume=True,
        title=f"\n{ticker.upper()} — EMA Stack",
        figsize=(width, height),
        returnfig=True,
        tight_layout=True,
        panel_ratios=(3, 1),
    )

    # Add legend manually
    ax = axes[0]
    legend_labels = [f"EMA {s}" for s in EMA_COLORS if len(df) >= s]
    legend_colors = [EMA_COLORS[s] for s in EMA_COLORS if len(df) >= s]
    for w, style in SMA_STYLES.items():
        if len(df) >= w:
            legend_labels.append(f"SMA {w}")
            legend_colors.append(style["color"])

    import matplotlib.lines as mlines
    handles = [mlines.Line2D([], [], color=c, label=l) for l, c in zip(legend_labels, legend_colors)]
    ax.legend(handles=handles, loc="upper left", fontsize=7,
              facecolor="#0a0a0a", edgecolor="#333", labelcolor="#aaa")

    # Watermark
    ax.text(0.99, 0.01, "mphinance.com", transform=ax.transAxes,
            fontsize=7, color="#333", ha="right", va="bottom",
            style="italic")

    fig.savefig(str(out_path), dpi=150, bbox_inches="tight",
                facecolor="#050505", edgecolor="none")
    matplotlib.pyplot.close(fig)

    print(f"    ✓ Chart saved: {out_path}")
    return str(out_path)


def generate_charts_for_dossier(
    tickers: list[str],
    output_dir: str = "docs/charts",
    max_charts: int = 5,
) -> list[dict]:
    """
    Generate charts for top dossier tickers.

    Returns list of {ticker, path} dicts.
    """
    charts = []
    for ticker in tickers[:max_charts]:
        path = generate_chart(ticker, output_dir=output_dir)
        if path:
            charts.append({"ticker": ticker, "path": path})
    return charts


if __name__ == "__main__":
    # Quick test
    import sys
    ticker = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    result = generate_chart(ticker, output_dir="/tmp/charts")
    if result:
        print(f"\n✅ Chart generated: {result}")
    else:
        print(f"\n❌ Failed to generate chart for {ticker}")
