# Director's Report — Cross-Verification Against Audited ITR Data

## Purpose

When a Director's Report (prepared under Section 134 of the Companies Act, 2013) is being submitted alongside RERA registration documents, the **narrative claims** in the report must be factually consistent with the company's audited financial statements (ITR P&L, Balance Sheet, and Auditor's Report). This reference captures the workflow for extracting ITR data from scanned PDFs and cross-verifying both the **financial figures** and the **narrative explanations** in the Director's Report.

Distinct from `rera-cash-flow-itr-verification.md` (which covers only the CFS), this reference focuses on:
- Whether narrative claims about losses, project status, and expenses match the audited records
- The "pre-operative expenses gap" — when a report blames a loss on pre-operative costs but the Balance Sheet shows no Capital Work-in-Progress
- Whether project-related SPV structures explain the difference between direct costs and investment holdings

## When to Use

- User shares a Google Doc / .docx Director's Report and asks you to "check against the ITR" or "verify the figures"
- A Director's Report makes claims like "loss on account of pre-operative expenses towards project X" and you need to verify from the audited financials
- RERA filing requires the Director's Report to be consistent with the audited Cash Flow Statement and Balance Sheet
- You see the user is preparing RERA registration documents and the Director's Report is being drafted

## Workflow

### Phase 1: Access the Director's Report Document

The Director's Report is often a **.docx file uploaded to Google Drive**, not a native Google Doc. The Docs API throws `"This operation is not supported for this document. The document must not be an Office file."` on such files.

**Use the Drive API to download it:**

```python
import sys, os
sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service

drive = build_service('drive', 'v3')

# Download .docx
request = drive.files().get_media(fileId='DOC_ID')
from googleapiclient.http import MediaIoBaseDownload
import io
fh = io.BytesIO()
downloader = MediaIoBaseDownload(fh, request)
done = False
while not done:
    status, done = downloader.next_chunk()

with open('/tmp/directors_report.docx', 'wb') as f:
    f.write(fh.getvalue())
```

**Extract text from the .docx:**

```python
from docx import Document
doc = Document('/tmp/directors_report.docx')
text = []
for para in doc.paragraphs:
    text.append(para.text)
for i, table in enumerate(doc.tables):
    text.append("--- TABLE " + str(i+1) + " ---")
    for row in table.rows:
        row_data = [cell.text.strip() for cell in row.cells]
        text.append(" | ".join(row_data))
full_text = "\n".join(text)
```

Fallback when `python-docx` is not installed: use `zipfile` to read the raw XML from the .docx.

### Phase 2: Identify What to Verify

From the extracted Director's Report, extract two categories of claims:

**Category A — Financial Figures (exact match required):**
- Total Income (each FY)
- Total Expenditure (each FY)
- Profit/(Loss) Before Tax
- Current Tax
- Profit/(Loss) After Tax

**Category B — Narrative Claims (evidence-based verification):**
- "Loss primarily on account of pre-operative expenses towards Project X"
- "Company has commenced development of Project X"
- "Strategic investments in project SPVs"
- Any claim about project status, construction milestones, or revenue recognition

### Phase 3: Extract ITR Data from Scanned PDFs

ITR PDFs for Indian companies are scanned images — `pdftotext` returns empty. Use the pdftoppm + vision_analyze (OCR) pipeline:

```bash
pdftoppm -jpeg -r 200 /path/to/itr_FY2024-25.pdf /tmp/itr_images/itr_2024-25_page
```

Then read pages via `vision_analyze()`:

| Target Content | Page Range (FY 24-25) | What to Look For |
|---|---|---|
| ITR Acknowledgement | 1 | PAN, Company Name, Address |
| Company Header | 13-14 | Registered Office, CIN, Directors |
| Balance Sheet | 14-15 | Assets (Fixed, Current, CWIP, Investments), Liabilities (Borrowings) |
| P&L Statement | 16-17 | Total Income, Expenses, PBT, Tax, PAT |
| Notes & Schedules | 17-23 | Expense breakdown, Fixed Assets schedule, Investments, Related Parties |

**⚠️ Unit conversion:** ITR values are in **₹ Thousands**. Multiply by 1000 to get Rupees.

### Phase 4: Cross-Verify Financial Figures

For each Director's Report figure, find the corresponding ITR P&L line and multiply by 1000:

```python
# Director's Report says ₹10,29,000 for Total Income FY 2024-25
# ITR P&L shows 1,029 (in thousands)
# 1,029 × 1000 = ₹10,29,000 ✅
```

Build a verification table:

| Item | Director's Report | ITR P&L (×1000) | Result |
|---|---|---|---|
| FY 24-25 Total Income | ₹10,29,000 | 1,029 = ₹10,29,000 | ✅ |
| FY 24-25 Total Expenditure | ₹2,25,89,000 | 22,589 = ₹2,25,89,000 | ✅ |
| FY 24-25 PBT | ₹(2,15,59,815) | (21,560) = ₹(2,15,60,000) | ✅ (₹185 rounding) |

Accept minor rounding differences (±0.1%) since the ITR is in thousands.

### Phase 5: Cross-Verify Narrative Claims — The Pre-Operative Expenses Gap

This is the most common and most important check. Run through this checklist:

#### Checklist: "Pre-operative expenses towards Project X"

| Check | What to Look For | Evidence Source |
|---|---|---|
| **1. Is there Capital Work-in-Progress?** | Balance Sheet under Non-current Assets. If CWIP is zero, no costs were capitalized. | BS line item "Capital Work-in-Progress" |
| **2. Is there a "Pre-operative expenses" line?** | Check Notes to Accounts or expense schedules for any capitalized pre-op costs | Notes & Schedules |
| **3. What are the actual expenses?** | Check the P&L expense break-up — are they salary, professional fees, rent (general corporate) or material, contractor payments, site costs (project)? | P&L + Notes on Other Expenses |
| **4. When was the JDA signed?** | Check the Director's Report's own "Material Changes" section. If the JDA was signed AFTER the financial year end, the expenses cannot be towards that project. | Director's Report Section 3 |
| **5. Does the company have Fixed Assets for construction?** | If Fixed Assets are only office equipment (₹28,06,000), there are no construction-related assets. | BS: Fixed Assets schedule |
| **6. Is the project done through an SPV?** | Check Non-current Investments. If the company holds investments in "XXX Land Partners" or similar, the project is being done through an SPV, not directly. | BS: Non-current Investments |
| **7. What did the Auditor's CARO say about cash losses?** | The Auditor's Report (CARO clause xvii) may provide a cash-loss table showing profit after tax vs depreciation. Cross-verify. | Auditor's Report, CARO Annexure |

#### Expected Gap Patterns

**Gap Type A: "Pre-operative expenses stated, no CWIP exists"**
- The Director's Report blames the loss on pre-operative expenses
- Balance Sheet shows ZERO Capital Work-in-Progress
- P&L shows general corporate expenses (salary, professional fees, rent)
- → **The expenses are revenue expenses, not capitalized pre-operative costs**
- → The narrative claim is misleading for RERA

**Gap Type B: "Project stated as direct development, but done through SPV"**
- The Director's Report says "Company has commenced development of Project X"
- Balance Sheet shows NO fixed assets related to construction
- But shows significant Non-current Investments in "XXX Land Partners"
- → The company is an investor/holding entity, not the direct developer
- → The narrative should clarify the SPV structure

**Gap Type C: "Loss attributed to Project X, but JDA signed post-year-end"**
- Director's Report in Section 3 states JDA was signed after the FY end
- Yet Section 2 says loss was due to "pre-operative expenses towards Project X"
- → If the JDA didn't exist during the FY, no expenses can be attributed to that project
- → The expenses are pre-project pursuit costs at best

### Phase 6: Suggested Revisions

When the narrative claims don't match the ITR evidence, suggest one of these revisions:

**For Gap Type A (expenses not capitalized):**
> "...resulting in a net loss before tax of Rs. X/- primarily on account of corporate and administrative expenses incurred during the year. The Company is pursuing Project X and incurred preliminary pursuit costs; however, direct project costs will be capitalized upon execution of development agreements."

**For Gap Type B (project through SPV):**
> "The Company holds investments in project-specific Special Purpose Vehicles (SPVs) including [XXX Land Partners]. During the year, the Company has made additional investments of Rs. X towards these SPVs. Direct project development costs are being incurred through these SPVs."

**For Gap Type C (post-year-end JDA):**
> "Subsequent to the balance sheet date, the Company has entered into a Joint Development Agreement dated [Date] for the development of Project X. During the financial year, the Company incurred pre-project pursuit costs which have been charged to revenue."

### Phase 7: Upload Revised Document to Drive

After the document has been updated (either via the user making edits or by replacing the .docx), upload it back:

```python
from googleapiclient.http import MediaFileUpload

media = MediaFileUpload('/tmp/directors_report_REVISED.docx',
                        mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                        resumable=True)

updated = drive.files().update(
    fileId='DOC_ID',
    media_body=media
).execute()
```

## Known Pitfalls

1. **The .docx file is NOT a native Google Doc.** The Docs API cannot read it. Always use Drive API `get_media()` → local extraction → analysis.

2. **Two addresses on ITR documents:** The ITR acknowledgement shows a **correspondence address** (e.g., No.4A/B, Ranka Chambers, Cunningham Road), while the Balance Sheet header shows the **statutory registered office** (e.g., 201A/202BA, Queens Corner, Queens Road). Always use the Balance Sheet address for RERA/legal filings.

3. **Directors change year-over-year.** FY 2022-23 may list different directors than FY 2024-25. Always use the latest balance sheet for current directors.

4. **Expense description on Director's Report vs ITR.** The ITR P&L may show "Other Expenses" as a lump sum. Its break-up (Note 13) shows items like salary, professional fees, audit fees — NOT "pre-operative expenses" or "project development costs." If the Director's Report recharacterizes these, flag the inconsistency.

5. **Rounding differences are normal.** ITR values in ₹ thousands × 1000. Expect ±₹100-₹200 differences on crore-scale figures — these are rounding artifacts.

6. **OCR quality varies.** Low-contrast scans, Kannada text, and handwritten numbers in the ITR may OCR incorrectly. Cross-check critical figures across both the ITR P&L and the Balance Sheet comparative columns.

7. **Revenue may be zero while narrative says "commenced development."** Zero revenue from operations + no CWIP + no construction fixed assets = development hasn't started. The Director's Report should not claim otherwise.

8. **Cash flow statement has its own verification workflow.** See `rera-cash-flow-itr-verification.md` for CFS-specific checks (depreciation, working capital, fixed asset purchases, borrowing changes).

## Verified Example: DRA Realty, Ranka Amber (Jun 2026)

| Check | ITR Evidence | Director's Report Claim | Verdict |
|---|---|---|---|
| FY 24-25 Total Income | ₹10,29,000 | ₹10,29,000 | ✅ |
| FY 24-25 Total Expenditure | ₹2,25,89,000 | ₹2,25,89,000 | ✅ |
| FY 24-25 PAT | ₹(2,15,60,000) | ₹(2,15,60,000) | ✅ |
| Capital Work-in-Progress in BS | Zero | N/A (no claim) | — |
| Pre-operative expenses in BS/Notes | None | "Loss on account of pre-operative expenses towards Ranka Amber" | ⚠️ Gap Type C |
| JDA date (from Section 3) | 16 Aug 2025 | 16 Aug 2025 — signed post-FY end | ⚠️ |
| Project SPV investments | ₹2,33,22,400 | Not mentioned | ⚠️ |
| Revenue from operations | NIL | N/A | — |
| Fixed Assets | Office equipment only (₹28,06,000) | N/A | — |
