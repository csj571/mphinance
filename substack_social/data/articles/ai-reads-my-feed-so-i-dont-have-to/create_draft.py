#!/usr/bin/env python3
"""
create_draft_ai_reads.py
Creates the "AI Reads My Feed So I Don't Have To" Substack draft.

Uses native ProseMirror nodes (paragraph, heading, blockquote, hardBreak)
NOT rawHtml (which is broken as of March 2026).

Run from the mphinance directory:
    python3 create_draft_ai_reads.py

Requires SUBSTACK_SID in secrets.env.
"""

import requests
import json
import os

# ─── Load secrets ────────────────────────────────────────────────────────────
from urllib.parse import unquote

_here = os.path.dirname(os.path.abspath(__file__))
_mphinance = os.path.expanduser("~/Antigravity/mphinance/secrets.env")
SECRETS_FILE = os.path.join(_here, "secrets.env") if os.path.exists(os.path.join(_here, "secrets.env")) else _mphinance
secrets = {}
with open(SECRETS_FILE) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            secrets[k] = v.strip('"')

# URL-decode the SID (secrets.env stores it percent-encoded)
_sid_raw = os.environ.get('SUBSTACK_SID') or os.environ.get('SUBSTACK_API_KEY') or secrets.get('SUBSTACK_SID', '')
SID = unquote(_sid_raw)
PUB = secrets.get('SUBSTACK_PUB_URL', 'mphinance.substack.com')

session = requests.Session()
session.cookies.set('substack.sid', SID, domain='.substack.com')
HEADERS = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}


# ─── ProseMirror helpers ──────────────────────────────────────────────────────
def p(*items):
    """Paragraph node. Items can be strings or inline nodes."""
    content = []
    for item in items:
        if isinstance(item, str):
            if item:
                content.append({"type": "text", "text": item})
        else:
            content.append(item)
    return {"type": "paragraph", "content": content}

def h(level, text):
    return {"type": "heading", "attrs": {"level": level}, "content": [{"type": "text", "text": text}]}

def bold(text):
    return {"type": "text", "text": text, "marks": [{"type": "bold"}]}

def link(text, url):
    return {"type": "text", "text": text, "marks": [{"type": "link", "attrs": {"href": url, "target": "_blank"}}]}

def blockquote(*paragraphs):
    return {"type": "blockquote", "content": list(paragraphs)}

def hr():
    return {"type": "horizontalRule"}

def paywall():
    return {"type": "paywall"}

def _ascii(s):
    """Strip non-ASCII to keep Substack editor happy."""
    return s.encode('ascii', 'ignore').decode('ascii')


# ─── Article content ──────────────────────────────────────────────────────────
# NOTE: Images are embedded via Substack's image upload after draft creation.
# Paste image URLs into the draft editor manually, or use the media upload API.
# The image filenames are noted in comments below for reference.

