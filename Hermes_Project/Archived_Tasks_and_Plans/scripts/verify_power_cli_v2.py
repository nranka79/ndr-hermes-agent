# -*- coding: utf-8 -*-
"""
Workspace Power CLI Detailed Verification
Checks scopes and tries basic list operations on all enabled services.
"""

import os
import sys
import io
import json
import requests
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

    with open(TOKEN_PATH, 'r') as f:
        token_data = json.load(f)
        print(f"Token Scopes: {token_data.get('scopes')}")

    creds = Credentials.from_authorized_user_file(TOKEN_PATH)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    
    token = creds.token

    # 1. TEST DRIVE
    print("\n--- TEST: DRIVE ---")
    try:
        drive = build('drive', 'v3', credentials=creds)
        # Try listing first 5 files
        results = drive.files().list(pageSize=5, fields="files(id, name)").execute()
        files = results.get('files', [])
        print(f"SUCCESS: Found {len(files)} files in Drive.")
        for f in files:
            print(f"  - {f['name']} ({f['id']})")
        
        # Try specific aadhar
        file_id = "1M7JkY7Sx5JpZsx4Di14iPywV0GIrqdLW"
        print(f"Attempting meta-data fetch for Aadhaar ID: {file_id}")
        meta = drive.files().get(fileId=file_id, fields="id, name, mimeType").execute()
        print(f"  Found Meta: {meta['name']} | {meta['mimeType']}")
    except Exception as e:
        print(f"ERROR: Drive test failed: {e}")

    # 2. TEST TASKS
    print("\n--- TEST: TASKS ---")
    try:
        tasks = build('tasks', 'v1', credentials=creds)
        lists = tasks.tasklists().list().execute().get('items', [])
        print(f"SUCCESS: Found {len(lists)} task lists.")
        for l in lists:
            print(f"  - {l['title']}")
    except Exception as e:
        print(f"ERROR: Tasks test failed: {e}")

    # 3. TEST CALENDAR
    print("\n--- TEST: CALENDAR ---")
    try:
        cal = build('calendar', 'v3', credentials=creds)
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        events = cal.events().list(calendarId='primary', timeMin=now, maxResults=3).execute().get('items', [])
        print(f"SUCCESS: Found {len(events)} upcoming events.")
    except Exception as e:
        print(f"ERROR: Calendar test failed: {e}")

    # 4. TEST SHEETS
    print("\n--- TEST: SHEETS ---")
    try:
        sheets = build('sheets', 'v4', credentials=creds)
        # Just a discovery call
        print("SUCCESS: Sheets service initialized.")
    except Exception as e:
        print(f"ERROR: Sheets test failed: {e}")

if __name__ == '__main__':
    main()
