# Tailor Talk (leads_data) Format — MagicBricks Lead Conversion

Sheet: `leads_data (8)` — https://docs.google.com/spreadsheets/d/1ZigDYLtjdDEY3k2_h16LvL-3lb2VZ40LCboQGdbYlrI
GWS service: `google-draas` (Bharat's sales1.blr@draas.com token). API: sheets v4.

## Column layout (18 columns, row 1 header, data from row 2)

1. Service Type          → "Under Construction"
2. Property Type          → "NA"
3. Lead Date              → DD/MM/YYYY (from MagicBricks email date, oldest → newest)
4. Lead Name              → sender name from email (strip "(Individual)"/"(Owner)" suffix markers)
5. Lead Phone Number      → (+91)-XXXXXXXXXX
6. Lead Email             → sender email
7. Seller Id              → 5c07e434-6dbd-4f27-be13-54a99ffda912
8. Seller Name            → DRA Homes
9. Locality               → from email subject/body (Sarjapura, Bagalur Sarjapur Road, Chichuraganapalli, Hosur Road…)
10. City                  → Bangalore / Hosur / Krishnagiri
11. Configuration         → Residential Plot
12. Price                 → "NA" (DRA rule: keep pricing blank; do not invent)
13. Building/Project Name → DRA Ranka Udaya / DRA Ranka Oasis / NA (map from listing locality)
14. Property/Project ID   → MagicBricks listing ID from email body ("Property ID 84675109"), OR DRA internal ID 364389 for Ranka Udaya rows — CONFIRM with Bharat which ID convention the target sheet uses; the sheet's pre-existing rows used 364389 while MagicBricks listing IDs are 8-digit
15. Address               → "NA"
16. primary_lead_status   → "NA"
17. secondary_lead_status → "NA"
18. Notes                 → "NA"

## Append workflow (do NOT overwrite existing rows)

1. GET sheet range A1:R1000; count rows; find last non-empty row in column A.
2. Diff existing rows against new leads by (name.lower(), phone) — never re-append a phone already in the sheet.
3. Build rows padded to exactly 18 cells; normalize None → "NA".
4. values().update with range starting at last_row+1, valueInputOption='USER_ENTERED'.
5. Verify by re-reading the appended range and printing row 25 (boundary), first appended row, last row.

## Pitfalls

- The sheet may already contain a manually-filled batch (e.g. 24 rows of DRA Ranka Udaya with project ID 364389). Diff by phone before appending; do not clobber.
- Phone-less leads (email only, e.g. Samson) — include with blank phone and flag to Bharat; do not silently drop or fabricate a number.
- MagicBricks email date strings have a trailing space at position ~25 — trim before parsing or the match returns 0/78.
- Email body fields are labeled: "Sender's Name:", "Mobile:", "Email:" — not subject-line patterns.
- Leads without phone were previously excluded from Camp Magic format but kept (blank phone) in Tailor Talk — follow the user's current instruction per request.
