# Deed execution date & registration verification

## The question shape

NDR asks "which year was this sale deed executed?" — the answer gets used in
legal correspondence, so it must come from **the deed**, not from the Drive
filename.

## Rule: cite the execution clause AND the registration endorsement

DRAAS Drive filenames follow `YYYYMMDD_Property_DocType_Party.pdf`
(e.g. `20100802_EmbassyHabitat1503_SaleDeed_NDR.pdf`). The date prefix is a
**convention and is usually correct — but it is not evidence.** To answer a
legal date question, open the deed and cite two things:

1. **The execution clause** (opening paragraph). Deeds are drafted as:
   > "THIS DEED OF SALE executed on the 02nd day of August Two Thousand Ten
   > (02.08.2010)"

   That is the execution date.
2. **The registration endorsement** (foot of the deed / page-1 stamp block):
   Document No., Book, C.D. No., and the sub-registrar's office. The e-stamp
   print timestamp on page 1 shows the presentation time.

Execution and registration are usually the same day for a clean sale. **If they
differ, say both** — do not collapse them into one date.

Give the year AND the full date, plus the parties and the registration number.
That is what makes the answer verifiable and lets NDR cite it.

## Worked example — Embassy Habitat flat 1503

- Filename prefix: `20100802`
- Deed opening clause: *"THIS DEED OF SALE executed on the 02nd day of August
  Two Thousand Ten (02.08.2010)"*
- Purchaser: Nishant Ranka S/o Dinesh Ranka
- Vendors: Smt. Chinnamamba Desraj Urs, Mrs. Ila Desraj Urs, Mrs. Aparna
  Desraj Urs, M/s L.K. Trust — represented by GPA holder M/s Magrath Property
  Developers (partners Dharmesh Ranka and another)
- Registered as: Document No. `GAN-1-00849-2010-11`, Book I, C.D. No.
  `GAND119`, Sub-Registrar Gandhinagar, Bangalore
- Stamp duty: Rs.7,08,375 by DD No. 048067 dt 30/07/2010 (Standard Chartered
  Bank, M.G. Road) + Rs.10 cash
- E-stamp print timestamp 02-08-2010 11:04:27 AM (stamp paid 10:53:54 AM)
- **Answer given: executed and registered 2 August 2010.**

The deed also recited that the purchase was of the **undivided share**, with the
apartment itself built under a **Construction Agreement** with the confirming
party — standard for this project's structure.

## Pitfall — do not confuse the purchase deed with the sale deed

The family has both directions of transaction on Embassy Habitat:

- flat **1503** — PURCHASED by NDR in **2010** (this deed)
- flat **914** — SOLD by RNR to Ravikumar Naik in **2026**

When NDR says "the Embassy Habitat sale deed", establish **which flat and which
direction** before answering. A wrong-flat answer is worse than a clarifying
question.

## Extraction mechanics

Adobe Scan PDFs (the common capture app in this corpus) carry an **OCR text
layer**, so `pdftotext -layout <file> -` works despite the document being a
scan. Kannada glyph runs come out as garbage characters, but the English
clauses — dates, parties, covenants, registration references — are clean. Run
`pdfinfo` first to get the page count.

Do not reach for tesseract / pymupdf rendering unless `pdftotext` returns
nothing.
