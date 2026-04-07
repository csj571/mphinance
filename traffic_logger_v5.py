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
#  Scrambled by a nutty Squirrel 
#
#



from flask import Flask, request, jsonify
import csv
import datetime
import requests
import os

app = Flask(__name__)

# --- CONFIGURATION ---
ZIP_CODE = "82601" 
CSV_FILENAME = "foot_traffic_log.csv"

# --- IN-MEMORY TRACKING ---
# Stores { "object_id": datetime_object }
active_sessions = {}

# --- WEATHER CACHING ---
cached_weather = {"temp": "Unknown", "condition": "Unknown", "timestamp": None}
CACHE_DURATION_SECONDS = 600 # 10 minutes

def get_current_weather():
    global cached_weather
    now = datetime.datetime.now()
    
    if cached_weather["timestamp"]:
        time_diff = (now - cached_weather["timestamp"]).total_seconds()
        if time_diff < CACHE_DURATION_SECONDS:
            return cached_weather["temp"], cached_weather["condition"]

    try:
        # Fetch from wttr.in — FREE, no API key required
        url = f"https://wttr.in/{ZIP_CODE}?format=j1"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        current = data['current_condition'][0]
        temp = current['temp_F']
        condition = current['weatherDesc'][0]['value']
        
        cached_weather["temp"] = temp
        cached_weather["condition"] = condition
        cached_weather["timestamp"] = now
        
        return temp, condition
    except Exception as e:
        print(f"Weather Fetch Error: {e}")
        return "Error", "Error"

def initialize_csv():
    if not os.path.isfile(CSV_FILENAME):
        with open(CSV_FILENAME, mode='w', newline='') as file:
            writer = csv.writer(file)
            # Session_ID and Duration_Minutes added
            writer.writerow(["Timestamp", "Day", "Session_ID", "Camera", "Direction", "Duration_Min", "Temp_F", "Weather"])

@app.route('/unifi_webhook', methods=['POST'])
def handle_webhook():
    now = datetime.datetime.now()
    data = request.json
    
    # --- UNIFI PARSING Parsing ---
    alarm_data = data.get("alarm", {})
    alarm_name = alarm_data.get("name", "General_Alert")
    
    # Extract unique ID for matching (provided by UniFi AI/G6 cameras)
    # This is usually nested inside 'triggers' or the main payload
    session_id = data.get("objectId", data.get("detectionId", "Unknown"))
    
    triggers = alarm_data.get("triggers", [])
    camera_source = "Unknown_Camera"
    if triggers:
        camera_source = triggers[0].get("key", triggers[0].get("device", "Unknown_Camera"))

    # Determine Direction
    direction = "Unknown"
    lower_alarm = alarm_name.lower()
    if any(word in lower_alarm for word in ["enter", "inbound", "entry"]):
        direction = "Entrance"
    elif any(word in lower_alarm for word in ["exit", "outbound"]):
        direction = "Exit"

    # --- DURATION LOGIC ---
    duration = ""
    if direction == "Entrance" and session_id != "Unknown":
        active_sessions[session_id] = now
    
    elif direction == "Exit" and session_id != "Unknown":
        if session_id in active_sessions:
            entry_time = active_sessions.pop(session_id)
            delta = now - entry_time
            duration = round(delta.total_seconds() / 60, 2) # Minutes
        else:
            duration = "No Entry Match"

    # Get Weather
    temp, condition = get_current_weather()

    # Log to CSV
    with open(CSV_FILENAME, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            now.strftime("%Y-%m-%d %H:%M:%S"),
            now.strftime("%A"),
            session_id,
            camera_source,
            direction,
            duration,
            temp,
            condition
        ])

    print(f"Logged {direction}: ID {session_id} | {duration} min | {temp}F")
    
    return jsonify({"status": "success"}), 200

if __name__ == '__main__':
    initialize_csv()
    print(f"Server starting on port 5000...")
    app.run(host='0.0.0.0', port=5000)
