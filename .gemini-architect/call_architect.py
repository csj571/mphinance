#!/usr/bin/env python3
"""
Architect Agent — Gemini API conversation handler.
Sends prompts to Gemini and captures structured responses.
Includes retry logic with exponential backoff.
"""
import json
import sys
import os
import time
import urllib.request
import urllib.error


def call_gemini_rest(prompt, api_key, model="gemini-2.0-flash", max_retries=5):
    """Call Gemini REST API with retry logic."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 8192,
        }
    }
    data_bytes = json.dumps(payload).encode()

    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(
                url,
                data=data_bytes,
                headers={"Content-Type": "application/json"},
            )
            resp = urllib.request.urlopen(req, timeout=180)
            data = json.loads(resp.read())

            # Extract text from response — handle multiple parts (thinking models)
            try:
                parts = data["candidates"][0]["content"]["parts"]
                text_parts = []
                for part in parts:
                    if "text" in part:
                        text_parts.append(part["text"])
                if text_parts:
                    return "\n".join(text_parts)
                return f"WARN: No text in parts. Raw: {json.dumps(data, indent=2)[:2000]}"
            except (KeyError, IndexError) as e:
                return f"ERROR: {e}\nRaw: {json.dumps(data, indent=2)[:2000]}"

        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 2 ** (attempt + 2)  # 4, 8, 16, 32, 64 seconds
                print(f"  ⏳ Rate limited. Retrying in {wait}s... (attempt {attempt+1}/{max_retries})")
                time.sleep(wait)
            else:
                body = e.read().decode() if e.fp else ""
                return f"HTTP Error {e.code}: {e.reason}\n{body[:500]}"
        except Exception as e:
            return f"ERROR: {e}"

    return "ERROR: Max retries exceeded (rate limited)"


def main():
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        print("ERROR: GEMINI_API_KEY not set")
        sys.exit(1)

    model = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")

    prompt_file = sys.argv[1] if len(sys.argv) > 1 else None
    if prompt_file:
        with open(prompt_file) as f:
            prompt = f.read()
    else:
        prompt = sys.stdin.read()

    print(f"🤖 Architect Agent (Gemini {model}) responding...\n")
    response = call_gemini_rest(prompt, api_key, model)
    print(response)

    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(out_dir, "architect_response.md")
    with open(out_path, "w") as f:
        f.write(response)
    print(f"\n💾 Response saved to {out_path}")


if __name__ == "__main__":
    main()
