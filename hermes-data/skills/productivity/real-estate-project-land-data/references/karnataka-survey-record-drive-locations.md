# Karnataka Survey-Record Documents — Where They Live on Drive (Allalasandra / Ranka Northstar)

## Document vocabulary (voice variants)
NDR often asks for "Podi, Sartipani, Satbara, Tippani, Atlas, hakka bukka, whatever they're called" — these are Karnataka village land-records, mostly scanned image PDFs in Kannada (no text layer):

| Document | What it is | Searched-as |
|---|---|---|
| Podi / Phodi | Survey sketch showing subdivisions (often per-sy-no "podi sketch and index") | `podi`, `Phodi`, `Phodi sketch` |
| Satbara / RTC | Record of Rights (ownership/tenancy record, often per survey no) | `RTC`, `Satbara`, `Record of Rights` |
| MR | Mutation Register extracts | `MR`, `MRL` |
| Tippani | Survey notes / resurvey notes book | `Tippani`, `Tipni`, `Survey Book` |
| Akarbandh | Village land register / map | `Akarbandh`, `Aakarbhand` |
| Atlas Sketch | Village atlas sheet | `Atlas` |
| Hakka bukka | Rights list / hissa (subdivision) survey | `hakka`, `bukka`, `Hissa` |
| Village map | Village layout map | `village map` |
| FMB | Field Measurement Book sketch (survey division drawing) | `FMB`, `FMB sketch` |
| e-Khatha | Digitized khatha certificate | `khatha`, `e-khatha` |

## Key pitfall
These are scanned Kannada image PDFs — `pdftotext` returns nothing, and `vision_analyze` can be flaky/no-provider. Verify by **folder location + filename** (the parent folder name carries the project identity), not by OCR content. Render at 150 dpi only if you must examine a specific sheet.

## Ranka Northstar (Allalasandra, Sy 14/1, 14/2–14/5) — where the records live
**"North star approval folder 2026 April"** (`1dw-BzPEmoWdiQ-ePcanYA0INvVfQxJfB`) holds the whole survey-record set:
- `RTCs (1).pdf` — 53 pages (likely one RTC per survey no) → `1R2kv6JvIHBJxHIkQtxvkCv0ZCytToQQg`
- `MRs (1).pdf` — 3 pages → `17CFv8hHDXWajwrmj4uBODx3K4yB8Zujn`
- `Akarbandh (2).pdf` (2 p), `Akarbandh 2 (1).pdf` (1 p), `Akarbandh (1).pdf` → `1zB5W5SV4hj9gclAr2Xe9A_M0MwqZ-fpy`, `1tJ9SQqbEDjreI_id2nvaTiTK4sbGOP1N`, `1aaiEVRPYDEudbYzlU6Ce6Emh9ATRaaK6`
- `hakka bukka Hissa Surevy (1).pdf` → `15zd7nmAIjIkyE7z9LgHexvL9o7r_2iDA`
- `Atlas Sketch (1).pdf` → `15uEOG3Sd67WMcyDlxpx4-Nv2yfzSvrqu`
- `village map (1).pdf` → `1pI9Ne3r_sj_7wEcATk2oT2z6mB-NOCDX`
- `new e khatha allalasandra 1-8 Kannada version.pdf` → `1-g6RLnhfk-qwBO2SS4xuYFuOBzRi5f7R`

Also in that folder: JDA files, tax receipts, SHEET 1/2/3, amalgamation deed, MRs.

Related:
- FMB sketch jpg (root): `20260320_RankaNorthstar_Allalasandra_FMB_Sketch.jpg` → `1kG7D01CWz4rgD7dXaOl7KMFT6ULne0t5`
- Site Digital Survey Drawing.pdf (legacy root) → `0B1Oc8cSaJXPGenJSakZqTll4SXV5ajNsblhCMlJlY1I3d24w` (+ .dwg)
- Allalasandra Site 1-8 ekhatha older copy → `1_mxJ1OdWooA-9Ovb8hrR7lyOX4FKux75`
- Sy 14/1 Guidance Value (31-Aug-2026): `20260831_RankaNorthStar_Allalasandra_Sy14-1_GuidanceValue_Attested.pdf` → `1l-VgAtKSa7bNm9IkOE-sdNIn-D9jBhII` (dupe `1AKfZR6ImsejP7iQp8QUBEwJryo2aHVbA`; both inside Ranka Northstar folder `15sQdh6hCszfOzaQM3BZ44Q4Du1Gbhug4`)
- Judicial Layout survey (03-Aug): `20260803_RankaNorthstar_Allalasandra_MainRoad_NH44_JudicialLayout_Survey.pdf` → `15W18n5_c0OnjPuo5yR4NDk0cJackpTvd` (in Ranka Northstar 02_Engineering_and_Design `1_j5sGrDoWx6PfkESWxGOCSvmf0xOMUAB`)
- Title Deeds sy no. 14/1 DD sheet: `1LNWa6HAvuRd0Wue6e83FulPJb2rewybgoikqtnkbO2M` + doc `1T5WsF9wnsR3Q6uKxP42OWyyb5L9G3-ya3VfQLs7KVlk`

## Delivery pattern (10-Sep-2026)
NDR asked "list everything with links" for survey sketches — deliver as: **grouped bullets with `https://drive.google.com/file/d/<id>/view` links**, named per doc type, note that scans are Kannada image-only so content is verified by folder location, and offer OCR verification once the vision provider is available. Voice names: "Sartipani" = Satbara/RTC, "Podi" = Phodi sketch.