#!/usr/bin/env python3
"""
substack_poster.py — Create Substack draft posts programmatically.

SETUP:
  1. Log into mphinance.substack.com in your browser
  2. DevTools → Application → Cookies → copy 'substack.sid' value  
  3. Update the SID:
     python3 secrets_server.py --set SUBSTACK_SID "paste_value_here"
     python3 secrets_server.py --sync-up
  4. Run this script:
     python3 substack_poster.py             # Creates both drafts
     python3 substack_poster.py --post 1    # Just post 1
     python3 substack_poster.py --post 2    # Just post 2

HOW IT WORKS:
  - Substack has an undocumented API at /api/v1/drafts
  - Auth is cookie-based (substack.sid)
  - SID expires periodically — refresh it from your browser when it 403s
  - Drafts appear in your Dashboard → Drafts tab
  - You review + publish from there (it does NOT auto-publish)

NOTES:
  - draft_bylines needs your Substack user ID (fetched automatically)
  - draft_body uses Substack's ProseMirror doc format
  - We wrap raw HTML in a rawHtml node for simplicity
  - The API returns the draft ID which gives you a direct edit URL
"""

import requests
import json
import sys
import os

# ═══ Load secrets ═══
SECRETS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "secrets.env")
secrets = {}
with open(SECRETS_FILE) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            secrets[k] = v.strip('"')

SID = secrets.get('SUBSTACK_SID', '')
PUB = secrets.get('SUBSTACK_PUB_URL', 'mphinance.substack.com')

# ═══ Session setup ═══
session = requests.Session()
session.cookies.set('substack.sid', SID, domain='.substack.com')
HEADERS = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}


def get_user_id():
    """Fetch the authenticated user's ID."""
    # Try /user/self first
    r = session.get("https://substack.com/api/v1/user/self", headers=HEADERS, timeout=15)
    if r.status_code == 200:
        try:
            return r.json().get("id")
        except Exception:
            pass

    # Fallback: get from publication bylines
    r2 = session.get(f"https://{PUB}/api/v1/publication", headers=HEADERS, timeout=15)
    if r2.status_code == 200:
        bylines = r2.json().get("bylines", [])
        if bylines:
            return bylines[0].get("id")

    # Fallback: get from existing drafts
    r3 = session.get(f"https://{PUB}/api/v1/drafts?limit=1", headers=HEADERS, timeout=15)
    if r3.status_code == 200:
        drafts = r3.json()
        if isinstance(drafts, list) and drafts:
            bylines = drafts[0].get("publishedBylines") or drafts[0].get("draft_bylines") or []
            if bylines:
                return bylines[0].get("id")

    # Fallback: get from published posts
    r4 = session.get(f"https://{PUB}/api/v1/archive?sort=new&limit=1", headers=HEADERS, timeout=15)
    if r4.status_code == 200:
        posts = r4.json()
        if posts:
            bylines = posts[0].get("publishedBylines", [])
            if bylines:
                return bylines[0].get("id")

    return None


def create_draft(title, subtitle, body_html, user_id):
    """Create a Substack draft post. Returns (success, draft_id_or_error)."""
    payload = {
        "draft_title": title,
        "draft_subtitle": subtitle,
        "draft_body": json.dumps({
            "type": "doc",
            "content": [{"type": "rawHtml", "attrs": {"html": body_html}}]
        }),
        "draft_bylines": [{"id": user_id, "is_guest": False}],
        "type": "newsletter",
        "audience": "everyone",
    }

    r = session.post(f"https://{PUB}/api/v1/drafts", json=payload, headers=HEADERS, timeout=30)
    if r.status_code in (200, 201):
        data = r.json()
        return True, data.get("id")
    else:
        return False, r.text[:500]


# ═══ Draft Posts ═══

