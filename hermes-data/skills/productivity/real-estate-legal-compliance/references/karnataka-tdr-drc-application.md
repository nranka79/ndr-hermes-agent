# Karnataka TDR / DRC Applications — Sec 14-B KTCP Act (BBMP)

Class-level workflow for preparing Transferable Development Rights / Development Rights
Certificate application packs when a DRAAS project's land is acquired (or proposed/notified
to be acquired) by BBMP for a public purpose — road widening, stormwater drain, lake-side
road, etc. Verified Sep 2026 on **Ranka Northstar / Allalasandra, Sy No 14/1** (lake-side
road acquisition, 499.66 sqm).

## Legal basis

- **Sec 14-B, Karnataka Town and Country Planning Act, 1961** — surrender of land reserved
  for public purpose in lieu of Development Rights Certificate (DRC) / TDR.
- **Karnataka Town and Country Planning (Benefit of Development Rights) Rules, 2016** —
  forms and procedure. Form numbers:
  - **Form I** (see sub-rule (1) of rule 3) — the acquisition NOTIFICATION issued by the
    BBMP division Executive Engineer (the "Form 1 notification" the affidavit recites).
  - **Form IV** (Annexure-6, see sub-rule (4) of rule-3) — "Option for Development Rights
    Certificate by the Applicant" — the landowner's surrender/application letter.
- TDR entitlement per the notification: **2× surrendered land area** as notional
  development rights, plus **1× building area** surrendered (factored by valuation).

## Form I notification — anatomy

Issued by: Office of the Executive Engineer, [Division], Road Infrastructure, BBMP
(letterhead carries division email e.g. `bbmpeerivnk@gmail.com`). Number format:
`No. EE/YNK/TDR/03/17-18` (division / TDR / serial / FY) — **dated** on the document
(19.12.2017 in the worked case). Contains:

- Purpose recital: "…required by The Commissioner, BBMP (Public Authority) for
  development and [purpose] for implementing the proposals of the Approved Master Plan…"
- Claim window: landowners must appear and submit claims **within 10 days** with title
  deeds, up-to-date RTCs, mutation copy, tax paid receipts, **conversion order for
  non-agriculture**, revenue sketch, **akar bandh**.
- **SCHEDULE table** (page 2): Sl No | District | Taluk | Village | Sy.no/Khata no | Type of
  land | Nature of land | Area (sqm) | Name and address of landowner/interested persons.
  Handwritten margin annotations like "PRC / PRC issued" = Property Register Card notes.
- Signed by Commissioner, BBMP; "Copy submitted to" distribution list of ~16 offices.

## Template set (from samples NDR holds)

**Affidavit on ₹100 e-Stamp** (2 pages, sample was Article-4 Affidavit, purchased by the
deponent, Second Party = the public authority):
- Page 1 = the e-stamp certificate itself (Certificate No, Unique Doc Ref, First/Second
  Party, stamp duty ₹100, notary/agent stamps). Only page 2 is the actual affidavit text.
- Page 2 recital: "The aforesaid land is partly acquired for the Construction of [project]
  … from BBMP vide FORM I Notification No.[no] dated [date] for an extent of [X] Sq mtr for
  the Public Authority for Grant of Development Rights Certificate as compensation in
  respect of the Land bearing Survey No/Khatha No.[no] of [village] of [hobli] Hobli,
  [taluk] Taluk."
- Key clause: "I have neither taken any monetary compensation nor compensatory FAR from any
  Department of Government of Karnataka or Government of India, nor claimed TDR in lieu of
  the said land either; I am entitled for TDR and grant of Development Rights Certificate
  under Section 14-B…"
- Execution blocks: Identified by [Advocate], DEPONENT, SWORN TO BEFORE [Notary] — **physical
  execution on e-stamp paper; cannot be generated digitally** — leave blank for execution.

**Form IV (Annexure-6)** — one page template:
- From: Name of owner + Address → To: [authority].
- Body: "I, intend to surrender the under mentioned land bearing Survey No/Khatha
  No…of…Village of…Hobli and…Taluk reserved for the public purpose of…as per the Master
  Plan or for the Public Authority to grant of Development Rights Certificate. I/We
  forwarded herewith the following:-"
