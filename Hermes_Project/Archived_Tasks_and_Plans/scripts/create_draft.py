import base64
from email.message import EmailMessage
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os

TOKEN_PATH = r'C:\Users\ruhaan\AntiGravity\gmail_token.json'
# We might need 'https://www.googleapis.com/auth/gmail.compose' 
# or 'https://www.googleapis.com/auth/gmail.modify'
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.modify', 'https://www.googleapis.com/auth/gmail.compose']

from google_auth_oauthlib.flow import InstalledAppFlow

def get_credentials():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except:
                creds = None
        
        if not creds:
            flow = InstalledAppFlow.from_client_secrets_file(
                r'C:\Users\ruhaan\AntiGravity\gmail_credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
    return creds

def create_draft():
    creds = get_credentials()
    service = build('gmail', 'v1', credentials=creds)

    # 1. Fetch the 404 message
    msg_id = '19cdb95828138980'
    original_msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
    
    # 2. Extract some info from the original message
    headers = original_msg['payload']['headers']
    orig_subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'Demand Notice')
    orig_from = next((h['value'] for h in headers if h['name'] == 'From'), 'Century CRM')
    orig_date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
    
    # Simple way to get the body (handle multipart)
    def get_body(payload):
        if 'parts' in payload:
            for part in payload['parts']:
                body = get_body(part)
                if body:
                    return body
        if payload.get('mimeType') == 'text/plain':
            data = payload.get('body', {}).get('data', '')
            return base64.urlsafe_b64decode(data).decode()
        return None

    orig_body = get_body(original_msg['payload']) or original_msg['snippet']

    # 3. Construct the draft content
    draft_body = f"""Dear Ashwin,

I am forwarding the Demand Notice received for Century Regalia Unit 404.

As we discussed, the CRM team is continuing to generate these automated invoices, but I wanted to put this on record. Please note that the purchase of units 404 and 401 was part of an arrangement where the loan amount was adjusted. 

When looking at both units together, specifically unit 401 (which shows an excess payment) and unit 404, the combined balance is currently in excess. Therefore, I'm assuming that since the combined payment across the two apartments is still in excess, this is not due in any way.

I would also like to request you to push Anthony and the sales team, as we previously discussed, to focus on the liquidation and sale of these units. This will help close out the transaction completely and ensure the repayment of the loan principal that was adjusted here.

I hope you find this in order, Ashwin. Looking forward to a logical end to what began as a loan transaction.

Best regards,
Nishant

---------- Forwarded message ---------
From: {orig_from}
Date: {orig_date}
Subject: {orig_subject}
To: ndr@drahomes.in

{orig_body}
"""

    message = EmailMessage()
    message.set_content(draft_body)
    message['To'] = 'ashwin.pai@centuryrealestate.in'
    message['Subject'] = f'Fwd: {orig_subject}'

    # encoded message
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    create_message = {
        'message': {
            'raw': encoded_message
        }
    }

    try:
        draft = service.users().drafts().create(userId='me', body=create_message).execute()
        print(f"Draft created successfully. ID: {draft['id']}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    create_draft()
