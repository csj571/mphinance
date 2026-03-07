import json
import os
from datetime import datetime

PROJECT_ROOT = "/home/sam/Antigravity/empty/mphinance"
DAILY_PICKS_PATH = os.path.join(PROJECT_ROOT, "docs/api/daily-picks.json")
TRACK_RECORD_PATH = os.path.join(PROJECT_ROOT, "docs/backtesting/track_record.json")

def format_twitter_thread(picks_json_path=DAILY_PICKS_PATH) -> list[str]:
    """
    Generates a Twitter thread from daily picks.
    """
    if not os.path.exists(picks_json_path):
        return ["Picks file not found."]
        
    with open(picks_json_path) as f:
        data = json.load(f)
        
    date = data.get("date", "Today")
    regime_data = data.get("market_regime", {})
    regime = regime_data.get("regime", "UNKNOWN")
    vix = regime_data.get("vix", 0)
    
    tweets = []
    
    # Tweet 1: Header
    header = (
        f"⚡ MOMENTUM PICKS — {date}\n\n"
        f"Market: {regime} (VIX {vix:.1f})\n\n"
        "Today's top setups scored by our 9-factor ML-calibrated algorithm 🧵👇"
    )
    tweets.append(header)
    
    # Tweets 2-4: Podium
    medals = ["🥇", "🥈", "🥉"]
    for i, pick in enumerate(data.get("picks", [])[:3]):
        # Breakdown summary
        bd = pick.get("breakdown", {})
        summary = f"EMA: {pick['ema_stack']} | ADX: {pick['adx']} | RSI: {pick['rsi']}"
        note = pick.get("regime_note", "")
        
        tweet = (
            f"{medals[i]} ${pick['ticker']} — Score: {pick['score']}/100\n\n"
            f"{summary}\n"
            f"{note}\n\n"
            f"Key: {pick['rank']}/10 ranking. {pick['trend']} trend."
        )
        tweets.append(tweet)
        
    # Tweet 5: Rest of top 10
    rest = data.get("picks", [])[3:10]
    if rest:
        rest_list = "\n".join([f"• ${p['ticker']} ({p['score']})" for p in rest])
        tweets.append(f"Ranked #4-10:\n\n{rest_list}\n\nCheck full technicals at mphinance.com")
        
    # Tweet 6: Track record
    if os.path.exists(TRACK_RECORD_PATH):
        with open(TRACK_RECORD_PATH) as f:
            tr = json.load(f)
            stats = tr.get("stats", {})
            if stats:
                tr_tweet = (
                    "📊 Track Record Summary:\n\n"
                    f"Win Rate: {stats.get('win_rate_5d', 0)}% (5-day)\n"
                    f"Avg 5d Return: {stats.get('avg_5d_return', 0)}%\n"
                    f"Total Validated: {stats.get('total_validated', 0)}\n\n"
                    "Join the alpha momentum."
                )
                tweets.append(tr_tweet)
                
    return tweets

def format_discord_embed(picks_json_path=DAILY_PICKS_PATH) -> dict:
    """
    Returns a Discord webhook compatible embed.
    """
    if not os.path.exists(picks_json_path):
        return {"content": "Picks file not found."}
        
    with open(picks_json_path) as f:
        data = json.load(f)
        
    date = data.get("date", "Today")
    regime_data = data.get("market_regime", {})
    regime = regime_data.get("regime", "UNKNOWN")
    vix = regime_data.get("vix", 0)
    
    # 3-color system: bullish=00ff41, caution=f0b400, danger=e53935
    colors = {"CALM": 0x00ff41, "NORMAL": 0x00ff41, "ELEVATED": 0xf0b400, "FEAR": 0xe53935, "PANIC": 0xe53935}
    color = colors.get(regime, 0x00f3ff)
    
    fields = []
    for pick in data.get("picks", [])[:5]:
        medal = "🥇 " if pick['rank'] == 1 else ""
        fields.append({
            "name": f"{medal}{pick['ticker']} (Score: {pick['score']})",
            "value": f"Price: ${pick['price']} | RSI: {pick['rsi']} | Grade: {pick['grade']}",
            "inline": False
        })
        
    embed = {
        "title": f"⚡ Daily Momentum Picks — {date}",
        "description": f"Market Regime: **{regime}** (VIX: {vix:.1f})",
        "color": color,
        "fields": fields,
        "url": "https://mphinance.com/reports/",
        "footer": {"text": "mph1nance | Ghost Alpha Pipeline"}
    }
    
    return {"embeds": [embed]}

if __name__ == "__main__":
    thread = format_twitter_thread()
    print("--- TWITTER THREAD ---")
    for i, t in enumerate(thread):
        print(f"Tweet {i+1}:\n{t}\n{'-'*30}")
        
    print("\n--- DISCORD EMBED ---")
    print(json.dumps(format_discord_embed(), indent=2))