- **The 9 attachments checklist (verbatim):** Site plan as per Master Plan; Title Deed &
  Mother Deed; RTC / Khatha Certificate and latest assessment book extract; Up-to-date tax
  paid receipt; Encumbrance certificate (E.C); Conversion Copy and Sketch; Building Plan
  Copy; Affidavit; Aadhaar Card.
- Closing request + Signature of the Owner(s) of the land.

## GPA authority verification — when developer/GPA holder signs

The TDR application forms (Form IV &amp; Affidavit) must be signed by the landowner(s)
or their duly authorised GPA holder. When the developer acts as GPA holder, follow this
verification pattern BEFORE producing the forms.

### Locate + read the operative GPA

Search Drive for `name contains 'GPA' or 'Power of Attorney'` AND the property
Sy no / project name. The relevant GPA is the one **from the landowners to the
developer entity** (not inter-owner GPAs for individual representation, e.g.
Kankshita → V. Swaminathan).

**OCR the registered GPA** — it's scanned with no text layer:
```bash
pdftoppm -r 300 -gray gpa.pdf png/p
for f in png/p-*.pgm; do tesseract "$f" "${f%.pgm}" -l eng --psm 6; done
cat png/p-*.txt > gpa_all.txt
```

### Clause-by-clause mapping to TDR

The 2014 Ranka Northstar GPA (07.02.2014, SRO Malleshwaram, Doc MLS-4-00321/2013-14,
22 pages) covered the TDR application through these clauses:

| Clause | Text summary | Relevance to TDR |
|--------|-------------|------------------|
| 16 — General authority | "To sign and submit necessary applications, petitions, memorandum, **affidavits**, undertakings… and to represent [the owners] before the Revenue Authorities, **authorities under the Karnataka Town and Country Planning Act**, BDA, BESCOM… or any other local bodies or statutory authorities, State Government, etc., **in connection with all or any matter pertaining to the Schedule Properties**" | A TDR/DRC claim under Sec 14-B KTCP Act is a matter before a KTCP authority pertaining to the Schedule Properties. DIRECTLY COVERS the application + affidavit. |
| 21 — Statutory clearances | "To submit applications, affidavits, statements, returns to the Government of Karnataka and/or authorities under any state or central statute, to obtain necessary clearances, exemptions, sanctions and permissions required under any applicable law" | Covers obtaining TDR certificate as a statutory permission/clearance. |
| 22 — Acquisition proceedings | "To appear for and represent [the owners] before the **Land Acquisition Officer** and other Officers in respect of acquisition proceedings pending if any or any that may arise and take such steps as are required for clearing the Schedule Properties from the acquisition proceedings by signing and executing necessary documents, petitions, applications" | The BBMP road acquisition is the trigger for the TDR. Covers representation in acquisition. |
| 27 — General power | "To generally do all such acts, deeds and things as may be necessary" | Residual catch-all |
| 29 — Ratification | "We do hereby agree to ratify and confirm whatever acts, deeds and things lawfully and bonafide done by our ATTORNEY… notwithstanding the fact that no Special Power in this behalf is contained in these presents" | Owners cannot later challenge any act done under the GPA. |

### The entity identity trap

⚠️ **The GPA is in favour of a specific company — NOT the individual director and NOT
the JDA assignee.** In the Ranka Northstar case:
- **GPA**: from 7 landowners **TO M/s DRA PROJECTS PRIVATE LIMITED** (represented by its
  Director, Dinesh Ranka at execution).
- **JDA developer rights**: assigned in 2021 from DRA Projects to **DRA RANKA HOLDINGS**
  (a partnership firm).
- **GPA status**: continues with DRA Projects Pvt Ltd — it was NOT automatically transferred
  to DRA Ranka Holdings with the JDA assignment.

The signature block MUST name the GPA holder entity correctly:
```
For M/s DRA PROJECTS PRIVATE LIMITED
(GPA holder of the landowners, per GPA dated 07.02.2014
 registered at SRO Malleshwaram, Doc MLS-4-00321/2013-14)
As its Director, Mr. Nishant Ranka
```
NOT "For DRA Ranka Holdings" and NOT "Nishant Ranka personally".

