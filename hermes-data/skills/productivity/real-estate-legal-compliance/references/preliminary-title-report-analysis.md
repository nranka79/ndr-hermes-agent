# Analyzing a scanned Preliminary Title Report (advocate's opinion letter)

Worked example: Jayanth Pattanshetti Associates LLP (BRK Law, Infantry Rd
Bengaluru) Preliminary Title Report for Gunjur Sy. No. 40 (18A 21G,
Doddaballapur Taluk), received as 24-page scanned PDF + bill PDF attachment
via Gmail 2026-09-03 from B. R. Krishna (krishna@brklaw.in).

## When to use

- An advocate emails a "Preliminary Title Report / Title Opinion" (scanned PDF)
  with a companion fee bill, after a request for title due diligence
  (often on the NIL PTCL & 48A endorsement track).
- User asks: "what does the opinion say, what are the caveats, is title clear?"

## Workflow

1. **Locate the email** in Gmail via `from:` + subject keywords
   (`"title opinion" survey 40`, advocate's domain, project name). Walk the
   payload for attachments (`messages().get(format='full')` → recursive
   payload walk collecting `filename` + `body.attachmentId`). Emails like
   this carry exactly TWO PDFs: the report (multi-page scan, MBs) and the
   fee bill (1 page).
2. **Download both** with `messages().attachments().get` (base64
   url-safe-decode `data`), save to /tmp.
3. **Render the scan**: `pdftoppm -r 150 -png report.pdf pgs` then
   `vision_analyze` page-by-page. The PDF has NO text layer — vision is the
   only way. Fixed structure to expect (Pattanshetti format):
   - pg1: cover — addressee (often **Dharmesh D. Ranka**, not NDR), land
     description, purpose ("determine marketability"), limitation/use-only
     disclaimers, "Encl: Title Search Report"
   - continuation sheets 2.1..2.x: discussion of title — one sub-section per
     source line/parcel, each citing deeds by date + registration number
     (e.g. Sale Deed 20-09-2004 DBP-1-02596/2004-05, Sale Deed 02-01-1970
     2569/1969-70, Sale Deed 20-05-1993 302/1993-94, GPA 02-04-1993, Will
     03-12-1994, O.S. 196/1991)
   - revenue/mutation sections (RTCs by year bands, MR serials, inheritance
     certificates), survey section (Akarband, Tippany), endorsements
     (48A/77A nil, PTCL nil), EC window
   - **Section 9 Opinion** (near end): the operative finding; here "absolute
     owner" BUT with two different qualification levels per parcel:
     "valid and marketable title ... subject to verification of ..." vs
     "may be considered valid and marketable, subject to verification and
     the other qualifications set out in this report"
   - **document list to be furnished** (the caveat to-do: original Grant
     Order/Grant Certificate/Caste Certificate/upset-price receipt,
     Hanume Gowda sale certificate + receipt, O.S. records, death certs,
     EC 1940-2004 & to-date, public notice, originals)
   - Annexure A: standard exceptions (post-report defects, undisclosed
     testamentary dispositions, encroachments needing survey, etc.)
   - Annexure B: schedule of documents examined
4. **File per NDR convention** `YYYYMMDD_Entity_Description` underscore-only:
   - `20260903_GunjurSy40_PreliminaryTitleReport_JayanthPattanshettiLLP.pdf`
   - `20260903_GunjurSy40_Bill99_ProfessionalFees_JayanthPattanshettiLLP.pdf`
   Upload to the project's land-records folder — for Gunjur Sy 40/39/41 the
   folder is **Copy Gunjur-Doddaballapur** (holds the exact source deeds the
   opinion cites). Choose the folder that mirrors the cited source docs, not
   the generic "Legal Files" litigation folder.
5. **Answer the "clear title?" question honestly**: a PRELIMINARY opinion is
   conditional. Report (a) the operative owner finding verbatim, (b) the
   per-parcel qualification level, (c) the concrete outstanding document
   list, (d) the bill balance (professional fee − amount received),
   (e) the live-litigation flag if any cited suit is still contested.

## Pitfalls

- **Bill party ≠ email sender**: report is on Pattanshetti letterhead while
  the covering email is from krishna@brklaw.in (BRK Law); bill is raised on
  Jayanth Pattanshetti Associates LLP billhead addressed to Dharmesh Ranka.
  Report the firm + bill details as read, don't assume one entity.
- **The opinion's cited suit may still be LIVE**: the report claims O.S.
  196/1991 was settled/withdrawn; the plaintiff's family (Ahmed Shariff's
  wife + children, i.e. Khurshudunissa et al.) later filed **O.S. 95/2008**
  claiming they never sold — the full 196/91 order sheet + exhibits survive
  on Drive inside the OS 95/2008 folder. Always cross-check a suit cited in
  an opinion against the tracked cases before calling title "clear".
- **Cross-reference the 48A/PTCL endorsements**: unfinished title work often
  intersects the NIL PTCL & Section 48A endorsements (grant clearance)
  track — the opinion's endorsement sections ARE the deliverable that track
  awaited.
- **Same-name family-tree evidence tasks**: when settlement strategy relies
  on disproving a claimant's family connection to the original title holder
  (e.g. Rafiq & Badrurisa vs Ahmed Shariff), the deliverable is identity
  cards + family tree docs — a trackable P-xxx task with a commitment-date
  ask, not a document-analysis task.