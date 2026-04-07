# -*- coding: utf-8 -*-
import os
import sys
import io
import json
import urllib.parse
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Force UTF-8 output
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

TOKEN_PATH = r"C:\Users\ruhaan\AntiGravity\workspace_power_token.json"

def get_service(api_name, version):
    if not os.path.exists(TOKEN_PATH):
        raise FileNotFoundError("Power Token not found.")
    creds = Credentials.from_authorized_user_file(TOKEN_PATH)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return build(api_name, version, credentials=creds)

def main():
    try:
        drive_service = get_service('drive', 'v3')
        
        # 1. Search for the folder
        query = "name contains 'Charitra' and mimeType = 'application/vnd.google-apps.folder'"
        print(f"Searching for folder: {query}")
        results = drive_service.files().list(q=query, fields="files(id, name, webViewLink)").execute()
        folders = results.get('files', [])
        
        if not folders:
            print("No folder found with 'Charitra' in name. Trying broader search...")
            # Maybe it's "personal" parent folder?
            results = drive_service.files().list(q="name contains 'personal' and mimeType = 'application/vnd.google-apps.folder'", fields="files(id, name)").execute()
            personal_folders = results.get('files', [])
            for pf in personal_folders:
                print(f"Checking inside 'personal' folder: {pf['name']} ({pf['id']})")
                sub_results = drive_service.files().list(q=f"'{pf['id']}' in parents and mimeType = 'application/vnd.google-apps.folder'", fields="files(id, name, webViewLink)").execute()
                folders.extend(sub_results.get('files', []))
        
        target_folder = None
        for f in folders:
            if 'charitra' in f['name'].lower():
                target_folder = f
                break
        
        if not target_folder:
            print("Could not find the target folder.")
            return

        print(f"Found folder: {target_folder['name']} ({target_folder['id']})")
        folder_link = target_folder['webViewLink']
        
        # 2. Add Roshi as Editor
        roshi_email = "rnr@draas.com"
        print(f"Sharing folder with {roshi_email} as Editor...")
        permission = {
            'type': 'user',
            'role': 'writer',
            'emailAddress': roshi_email
        }
        drive_service.permissions().create(fileId=target_folder['id'], body=permission, fields='id').execute()
        print("Successfully shared folder.")

        # 3. Create WhatsApp link
        # Message: Here is the link to the folder and all documentation for Charitra have been prepared here [link]. 
        # Please review it once. Particularly the loan documentation will documentation and FTA documentation 
        # are critical for her to review.
        
        message = (
            f"Here is the link to the folder and all documentation for Charitra have been prepared here {folder_link}. "
            f"Please review it once. Particularly the loan documentation, will documentation and FTA documentation "
            f"are critical to review."
        )
        # Roshi's number is not provided, so I'll use a placeholder or just the link format
        # Actually, the user asked for a "wa.me with her number", but didn't give the number.
        # Wait, let me check if Roshi's number is in contacts or previous messages.
        # User said "create a hyperlink WhatsApp message for my wife Roshi Basically a wa.me with her number"
        # I'll check if I can find her number in Contacts.
        
        print("\n--- GENERATED WHATSAPP MESSAGE ---")
        print(message)
        
        # Search for Roshi in People API
        people_service = get_service('people', 'v1')
        contact_results = people_service.people().connections().list(resourceName='people/me', personFields='names,phoneNumbers').execute()
        connections = contact_results.get('connections', [])
        
        roshi_num = ""
        for person in connections:
            names = person.get('names', [])
            if any('roshi' in n.get('displayName', '').lower() for n in names):
                nums = person.get('phoneNumbers', [])
                if nums:
                    roshi_num = nums[0].get('value', '').replace(' ', '').replace('-', '').replace('+', '')
                    break
        
        if roshi_num:
            encoded_msg = urllib.parse.quote(message)
            wa_link = f"https://wa.me/{roshi_num}?text={encoded_msg}"
            print(f"\nWhatsApp Link for Roshi ({roshi_num}):")
            print(wa_link)
        else:
            print("\nCould not find Roshi's phone number in contacts. Please provide it for a direct wa.me link.")
            encoded_msg = urllib.parse.quote(message)
            print(f"General WhatsApp Link (share manually): https://wa.me/?text={encoded_msg}")

    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == '__main__':
    main()
