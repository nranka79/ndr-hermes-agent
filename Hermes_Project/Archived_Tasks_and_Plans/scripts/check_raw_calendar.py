# -*- coding: utf-8 -*-
import os
import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN_PATH = r"C:\Users\ruhaan\AntiGravity\workspace_power_token.json"

def main():
    creds = Credentials.from_authorized_user_file(TOKEN_PATH)
    service = build('calendar', 'v3', credentials=creds)

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

        for e in events:
            summary = e.get('summary', 'No Title')
            start = e['start'].get('dateTime', e['start'].get('date'))
            print(f"RAW_EVENT: {start} | {summary}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()
