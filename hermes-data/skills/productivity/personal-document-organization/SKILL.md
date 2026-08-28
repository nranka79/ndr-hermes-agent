---
name: personal-document-organization
description: "Classify, rename, and file personal documents (Form 16s, salary slips, financial docs, tax records) into the user's personal folder structure under /data/hermes/users/ndr/personal/. Covers identification of issuing entity, consistent naming conventions, and folder-creation-on-demand."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [documents, organization, filing, personal, financial, tax, form16]
    related_skills: [ocr-and-documents, messaging-links, medical-document-processing]
---

# Personal Document Organization

Trigger: user uploads PDFs/files and says "rename", "put under personal", "organize these", "file these", "store these", or explicitly names a folder destination.

## Workflow

### 1. Extract content to identify the documents

Use `ocr-and-documents` skill — pymupdf for text-based PDFs (Form 16s, salary slips), marker-pdf for scanned docs.

```bash
/opt/hermes/.venv/bin/python3 -c "
import pymupdf
doc = pymupdf.open('path/to/document.pdf')
for page in doc:
    print(page.get_text())
"
```

Extract key identifiers:
- **Employer / issuing entity name** (from the header/first page)
- **Document type** (Form 16 Part A vs Part B, salary slip, bank statement, etc.)
- **Assessment year / financial year** (e.g. "2026-27")
- **Certificate number** (Form 16: matches Part A ↔ Part B to confirm they belong together)
- **Employee name** (verify it's the user's document)

### 2. Form 16 specific knowledge

**Part A** contains:
- Employer name, PAN, TAN
- Employee PAN, name, address
- Assessment Year
- Quarter-wise salary paid and TDS deducted
- TDS deposit details (challan, BSR code, dates)
- Certifying authority signature (Dharmesh Ranka for DRA Group cos)

**Part B** (Annexure) contains:
- Salary breakup (basic, HRA, perquisites, etc.)
- Section 16 deductions (standard deduction, professional tax)
- Chapter VI-A deductions (80C, 80D, etc.)
- Tax computation

**Pairing rule**: Part A and Part B share the same Certificate Number (e.g. AONGJMA, AOLLXIA). Always verify they match before filing as a set.

### 3. Rename consistently

Format: `{serial}_{IssuingEntity}_{DocTypePart}_{AY}.pdf`

Examples:
```
01_DRA_Projects_Form16_PartA_AY2026-27.pdf
01_DRA_Projects_Form16_PartB_AY2026-27.pdf
02_Southcity_Properties_Form16_PartA_AY2026-27.pdf
```

Use leading zeros (01, 02) to order multiple employers by salary amount or alphabetically.

### 4. Determine folder path

Default base: `/data/hermes/users/ndr/personal/`

Subfolder conventions from observed user preference:
- Income tax returns / Form 16s → `personal/income-tax/AY {YYYY-YY}/`
- Salary slips → `personal/salary-slips/{AY}/`
- Bank statements → `personal/financial/bank-statements/{year}/`
- Insurance docs → `personal/insurance/`
- Property docs → `personal/property/`

**If the target subfolder doesn't exist, create it** — don't ask for permission:
```bash
mkdir -p "/data/hermes/users/ndr/personal/income-tax/AY 2026-27"
```

### 5. Place the files

Copy (or move, if the cache originals are disposable) the renamed files to the target directory:
```bash
cp /data/hermes/cache/documents/{original}.pdf /data/hermes/users/ndr/personal/{subfolder}/{new_name}.pdf
```

### 6. Report to the user

Present a concise table:
```
| # | File | Company |
|---|------|---------|
| 1 | 01_DRA_Projects_Form16_PartA_... | DRA PROJECTS PRIVATE LIMITED |
```

Include the answers they asked about the documents (which company, salary amount, etc.).

### 7. Cross-skill handoff: Attaching filed documents to an email draft

The user may follow up with "now attach those to [Name]'s email reply." This is a
predictable two-step workflow: file first, then attach. When the user mentions
attaching to an email **before** filing:

1. **File the documents first** (Steps 1-6 above) — this gives you clean, permanent paths.
2. **Then hand off to the `email-drafter` skill** for the draft. The `email-drafter`
   skill's Pitfall P8 covers threaded reply-all with MIME attachments.

Key: use the **renamed, permanent paths** from the personal folder as the attachment
source, not the cache paths. This way when the user later adds more documents (e.g.
"O3 Infotech Form 16 arrives, add it to the same draft"), you can:
- File the new document in the same personal folder (same naming convention)
- Attach it to the existing draft
- Update the draft body to reflect the new addition

**Do NOT move the cache files** — cache files have hash-based names and may be needed
for diagnostic purposes. Always `COPY` (or reference) from the personal folder.

**Related skill:** `medical-document-processing` covers the Google-Drive-filing + calendar + WhatsApp workflow for medical documents (discharge summaries, lab reports, prescriptions). Local financial/family documents (this skill) complement medical docs on Drive (that skill).

For the `email-drafter` handoff, the expected pattern is:
```
1. User: "file these 4 Form 16s and then reply to Rohit's email with them attached"
2. Your action: file them (this skill), note the permanent paths
3. Your action: compose a reply-all draft with all 4 PDFs attached (email-drafter skill, P8)
4. Report: "Draft ready with [N] attachments in thread [subject]."
```

If the O3 Infotech Form 16 (or any other) is pending, mention it in the draft body
("O3 Infotech Form 16 will follow once received") and tell the user you'll update
the draft when the remaining document arrives — attaching it to both the folder and
the draft.

## Pitfalls

- **vision_analyze rejects PDFs** — `vision_analyze` only accepts real image files, not PDFs. Use pymupdf (text extraction) or pdftoppm (convert PDF pages to PNGs first) instead.
- **pymupdf may not be installed** — install via `uv pip install pymupdf` if missing. The venv is at `/opt/hermes/.venv/bin/python3`.
- **Cache files vs permanent storage** — the user's uploaded files land in `/data/hermes/cache/documents/` with hash-based names. Always COPY (not move) to the personal folder, so the cache isn't disrupted.
- **Part A ↔ Part B mismatches** — a user may upload 4 files (2 Part A + 2 Part B) from 2 employers. Always cross-reference Certificate Numbers to pair them correctly. An orphaned Part B without matching Part A (or vice versa) should be flagged to the user.
- **Multiple employers in one year** — cross-check: does the user have multiple Part A certificates from different employers in the same AY? Report both sets separately.
