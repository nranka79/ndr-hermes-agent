import os
import sys
import subprocess
import requests

def get_token():
    try:
        # Calling the gcloud.ps1 script via powershell
        cmd = ['powershell', '-Command', 'gcloud auth print-access-token']
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except Exception as e:
        print(f"Error getting gcloud token: {e}")
        # Try fallback to just 'ndr@draas.com' token if we can get it via a direct call
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
    
    # Check if download is restricted or if we need to handle specific MIME types
    print(f"Downloading {filename}...")
    r = requests.get(url, headers=headers, stream=True)
    if r.status_code != 200:
        print(f"Error downloading: {r.text}")
        return False
        
    with open(filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024 * 64):
            if chunk:
                f.write(chunk)
    return True

def main():
    token = get_token()
    if not token:
        print("Could not retrieve authentication token. Please ensure gcloud is logged in.")
        return

    files = search_drive(token, "Aadhar")
    if not files:
        print("No Aadhaar files found.")
        return

    # Files to look for (from the Drive search screenshot)
    preferred_names = [
        "20201008 NDR New Aadhar Card New Scan.pdf",
        "NDR Aadhar Card.pdf",
        "NDR Aadhar New Sep2019.pdf"
    ]
    
    target_file = None
    for p in preferred_names:
        for f in files:
            if f['name'] == p:
                target_file = f
                break
        if target_file: break

    if not target_file:
        # Fallback to anything with NDR and Aadhar
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
            
        # Clean local name for filesystem
        safe_name = local_name.replace(" ", "_").replace("(", "").replace(")", "").replace("&", "and")
        
        success = download_file(token, target_file['id'], safe_name)
        if success:
            abs_path = os.path.abspath(safe_name)
            print(f"\n--- SUCCESS ---")
            print(f"File: {target_file['name']}")
            print(f"Saved to: {abs_path}")
            print(f"---------------")
    else:
        print("No suitable Aadhaar file found in the search results.")

if __name__ == "__main__":
    main()
