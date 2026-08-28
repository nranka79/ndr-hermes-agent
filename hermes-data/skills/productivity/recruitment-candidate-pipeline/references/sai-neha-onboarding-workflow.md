# Worked Example: Sai Neha Vaddadi Onboarding (Jul 2026)

Complete onboarding trace for **Sai Neha Vaddadi** — Content Creator, DRA Realty Private Limited.

## Context

- **Hired via:** Offer of Employment (docx attachment) sent 2 Jun 2026 by Nishant Ranka
- **Personal email:** esotericarts.ani@gmail.com
- **Phone:** +91 7899398273 (found in offer letter text + resume)
- **DOJ:** 16 June 2026
- **Manager:** Gowri Singh (gsingh@draas.com)
- **Department:** Marketing (Content & Marketing)
- **CTC:** ₹38,000/month (₹33,000 base + ₹5,000 attendance allowance)
- **Company email created:** nVaddadi@draas.com (Nishant created in Google Admin)
- **Temporary password:** 5d&C6u7jq9Jy4yU& (from Nishant)

## Data Sources Used

### 1. Gmail — Offer Letter Email
- **Message ID:** `19e8c1b15f7e30ab`
- **Subject:** "Offer Letter — Content Creator Role — DRA Realty Private Limited"
- **From:** Nishant Ranka <ndr@draas.com>
- **Attachments:**
  - Part 1: `20260603_DRA_SaiNehaVaddadi_OfferLetter_ContentCreator.docx` (MIME: `application/vnd.openxmlformats-officedocument.wordprocessingml.document`, size: 203,980 bytes)
  - Part 2: `2026 DRA - HR POLICY.docx`

### 2. Drive — Resume PDF
- **File:** `20260603_DRA_SaiNehaVaddadi_Naukri_Resume_0y5m_ContentCreator.pdf` (ID: `1IApjLdMCbtKEWZimsq6CFs5fNfv-bA4R`)
- **Resume text extracted:** Contact info shows "Bangalore - 37, Karnataka" — no full residential address

### 3. Gmail — Employee's Request for Email
- **Message ID:** `19f7dd0f0c4a613e`
- **Subject:** "Request for Official Email ID"
- **Date:** 20 Jul 2026 — employee proactively asked for company email

## API Calls Executed

All via `tools.gws_auth.build_service()` using service_name='google-draas'.

### Gmail: Search & Read
```python
# Find offer letter
results = service.users().messages().list(userId='me', q='Sai Neha OR Vaddadi offer letter', maxResults=10).execute()

# Read full message with parts
m = service.users().messages().get(userId='me', id=MSG_ID, format='full').execute()

# Download docx attachment
att = service.users().messages().attachments().get(userId='me', messageId=MSG_ID, id=ATTACH_ID).execute()
data = base64.urlsafe_b64decode(att['data'])
```

### Docx Text Extraction (no python-docx)
```python
import zipfile, xml.etree.ElementTree as ET
with zipfile.ZipFile('/tmp/offer.docx') as z:
    with z.open('word/document.xml') as f:
        tree = ET.parse(f)
        ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        text_parts = [t.text for t in tree.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t') if t.text]
        full_text = ' '.join(text_parts)
```

### Drive: Search & Download Resume
```python
results = service.files().list(q="name contains 'Neha' or name contains 'Vaddadi'", fields='files(id,name,mimeType)').execute()

# Download PDF
request = service.files().get_media(fileId=FILE_ID)
fh = io.BytesIO()
downloader = MediaIoBaseDownload(fh, request)
done = False
while not done:
    status, done = downloader.next_chunk()
```

### People API: Create Contact
```python
contact = {
    "names": [{"givenName": "Sai", "middleName": "Neha", "familyName": "Vaddadi", "displayName": "Sai Neha Vaddadi"}],
    "emailAddresses": [
        {"type": "work", "value": "nVaddadi@draas.com"},
        {"type": "personal", "value": "esotericarts.ani@gmail.com"}
    ],
    "phoneNumbers": [{"type": "mobile", "value": "+917898398273"}],
    "organizations": [{"name": "DRA Realty Private Limited", "title": "Content Creator", "department": "Marketing"}],
    "addresses": [{"city": "Bangalore", "region": "Karnataka", "country": "India"}],
    "biographies": [{"value": "Reports to Gowri Singh (gsingh@draas.com). Part of content@draas.com group email.", "contentType": "TEXT_PLAIN"}]
}
created = people_service.people().createContact(body=contact).execute()
# Returns resourceName e.g. people/c7914236520266158008
```

