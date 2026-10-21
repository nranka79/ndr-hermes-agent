# Preliminary Title Report Analysis (Karnataka scanned title opinion)

Worked example: BRK Law / Jayanth Pattanshetti Associates LLP preliminary title report for
Gunjur Sy. No. 40, 18A 21G, Doddaballapur (03-Sep-2026, File 158/25, 24 scanned pages,
email from krishna@brklaw.in with two attachments: report + Bill No. 99).

## When to use

- User forwards a **preliminary title report / title opinion** PDF (typically scanned, 15–30 pp)
  from a Karnataka law firm (Pattanshetti, BRK Law, Indus Law, etc.)
- Ask is usually: "what does the opinion say, what are the caveats, is it a clean/clear title opinion?"

## Pipeline

1. **Find the email + both attachments** — the report email almost always arrives with the firm's
   fee bill as a second attachment. Extract both, note bill no./amount for the invoice family
   check (see payment-tracing skill: older part-fee bills get credited as "Less: Amount received").
2. **pdftoppm render** at 150 dpi: `pdftoppm -r 150 -png report.pdf pg` — then `vision_analyze`
   on each page with "Read ALL text exactly" prompts. Optionally `pdftotext` first: some scanned
   files have an embedded OCR text layer (order sheets did here) — try pdftotext before rendering.
3. **File alongside the source deeds** — the opinion cites the exact registered deeds it examined
   (sale deed dates + doc. numbers). Search Drive for those sibling deeds; the folder that holds
   them (e.g. "Copy Gunjur-Doddaballapur") is the right home, NOT a generic legal folder.
   Rename per NDR convention: `YYYYMMDD_Project_DocumentType_Firm.pdf`.
4. **Extract the opinion in three tiers** (this is the substance):
   - **Chain of title** — list every registered transaction w/ doc. numbers, dates, parties.
     Two parallel chains often converge on the current owner (here: 9A21G via B. Thippaiah grant
     → Sale Deed 20-09-2004; and 9A via govt. sale to Patel Hanume Gowda → Ahmed Shariff 1970 →
     defect 1988 deed → joint 1993 deed to Jarava Bai → WILL 1994 → Dharmesh).
   - **Opinion language levels** — watch for the difference:
     * "**valid and marketable title**" — strong (per-parcel)
     * "**may be considered valid and marketable, subject to verification and the other
       qualifications set out in this report**" — conditional (per-parcel)
     * "**absolute owner**" (Section 9.1) — the overall holding, but still qualified.
     Report each per-parcel level, not just the headline.
   - **Caveats / documents to be furnished** — the firm lists 15–25 outstanding items at the end
     (grant order/grant certificate/caste certificate, sale certificate + upset-price receipt for
     old govt. purchases, O.S. court records, old ECs 1940-2004, acquisition endorsements from
     LPA/KIADB/KHB/NHAI, gap-year RTCs, public notice, originals for verification). The clean-title
     gap is the intersection of these with what the user actually holds.
5. **Cross-reference litigation** — the opinion's "settled/withdrawn" suit may still have living
   descendants; e.g. O.S. 196/1991 (Ahmed Shariff vs Hanume Gowda heirs, settled, led to 1993
   deed) was followed decades later by **O.S. 95/2008 — Shariff's wife/children claiming they
   never sold**. Verify the on-Drive case file before quoting the opinion's settlement fact.

## Canonical report structure (Pattanshetti format)

- Cover page: addressee, property description, "Encl: Title Search Report", use/disclaimer
  (preliminary — not to be relied on by third parties)
- "Discussion on Title" paragraphs (2.x): chain per parcel with registered doc. numbers
- "Revenue Records/Mutations" (4.x): mutation register serials + IHC/order numbers
- RTC history tables (period/owner/cultivator/remarks) — includes the computerisation-error
  rectification saga (37A-02G wrong extent vs actual 18A-21G, AC order dated 18-05-2026)
- Endorsements (7.x): 48A/77A nil cert, PTCL nil endorsement (e.g. No. PTCL(Do)(End)/C.R:387/2026)
- Encumbrance Certificates (8.x) — note the EC gap periods explicitly
- **Section 9.1 Opinion** — the absolute-owner holding
- **Annexure A**: Standard Exceptions to the Title Search (8 items: post-date defects, undisclosed
  testamentary dispositions, survey-disclosed encroachments, off-record claims, undisclosed
  easements/liens, tax/assessment liens, corporate matters, undisclosed suits)
- **Annexure B**: Description of Documents table (doc no. → date → description with registration
  numbers)
- Documents to be furnished list (numbered, the caveat engine)

## Pitfalls

- **Opinion "to the extent of"** — an absolute-owner opinion may still be per-parcel scoped;
  check the extent wording on each parcel.
- **Missing original grant papers** is the #1 caveat for granted (darkasth) agri land — grant
  order, grant certificate, saguvali chit, upset-price receipt. The opinion cites the NOC/
  endorsement as reliance but still flags originals.
- **Old suit files may live inside a NEWER case folder** (O.S. 196/91 exhibits sat inside the
  O.S. 95/2008 folder because they were re-used as evidence). When asked "do we have OS holdings
  for X", search by case-number strings AND folder-name; don't expect a dedicated folder.
- **Bill may be raised on a relative not the user** (here: on Dharmesh Ranka) — the tracker/
  finance person is still NDR's SPOC.