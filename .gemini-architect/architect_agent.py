#!/usr/bin/env python3
"""
Architect Agent - Gemini-powered editorial review loop.
Lead Writer (Claude) spawns this to get structural feedback on articles.
"""

import json
import sys
import requests
import os

API_KEY = os.environ.get("GEMINI_API_KEY")
MODEL = "gemini-2.5-flash"
ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"

# Conversation history for multi-turn
conversation_history = []

def call_gemini(user_message):
    """Send a message to Gemini and get a response, maintaining conversation history."""
    conversation_history.append({
        "role": "user",
        "parts": [{"text": user_message}]
    })
    
    payload = {
        "contents": conversation_history,
        "generationConfig": {
            "temperature": 0.9,
            "maxOutputTokens": 8192,
        }
    }
    
    resp = requests.post(ENDPOINT, json=payload, timeout=120)
    resp.raise_for_status()
    
    data = resp.json()
    reply = data["candidates"][0]["content"]["parts"][0]["text"]
    
    # Add assistant response to history
    conversation_history.append({
        "role": "model",
        "parts": [{"text": reply}]
    })
    
    return reply

def main():
    if len(sys.argv) < 2:
        print("Usage: architect_agent.py <prompt_file> [followup_message]")
        sys.exit(1)
    
    prompt_file = sys.argv[1]
    
    with open(prompt_file, 'r') as f:
        initial_prompt = f.read()
    
    if len(sys.argv) > 2:
        # Follow-up mode: load conversation history and send new message
        history_file = sys.argv[2]
        followup_msg = sys.argv[3] if len(sys.argv) > 3 else None
        
        if os.path.exists(history_file):
            with open(history_file, 'r') as f:
                global conversation_history
                conversation_history = json.load(f)
        
        if followup_msg:
            reply = call_gemini(followup_msg)
        else:
            reply = call_gemini(initial_prompt)
    else:
        # Initial prompt mode
        reply = call_gemini(initial_prompt)
    
    # Save conversation history
    history_path = os.path.join(os.path.dirname(prompt_file), "conversation_history.json")
    with open(history_path, 'w') as f:
        json.dump(conversation_history, f, indent=2)
    
    print("=" * 80)
    print("ARCHITECT AGENT RESPONSE")
    print("=" * 80)
    print(reply)
    print("=" * 80)
    print(f"\nConversation history saved to: {history_path}")

if __name__ == "__main__":
    main()