### Sheets: Append to employees tab
```python
row = ['Sai Neha Vaddadi', 'nVaddadi@draas.com', '+917899398273', 'employee', '', 'Content Creator, Reports to Gowri Singh (gsingh@draas.com), Marketing Dept']
result = sheets.spreadsheets().values().append(
    spreadsheetId='1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g',
    range='employees!A:F',
    valueInputOption='USER_ENTERED',
    insertDataOption='INSERT_ROWS',
    body={'values': [row]}
).execute()
# Returns updatedRange: employees!A10:F10
```

### Sheets: Append to main contacts CSV tab
```python
row_data = [None] * 93
row_data[0] = 'Sai'       # First Name
row_data[1] = 'Neha'      # Middle Name
row_data[2] = 'Vaddadi'   # Last Name
row_data[9] = 'Vaddadi, Sai Neha'  # File As
row_data[10] = 'DRA Realty Private Limited'
row_data[11] = 'Content Creator'
row_data[12] = 'Marketing'
row_data[14] = 'Reports to Gowri Singh. Part of content@draas.com group email.'
row_data[17] = 'Work'     # E-mail 1 - Label
row_data[18] = 'nVaddadi@draas.com'
row_data[19] = 'Personal' # E-mail 2 - Label
row_data[20] = 'esotericarts.ani@gmail.com'
row_data[27] = 'Mobile'   # Phone 1 - Label
row_data[28] = '+917899398273'
row_data[42] = 'Bangalore' # Address 1 - City
row_data[44] = 'Karnataka'  # Address 1 - Region

result = sheets.spreadsheets().values().append(
    spreadsheetId='1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g',
    range="'NDR DRAAS Google contacts.csv'!A:A",
    valueInputOption='USER_ENTERED',
    insertDataOption='INSERT_ROWS',
    body={'values': [row_data]}
).execute()
# Returns updatedRange: 'NDR DRAAS Google contacts.csv'!A4218:AS4218
```

## WhatsApp Welcome Message

**Recipient:** +91 7899398273 (Sai Neha Vaddadi)

```
Hi Sai Neha, welcome to DRA Realty!

Your company email account has been created:

📧 Email: nVaddadi@draas.com
🔑 Temporary Password: 5d&C6u7jq9Jy4yU&

Please follow these steps:
1. Go to https://gmail.com
2. Enter your username: nVaddadi@draas.com
3. Enter the temporary password above
4. You will be prompted to reset your password — please set a new password of your choice
5. Start using your email going forward

Also, please note that you, Gowri, and the team are part of a group email: content@draas.com. Any emails sent to this address will also reach your inbox. We'll use this group for internal discussions and communications related to content — just keeping you informed.

Welcome aboard! 🚀
```

Generated via `urllib.parse.quote()` → `https://wa.me/917899398273?text=<encoded>`.

## Key Decisions Made

1. **Email address convention:** nVaddadi@draas.com (first initial + last name) — confirmed by Nishant
2. **Temporary password:** Provided by Nishant (agent does not have Google Admin access)
3. **Group email:** content@draas.com — mentioned in the welcome message for awareness
4. **Residential address:** Not available in any record — offer letter explicitly says "to be confirmed at joining"

## Sources of Employee Data (by reliability)

| Field | Source | Reliability |
|-------|--------|-------------|
| Phone | Offer letter docx text | ✅ High (confirmed across 2 docs) |
| Personal Email | Email thread | ✅ High |
| Role/Title | Offer letter | ✅ High |
| CTC | Offer letter | ✅ High |
| DOJ | Email thread | ✅ High |
| Manager | Offer letter | ✅ High |
| Department | Offer letter | ✅ High |
| City/Location | Resume PDF | ⚠️ Medium (city only, not full address) |
| Residential Address | None | ❌ Missing |