doc_content = [
    # ── Eco section ────────────────────────────────────────────────────────
    h(2, "First, a Quick Detour for a Friend of Ours"),

    p("We know someone who isn't against AI. They're against the water bill that comes with it. And after reading a recent Tom's Hardware piece, that's a completely reasonable position."),

    p("Here's the short version: a data center campus in Fayette County, Georgia quietly used 29 million gallons of water without it being metered or billed. A \"procedural mix-up\" during a smart meter transition. Two industrial water connections just... missed. County officials discovered it after residents in a nearby neighborhood started complaining about low water pressure. While the county was actively asking residents to conserve water during a regional drought. The company eventually paid $147,474 in retroactive charges. No fines."),

    p("To be clear: 29 million gallons for construction prep, not ongoing operations. But that number lands differently when your neighborhood's taps are running low."),

    p("The water and energy concerns around AI infrastructure are real. A single large model training run can consume as much electricity as 100 American homes use in a full year. Data centers globally are tracking toward 1,000 terawatt-hours of annual consumption by 2026. AI alone could double global data center power demand by 2030."),

    p("If someone you know is skeptical of AI because of what it costs the planet, the right response isn't to wave it away. The right response is to show them where capital is already moving to solve it."),

    p("Here's what we found."),

    # ── IMAGE PROMPT (paste into Substack AI image generator) ──────────────
    blockquote(
        p(bold("[IMAGE PROMPT FOR SUBSTACK AI GENERATOR]")),
        p("Dark Bloomberg terminal-style infographic. Background pure black. Title in neon green monospace: 'GREEN AI: WHERE CAPITAL IS MOVING'. Four company cards in a 2x2 grid. Top left cyan border: '$NBIS NEBIUS — PUE 1.13 vs industry avg 1.58 — Heats Finnish town with GPU exhaust — $2B NVIDIA Investment — NASDAQ: NBIS'. Top right gold border: 'CRUSOE ENERGY — $2.77B raised, $10B valuation — 900 MW Texas campus — Solar plus iron-air batteries — Microsoft anchor — Pre-IPO'. Bottom left green border: 'PANTHALASSA — $140M Series B, $1B valuation — 85m floating ocean nodes — Wave power plus seawater cooling — Peter Thiel backed — Ocean-3 pilot 2026'. Bottom right orange border: 'WAVR TECHNOLOGIES — UNLV Spinout — Extracts water from air at 10% humidity — Uses data center waste heat — Early stage'. Monospace text throughout. No rounded corners. Bloomberg aesthetic."),
    ),

    h(3, "$NBIS: Nebius Group -- The Giant Space Heater"),

    p("This one is investable right now. Nebius Group (NASDAQ: $NBIS) built their flagship data center in Mantsala, Finland from the ground up for maximum thermal efficiency."),

    p("Their facility achieves a Power Usage Effectiveness of 1.13. The global industry average is 1.58. PUE measures how much total energy a facility uses versus how much goes directly to compute. At 1.13, almost everything going in is doing actual work."),

    p("The waste heat story is the piece that makes this genuinely different. Instead of venting all that server heat into the atmosphere, Nebius captures it and feeds it directly into Mantsala's municipal district heating network. They are literally heating a Finnish town with their GPU exhaust. Roughly 75% of the city center's heating demand. The building is a data center and a community utility at the same time."),

    p("In March 2026, NVIDIA dropped $2 billion into them. They're now planning a second Finnish facility in Lappeenranta at 310 MW, targeted for 2027. If you want publicly traded exposure to AI infrastructure done right, this is the cleanest on-ramp we've found."),

    h(3, "Crusoe Energy -- From Stranded Gas to Renewable Campus"),

    p("Crusoe started clever: they took modular data centers to oil fields to run off flared natural gas that would otherwise just burn into the atmosphere for nothing. Capturing waste gas to run compute is still meaningfully better than letting it flare."),

    p("They've since gone all-in on renewables. In March 2025, they sold off their Digital Flare Mitigation and Bitcoin mining divisions entirely to focus on vertically integrated AI infrastructure."),

    p("Their campus in Abilene, Texas is one of the most interesting projects in the space. Multi-gigawatt scale, Microsoft as anchor tenant, solar backed by second-life EV batteries through a Redwood Materials partnership. In March 2026, they secured 12 gigawatt-hours of iron-air battery storage from Form Energy for sustained overnight power. NVIDIA is a Series E investor. Total funding: $2.77 billion at a $10 billion valuation. Not publicly traded yet, but one to watch for an IPO."),

    h(3, "Panthalassa -- AI Data Centers in the Ocean"),

    p("This one sounds like a joke until you look at the specs."),

    p("Panthalassa is an Oregon startup building autonomous, 85-meter-long steel nodes that float in the open ocean. As they bob with the waves, they force water through internal turbines to generate electricity. That electricity runs AI chips on board. The surrounding seawater cools everything naturally. Starlink handles the data link. No cables to shore. No grid dependency whatsoever."),

    p("$140 million Series B led by Peter Thiel. $1 billion valuation. Their Ocean-3 series nodes are scheduled for pilot testing in the northern Pacific later in 2026, with commercial deployments targeted for 2027."),

    p("Is it speculative? Completely. Is it the most unhinged idea that might actually work? Also yes."),

    h(3, "WAVR Technologies -- Turning Server Heat Into Drinking Water"),

    p("This one is the sleeper."),

    p("WAVR is a UNLV spinout based in Las Vegas. Their technology extracts liquid water directly from atmospheric air using a hybrid hydrogel and liquid desiccant system that works even in arid climates with humidity as low as 10%."),

    p("The data center connection is direct. Servers generate massive amounts of low-grade waste heat in the 30 to 70 degree Celsius range. WAVR's system uses that waste heat as an input, which increases efficiency and drives the cost of produced water toward municipal rates. Instead of a data center consuming freshwater for cooling and venting heat into the atmosphere, you get a facility that produces usable water as a byproduct."),

    p("Think about that relative to Fayette County."),

    p("Not publicly traded. Early stage. But if you're looking for a technology that directly converts AI's biggest environmental liability into a resource, this is the one to watch."),

    h(3, "The Pattern"),

    p("The story isn't \"AI is bad for the planet.\" The story is \"AI has an energy and water problem, and serious capital is moving hard at the people trying to solve it.\""),

    p("For the skeptical investor, that's where the asymmetric opportunities live. Early enough that most people aren't looking. Specific enough that the thesis is clear."),

    p("Worth watching: $NBIS for the public market play, Crusoe for the pre-IPO pipeline, Panthalassa for the moonshot, WAVR for the water arbitrage nobody has priced yet."),

    hr(),

    # ── Main article ───────────────────────────────────────────────────────
    h(2, "Now Back to Our Regularly Scheduled Programming"),

    p("I subscribe to 74 Substack writers. Seventy-four. I'm not gonna pretend I read them all every morning. I have a full-time obsession building a swarm intelligence trading system, a kid, a recovery program, and approximately zero extra hours. But I also can't afford to miss the good stuff."),

    p("So I built a machine to read it for me. And then I taught it to sound like me."),

    p("Here's the whole thing, soup to nuts. If you're a Substack writer who wants to stay plugged into your community without losing your entire morning to your inbox, this is for you."),

    hr(),
    h(2, "The Problem Every Substack Writer Has and Nobody Talks About"),

    p("You follow people. Smart people. Young Bull is breaking down why ARM is the layer beneath the layer. SpotGamma is tracking vol compression going into NVDA earnings. Henrik Zeberg is calling the terminal wave of this entire cycle. The Disruptive Investor is posting AAOI up 71% in 35 days with receipts."),

    p("And you're scrolling your inbox like it's a second job."),

    p("The real cost isn't the 45 minutes it takes. It's that you read everything passively. You have no record of what you read. You have no quick reference for \"what was the thesis on ASTS again?\" And you definitely don't have a curated one-liner ready to drop in as a comment that sounds like you, not a bot."),

    p("I fixed all three of those."),

    hr(),
    h(2, "What I Built (Plain English Version)"),

    p("Three scripts. One session cookie. Here's the architecture:"),

    # ── IMAGE PROMPT (paste into Substack AI image generator) ──────────────
    blockquote(
        p(bold("[IMAGE PROMPT FOR SUBSTACK AI GENERATOR]")),
        p("Dark terminal-style pipeline flow diagram. Black background. Three boxes connected by neon green arrows. Left box green border: 'SUBSTACK /reader/feed — 74 subscriptions — Posts plus Notes — Mixed feed API'. Center box gold border: 'pnpm summarize — Strips HTML — Maps pub names — Applies time filter — Writes markdown'. Right box green border: 'daily-reads-digest.md — Clickable links — Voice-matched replies — Notes section'. Below all three, a full-width cyan-bordered box: 'pnpm engage — Comment scanner plus READ-ONLY reply drafts'. All monospace font. Bloomberg terminal aesthetic. No rounded corners."),
    ),

    p(bold("pnpm summarize"), " hits Substack's internal /reader/feed endpoint, the same mixed feed your inbox uses. It pulls Posts AND Notes, strips out the HTML, maps publication IDs to real names, applies a 24-hour time filter, and writes everything to a single markdown file. Every entry gets a pre-filled one-liner comment in my voice."),

    p(bold("pnpm analytics"), " pulls my own post and note performance. Likes, comments, restacks. You look at this once a day and you know exactly which posts are gaining momentum."),

    p(bold("pnpm engage"), " scans recent comments on my own posts, filters out my previous replies, and prints each comment with a suggested one-sentence response. It's read-only. The thing literally prints a banner at the top every single run that says \"No posts. No comments. No likes. Ever.\" I built the guardrails in because AI writing as you without permission is how you end up with posts you didn't write and subscribers you didn't earn."),

    hr(),
    h(2, "Today's Digest (The Short Version)"),

    p("Here's what the machine surfaced this morning. Five posts worth your time, with my actual reaction to each one."),

    p(bold("Holding ASTS Into Earnings: Part 1 by Young Bull")),
    p("Pre-earnings conviction post. He's holding. Part 2 lands after the print. This is how you build a following: show your work before the result, not after."),
    blockquote(p("The Phund is watching the ASTS print because narrating the outcome is easier than trading the volatility.")),

    p(bold("Weekly Market Outlook: CPI, OPEX, and a Crowded AI Rally by TanukiTrade")),
    p("The real signal: the rally is six weeks old, vol is compressed, and we're walking into CPI, PPI, OPEX, and NVDA earnings in the same week. SpotGamma said it too: strong tape, crowded structure."),
    blockquote(p("The rally is narrow enough to walk a tightrope, so keep your risk gates tight.")),

    p(bold("The Deep Dive: The Dominant Supplier AI Cannot Function Without by The Disruptive Investor")),
    p("Optical networking. Compound semiconductors. The bottleneck nobody is talking about because everyone is still arguing about which GPU wins."),
    blockquote(p("Optical networking is the real bottleneck, and silicon is starting to look like a legacy asset.")),

    p(bold("Google Closes the Gap on NVIDIA by Tiger Capital Research")),
    p("$4.67T vs $4.79T. Google Cloud up 63% QoQ, backlog nearly doubled to $460B. Full-stack integration beats raw model performance."),
    blockquote(p("Google is trying to build a vertical money glitch to rival NVIDIA's crown.")),

    p(bold("90% of Your Job is Relieving Anxiety by The No-Stress Trader")),
    p("Not a trading post. A mental health post disguised as a trading post. \"You can only gain clarity by execution.\""),
    blockquote(p("Trading isn't about being right, it's about staying calm enough to not pull the trigger on your own foot.")),

    hr(),
    h(2, "How You Build This Yourself"),

    p("The whole thing lives on GitHub at jakub-k-slys/substack-api. I forked it and extended it. You need:"),
    p("A Substack account with subscriptions. Node.js and pnpm installed. Your SUBSTACK_SID session cookie from browser dev tools. About 45 minutes to wire it up."),
    p("The core credential is just a cookie. Substack doesn't have a public API, but their internal API is fully functional and the endpoints are consistent. The library handles auth, pagination, rate limiting, and validation."),
    p("Once it's running, pnpm summarize takes about 90 seconds to produce a complete markdown digest of everything published in the last 24 hours across all your subscriptions."),

    hr(),
    h(2, "Here's the Truth About Growing on Substack"),

    p("The writers who grow aren't the ones posting the most."),
    p("They're the ones who show up consistently in the comments of other writers. Not with generic responses. With actual takes. A good comment on KASM Capital's options flow breakdown or a thoughtful reply to VantagePoint's sector analysis does more for your subscriber count than posting three times a week."),
    p("The automation gives you the raw material. The voice-matching gives you the quality bar. The read-only guardrail keeps you honest."),
    p("You still have to hit send. That's your job. The machine just makes sure you've done your reading first."),

    hr(),
    h(2, "Who Else is Doing This Right"),

    p("Young Bull / KASM Capital / TanukiTrade / The No-Stress Trader / The Disruptive Investor / Tiger Capital Research / SpotGamma / Henrik Zeberg / VantagePoint AI / TradingWarz / Glitch SPX / Cleaner to Consistent / The M&A Hunter / BiggerPicture Trading / Quant Enthusiasts / Stats Edge / Cassandra Unchained / Marlin Capital"),

    p("Good people. Real content. Worth your time."),

    paywall(),

    h(2, "The Full Technical Breakdown (Paid)"),
    p("What's above is the what. Below is the how. Every endpoint, every gotcha, every rate limit I hit before figuring out the right call intervals."),
    p("The exact session cookie format and how to extract it without touching a CLI. The /reader/feed cursor pagination pattern -- it's opaque base64, not offset-based. How to distinguish a Note from a Post from a Chat from the same API response. Why rawHtml is completely broken for programmatic draft creation and what actually works. The ProseMirror JSON structure Substack actually accepts."),
    p("The repo is public. The pattern is yours. Subscribe if you want the full walkthrough."),

    hr(),

    p("\"You can only gain clarity by execution.\""),
    p("That's from Mr. Sicko today. He's right. I've been sitting on this automation for weeks because I kept thinking it needed to be more polished. It didn't. It needed to ship."),
    p("So here it is. Shipped."),
    p("- Michael Hanko, Managing Partner, The Phund"),
]

