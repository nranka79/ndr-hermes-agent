# -*- coding: utf-8 -*-
"""
Workspace CLI Power Setup
One-time setup to authorize all Workspace APIs for the 'ndr@draas.com' CLI.
"""

import os
import sys
import io
from google_auth_oauthlib.flow import InstalledAppFlow

# Force UTF-8 output
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# COMPREHENSIVE POWER USER SCOPES
SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',      # GMAIL: Read/Write/Internal management
    'https://www.googleapis.com/auth/calendar',         # CALENDAR: Full schedule management
    'https://www.googleapis.com/auth/drive',            # DRIVE: Full file management (Download/Upload)
    'https://www.googleapis.com/auth/tasks',            # TASKS: Full task management
    'https://www.googleapis.com/auth/spreadsheets',     # SHEETS: Automated data entry
    'https://www.googleapis.com/auth/documents',        # DOCS: High-quality document drafting
    'https://www.googleapis.com/auth/contacts.readonly', # CONTACTS: Search for driver/staff numbers
    'https://www.googleapis.com/auth/admin.directory.user.readonly' # ADMIN: User/Org info
]

TOKEN_PATH = r"C:\Users\ruhaan\AntiGravity\workspace_power_token.json"
CREDS_PATH = r"C:\Users\ruhaan\AntiGravity\gmail_credentials.json"

def main():
    if not os.path.exists(CREDS_PATH):
        print(f"CRITICAL ERROR: Credentials file not found at {CREDS_PATH}")
        return

    print("\n" + "!"*60)
    print("INITIALIZING WORKSPACE POWER CLI SETUP")
    print("!"*60)
    print("This will authorize Gmail, Calendar, Drive, Tasks, Sheets, and Docs.")
    print("\n1. A browser tab will open.")
    print("2. Approve the permissions for ndr@draas.com.")
    print("3. When you reach the failed 'localhost' page, COPY THE URL.")
    print("4. Paste the full URL here below.")
    print("!"*60 + "\n")

    try:
        flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
        # Using a port that is unlikely to be blocked
        creds = flow.run_local_server(port=0, prompt='consent')
        
        with open(TOKEN_PATH, 'w', encoding='utf-8') as token:
            token.write(creds.to_json())
            
        print("\n" + "="*60)
        print("SUCCESS! WORKSPACE POWER TOKEN GENERATED.")
        print(f"Saved to: {TOKEN_PATH}")
        print("You can now use all Power User Recipes.")
        print("="*60)

    except Exception as e:
        print(f"\nSetup encountered an error: {e}")

if __name__ == '__main__':
    main()
