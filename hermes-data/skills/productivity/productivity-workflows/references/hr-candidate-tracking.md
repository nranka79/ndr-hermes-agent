# HR Candidate Tracking — Interview Discussion Notes

## Pattern
Bharat tracks candidate call outcomes in a Google Docs file (`HR – Interviews & Discussions with Candidates`) rather than a Sheet. This allows free-form notes with structured fields per candidate.

## Workflow

### 1. Create the doc (once)
```python
from tools.gws_auth import build_service

drive_service = build_service("drive", "v3")

body = {
    "name": "HR – Interviews & Discussions with Candidates",
    "mimeType": "application/vnd.google-apps.document"
}
doc = drive_service.files().create(body=body, fields="id, name, webViewLink").execute()
doc_id = doc['id']
```

### 2. Share with NDR + RNR
```python
for email in ["ndr@draas.com", "rnr@draas.com"]:
    drive_service.permissions().create(
        fileId=doc_id,
        body={"type": "user", "role": "writer", "emailAddress": email},
        transferOwnership=False
    ).execute()
```

### 3. Write/update content
```python
from googleapiclient.http import MediaIoBaseUpload
import io

content = """HR – Interviews & Discussions with Candidates

---

Candidate: [Name]

Status: [Interested / Call not answered / Not interested / etc.]

Communication: [Good / Poor / Very poor / Okay]

Skills: [as mentioned in resume]

Joining: [Immediate / Later / Not specified]

Key Concern: [if any — e.g., WFH only]

Notes: [Free-form observations, next steps]
---"""

media = MediaIoBaseUpload(io.BytesIO(content.encode()), mimetype="text/plain")
drive_service.files().update(fileId=doc_id, media_body=media).execute()
```

## Standard Fields Per Candidate
- **Name** — candidate full name
- **Status** — Interested / Call not answered / Not interested / etc.
- **Communication** — Good / Okay / Poor / Very poor
- **Skills** — GST, TDS, PT filing, etc.
- **Joining** — Immediate / Specific timeline / Not interested
- **Key Concern** — WFH only, salary expectations, location, etc.
- **Notes** — free-form, includes next steps and Bharat's recommendation

## Document ID
- `1UjMKcIDeoEb3wPHkrOyRnUh-hAq38sYVBJhcFe40APo` (existing doc, May 2026)

## Sharing
- Shared with: ndr@draas.com, rnr@draas.com (both as writer)