doc = {"type": "doc", "content": doc_content}


# ─── Auth & draft creation ────────────────────────────────────────────────────
def get_user_id():
    # Fallback: get from published posts (most reliable with this cookie format)
    r = session.get(f"https://{PUB}/api/v1/archive?sort=new&limit=1", headers=HEADERS, timeout=15)
    if r.status_code == 200:
        posts = r.json()
        if posts:
            bylines = posts[0].get("publishedBylines", [])
            if bylines:
                return bylines[0].get("id")

    # Hardcoded fallback for mphinance
    return 108093971


def create_draft():
    user_id = get_user_id()
    if not user_id:
        print("ERROR: Could not get user ID. Check your SUBSTACK_SID.")
        return

    print(f"Authenticated as user ID: {user_id}")

    payload = {
        "draft_title": "AI Reads My Feed So I Don't Have To",
        "draft_subtitle": "A Substack writer's guide to building your own digest machine, plus: green AI companies for the energy-skeptical investor.",
        "draft_body": json.dumps(doc),
        "draft_bylines": [{"id": user_id, "is_guest": False}],
        "type": "newsletter",
        "audience": "everyone",
    }

    r = session.post(f"https://{PUB}/api/v1/drafts", json=payload, headers=HEADERS, timeout=30)

    if r.status_code in (200, 201):
        data = r.json()
        draft_id = data.get("id")
        print(f"\nDraft created successfully!")
        print(f"Draft ID: {draft_id}")
        print(f"Edit URL: https://{PUB}/publish/post/{draft_id}")
        print(f"\nNEXT STEPS:")
        print(f"1. Open the edit URL above")
        print(f"2. Insert images at the marked locations:")
        print(f"   - After 'Here's what we found.' -> eco_ai_companies.png")
        print(f"   - In 'What I Built' section -> pipeline_flow.png")
        print(f"3. Review, add hero image, publish when ready")
    else:
        print(f"ERROR {r.status_code}: {r.text[:500]}")


if __name__ == "__main__":
    create_draft()
