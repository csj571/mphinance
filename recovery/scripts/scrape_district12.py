#!/usr/bin/env python3
"""
scrape_district12.py
--------------------
Automated scraper for District 12 AA meetings.
Fetches data from aamilwaukee.com and updates docs/district12.html.
"""

import requests
from bs4 import BeautifulSoup
import re
import os
import json
import urllib.parse
from datetime import datetime

# --- CONFIGURATION ---
SOURCE_URL = "https://www.aamilwaukee.com/index.php?page=meeting-directory"
# Absolute path resolution
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET_FILE = os.path.join(BASE_DIR, "docs/district12.html")

# Try to find the blog log file relative to BASE_DIR or repo root
REPRO_ROOT = os.path.dirname(BASE_DIR)
LOG_FILE = os.path.join(REPRO_ROOT, "landing/blog/blog_entries.json")

# Mapping from raw code text to UI slugs
CODE_MAP = {
    "handicap access": "handicap",
    "ladies/women": "womens",
    "men's": "mens",
    "ns": "ns",
    "non-smoking": "ns",
    "beginner's class": "beginner",
    "online meeting available": "online",
    "weekly/monthly open meeting": "open",
}

def fetch_meetings():
    """Fetches meeting data from the Milwaukee AA site for District 12."""
    payload = {
        "district": "12",
        "submit": "Search"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Referer": "https://www.aamilwaukee.com/index.php?page=meeting-directory"
    }
    
    print(f"📡 Fetching District 12 from {SOURCE_URL}...")
    try:
        response = requests.post(SOURCE_URL, data=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        return None

def parse_meetings(html_content):
    """Parses the table-based HTML from aamilwaukee.com into structured meeting objects."""
    soup = BeautifulSoup(html_content, 'html.parser')
    meetings = []
    
    # Each meeting is wrapped in a <table> with border="0"
    tables = soup.find_all('table', border="0")
    print(f"🧐 Found {len(tables)} meeting tables.")
    
    for table in tables:
        try:
            meeting = {
                "name": "",
                "day": "",
                "time": "",
                "codes": [],
                "notes": "",
                "address_lines": [],
                "google_maps_link": "",
                "additional_info": ""
            }
            
            rows = table.find_all('tr')
            if not rows:
                continue
                
            # Main row contains core info
            main_row = rows[0]
            tds = main_row.find_all('td')
            if len(tds) < 3:
                continue
                
            # Left TD: Name, Day, Time, Codes, Notes
            left_td = tds[0]
            name_span = left_td.find('span', style=lambda s: s and 'font-size: 25px' in s)
            if name_span:
                meeting["name"] = name_span.get_text(strip=True)
            
            day_time_span = left_td.find('span', style=lambda s: s and 'font-weight: bolder' in s)
            if day_time_span:
                dt_text = day_time_span.get_text(strip=True)
                if " - " in dt_text:
                    meeting["day"], meeting["time"] = dt_text.split(" - ", 1)
                else:
                    meeting["day"] = dt_text
            
            # Codes and Notes extraction
            for br in left_td.find_all('br'):
                next_node = br.next_sibling
                if next_node and isinstance(next_node, str):
                    text = next_node.strip()
                    if text.startswith("Codes:"):
                        meeting["codes"] = [c.strip() for c in text.replace("Codes:", "").split(",")]
                    elif text.startswith("Notes:"):
                        meeting["notes"] = text.replace("Notes:", "").strip()

            # Right TD: Location and Address
            right_td = tds[2]
            # Find the strong "Location:" tag
            location_tag = right_td.find('strong', string=re.compile("Location:"))
            if location_tag:
                # Iterate siblings after "Location:" until a link or end
                curr = location_tag.next_sibling
                while curr:
                    if curr.name == 'a':
                        break
                    if isinstance(curr, str):
                        part = curr.strip()
                        if part and not part.startswith("District") and not part.startswith("Group") and not part.startswith("County"):
                            meeting["address_lines"].append(part)
                    curr = curr.next_sibling
            
            map_link = right_td.find('a', href=re.compile("maps.google.com"))
            if map_link:
                meeting["google_maps_link"] = map_link['href']

            # Check for second row (Additional Info)
            if len(rows) > 1:
                info_td = rows[1].find('td', colspan="3")
                if info_td:
                    meeting["additional_info"] = info_td.get_text(" ", strip=True).replace("Additional Meeting Information:", "").strip()

            if meeting["name"]:
                meetings.append(meeting)
                
        except Exception as e:
            print(f"⚠️ Error parsing a meeting table: {e}")
            continue
            
    return meetings

def generate_html_card(m):
    """Generates a glassmorphic HTML card for the meeting."""
    day_slug = m['day'].lower()
    
    # Map codes to tags
    tags = []
    text_for_tagging = (m['name'] + " " + m['notes'] + " " + m['additional_info']).lower()
    
    for code in m['codes']:
        slug = CODE_MAP.get(code.lower())
        if slug: tags.append(slug)
    
    if "women" in text_for_tagging and "womens" not in tags: tags.append("womens")
    if "men" in text_for_tagging and "mens" not in tags: tags.append("mens")
    if "handicap" in text_for_tagging and "handicap" not in tags: tags.append("handicap")
    if ("open" in text_for_tagging or "weekly/monthly open" in text_for_tagging) and "open" not in tags:
        tags.append("open")
    else:
        if "closed" not in tags and "open" not in tags:
            tags.append("closed")
    
    type_attr = ",".join(list(set(tags))) # Comma-separated for JS filter
    search_text = f"{m['name']} {m['day']} {m['time']} {' '.join(m['address_lines'])} {m['notes']} {m['additional_info']}".lower()
    
    # Format tags for display
    tag_html = ""
    for tag in tags:
        label = tag.capitalize()
        if tag == 'mens': label = "Men's"
        if tag == 'womens': label = "Women's"
        tag_html += f'<span class="tag">{label}</span>'

    # Build address HTML
    address_html = "<br>".join(m['address_lines'])
    
    # Build Google Maps search URL if link is missing or generic
    if not m['google_maps_link'] or "maps.google.com" not in m['google_maps_link']:
        query = " ".join(m['address_lines'])
        m['google_maps_link'] = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(query)}"

    card = f"""
            <div class="meeting-card" data-day="{day_slug}" data-types="{type_attr}" data-search="{search_text}">
                <div class="time-badge">{m['time']}</div>
                <h3 class="meeting-name">{m['name']}</h3>
                <div class="meeting-day">{m['day']}</div>
                <div class="info-group">
                    <span class="info-label">Location</span>
                    <div class="location"><a href="{m['google_maps_link']}" target="_blank">{address_html}</a></div>
                </div>
                {"<div class='notes'><span class='info-label'>Notes</span>" + m['notes'] + "</div>" if m['notes'] else ""}
                {"<div class='additional-info'><span class='info-label'>Additional Info</span>" + m['additional_info'] + "</div>" if m['additional_info'] else ""}
                <div class="codes" style="margin-top: 1rem; background: transparent; padding: 0; border: none;">
                    {tag_html}
                </div>
            </div>"""
    return card