If the operator/developer entity has changed (JDA assigned away from the GPA-holder company),
you need either: (a) a fresh GPA from owners to the current entity, or (b) execution by the
original GPA-holder company through a director who is also part of the current developer group.
The current director CAN sign — the power is to the **company**; any current director
exercises it for the company. A board resolution authorising the specific director for this
application makes it airtight.

### Form structure change — GPA holder execution block

When the signatory is the GPA holder, NOT the individual owners:

1. **Owner identification block** — list all owners with full details (name, parent,
   age, address, Aadhaar/OCI) as the "Deponents"/"Applicants". Unchanged from the owner-signed
   version.

2. **"ACTING THROUGH GPA HOLDER" block** — add a styled callout box (light grey background,
   3px left border) immediately after the owner list:
   ```
   ACTING THROUGH GPA HOLDER:
   The [Deponents/Applicants] are represented in this [application/affidavit]
   through their registered Power of Attorney dated [DATE] registered at SRO [NAME]
   as Document No. [NUMBER], by which they have nominated, constituted and appointed
   [COMPANY NAME] as their true and lawful attorney in respect of the said property.
   Accordingly, the [Deponents/Applicants] are represented by their said GPA holder
   [COMPANY NAME], represented by its Director, [DIRECTOR NAME] (Aadhaar No. [XXXX]),
   who is duly authorised to sign, execute and submit this [application/affidavit]
   on behalf of the [Deponents/Applicants].
   ```

3. **GPA recital paragraph** (in the Affidavit body) — add a numbered paragraph stating
   that the GPA specifically authorises signing applications/affidavits before KTCP authorities
   for the property, and that a certified copy is annexed as Annexure-GPA.

4. **Signature block** — single execution line:
   ```
   M/s [GPA HOLDER COMPANY NAME]
   (GPA holder of the [Deponents/Applicants])
   Represented by its Director, [NAME]
   ___________________________
   (Signature — Director, for [Company], as GPA holder)
   ```
   Remove individual owner signature lines. They are already listed in the body; execution
   through the GPA holder is the operative signature.

### Annexure-GPA

Add a **numbered attachment** to the pack:
- Cover page ("ANNEXURE-GPA — Certified copy of Registered GPA dated [date]")
- Full registered GPA scan (or the relevant pages including the powers clause and
  registration endorsement)

In **Form IV**, add the GPA to the 9-attachment check list as item **10**:
```
10. Power of Attorney (Annexure-GPA) — Registered GPA dated [date]
    authorising the GPA holder to sign and submit this application.
```

In the **Checklist/Index**, add a row at the top:
```
3A. ANNEXURE-GPA — Certified copy of Registered Power of Attorney
    dated [date] ([Company] as GPA holder of landowners)  — ENCLOSED
```

### File replacement pattern

After building the updated forms:
1. DELETE old Form IV and Affidavit files from the Drive folder
2. UPLOAD new versions with descriptive filenames:
   - `02_FORM_IV_Filled_by_[Company]_Director.pdf`
   - `03_Affidavit_Filled_by_[Company]_Director.pdf`
3. UPLOAD `07_ANNEXURE_GPA_Registered_POA_[date].pdf` as a new file
4. UPDATE the checklist/index file to reflect the new rows
5. DELETE old index file if overwritten

Since the **sent email referenced a folder link, not individual file names**, the
updated files are visible to the recipient automatically — no email correction needed
for the file-level update. Send a threaded reply draft flagging the revision as a
courtesy.

## Workflow (verified Sep 2026)

1. **OCR the templates** — samples arrive as scanned PDFs with NO text layer
   (`pdftotext` returns empty). Convert: `pdftoppm -r 200 -png <in.pdf> <out>` then
   `vision_analyze` each page. For a truncated header/notification number, re-render at
   higher DPI and crop the top band (`PIL` crop ~55% height) — the full "No. EE/…/FY"
   line only reads cleanly at 400 DPI.
