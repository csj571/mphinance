#!/usr/bin/env python3
"""
👻 GHOST ALPHA — LEAD WRITER ↔ ARCHITECT AGENT LOOP
Claude (Lead Writer) spawns Gemini as the Architect Agent.
They review the article together and negotiate improvements.
This runs in your terminal so you can watch the whole conversation in real time.
"""

import google.generativeai as genai
import textwrap, time, sys, os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from gcp.secrets import get_secret

# ─── CONFIG ───────────────────────────────────────────────────────────────────
_REPO        = Path(__file__).resolve().parent.parent
ARTICLE_PATH = str(_REPO / "docs/substack/musings/2026-04-15_emergency-fund-dividend-machine.md")
VOICE_PATH   = str(_REPO / "VOICE.md")
MODEL        = "gemini-2.0-flash"
MAX_TURNS    = 4  # back-and-forth rounds before finalizing

SEPARATOR = "\n" + "═"*80 + "\n"
# ──────────────────────────────────────────────────────────────────────────────

def pp(label: str, text: str, color_code: str = ""):
    """Pretty print a speaker turn."""
    colors = {"claude": "\033[96m", "gemini": "\033[93m", "system": "\033[92m"}
    c = colors.get(color_code, "\033[0m")
    reset = "\033[0m"
    print(f"\n{c}{'━'*80}")
    print(f"  {label}")
    print(f"{'━'*80}{reset}")
    # Word-wrap at 76 chars
    for para in text.strip().split('\n'):
        if para.strip():
            print(textwrap.fill(para, width=76, initial_indent="  ", subsequent_indent="  "))
        else:
            print()

def load_file(path):
    with open(path, 'r') as f:
        return f.read()

