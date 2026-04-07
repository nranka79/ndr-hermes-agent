# -*- coding: utf-8 -*-
"""
Workspace Power CLI Verification
Downloads Aadhaar from Drive and fetches Tasks to verify full 'Power User' access.
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

    creds = Credentials.from_authorized_user_file(TOKEN_PATH)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    # 1. TEST DRIVE ACCESS (Download Aadhar)
    print("--- TESTING DRIVE ACCESS ---")
    drive_service = build('drive', 'v3', credentials=creds)
    file_id = "1M7JkY7Sx5JpZsx4Di14iPywV0GIrqdLW"
    local_filename = "NDR_Aadhar_PowerVerif.pdf"
    
    try:
        url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
        print(f"Downloading Aadhaar (ID: {file_id})...")
        r = requests.get(url, headers={"Authorization": f"Bearer {creds.token}"}, stream=True)
        if r.status_code == 200:
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024*64):
                    f.write(chunk)
            print(f"SUCCESS: Aadhaar downloaded to {local_filename}")
        else:
            print(f"FAILED: Drive download failed with status {r.status_code}")
    except Exception as e:
        print(f"ERROR: Drive test failed: {e}")

    # 2. TEST TASKS ACCESS
    print("\n--- TESTING TASKS ACCESS ---")
    try:
        tasks_service = build('tasks', 'v1', credentials=creds)
        task_lists = tasks_service.tasklists().list().execute()
        lists = task_lists.get('items', [])
        if lists:
            print(f"SUCCESS: Found {len(lists)} task list(s).")
            # List tasks from the first list
            first_list_id = lists[0]['id']
            print(f"Fetching tasks from list: {lists[0]['title']}...")
            tasks_result = tasks_service.tasks().list(tasklist=first_list_id, maxResults=5).execute()
            tasks = tasks_result.get('items', [])
            for t in tasks:
                print(f"  - {t['title']}")
        else:
            print("INFO: No task lists found.")
    except Exception as e:
        print(f"ERROR: Tasks test failed: {e}")

    # 3. TEST CALENDAR ACCESS (Quick check)
    print("\n--- TESTING CALENDAR ACCESS ---")
    try:
        cal_service = build('calendar', 'v3', credentials=creds)
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        events_result = cal_service.events().list(calendarId='primary', timeMin=now, maxResults=3, singleEvents=True, orderBy='startTime').execute()
        events = events_result.get('items', [])
        if events:
            print(f"SUCCESS: Found upcoming events.")
            for e in events:
                print(f"  - {e['summary']}")
        else:
            print("INFO: No upcoming events.")
    except Exception as e:
        print(f"ERROR: Calendar test failed: {e}")

if __name__ == '__main__':
    main()
