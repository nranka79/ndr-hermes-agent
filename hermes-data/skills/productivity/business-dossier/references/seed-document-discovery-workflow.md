# Seed Document → Drive+Gmail Discovery Workflow

## When to Use

User shares a **single document** (legal opinion, title report, facts compilation, due diligence report) and asks you to "find all related documents on Drive and Gmail." The document serves as the seed — its text contains the identifiers (names, survey numbers, case references, document references) that drive the search.

## Worked Example: Binnamangala / Bin Mangala (Jul 2026)

### Step 1 — Download the Seed Document

```python
from googleapiclient.http import MediaIoBaseDownload

drive = build_service('drive', 'v3')
file_id = '0B1Oc8cSaJXPGQ0dkLWtfOWVQSE5TUGpyeUdVQXVYWld6eUd3'
local_path = '/tmp/binnamangala_legal_opinion.pdf'

request = drive.files().get_media(fileId=file_id)
with open(local_path, 'wb') as f:
    downloader = MediaIoBaseDownload(f, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
```

### Step 2 — Check & Extract Text

```bash
# First check if text-based
pdftotext /tmp/doc.pdf /tmp/doc.txt
wc -c /tmp/doc.txt  # 0 bytes = scanned, >0 bytes = text-based
```

If scanned (0 bytes):

```bash
# Convert each page to JPEG at 300 DPI
mkdir -p /tmp/pages
pdftoppm -jpeg -r 300 /tmp/doc.pdf /tmp/pages/page
# → produces page-1.jpg, page-2.jpg, etc.
```

Then OCR each page with `vision_analyze`:

```python
# In parallel batches of 4
from hermes_tools import vision_analyze

pages = [f'/tmp/pages/page-{i}.jpg' for i in range(1, total_pages+1)]
for i in range(0, len(pages), 4):
    batch = pages[i:i+4]
    for page in batch:
        vision_analyze(
            image_url=page,
            question="Extract ALL text. OCR everything visible."
        )
```

**Important:** `pdftotext` returning 0 bytes is the definitive check that a PDF is scanned. Do NOT skip this check — some PDFs have mixed content (text + scanned images).

### Step 3 — Extract Identifiers

From the OCR output, extract every term that could match a Drive file or Gmail message:

| Category | Examples from Binnamangala |
|----------|---------------------------|
| **Property** | Binnamangala, Binmangala, Birmangala, Binnamagala |
| **Survey Nos** | Sy. 151, 152, 153, 1/1, Sy.151, Sy.152, etc. |
| **Locality** | Indiranagar I Stage, Rangappa Garden, Narayanappa Garden, Manavarthi Kaval |
| **Municipal No** | Municipal No.1, No. 1 Binnamangala |
| **Extent** | 12240 sq.ft, 14281 sq.ft, 4 acres 13 guntas |
| **Landowners** | Chinnaraje Ammal, M. Ramaswamy Reddy, R. Mahalingam Reddy, R. Lalitha, R. Vijaya Kumar Reddy |
| **Developer/Entity** | Arya Developers, Dinesh Ranka, Kanta D. Ranka, Dinesh D. Ranka |
| **Intermediaries** | P. Dayananda Pai, M. Devraj, Dayanand Pai |
| **Advocates/Firms** | Prashanth Acharya, Muniyappa Advocate, CrestLaw Partners, Jacob, Pingal Khan, Harish Sasikumar, Ashlar Law, K M Harsha, Ashwin Bellad, Balaraj R |
| **Document refs** | JDA 07.09.1995, GPA 25.03.1995, GPA 09.02.1996, Supplemental Agreement 07.02.1996, Supplemental Agreement 07.09.1995 |
| **Case refs** | OS 6889/1998, OS 2095/2002, AC 10017/1984, Misc 240/2012, RFA 347/1993, OS 7005/2000 |
| **Authority refs** | BDA Resolution 485, BBMP License 94/96-97, Sanctioned Building Plan 94/96-97 |
| **Dates** | 28.08.1952, 01.11.1973, 26.05.1974, 29.04.1986, 07.09.1995, etc. |
| **Key individuals** | Aamir Khan (aamirkhan@me.com) — collaborator on early workings |

### Step 4 — Drive Search

Use `fullText contains` queries with each identifier:

```python
drive = build_service('drive', 'v3')
all_files = {}
seen_ids = set()

for term in all_identifiers:
    try:
        results = drive.files().list(
            q=f"fullText contains '{term}' and trashed=false",
            pageSize=100,
            fields='files(id, name, mimeType, owners, webViewLink, modifiedTime, size)'
        ).execute()
        for f in results.get('files', []):
            if f['id'] not in seen_ids:
                seen_ids.add(f['id'])
                all_files[f['id']] = f
    except:
        pass  # Some terms may cause API errors — skip and continue
```

**Important:**
- Escape single quotes in terms by using double quotes or raw strings
- `fullText contains` searches file name AND content (for Google Docs, PDFs with text layer)
- For scanned PDFs, the content is NOT searchable — rely on file names and parent folder names
- Deduplicate by file ID — same file matches multiple terms

