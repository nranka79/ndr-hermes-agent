# -*- coding: utf-8 -*-
"""
Identify unique senders in Spam, add itd_support, and create a Gmail filter to whitelist them.
"""
import sys, io, os, re
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Added settings.basic scope for filters
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.settings.basic"
]
TOKEN_PATH = r"C:\Users\ruhaan\AntiGravity\gmail_token.json"
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

def extract_email(sender_str):
    match = re.search(r'<(.+?)>', sender_str)
    if match:
        return match.group(1).lower().strip()
    return sender_str.lower().strip()

def main():
    service = get_service()
    
    print("Fetching emails from Spam folder...")
    results = service.users().messages().list(userId='me', labelIds=['SPAM']).execute()
    messages = results.get('messages', [])
    
    senders = set()
    senders.add("itd_support@insight.gov.in")
    
    if not messages:
        print("Spam folder is empty (except for IT support).")
    else:
        print(f"Found {len(messages)} emails in Spam. Processing senders...")
        for msg_ref in messages:
            msg = service.users().messages().get(userId='me', id=msg_ref['id'], format='metadata', metadataHeaders=['From']).execute()
            headers = msg.get('payload', {}).get('headers', [])
            for header in headers:
                if header['name'].lower() == 'from':
                    email = extract_email(header['value'])
                    senders.add(email)
    
    print(f"\nUnique senders to whitelist ({len(senders)}):")
    for s in sorted(senders):
        print(f" - {s}")
        
    # Create the filter
    # To whitelist multiple senders, we use the 'from:(email1 OR email2 OR ...)' syntax
    query = " OR ".join(senders)
    filter_resource = {
        'criteria': {
            'from': query
        },
        'action': {
            'removeLabelIds': ['SPAM'],
            'addLabelIds': []
        }
    }
    
    print("\nCreating whitelist filter in Gmail...")
    try:
        created_filter = service.users().settings().filters().create(userId='me', body=filter_resource).execute()
        print(f"Success! Created Filter ID: {created_filter.get('id')}")
        print("All future emails from these senders will bypass the Spam folder.")
    except Exception as e:
        print(f"Error creating filter: {e}")

if __name__ == "__main__":
    main()
