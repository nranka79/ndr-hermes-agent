# RERA Side-by-Side Comparison (our submission vs a comparable's submission)

Trigger: NDR names a comparable project and asks "compare what they gave RERA
versus what we gave RERA, tell us the documentation difference, and how we bring
our submission in line." The comparable usually arrives as a **Drive folder of
RERA PDFs** rather than a portal link. Verified 2026-09-21 on
Sobha Gardenia vs Ranka Oasis (TN RERA).

## Step 1 — the given Drive folder IS the comparable's submission

NDR drops a folder link like `drive.google.com/drive/folders/<id>` and says
"link to all Gardenia RERA docs". Do not go hunting the portal for their docs —
walk the folder. Expect the filename convention
`<REG>SERIES_<doc type>.pdf`, e.g.:

```
TN01_Building_0043_2018__01_Project_Details.pdf
TN01_Building_0043_2018__02_Approval_Details.pdf
TN01_Building_0043_2018__03_Carpet_Area.pdf
TN01_Building_0043_2018__04_Share_of_Plots_and_Villas_among_Promoters.pdf
TN01_Building_0043_2018__05_Current_Status.pdf
TN-01-Layout-0018-2017_Approval_Details.pdf
```

The filename prefix **is the registration number** — group the files by prefix to
recover the whole registration FAMILY before analysing anything. Gardenia's 14
files resolved to 5 registrations.

## Step 2 — download + OCR every file before comparing

List with `build_service('drive','v3', service_name='google-draas')` (NDR's own
token; the folder is often already in his drive), download each with
`files().get_media` + `MediaIoBaseDownload`, md5 them.

**These RERA PDFs are mostly image scans, and many are in Tamil.** Detect and
route:

```bash
txt=$(pdftotext -layout "$f" - 2>/dev/null | tr -d '\f\n\r ' | wc -c)
if [ "$txt" -gt 200 ]; then pdftotext -layout "$f" "$out"
else pdftoppm -r 200 -png "$f" /tmp/pg; for p in /tmp/pg*.png; do
       tesseract "$p" - >> "$out"; rm -f "$p"; done
fi
```

A file returning ~1 char per page (e.g. 11 pages → 11 chars) is a scan with no
text layer — that is the tell, not a corrupt file. Tamil approval letters OCR
into garbage Latin transliteration; rely on the English/numeral fields (permit
numbers, extents, plot tables) and the page structure instead.

## Step 3 — pull OUR registration to compare against

Use NDR's own token / per-user auth, and the TN flows in
`rera-preliminary-info` → `references/tn-rera-lookup.md`.
Faster than the 38 MB POST when you only need the registration row: the
register HTML pages are plain server-rendered tables —

```bash
curl -s --max-time 120 --proxy socks5h://hermes-utilities:1000 -A "$UA" \
  "https://rera.tn.gov.in/registered-layout/tn" -o layout.html      # ~9.7 MB
curl -s --max-time 120 --proxy socks5h://hermes-utilities:1000 -A "$UA" \
  "https://rera.tn.gov.in/registered-building/tn" -o building.html  # ~1.2 MB
```

Each row carries the full project description, promoter names, approval letter
references, validity date, GPS, and the `formcqr/<uuid>` link. Anchor the regex
on the EXACT registration string.

Also check the Drive for our own certificate/application PDF as an independent
copy — Oasis's was `20260807 Ranka Oasis Rera .pdf` (Form C certificate, owner
`psingh@draas.com`), found with `name contains 'RERA' and name contains 'Oasis'`.

## Step 4 — build the comparison around the DOCUMENT SET, not the prose

The deliverable NDR wants is a document-by-document diff with links to both
sides. Structure that worked:

1. **Registration family table** — every registration on each side, with type
   (Layout/Building), date, and what it covers. This alone usually answers the
   question, because the gap is a MISSING registration type rather than a
   missing file.
2. **Doc-set matrix** — rows = document type (Project Details, Approval Details,
   Carpet Area, Share of Plots/Villas, Current Status/Progress Report), columns =
   Gardenia (with link) vs Oasis (with link or "not filed").
3. **The mechanism section** — quote the annexure content that enables the
   difference, with the actual column headers and real rows from their filing.
4. **What to add** — the specific annexures/pages to file, mapped to the TN RERA
   doc-type names.

## Pitfalls

- **Don't equate "layout approval" with the registration type.** A DTCP/CMDA
  layout sanction is an approval; the RERA registration family (LO vs BLG) is a
  separate decision. Gardenia held layout permits AND building registrations.
- **The same project family can span district indices** (`TN/01` vs `TN/35`).
  Search each index, don't assume one covers the family.
- Different registrations in one family carry DIFFERENT versions of the same
  annexure. The newest registration's area statement is the current product spec;
  earlier ones filed thinner versions. Read all of them before quoting one.
- Progress-report / Current_Status PDFs are where you PROVE how sales are booked
  (carpet area vs plot extent; whether UDS is registered). Quote them — they are
  the strongest evidence of the sale treatment actually used.
- Give the user both links: their own submission AND the comparable's, per
  document. NDR reads the diff against the sources.
