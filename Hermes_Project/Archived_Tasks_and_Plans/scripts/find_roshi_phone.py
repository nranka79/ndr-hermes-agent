# -*- coding: utf-8 -*-
import os
import sys
import io
import re
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

    service = build('gmail', 'v1', credentials=creds)
    
    query = "from:rnr@draas.com"
    print(f"Searching for emails from: {query}")
    results = service.users().messages().list(userId='me', q=query, maxResults=10).execute()
    messages = results.get('messages', [])
    
    phone_pattern = re.compile(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')
    
    for msg in messages:
        m = service.users().messages().get(userId='me', id=msg['id']).execute()
        snippet = m.get('snippet', '')
        print(f"Snippet: {snippet}")
        phones = phone_pattern.findall(snippet)
        if phones:
            print(f"Probable Phone numbers found in snippet: {phones}")

if __name__ == '__main__':
    main()
