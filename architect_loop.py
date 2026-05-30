#!/usr/bin/env python3
"""Lead Writer + Architect Agent feedback loop for the Substack draft."""

import os
import sys
import google.genai as genai
from google.genai import types
from gcp.secrets import get_secret

api_key = get_secret("GEMINI_API_KEY")
if not api_key:
    sys.exit("ERROR: GEMINI_API_KEY not set (env var or VaultGuard).")

client = genai.Client(api_key=api_key)
MODEL = "models/gemini-2.5-flash"

import time

def call(prompt, attempt=0):
    try:
        response = client.models.generate_content(model=MODEL, contents=prompt)
        return response.text
    except Exception as e:
        if "429" in str(e) and attempt < 3:
            wait = 30 * (attempt + 1)
            print(f"  [Rate limited, waiting {wait}s...]")
            time.sleep(wait)
            return call(prompt, attempt + 1)
        raise

with open("docs/substack/musings/2026-04-21_road-to-2k-wheel.md") as f:
    draft = f.read()

VOICE_RULES = """
VOICE RULES (non-negotiable):
- No em dashes (—) ever. Use commas, colons, or rewrite.
- No markdown tables. Use prose or generated images instead.
- PG-13 profanity is fine ("damn", "bullsh*t", "degenerate").
- Short paragraphs, max 3 sentences.
- Bold openers, real numbers, real P&L — no theoretical examples.
- Michael writes as Momentum Phinance. Sam (she/her) is the AI copilot, sarcastic and brilliant.
- Closing CTA: always a subscribe nudge, never desperate.
- Never start with "In this article..."
- Uses "True Basis", "The Phund", "money glitch" as Michael's branded phrases.
- BTG was added TODAY because gold is at all-time highs, tariff chaos is driving safe-haven flows,
  central banks are buying gold at record pace, and BTG pays a dividend while trading in a tight
  $4-$5 range. The $5 calls pay $10-15 per contract (2-3% every 2 weeks). The real kicker: gold
  miners are operationally leveraged to gold prices — when gold goes up 10%, miner profits can go
  up 30-40%. BTG is essentially a boring money printer in a macro tailwind.
- This week's Substack theme: THE WHEEL. All posts this week are wheel-related.
  Prior posts this week: 35-Stock Protocol (April 18), Lodgepole Pine essay (April 18).
  This is the wheel-specific deep dive. It should feel like the final piece of a series.
- The screenshots attached show Michael's OTHER wheel tracker (the Decay Derby / CSP tracker app):
  ONDS won ($17.31 NET P/L), AG active ($32 premium, $20 strike, 20% port), two UAMY positions
  active ($10 and $15 premiums, $9.50 strike). Portfolio value: $10,017.31, 61% capital free,
  100% win rate. This is a DIFFERENT account than Tastytrade — but shows the broader wheel system.
- The title needs to be changed to something clever referencing 42% (the Hitchhiker's Guide to the
  Galaxy "answer to life, the universe, and everything" joke). Michael hinted at a "clever idea."
"""

CURRENT_STATE = f"""
CURRENT DRAFT:
{draft}

CONTEXT: 
- This is a Substack post for Momentum Phinance (Michael's brand).
- It covers the Tastytrade wheel account: DDD (true basis $1.87), RR (true basis $2.69), BTG ($4.75 new).
- The 42% probability number is a Hitchhiker's Guide joke and should be in the title.
- Michael also runs a separate wheel tracker (Decay Derby app) showing ONDS, AG, UAMY positions.
  Those screenshots need to be mentioned/integrated as "proof the system works across accounts."
- 50% of Substack subscription revenue goes directly into the Tastytrade account as deposits.
  More subscribers = faster path to $2,000 = escape from Tastytrade by Q2.
- BTG was bought TODAY (April 21, 2026) and we need a better explanation of WHY.
"""

# ---- ROUND 1: Architect analyzes ----
architect_prompt = f"""
You are the Architect Agent — a senior content strategist and financial writer.

{VOICE_RULES}

{CURRENT_STATE}

Your job:
1. Analyze the article for structural improvements, missing beats, and opportunities to add personality.
2. Give me your top 5 prioritized suggestions. Focus on:
   - Title change (42% Hitchhiker's Guide angle — what's the cleverest version?)
   - BTG section: make the "why I bought it TODAY" more compelling with the macro context
   - Decay Derby screenshots: how to weave in the other account's data as social proof
   - Overall flow and punchiness
   - Any missing CTA or emotional hook opportunities
3. Be specific. No vague "make it more engaging" advice. Tell me exactly what to change and why.
4. Keep your response under 600 words.
"""

print("=" * 70)
print("ARCHITECT AGENT — Round 1 Analysis")
print("=" * 70)
architect_r1 = call(architect_prompt)
print(architect_r1)

# ---- ROUND 2: Lead Writer pushes back / refines ----
lead_writer_prompt = f"""
You are the Lead Writer Agent. You just received the Architect's feedback below.

ARCHITECT FEEDBACK:
{architect_r1}

Your job:
1. Push back on anything too complex or off-brand for Michael's voice.
2. Ask ONE clarifying question about the Decay Derby screenshot integration.
3. Propose a FINAL prioritized action plan with exactly 5 items. Be opinionated.
4. Keep it under 400 words.
"""

print()
print("=" * 70)
print("LEAD WRITER AGENT — Round 2 Pushback & Refinement")
print("=" * 70)
lead_writer_r2 = call(lead_writer_prompt)
print(lead_writer_r2)

# ---- ROUND 3: Architect agrees / finalizes ----
architect_final_prompt = f"""
You are the Architect Agent.

The Lead Writer responded:
{lead_writer_r2}

Now finalize. Give me:
1. AGREED FINAL PLAN — exactly 5 numbered items in priority order.
2. For each item, provide the EXACT text change or addition (quote it). Be surgical.
3. For the title, give me your top 3 options with the 42% / Hitchhiker's Guide joke.
4. Under 500 words total.
"""

print()
print("=" * 70)
print("ARCHITECT AGENT — Round 3 Final Plan")
print("=" * 70)
print(call(architect_final_prompt))
print()
print("=" * 70)
print("LOOP COMPLETE. Review above and approve changes.")
print("=" * 70)
