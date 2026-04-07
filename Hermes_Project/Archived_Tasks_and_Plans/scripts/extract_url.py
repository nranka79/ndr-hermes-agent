import os

# Reading the UTF-16LE file created by PowerShell redirect
try:
    with open('gcloud_auth_url.txt', 'rb') as f:
        content = f.read().decode('utf-16')
    
    # Simple extraction of the URL (assuming it starts with https and ends with some query params)
    import re
    urls = re.findall(r'https://[^\s]+', content)
    if urls:
        print(urls[0])
    else:
        print("URL not found in file:")
        print(content)
except Exception as e:
    print(f"Error: {e}")
