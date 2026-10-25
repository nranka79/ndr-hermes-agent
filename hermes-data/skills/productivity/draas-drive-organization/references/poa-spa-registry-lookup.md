# POA / SPA / GPA registry lookup — "did we ever give X a power of attorney?"

Trigger: "check if we gave <person> a POA/SPA/GPA from <entity>", "did DRA Realty ever execute a power of attorney in favour of <person>", "find a signed power of attorney PDF in my Drive". Validated 2026-09-23 on the DRA Realty → Bharat Hawaldar lookup.

## Workflow

1. **Drive name + fullText sweep across ALL vault drives** (google-draas primary; google-ahfl + google-gmail for completeness — the ahfl/gmail drives held a KDR→Bharat SPA and a WHPL→NDR GPA, so the sweep is not redundant). Queries that work (pageSize up to 100, dedupe by file id, print `modifiedTime` so stale duplicates are visible):
   - `name contains 'power of attorney'` / `'POA'` / `'GPA'` / `'attorney'` / `'Special'`
   - `fullText contains '<person surname>'` — **Drive's index includes OCR of scanned PDFs**, so this catches scans with no text layer
   - `fullText contains 'power of attorney' and fullText contains '<entity>'` (e.g. `'DRA Realty'`)
   - `fullText contains '<project>' and fullText contains '<person>'` (e.g. `'Amber' and 'Hawaldar'` — surfaces the project's registered deeds mentioning the person)

2. **Read the registration pages, not just page 1.** The parties are on pages 1–3 ("EXECUTED BY" = Principal/grantor, "IN FAVOUR OF" = Attorney/grantee); the **Kaveri/registration pages** (often page 2 or last page) carry the doc/registration number (e.g. "SPA No 503 of 2024", "GNR-4-00675-2025-26"), the presenter (Director vs SPA holder), identifiers and witnesses. The presenter on a registered deed tells you who actually admitted it — e.g. Ranka Amber JDA Reg 2227/2025-26 was presented by Director Nishant Ranka, not by Bharat.

3. **OCR template for scanned registration PDFs** (fitz is installed in `/opt/hermes/.venv`; it prints a deprecation warning — `import pymupdf` works the same). Render at **200 DPI grayscale**, `tesseract <img> stdout --psm 6`, run pages 1–2 + last page only to identify parties/purpose in seconds; scanning every page is unnecessary.

4. **Determine direction.** Registry files named "<Project> GPA for JDA" or "<Project> GPA" are often the OPPOSITE direction. Worked case: `20260918_RankaAmber_GPA_for_JDA_ContactDetails_Updated.pdf` is an **irrevocable GPA from the Iyer landowners → DRA Realty** (Attorney/Developer) coupled with interest — NOT a DRA-granted POA. Read before claiming.

5. **Distinguish the grantor entity.** "DRA Realty Pvt Ltd", "DRA Projects Pvt Ltd" (old name), "DRA Thindlu Land Partners", and an individual director (NDR personally) are different grantors. NDR's question usually names the exact entity — answer per entity, and flag SPA/grantor mismatches explicitly.

## Known registry snapshot (google-draas, as of 2026-09-23)

SPAs from **DRA Realty Pvt Ltd → Bharat Baburao Hawaldar** (all signed/registered PDFs):
- **SPA No 503/2024** (19-Sep-2024) — Poojena Agrahara Village, Kasaba Hobli, Hoskote taluk (purchases). Executed by Director Nishant Ranka, Board Res. 24.11.2023.
- **SPA (26-Sep-2024)** — Anbarasan + Bharat as joint attorneys — Tamil Nadu properties.
- **SPA No 675** (20-Mar-2026, Reg **GNR-4-00675-2025-26**) — Karnataka-wide: admit & present Sale Deeds, **JDAs**, Sharing Agreements, Mortgage Deeds, Lease Deeds for purchase/sale/lease/mortgage/**development** — the one covering JDA registration in Karnataka (post-dates the Amber JDA, so not its presenter).

Related, different grantors: NDR (personal) → Bharat SPA 20-Feb-2024 (Ashokji Mortgage Deed, Muthanallur/Byadarahalli); DRA Thindlu Land Partners → Bharat (Oct-2024) and new Thindlu SPA by DRA Realty + NDR (May-2026); Ranka Oasis / Sevaganapalli SPA DRA Realty → Bharat & Anbu (Aug-2025 execution copies) + SPA Doc 339 investors → Bharat (Sep-2025). **No DRA→Bharat SPA tied to Ranka Amber as of this date** — the Amber-side POA is the Iyers' GPA to DRA Realty (see direction pitfall).