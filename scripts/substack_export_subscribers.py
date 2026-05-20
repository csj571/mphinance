#!/usr/bin/env python3
"""
substack_export_subscribers.py — Export subscriber list via Playwright.

Substack locks subscriber emails behind dashboard auth — the cookie-based
API doesn't expose them. This script injects your SID cookie into a headless
browser, navigates to the subscriber export page, and downloads the CSV.

Usage:
    export SUBSTACK_SID="s%3A..."
    python3 scripts/substack_export_subscribers.py

    # With visible browser (debug mode):
    python3 scripts/substack_export_subscribers.py --headed

Output:
    ./subscribers_YYYY-MM-DD.csv
"""

import os
import sys
import asyncio
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

from playwright.async_api import async_playwright

SID_RAW = os.environ.get("SUBSTACK_SID", "")
PUB_URL = os.environ.get("SUBSTACK_PUB_URL", "https://mphinance.substack.com")
HEADED = "--headed" in sys.argv
OUTPUT_DIR = Path(__file__).parent.parent  # repo root

DASHBOARD_URL = f"{PUB_URL}/publish/users"
EXPORT_URL    = f"{PUB_URL}/api/v1/subscribers/export"


async def run():
    if not SID_RAW:
        print("❌ SUBSTACK_SID not set. Export it first.")
        sys.exit(1)

    # Decode URL-encoded SID for cookie injection
    sid_decoded = unquote(SID_RAW)

    output_file = OUTPUT_DIR / f"subscribers_{datetime.now().strftime('%Y-%m-%d')}.csv"

    print(f"🚀 Launching {'headed' if HEADED else 'headless'} browser...")
    print(f"   Target: {DASHBOARD_URL}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=not HEADED)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
        )

        # Inject the SID cookie before navigating
        await context.add_cookies([
            {
                "name": "substack.sid",
                "value": sid_decoded,
                "domain": ".substack.com",
                "path": "/",
                "httpOnly": True,
                "secure": True,
                "sameSite": "Lax",
            }
        ])

        page = await context.new_page()

        # ── Method 1: Direct API export (fastest if it works) ──────────────
        print("\n🔑 Trying direct API export...")
        try:
            response = await page.goto(EXPORT_URL, timeout=15000)
            if response and response.status == 200:
                ct = response.headers.get("content-type", "")
                if "csv" in ct or "text/plain" in ct or "octet" in ct:
                    body = await response.body()
                    output_file.write_bytes(body)
                    print(f"✅ Downloaded via API: {output_file}")
                    await browser.close()
                    summarize(output_file)
                    return
                else:
                    print(f"   API returned {ct} (not CSV) — trying dashboard...")
            else:
                print(f"   API returned {response.status if response else 'no response'} — trying dashboard...")
        except Exception as e:
            print(f"   API export blocked ({e.__class__.__name__}) — trying dashboard...")

        # ── Method 2: Dashboard UI click ────────────────────────────────────
        print("\n🖱  Navigating to subscriber dashboard...")
        try:
            await page.goto(DASHBOARD_URL, wait_until="domcontentloaded", timeout=45000)
        except Exception as e:
            print(f"   Note: goto timed out or errored ({e.__class__.__name__}), proceeding anyway...")
        
        await page.wait_for_timeout(5000)  # let React render the table

        # Check if we're actually logged in
        if "sign-in" in page.url or "login" in page.url:
            print("❌ SID rejected — redirected to login. Refresh your cookie.")
            await browser.close()
            sys.exit(1)

        print(f"   Current URL: {page.url}")

        # ── Step 1: Try the ⋯ overflow menu (top-right of subscriber table) ──
        print("   Looking for ⋯ overflow menu...")
        clicked = False
        try:
            # The kebab/overflow menu button near the top-right
            overflow_btn = page.locator("button[aria-label='More options'], button:has(svg), [aria-haspopup='menu']").last
            # More targeted: the ... button in the header area
            kebab_candidates = page.locator("button").filter(has_text="")
            # Try clicking the last button in the top-right area which is ⋯
            all_buttons = page.locator("header button, [role='toolbar'] button, .subscriber-list-header button")
            count = await all_buttons.count()
            print(f"   Found {count} header buttons")

            # Try the triple-dot button via its position (top-right area)
            kebab = page.locator("button").last
            for i in range(await page.locator("button").count() - 1, -1, -1):
                btn = page.locator("button").nth(i)
                box = await btn.bounding_box()
                if box and box["x"] > 600 and box["y"] < 250:
                    print(f"   Clicking top-right button at ({box['x']:.0f}, {box['y']:.0f})")
                    await btn.click()
                    await page.wait_for_timeout(1000)
                    # Look for Export in dropdown
                    export_item = page.locator("[role='menuitem']:has-text('Export'), li:has-text('Export'), a:has-text('Export')")
                    if await export_item.count() > 0:
                        print("   Found Export in dropdown!")
                        async with page.expect_download(timeout=20000) as dl_info:
                            await export_item.first.click()
                        download = await dl_info.value
                        await download.save_as(str(output_file))
                        print(f"✅ Downloaded via overflow menu: {output_file}")
                        clicked = True
                        break
                    else:
                        # Close the menu and try next button
                        await page.keyboard.press("Escape")
                        await page.wait_for_timeout(300)
        except Exception as e:
            print(f"   Overflow menu attempt failed: {e}")

        if not clicked:
            # ── Method 3: Scrape emails directly from the page ─────────────
            print("\n📋 Scraping emails directly from loaded subscriber table...")
            emails = []

            # Scroll and collect all visible emails
            prev_count = 0
            for scroll_attempt in range(20):  # max 20 scrolls
                # Extract emails from current view
                new_emails = await page.evaluate("""
                    () => {
                        const emails = [];
                        // Grab all text nodes that look like emails
                        const walker = document.createTreeWalker(
                            document.body, NodeFilter.SHOW_TEXT
                        );
                        let node;
                        while (node = walker.nextNode()) {
                            const txt = node.textContent.trim();
                            if (txt.match(/^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/)) {
                                emails.push(txt);
                            }
                        }
                        return [...new Set(emails)];
                    }
                """)
                for e in new_emails:
                    if e not in emails:
                        emails.append(e)

                # Click "Load more" if present
                load_more = page.locator("button:has-text('Load more'), a:has-text('Load more')")
                if await load_more.count() > 0 and await load_more.first.is_visible():
                    try:
                        await load_more.first.scroll_into_view_if_needed()
                        await load_more.first.click(force=True, timeout=5000)
                        await page.wait_for_timeout(2000)
                    except Exception as e:
                        print(f"   Could not click Load More: {e}")
                        break
                else:
                    break  # No more pages

                if len(emails) == prev_count:
                    break
                prev_count = len(emails)
                print(f"   Collected {len(emails)} emails so far...")

            if emails:
                # Write as CSV
                csv_lines = ["email"]
                csv_lines.extend(emails)
                output_file.write_text("\n".join(csv_lines))
                print(f"✅ Scraped {len(emails)} emails to: {output_file}")
                clicked = True
            else:
                screenshot = OUTPUT_DIR / "substack_dashboard_debug.png"
                await page.screenshot(path=str(screenshot), full_page=True)
                print(f"⚠️  Could not extract emails.")
                print(f"   Screenshot saved: {screenshot}")
                await browser.close()
                sys.exit(1)

        await browser.close()
        summarize(output_file)


def summarize(path: Path):
    """Print a quick summary of the downloaded CSV."""
    try:
        lines = path.read_text().splitlines()
        if not lines:
            print("⚠️  CSV is empty.")
            return
        header = lines[0]
        count = len(lines) - 1  # subtract header
        print(f"\n📊 Subscriber Export Summary")
        print(f"   File:    {path}")
        print(f"   Columns: {header}")
        print(f"   Total:   {count} subscribers")
        # Show first 3 rows
        if count > 0:
            print(f"\n   Sample (first 3 rows):")
            for row in lines[1:4]:
                print(f"   {row}")
    except Exception as e:
        print(f"⚠️  Could not parse CSV: {e}")


if __name__ == "__main__":
    asyncio.run(run())
