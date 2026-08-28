# Searching Scanned Document Archives for Customer Records

Scanned document archives (multiple FILE folders with batch-scanned PDFs) may not contain customer names or unit numbers in filenames. Here is the systematic approach for locating customer-specific records.

## Workflow

1. **Identify the project's master folder on Drive**, then enumerate subfolders (typically FILE 1–N or document-type categories).

2. **Search file names for the unit number** — try all common formats:
   - `name contains 'C-15'`
   - `name contains 'C15'`
   - `name contains 'C 15'`

3. **Search file names for the customer name** — try alternate spellings:
   - `name contains 'Veranna'`
   - `name contains 'Veeranna'`

4. **FullText search scoped to the project folder**:
   ```
   '{master_folder_id}' in parents and fullText contains 'Veeranna'
   ```

5. **If no scanned PDF matches, look for project index/spreadsheet data**:
   - Search for master index spreadsheets (`AHFL_Master_Index`, etc.)
   - Search for customer payment/debit spreadsheets (`Stelo Customer Payment Credits Debits Entries`)
   - These sheets contain the actual unit ↔ customer ↔ amount mapping even when scanned receipts aren't individually named

6. **Scan the spreadsheet for the unit** — columns typically: `Tally Vch No`, `Unit No`, `Date`, `Description`, `Credit`/`Amount`. Extract all payment rows for that unit.

## Concrete Example: AHFL Stelo Dharwad

| Project | Folder Structure | Customer Data Location |
|---------|-----------------|----------------------|
| AHFL Stelo, Dharwad | Ahfl Master Folder > FILE 1–11 (scanned PDFs by category) | "Stelo Customer Payment Credits Debits Entries" spreadsheet |

For Unit C-15 / Veeranna: 5 payment entries found (₹20,00,000 total) in the spreadsheet — no individually named receipt PDF found in the FILE folders.

## Caveats

- **Scanned PDF titles are often generic** — "Plan Sanction And Payment receipts.pdf", "Undated_Original_Receipt_No_10684.pdf" — and may contain multiple customer records inside a single multi-page scan.
- **FullText search on Drive may not index PDF body text**, especially for older scans. File-name search is more reliable than content search.
- **Bharat's naming convention** for AHFL: files are renamed with `YYYYMMDD_Description_CustomerName_Project.pdf` format where possible, but batch scans often keep generic names.
