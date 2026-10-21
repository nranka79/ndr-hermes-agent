# JDA / Addendum / GPA — Party & Signatory Verification

Class of task: NDR asks *"is <person> a signatory to the original Joint
Development Agreement / the addendum / the GPA?"* — typically because the answer
decides whether that person must physically attend a sub-registrar registration.
Answer only from executed documents.

Verified 2026-09-17 on **Ranka North Star (Allalasandra / "Alal Sandra")** —
JDA 07.02.2014, Addendum 30.11.2024, the Allalasandra legal index, and the
extracted-document index.

(Companion to `property-title-due-diligence`, which is the title/chain-of-title
umbrella. This file lives here because that skill's directory is read-only in
this environment.)

## Why this is high-stakes

Asserting "X is not a party to it" when X *is* a named executant puts a wrong
claim into a landowner WhatsApp group days before the registration counter does
its own check. NDR gave the group exactly that assurance about Sreeraman
Vaidyanathan before the records were read; the addendum names him as party No. 6
("Landowner 6"). Verify **before** the claim leaves the building, and if NDR has
already told a third party something the documents contradict, flag it
explicitly and early rather than quietly answering the question.

## Source hierarchy — trust in this order

1. **The executed deed itself.** Opening recital = parties; schedule = assets;
   per-page signature blocks = who executed.
2. **The legal index sheet** — Allalasandra: spreadsheet
   `1mmTJJiBTaLUdKXte9j-VnRuSu1uL8YchjV3M8ZP_u3M`, tab
   `Allalsandra Index inc MDR & Anup Doc's` (companions: `Non Avail Doc in Anup
   shah Opinion`, `Avail in Anupshah opinion`, `Balance Documents`). Columns:
   `# | Doc Type | Doc No | Date | Pages | Original/Photocopy | File (physical
   binder no.) | Available in Anup Shah set`.
3. **The extracted-document index sheet** — `Allalsandra - Extracted Document
   Index`, id `1LwzRjdaWEp06kd7Ek1cCCW5FpjYD4Tb7rR3oMjNCq6c`; maps the numbered
   DD bundle (`01_Index.pdf` … `28_Search_Reports_2020.pdf`, folder
   `1KOy9rVGX1PE5H--9Q0yh1KmUSWBiuyFp`) to master-set page ranges and carries
   the site↔owner attribution.
4. **A Drive filename.** LAST — hint only. See pitfall below.

## NEVER summarise an index from memory — cite sheet + row (USER-CORRECTED)

NDR's verbatim challenge, after a provenance-free answer that said "File 4,
File 5": *"where did you get this information from, which index are we referring
to, and which row of the index?"*

Rule: every finding quoted from a register, index, sheet or table is reported as
**document/sheet name + row number + the literal cell contents**. If you cannot
point at a row, say "not found". Never reconstruct from an earlier turn's
summary or from memory — those are the usual source of confident fabrication.

## PITFALL — bulk-generated Drive filenames are frequently mislabelled

The Allalasandra set contains `19990415 Allalsandra Site N Sale Deed –
<owner>.pdf` files created in one batch (2026-05-04). Those names disagree with
the registered JDA on five of eight sites:

| Site | JDA schedule (`Held by` + sale-deed doc no.) | Batch Drive filename |
|---|---|---|
| 3 | Lakshmi Vaidyanathan (doc 6707/98-99) | "R. Geeta Swaminathan" |
| 4 | Sundar Padmanabhan (doc 6693/98-99) | "A.S. Vaidyanathan" |
| 5 | Sreeraman Vaidyanathan (doc 6708/98-99) | "Lakshmi Vaidyanathan" |
| 7 | Kankshita Swaminathan (doc 2149/99-2000) | "V. Rangammal" |
| 8 | Rangammal (doc 2151/99-2000) | "Sreeraman Vaidyanathan" |