def update_directory(html_content):
    """Injects the new meeting cards into the target HTML file."""
    if not os.path.exists(TARGET_FILE):
        print(f"❌ Error: Target file {TARGET_FILE} not found!")
        return False
        
    with open(TARGET_FILE, 'r', encoding='utf-8') as f:
        full_html = f.read()
        
    start_marker = "<!-- MEETINGS START -->"
    end_marker = "<!-- MEETINGS END -->"
    
    if start_marker not in full_html or end_marker not in full_html:
        print("❌ Error: Markers not found in HTML!")
        return False
        
    # Using regex to replace content between markers
    pattern = re.compile(f"{re.escape(start_marker)}.*?{re.escape(end_marker)}", re.DOTALL)
    replacement = f"{start_marker}\n{html_content}\n            {end_marker}"
    
    updated_html = pattern.sub(replacement, full_html)
    
    with open(TARGET_FILE, 'w', encoding='utf-8') as f:
        f.write(updated_html)
    
    return True

def log_to_blog(count):
    """Adds a sarcastic Sam-style entry to the blog log."""
    if not os.path.exists(LOG_FILE):
        print(f"📝 Blog file {LOG_FILE} not found, skipping log.")
        return
        
    try:
        with open(LOG_FILE, 'r') as f:
            entries = json.load(f)
            
        new_entry = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "ghost_log": f"Ghost in the machine just refreshed the District 12 directory. Found {count} meetings. Michael finally stopped manually typing addresses like it's 1998. <br>The pipeline is live and breathing. Go drink some water.",
            "suggestions": [
                "Add a 'Share' button to meeting cards",
                "Integrate local weather for outdoor meetings",
                "Stop poking the scraper if it works."
            ],
            "commits": 1,
            "files_changed": 1,
            "chart_ticker": "AA"
        }
        
        entries.insert(0, new_entry)
        
        with open(LOG_FILE, 'w') as f:
            json.dump(entries, f, indent=2)
        print("📝 Logged session to blog.")
    except Exception as e:
        print(f"❌ Failed to log to blog: {e}")

def main():
    print("🚀 Starting District 12 Automation...")
    raw_html = fetch_meetings()
    if not raw_html:
        print("❌ No content fetched. Exiting.")
        return
        
    meetings = parse_meetings(raw_html)
    print(f"📋 Parsed {len(meetings)} meetings.")
    
    if not meetings:
        print("❌ No meetings found. Check parsing logic or site structure.")
        return
        
    # Build the final injection string
    cards_html = ""
    for m in meetings:
        cards_html += generate_html_card(m)
        
    if update_directory(cards_html):
        print(f"✅ Successfully updated {TARGET_FILE}")
        log_to_blog(len(meetings))
    else:
        print("❌ Failed to update directory.")

if __name__ == "__main__":
    main()
