import os
import sys
import subprocess
import requests

def get_token():
    try:
        result = subprocess.run(['gcloud', 'auth', 'print-access-token'], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except Exception as e:
        print(f"Error getting gcloud token: {e}")
        return None

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
    token = get_token()
    if not token:
        return

    files = search_drive(token, "Aadhar")
    if not files:
        print("No Aadhaar files found.")
        return

    print(f"Found {len(files)} potential file(s):")
    # Priority search for the most relevant files from the screenshot
    targets = [
        "20201008 NDR New Aadhar Card New Scan.pdf",
        "NDR Aadhar Card.pdf",
        "NDR Aadhar New Sep2019.pdf"
    ]
    
    target_file = None
    # Try exact matches first
    for t in targets:
        for f in files:
            if f['name'] == t:
                target_file = f
                break
        if target_file: break
    
    # Fallback to anything with "NDR" and "Aadhar"
    if not target_file:
        for f in files:
            if "NDR" in f['name'].upper() and "AADHAR" in f['name'].upper():
                target_file = f
                break
                
    if not target_file and files:
        target_file = files[0]
        
    if target_file:
        local_name = target_file['name']
        if not local_name.endswith('.pdf') and 'pdf' in target_file['mimeType']:
            local_name += '.pdf'
        
        # Ensure filenames are safe
        local_name = local_name.replace(" ", "_").replace("(", "").replace(")", "")
        
        success = download_file(token, target_file['id'], local_name)
        if success:
            print(f"Successfully downloaded to: {os.path.abspath(local_name)}")
            print(f"RESULT_FILE:{os.path.abspath(local_name)}")

if __name__ == "__main__":
    main()
