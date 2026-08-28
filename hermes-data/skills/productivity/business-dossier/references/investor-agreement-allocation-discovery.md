# Investor/Landowner Agreement Allocation Discovery

Finding unit allocation details (plot area, facing, built-up area) from executed investor agreements for DRAAS real estate projects — typically villa-under-construction or plotted development investment schemes.

## When to Use

- User asks to find "what was allocated" to investors in a project from executed agreements
- User needs a structured table of investor names vs unit details (facing, size, amount)
- Cross-referencing referral tracking sheets with signed PDF agreements
- Distinguishing executed (signed) agreements from pending/in-progress ones

## Drive Search Strategy

Search the user's Drive (via `gws_auth.build_service('drive','v3', service_name='google-draas')`) with multiple query patterns:

### 1. Project Folder Discovery

```python
# Search multiple name variants — user may say "Oasis" but folder is "Saveganapalli"
for q in ['Ranka Oasis', 'Saveganapalli', 'Savega', 'SLP']:
    results = drive.files().list(
        q=f"name contains '{q}'",
        spaces='drive',
        fields='files(id,name,mimeType,parents,webViewLink)'
    ).execute()
```

### 2. Investor Document Patterns

Investor agreements for DRAAS villa projects follow consistent naming:

| Pattern | What it finds |
|---------|---------------|
| `name contains 'Loan cum Investment'` | The core investment agreement (Villa Option Track) |
| `name contains 'Mortgage Deed' and name contains 'Investor'` | The joint/simple mortgage deed |
| `name contains 'Investor Specs'` | Presentation with allocation overview |
| `name contains 'Investor Referral'` | **Key sheet** — tracks allocations per investor |
| `name contains 'Investor Workings'` | Spreadsheet with project-level allocation assumptions |
| `name contains 'Oasis' and name contains 'Investor'` | Broad catch-all for investor docs |

### 3. Individualized vs Template Agreements

Template agreements have names like:
- `20250610 FINAL Ranka Oasis SLP - Loan cum Investment Agreement (Villa Option Track).docx`

Individualized (named for specific investor) agreements prepend the investor name:
- `Neehar 20250610 FINAL Ranka Oasis SLP - Loan cum Investment Agreement (Villa Option Track).docx`
- `Sudershan 20250610 FINAL Ranka Oasis SLP - Loan cum Investment Agreement (Villa Option Track).docx`

**Key insight:** Individualized agreements may be fewer than the total investor list — many investors signed the same template without a named copy. The referral sheet is the authoritative source for ALL investors.

## The Referral Sheet — Primary Data Source

The **Investor Referral Sheet** (Google Sheets) is the most reliable source for per-investor allocation data. It typically has multiple tabs:

### Tab Structure (from observed pattern)

| Tab | Content |
|-----|---------|
| **Total amount Received** | Per-investor rows: Name, Option, Facing, Villa Size (sqft), Per sft rate, Total Amount, Agreement Link, Payment history |
| **Sheet5** | Summary table: Investor Name, Date of Agreement, Total Investment Amount |
| **Sheet3** | Referral commission tracking: Referral agent → Recipient → Client → Commission sqft → Amount |
| **Sheet1** | Unit size break-up: How many units of each size, referral fee breakdown by agent |

### Data Columns in "Total amount Received" Tab

```
SL NO | Investor Name | AMOUNT | Option | Facing | Villa Size | Per Sft | Amount | Agreement Link | DATE | AMOUNT
```

Key fields:
- **Option**: Always "Villa" for villa-track investments
- **Facing**: East Facing or West Facing (drives rate differential)
- **Villa Size**: The Saleable Super Built-Up Area (SBUA) in sqft
- **Per Sft**: Rate per sqft (₹3,500 for East, ₹3,300 for West in observed pattern — ₹200 premium)
- **Agreement Link**: Direct link to the signed PDF agreement on Drive
- Payment rows show installment history (token, subsequent payments, total)

### Executed vs Pending Distinction

Check **Sheet5** or the Agreement Link column:
- **Executed**: Has a live Drive agreement link AND a date of agreement
- **Pending**: "Sent to Client for sign", "Agreement not done yet", or empty agreement link
- **Partially paid**: Has payment history but agreement not yet finalized

## Unit Allocation Data Model

For villa-track investments, per-investor allocation consists of:

| Field | Source | Example |
|-------|--------|---------|
| Villa size (SBUA) | "Villa Size" column | 2,700 or 3,150 sqft |
| Facing | "Facing" column | East or West |
| Rate per sqft | "Per Sft" column | ₹3,500 (East) / ₹3,300 (West) |
| Total amount | "Amount" column | ₹94,50,000 |
| Agreement link | "Agreement Link" column | Drive PDF link |

The **site/plot area** (land component) is NOT in the referral sheet — it's specified in Schedule C of each executed PDF. The executed PDFs are often scanned (image-based), making text extraction impossible via pdftotext. Two options:
1. **OCR** the PDF page where Schedule C appears
2. **Cross-reference** the Investor Workings sheet which may have the assumed plot size (~1,500 sqft)

## Result Compilation Format

Present findings in a structured table:

```
## Unit Allocation Summary

| # | Investor Name | Villa Size (sqft) | Facing | Rate/sqft | Total Amount | Status |
|---|---|---|---|---|---|---|
| 1 | Sudharsan JP | 2,700 | East | ₹3,500 | ₹94,50,000 | ✅ Executed |
| 2 | Mahesh Athi | 2,700 | West | ₹3,300 | ₹89,10,000 | ✅ Executed |
```

Include a summary section:
- Total investors (X executed, Y pending)
- Unit size break-up (X units of 2,700 sqft, Y units of 3,150 sqft)
- East-facing count vs West-facing count
- Total investment amount

## Pitfalls

- **Scanned PDFs block text extraction.** Executed PDF agreements are often image-based scans. `pdftotext` returns 0 bytes. Fall back to the referral sheet data and note the limitation.
- **Referral sheet data may span multiple tabs.** One tab has allocation details, another has payment history, a third has commission structure. Always read all tabs.
- **Payment rows are stacked under investor name.** The first row has the investor name; subsequent rows are payment installments with date and amount.
- **Individualized agreement files ≠ complete set.** A named agreement file on Drive (e.g., "Neehar") may exist for only a subset of investors. Don't report "only X investors found" — check the referral sheet for the full list.
- **Investor count changes over time.** The sheet may show investors who paid but haven't signed agreements yet, and vice versa. Distinguish clearly.
- **Price differential by facing.** East-facing villas command a premium (observed: ₹200/sqft). Include the rate per sqft in the output to make the premium visible.
