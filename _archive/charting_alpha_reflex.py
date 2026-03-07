import mplfinance as mpf
import pandas as pd
import io
import base64
from core.data_engine import DataEngine
from typing import Optional

class ChartingService:
    def __init__(self):
        self.engine = DataEngine()
        # Custom Mission Control HUD Style
        self.hud_style = mpf.make_mpf_style(
            base_mpf_style='charles',
            marketcolors=mpf.make_marketcolors(
                up='#39ff14', down='#ff073a',
                edge='inherit', wick='inherit',
                volume='inherit'
            ),
            facecolor='#0a0a0a',
            gridcolor='#1a1a1a',
            gridstyle='-',
            rc={'font.family': 'monospace', 'text.color': '#e0e0e0', 'axes.labelcolor': '#e0e0e0', 'xtick.color': '#e0e0e0', 'ytick.color': '#e0e0e0'}
        )

    async def generate_chart_base64(self, symbol: str, interval: str = "daily") -> Optional[str]:
        """
        Generates an mplfinance chart and returns it as a base64 encoded PNG.
        """
        try:
            # Use Tradier for UI precision
            df = await self.engine.get_history(symbol, interval=interval, limit=100, source="tradier")
            if df.empty:
                return None
            
            # Ensure index is datetime and columns are properly named for mplfinance
            # Tradier returns: open, high, low, close, volume, date (index)
            # mplfinance expects: Open, High, Low, Close, Volume
            df.columns = [c.capitalize() for c in df.columns]

            # Calculate EMAs for the "Cloud"
            add_plots = []
            for span, color in [(8, '#00d4ff'), (21, '#9c40ff'), (34, '#ff6b6b'), (55, '#ffbf00'), (89, '#ffffff')]:
                ema = df['Close'].ewm(span=span, adjust=False).mean()
                add_plots.append(mpf.make_addplot(ema, color=color, width=0.8))

            # Render to buffer
            buf = io.BytesIO()
            fig, axes = mpf.plot(
                df,
                type='candle',
                style=self.hud_style,
                volume=True,
                addplot=add_plots,
                figsize=(12, 8),
                returnfig=True,
                tight_layout=True,
                savefig=dict(fname=buf, format='png', bbox_inches='tight')
            )
            
            buf.seek(0)
            img_str = base64.b64encode(buf.read()).decode('utf-8')
            return img_str
        except Exception as e:
            print(f"Charting Error for {symbol}: {e}")
            return None

if __name__ == "__main__":
    import asyncio
    async def test():
        service = ChartingService()
        print("Generating SPY Chart...")
        b64 = await service.generate_chart_base64("SPY")
        if b64:
            print(f"Chart generated (Base64 length: {len(b64)})")
        else:
            print("Failed to generate chart.")
            
    asyncio.run(test())