### Step 5 — Gmail Search

```python
gmail = build_service('gmail', 'v1')
all_msgs = {}
seen_ids = set()

# Use the 10-15 most distinctive terms
for term in distinctive_identifiers:
    try:
        results = gmail.users().messages().list(
            userId='me', q=term, maxResults=50
        ).execute()
        for m in results.get('messages', []):
            if m['id'] not in seen_ids:
                seen_ids.add(m['id'])
                msg = gmail.users().messages().get(
                    userId='me', id=m['id'],
                    format='metadata',
                    metadataHeaders=['Subject','From','Date','To']
                ).execute()
                headers = {h['name']: h['value'] for h in msg['payload']['headers']}
                all_msgs[m['id']] = {
                    'subject': headers.get('Subject', ''),
                    'from': headers.get('From', ''),
                    'date': headers.get('Date', ''),
                    'snippet': msg.get('snippet', '')[:150]
                }
    except:
        pass
```

**Gmail search tips:**
- Use quoted phrases for multi-word terms: `'"OS 6889"'`, `'"Chinnaraje Ammal"'`
- Name variants matter: search both `Binnamangala` and `Binmangala` and `Birmangala`
- Sort results by date — recent emails tell the current status
- Look for attachments in emails — documents shared via email may NOT be on Drive
- Thread subjects reveal the deal stage: "Legal Opinion", "JDA", "List of Documents", "BDA NoC", "Payment Receipts"

### Step 6 — Cross-Reference & Gap Analysis

Create a list of documents the seed document **references** that may or may not exist on Drive:

```
# From Binnamangala legal opinion:
REFERENCED IN OPINION          | ON DRIVE?  | NOTES
JDA 07.09.1995                 | ❌ NOT FOUND | May exist physically
GPA 25.03.1995                 | ❌ NOT FOUND |
GPA 09.02.1996                 | ❌ NOT FOUND |
Supp. Agreement 07.02.1996     | ❌ NOT FOUND |
Sale Deed 28.08.1952           | ❌ NOT FOUND | Original purchase
Khatha Cert 11.01.1996         | ❌ NOT FOUND |
BBMP License 94/96-97          | ❌ NOT FOUND |
Sanctioned Plan 94/96-97       | ❌ NOT FOUND |
Os 6889/1998 docs              | ❌ NOT FOUND | Dismissed case
```

Documents that ARE found may be in unexpected locations:
- Same subject in different folders (Legal folder vs Binnamangala folder vs root)
- Owned by different users (ndr, admin2, sales1, crm)
- Duplicate copies with slightly different names

### Step 7 — Compile HTML Inventory Report

Upload to Drive `temp.tmp` folder for the user to review. Structure:

```
1. Property Summary Card (from seed document)
2. Section A: Core Property Documents Found (tables by type)
   - Legal Opinions (with links)
   - JDAs, GPAs, Supplemental Agreements
   - Court Documents
   - Revenue / Khata / EC Documents
   - Payment / Financial Documents
3. Section B: Key Emails Found (chronological table)
4. Section C: Entity/Firm Documents (not property-specific)
5. Section D: Separate-Property Documents (under same entity, different property)
6. Section E: Referenced-but-Missing Documents (GAP ANALYSIS)
7. Section F: Current Drive Organization
```

Use the `google-doc-formatting-template` style for clean HTML/CSS — or build a self-contained HTML timeline-style document (see `business-dossier` SKILL.md Phase 6b).

## Common Pitfalls

| Pitfall | Why It Happens | How To Avoid |
|---------|---------------|--------------|
| OCR is incomplete or garbled | Scanned legal docs use small fonts, faded ink, or Kannada/English mix | Use `vision_analyze` with explicit "OCR everything" prompt; if one model misses, try another |
| 100+ irrelevant Drive results | Broad terms match unrelated files | Filter: check if file name contains property-specific term; check parent folder name |
| Key docs not found by `fullText` | They're scanned PDFs — no text layer | Search by file name patterns instead (`name contains 'Binnamangala'`) |
| Same email thread has 50+ messages | Gmail threading groups replies | Take the most informative message per thread (the one with the attachment or the final response) |
| No results for exact case number | Gmail search doesn't always index OCR'd PDF attachments | Use the human-readable subject line keywords instead |
| "Dayananda Pai" docs seem unrelated | He's the purchaser from 1986 — his docs are part of the property's sale history | Include ALL party names, even historical ones |

## Results from Binnamangala Session (Jul 2026)

- **Drive:** 141 unique files from targeted Binnamangala-specific search terms
- **Gmail:** 116 unique emails spanning 2013-2026
- **Core Binnamangala docs on Drive:** 6 (in Binnamangala folder + Legal folder)
- **Dayananda Pai docs:** 7+ (folder of payment receipts)
- **Arya Developers firm docs:** 10 (reconstitution, release deed, partnership deeds)
- **Elegant Springdale docs:** 12+ (separate property under same entity)
- **Referenced but missing:** 13 documents from the legal opinion not on Drive
