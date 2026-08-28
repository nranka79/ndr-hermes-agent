# NDR DRAAS Google Contacts CSV — Sheet Schema (dual-store updates)

When updating a contact in BOTH Google Contacts (People API) and the
"NDR DRAAS Google contacts.csv" sheet, you must write the same data to
the sheet's CSV-shaped columns. Sheet ID: `1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g`
(91 columns, header row 1).

## Address block columns (the part you'll usually edit)

Each address occupies a 9-column block: Label, Formatted, Street, City,
PO Box, Region, Postal Code, Country, Extended.

| Block | Label | Formatted | Street | City | PO Box | Region | Postal | Country | Extended |
|-------|-------|-----------|--------|------|--------|--------|--------|---------|----------|
| Address 1 | AN (40) | AO (41) | AP (42) | AQ (43) | AR (44) | AS (45) | AT (46) | AU (47) | AV (48) |
| Address 2 | AW (49) | AX (50) | AY (51) | AZ (52) | BA (53) | BB (54) | BC (55) | BD (56) | BE (57) |
| Address 3 | BF (58) | BG (59) | BH (60) | BI (61) | BJ (62) | BK (63) | BL (64) | BM (65) | BN (66) |
| Address 4 | BO (67) | BP (68) | BQ (69) | BR (70) | BS (71) | BT (72) | BU (73) | BV (74) | BW (75) |

## Canonical address value

For a Bangalore address the standard packed value is:

```
A3-202, White House Apartments, R.T. Nagar, Bengaluru, Karnataka 560032, India
```

- Formatted = the packed string
- Street = `A3-202, White House Apartments, R.T. Nagar`
- City = `Bengaluru` · Region = `Karnataka` · Postal = `560032` · Country = `India`
- PO Box / Extended = empty

## Worked pattern (verified 2026-08 — Murjani address update)

1. **People API side:** `people.get(resourceName=..., personFields='addresses,metadata')`
   → get etag. `updateContact(updatePersonFields='addresses', body={etag, addresses:[...]})`.
   ⚠️ `updatePersonFields='addresses'` REPLACES the whole addresses array —
   re-send every address you want to keep (old ones become "other" or get
   relabelled, e.g. a stale USA home → `type: "Old"` custom label; see
   google-workspace-api People section for custom labels).
2. **Sheet side:** find the row by scanning column A..J for the name
   (e.g. `Charitra Murjani` row 718, `Nenumal Murjani` row 2268), then
   `values().update` the right Address-N block range (e.g. `AN718:AU718`
   for Address 1, `AW718:BE718` for Address 2). Use
   `valueInputOption='USER_ENTERED'`.
3. **Verify:** re-read the block and confirm Label/Formatted/Street/City/
   Region/Postal/Country all present. Beware: the sheet's Address 2 was
   the USA address for Charitra before the Bangalore home replaced it —
   when repurposing blocks, restore the old address into the next free
   block with its original label so no data is lost.

## Notes

- Rows are 1-indexed with header at row 1, so data starts at row 2.
- The sheet is a CSV-import shape: repeated email/phone columns exist
  (e.g. email type + value pairs); don't confuse the "email type" column
  with the "address label" column when reading.
- Names sometimes sit in First Name only (e.g. `Charitra Murjani` as one
  cell) vs First+Last split — search the joined A..J string, don't assume
  a column layout.
- Row numbers drift as the sheet grows — ALWAYS scan for the name, never
  hardcode the row from an old session.
