# -*- coding: utf-8 -*-
"""
Google Calendar Event Creator
Creates a specialized work visit event for March 17, 2026.
"""

import os
import sys
import io
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

    title = "Full Day Visit: Kothur & Property Inspection"
    description = (
        "1. Presentation at Magistrate spoke in relationship to WHPL FIR.\n"
        "2. Meeting with lawyer to understand legal title flow and current blockers with respect to Tal property.\n"
        "3. Visiting Tal property Strr Access and the new NH888 up to Chandapur.\n"
        "4. Visiting Ranka Udaya.\n"
        "5. Visiting Ranka Oasis.\n"
        "6. Visiting Shulagiri property proposed by Prakash for Farm Home development near Embassy Warehouse."
    )

    event = {
        'summary': title,
        'description': description,
        'start': {
            'dateTime': '2026-03-17T07:00:00',
            'timeZone': 'Asia/Kolkata',
        },
        'end': {
            'dateTime': '2026-03-17T19:00:00',
            'timeZone': 'Asia/Kolkata',
        },
        'reminders': {
            'useDefault': True,
        },
    }

    try:
        event_result = service.events().insert(calendarId='primary', body=event).execute()
        print(f"SUCCESS: Event created.")
        print(f"EVENT_ID: {event_result.get('id')}")
        print(f"HTML_LINK: {event_result.get('htmlLink')}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    main()
