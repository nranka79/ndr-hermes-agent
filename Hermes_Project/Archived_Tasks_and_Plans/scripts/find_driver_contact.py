# -*- coding: utf-8 -*-
"""
Google Contacts Searcher
Searches for 'Shyam' or 'Sham' to find the driver's phone number.
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

    service = build('people', 'v1', credentials=creds)

    print("Searching contacts for 'Shyam' or 'Sham'...")
    try:
        # Searching across all connections
        results = service.people().connections().list(
            resourceName='people/me',
            personFields='names,phoneNumbers',
            pageSize=100
        ).execute()
        
        connections = results.get('connections', [])
        found = False
        for person in connections:
            names = person.get('names', [])
            full_names = [n.get('displayName', '').lower() for n in names]
            
            if any("shyam" in name or "sham" in name for name in full_names):
                phones = person.get('phoneNumbers', [])
                if phones:
                    print(f"FOUND: {full_names[0]} | Phone: {phones[0].get('value')}")
                    found = True
        
        if not found:
            print("No contact found with 'Shyam' or 'Sham'.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    main()
