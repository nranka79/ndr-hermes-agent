# Important Information — Drive Document

**Document ID:** `17qG23od-hRioDFj0yXSBfTraiuFXM019UwVBvRLlpR0`
**Document type:** Google Docs (Google Apps Document)
**Accessible via:** Google Docs API (`https://docs.googleapis.com/v1/documents/{id}`) with OAuth token

## How to Access

```python
import json, urllib.request, urllib.parse

with open('/data/hermes/oauth-draas.json') as f:
    creds = json.load(f)

data = urllib.parse.urlencode({
    'client_id': creds['client_id'],
    'client_secret': creds['client_secret'],
    'refresh_token': creds['refresh_token'],
    'grant_type': 'refresh_token'
}).encode()
req = urllib.request.Request('https://oauth2.googleapis.com/token', data=data,
    headers={'Content-Type': 'application/x-www-form-urlencoded'})
with urllib.request.urlopen(req, timeout=15) as resp:
    token = json.loads(resp.read())['access_token']

doc_id = '17qG23od-hRioDFj0yXSBfTraiuFXM019UwVBvRLlpR0'
url = f'https://docs.googleapis.com/v1/documents/{doc_id}'
req2 = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}'})
with urllib.request.urlopen(req2, timeout=15) as resp:
    doc = json.loads(resp.read())

# Extract text from all paragraphs
text_content = ''
for content in doc.get('body', {}).get('content', []):
    if 'paragraph' in content:
        for elem in content['paragraph'].get('elements', []):
            if 'textRun' in elem:
                text_content += elem['textRun'].get('content', '')
        text_content += '\n'
```

## Contents (as of last session)

This document is the user's personal key-reference file. Key entries include:

| Entry | Value |
|-------|-------|
| **DRA Realty Pvt Ltd GSTN** | `29AAPCS9730H1ZO` |
| **Westbury Hospitality Pvt Ltd GSTN** | `29AAACW5838P1ZH` |
| NDR PAN | `AHVPR5168E` |
| NDR DIN | `00298854` |
| NDR Aadhar | `415905352796` |
| NDR Passport No | `Z7003791` |
| HDFC Customer ID | `112512101` |
| Kotak CRN | `465585244` |
| DRA Partners One A/c | `10062335419` (IFSC: IDFB0080151, Sadashivnagar) |
| Metamask phrase | Stored (do not share) |
| Marriott Bonvoy A/c | `291896419` |
| Club Vistara membership | `147778190` |

## When to Use This

- Looking up GST numbers for DRA entities
- Filling in PAN/GST fields on forms, agreements, or invoices
- Retrieving DRA bank account details for payment references
- Any task requiring official entity registration details

## Note

This document is NOT accessible via Drive export (403 on some files). Use the Google Docs API as shown above.
