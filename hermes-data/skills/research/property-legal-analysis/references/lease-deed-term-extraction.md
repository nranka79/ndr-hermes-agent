# Lease Deed Term & Expiry Extraction (old scanned Indian deeds)

Trigger: "when does the lease terminate for [property]", "check the lease end date",
"how many years left on the lease", "review the lease-cum-construction agreement".

## Discovery (Drive)

- Search Drive with `name contains '<Property>'` plus `name contains 'lease'` — old
  leases are often named `Ranka Chambers - 18-Jun-1986 Lease Deed.pdf` style.
- Check the property's folder (e.g. `Ranka Chambers` root folder) — it may hold only
  photos + the deeds, nothing more.
- An "… Office Documents Index" spreadsheet by the same name is usually a **physical
  file inventory** (vouchers, customer files, lease-deed originals list) — NOT a
  summary of lease terms. Don't burn time reading it for dates.

## Extraction pipeline (scanned deeds — no text layer)

1. Download via Drive API `MediaIoBaseDownload` (authenticated; raw curl gets
   sign-in HTML on private files).
2. `pdftotext -layout file.pdf out.txt` → near-zero bytes = scanned, skip text
   extraction entirely.
3. `pdftoppm -r 200 -png -f 1 -l N file.pdf prefix` render first ~5 pages, then
   `tesseract page.png stdout --psm 6` for **TRIAGE ONLY**: identify which page
   holds the operative clauses. Keywords: `period`, `years`, `rent`, `come into
   full force`, `commencement`.
4. **Tesseract output on 1980s typewriter/handwritten scans is garbage — do NOT
   trust it for the actual dates/terms.** Run `vision_analyze` on the rendered PNG
   of the operative page with a pointed question ("read the clauses exactly: lease
   period in years, rent and from which date, any extension clause"). Vision reads
   the term cleanly (e.g. "fixed for 58 (fifty-eight) years").
5. For one ambiguous field (e.g. deed date `4th` vs `14th` when the filename says
   one thing and OCR another): crop the date band with PIL, re-render at 400 DPI,
   then `vision_analyze` the crop.

## Where the clauses live (typical structure)

| Content | Location |
|---|---|
| Parties (lessor/lessees, addresses) | Page 1 |
| Recitals (prior lease, partition deed, surrender) | Pages 2–4 |
| **Operative term clause** ("period … fixed for N years", "come into full force") | Mid-document — page ~4 of 8, or pages 4–5 of 11 |
| Rent clause + from-date | Same region as term clause |
| Extension / renewal clause | Next clause after term |
| Schedule of property + boundaries | Near end, before signature/registration pages |

Do NOT guess end date from filename. Compute: `end = deed_date + term`
(60 years "from the date of this deed"). Report both the exclusive-ish bounds
(e.g. 3-Aug-2044 vs 4-Aug-2044) unless the deed says otherwise.

## Pitfalls

- **Deed-body date ≠ filename date.** `Ranka Chambers - 14-Aug-1984 Lease Deed.pdf`
  body reads "made this **4th** day of August 1984". The filename likely carries
  the registration date, not the execution date. Always quote the deed text; flag
  the mismatch to the user instead of silently picking either.
- **Stamp-paper handwritten annotations corroborate the term.** The 1984 deed's
  non-judicial stamp had "1984" and "2044" handwritten — a 60-year term cross-check
  that matched clause language. Use annotations as a second source, not a primary.
- **A property may have TWO leases (main + adjoining).** The 1986 deed references
  the 1984 deed as "the adjoining property … already leased… the period under this
  lease should automatically be extended … consistent with the period under the
  said lease". Identify which deed is the user's "Ranka Chambers" lease (the
  lease-cum-construction one) and report both with the extension-clause note.
- **Lease-cum-construction markers**: clauses granting the lessee the right to
  demolish existing constructions and build a business complex, and "all
  constructions shall become the absolute property of the Lessor after the expiry
  of the period of lease". This distinguishes a ground-lease-plus-develop deal from
  a plain office lease.
- **Old deed parties are the family's earlier generation.** 1984 lessees were
  "partners of M/s NANDI ENTERPRISES" incl. Arun B. Ranka; the lessor was the
  original landowner (Syed Aviuddin). Keep party names verbatim — useful for title
  context later.

## Worked example — Ranka Chambers, 31 Cunningham Road (Sep 2026)

- **1984 deed** (lease-cum-construction): made 4-Aug-1984; lessor Syed Aviuddin;
  lessees = partners of M/s Nandi Enterprises incl. Arun B. Ranka; term **60 years**
  from deed date → ends ~3/4-Aug-2044; rent Rs 700/month; ~42 yrs elapsed,
  **~17y 11m left** as of 2-Sep-2026. File on Drive: `Ranka Chambers - 14-Aug-1984
  Lease Deed.pdf`.
- **1986 deed** (adjoining property): made 18-Jun-1986; term **58 years** → ends
  ~17/18-Jun-2044; rent Rs 50/month from 1-7-1986; auto-extension to stay
  consistent with the 1984 lease; ~40 yrs elapsed, **~17y 9m left**. File:
  `Ranka Chambers - 18-Jun-1986 Lease Deed.pdf`.

Bottom line for Ranka Chambers: lease terminates **2044** (~18 years from Sep 2026).