# NDR Contacts Registry — dual-store workflow (Aug 2026)

NDR keeps contacts in TWO stores that must BOTH be updated when he says "update the contact":

1. **Google Contacts (live)** — People API `people` v1, service `google-draas`.
   Contacts added on his phone appear here immediately. Resource names look like `people/c2764143950027406658`.
2. **"NDR DRAAS Google contacts" CSV sheet** — spreadsheet `1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g`,
   tab `'NDR DRAAS Google contacts.csv'` (grid sheetId `1196451362`). This is the **"online contact sheet"**.
   93-column Google-Contacts-format export, ~4220 rows, roughly alphabetical by first name.
   **It goes STALE** — contacts added to Google Contacts after the last export are NOT in the sheet.

A third, rarely-used store: **"NDR CONTACTS"** sheet `1fYa-t2RY1siy2qBgAH8uu_Jd2chjJ716BbcpxilpOK0`
(curated list, cols SL.NO/NAME/COMPANY/DESIGNATION/ADDRESS/TELEPHONE/FAX/MOBILE/E-MAIL/WEBSITE/NOTES, ~13 rows).

## User convention
"Make the update both to the Google contact as well as online contact sheet." → update People API + CSV sheet,
and report the CSV row number so he can verify. When editing notes, KEEP existing note content
("New York", "met him", etc.) and append/correct — do not rewrite.

## Search procedure
1. Search CSV sheet first (batched `values().get` over A:AK, ~500 rows/call) — name/org/phone.
   Absence here ≠ contact doesn't exist (stale export).
2. Search Google Contacts: `people().connections().list(resourceName='people/me',
   personFields='names,phoneNumbers,emailAddresses,organizations,biographies', pageSize=1000)`
   and **paginate with nextPageToken** (~4400 contacts, ~5 pages). Match displayName/phones/orgs/bio.
3. Search by phone digits too (find Prakash Singh via +91 97399 32078).

## People API update (rename / notes)
- `people().people().updateContact(resourceName=..., updatePersonFields='names,biographies', body=person)`
- **PITFALL: 400 "Request must set person.etag"** unless body includes the person's `etag`.
  Always `get()` first, copy `etag`, then send `{"etag": ..., "names": [...], "biographies": [...]}`.
- Rename = set givenName/familyName/unstructuredName. Notes = biographies[0].value (preserve old text, append correction).

## CSV sheet update / insert
Column map (0-indexed): A0=First, B1=Middle, C2=Last, J9=File As, K10=Org, L11=Title, O14=Notes,
AB27=Phone1 Label, AC28=Phone1 Value, AD29/AE30=Phone2.
- Exists → `values().update` with `USER_ENTERED`.
- Missing → insert alphabetically:
  1. `spreadsheets().get(fields="sheets.properties(sheetId,title)")` for the real grid id.
     **PITFALL: hardcoding sheetId 0 fails "No grid with id: 0"** (this tab's id is 1196451362).
  2. `batchUpdate` `insertDimension` (ROWS, startIndex=row-1, endIndex=row, inheritFromBefore=False).
  3. `values().update` the new row.
- **PITFALL: "+91 98151 60009" written with USER_ENTERED renders `#ERROR!`** (parsed as formula).
  Re-write the phone cell with `valueInputOption='RAW'`.
- Sort order: shorter prefix before longer ("Puneet" < "Puneeth"); insert after the last row that sorts before the new name.

## Verification
Re-read the written range; print name/phone/notes. Confirm both stores before reporting.

## Worked example — Anthony George Mathew (this session)
- CSV row 331 was a mash-up ("Anthony Century Home Sales" in First Name, org empty).
- Fixed: A="Anthony", B="George", C="Mathew", J="Anthony George Mathew", K="Century Real Estate",
  L="Sales Head, Luxury Sales Head". Phone +91 96069 13114 already present.

## Worked example — Aditya Gill → Puneeth Gill (this session)
- Google contact `people/c2764143950027406658`, phone +91 98151 60009, created 2026-08-08, NOT in CSV.
- People API: renamed to Puneeth Gill (dictated spelling P-U-N-E-E-T-H), bio appended
  "This telephone number belongs to Puneeth Gill and his son is Veer Aditya Gill" (old "Son: Puneet Gill" line removed as superseded).
- CSV: inserted row 2598 (after "Puneet Malode" row 2596, before "Puneeth Gowda BBMP" row 2597 → insert at 0-based 2597).
