"""
Sam's Daily Wisdom — quotes, quips, and occasionally deep thoughts.

A rotating collection of recovery wisdom, trading truth, and life advice,
filtered through Sam's voice. One per day, appended to the Ghost Log.

Categories:
- Recovery (AA/NA — Serenity Prayer, Big Book, meeting wisdom)
- Trading (hard-won market lessons)
- Life (funny, punny, occasionally profound)
"""

import hashlib
from datetime import datetime


# ── The Collection ──
QUOTES = [
    # ═══ RECOVERY WISDOM ═══
    {"text": "God, grant me the serenity to accept the trades I cannot change, the courage to cut the ones I can, and the wisdom to know the difference.", "category": "recovery", "source": "Adapted Serenity Prayer"},
    {"text": "One day at a time. One trade at a time. One lesson at a time. The market doesn't care about yesterday.", "category": "recovery"},
    {"text": "Progress, not perfection. Your P&L doesn't have to be perfect — it has to be honest.", "category": "recovery", "source": "Big Book energy"},
    {"text": "Easy does it. But do it. Don't just watch the chart — execute the plan.", "category": "recovery"},
    {"text": "Let go and let the market do what it's going to do. Your job is to manage YOUR side of the trade.", "category": "recovery"},
    {"text": "First things first. Check the macro, check the VIX, THEN look at your positions.", "category": "recovery"},
    {"text": "Keep it simple. If your thesis needs a whiteboard and three footnotes, it's not a thesis — it's a hope.", "category": "recovery"},
    {"text": "Live and let live. Other people's trades are not your business. Your risk is your business.", "category": "recovery"},
    {"text": "This too shall pass. That drawdown? Temporary. That winning streak? Also temporary. Stay humble.", "category": "recovery"},
    {"text": "We are only as sick as our secrets. Track every trade. Log every loss. The ones you hide are the ones that kill you.", "category": "recovery", "source": "Big Book"},
    {"text": "Half measures availed us nothing. Either follow the trading plan or don't trade. There is no 'kinda' hedged.", "category": "recovery", "source": "Big Book"},
    {"text": "Insanity is making the same revenge trade over and over and expecting a different result.", "category": "recovery"},
    {"text": "The only requirement for membership is a desire to stop losing money.", "category": "recovery"},
    {"text": "Came to believe that a systematic approach could restore us to profitability.", "category": "recovery"},
    {"text": "Made a searching and fearless inventory of our portfolio. And then wished we hadn't.", "category": "recovery"},

    # ═══ TRADING TRUTH ═══
    {"text": "Don't revenge trade. The market doesn't know you exist and it definitely doesn't owe you money.", "category": "trading"},
    {"text": "The best trade is the one you don't take. Second best is the one with a stop loss.", "category": "trading"},
    {"text": "If you can't explain your thesis in one sentence, you don't have a thesis — you have FOMO.", "category": "trading"},
    {"text": "Position sizing isn't sexy, but neither is a margin call at 3 AM.", "category": "trading"},
    {"text": "The trend is your friend until it bends at the end. That's what EMAs are for.", "category": "trading"},
    {"text": "Bull markets make you money. Bear markets make you smart. Sideways markets make you drink.", "category": "trading"},
    {"text": "Never fall in love with a stock. It can't love you back and it will absolutely leave you.", "category": "trading"},
    {"text": "Cut your losers fast. Let your winners run. And for the love of god, stop averaging down on garbage.", "category": "trading"},
    {"text": "The market can stay irrational longer than you can stay solvent. Respect the tape.", "category": "trading"},
    {"text": "Volume precedes price. If nobody's buying, the chart is lying.", "category": "trading"},
    {"text": "Risk management isn't what you do after the trade goes wrong. It's what you do before you enter.", "category": "trading"},
    {"text": "There are old traders and bold traders, but no old bold traders.", "category": "trading"},
    {"text": "The best stop loss is the one you set before you need it.", "category": "trading"},
    {"text": "Don't confuse a bull market with brains. We're all geniuses until we're not.", "category": "trading"},
    {"text": "IV is high for a reason. Selling premium into earnings is not a strategy — it's a prayer.", "category": "trading"},

    # ═══ LIFE WISDOM (funny, punny, real) ═══
    {"text": "Don't pee upwind. Don't trade against the trend. Same energy.", "category": "life"},
    {"text": "Never pass up an opportunity to pee, or to take profits.", "category": "life"},
    {"text": "Life is short. Your options expiry is shorter.", "category": "life"},
    {"text": "Be the person your dog thinks you are. Trade like the person your backtests think you are.", "category": "life"},
    {"text": "If you're going through hell, keep going. Same applies to drawdowns.", "category": "life", "source": "Churchill-ish"},
    {"text": "The best time to plant a tree was 20 years ago. The best time to start a trading journal was your first trade.", "category": "life"},
    {"text": "You miss 100% of the trades you don't take. You also miss 100% of the losses.", "category": "life"},
    {"text": "Compound interest is the eighth wonder of the world. Compound losses are the ninth.", "category": "life"},
    {"text": "Drink water. Set stop losses. Call your sponsor. In that order.", "category": "life"},
    {"text": "The market doesn't care about your feelings, your rent, or your divorce. Trade accordingly.", "category": "life"},
    {"text": "Some days you're the bug. Some days you're the windshield. Set your position size for bug days.", "category": "life"},
    {"text": "If you can't handle a 5% drawdown, you don't deserve a 50% gain.", "category": "life"},
    {"text": "Your portfolio is like your bathroom — you should clean it more often than you do.", "category": "life"},
    {"text": "Comparison is the thief of joy. Also of rational position sizing.", "category": "life"},
    {"text": "The two most powerful warriors are patience and time. Also caffeine.", "category": "life", "source": "Tolstoy-ish"},
]


def get_daily_quote(date: str = None) -> dict:
    """
    Get a deterministic daily quote based on the date.
    Same date always returns the same quote, but it rotates daily.

    Returns: {"text": "...", "category": "...", "source": "..." (optional)}
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    # Deterministic selection based on date hash
    hash_val = int(hashlib.md5(date.encode()).hexdigest(), 16)
    idx = hash_val % len(QUOTES)
    return QUOTES[idx]


def format_quote(quote: dict) -> str:
    """Format a quote for display in the Ghost Log / blog."""
    source = f' — {quote["source"]}' if quote.get("source") else ""
    emoji = {"recovery": "🙏", "trading": "📉", "life": "💀"}.get(quote["category"], "💭")
    return f'{emoji} <em>"{quote["text"]}"</em>{source}'
