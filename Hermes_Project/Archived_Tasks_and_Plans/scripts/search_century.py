from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os

TOKEN_PATH = r'C:\Users\ruhaan\AntiGravity\gmail_token.json'
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def search_emails():
    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    service = build('gmail', 'v1', credentials=creds)
    
    # Try searching for "Century"
    print("Searching for 'Century'...")
    results = service.users().messages().list(userId='me', q='Century', maxResults=10).execute()
    messages = results.get('messages', [])
    
    for m in messages:
        msg = service.users().messages().get(userId='me', id=m['id'], format='metadata', metadataHeaders=['Subject', 'From']).execute()
        headers = msg['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(no subject)')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), '(unknown)')
        print(f"ID: {m['id']} | From: {sender} | Subject: {subject}")

if __name__ == "__main__":
    search_emails()
