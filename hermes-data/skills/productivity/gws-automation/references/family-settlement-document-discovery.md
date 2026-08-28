# Family Settlement / Estate Document Discovery

**Class of task:** User asks to find a specific letter/document between family members (identified by initials) around a known family settlement date.

**Worked example:** June 2026 session — user asked for "letter from NDR to MRR about a loan around the family settlement date."

## Step 1: Establish the Anchor Date

The user will usually name the event: "family settlement deed was on the 20th in August 2025." The anchor is August 20, 2025. However, the actual executed Family Arrangement Deed may be dated **August 6, 2025** (same week). Search window: **anchor ±10 days** (Aug 10–Aug 30, 2025, but also check Aug 6).

## Step 2: Know the Initials

| Initials | Person | Notes |
|----------|--------|-------|
| NDR | Nishant Ranka | User himself |
| MRR | Mamata Ranjeeth Rathod | Sister (Mamta) |
| KDR | Kanta Ranka | Mother |
| DDR | Dharmesh Ranka | Brother |
| MDR | Manish Ranka | Brother |

These initials appear in filenames throughout Drive. When searching, use all-caps with no spaces: `NDR`, `MRR`, `KDR`, etc.

## Step 3: Search Strategy

### Primary search — Family Settlement folder

The Family Settlement documents live in two sibling folders under `Family/`:
- **Family Settlement - Final - 2025** — `145edzJXYcE4bHas77K59vPqT3ruvtOzx` — contains signed PDFs (Family Arrangement Deed, Release Deeds, SPAs, NOC letters)
- **Final Settlement Docs** — `1zKBSShukqJ5JR6rS7emzrqv8yqe6YvvB` — contains draft/more detailed Google Docs (loan letters, succession petitions, release deed drafts, payment acknowledgements, valuation sheets)

Search **both** folders, as the document may be in either one.

### Drive-wide search

If not in the family settlement folders, search Drive by:
```python
query = f"(name contains 'NDR' or name contains 'ndr') and (name contains 'MRR' or name contains 'mrr' or name contains 'Mamta' or name contains 'Mamata') and trashed=false"
```

Look for patterns like `Ltr NDR2MRR ...` or `Ltr MRR2NDR ...` — these follow a consistent naming convention for family correspondence.

### Filename patterns to expect

Standard naming: `YYYYMMDD` prefix + `Ltr <Sender>2<Recipient> <Purpose>`
- `Ltr NDR2MRR For Balance Payment` — Nishant to Mamata about balance settlement
- `Ltr MRR 2 DRAPL Board Ack Loan Repayment` — Mamata to company about loan
- `Pymt Ack MRR2NDR` — Payment acknowledgement from Mamata to Nishant
- `Ltr DR Heirs to DRAPL Board for Loan to MRR` — All heirs about loan allocation

### Full-text search in Drive

For documents that don't match filename patterns, search the actual content:
```python
query = f"fullText contains 'NDR' and fullText contains 'MRR' and fullText contains 'loan'"
# Or more targeted:
query = f"fullText contains 'family arrangement' and fullText contains 'Mamta'"
```

## Step 4: Verify Content

Once a candidate is found, **read the content** using the appropriate method:
- Google Docs: `export(fileId, mimeType='text/plain')`
- PDFs: `get_media` → `fitz.open()` or `pdftoppm` + `tesseract`
- Check the **date**, **sender**, **recipient**, **amount**, and **terms**

If the doc is a PDF from 2025, it's likely text-extractable via `fitz`.

## Step 5: Present to User

Show:
- Document link
- Date
- From → To
- Key details (amount paid, amount owed, deadlines, interest rates)
- Folder location

Then ask: "Is this the one?"

## Key Folders Reference (June 2026)

| Folder | ID | Contents |
|--------|----|----------|
| Family | `16NAzSHe0cnYhN1uf43kKlqi_qjNlHVYJ` | Root — contains both settlement subfolders |
| Family Settlement - Final - 2025 | `145edzJXYcE4bHas77K59vPqT3ruvtOzx` | Signed PDFs: Family Arrangement Deed (Aug 6), Release Deeds (Aug 20), NOC letters, SPAs |
| Final Settlement Docs | `1zKBSShukqJ5JR6rS7emzrqv8yqe6YvvB` | Google Docs drafts: loan letters, succession petitions, release deed drafts, payment acks, interest calculations, asset valuations, Master Document Checklist |

## Common Pitfalls

- **Multiple folders exist** — the document may be in "Final Settlement Docs" (Google Docs) rather than "Family Settlement - Final - 2025" (PDFs). Check both.
- **Date in filename may differ from content date** — Family Arrangement Deed shows `20250806` in filename but user said "20th August." The actual deed was signed Aug 6; release deeds were Aug 20.
- **Initials appear in inconsistent order** — `NDR2MRR` vs `MRR2NDR` vs `DR Heirs to...`. Search all permutations.
- **Loan documents may be titled "Letter" not "Loan"** — the key document was `Ltr NDR2MRR For Balance Payment`, which doesn't say "loan" in the name but is about a loan settlement.
- **PDF documents in this folder may be image-based** (scanned signatures on registered deeds) — use `pdftoppm` + `tesseract` or `vision_analyze` for text extraction.
- **The Drive search `q` parameter needs single quotes** — when building a query with initials, use `chr(39)` for single quotes inside f-strings passed to subprocess.
