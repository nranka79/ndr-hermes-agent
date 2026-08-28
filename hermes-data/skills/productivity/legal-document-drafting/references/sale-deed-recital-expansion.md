# Sale Deed Recital Expansion — From Source Deed to Expanded Recital

Expanding a bare recital entry (e.g. "(i) Sale Deed dated 16.10.2023, Doc No.21201/2023") into a full recital with parties, survey numbers, extents, and per-survey title history. Recurring DRAAS workflow when Bharat/NDR drafts a new absolute sale deed and references a prior deed of title.

## Workflow

### 1. Download the source deed from Drive

The user drops a Drive link. Use `build_service('drive','v3', ...)` + `get_media()` — never curl (returns sign-in page for private files). Confirm with `files().get(fields='id,name,mimeType,size,owners')` to identify the document.

### 2. Confirm it's a scanned PDF

- `pdftotext source.pdf - | wc -c` returns near-zero bytes → scanned image PDF
- `pdfinfo` shows Creator = "Adobe Scan" → confirmed scan
- 148 pages, 60MB = typical for a multi-party absolute sale deed

### 3. OCR the key pages (not all 148)

**Page 1** — parties header: "THIS DEED OF SALE IS EXECUTED ON THIS 16 DAY OF OCTOBER 2023 ... BETWEEN" + first vendor name. The deed lists 100+ co-vendors; you only need the **first vendor name + "and others"** for the recital.

**Pages 56–60** — the Schedule of Properties. This is the only table that matters for the recital listing. Look for "SCHEDULE OF PROPERTIES" heading. Items are in the format:
`Survey No.158/1A1A, Dry Ext Hec.0.14.50 (or) Ac.0.36 cents`
Record BOTH hectares and acres. The deed footer states the total: `making a total extent of Ac.7.53 cents`.

**Pages 51–52** — the GPA authorisation recital (often contains a duplicate list of all survey numbers with extents, useful as cross-check).

**Pages 22–55** — the "And whereas" recitals (title chain). These trace the history for each survey group. OCR these and grep for each survey number to extract the chain.

### 4. DRAAS recital drafting convention (Bharat, Aug 2026)

- **Parties**: Keep only the first seller name + "and others" (e.g. "Mr. J. Venkata Swami Reddy and others"). Do NOT list all 100+ co-owners.
- **Purchaser**: Full firm name — "M/s. SEVAGANAPALLI LAND PARTNERS"
- **Registration details**: Doc No, Book, Sub-Registrar Office as they appear in the source deed
- **Survey numbers**: List ALL survey numbers from the deed's Schedule of Properties with their extents (both hectares and acres). End with the total extent.
- **Highlighting**: All newly added text is highlighted in YELLOW (python-docx `r.font.highlight_color = YELLOW`). The original stub text stays uncoloured.
- **Title history**: Add one paragraph per survey number after the recital, showing the full chain from origin → vendors → GPA holder → purchaser. Each paragraph covers: UDR classification, ancestral origin, key transactions (partitions, gifts, sales with document numbers), and the final GPA authorisation that led to the sale.

### 5. Title chain extraction from "And whereas" recitals

The source deed's "Background and Recitals" section (Part I) walks the chain of title in chronological "And whereas" paragraphs. The structure is:

- **158 group**: Survey 158/1 → Pedda Siddareddy's family → UDR sub-divisions (158/1A1, 158/1C1, 158/1C2, 158/1C3, 158/1C9B) → partitions, gifts, and sales → various vendors → GPA to Pavan Kumar
- **166/3 group**: Butta Reddy's ancestral property → oral partition → UDR sub-divisions (166/3A through 166/3F) → Nanjunda Reddy, G.Nagi Reddy, Kamalamma, etc. → GPA to Pavan Kumar
- **167/1 group**: Part of Butta Reddy's ancestral property → UDR sub-divisions (167/1A, 167/1B, 167/1D, 167/1H, 167/1I, 167/2D) → Guvva Reddy, Nanjunda Reddy → GPA to Pavan Kumar

For each survey number, extract:
- **UDR classification**: The survey number and its recorded extent
- **Original pattadar**: From the UDR patta table
- **Key transactions**: Partition deeds, gift deeds, sale deeds that moved the property (with document numbers and dates)
- **Final vendor**: Who held it just before the sale (usually the 116+ co-vendors)
- **GPA**: The General Power of Attorney that consolidated authority (Pavan Kumar S/o.Sreenivas held GPA from multiple vendor groups)
- **Sale to Sevaganapalli LP**: The final conveyance under the deed being analysed

