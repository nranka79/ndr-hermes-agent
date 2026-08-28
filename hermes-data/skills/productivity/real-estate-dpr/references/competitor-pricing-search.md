# Competitor Pricing Research for DPR Section 5.2

User trigger: "request search my profile - add competitive pricing analysis to all the projects in the DPR" / "to all the competitive pricing analysis to all the projects".

Rule: **Search the user's own Drive + past sessions FIRST**. The DRA Drive already contains per-project market-research decks, comp sheets, and R&D maps. Web research is the last resort (and Tavily may be out of credits — 432/insufficient credits → pivot immediately, don't retry the same path).

## 1. Discovery — Drive name-searches

Run all of these (name search is cheap and catches the decks):

```
name contains 'pric' and trashed=false
name contains 'competitor' and trashed=false
name contains 'market' and trashed=false
name contains 'Ranka' and trashed=false
fullText contains 'per sqft' or fullText contains 'per sq.ft' and trashed=false
fullText contains 'comparable' and trashed=false
```

Typical hits: `... Market Research Report (Brochure Edition)` (Slides decks), `... Comp Property Details & Cost Details` (sheets), `... R & D for Pricing` (Google My Maps), `... Verified Prices` decks.

Also try `session_search("competitive pricing analysis comparables per sqft")` — past sessions hold the decks' source compilations when exports are locked.

## 2. Extraction from decks (Slides)

- Slides → PDF: `drive.files().export(fileId, mimeType='application/pdf')` → save → `pdftotext -layout file.pdf -` .
- Competitor tables render as 3-column lines: `1 NVT Arcot Vaksana  ₹10,600 — 12,300/sq.ft  1 Godrej 24  ~₹10,807/sq.ft  1 Morefields by Manyata ₹8,000 — 9,500/sq.ft` (Villas | Apartments | Plotted side by side). Grep `₹` to find them.
- Detail pages per project have `💰 CURRENT PRICE ₹X/sq.ft`, `🚀 LAUNCH PRICE`, unit sizes, units, status, RERA no — usable verbatim.

## 3. Export 403 = download-disabled sharing (critical)

- `files().export` returning `403 ... "Export on..."` (message truncated with "Export on") = the file's **sharing setting disabled "Viewer and commenter can see the option to download, print, and copy"**. NOT an API fault, NOT ownership.
- Google-native files (My Maps, Slides) also reject `get_media` with `"Only files with binary content can be downloaded. Use Export..."` — so no raw fallback either.
- Pivot ladder: (a) `session_search` for the deck content; (b) live portal mining (NoBroker works from VPS); (c) ask the owner to re-enable download.
- Flag it to the user: "the Amber R&D map is download-restricted — change sharing to 'Viewer can download' for future reuse."

## 4. Live portal fallback — NoBroker listing parse (validated Aug 2026, Whitefield)

```python
import re, urllib.request
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36'}
html = urllib.request.urlopen(urllib.request.Request(
    "https://www.nobroker.in/flats-for-sale-in-whitefield-bangalore",
    headers=UA), timeout=45).read().decode('utf-8', 'ignore')
titles = re.findall(r'"propertyTitle"\s*:\s*"([^"]+)"', html)
prices = re.findall(r'"price"\s*:\s*"?(\d+)"?', html)     # raw rupees
carpets = re.findall(r'"carpetArea"\s*:\s*"?(\d+)"?', html)
# psf = price/carpet; SKIP carpet <300 or >8000 (junk rows, non-listing noise)
# also '₹X per sq ft' banner numbers per project/locality
```

Compute psf = price ÷ carpet, filter junk, curate top comparable listings (name, BHK, total, area, psf). Mark `(approx)` when derived; label "NoBroker listing, <month-year>".

## 5. Docs API in-place update of the DPR (Section 5.2)

Works on native Google Docs; preserves doc ID/link:

```python
docs = build_service('docs', 'v1', service_name='google-draas')
d = docs.documents().get(documentId=DOC_ID).execute()
# find the paragraph whose elements' textRun content contains the placeholder
start, end = para_start, para_end   # item['startIndex'], item['endIndex'] (end incl. newline)
repl = "\n".join(lines)
docs.documents().batchUpdate(documentId=DOC_ID, body={'requests': [
    {'deleteContentRange': {'range': {'startIndex': start, 'endIndex': end}}},
    {'insertText': {'location': {'index': start}, 'text': repl + "\n"}},
]}).execute()
```

