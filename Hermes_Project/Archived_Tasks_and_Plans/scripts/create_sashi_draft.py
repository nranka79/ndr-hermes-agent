
import os
import json
import base64
from email.message import EmailMessage
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def create_draft():
    token_path = r'c:\Users\ruhaan\AntiGravity\workspace_power_token.json'
    if not os.path.exists(token_path):
        print("Token not found.")
        return

    creds = Credentials.from_authorized_user_file(token_path)
    service = build('gmail', 'v1', credentials=creds)

    message = EmailMessage()

    # Format the message based on the user's instructions
    message_body = """Hi Sashi Dharan,

Here's a clear explanation of how the current investors are securing their 176,612 sq ft of the property.

As it stands, out of the total project plot cost, ₹21 Crores is attributed to the land value, accompanied by ₹6.0 Crores allocated for development and ₹1.2 Crores for miscellaneous costs, aggregating to a total project cost of roughly ₹28.2 Crores.

Based on our agreement, Group 1 holds a 50% financial commitment, while taking up 60% of the land area.

This arrangement means the remaining portion (₹14.1 Crores representing 50% of the cost burden) is to be borne by the Group 2 investors (P1-P19), who hold a 40% share of the overall land piece (117,612 sq ft). This translates to an effective entry cost equivalent of approx ₹1198.86 per sq ft.

We established that the early investors who brought in resources initially and locked the land area in, with an added 10% premium space allocation, maintain a solid stake based on our agreement with Group 1.

Please feel free to reach out if you have further queries about these calculations or the general break up."""

    message.set_content(message_body)

    message['To'] = 'sashidharan@example.com'  
    message['Subject'] = 'Breakdown of Investment Allocation and Cost Structure'

    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    create_message = {
        'message': {
            'raw': encoded_message
        }
    }

    draft = service.users().drafts().create(userId='me', body=create_message).execute()
    print(f"Draft created successfully. Draft ID: {draft['id']}")

if __name__ == '__main__':
    create_draft()
