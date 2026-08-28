# Hiring Tracker Sheet + Resume Folder Setup (DRAAS Pattern)

When Bharat asks to create a hiring tracker: create **one sheet** + **one Drive folder** linked together.

## Sheet Structure

**Title:** `DRA Hiring Tracker`
**Tab 1:** `Candidates` (frozen header row)

| Sl No | Date | Candidate Name | Mobile Number | Email ID | Total Experience (Yrs) | Department | Job Role | Resume Drive Link | Status | Remarks |
|-------|------|---------------|--------------|---------|----------------------|-----------|---------|-----------------|------|-------|

**Tab 2:** `Departments` (reference table — departments DRAAS hires for):

| Department | Hiring For |
|-----------|-----------|
| Designing | Designer |
| Project Management | Project Manager |
| Sales / Presales | Presales / Stellar Color |
| Admin | Admin Executive |
| Accounts | Accounts Executive |

## Drive Folder

**Name:** `DRA Hiring - Resumes`
Create under the user's My Drive root (no shared folder).

## Resume Processing Workflow

When Bharat uploads a resume file:
1. Download & extract: Name, Mobile, Email, Experience, Job Role
2. Upload resume PDF to the Drive folder
3. Add a new row to the `Candidates` sheet with extracted info + resume Drive link
4. Ask Bharat to confirm/assign the Department

## Python Snippet

```python
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from pathlib import Path

# Load creds (use direct-load pattern, see gws-token-field-name-mismatch.md)
TOKEN_PATH = 'the gws-vault daemon (no token files exist on disk — see api-references/google-workspace-api/references/token-access-canonical.md)'
SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']
creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
if creds.expired and creds.refresh_token:
    creds.refresh(Request())
    Path(TOKEN_PATH).write_text(creds.to_json())

drive = build('drive', 'v3', credentials=creds)
sheets = build('sheets', 'v4', credentials=creds)
```

## Verified Assets (Jun 2026)

- **Resume Folder ID:** `1mRj2OvWjTIbXb520-fanlseXchV87MTU`
- **Hiring Sheet ID:** `1KNYOYgEWMUWSrCD2cFxrQSZcfjNWnRBFIZGdxCi0Q6k`
- **Owner:** Bharat Hawaldar (sales1.blr@draas.com)