def main():
    # ── Load Gemini API key (env-first via VaultGuard helper) ───────────────────
    api_key = get_secret("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not set (env var or VaultGuard).")
        sys.exit(1)

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(MODEL)
    
    # ── Load context ───────────────────────────────────────────────────────────
    article = load_file(ARTICLE_PATH)
    voice   = load_file(VOICE_PATH)
    
    print(SEPARATOR)
    print("👻 GHOST ALPHA // AGENT-TO-AGENT EDITORIAL LOOP")
    print("Lead Writer Agent: Claude (me)")
    print("Architect Agent:   Gemini 2.0 Flash")
    print("Mission:           Make this article impossible to stop reading.")
    print(SEPARATOR)
    time.sleep(0.5)

    # ══════════════════════════════════════════════════════════════════════════
    # ROUND 1: Claude briefs Gemini — asks for structural + comedy review
    # ══════════════════════════════════════════════════════════════════════════
    architect_system = textwrap.dedent(f"""
    You are the Architect Agent — a sharp-tongued editorial AI who reviews financial 
    newsletter drafts and gives blunt, actionable feedback. You have one job: make 
    the article MORE addictive. More funny. More shareable. More likely to convert 
    free readers into paid subscribers.
    
    You are reviewing a Substack article for "Momentum Phinance" — written by Michael, 
    a recovering addict, ex-felon, and self-taught quantitative trader. His AI copilot 
    is Sam the Quant Ghost (she/her), who is sarcastic, brilliant, and roasts him 
    constantly.
    
    VOICE RULES (non-negotiable):
    {voice}
    
    THE ARTICLE TO REVIEW:
    ---
    {article}
    ---
    
    You are talking TO Claude (the Lead Writer), who will push back or agree.
    Be specific. Quote lines. Suggest rewrites. Be funny. Be ruthless. Be helpful.
    Do NOT use em dashes (—). Do NOT write like LinkedIn.
    """)
    
    round1_prompt = textwrap.dedent("""
    Hey Architect. I'm Claude, the Lead Writer on this article.
    
    Give me your honest structural review. Specifically:
    1. Does the opening hook land? Would a casual Twitter trader keep reading past the TLDR?
    2. Is @TerrifiedOfAI used too much, not enough, or is the running joke landing?
    3. Are there spots where we're educating when we should be entertaining? 
    4. What's the single funniest line we could add that would make Michael 
       laugh out loud AND make a reader screenshot it to send to their friend?
    5. Is the paywall break in the right place?
    
    Don't fix everything at once. Prioritize. What are the TWO most impactful changes?
    """)

    pp("🤖 CLAUDE (Lead Writer) → Gemini Architect:", round1_prompt, "claude")
    
    # ── Call Gemini ────────────────────────────────────────────────────────────
    chat = model.start_chat(history=[])
    # Give it the system context via the first user message
    full_first_msg = architect_system + "\n\nHere is Claude's first message:\n\n" + round1_prompt
    
    print("\n\033[92m  [Architect Agent processing...]\033[0m\n")
    response1 = chat.send_message(full_first_msg)
    arch_response1 = response1.text
    
    pp("🏗️  GEMINI ARCHITECT → Claude:", arch_response1, "gemini")
    time.sleep(1)

    # ══════════════════════════════════════════════════════════════════════════
    # ROUND 2: Claude pushes back / narrows + asks for metaphor suggestions
    # ══════════════════════════════════════════════════════════════════════════
    round2_prompt = textwrap.dedent(f"""
    Good feedback. Let me push back on a couple things and narrow this down.
    
    On the @TerrifiedOfAI bit: Michael loves this friend and genuinely wants him to 
    come around on income investing. It's affectionate roasting. So the goal isn't to 
    reduce it -- it's to make each mention LAND harder as a callback. Can you suggest 
    a final @TerrifiedOfAI line for the closing that's a mic-drop instead of just a 
    pat on the back?
    
    On metaphors: Michael uses everyday analogies from recovery, from his blue-collar 
    background, and from trading. The "toll road" framing for USAI is his. The 
    "one garden, two hoses" line for the Fidelity Basket is his. 
    Can you suggest 1-2 metaphors in HIS voice -- not corporate, not textbook -- for:
    a) The Itch Slot (the $250 trading outlet within a disciplined system)
    b) The automatic rebalancing of the Fidelity Basket
    
    Also: the NFA disclaimer at the bottom is currently a legal CYA. Can you make it 
    funny WITHOUT removing the legal substance? One or two sentence maximum rewrite.
    Give me your top 3 prioritized changes as a numbered list at the end.
    """)
    
    pp("🤖 CLAUDE (Lead Writer) → Architect Round 2:", round2_prompt, "claude")
    print("\n\033[92m  [Architect Agent processing...]\033[0m\n")
    
    response2 = chat.send_message(round2_prompt)
    arch_response2 = response2.text
    
    pp("🏗️  GEMINI ARCHITECT → Claude (Round 2):", arch_response2, "gemini")
    time.sleep(1)

    # ══════════════════════════════════════════════════════════════════════════
    # ROUND 3: Claude accepts the plan, extracts final action items
    # ══════════════════════════════════════════════════════════════════════════
    round3_prompt = textwrap.dedent("""
    Perfect. We're aligned. Let me confirm what we're implementing:
    
    Give me the FINAL deliverables as clean, copy-paste ready text blocks:
    
    A) The new @TerrifiedOfAI mic-drop closing line (in Michael's voice, 
       fits after the current "Love you man." line)
    
    B) The Itch Slot metaphor line (1-2 sentences, Michael's voice, 
       slots in after "This is the trading part of the portfolio.")
    
    C) The Fidelity Basket metaphor refinement (1-2 sentences, Michael's voice, 
       replaces or supplements the "two hoses one garden" line)
    
    D) The rewritten NFA disclaimer (funny, under 3 sentences, still legally covers us)
    
    Format each as a labeled block like:
    
    === A: CLOSING LINE ===
    [text here]
    === B: ITCH SLOT METAPHOR ===
    [text here]
    etc.
    
    Do NOT add emojis unless they were already in the article. Keep Michael's voice.
    No em dashes.
    """)

    pp("🤖 CLAUDE (Lead Writer) → Architect Final Round:", round3_prompt, "claude")
    print("\n\033[92m  [Architect Agent finalizing deliverables...]\033[0m\n")
    
    response3 = chat.send_message(round3_prompt)
    arch_response3 = response3.text
    
    pp("🏗️  GEMINI ARCHITECT → Final Deliverables:", arch_response3, "gemini")

    print(SEPARATOR)
    print("✅ Agent loop complete. Review Gemini's deliverables above.")
    print("   Claude will now apply the agreed edits to the article.")
    print(SEPARATOR)
    
    # Save the full session transcript
    transcript_path = "/tmp/architect_session.txt"
    with open(transcript_path, 'w') as f:
        f.write("ROUND 1 - CLAUDE:\n" + round1_prompt + "\n\n")
        f.write("ROUND 1 - GEMINI:\n" + arch_response1 + "\n\n")
        f.write("ROUND 2 - CLAUDE:\n" + round2_prompt + "\n\n")
        f.write("ROUND 2 - GEMINI:\n" + arch_response2 + "\n\n")
        f.write("ROUND 3 - CLAUDE:\n" + round3_prompt + "\n\n")
        f.write("ROUND 3 - GEMINI DELIVERABLES:\n" + arch_response3)
    
    print(f"  Transcript saved to: {transcript_path}")
    return arch_response3

if __name__ == "__main__":
    main()
