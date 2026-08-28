---
name: travel-document-retrieval
description: Retrieve travel documents from Google Drive (itineraries, tickets, visas), extract flight details, and facilitate web check-in. Triggered when user asks about flight details, check-in, booking reference, or requests travel document retrieval.
trigger: "flight details, web check-in, check in online, flight itinerary, booking ref, PNR, retrieve travel document, airport, boarding"
---

# Travel Document Retrieval

## Bali May 2026 Trip — Fixed Folder IDs

| Folder | ID |
|--------|----|
| Trip folder | `1JvrSZpIeToZT6KBxz4pNDM3GS7-fevWU` |
| Temp (discard after trip) | `1kXZTjrfcsfNBli1wPHZCAcJLha1Uvsle` |
| Permanent (keep long term) | `1mZbVBUC42HX5HzrBpLw5y1_nmkypbaDC` |
| Receipts subfolder | `1M2PuL6Yp-34Es-6TaQfNiUec4b-Vb0cD` |

**Known itinerary files in Permanent folder:**
| Passenger | File ID |
|-----------|---------|
| Nishant | `1-UXKH9R7xEzxSEeUfjnGlxEKSxxtxMWi` |
| Roshini | `1Dor-ERHQZ9jzDn85CFGYPbNNR_-Kk-5T` |
| Ruhaan | `1z8ASSCv7ERw6JiN5753N13O7KkrK7wBn` |
| Rivaan | `1K5EiV3VhzIwzyft4Zn88lGIo9pJBxwm6` |

## Retrieving Itinerary PDFs from Drive

```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

TELEGRAM_ID = "ndr"
SCOPES = ['https://www.googleapis.com/auth/drive']

creds = Credentials.from_authorized_user_file(f"/data/hermes/users/{TELEGRAM_ID}/the gws-vault daemon (no token files exist on disk — see api-references/google-workspace-api/references/token-access-canonical.md)", SCOPES)
if creds.expired:
    from google.auth.transport.requests import Request
    creds.refresh(Request())
drive = build("drive", "v3", credentials=creds)

# Download a PDF file by ID
file_id = "1-UXKH9R7xEzxSEeUfjnGlxEKSxxtxMWi"
fh = io.FileIO('/tmp/flight.pdf', 'wb')
request = drive.files().get_media(fileId=file_id)
downloader = MediaIoBaseDownload(fh, request)
done = False
while not done:
    status, done = downloader.next_chunk()
```

## Extracting Text from Downloaded PDFs

Use `fitz` (PyMuPDF) to extract text:

```python
import fitz
doc = fitz.open('/tmp/flight.pdf')
for page in doc:
    print(page.get_text())
```

Key fields to extract from Malaysia Airlines e-ticket receipts:
- **Booking ref / PNR** — look for `Booking ref:` or `PNR:` in the text
- **Passenger name**
- **Flight numbers, dates, departure/arrival times, terminals**
- **Class of travel**
- **Booking status** (look for `OK` = confirmed)
- **Baggage allowance**

## Web Check-in

### Malaysia Airlines
**Check-in URL:** `https://www.malaysiaairlines.com/en_US/manage/check-in`

**Required inputs:**
- **Booking Reference (PNR):** found in itinerary as `Booking ref: DVAZVS`
- **Last Name:** extracted from itinerary (e.g. `RANKA`)

**Common issues:**
- Direct check-in URL sometimes returns "Campaign Expired or Page Not Found" — try the homepage first, then navigate to check-in
- If the site is down, provide the user with the direct URL + PNR + last name for manual use
- Check-in counters close **60 minutes before departure**; gates close **30 minutes before**

### Singapore Airlines
**Check-in URL:** `https://www.singaporeair.com/en_UK/check-in/`
Same pattern — booking reference (6-character alphanumeric) + last name.

### IndiGo / Air India / SpiceJet
Usually no online check-in for domestic Indian flights — advise airport counter check-in.

## After Retrieval — Create HTML Summary

When user asks for flight details or web check-in, after extracting info from itineraries, create an HTML summary file with:
- PNR prominently displayed
- All flight segments with times, terminals, class
- Copy-paste boxes for booking ref and last name
- Direct link to airline check-in page

Upload to Drive and share the link with the user. Do NOT send local file paths via Telegram — always use Drive links.

## Bali May 2026 — Known Flight Summary (from itineraries, May 2026)

**Outbound (May 9):**
- MH193: BLR 00:40 → KUL 07:30 (Terminal 2 → Terminal 1, Economy M)
- MH715: KUL 09:00 → DPS 12:05 (Terminal 1 → Terminal I, Economy M)
- All 4 passengers confirmed OK, 4×35kg baggage

**Return (May 16):**
- MH850: DPS 16:25 → KUL 19:35 (Terminal I → Terminal 1, Business B)
- MH192: KUL 22:00 → BLR 23:45 (Terminal 1 → Terminal 2, Business B)
- All 4 passengers confirmed OK, 4×35kg baggage

**Common across all passengers:** PNR `DVAZVS`, ticket series `232 2484374xxx`, paid via HDFC card ending 1506.