2. **Pull the notification from Drive** — NDR shares it the day before ("refer to the
   notification I added yesterday"). Search `name contains 'TDR' or 'notif' or 'Northstar'`;
   find the `…_BBMP_TDR_Notification_…Sy14-1.pdf`; download via
   `drive.files().get_media()` (scanned too — same OCR path). Extract the schedule row for
   DRA's survey number (owner name per schedule, extent).
3. **Fill what is derivable WITHOUT asking**: notification no + date, survey no, village,
   taluk, extent, purpose text verbatim, TDR math (2× extent), addressee (the Executive
   Engineer division office from the letterhead). Compute DRC entitlement and present it.
4. **ASK before producing anything** — NDR's explicit gating: "Ask me before making HTML,
   before making PDF, before making any packs. Let's first get all the details filled in."
   The gaps that ALWAYS need him: (a) who signs as owner/deponent — the notification
   schedule owner (e.g. "Ashwathamma") may NOT be the current JDA holder; get full name,
   father's/husband's name, age, complete address, Aadhaar no; (b) hobli (sample used
   "Yelahanka 1 Hobli" — confirm for the village); (c) which attached documents exist
   (esp. **conversion order** — explicitly demanded by both notification and Form IV;
   RTC/khatha, EC, building plan, master-plan site plan).
5. **After confirmation**: rebuild each template as HTML styled to match the original
   (layout, dotted blanks), convert to PDF via `chrome-headless-shell` (see Production pipeline
   for the exact binary + flags), assemble the pack (filled Form IV + affidavit + existing
   attachments from Drive), merge as one PDF, and produce a **missing-document checklist** for
   procurement. If the GPA holder signs instead of individual owners, apply the GPA authority
   verification pattern above before building the forms.

## Worked case — Ranka Northstar Sy No 14/1 (Sep 2026)

- Notification: **No. EE/YNK/TDR/03/17-18 dated 19.12.2017**, Form I, BBMP Executive
  Engineer Yelahanka Division Road Infrastructure (#208, 2nd Fl, Annex-3, N R Square,
  Bengaluru-560002). Purpose: "Comprehensive Development of road by side of Allalasandra
  Lake (southern side) to connect Allalasandra Village and Chikkabommasandra"
  (Nagarothanna scheme, GO UDD.199.SFC.2016 dt 21.06.2016). Schedule row: **Sy No 14/1**,
  Allalsandra, Bengaluru North Taluk, Agricultural/Open Space, **499.66 sqm**, owner per
  schedule **Ashwathamma**. Total schedule 7202.04 sqm.
- TDR math: 499.66 × 2 = **999.32 sqm DRC**.
- Drive assets found: 20260922 Boundary Survey Sketch + Sy14-1 SurveyBoundary R12 DXF +
  Village FMB (Attalikoppa sheet) under `Ranka Northstar/01_Approvals_and_Title`;
  "current TAX PAID Ranka north star allasandra.pdf"; 20260831 Guidance Value attested;
  Judicial Layout Approved Plan; 2014 JDA (Swaminathan & others).
- **Deep-dive resolution (same session, follow-up):**
  - **Conversion order NUMBER FOUND** — not spelled "conversion order" anywhere; it is the
    **Official Memorandum No. ALN(NAY)SR/60/2016-17 dated 06.01.2018** from the Deputy
    Commissioner, Bangalore District (agri → non-agri **residential**, 1 Ac 8½ G = Items 1–8),
    preceded by Demand Note ALN(NAY)SR/60/2016-17 dt 30.12.2017 + conversion-fine SBI receipt
    dt 01.01.2017, recorded via MR No. T4/2017-18 … T11/2017-18. Source: Anup Shah Law Firm
    title report (Jun 2020), Drive `DRA Projects - Allalasandra - Title Report Anup Shah
    JUN2020.pdf`. ⚠️ The **copy of the 2018 OM is not on Drive** — only the number. If the
    number is found but the copy isn't, put the number in the pack and route the copy request
    to Rahul (vkdas) via Telegram.
  - **EC FOUND** — `ECC-29012026-9695960.pdf` dt 29.01.2026, search window 01.01.2004–
    29.01.2026; sole encumbrance = JDA 07.02.2014 (Doc MLS-1-03034-2013-14). Older ECs also
    on Drive (1967–2013 RTC register scan, 54 pp — handwritten, OCR useless; treat as record).
  - **Khata FOUND** — amalgamated **591/1077/14/1/1**, ePID 4457904186, e-Khatha doc 2844641
    (issued 10.02.2025), 53,148 sq ft; tax receipts 2024-25 & 2025-26; khata certificates\
    45-page PDF in the Rahul title pack.
  - **Owners — 7 joint owners** (per e-Khatha + signed Addendum 30.11.2024): R. Geeta
    Swaminathan; Kankshita Swaminathan (rep. by GPA holder V. Swaminathan, GPA 18.08.2003);
    V. Swaminathan (s/o late R. Venkataraman — holds V. Rangammal's share via her will
    13.11.2009, Doc 56/2009; she died 02.08.2017); A.S. Vaidyanathan; Lakshmi Vaidyanathan;
    Sreeraman Vaidyanathan; Sunder Padmanabhan. V. Swaminathan's Aadhaar **3176 0609 8349**
    appears in the addendum. Owner addresses come from the e-Khatha English fields (see
    OCR reference). Aadhaar copies folder on Drive holds 6 of 7 (Kankshita's missing —
    she is US-based; flag "provided separately").
  - **Addendum 30.11.2024** (signed, `20241130 Signed Addendum 2 JDA Allalsandra Site No
    1 to 8 (DRA Ranka Holdings).pdf`) — the "latest amended JDA addendum": owners keep
    33% BUA at 1.75 FAR + **15% of SBUA attributable to additional FAR incl. TDR/premium**
    (so this TDR is partly the landowners' entitlement). Registration of the addendum was
    pending Sep 2026 (GPA/apostille logistics) — check registration status before citing it.
- Genuinely absent (do not invent): **building plan copy** (never existed), **site plan as
  per Master Plan** (no master plan for the site) — mark N/A with NDR's confirmation.
- Tornado check: a numbered pack "01 – Form 5.pdf … 09 – Declaration (Form B).pdf" uploaded
  same day by Prakash was **RANKA UDAYA – TN RERA Documents (TN30_LO_0642_2026)** — a
  different project; do not fold it into the TDR pack without checking the parent folder
  name first.

## Pack production run — confirmed answers and delivery (Sep 2026, follow-up pass)

After the research pass, NDR answered the gating questions and the pack was built end-to-end.
Confirmed decisions (reuse these as defaults for the next TDR pack unless overridden):

- **Addressee = The Executive Engineer, Yelahanka Division, Road Infrastructure, GBA
  (formerly BBMP), #208, 2nd Fl, Annex Bldg-3, N R Square, Bengaluru – 560002.**
  There is no BBMP in the name anymore — GBA (Greater Bengaluru Authority). NDR: "start with
  Executive Engineer"; only switch to Commissioner if the original Affidavit sample says so.
- **Hobli/Taluk line = "Yelahanka Hobli, Bengaluru North (Additional) Taluk"** — confirmed as
  the operative line; the EC's "Yalahanka 2 Hobli" is just the SRO zone.
- **Conversion OM copy**: put the NUMBER (ALN(NAY)SR/60/2016-17 dt 06.01.2018) in the text and
  add a **placeholder slot page** inside the pack ("CERTIFIED COPY TO BE INSERTED — SLOT
  RESERVED" box). Rahul (vkdas) ordered to trace the certified copy → WhatsApp deep link to
  his WORK number **+91 99000 93813** (not on the Telegram registry — WhatsApp link only,
  nothing auto-sent).
- **Kankshita (US resident, OCI only now)**: give her Aadhaar number + OCI card number in the
  form; her OCI copy was NOT on Drive (name/fullText/recent searches missed it — if so, tell
  NDR outright, don't hunt forever). Her e-Khatha Aadhaar is masked (`xxxxxxxx543E`).
- **Physical execution** (₹100 e-stamp, notary, 7 owner signatures): placeholders in the HTML
  — never fabricate; NDR's team executes.
- N/A rows in the attachment list: Site plan per Master Plan (no master plan) and Building
  Plan Copy (never existed) — marked N/A with NDR's confirmation, not chased.

### Owner roster with addresses (from e-Khatha English fields — reusable for any Sy 14/1 doc)

1. R. Geeta Swaminathan (w/o V.S., ~76) — No. 357, 1st Cross, Canara Bank Layout,
   Vidyaranyapura Post, Bengaluru 560097
2. Kankshita Swaminathan (d/o V.S., ~49) — 230 Mainsail Way, Madison, Alabama 35758, USA;
   permanent add. 357 1st Cross Canara Bank Layout, Vidyaranyapura, B'lore 560097; rep. by
   GPA holder V. Swaminathan (GPA 18.08.2003)
3. V. Swaminathan (s/o late R. Venkataraman, ~82) — 357 1st Cross Canara Bank Layout,
   Vidyaranyapura; Aadhaar 3176 0609 8349; holds Rangammal's share (will 13.11.2009, doc
   56/2009; she died 02.08.2017)
4. A.S. Vaidyanathan (s/o A.K. Sriraman, ~80) — No. 202, Sterling Court, No. 21 Kanakapura
   Rd, Basavanagudi, B'lore 560004
5. Lakshmi Vaidyanathan (w/o A.S.V., ~75) — No. 4084, Prestige South Ridge, Hosakerehalli
   Cross, Banashankari 3rd Stage, B'lore 560085
6. Sreeraman Vaidyanathan (s/o A.S.V., ~47) — same address as #5
7. Sunder Padmanabhan (s/o S.P., ~66) — No. 401-A, Riddhi Siddhi Bldg, 5th Rd, Chembur,
   Mumbai 400071

Developer/JDA other party: DRA Ranka Holdings, No. 4 Ranka Chambers, 31 Cunningham Rd,
B'lore 560052 (partnership deed 06.07.2020; assignment 15.03.2021 doc 5695; NDR Aadhaar
4159 0535 2796).

### Production pipeline (VPS-verified)

- **HTML → PDF: use the Playwright chrome-headless-shell, NOT weasyprint** (weasyprint is
  not installed on this VPS). Find the binary dynamically (version number changes):
  ```bash
  find /opt/hermes/.playwright/ -name 'chrome-headless-shell' -type f 2>/dev/null | head -1
  ```
  That gives e.g. `/opt/hermes/.playwright/chromium_headless_shell-1234/chrome-headless-shell-linux64/chrome-headless-shell`.
  Use with flags `--headless --disable-gpu --no-sandbox --print-to-pdf=out.pdf
  --no-pdf-header-footer file:///abs/path.html`. Set `@page { size: A4; margin: ... }` in
  the HTML style.
- **Merge: `qpdf --empty --pages a.pdf b.pdf ... -- out.pdf`** — exit code 3 with
  "stream keyword followed by extraneous whitespace" warnings is OK; verify pages via
  `pdfinfo`.
- **JPEG → PDF: gs -sDEVICE=pdfwrite fails on some DRA Aadhaar JPEGs** — use PIL instead:
  `Image.open(f).convert('RGB').save(f.replace('.jpg','.pdf'),'PDF',resolution=150)`.
- **Binary Drive upload**: `gws_drive_create_file` is text-only — use
  `build_service('drive','v3',service_name=...)` + `MediaFileUpload` +
  `files().create(body={'name':..., 'parents':[...]}, media_body=..., fields='id,name,size')`.
- **HTML write-size pitfall**: ONE `write_file` containing a full 2-page form HTML
  stream-times out. Split the HTML into p1/p2/p3 fragment files (each well under ~8K
  tokens) with `write_file`, then `cat p1 p2 p3 > final.html`.
- **Delivered shape** (reuse): pack folder on Drive `TDR_DRC_Application_Sy14-1_RankaNorthstar`
  containing `01_TDR_Application_Pack_FULL_NNp.pdf` (merged: index/checklist → Form IV →
  Affidavit → Annexure-GPA cover + GPA scan → notification → property details → e-Khatha →
  EC → tax receipt → FMB → boundary sketch → Aadhaars/OCI; 12–13 MB), plus individual
  `02_FORM_IV_Filled_by_[Company]_Director.pdf`, `03_Affidavit_Filled_by_[Company]_Director.pdf`,
  `04_Index_and_Checklist_v2.pdf`, `05_Conversion_Order_SLOT_placeholder.pdf`,
  `06_[Owner]_OCI_Card_....pdf`, `07_ANNEXURE_GPA_Registered_POA_[date].pdf`.
  Keep the big title-deed volume (sale deeds, amalgamation, JDA, addendum — ~50 MB) as a
  Drive folder + index row, NOT inside the merged pack.
- **Folder-level sharing means file swaps need no email correction**: when the hand-off email
  links the Drive FOLDER (not individual files), replacing files inside it is immediately
  visible to the recipient. Verify with `gws_gmail_search("from:<me> to:<recipient> <topic>")`
  whether the original email was actually SENT (check `labelIds` contains `SENT`) before
  assuming you must first send a pending draft — then send only a threaded reply-draft noting
  the revision.

## Pitfalls

- Scanned templates have no text layer — `pdftotext` gives nothing; go straight to
  pdftoppm + vision.
- The notification number line is easy to truncate at default OCR DPI; the full
  `No. EE/YNK/TDR/03/17-18` with date needed for the affidavit recital only emerges at
  400 DPI on a cropped top band.
- e-Stamp + notary/advocate execution cannot be faked digitally — leave those blocks blank
  and tell NDR the physical execution step remains.
- Don't assume a folder of numbered PDFs belongs to the current pack — verify the parent
  folder name (namespace it: RANKA UDAYA – TN RERA vs Ranka Northstar TDR).
- The notification's schedule owner name is a 2017 snapshot — current title may have passed
  to JDA parties; never put the schedule name in the affidavit without NDR's confirmation.
- **Near-name JDA addendum trap:** a Drive file named "Addendum to JDA 03.04.2010 (regd
  12.12.2014 …)" can belong to a DIFFERENT project (Kolte Patil/Mirabilis), not the current
  Northstar addendum — always OCR the parties block (BETWEEN…) before trusting the file name;
  41 MB scans are often the wrong decade.
- **Conversion order ≠ the phrase "conversion order".** In Karnataka title reports it appears
  as an **Official Memorandum** from the Deputy Commissioner with an `ALN(NAY)SR/…`-style
  serial + a Demand Note + a conversion-fine receipt + MR extract numbers. Grep OCR output
  for `conversion|memorandum|ALN|MR No` to pin the number.
- **EC "Hobli: Yalahanka 2" is an SRO zone code** — the correct revenue line is
  "Yelahanka Hobli, Bangalore North (Additional) Taluk" from the khata/title report; don't
  copy the EC's hobli verbatim into the affidavit.
- **e-Khatha / old-RTC Kannada fonts:** `pdftotext` garbles the Kannada glyphs but the
  ENGLISH fields (owner names, masked Aadhaar, khata/ePID numbers, document registers,
  dates) are embedded cleanly — read those without OCR-ing the Kannada columns.
- **Batch OCR scanned legal PDFs with a background loop, not one big pass**: `pdftoppm -r
  150 -png <pdf> <out>` per file, `tesseract <img> <base> -l eng --psm 3` per page, then
  `cat` per-page txt into `<tag>_all.txt`. Run the whole thing as one background shell
  script with `notify_on_complete` (173 pages ≈ 5 min) and grep the aggregates — keeps the
  main context clean.
- **Document identity is established by OCR of parties/recitals, never file name** — the
  "Addendum to JDA 03.04.2010" file was the Kolte-Patil/Mirabilis addendum, and a "Title
  Deeds sy no 14/1" Google Doc turned out to be the advocate's *preliminary checklist* of
  documents still required (not the deeds themselves). Verify the FIRST PAGE before quoting
  a document as evidence.
- **Aadhaar regex false positives**: `\d{4} \d{4} \d{4}` over a GPA draft matched
  V. Swaminathan's Aadhaar (correct) AND Nishant Ranka's (4159 0535 2796 — the developer's
  partner, not a landowner). Attribute every Aadhaar to its holder before writing it into a
  form.