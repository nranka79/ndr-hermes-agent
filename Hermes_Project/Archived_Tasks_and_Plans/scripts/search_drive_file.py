# -*- coding: utf-8 -*-
"""
Google Drive File Searcher
Searches for files in Google Drive by name/pattern.
"""

import os
import sys
import io
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Force UTF-8 output on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# SCOPES for Drive search and download
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
TOKEN_PATH = r"C:\Users\ruhaan\AntiGravity\drive_token.json"
CREDS_PATH = r"C:\Users\ruhaan\AntiGravity\gmail_credentials.json"

def get_drive_service():
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

    return build('drive', 'v3', credentials=creds)

def main():
    try:
        service = get_drive_service()

        query = "name contains 'Aadhar' or name contains 'Aadhar'"
        print(f"Searching for query: {query}")
        
        results = service.files().list(
            q=query,
            pageSize=10,
            fields="nextPageToken, files(id, name, mimeType)"
        ).execute()
        items = results.get('files', [])

        if not items:
            print('No files found.')
            # Broaden search
            print("Broadening search to just 'Aadhar'...")
            results = service.files().list(
                q="name contains 'Aadhar'",
                pageSize=20,
                fields="files(id, name, mimeType)"
            ).execute()
            items = results.get('files', [])

        if not items:
            print('Still no files found.')
        else:
            print(f"Found {len(items)} file(s):")
            for item in items:
                print(f"{item['name']} ({item['id']}) - {item['mimeType']}")

    except HttpError as error:
        print(f'An error occurred: {error}')

if __name__ == '__main__':
    main()
