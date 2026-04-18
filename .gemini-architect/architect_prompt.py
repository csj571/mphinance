import json
import requests
import sys
import textwrap

API_KEY = "AIzaSyCRLrlnBmBqcP8dR6WOQGp3eKA3Hwk10gc"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"

# Load context files
with open("/home/mph/Antigravity/mphinance/VOICE.md") as f:
    voice = f.read()
with open("/home/mph/Antigravity/mphinance/SUBSTACK.md") as f:
    substack = f.read()
with open("/home/mph/Antigravity/mphinance/docs/articles/letf-scanner-v2/README.md") as f:
    article = f.read()

prompt = textwrap.dedent(f"""
You are the Architect Agent for Momentum Phinance. You are a world-class editorial consultant specializing in financial newsletter content that grows subscriber bases. Your job is to review, critique, and improve this Substack article written in Michael Hanko's voice.

=== VOICE GUIDE ===
{voice}

=== SUBSTACK FORMATTING RULES ===
{substack}

=== CURRENT ARTICLE DRAFT ===
{article}

=== YOUR TASK ===

Review this article as a ruthless editorial architect. The author wants this to be his BEST article yet. One that converts readers into subscribers. Analyze and provide specific, actionable feedback on:

1. **STRUCTURAL IMPROVEMENTS**: Is the article flow optimal? Are there sections that drag, that should be reordered, combined, or split? Is the pacing right? Does every section earn its place?

2. **VOICE AUTHENTICITY**: Rate how well this matches Michael's voice from VOICE.md. Where does it sound like AI wrote it? Where does it sound like a real human trading with his own money? Be merciless.

3. **COMEDY & PERSONALITY**: Where are the missed comedy opportunities? Michael's best content has jokes landing between data points. Where could we add analogies, metaphors, self-deprecation, or recovery wisdom that makes the data STICK?

4. **HOOK STRENGTH**: Is the opening strong enough to stop someone mid-scroll? Would YOU click this in a crowded inbox? How could the hook be sharper?

5. **SUBSCRIBER CONVERSION**: What would make a free reader say "I need to subscribe"? Where should the paywall go? What content is being given away that should be paywalled, or vice versa?

6. **METAPHOR OPPORTUNITIES**: Michael excels at explaining finance through everyday life and recovery analogies. Where can we add metaphors that make technical concepts (ADX delta, ATR squeeze, cubic spline IV smoothing) accessible and memorable?

7. **MISSING CONTENT**: What's NOT in this article that SHOULD be? Is there a section that a reader would expect that's missing?

8. **LINE-LEVEL EDITS**: Give me 5-10 specific lines that could be rewritten for more punch, more personality, more Michael.

IMPORTANT CONSTRAINTS:
- NO EM DASHES. Ever. Not one. Don't suggest any.
- No markdown tables. Data = images.
- Keep the PG-13 profanity level. Bar conversation, not locker room.
- Recovery/AA wisdom should feel natural, not forced.
- Michael is the narrator, Sam is referenced in third person.

Format your response as a clear, numbered action plan with specific rewrites where applicable. Be brutal. Be specific. Be helpful.
""")

payload = {
    "contents": [{"parts": [{"text": prompt}]}],
    "generationConfig": {
        "temperature": 0.9,
        "maxOutputTokens": 8192
    }
}

headers = {"Content-Type": "application/json"}
response = requests.post(URL, headers=headers, json=payload, timeout=120)

if response.status_code == 200:
    data = response.json()
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    print(text)
else:
    print(f"ERROR {response.status_code}: {response.text[:500]}")
