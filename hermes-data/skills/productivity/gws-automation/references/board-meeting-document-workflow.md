# Board Meeting Document Workflow — Drive + Calendar

## When to Use

**Trigger:** User uploads or shares a board meeting document (shorter notice consent, agenda, minutes) and tells you which company it belongs to, or provides enough context to identify the company.

This covers: identifying the company → finding/creating the Drive folder → applying Nishant's naming convention → uploading → linking in the calendar event.

## Step 1 — Identify the Company from Document

Read the document content (DOCX via zipfile + XML, PDF via pymupdf) to extract the company name:

```python
import zipfile, xml.etree.ElementTree as ET

with zipfile.ZipFile(path) as z:
    xml_content = z.read('word/document.xml')
    root = ET.fromstring(xml_content)
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    text = ''
    for t in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
        if t.text:
            text += t.text + ' '
```

Look for the full company name in the document body (e.g. "DRA AADITHYA SOUTH CITY PROJECTS PRIVATE LIMITED").

## Step 2 — Find the Company's Drive Folder

Search Drive for a folder matching the company name:

```python
results = drive.files().list(
    q="mimeType='application/vnd.google-apps.folder' and name contains 'Aadithya' and trashed=false",
    fields="files(id, name, parents)",
    pageSize=10
).execute()
```

**Nishant's folder structure (Jun 2026):**
- Chennai company folders live under a parent like "Chennai shares gifting"
- Each company has its own folder: "DRA Aadithya Southcity Projects Pvt Ltd"
- Board meeting documents go into a subfolder: "Board Meeting Notices & Minutes"
- Create this subfolder if it doesn't exist

## Step 3 — Name the Document

**Nishant's naming convention (confirmed Jun 2026):**
`YYYYMMDD_CompanyCode_DocType.docx`

Company codes observed:
- `DRAASCS` = DRA Aadithya South City Projects Pvt Ltd
- `DRAAP` = DRA Aadithya Projects Pvt Ltd

Document type examples:
- `ShorterNotice_Consent`
- `BMConsentLetter`
- `Agenda`
- `Minutes`

The date in the filename reflects the **document content date** (e.g. 08 Jun 2026 when the consent was signed), not the upload date.

## Step 4 — Upload to Drive

```python
from googleapiclient.http import MediaFileUpload

file_meta = {
    'name': '20260608_DRAASCS_ShorterNotice_Consent.docx',
    'parents': [subfolder_id]
}
media = MediaFileUpload(local_path, mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
uploaded = drive.files().create(body=file_meta, media_body=media, fields='id, name, webViewLink').execute()

# Set public access
drive.permissions().create(fileId=uploaded['id'], body={'type': 'anyone', 'role': 'reader'}, fields='id').execute()
```

## Step 5 — Link in Calendar Event

The document is usually for an upcoming board meeting. Find the event and append the Drive link to its description:

```python
event = calendar.events().get(calendarId='primary', eventId=event_id).execute()
doc_info = f"\n\n**📄 Attached Document:** {new_name}\nDrive Link: {uploaded['webViewLink']}"
calendar.events().patch(calendarId='primary', eventId=event_id, body={'description': event['description'] + doc_info}).execute()
```

Also add any external meeting links (Teams/Zoom) shared separately — append them to the same description.

## Steps Recap

1. Read the document → identify company name
2. Search Drive for company folder
3. Create/use "Board Meeting Notices & Minutes" subfolder
4. Rename per Nishant's convention: `YYYYMMDD_CompanyCode_DocType.ext`
5. Upload with public "anyone with link" permission
6. Add Teams/Zoom meeting link to calendar event description
7. Add Drive document link to calendar event description

## Pitfalls

- **Subfolder may not exist** — always check with Drive list query before creating
- **.docx files can't be exported to PDF via Drive API** — if the user wants a PDF, convert locally with libreoffice (if available) or attach the original .docx
- **Multiple related companies** — confirm with user which entity the document belongs to if the document mentions several (e.g. DRA Aadithya Southcity vs DRA Aadithya Projects)
- **The naming convention date** = date on the document (signed date), not today's date