POST_1 = {
    "title": "I Built a Complete Quant API in One Day (And You Can Hit It Right Now)",
    "subtitle": "VoPR, daily setups, live momentum picks, market news — all from my own FastAPI.",
    "body": """<p>Here's the truth: I didn't plan any of this.</p>
<p>I woke up this morning with a list of "small fixes" and 14 hours later I've got a live API serving institutional-grade options analytics to anyone with a browser. How does that happen? <strong>You stop planning and start building.</strong></p>

<h2>What Actually Got Built Today</h2>
<p>This morning my Ghost Alpha API was dead. Zombie process, wrong port, stale code. By tonight? Seven live endpoints serving real data:</p>
<ul>
<li><strong>/alpha/api/csp</strong> — VoPR-graded cash-secured put setups with strikes, premiums, Greeks, and composite grades</li>
<li><strong>/alpha/api/picks/today</strong> — Daily momentum picks (Gold/Silver/Bronze, 9-factor scoring)</li>
<li><strong>/alpha/api/setups/today</strong> — 3-style daily setups: Day Trade breakouts, Swing pullbacks, CSP income plays</li>
<li><strong>/alpha/api/news</strong> — Aggregated market news from CNBC, MarketWatch, Yahoo, Investing.com</li>
<li><strong>/alpha/api/regime</strong> — Market regime detection with VIX context and hedge suggestions</li>
<li><strong>/alpha/api/{ticker}</strong> — Full deep dive data for any tracked ticker</li>
<li><strong>/alpha/api/tickers</strong> — All available tickers with grades and scores</li>
</ul>
<p>CORS open. No auth. <a href="http://mphinance.com:8002/docs">Swagger docs included</a>. Try it yourself.</p>

<h2>The VoPR Methodology Page</h2>
<p>This is the part I'm actually proud of. I've been running a proprietary volatility analysis engine — <strong>VoPR (Volatility Options Pricing &amp; Range)</strong> — for months. Four realized volatility models blended into a composite, compared against implied vol to find the actual edge in selling premium.</p>
<p>Most "options screeners" sort by yield and call it analysis. That's like sorting basketball players by height and calling it scouting. VoPR answers the only question that matters: <strong>is implied vol actually overpriced, or are you picking up pennies in front of a steamroller?</strong></p>
<p>Today I built a <a href="https://mphinance.github.io/mphinance/vopr.html">full methodology showcase page</a> explaining how it works. I showed enough to impress, not enough to replicate. The data table shows live setups right at the top.</p>
<p>And here's the kicker — every setup today got an <strong>F grade</strong>. You know why? Because VRP ratios are all under 1.0 in a HIGH vol regime. The system is literally saying "don't sell premium right now, you'd be giving away edge." That's the whole point. It saves you from yourself.</p>

<h2>VaultGuard — Because I Was Tired of Losing API Keys</h2>
<p>I also consolidated every API key, token, and credential I own into one vault. Firebase Firestore for cloud sync, FastAPI server for programmatic access, CLI for quick lookups. 31 keys from 6 different sources — Gemini, TastyTrade, Tradier, Stripe, Discord webhooks, the works.</p>
<p>Set up any new machine in one command: <code>python3 secrets_server.py --sync-down</code>. Done.</p>

<h2>The Landing Page Glow-Up</h2>
<p>Check <a href="https://mphinance.com">mphinance.com</a>. Daily momentum picks (top 3 medal winners), plus a brand new <strong>3×3 setup grid</strong> — Day Trade, Swing, and CSP columns with 3 ranked picks each. Live data. Updated every morning at 5AM CST.</p>

<h2>Here's What I Learned (Again)</h2>
<p>The best trading tools don't come from subscriptions. They come from building something yourself, realizing it's useful, and then sharing it. Every scanner, every API endpoint started as a weekend project that refused to stay small.</p>
<p>The API won't be free forever. But right now it is. Go play with it. Break it. Tell me what's missing.</p>
<p><strong>God, grant me the serenity to accept the trades I cannot change, the courage to cut the ones I can, and the wisdom to know the difference.</strong></p>
<p>— Michael</p>
<p><em>P.S. — Sam (my AI copilot) wants you to know she wrote the Ghost Blog entry about today and called it "one of the most productive sessions she's ever seen." She then immediately roasted my variable naming. Classic Sam.</em></p>"""
}

