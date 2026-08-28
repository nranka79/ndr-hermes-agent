# Ranka North Star — Pre-DCR Drawing Filing

## When to Use

Architect submits pre-DCR sanction drawings for Ranka North Star (Allalsandra) — PDF + DWG versions — to go into final BBMP submission.

## Naming Convention

```
YYYYMMDD_NorthStar_DraDevelopers_PreDCRDrawings.<ext>
```

Example: `20260525_NorthStar_DraDevelopers_PreDCRDrawings.pdf`

## Workflow

### Step 1 — Confirm Target Folder with User
- Do NOT upload until folder is confirmed by user
- Search Drive for existing folders: "North star approval folder", "Ranka North Star", etc.
- List folder contents to confirm appropriateness
- Present recommendation and wait for user confirmation

### Step 2 — Upload/Copy Files
- **PDF**: Upload from local cache to target folder with new name
- **DWG**: If already in Drive, COPY to target folder (don't re-upload/download); if not, upload local file
  - Use `drive.files().copy()` for Drive-hosted files — avoids download/upload round-trip
  - For non-Drive files, use `MediaFileUpload` via SA credentials

### Step 3 — Share with 1-Week Expiry
Recipients typically include:
- **Architect**: Arvind Jain (A J Architect) — `arch_arvind2000@yahoo.co.in`
- **Architecture team colleague**: Bhuvanesh Krishnan — `bk@findingform.design`
- **DRAAS PM**: Anbarasan — `pm2.blr@draas.com`

```python
from datetime import datetime, timedelta
one_week = (datetime.utcnow() + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
drive.permissions().create(
    fileId=file_id,
    body={
        "type": "user",
        "role": "reader",
        "emailAddress": email,
        "expirationTime": one_week
    }
)
```

### Step 4 — Draft Email to Architect
- Address to Arvind Jain (A J Architect)
- CC architecture team colleague + DRAAS PM
- State these are pre-DCR drawings going into final submission
- Request review and formal green signal before BBMP submission
- Include Drive links in email body

## Known Contacts

| Person | Role | Email |
|--------|------|-------|
| Arvind Jain | A J Architect — lead architect for North Star | arch_arvind2000@yahoo.co.in |
| Bhuvanesh Krishnan | Architecture team colleague | bk@findingform.design |
| Anbarasan | DRAAS PM (PM2 BLR) | pm2.blr@draas.com |

## Folder IDs (verify before use)

- Target folder used 25 May 2026: `14BDNAcDKmGDHbDswU7UnBd4mOj-1xLMt`
- "North star approval folder 2026 April": `1dw-BzPEmoWdiQ-ePcanYA0INvVfQxJfB`

## Key Pitfall

**Never download DWG from Drive to upload again** — use `drive.files().copy()` to duplicate the file in target folder with new name. DWG download via `curl/wget` to Drive direct link returns HTML cookie page, not the file. Use `MediaIoBaseDownload` via Drive API if download is needed.

## Benson Town / Bhuvanesh FAR Working Follow-Up

**Trigger:** User asks to WhatsApp/message Bhuvanesh reminding him about Benson Town Abdullah ~15,000 sqft property and his FAR/setback/floor plate/building height workings.

### Step 1 — Locate Existing Files

Search Drive for `name contains 'Benson'` or `name contains '15000'`.

Known files (as of May 2026):
- `20260506 Benso town Javad 15000 sqft – Survey Drawing.pdf` — ID `1cAupxip00ZDJBqZAKxJqa-G5BnfOr9N9` — survey drawing only
- **No FAR analysis or floor plate drawings found** in Drive or Gmail from Bhuvanesh

### Step 2 — If Files Exist → Share with User

If you find FAR/setback files from Bhuvanesh: share with user via PDF + DWG (as requested), file in Drive, and send links.

### Step 3 — If Files Not in Drive → WhatsApp Reminder

Draft WhatsApp message to Bhuvanesh asking him to share the workings:
```
Hi Bhuvanesh, following up on the Benson Town Abdullah property (~15,000 sqft) — 
can you please share the FAR analysis, setback norms, building height and floor plate 
workings you've done? Need it for internal review before we proceed. PDF and DWG ideally. Thank you!
```

**WhatsApp deep-link encoding:** replace every `&` in message body with `%2526` (double-encoded), then URL-encode normally. Format: `https://wa.me/?phone=...&text=...`

Bhuvanesh contact: `bk@findingform.design` (email — no phone found in contacts as of May 2026; check contacts sheet row for phone)