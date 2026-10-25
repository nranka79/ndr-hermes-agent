# BBMP TDR Claims — Release Deed & Khata-Reduction Process (Karnataka)

**Class:** When a BBMP road/parks acquisition notification exists against a project survey
number, the landowner/developer can claim Transferable Development Rights (TDR) instead of
monetary compensation. Verified Sep-2026 on Ranka NorthStar (Allalasandra, Sy 14/1).

## Trigger
- User shares a BBMP notification (FORM-1 / TDR) covering part of a project's survey number
- User wants to "file the application → get the release deed → khata stands reduced"
- User's plan: reduce khata by the acquired strip, then claim 2x TDR benefit for the loss

## Legal basis (verified from the notification itself)
- **Karnataka Town & Country Planning Act 1961, s.14-B** (acquisition for public purpose
  with Development Rights in lieu)
- **Karnataka TCP (Benefit of Development Rights) Rules, 2016** — rule 3, FORM-1 notification
- Entitlement: **twice the area of land surrendered** as notional development rights
  (plus one-time building-area value compensation where buildings exist)
- Notional land is eligible for FAR and used as **additional built-up area at the receiving plot**

## The FORM-1 notification anatomy (19.12.2017 example, No. EE/YNK/TDR/03/17-18)
- Header: BBMP, Office of Executive Engineer (Road Infrastructure), Yelahanka Division,
  #208, 2nd Floor, Annex Building-3, N.R. Square, Bengaluru-560002
- Schedule table: Sl.No | District | Taluk | Village | Sy.No/Khata | Type of land | Nature |
  Area (sqm) | Name & address of owner
- Landowners must appear (10 days, 10 AM–4 PM) with sale deeds, RTCs, mutation copy, tax
  paid receipts, conversion order, revenue sketch
- Owners give **option for Grant of Development Rights** to the Commissioner, BBMP

## Process chain (as dictated by NDR, Sep-2026)
1. **File the TDR application** under the notification for the acquired strip
2. Get the **release deed** executed → khata stands reduced by the acquired area
3. **Investigate the south-side road** through the survey number (often also notified and
   acquired years earlier) → claim 2x TDR for that road-area loss as well
4. **Plan-sanction strategy**: combined khata after reduction (~47,000 sqft in the NorthStar
   case) — apply for plan sanction showing the road land is relinquished (it already exists
   as road); build on the balance (~43,000 sqft) while taking FAR benefit on the FULL reduced
   khata area
5. Watch the arithmetic: 53,148 − ~5,378 (499.66 sqm) ≈ 47,770. Present the equation so the
   khata number, not a rounded claim, drives the application.

## Worked example — Ranka NorthStar Sy 14/1 (2017 notification, 2 pages)
- Page 1 = FORM-1 notification (19.12.2017). Page 2 = SCHEDULE.
- Schedule row 8: Sy No 14/1, Agricultural, Open Space, **499.66 sqm ≈ 5,378 sq ft**, owner
  listed as **Ashwathamma** (the strip along Allalasandra Lake, southern side road to
  Chikkabomsandra).
- Other rows are for different survey numbers (6/1, 6/2, 7, 8/1, 8/2, 14/2) — only 14/1 is
  the project's survey. Do not lump rows.
- Notification date 19.12.2017 = the reference date for limitation/timeline purposes.

## Filing pattern (drive + tracker)
- Convert the WhatsApp image set into ONE PDF (PIL: `imgs[0].save(out, save_all=True,
  append_images=imgs[1:], resolution=200.0)`); name `YYYYMMDD_BBMP_TDR_Notification_...
  _Sy<no>.pdf` (date from the notification, not today's date).
- File into the project legal folder via Drive API `files().create(media_body=
  MediaFileUpload(...))` — note **MediaFileUpload**, not BytesIO (googleapiclient raises
  `TypeError: media_filename must be str or MediaUpload` on raw BytesIO).
- **Privacy**: see `draas-drive-organization` → `references/file-privacy-inherited-permissions.md`
  — a folder's grants inherit to new files; to make a file PRIVATE, place it in the owner-only
  TMP folder (or remove inherited permissions at the folder level), because inherited
  permissions cannot be deleted per-file via the Drive API.
- Tracker: one row (assignee = revenue SPOC, e.g. Vinod/Rahul for khata work) capturing the
  application → release deed → khata-reduction → south-road 2x TDR investigation → plan-
  sanction strategy, with the notification Drive link in O/P.

## Pitfalls
- **Vision/OCR of the schedule is unreliable for the row that matters** — rows are
  contiguous and visually similar; the vision description is fine for context but re-check
  the specific row (Sl.No, survey, area, owner) before quoting it in a filing.
- The notification says "receive twice the area of land surrendered" — that is the TDR
  multiplier, not a khata reduction. The khata REDUCES by the surrendered area; the TDR is
  granted as notional land usable elsewhere (receiving plot), per the rules.
- FORM-1's claim window is short (10 days from notification) but the right to claim is not
  lost on the date — practice post-dates it; don't tell the user the window has closed
  without checking.
- **Acreage ≠ khata area.** 1 Ac 28 Guntas (60,984 sqft) is the ORIGINAL survey 14/1 total
  (MR 36/1980-81); the amalgamated khata is 53,148; the buildable physical land ~43,000.
  Compute on the khata figure the user names, and flag when the e-khata differs from the
  recital narrative (see `northstar-area-evolution-worked-example.md`).