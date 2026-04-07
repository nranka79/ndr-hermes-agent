import os
import sys
import requests

TOKEN = "<REDACTED_OAUTH_ACCESS_TOKEN>" # Note: This token is short-lived
FILENAME = "ndr Aadhar"

def search_drive(token, name):
    headers = {"Authorization": f"Bearer {token}"}
    query = f"name contains '{name}'"
    url = f"https://www.googleapis.com/drive/v3/files?q={requests.utils.quote(query)}&fields=files(id,name,mimeType)"
    
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        print(f"Error searching: {r.text}")
        return None
    
    return r.json().get('files', [])

def download_file(token, file_id, filename):
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://www.googleapis.com/drive/v3/files/{file_id}?alt=media"
    
    print(f"Downloading {filename}...")
    r = requests.get(url, headers=headers, stream=True)
    if r.status_code != 200:
        print(f"Error downloading: {r.text}")
        return False
        
    with open(filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
    return True

def main():
    files = search_drive(TOKEN, "Aadhar")
    if not files:
        print("No Aadhaar files found.")
        return

    print(f"Found {len(files)} potential file(s):")
    for i, f in enumerate(files):
        print(f"[{i}] {f['name']} ({f['mimeType']})")

    # Pick the one that looks most like 'NDR Aadhar Card.pdf' or '20201008 NDR New Aadhar Card New Scan.pdf'
    # Based on the screenshot from before, the best one is index 0 or the one with 'New Scan'
    target = None
    for f in files:
        if "New Scan" in f['name']:
            target = f
            break
    
    if not target and files:
        target = files[0]
        
    if target:
        local_name = target['name']
        if not local_name.endswith('.pdf') and 'pdf' in target['mimeType']:
            local_name += '.pdf'
        
        success = download_file(TOKEN, target['id'], local_name)
        if success:
            print(f"Successfully downloaded to: {os.path.abspath(local_name)}")

if __name__ == "__main__":
    main()
