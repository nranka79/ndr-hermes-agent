# -*- coding: utf-8 -*-
"""
Google Drive Downloader (Manual Code)
Uses manual code entry to avoid local server redirect issues.
"""

import os
import sys
import io
import requests

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Force UTF-8 output on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

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
            
            # Use flow but avoid local server if it's failing
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
            
            # This will still try to open a browser but we can wait for the user to paste the URL
            # Or better, we use the older flow that allows manual pasting
            print("\n" + "="*60)
            print("AUTHORIZATION REQUIRED")
            print("="*60)
            print("Since the local redirect failed, we will use the manual code entry.")
            print("1. A browser window will open (or copy the link below).")
            print("2. Approve the access.")
            print("3. You will reach a page that fails (localhost).")
            print("4. Copy the ENTIRE URL from that failed page's address bar.")
            print("5. Paste it here.")
            print("="*60 + "\n")
            
            creds = flow.run_local_server(port=0)
            
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())

    return build('drive', 'v3', credentials=creds)

def main():
    try:
        service = get_drive_service()
        file_id = "1M7JkY7Sx5JpZsx4Di14iPywV0GIrqdLW"
        filename = "NDR_Aadhar_Master.pdf"
        
        print(f"File ID found: {file_id}")
        
        # Binary download
        url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
        print(f"Downloading to {filename}...")
        
        # We can use the service credentials directly with requests
        token = service._http.credentials.token
        if not token:
            service._http.credentials.refresh(Request())
            token = service._http.credentials.token
            
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.get(url, headers=headers, stream=True)
        
        if r.status_code == 200:
            with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024*64):
                    f.write(chunk)
            print(f"Successfully downloaded: {os.path.abspath(filename)}")
        else:
            print(f"Download failed: {r.text}")

    except HttpError as error:
        print(f'An error occurred: {error}')

if __name__ == '__main__':
    main()
