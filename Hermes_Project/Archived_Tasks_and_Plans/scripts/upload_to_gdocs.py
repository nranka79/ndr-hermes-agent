import os
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

def get_creds(token_path):
    if not os.path.exists(token_path): return None
    with open(token_path, 'r') as f:
        creds_data = json.load(f)
    try:
        creds = Credentials.from_authorized_user_info(creds_data)
    except ValueError:
        creds = Credentials(
            token=creds_data.get('access_token', creds_data.get('token')),
            refresh_token=creds_data.get('refresh_token'),
            token_uri=creds_data.get('token_uri', "https://oauth2.googleapis.com/token"),
            client_id=creds_data.get('client_id'),
            client_secret=creds_data.get('client_secret')
        )
    return creds

def upload_html_to_docs():
    for tk in ['drive_token.json', 'workspace_power_token.json', 'gmail_token.json']:
        try:
            creds = get_creds(tk)
            if not creds: continue
            
            drive_service = build('drive', 'v3', credentials=creds)

            file_metadata = {
                'name': 'MAIS Class 8 Math Enhanced Model Paper (80 Marks)',
                'mimeType': 'application/vnd.google-apps.document'
            }
            
            media = MediaFileUpload('enhanced_qp.html',
                                    mimetype='text/html',
                                    resumable=True)
                                    
            file = drive_service.files().create(body=file_metadata,
                                                media_body=media,
                                                fields='id, webViewLink').execute()
            
            print(f"Uploaded successfully using {tk}!")
            print(f"Document ID: {file.get('id')}")
            print(f"Open the document at: {file.get('webViewLink')}")
            # Save the link to a text file for easy access
            with open('generated_doc_link.txt', 'w') as out:
                out.write(f"Link: {file.get('webViewLink')}\n")
            return
        except Exception as e:
            print(f"Failed with {tk}: {e}")

if __name__ == '__main__':
    upload_html_to_docs()
