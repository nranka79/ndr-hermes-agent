# -*- coding: utf-8 -*-
"""
Filtered Calendar Week View
Filters out Workouts, Health Tasks, and Kids' events to show only work/other meetings.
"""

import os
import sys
import io
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Force UTF-8 output
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

TOKEN_PATH = r"C:\Users\ruhaan\AntiGravity\workspace_power_token.json"

def main():
    if not os.path.exists(TOKEN_PATH):
        print("ERROR: Power Token not found.")
        return

    creds = Credentials.from_authorized_user_file(TOKEN_PATH)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    service = build('calendar', 'v3', credentials=creds)

    # Week of March 15 - 21, 2026
    time_min = '2026-03-15T00:00:00Z'
    time_max = '2026-03-21T23:59:59Z'

    try:
        events_result = service.events().list(
            calendarId='primary', 
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])

        if not events:
            print('No events found for this week.')
            return

        print("\n" + "="*80)
        print(f"{'DATE':<15} | {'TIME':<15} | {'EVENT'}")
        print("-" * 80)

        found_work_events = False
        for event in events:
            summary = event.get('summary', 'No Title').lower()
            
            # FILTERS:
            # 1. Ignore "Workout"
            if "workout" in summary: continue
            # 2. Ignore Kids' events (Ruhaan & Rivaan)
            if "ruhaan & rivaan" in summary: continue
            if "kids" in event.get('organizer', {}).get('displayName', '').lower(): continue
            # 3. Ignore Daily Health Tasks (Fortacort, Metformin, Flowmist)
            if any(med in summary for med in ["fortacort", "metformin", "rosavel", "flowmist"]): continue
            
            # Format and display
            start = event['start'].get('dateTime', event['start'].get('date'))
            if 'T' in start:
                dt = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
                date_str = dt.strftime('%a, %b %d')
                time_str = dt.strftime('%I:%M %p')
            else:
                date_str = start
                time_str = "All Day"

            print(f"{date_str:<15} | {time_str:<15} | {event.get('summary')}")
            found_work_events = True
        
        if not found_work_events:
            print("No business or work-related meetings found after filtering.")
        
        print("="*80 + "\n")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    main()
