#!/usr/bin/env python3
"""
substack_sid_refresh.py — Keep Substack SID alive using Playwright.

Loads the Substack dashboard with the current SID cookie, which refreshes
the session server-side. Then grabs the updated cookie and saves it back.

Run periodically (cron every few days) to prevent SID expiration.

Usage:
  python3 substack_sid_refresh.py           # Refresh and save
  python3 substack_sid_refresh.py --check   # Just check if current SID works

Requires: pip install playwright && playwright install chromium
"""
import os, sys, re

def load_secrets():
    secrets = {}
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "secrets.env")
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                secrets[k] = v.strip('"')
    return secrets, env_path

def save_sid(env_path, new_sid):
    """Update SUBSTACK_SID in secrets.env."""
    with open(env_path) as f:
        content = f.read()
    if 'SUBSTACK_SID=' in content:
        content = re.sub(r'SUBSTACK_SID=.*', f'SUBSTACK_SID={new_sid}', content)
    else:
        content += f'\nSUBSTACK_SID={new_sid}\n'
    with open(env_path, 'w') as f:
        f.write(content)

def main():
    from playwright.sync_api import sync_playwright

    secrets, env_path = load_secrets()
    old_sid = secrets.get('SUBSTACK_SID', '')
    pub = secrets.get('SUBSTACK_PUB_URL', 'mphinance.substack.com')

    if not old_sid:
        print("❌ No SUBSTACK_SID found in secrets.env")
        return

    print(f"🔑 Current SID: {old_sid[:30]}...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()

        # Set the existing SID cookie
        context.add_cookies([{
            "name": "substack.sid",
            "value": old_sid,
            "domain": ".substack.com",
            "path": "/",
            "httpOnly": True,
            "secure": True,
            "sameSite": "Lax",
        }])

        page = context.new_page()
        print(f"🌐 Loading https://{pub}/publish/dashboard...")
        page.goto(f"https://{pub}/publish/dashboard", wait_until="networkidle", timeout=30000)

        # Check if we're logged in
        if "sign-in" in page.url.lower() or "login" in page.url.lower():
            print("❌ SID is expired — redirected to login")
            browser.close()
            return

        print(f"✅ Page loaded: {page.url}")

        # Grab the refreshed cookie
        cookies = context.cookies()
        new_sid = None
        for c in cookies:
            if c["name"] == "substack.sid":
                new_sid = c["value"]
                break

        if new_sid and new_sid != old_sid:
            print(f"🔄 SID refreshed! New: {new_sid[:30]}...")
            if "--check" not in sys.argv:
                save_sid(env_path, new_sid)
                print(f"💾 Saved to {env_path}")
            else:
                print("   (check mode — not saving)")
        elif new_sid:
            print("✅ SID is still valid (unchanged)")
        else:
            print("⚠️ Could not find substack.sid cookie")

        browser.close()

    print("🏁 Done")

if __name__ == "__main__":
    main()
