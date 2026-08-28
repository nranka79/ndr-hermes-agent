# Drive Contact Address Retrieval

When a user provides a contact name (e.g. emergency contact, neighbour, relative) but no address or phone, you can find missing details by searching Drive for that person's identity documents.

## Workflow

1. **Search Drive** using `gws_auth` drive service with `fullText contains` queries:
```python
results = service.files().list(
    q="fullText contains 'Kishan' and fullText contains 'Nair'",
    pageSize=20, fields='files(id, name, mimeType)',
    supportsAllDrives=True, includeItemsFromAllDrives=True
).execute()
```

2. **Look for identity documents** — PAN card, Aadhaar card PDFs (often named `{Name} Pan and Adhaar.pdf`).

3. **Download & OCR** — use `pdftoppm` to convert PDF pages to PNG, then `vision_analyze` to extract text:
```bash
pdftoppm -png -r 200 doc.pdf /tmp/prefix
```

4. **Extract** full name (correcting the user's phonetic approximation), address, phone.

## Document types
- "Self Attested Pan and Adhaar.pdf" — has full address
- Rental/lease agreements, property documents listing the person

## Pitfalls
- **Name spelling**: User may say "Kichen Nair" when document says "Kishan Murjani Nair" — use documented spelling.
- **Scanned PDF**: `pdftotext` returns empty; always export to image first.
- **Cross-verify** address consistency across multiple documents.