Reconcile with two independent keys before asserting any site→owner mapping:
the khata suffix (`<n>/<n>/14/1/<site>`) and the 1999 sale-deed document number
cited in the JDA schedule. The extracted-document index agrees with the JDA
(Sites 1-4 / 5-8 naming), which is how the conflict surfaced.

## PITFALL — reading a JDA schedule: `Held by:` closes the PRECEDING item

```
Item No.N
All that piece and parcel of property bearing Site No.N, Khata No.…, measuring…
bounded on: East by … / West by … / North by … / South by …
Held by: <owner> in terms of sale deed dated … vide document No.…
Item No.N+1
```

The `Held by:` line and the `Item No.N+1` heading frequently land on different
scanned pages, so the owner is easy to attach to the wrong item. Two checks
resolve it every time: the boundary chain (`North by: Site No.N+1`,
`South by: Site No.N-1`) and the `14/1/<site>` khata suffix.

## Extracting text from registered-deed scans (no text layer)

DRAAS deed scans are usually image-only — e.g. a real 37-page JDA
(`Producer: iLovePDF`) whose `pdftotext` output is one formfeed per page (~37
bytes). Working chain:

```bash
pdfinfo deed.pdf | egrep -i 'Pages|Producer'      # page count first
pdftotext -layout deed.pdf out.txt; wc -c out.txt # ~= page count => no text layer
pdftoppm -r 200 -gray -png deed.pdf pg/p          # render
tesseract pg/p-03.png - --psm 6                   # OCR one page
```

- `pytesseract` / `pymupdf` / `pypdf` may be absent; `pdftotext`, `pdfinfo`,
  `pdftoppm`, `tesseract` (eng only) and PIL are present. Prefer this chain over
  installing Python PDF libraries on the fly.
- English-only tesseract is sufficient for the party / schedule / signature pages
  of these deeds (typed English). Kannada needs separate traineddata — see
  `property-title-due-diligence` → `references/kannada-land-doc-ocr-patterns.md`.
- Crop + upscale a region when it matters:
  `PIL.Image.open(p).crop((0, int(h*0.62), w, h)).resize(...)` then tesseract.
- **Handwritten signatures do not OCR.** "Cannot verify from this scan" is a
  legitimate answer — never infer that a party signed because the printed label
  appears on the page.
- `vision_analyze(..., also_describe_visually=true)` is the documented visual
  path, but the model can be unavailable (observed 404 from the provider on
  2026-09-17) — keep OCR as the fallback instead of blocking on vision.

## GPA facts for the Allalasandra set (worked example)

Index sheet rows 241 and 246-252 — GPAs **dated 18.08.2003**, 5 pages each,
photocopies, all physically in **File 6**, all in favour of
**Sri V. Swaminathan**, one per landowner/site:

| Row | Doc | Site |
|---|---|---|
| 246 | GPA — R Geeta Swaminathan to V Swaminathan | 1 |
| 247 | GPA — A S Vaidyanathan to V Swaminathan | 2 |
| 248 | GPA — Lakshmi Vaidyanathan to V Swaminathan | 3 |
| 249 | GPA — Sundar Padmanabhan to V Swaminathan | 4 |
| 250 | GPA — Sriraman (Sreeraman) Vaidyanathan to V Swaminathan | 5 |
| 251 | GPA — Kankshita Swaminathan to V Swaminathan | 6 |
| 252 | GPA — V Rangamal to V Swaminathan | — |

Registered POAs around the JDA date are also indexed: rows 282 (`142/12-13`,
23.02.2013), 288 (`320/2013-14`, 07.02.2014), 289 (`143/2012-13`, 25.02.2013),
294 (`321/2013-14`, 07.02.2014, 22 pp, original, File 9). The 07.02.2014 date is
the JDA's own execution date.

**A GPA being recorded is not the same as it being usable now.** As of Sep 2026
the sub-registrar does not accept an **unregistered** GPA for representation —
so an unregistered 2003 GPA cannot carry a 2026 registration. Report the
documentary fact and this limitation as two separate statements.

