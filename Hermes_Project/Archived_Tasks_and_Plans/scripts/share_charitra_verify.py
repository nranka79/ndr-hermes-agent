# -*- coding: utf-8 -*-
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
    creds = Credentials.from_authorized_user_file(TOKEN_PATH)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    drive_service = build('drive', 'v3', credentials=creds)
    
    folder_id = "1PYWau7jJdkAbMe49a6astOUC3lGRAvCC"
    roshi_email = "rnr@draas.com"
    
    print(f"Sharing folder {folder_id} with {roshi_email}...")
    permission = {
        'type': 'user',
        'role': 'writer',
        'emailAddress': roshi_email
    }
    
    try:
        res = drive_service.permissions().create(fileId=folder_id, body=permission, fields='id').execute()
        folder = drive_service.files().get(fileId=folder_id, fields="name, webViewLink").execute()
        print(f"FOLDER_LINK:{folder['webViewLink']}")
        
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == '__main__':
    main()
