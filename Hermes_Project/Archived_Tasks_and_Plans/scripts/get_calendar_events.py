# -*- coding: utf-8 -*-
"""
Google Calendar Event Fetcher
Fetches calendar events for the specified week using the Google Calendar API.
"""

import os
import sys
import io
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Force UTF-8 output on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# If modifying these scopes, delete the file calendar_token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
TOKEN_PATH = r"C:\Users\ruhaan\AntiGravity\calendar_token.json"
CREDS_PATH = r"C:\Users\ruhaan\AntiGravity\gmail_credentials.json"

def get_calendar_service():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDS_PATH):
                print(f"ERROR: Credentials file not found at {CREDS_PATH}")
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())

    return build('calendar', 'v3', credentials=creds)

def main():
    try:
        service = get_calendar_service()

        # Define the week: March 15 to March 21, 2026
        # Using ISO format with Z for UTC (or you can specify offset)
        time_min = '2026-03-15T00:00:00Z'
        time_max = '2026-03-21T23:59:59Z'

        print(f"Fetching events between {time_min} and {time_max}...")
        
        events_result = service.events().list(
            calendarId='primary', 
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])

        if not events:
            print('No upcoming events found for this week.')
            return

        print("\n" + "="*60)
        print(f"{'DATE':<15} | {'TIME':<15} | {'EVENT'}")
        print("-" * 60)

        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            
            # Formatting start time
            if 'T' in start:
                dt = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
                date_str = dt.strftime('%Y-%m-%d')
                time_str = dt.strftime('%H:%M')
            else:
                date_str = start
                time_str = "All Day"

            summary = event.get('summary', 'No Title')
            print(f"{date_str:<15} | {time_str:<15} | {summary}")
        
        print("="*60 + "\n")

    except HttpError as error:
        print(f'An error occurred: {error}')

if __name__ == '__main__':
    main()
