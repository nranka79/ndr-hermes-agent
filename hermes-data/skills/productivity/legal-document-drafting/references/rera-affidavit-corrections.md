# RERA Affidavit — Known Corrections & Pitfalls

## BANK AFFIDAVIT — 70% Account vs IFSC Mixup

**The most common error**: The 70% Designated Account Number field gets filled with the IFSC code instead of the actual account number.

```
❌ Account Number: KKBK0000431   ← THIS IS AN IFSC, NOT AN ACCOUNT NUMBER
✅ Account Number: 8551119394     ← CORRECT (from FORM B)
```

**Second error**: The 70% IFSC field often points to the wrong branch:

```
❌ IFSC Code: KKBK0008068   ← 100 Feet Road, HAL 2nd Stage (WRONG BRANCH)
✅ IFSC Code: KKBK0000431   ← Indiranagar (CORRECT)
```

**Cross-reference rule**: FORM B is the authoritative source for bank account details. Always verify BANK AFFIDAVIT numbers against FORM B before finalising.

## JDA AFFIDAVIT — "character account" Typo

The withdrawal certification clause in the JDA Affidavit consistently has:

```
❌ "...certified by an engineer, an architect and character account in practices"
✅ "...certified by an engineer, an architect and a chartered accountant in practice"
```

This exact typo appears in multiple document sets — check for it every time.

## RERA Affidavit Placeholders

Every RERA affidavit (FORM B, Bank Affidavit, JDA, Section 3(1), No Mortgage, Non-Litigation) has blank `__________` for:
- Place of verification
- Date of signing
- Date of verification

These must be filled before notarization. Ask the user for the specific date and place.

## Document Source

The 6 RERA affidavits are typically stored in a folder named **"RERA - AFFIDAVITS DRAFTS"** inside the project's main Drive folder.

| Document | Purpose |
|---|---|
| FORM B.docx | Affidavit cum Declaration (Rule 3(4)) — main RERA compliance affidavit |
| BANK AFFIDAVIT.docx | Bank account declaration — 100%/70%/30% account details |
| JDA AFFIDAVIT.docx | Joint Development Agreement affidavit (Promoter + Landowners) |
| Section 3(1) No-Violation AFFIDAVIT.docx | Declares no pre-launch marketing/sales |
| No Mortgage AFFIDAVIT.docx | States land/units free from encumbrances |
| non-litigation Affidavit.docx | Title dispute indemnity |

## NRI Landowner GPA Reference Insertion

When landowners are NRI/OCI (Australian passport holders), add a GPA (General Power of Attorney) reference wherever landowners are described.

**Standard GPA text:**
`, as represented by their GPA Holder M/s DRA Realty Private Limited vide General Power of Attorney registered as Document No. DRO/SJN/GPA/1088/2025-2026 dated 12.08.2025 at the office of the District Registrar, Shivajinagar, Bangalore`

**Documents affected and insertion points:**
- FORM B: After "the Landowners" — restructure sentence: `...the Landowners, [GPA TEXT], have the legal title...`
- JDA AFFIDAVIT: (1) After "Bangalore East" in first landowner para; (2) After first "plot" in second landowner para
- No Mortgage AFFIDAVIT: After "Bangalore East" in the single landowner para
- non-litigation Affidavit: After "Bangalore East" in the single landowner para

**Documents NOT needing GPA** (no landowner text): BANK AFFIDAVIT, Section 3(1) No-Violation Affidavit.

## Project End Date Updates

When the RERA timeline changes, update the end date (DD-MM-YYYY format) in:
- FORM B: `10-12-2027` → `30-12-2028`
- BANK AFFIDAVIT: `10-12-2027` → `30-12-2028`
- JDA AFFIDAVIT: `10-12-2027` → `30-12-2028`

Search for the exact old date string and replace across all documents.

## Technical Note — Editing .docx Files on Drive

These affidavits are binary .docx files (MIME: application/vnd.openxmlformats-officedocument.wordprocessingml.document). Use raw XML manipulation:

1. Download via drive.files().get_media(fileId)
2. Unzip, parse word/document.xml with ElementTree
3. Modify all `<w:t>` elements for simple text replacements
4. For paragraph-targeted inserts, find paragraph by joined text, locate the anchor run, append to its last `<w:t>`
5. Rebuild docx, upload as NEW file via drive.files().create() with UPDATED suffix
6. Always rebuild from original in ONE pass — incremental uploads corrupt run structure

See gws-automation skill -> references/docx-modify-reupload-drive.md -> Alternative: Raw XML Manipulation section for full code patterns.

## User Preference (Prakash Singh)

- **Concise data output**: When asked for land extent totals from a spreadsheet, give ONLY the final total per group (Acres + Guntas), not a per-owner breakdown or commentary. He will ask for details if needed.
- **"Re-check" means simplify**: When he says "re-check" or "generate only", he wants the answer stripped to just the requested metric — no explanatory framing, no sub-breakdowns.

- **Concise data output**: When asked for land extent totals from a spreadsheet, give ONLY the final total per group (Acres + Guntas), not a per-owner breakdown or commentary. He will ask for details if needed.
- **"Re-check" means simplify**: When he says "re-check" or "generate only", he wants the answer stripped to just the requested metric — no explanatory framing, no sub-breakdowns.
