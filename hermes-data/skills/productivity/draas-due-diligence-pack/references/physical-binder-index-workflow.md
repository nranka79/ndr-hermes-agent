# Physical Document Binder Index — Allalsandra NorthStar Worked Example

## The Index Spreadsheet

The master index for Allalsandra NorthStar legal documents is the sheet **"Allalsandra Index inc MDR & Anup Doc's"** in this spreadsheet:
`https://docs.google.com/spreadsheets/d/1mmTJJiBTaLUdKXte9j-VnRuSu1uL8YchjV3M8ZP_u3M`

It tracks documents across **7+ physical binders** (File 1 through File 7), each containing ~30-80 documents. Columns: Sl No | Doc Type | Doc No | Date | Pages | Original/Photo.

## Search Pattern

When a document ref number is requested (e.g. `ALN/NAY/SR/60-2016-17`):

### Step 1 — Resolve variant spellings

Government document numbers appear in several forms on the same index:
- `LLN(NY)SR 60/16-17` (the "L" reads similar to "A" in faded typewriter)
- `LLN(NY)SR 61/16-17`
- `ALN(NAY)SR/60/2016-17` (matches user's exact recall)
- `60/16-17` / `61/16-17` (bare number)

Search the index with ALL variants.

### Step 2 — Collect all entries across files

In the Allalsandra index, these refs appear across three binders:

**File 4** (applications + endorsements):
| Sl No | Doc Type | Doc No | Date | Pages | Type |
|---|---|---|---|---|---|
| 172 | Application | 61/16-17 | 01.07.2016 | 1 | Photocopy |
| 173 | Application | 60/16-17 | 01.07.2016 | 1 | Photocopy |
| 174 | Endorsement | LLN(NY)SR 61/16-17 | 04.09.2017 | 1 | Original |
| 175 | Endorsement | LLN(NY)SR 60/16-17 | 04.09.2017 | 1 | Original |

**File 5** (DC letters, endorsements, demand note, memorandum):
| Sl No | Doc Type | Doc No | Date | Pages | Type |
|---|---|---|---|---|---|
| 193 | Letter Signed by DC | LLN(NY)SR 60/16-17 | 13.01.2017 | 1 | Photocopy |
| 194 | Letter Signed by DC | LLN(NY)SR 61/16-17 | 13.01.2017 | 1 | Photocopy |
| 214 | Endorsement | LLN(NY)SR 61/16-17 | 05.06.2017 | 1 | Photocopy |
| 215 | Endorsement | LLN(NY)SR 60/16-17 | 05.06.2017 | 1 | Photocopy |
| 227 | Demand Note | ALN(NAY)SR/60/2016-17 | 30.12.2017 | 3 | Original |
| 228 | Memorandum | ALN(NAY)SR/60/2016-17 | 06.01.2018 | 2 | Original |

**File 7** (additional endorsements):
| Sl No | Doc Type | Doc No | Date | Pages | Type |
|---|---|---|---|---|---|
| 253 | Endorsement | LLN(NY)SR-60/16-17 | 06.01.2018 | 3 | Photocopy |

Total: **11 document entries** across three physical binders.

### Step 3 — Check compiled PDFs

`Allalsandra Docs Legal Set.pdf` (id `1ABXJZX6I5P324iuslD8QiAVoq3C2ebrB`, 39 MB, 291 pages) was created via NAPS2 scanner on 2019-05-22. It likely contains scanned versions of these binder documents, but at 150 DPI with faded Kannada typewriter text, it is **not machine-readable** — tesseract kan+eng and vision_analyze both fail.

### Step 4 — Report precisely

Tell the user: "These documents exist in File 4, Sl No 172-175 and File 5, Sl No 193-194, 214-215, 227-228, and File 7, Sl No 253 of the `Allalsandra Index inc MDR & Anup Doc's` sheet. The compiled PDF on Drive is too poorly scanned for automated reading."

## Parallel patterns (other projects)

When a similar question arises for other projects (Ranka Oasis, Ranka Amber, Sevaganapalli), look for:
- A spreadsheet named `*Index*` in the project's Drive folder
- A sheet tab named `Index`, `Document Index`, or `Master Index`
- Columns like `Sl No`, `File No`, `Doc Type`, `Doc No`, and `Original/Photo`

The physical binder naming convention at DRAAS is **File N** (File 1, File 2, ..., File 7+), and each binders' sl-no range is typically contiguous within the index.