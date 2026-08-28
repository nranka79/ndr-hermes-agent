# Lalbagh / Annipura 33 Guntas Land Proposal — 2026-08-26

## Session: Creating DRA Land Proposal #54965107

### Pitfalls Encountered

#### 1. `cf_name` (Proposal Brief) required in `field_values`, NOT just `name` parameter

The `create_lead` tool for Pipeline 519 (DRA Land Proposal) accepts a `name` parameter for the record
title AND requires `cf_name` as a separate field_value. The first attempt failed with:

> Draft 102881613 failed: Validation failed: Required fields not present: Proposal Brief

**Fix:** Always pass BOTH:
```python
create_lead(
    pipeline_id=519,
    name="Location - Size - via Broker",
    field_values={
        "cf_name": "Location - Size - via Broker",  # same value as name
        # ... other fields
    }
)
```

The `name` parameter and `cf_name` are architecturally distinct fields on the Kelsa record.
One does not satisfy the other.

#### 2. S3 presigned POST 25 MB upload limit

The presigned POST returned by `get_upload_url` enforces:
```
content-length-range [0, 26214400]  →  25 MB max
```

A 33 MB scanned PDF returned HTTP 400 `EntityTooLarge`.

**Fix:** Compress with Ghostscript before uploading:
```bash
gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/screen \
  -dNOPAUSE -dQUIET -dBATCH \
  -sOutputFile=compressed.pdf input.pdf
```

Result: 33 MB → 1.8 MB (95% compression) with `/screen` setting.
For better quality on scanned documents, use `/ebook` instead.

#### 3. Downloading native PDFs from Google Drive for Kelsa attachments

Google Drive native PDFs (not Google Docs exports) need `get_media()` not `export()`:

```python
from tools.gws_auth import build_service
svc = build_service('drive', 'v3', service_name='google-draas')

# get_media() for binary files (PDFs, images, etc.)
request = svc.files().get_media(fileId=file_id)
pdf_bytes = request.execute()

# Export only works for Google Docs Editors files
# .export(fileId=..., mimeType='application/pdf') → 403 for native PDFs
```

The `get_media()` endpoint returns raw bytes that can be written to disk or
uploaded directly to S3 via the Kelsa attachment flow.

#### 4. Rahul (Vinod Kumar Das) Kelsa user resolution

- Email: vkdas@draas.com
- Display name in Google Contacts: "Vinod Kumar Das (Rahul)"
- Kelsa user ID in DRA Land Proposal pipeline: **31363**
- Kelsa display name: "Vinod Kumar"
- Found via `list_users(pipeline_id=519, query="vinod")` — searching by "Rahul" returns nothing
- Present in Land Proposal (519) pipeline but NOT in PO-WO Issuing (537)

### Property Details Extracted

| Field | Value |
|---|---|
| Location | Sy. No. 15, Annipura Village, Kasaba Hobli, Bengaluru North Taluk |
| Boundaries | E: Sy.10/1, W: Petrol Bunk, N: Sy.67/2, S: Hosur Highway (Lalbagh) Road |
| Extent | 1a 33½g (out of 12a 19g total) ≈ 1.8375 acres ≈ 80,042 sqft |
| Zone | Commercial (33½g converted to non-agricultural — 200ft × 400ft) |
| Original Grant | Inam land → Kolada Matt Mahasamsthana (religious institution) |
| Occupant | N. Muniswamy S/o Nanjappa (d. 2018) → widow Muniramma (d. 2024) → 5 legal heirs |
| Price | ₹18,000/sqft quoted by Etesh Reddy (contact via VK Reddy) |
| Title Status | Pending before Special DC Bengaluru North (INA.CR.No.13/1998-99) |
| HC Order | WP 18989/2007(LR) — Justice Ravi Malimath, 20-02-2017 — set aside on Rule 17 procedural grounds, remanded with 3-month deadline (7+ years overdue) |
