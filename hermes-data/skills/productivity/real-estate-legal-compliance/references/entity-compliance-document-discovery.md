# Entity Compliance Document Discovery (GST, PAN, Registration Certificates)

When a DRAAS team member asks you to find a compliance document for a **business entity** (Partnership Firm, Pvt Ltd, LLP, Trust) — GST certificate, PAN card, Partnership Registration certificate — follow this systematic search pattern.

## Search Order

### 1. Drive — Name Search (fastest hit rate)

Search for the entity's name combined with document type:

```python
# GST cert
call("drive_search", query="name contains 'GST' and name contains 'Hurestic'", raw_query=True, max=20)

# PAN card / PAN number
call("drive_search", query="fullText contains 'AAKFH0675'", raw_query=True, max=20)

# Registration cert
call("drive_search", query="name contains 'regcert'", raw_query=True, max=20)
```

**Known naming patterns in DRAAS Drive:**
| Document | Likely Filename Pattern |
|----------|------------------------|
| GST Certificate | `*GST*Certificate*.pdf`, `*GST*Registration*.pdf` |
| PAN Card | `*PAN*.pdf`, `*PAN*.jpg`, `*PAN*.png` |
| Partnership Registration | `regcert.pdf`, `Form C*.pdf`, `Form D*.pdf` |
| Partnership Deed | `*Partnership Deed*.pdf` |

**False positive trap:** Generic filenames like `GST Registration.pdf`, `GST Registration (1).pdf` often belong to other entities (Westbury Hospitality, DRA Realty). Always verify by opening/reading before reporting success.

### 2. Drive — Entity Folder Contents

If a dedicated entity folder exists (e.g., `Hurestic`, `Hurestic Cloud Services`), list its contents:

```python
# Find the folder first
call("drive_search", query="name = 'Hurestic' and mimeType = 'application/vnd.google-apps.folder'", raw_query=True, max=10)

# Then list contents
call("drive_search", query="'FOLDER_ID' in parents", raw_query=True, max=50)
```

Entity folders often contain the cert under a non-obvious name (e.g., `regcert.pdf` inside an old startup folder). Don't skip this even if a name search returned nothing.

### 3. Compliance Tracker Sheet

DRAAS maintains a **Entity Statutory And Legal Compliance_Tracker** sheet with GSTIN, PAN, and filing status for all entities:

```python
# Check the sheet for the entity
call("sheets_get", sheet_id="1QJC8Ep-TznhWOtJG91cgoU2NXqb_lPp0d7wKgO174JI", range="A1:Z50")
```

The sheet confirms: GST number, PAN number, filing status — but usually does **NOT** contain a direct Drive link to the certificate file. It tells you whether the certificate *should* exist, not where it is.

### 4. Email — Attachments Search

The GST certificate may have been shared as an email attachment:

```python
call("gmail_search", query="Hurestic GST has:attachment", max=10)
call("gmail_search", query="29AAKFHO675G1Z6", max=10)
```

Key email senders for compliance documents: the entity's own accountant, Eshwari (echamundeshwari@draas.com), Abhishek Kaushik, the registering lawyer.

### 5. Check Generic GST Registration PDFs

Some certs are stored under generic filenames. Download and read each:

```bash
# Download candidate
pdftotext /tmp/gst_candidate.pdf /tmp/gst_candidate.txt
grep -i "hurestic\|29AAKFHO" /tmp/gst_candidate.txt
```

### 6. GST Portal (Last Resort)

If the cert isn't in Drive or email, it must be downloaded from the GST portal:

1. Go to https://www.gst.gov.in/
2. Login with the entity's GST credentials
3. Navigate: **Services → Registration → Certificate of Registration**
4. Download PDF

**You need separate login credentials for each entity's GST account.** If you don't have them, ask the user.

## Known Entity Data (DRAAS)

| Entity | Type | GSTIN | PAN | Drive Notes |
|--------|------|-------|-----|-------------|
| Hurestic Cloud Services | Partnership Firm | 29AAKFHO675G1Z6 | AAKFH0675G | No cert file found in Drive (Jul 2026). Must download from GST portal. |
| DRA Realty Pvt Ltd | Pvt Ltd | 29AAACW5838P1ZH | AAACW5838P | Cert exists: `DRA REALTY PRIVATE LIMITED GST CERTIFICATE.pdf` |
| Ranka Holdings | — | — | — | Cert exists: `Ranka Holdings Gst Certificate.pdf` |
| Westbury Hospitality | Pvt Ltd | 29AAACW5838P1ZH | — | `Westbury Hospitality GST Certificate.pdf` |

## Pitfalls

- **Entity vs startup confusion:** DRAAS has both an old "Hurestic" tech startup folder (2016-2020, with regcert.pdf, partnership deeds) and a newer "Hurestic Cloud Services" partnership firm. The GST cert for the partnership may be under neither.
- **Partnership Registration ≠ GST Certificate:** `regcert.pdf` is Form C under the Indian Partnership Act, NOT a GST certificate. They look different — GST cert has the GSTIN in large text, partnership reg has the firm's registration number.
- **Scanned PDFs may have no text layer:** Use vision_analyze on rendered PNG pages to confirm which entity a document belongs to.
- **No token in vault for this user:** When searching on behalf of someone who isn't Nishant (e.g., Bharat), the `google-draas` service still works if the token exists for Nishant's account. But the entity documents may be in a different user's Drive.
