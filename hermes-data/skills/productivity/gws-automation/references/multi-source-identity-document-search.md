# Multi-Source Identity Document Search (Drive + Gmail)

Find ALL identity documents (OCI, PAN, Aadhaar, Passport, Photo, Visa, DL) for specific individuals by searching both Google Drive and Gmail systematically.

## When to use

- User asks: "Find all identity documents for [person name] across all my drives and emails"
- User needs to locate OCI/PAN/Aadhaar/passport for a specific person for RERA, project finance, or KYC

## Phase 1 — Drive Search

Search Drive with keyword + name combinations:
```python
q = "(name contains 'OCI' or name contains 'PAN' or name contains 'Aadhaar' or name contains 'Passport' or name contains 'Photo') and (name contains '[LastName]' or name contains '[FirstName]') and trashed=false"
```

Page through results and capture parent folder names for each file found.

## Phase 2 — Gmail Search

Search with keyword + sender combinations:
```python
queries = [
    '(from:sender@email.com) (OCI OR Aadhaar OR PAN OR passport OR identity)',
    '"[Person Name]" (OCI OR Aadhaar OR PAN)',
]
```

For each matching email, extract attachment filenames and generate a Gmail inbox link:
```
https://mail.google.com/mail/u/0/#inbox/{message_id}
```

## Phase 3 — Compile

Return a structured table: Source (Drive/Email) | File | Location (Folder/Email Subject) | Link | Status

## Pitfalls

- **Scanned identity PDFs** are image-only. Use `pdfimages` to extract embedded JPEGs, then OCR. See `ocr-and-documents` → `references/pdf-text-removal-via-image-extraction.md`.
- **Split OCI docs** — only front may exist; ask about back.
- **Gmail limit** — max 100 results per query.
- **Duplicate files** across folders — list ALL locations.
- **Phone photos** — search `.jpg/.png` too, not just PDFs. Include `photo` keyword.
- **Name variants** — check alternate spellings (Raghunath vs Raghu, Farida vs Fareeda, maiden vs married names).