- Lines: `• <Project> (<type>) — ₹band/sq.ft — <status>` then a `Positioning:` paragraph (own price vs band + sales evidence) then `Sources:` line with deck/sheet URLs (Docs auto-linkifies).
- Verify after update: re-`documents().get`, assert 'Benchmarking against nearby' and count `• ` lines.

## 6. Ranka project research-file map (DRA Drive, as of Aug 2026)

| Project | Research file | ID | Exportable? |
|---|---|---|---|
| Oasis | Market Research Report (Brochure Edition) Jul-2026 | 1RJCsKaKj_HvaD8LRC7v2kV_zwJUNIvgjQGTbo59hToM | yes |
| Oasis | Comp Property Details & Cost Details (18-Jun-2025, villa comp table + room-level spec sheets) | 16wKGxe5tIporWlLJTVwibgzm6IgnFINIj35GX8nqWOI | n/a (sheet) |
| Oasis | Project Presentation v3 (Verified Prices) | 1HKv6PQLRO4IZEuEWniKfzJRwESSuvKWIFwqgoHaflX8 | 403 (locked) |
| North Star | Market Research v4 (Verified Prices + Hyperlinks) | 14wqhK0A6z4a7DTveXKBG1ycAbwXQMUDg5aPZMhuK9ss | yes |
| North Star | Allalasandra nearby projects (prices as on Jan-2026) | 1Ld3XjvRw-qpO9Bq0i1zVe9Ru2Tu5-sWKbKhW7DlBp90 | n/a (sheet) |
| North Star | R&D pricing map | 1EdjqeTsKemvmZWL8T2Gb3R_d9jriq-0 | n/a |
| Amber | Projects R&D for Pricing map | 1-Fu2J08TlGmBLPONwY4hJjmOw_gabgw | **403 (locked)** |
| Amber | Market Research deck copies | 10AYlTocLSIrpMcPvbHd-phHtaCmYDxus, 14hKPPARRyHKWuQcchLk2Rkp_0WtZGSc6 | **403 (locked)** |
| Udaya | no dedicated deck → use Oasis deck plotted segment + Hosur belt bands | — | — |

## 7. Observed comparable bands (Aug 2026, DRA research)

- **Amber / Whitefield**: 2–3 BHK mostly ₹8,000–17,000/sq.ft; premium new launches ₹14,000–29,000 (Sumadhura Folium ~₹28.7K, Prestige Raintree Park ~₹27.5K, Jagriti Renaissance ~₹12.5K). Amber achieved ₹12,000 → conservative.
- **Oasis / Sarjapur–Attibele (villas)**: band ₹6,700–12,300; NVT Arcot Vaksana ₹10.6–12.3K, Assetz 18&Oak ₹10.9–12K, Kumari Oakville ₹9.5–10K, Arvind Forest Trails ₹8.5–9K, Ruchira Villa Feliz ₹11K. Oasis at ₹12K = top tier (golf-front).
- **Udaya / plotted (Sarjapur–Attibele + Hosur)**: Morefields ₹8–9.5K, Saikam ₹6.3–7.4K, Palm Paradise ~₹5.5K, Ecocity ₹5.4K, NBR Trifecta ₹3.3K, Concorde Mist Valley ₹2.8K; Hosur town plots ₹3–5.5K, Berigai/Bagalur ₹1.5–3.5K (airport). Udaya ₹3.2–3.5K = entry.
- **North Star / Yelahanka**: Brigade Eternia ₹14–16K, Godrej Aveline ₹16.2K, Concorde Mayfair ₹14.5K, L&T Elara ₹18–23K; mid-band ₹6.5–12.2K (Aryan 1 Celeste ₹9.5–10.3K, Flowing Tree ₹12.2K, VISISTA ₹15–17K, Trendsquares Ortus III ₹11.5K). NS at ₹12K = mid-premium.

Prices shift; always re-verify before formal submission.