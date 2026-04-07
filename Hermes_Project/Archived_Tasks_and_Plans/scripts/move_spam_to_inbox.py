# -*- coding: utf-8 -*-
"""
Move all emails from Spam to Inbox.
"""
import sys, io, os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Using gmail.modify to allow moving messages between labels
SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
TOKEN_PATH = r"C:\Users\ruhaan\AntiGravity\gmail_token_modify.json"
CREDS_PATH = r"C:\Users\ruhaan\AntiGravity\gmail_credentials.json"

def get_service():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w", encoding="utf-8") as fh:
            fh.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)

def main():
    service = get_service()
    
    print("Searching for messages in Spam...")
    # Get all messages in SPAM
    results = service.users().messages().list(userId='me', labelIds=['SPAM']).execute()
    messages = results.get('messages', [])
    
    if not messages:
        print("No messages found in Spam.")
        return

    print(f"Found {len(messages)} messages in Spam. Moving to Inbox...")
    
    # We can use batchModify to do this efficiently
    msg_ids = [m['id'] for m in messages]
    
    batch_request = {
        'ids': msg_ids,
        'addLabelIds': ['INBOX'],
        'removeLabelIds': ['SPAM']
    }
    
    try:
        service.users().messages().batchModify(userId='me', body=batch_request).execute()
        print(f"Successfully moved {len(messages)} messages from Spam to Inbox!")
    except Exception as e:
        print(f"Error moving messages: {e}")

if __name__ == "__main__":
    main()
