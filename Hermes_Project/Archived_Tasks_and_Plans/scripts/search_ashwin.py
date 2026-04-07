from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os

TOKEN_PATH = r'C:\Users\ruhaan\AntiGravity\gmail_token.json'
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def search_ashwin():
    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    service = build('gmail', 'v1', credentials=creds)
    
    print("Searching for 'Ashwin Pai'...")
    results = service.users().messages().list(userId='me', q='Ashwin Pai', maxResults=10).execute()
    messages = results.get('messages', [])
    
    senders = set()
    for m in messages:
        msg = service.users().messages().get(userId='me', id=m['id'], format='metadata', metadataHeaders=['To', 'Cc', 'From']).execute()
        headers = msg['payload']['headers']
        for h in headers:
            senders.add(h['value'])
    
    print("Related contacts found:")
    for s in senders:
        print(f" - {s}")

if __name__ == "__main__":
    search_ashwin()
