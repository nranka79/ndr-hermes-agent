# Court Bundle Typed Set — Index Navigation

## What is a Typed Set?

In Indian civil litigation, when a party files an appeal (CMA, RFA, CRP, etc.), the appellant prepares a **Typed Set of Papers** — a paginated compilation of all relevant documents. Each page is assigned a sequential Typed Set (TS) page number. The bundle is served on all respondents.

## Typical Structure of a CMA Typed Set (Madras High Court)

| Section | Contents | Approx. TS Page Range |
|---------|----------|:---------------------:|
| **Index** | Listing of every document with TS page reference | (cover pages, not numbered) |
| Coding Sheet | Registry filing information | 1 |
| Court Fee | Court fee stamp sheets | 2–3 |
| Grounds of Appeal | Legal grounds challenging lower court order | 4–8 |
| Petition to Condon Delay | If appeal filed beyond limitation period | 9–10 |
| Affidavit in Support | Appellant's sworn statement supporting the appeal | 11–13 |
| **Fair Order** | Lower court's order (being challenged) | 14–30 |
| **Decreetal Order** | Formal decree from lower court | 31–35 |
| Plaint (Original Suit) | The original suit documents from the trial court | 36–56 |
| Written Statements | Defence filings from each respondent | 57–69 |
| **IA Petition** | Interlocutory application in the original suit (e.g., for attachment before judgment) | 70–74 |
| **IA Affidavit** | Affidavit supporting the IA | 75–84 |
| IA for Injunction | Separate IA for interim injunction (if filed) | 85–89 |
| Counter by D4/D5 | Defence responses to the IA | 90–102 |
| Vakalatnama / Batta | Counsel authorization / process fee | 103–105 |
| Verified Petition | The appeal petition itself | 106+ |

> Items in **bold** correspond to Apsaraa's requisition items 7 & 8 from the CMA 742/2026 session.

## Mapping TS Pages to PDF Pages

Scanned PDFs from counsel have their own PDF page numbering (1–N). Typed Set pages start at a different offset.

### Method 1 — Using the Index Page

1. Find the **Index page** — usually PDF page 1 (sometimes continues onto page 2)
2. Use `vision_analyze` to read the Index — it lists every document with its TS page number
3. Find one document you can positively identify visually (e.g., the Coding Sheet = TS 1)
4. Calculate offset: `offset = PDF_page_of_TS1 − TS_page_of_that_page`
5. Any TS page N is at PDF page: `N + offset`
6. To find a document spanning TS pages A–B, extract PDF pages `[A+offset]` through `[B+offset]`

### Method 2 — Using a Visible TS Page Number

1. Find any PDF page with a visible TS number (often hand-numbered in top-right corner or printed at bottom centre)
2. Note both the PDF page number and the TS page number
3. Calculate offset as above

### Example: CMA 742/2026 (Saveganapalli Land Partners)

From the Index page (confirmed via vision_analyze):

- **Index** shows Coding Sheet at TS 1
- **Coding Sheet** visible on **PDF page 3**
- **Offset** = 3 − 1 = 2
- **Fair Order** (Index says TS 14–30) → PDF pages 16–36
- **Decreetal Order** (Index says TS 31–35) → PDF pages 37–41
- **IA Petition for attachment** (Index says TS 70–74) → PDF pages 72–76
- **IA Affidavit** (Index says TS 75–84) → PDF pages 77–86

## Common Patterns & Pitfalls

- **Language mix**: Lower court orders from TN (Hosur, Krishnagiri) are in English for the order text, but the plaint and IA petition may be entirely in Tamil. The Index is the only reliable English-language identifier for those pages.
- **Blank pages**: Some TS pages are blank (back of title pages, separator between documents) — skip them during extraction. They still "consume" a TS page number.
- **Index spans 2 PDF pages**: Items 1–8 on PDF page 1, items 9–17 on PDF page 2. Always check both.
- **Served copy = Filed copy**: "CourtPapers_Served.pdf" contains the identical bundle served on your party. There is no separate "filed" version.
- **TS page numbers in the Index are the authoritative reference** — counsel uses these in correspondence and court filings.
- **Hand-numbered pages**: Some old bundles use hand-written circled numbers (🄌) in the top right — these correspond to TS page numbers.
- **When referring documents to counsel, always use TS page numbers**, not PDF numbers. Counsel's physical copy uses TS numbering.
