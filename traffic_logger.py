#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  traffic_logger.py
#  
#  Copyright 2026 Squirrel <squirrel@squirrels-darter>
#  
#  Upgraded by Sam the Quant Ghost 👻 — swapped OpenWeatherMap for wttr.in
#  No API key needed. No signup. No account. Just works.
#



from flask import Flask, request, jsonify
import csv
import datetime
import requests
import os

app = Flask(__name__)

# --- CONFIGURATION ---
ZIP_CODE = "82601" 
# ✅ NO API KEY NEEDED — wttr.in is 100% free, no account required
CSV_FILENAME = "foot_traffic_log.csv"

# --- WEATHER CACHING ---
# Cache weather to avoid hammering the API.
cached_weather = {"temp": "Unknown", "condition": "Unknown", "timestamp": None}
CACHE_DURATION_SECONDS = 600 # 10 minutes

def get_current_weather():
    global cached_weather
    now = datetime.datetime.now()
    
    # Checks for valid cached weather
    if cached_weather["timestamp"]:
        time_diff = (now - cached_weather["timestamp"]).total_seconds()
        if time_diff < CACHE_DURATION_SECONDS:
            return cached_weather["temp"], cached_weather["condition"]

    # Fetch from wttr.in — FREE, no API key, no signup!
    try:
        # wttr.in accepts zip codes and returns JSON
        url = f"https://wttr.in/{ZIP_CODE}?format=j1"
        response = requests.get(url, timeout=10, headers={"User-Agent": "traffic-logger/1.0"})
        data = response.json()
        
        current = data["current_condition"][0]
        temp = float(current["temp_F"])
        condition = current["weatherDesc"][0]["value"]  # e.g., "Sunny", "Light rain"
        
        # Update Cache
        cached_weather["temp"] = temp
        cached_weather["condition"] = condition
        cached_weather["timestamp"] = now
        
        return temp, condition
    except Exception as e:
        print(f"Weather API error: {e}")
        return "Error", "Error"

def initialize_csv():
    # Create the CSV with headers if it doesn't exist
    if not os.path.isfile(CSV_FILENAME):
        with open(CSV_FILENAME, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Timestamp", "Day_of_Week", "Camera_Source", "Event_Type", "Direction", "Temperature_F", "Weather_Condition"])

@app.route('/unifi_webhook', methods=['POST'])
def handle_webhook():
    # 1. Capture the exact time
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    day_of_week = now.strftime("%A")
    
    # 2. Parse the UniFi Webhook Data
    data = request.json
    

    camera_source = data.get("cameraName", data.get("source", "Unknown_Camera"))
    event_type = data.get("message", "Line_Crossing_Event")
    
    # Determine Entrance vs Exit based on UniFi Alarm name
    direction = "Unknown"
    if "enter" in event_type.lower() or "inbound" in event_type.lower():
        direction = "Entrance"
    elif "exit" in event_type.lower() or "outbound" in event_type.lower():
        direction = "Exit"

    # 3. Get Weather
    temp, condition = get_current_weather()

    # 4. Log to CSV
    with open(CSV_FILENAME, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, day_of_week, camera_source, event_type, direction, temp, condition])

    print(f"Logged: {timestamp} | {day_of_week} | {direction} | {temp}°F, {condition}")
    
    return jsonify({"status": "success"}), 200

if __name__ == '__main__':
    initialize_csv()
    # The server runs locally on port 5000
    app.run(host='0.0.0.0', port=5000)