Evidence that a GPA was actually exercised: the Deed of Consent cum Confirmation
dated 23.10.2013 (bundle `22_GPA_Will_Gift_Deeds.pdf`, id
`1wJFCJsnLfJhOEKZBSw8Jvr7bUGQjHEv0`) records, party by party,
`SRI. SREERAMAN VAIDYANATHAN S/o A. S. Vaidyanathan Rep by GPA Holder
V. Swaminathan`, registered `BYP-1-04977-2013-14`, stamp ₹200 — alongside Lakshmi
(`…-04973`), Sunder (`…-04976`) and Kankshita (`…-04980`).

## Reading the JDA / addendum party lists

**JDA 07.02.2014** — Doc No. 3034/2013-14, Sub-Registrar Malleshwaram, 37 scanned
pages. First Parties/Owners: 1 R Geeta Swaminathan, 2 Kankshita Swaminathan,
3 V Rangammal, 4 A S Vaidyanathan, 5 Lakshmi Vaidyanathan, 6 Sreeraman
Vaidyanathan, 7 Sunder Padmanabhan. The recital states that **only Nos. 2 and 3
were "duly represented by their GPA Holder Sri. V. Swaminathan"** — nobody else
was represented by an agent in the JDA. Schedule total 53,148 sq ft across khata
nos. 591/1077 … 596/1082 with `/14/1/1` … `/14/1/8`.

**Addendum 30.11.2024** (e-stamp `IN-KA82505335604880W`; first party
"V SWAMINATHAN AND OTHERS", second party DRA Ranka Holdings, stamp duty ₹500).
First Parties: 1 R Geeta Swaminathan; 2 Kankshita Swaminathan (represented by
V Swaminathan vide **GPA dated 18.08.2003**); 3 V Swaminathan in his own right
(Rangammal's successor under her registered Will `BNG(U)BYP/56/2009-10`);
4 A S Vaidyanathan; 5 Lakshmi Vaidyanathan; 6 **Sreeraman Vaidyanathan** (s/o
A S Vaidyanathan, aged ~47, Aadhaar 8762 8547 9740); 7 Sunder Padmanabhan. The
addendum cites only ONE GPA — Kankshita's. Its signature blocks repeat on every
page carrying `(Landowner N)` labels.

Distinguish two different questions: **named in the recital + printed signature
block** = "is a party". **"Did he physically sign?"** needs the executed page and
cannot be settled by OCR of a signature.

## Post-2024 changes to the same landowner register

Both created 2026-05-20, stamped 08-May-2026 as Article 4 Affidavits
("Assignment of Rights", ₹100), each expressly preserving the Developer's
subsisting GPA:

- `Assigning rights Lakshmi Vaidyanathan to Sreeraman Vaidyanathan.pdf` —
  Site 3, Khata 594/1080/14/1/3, 5,970 sq ft → son.
- `Assigning Rights AS Vaidyanathan and Hema Vaidayanathan.pdf` —
  Site 2, Khata 593/1079/14/1/2, 7,952 sq ft → daughter.

Both recite the 2014 JDA as `MLS-1-3033/2013-14, Book 1, dt. 07.02.2014`. When
answering "who is a party now", look for these later instruments — they shift the
beneficial picture even though the JDA parties are unchanged.

## Answer shape that worked

1. Yes/no up front, per document, each with the document identity (date,
   doc/registration number, registering office) and where in the document the
   person appears.
2. The schedule position — site number, khata number, area, and the 1999
   sale-deed doc number — so NDR can sanity-check against what he knows.
3. The GPA position: does one exist, its date, in whose favour, where it is
   filed, and whether it was ever exercised.
4. A short **flag** section for any conflict between the documents and what was
   already communicated to third parties, plus the concrete next check (e.g.
   "have Bharat/Rupa confirm his signature page on the registered set").
5. Drive links to the JDA, the addendum, the index sheet, and the supporting
   bundle.
