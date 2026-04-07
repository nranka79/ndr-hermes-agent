# -*- coding: utf-8 -*-
import os
import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

TOKEN_PATH = r"C:\Users\ruhaan\AntiGravity\workspace_power_token.json"
FILE_ID = "1M7JkY7Sx5JpZsx4Di14iPywV0GIrqdLW"
OUTPUT = "NDR_Aadhar.pdf"

def main():
    creds = Credentials.from_authorized_user_file(TOKEN_PATH)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    
    url = f"https://www.googleapis.com/drive/v3/files/{FILE_ID}?alt=media"
    headers = {"Authorization": f"Bearer {creds.token}"}
    
    print(f"Downloading Aadhar from Drive (ID: {FILE_ID})...")
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        with open(OUTPUT, "wb") as f:
            f.write(r.content)
        print(f"SUCCESS: Downloaded to {os.path.abspath(OUTPUT)}")
    else:
        print(f"FAILED: Status {r.status_code}\n{r.text}")

if __name__ == "__main__":
    main()