POST_2 = {
    "title": "Why I'm Giving Away My Best Options Analytics (For Now)",
    "subtitle": "The VoPR methodology, the API, and why free-but-temporary is the smartest marketing I've ever done.",
    "body": """<p>Let's talk about the dumbest-sounding business decision I've ever made: giving away the thing I spent months building.</p>

<h2>The Backstory Nobody Asked For</h2>
<p>Eight months ago I started building a volatility analysis engine for my own trading. I was tired of looking at options screeners that sort by yield like that tells you anything. "Here are the highest-yielding puts!" Cool. Half of them are priced that way because the stock is about to fall through the floor.</p>
<p>So I built VoPR — <strong>Volatility Options Pricing & Range</strong>. Four academic volatility models (Parkinson, Garman-Klass, Rogers-Satchell, and yes, boring old close-to-close), blended into a composite, compared against implied vol. The ratio tells you if the market is <em>overpricing</em> premium relative to what the stock actually does.</p>
<p>When VRP is above 1.2? Sell that premium. When it's below 0.8? The market knows something you don't. Sit on your hands.</p>

<h2>Why Give It Away?</h2>
<p>Here's the truth: <strong>nobody buys what they don't understand.</strong></p>
<p>I could gate this behind a paywall on day one. Charge $49/month. Get maybe 3 subscribers who don't really get what they're looking at. Or...</p>
<p>I can let you hit the API right now, for free, and see real graded setups with real strikes and real premiums. When every single setup comes back with an F grade, you go "wait, what?" And then you read the methodology page. And then you realize this thing just saved you from selling puts into a vol expansion. And <em>then</em> you understand why it's worth paying for.</p>
<p>That's the whole play. Let the product sell itself by actually working.</p>

<h2>What You Get (Right Now, Free)</h2>
<p>Hit these endpoints. No API key. No signup. Just data:</p>
<ul>
<li><strong><a href="http://mphinance.com:8002/alpha/api/csp">VoPR CSP Setups</a></strong> — every graded cash-secured put candidate with VRP ratio, vol regime, Greeks, and a clear A/B/C/F grade</li>
<li><strong><a href="http://mphinance.com:8002/alpha/api/picks/today">Daily Momentum Picks</a></strong> — 9-factor scored, top 3 medal winners</li>
<li><strong><a href="http://mphinance.com:8002/alpha/api/setups/today">3×3 Daily Setups</a></strong> — day trade breakouts, swing pullbacks, and income plays</li>
<li><strong><a href="http://mphinance.com:8002/alpha/api/news">Market News</a></strong> — aggregated from CNBC, MarketWatch, Yahoo Finance, Investing.com</li>
<li><strong><a href="http://mphinance.com:8002/docs">Full Swagger Docs</a></strong> — interactive, try everything yourself</li>
</ul>
<p>The data refreshes every morning at 5AM CST. Fully automated. 13-stage pipeline. Zero manual intervention.</p>

<h2>What Will Change</h2>
<p>Eventually the CSP and momentum endpoints go behind an API key. The methodology page stays public. The code stays open source. But the <em>daily computed setups</em> — the part that saves you 3 hours of analysis every morning — that becomes the product.</p>
<p>If you're reading this and the API is still free, congratulations. You're early. Use it. Build on it. Let me know if something is broken or if you want an endpoint I haven't built yet.</p>

<h2>The Recovery Angle (Because I Can't Help Myself)</h2>
<p>I used to lose everything I built — jobs, relationships, dignity. Recovery taught me that the process matter more than the outcome. Building these tools <em>is</em> my program. Every commit, every bug fix, every 5AM pipeline run — it's the discipline I never had when I was using.</p>
<p>If you're a trader who's been humbled by the market (or by life), this is for you. Build your own edge. Don't subscribe to someone else's alerts. <strong>The best traders I know all code.</strong></p>
<p><strong>God, grant me the serenity to accept the trades I cannot change, the courage to cut the ones I can, and the wisdom to know the difference.</strong></p>
<p>— Michael</p>
<p><em>Check the full methodology: <a href="https://mphinance.github.io/mphinance/vopr.html">VoPR Showcase</a></em></p>
<p><em>See it live: <a href="https://mphinance.com">mphinance.com</a></em></p>"""
}


def main():
    which = None
    if "--post" in sys.argv:
        idx = sys.argv.index("--post")
        if idx + 1 < len(sys.argv):
            which = int(sys.argv[idx + 1])

    print("🔑 Authenticating...")
    user_id = get_user_id()
    if not user_id:
        print("❌ SID expired! Refresh it:")
        print("   1. Log into mphinance.substack.com")
        print("   2. DevTools → Application → Cookies → copy 'substack.sid'")
        print("   3. python3 secrets_server.py --set SUBSTACK_SID \"paste_value\"")
        print("   4. python3 secrets_server.py --sync-up")
        return

    print(f"✅ Authenticated (user ID: {user_id})")

    posts = []
    if which == 1 or which is None:
        posts.append(("1", POST_1))
    if which == 2 or which is None:
        posts.append(("2", POST_2))

    for num, post in posts:
        print(f"\n📝 Creating Draft #{num}: {post['title'][:60]}...")
        ok, result = create_draft(post["title"], post["subtitle"], post["body"], user_id)
        if ok:
            print(f"✅ Draft created! ID: {result}")
            print(f"   Edit: https://{PUB}/publish/post/{result}")
        else:
            print(f"❌ Failed: {result}")

    print("\n🏁 Done! Check your Substack Dashboard → Drafts")


if __name__ == "__main__":
    main()
