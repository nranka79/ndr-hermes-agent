
import os
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def search_contact(query):
    token_path = r'c:\Users\ruhaan\AntiGravity\workspace_power_token.json'
    if not os.path.exists(token_path):
        print("Token not found.")
        return

    creds = Credentials.from_authorized_user_file(token_path)
    service = build('people', 'v1', credentials=creds)

    results = service.people().searchContacts(
        query=query,
        readMask='names,phoneNumbers'
    ).execute()

    connections = results.get('results', [])
    if not connections:
        print(f"No contacts found for '{query}'.")
        return

    for person in connections:
        person_data = person.get('person', {})
        names = person_data.get('names', [])
        phones = person_data.get('phoneNumbers', [])
        name = names[0].get('displayName') if names else "Unknown"
        phone_list = [p.get('value') for p in phones]
        print(f"Name: {name}, Phones: {phone_list}")

if __name__ == '__main__':
    search_contact('Sashi')