### 6. Inserting into the target document

The target document is a .docx on Drive (not a native Google Doc). Use the python-docx + OxmlElement paragraph insertion technique from `google-workspace` → `references/docx-format-edit-in-place.md` (section "Inserting new paragraphs between existing content").

**Sequence:**
1. Edit the recital paragraph (e.g. para [21] "(i) ...") — replace the single-line stub with the expanded text + yellow highlighting
2. Insert the title history paragraphs after the recital paragraph (between (i) and (ii)) — all highlighted yellow
3. Re-upload in-place: `drive.files().update(fileId=fid, media_body=MediaFileUpload(...))`
4. Verify via temp Google Doc → PDF export → vision_analyze

### 7. Verification

- Re-download the file from Drive and read the paragraph text back — confirm the real sentence is there, not label tokens
- Create a temp Google Doc (`drive.files().create(body={'mimeType':'application/vnd.google-apps.document'}, media_body=...)`) → export PDF → `pdftotext` to confirm text content
- Render the PDF page to PNG → `vision_analyze` asking specifically about yellow highlighting on the recital and survey number lines

## Common pitfalls

- **Tuple-unpacking order when rebuilding runs**: `[(label, text)]` iterated as `for txt, hl in runs` gives `txt="plain", hl="Sale Deed..."` — the paragraph silently becomes `"plainhlhlhl..."`. Use `(text, highlight_bool)` consistently.
- **OCR misreads on scribe/garbled pages**: Pages with signature stamps and vendor endorsements have heavy OCR noise. The "And whereas" paragraphs on clean pages are the reliable source.
- **Schedule appears twice**: Once in the body (page 51, inside a GPA recital) and once as the "SCHEDULE OF PROPERTIES" (pages 58-60). Cross-check both — the GPA recital version may omit some items.
- **Paragraph index shift after insertion**: After inserting title history paragraphs, the indices of all subsequent paragraphs (e.g. (ii) Exchange Deed, (iii) Sale Deed 02.03.2024) shift by +N. Always verify the next recital is still intact.
- **Extents in both hectares and acres**: The deed gives both (e.g. "Hec.0.56.0 (or) Ac.1.38 cents"). The user reads the acres column. Include both for completeness.
- **"7.53 cents" = 7.53 acres**: In Indian land deeds, "cents" after the acre figure means the fractional part of an acre. So "Ac.7.53 cents" = 7.53 acres.

## Example (from this session)

Source deed: `20231016 sale deed (7.53 acres).pdf` — 148 pages, 60MB, Adobe Scan, Doc No.21201/2023, SRO Hosur

Resulting recital expansion:
```
(i) Sale Deed executed on the 16th day of October 2023 between Mr. J. VENKATA SWAMI REDDY and others (the Vendors/First Party, comprising numerous co-owners together with their duly authorized General Power of Attorney holders) and in favour of M/s. SEVAGANAPALLI LAND PARTNERS (the Vendee/Purchaser), registered as Document No. 21201/2023, of Book 1, in the Office of the Sub-Registrar, Hosur, in respect of the undermentioned survey numbers of Sevaganapalli Village, Hosur Taluk, Krishnagiri District, Tamil Nadu, having a total extent of Ac.7.53 Cents, viz.: Survey No.158/1A1A admeasuring Hec.0.14.50 (or) Ac.0.36 cents; (...) Survey No.167/2D admeasuring Hec.0.02.5 (or) Ac.0.06 cents.
```

Title history section (22 paragraphs, one per survey + summary):
- "Common Origin: Main Survey No.158/1, Survey No.166/3 and Survey No.167/1..."
- "Survey No.158/1A1A - Hec.0.14.50 (or) Ac.0.36 cents: The main Survey No.158/1 was ancestrally held by sons of Pedda Siddareddy. By Partition deed dated 26.10.2009 (Doc.7512/2009, SRO Hosur)..."
- "...Thus, all the 19 survey numbers aggregating Ac.7.53 cents were brought under the common authority of Mr. Pavan Kumar S/o.Sreenivas (GPA holder) and conveyed to the VENDOR M/s. SEVAGANAPALLI LAND PARTNERS under the said Sale Deed dated 16.10.2023."