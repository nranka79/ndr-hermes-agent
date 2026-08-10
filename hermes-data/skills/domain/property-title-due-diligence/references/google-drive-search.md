# Google Drive multi-account file hunts (worked pattern)

For "find X on my drive" / "we downloaded Z from <portal>" requests. Covers Nishant's 3 Google accounts: google-draas (ndr@draas.com), google-ahfl (ndr@ahfl.in), google-gmail (nishantranka@gmail.com).

## Search recipe (per account)
1. `gws_resolve_account` (no args) → full account + auth status list before searching.
2. `build_service("drive","v3", service_name=...)` via execute_code with `/opt/hermes/.venv/bin/python` (system py lacks googleapiclient). Call `about().get()` first — it fails with `invalid_grant` when the token is dead.
3. Queries, in order:
   - `name contains '<Term>'` — **case-sensitive**. Also try spelling variants the user misremembers (real case: "Katalia" → "Cataleya").
   - `fullText contains '<Term>'` — indexed text/OCR only; scanned drawing PDFs usually NOT indexed, so a plan can exist without matching.
   - Combined: `name contains 'X' and (name contains 'plan' or name contains 'sanction')`.
   - Always: `supportsAllDrives=True, includeItemsFromAllDrives=True`; paginate on `nextPageToken` (pageSize 100); check `trashed=true` too; list shared drives via `drive.drives().list()` and search with `corpora='drive', driveId=<id>`.
4. On a brochure/marketing hit: download + `pdftotext` to extract developer/address/project identity, then search those terms (e.g. Legacy Cataleya → "Cunningham" + "Legacy" + "RERA").
5. Fetch `parents` of any hit, walk up 1–2 levels, list the containing folder — target files are often named WITHOUT the project name ("Sanctioned Plan.pdf", "Annexure 74 Sanction Drawings.pdf") inside a project-named folder.
6. Gmail trail: `gmail.users().messages().list(q='<term>')`, format=metadata + payload.headers. Folders like "Documents Downloaded  from RERA Website" on draas drive hold portal downloads.

## False-positive trap — Karnataka Gazette guideline-value books
Files named like `Shivajinagar.pdf`, `CVC - 25 - Shivajinagar.pdf`, `5 - III - 2018-19-Shivajinagar-f.pdf` contain property names in their valuation lists → they match `fullText contains '<project>'` but are value gazettes, NOT the requested plan. Always verify a candidate with pdftotext + first-page look before presenting it as the answer.

## Expired vault token (ahfl pattern)
- `invalid_grant: Token has been expired or revoked` from build_service = dead token, not a vault outage.
- `gws_resolve_account` can still report `has_token: true` while refresh fails — trust the build_service error.
- Fix: `send_oauth_url(service_name='google-ahfl', login_hint='ndr@ahfl.in', label='Re-authorize ahfl drive')` → user taps the Telegram button → token stays invalid until tap completes. Retry with a fresh build_service only after user confirms; do not retry-loop (max 2–3).

## RERA download naming
Karnataka RERA downloads are named `PRMKARERA<projectid>PR<...>.pdf`. "ARERA" in user speech ≈ Karnataka RERA (rera.karnataka.gov.in). Search `name contains 'PRM'` / `name contains 'KARERA'`.

## Session example — Legacy Cataleya sanctioned-plan hunt (2026-08-07)
- Project: Legacy Cataleya, Legacy Group (legacy.in, +91 767676 4200), 333 Thimmaih Rd / Cunningham Road, Bangalore; 4BHK vaastu condos, brochure Nov 2015.
- Found on google-draas: `Legacy Cataleya - Brochure.pdf` (1TJSmM3UARhRZS1Br_Z7WXqkbBWUMHr2y) in TMP folder (18p74II2uL32sNDzDDwXzmlOUdJJOTmE-).
- No sanctioned plan on draas or gmail (name + fulltext + trash + shared drives). ahfl unchecked — token expired, re-auth button sent (msg 38048). Search ahfl next with 'Cataleya'/'Legacy'/'Cunningham'.
