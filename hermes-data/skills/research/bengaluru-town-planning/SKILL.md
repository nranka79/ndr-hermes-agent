---
name: bengaluru-town-planning
description: |-
  Research and interpret Bangalore's town-planning regulations — ZR 2015
  (Revised Master Plan 2015), BBMP Building Byelaws 2003, GBA rules,
  Gazette amendments, and single-plot regulations. Trigger: "check the
  Zonal Regulation", "is [use] allowed in the basement?", "what does
  the ZR say about [topic]", "search R&D for [regulation]".
metadata:
  hermes:
    tags: [bangalore, town-planning, zonal-regulations, RMP-2015, BBMP, GBA, FAR, basement]
category: research
version: 1.0.0
author: ndr@draas.com
---

# Bengaluru Town Planning — Regulatory Research

A guide to finding, reading, and interpreting the regulations that govern building construction in Bengaluru's local planning area. The key document is **RMP 2015 (Revised Master Plan 2015) — Zoning Regulations, Volume 3**, supplemented by the **BBMP Building Byelaws 2003** and periodic **Gazette amendments**.

## 1. Regulatory Hierarchy (what applies where)

| Regulation | Scope | Status |
|---|---|---|
| **RMP 2015 — Zoning Regulations, Vol. 3** | Entire Bengaluru Local Planning Area (including Greater Bengaluru / GBA) | In force; amended periodically by Gazette notifications |
| **BBMP Building Byelaws 2003** | BBMP jurisdiction | Supplements ZR where ZR is silent; largely superseded for FAR/parking/basement rules but still referenced for technical definitions (ventilation, fire safety, etc.) |
| **Gazette amendments (e.g. UDD 338 MNJ 2026)** | City-wide (LPA) | Proposed draft amendments published for public objections — may not yet be in force |
| **Single Plot Regulations (2025 Amendment)** | Plots up to 10,000 sqm under Section 17 | In force (Notification UDD 272 MNJ 2025) |
| **GBA Draft Building ByeLaws 2026** | Greater Bangalore Authority | Draft stage — deviation condonation fee schedule only |
| **BMRDA regulations** | BMRDA area (peripheral) | Separate from BBMP/GBA; check if site falls in BMRDA |

**Key principle:** ZR 2015 is the primary document. BBMP Byelaws 2003 fill gaps. Gazette amendments modify specific clauses. Always check the latest Gazette date (see `references/` for key notification numbers).

## 2. Trigger Conditions

Activate when the user says anything like:
- "Check the Zonal Regulation under my R&D — the ZR, R&P 2015"
- "Is there any restriction on creating [common area / clubhouse / swimming pool] in the basement?"
- "Search the town planning norms for [topic]"
- "Look at GBA rules / Master Plan 2031 draft"
- "Study all regulations related to [specific use] in Bangalore"
- "What does the ZR say about [FAR / setbacks / parking / basement]?"

## 3. Where to Find the Documents

NDR's Drive has the relevant PDFs stored across various folders. The canonical search pattern:

```python
from tools.gws_auth import build_service
drive = build_service('drive', 'v3', service_name='google-draas')

# Key document queries:
queries = [
    "name contains 'Revised Master Plan 2015' and trashed=false",
    "name contains 'Zoning Regulation' and trashed=false",
    "name contains 'RMP 2015' and trashed=false",
    "name contains 'ZR 2015' and trashed=false",
    "name contains 'building byelaws' and trashed=false",
    "name contains 'GBA' and trashed=false",
    "mimeType='application/pdf' and name contains 'zonal' and trashed=false",
]
```

**Known key document IDs (from prior research):**

| Document | Drive ID |
|---|---|
| Revised RMP 2015 (full, ~10 MB PDF) | `0B1Oc8cSaJXPGUlcxM05kTVpLR0U` |
| 2026 Gazette — ZR Amendment Draft (UDD 338 MNJ 2026) | `1r5elhbWWF63ct2cE4UyWvkSt_1gNGpES` |
| Single Plot Regs (RMP 2015 Amendment, Jul 2025) | `1wFxkbvsfQuqQT0YSHzIu9zl4UStSYWjT` |
| BBMP Building Byelaws 2003 | `0B1Oc8cSaJXPGejRrMGk5VFk3S0U` |
| BBMP GBA Draft Byelaws 2026 | `1FJjCUHn25Tvuv2dK5VxPN6Ff0ba7DeYl` |
| ZR 2015 Clarification Letter (DRA→BDA re: parking) | `1fBJOu6l4W7Gkas7lfe03ZjUxuhCMf_D3HfALbGaDldI` |
| Model Building Byelaws Amendment 2025 | `1ExphU8euQhcHY6uNP838mbAMktEzP9g1` |
| RMP 2031 Objections/Comments (DRA's submission) | `1PMtfX-8nXMBRYYjP2JBQaeST8QPJPqPBb4aAfVPnNak` |
| Ranka Amber Zoning Analysis (RMP 2015) | `1HwKCulMK0v2_n-guk5y6m7Odpoo9Z6pV` |

**Akrama-Sakrama / Sadaavakasha regularisation handbook** (BBMP/UDD 2015-16, bilingual Kannada+English): the applicant guide for regularising unauthorised development/construction — Sec 76-FF KTCP Act 1961, Sec 321A KMC Act 1976, Sec 187A KM Act 1964 + application forms. Official UDD PDF: `https://udd.karnataka.gov.in/uploads/media_to_upload1741687877.pdf`. Full detail, egress notes and the Apify residential search recipe: `references/akrama-sakrama-regularisation-handbook.md`.

**Search the R&D folder first** — folder ID: `1wCyEkCHIWYp8q14D5OTzctROLA7203C0`. It contains a `Zonal Regulations` subfolder and a `Research Reports` subfolder. Use `execute_code` with Drive API to search within it:

```python
from tools.gws_auth import build_service
drive = build_service('drive', 'v3', service_name='google-draas')

# List everything in the R&D folder
results = drive.files().list(
    q="'1wCyEkCHIWYp8q14D5OTzctROLA7203C0' in parents and trashed=false",
    fields="files(id, name, mimeType)"
).execute()

# Or search for specific regulation terms across Drive
for term in ['zonal', 'ZR 2015', 'RMP 2015', 'building byelaws', 'gazette', 'GBA', 'master plan']:
    r = drive.files().list(
        q=f"name contains '{term}' and trashed=false",
        fields="files(id, name)"
    ).execute()
```

## 4. Extracting Text from Scanned PDFs

Most regulation PDFs are scanned images, not text-searchable. Two approaches:

### A. `pdftotext` (when the PDF has embedded text)
```bash
pdftotext /path/to/pdf /path/to/output.txt
grep -in "basement\|cellar\|common.*amenity\|clubhouse\|swimming" /path/to/output.txt
```

### B. Download via Drive API + convert pages to PNG + `vision_analyze`
For scanned/image PDFs, download the file via `drive.files().get_media()`, then use `pdftoppm` to convert specific pages to PNG images and feed each page through `vision_analyze`. Focus on the table of contents or clause list to find the relevant section number first.

```python
import subprocess, os
# Convert page 3 of a PDF to PNG
subprocess.run(['pdftoppm', '-f', '3', '-l', '3', '-png', pdf_path, out_prefix])
# Then vision_analyze each PNG with a targeted question
```

### C. Kannada / bilingual documents — OpenRouter Gemini vision (NOT vision_analyze)

`vision_analyze`'s built-in OCR **garbles Kannada** (returns mojibake — useless for translated titles/cover pages). For Kannada or bilingual (Kannada+English) regulation docs, send the image to `google/gemini-2.5-flash` via OpenRouter directly from `execute_code` — `call_openrouter_model` is text-only and cannot accept images:

```python
import base64, json, urllib.request, os
b64 = base64.b64encode(open(img_path,'rb').read()).decode()
data_url = "data:image/jpeg;base64," + b64
payload = {"model": "google/gemini-2.5-flash",
  "messages": [{"role": "user", "content": [
    {"type": "text", "text": "Transcribe ALL text (Kannada + English), translate Kannada to English, identify title/issuer/edition and any Acts or sections mentioned."},
    {"type": "image_url", "image_url": {"url": data_url}}]}],
  "max_tokens": 3000}
# POST to https://openrouter.ai/api/v1/chat/completions with OPENROUTER_API_KEY
```

NDR explicitly prefers Gemini 2.5 Flash via OpenRouter for Kannada text work.

## 5. Key Sections to Know

### ZR 2015 — Section 3.9: Basement

This is the most frequently consulted section for NDR's projects. It governs:
- **Definition:** Storey partly/wholly below avg ground level, max **1.2m** projection above ground, max 4.5m height  
  *(Note: if a structure projects >1.2m above ground, it may not legally be a "basement" — see Pitfall P1)*
- **Permissible uses (non-hotel buildings):** Parking, X-ray dark rooms, bank safes/strong rooms, AC/utility equipment.  
  **Clubhouse, common amenity, swimming pool, gym, banquet — NOT ALLOWED.**
- **3-star+ hotels ONLY:** Swimming pool, health club, banquet, gym, etc. allowed in spare basement area (counts towards FAR).
- **Residential (single dwelling, ≤500 sqm):** Home theater or gym without FAR (personal use only).

### BBMP Building Byelaws 2003 — Section 18: Basement floor

- **18.1:** "Basement floors shall not be used for purposes other than parking and for locating machines used for service and utilities of buildings." Exceptions: bank strong rooms, hospital X-ray (both counted in FAR).
- **18.2–18.14:** Technical requirements — height (2.4–2.75m), ventilation (mechanical if natural insufficient), fire safety, waterproofing, max 11.25m to exit, max 2 basements (3 for 3-star+ hotels).

### ZR 2015 — Section 3.9(viii): Residential basement (limited)

Basement in a residential building allowed WITHOUT FAR only for:
- Home Theater
- Gym
- Combination of both
- Site ≤500 sqm, single dwelling, Residential (Main) zone, entry from inside.

### 2026 Gazette Amendment (UDD 338 MNJ 2026)

Key changes relevant to basement:
- UG sump, STP, and **swimming pool** may be allowed in **setback area** after reserving space equal to required basement setback.
- Car lifts allowed for plots up to 6,000 sqm instead of ramps.
- Parking norms for basements: ramps vs. car lifts at various parking counts.

## 6. Pitfalls

### P1. The "basement" vs "ventilated stilt/floor" distinction

ZR 2015 Section 3.9(i) defines basement as projecting **max 1.2m** above average ground level. If the structure projects **>1.2m** (e.g. 1.75m as in Ranka Northstar's case), it does NOT legally qualify as a basement under the ZR. This means:
- The restrictive use list (parking + utilities only) does not apply.
- The space counts as a regular floor (FAR-applicable) and can be used for common amenities, clubhouse, swimming pool, etc.
- It must comply with normal floor-level regulations (setbacks, coverage, height).

When the user says "but it's a ventilated basement" — verify the projection height against the 1.2m threshold before applying the basement restrictions. This can be the decisive legal argument for/against a proposed use.

### P2. Gazette amendments may not be in force

The 2026 Gazette (UDD 338 MNJ 2026) is a **draft** notification — it says "proposes to make certain amendments" and invites objections within 30 days. Do NOT treat it as current law unless the user confirms it has been finalised. Check the language: "Draft Regulations" / "proposes" = not yet in force.

### P3. Documents are often scanned/image PDFs

Despite `pdftotext` being available (`/usr/bin/pdftotext`), many regulation PDFs have no embedded text layer (they are scanned images of printed pages). Use `pdftoppm` to convert pages to PNG + `vision_analyze` as described in §4B.

### P4. bbmp.gov.in / *.karnataka.gov.in block the VPS datacenter IP

Direct curl, `web_extract`, and local browser all fail against BBMP/UDD/Karnataka gov sites (HTTP 000 / tunnel error / timeout). Route through **Apify residential proxies** (`apify_run_actor` with `apify/google-search-scraper` or `apify/website-content-crawler`, `proxyConfiguration.apifyProxyGroups: ["RESIDENTIAL"]`, country IN) — this works. Browser Use Cloud also works once credits exist but is not immune to genuine server outages (UDD was down entirely). For login-walled Scribd mirrors of gov docs, recover the full text from the Wayback Machine's HTML capture and rebuild a PDF with reportlab — see `references/akrama-sakrama-handbook.md`. Kannada OCR: built-in `vision_analyze` garbles Kannada; use Gemini via OpenRouter (see same reference).

## References

- `references/gba-bbmp-officer-contacts.md` — **GBA/BBMP officer phone + email lookup** (Special Commissioners, Chief Commissioner, IAS/KAS staff): official HOD contact-list PDF at updates.bbmpgov.in (fetch with `curl -skL` — gov cert is invalid), pdftotext layout mapping, verified entry for Munish Moudgil (IAS, Special Commissioner Revenue & IT: 94481 94915 / spcomm-rev@bbmp.gov.in), and the no-Apify/no-Tavily direct lookup recipe (Google News RSS → Wikipedia → DDG-via-Jina)
- `references/premium-far-cost-analysis.md` — Premium FAR calculation formula (28% rule), FAR structure breakdown (Base/Amalgamation/Premium/TDR), BBMP fee components, Texworth quotation structure, and the email-thread-tracing workflow for finding project cost calculation history
- `references/akrama-sakrama-handbook.md` — Akrama-Sakrama / Sadaavakasha regularisation handbook (76-FF KTCP, 321-A KMC, 187-A KM): where it lives online, the egress ladder for bbmp.gov.in / *.karnataka.gov.in (Apify residential proxies — VPS datacenter IP is blocked), Wayback-based recovery of login-walled Scribd docs, and the Kannada-OCR-via-Gemini-OpenRouter workaround

> **Not metro.** For Bangalore Metro / Namma Metro routes, stations, proposed corridors, or transit KML questions, load `bangalore-metro-research` — this skill is zoning/regulations only.

## 7. Practical Strategies for Dealing with Restrictions

## 7. Critical Regulatory Findings (Consolidated from Bangalore Research)

### NOC Requirements for Plan Sanction
- **BESCOM NOC** → NOT a pre-condition for plan sanction. Only "development charges to be paid if any."
- **BWSSB NOC** → NOT a pre-condition. Same — development charges if any.
- **KSPCB / Pollution Control Board** → NOT mentioned in standard licence conditions.
- **AAI / Airport NOC** → Required only if within airport funnel zone (project-specific).
- **Labour Department NOC** → Mandatory before construction.
- **Fire Department** → Periodic clearance for high-rise (>15m), not a pre-condition.
- **Electric Transformer** → Required if floor area > 500 sq.m.

### ZR 2015 Basement Quick Reference
- Max projection above avg ground level: **1.2m** (>1.2m = not legally a basement)
- Permissible uses: parking, bank safes/strong rooms, X-ray/storage, AC/utility equipment
- Clubhouse, swimming pool, gym, banquet → NOT permissible (only 3-star+ hotels)
- Single dwelling (<500 sqm): home theater/gym allowed without FAR (personal use only)

### 2026 Gazette Key Amendments
- **Swimming pool allowed in setback area** after reserving space equal to required basement setback
- **Swimming pool excluded from ground coverage calculation** (Reg 3.5)
- **Basement parking up to 6,000 sq.m plot** allowed with car lifts without ramps
- Basement setback: minimum setback required for building

### Workflow for Regulatory Research
1. **Search Drive first** — use `drive_search` with specific name queries for ZR, GBA, BBMP, bylaws, and relevant project names
2. **Download PDFs** via `drive_download(file_id=..., output=...)` → use `pdftotext` for text extraction
3. **Search ZR/regulations** for specific restrictions (basement uses, FAR, setbacks, height limits)
4. **If rule not found in regulations**, look at **actual approved building licences** for comparable projects — the licence conditions show what the authority actually enforces
5. **Cross-reference** — compare what regulations say vs what actual licences required

## 8. Building Compliance Evidence Package

Trigger when the user needs to:
- Prove a NOC is or isn't required for plan sanction
- Highlight specific conditions in a building licence/sanctioned plan
- Cross-reference regulatory notifications (GOK, ZR, etc.) against a project
- Prepare an evidence PDF for bank pre-approval or regulatory clarification
- Draft an email attaching regulatory evidence for external stakeholders

### 8.1 Document Retrieval
- Search Google Drive using `build_service('drive', 'v3')` with targeted queries
- Look for: building licence (BBMP/CC/XXXX), sanctioned plan drawing, Ekhata, RERA registration, regulatory notifications
- The **original document** (scan/PDF from authority) is always the source — never generate a PDF from scratch for highlighting

### 8.2 Document Inspection (CRITICAL — do before any processing)
- **Visually inspect every page** of the original PDF using `vision_analyze` at adequate DPI (150+ for licence scans)
- Check for:
  - Pages that are wide/landscape format (sanctioned plans are often large-format drawings shrunk to A4/A3 — these need landscape orientation in output)
  - Pages that are cut off, misaligned, or have content in margins
  - Multi-page documents where page numbering goes to N but only N-1 pages are present
- **Record which pages need landscape vs portrait** before starting any PDF work

### 8.3 Content Analysis
- Extract conditions/NOC requirements from the licence and sanctioned plan
- Key things to check in a Bangalore building licence:
  - **Labour NOC**: is there a condition saying "Obtaining NOC from Labour Dept is a must"? This is the ONLY mandatory pre-sanction NOC in GBA
  - **BESCOM/BWSSB conditions**: Are they about "development charges" or "NOC"? Crucial distinction
  - **KSPCB/PCB**: Is it mentioned anywhere? If absent from 50+ conditions, proves it's not a pre-requisite
  - **AAI Height Clearance**: Only needed above specific heights
  - **Fire NOC**: Periodic (every 2 years, post-occupancy), not a pre-sanction NOC
  - **Deviation penalty**: If present, check if it was paid/regularised
  - **STP threshold**: For projects <120 units in sewered BBMP areas, STP/KSPCB clearance is not mandatory (GoK Notification FEE 43 EPC 2022, 12.03.2024)

### 8.4 Creating the Highlighted PDF
Use PyMuPDF (fitz) directly — do NOT re-render or recreate pages:

```python
import fitz
doc = fitz.open(original_path)
page = doc[page_num]
highlight = page.add_rect_annot(rect, color=(1, 1, 0), fill_color=(1, 1, 0), fill_opacity=0.3)
```

**Critical rules:**
- **Work directly on the original PDF** — the original authority scan has proper resolution and layout
- **Page size**: if the original page is landscape (width > height), set the output page to landscape
- **Large-format drawings**: crop the relevant condition area instead of shrinking the whole drawing
- **Highlight precision**: draw highlights EXACTLY over the text/condition being cited
- **No fabricated content**: never add text boxes, arrows, or annotations that aren't in the original

### 8.5 Verification & Delivery
1. Re-run `vision_analyze` on the output PDF — check every page
2. Verify: all highlight rectangles sit precisely on target text; no page is cut off
3. Verify: page count matches original
4. Upload to Drive TMP folder
5. If applicable, draft email via `gws_skill_bridge.call('draft_create', ...)` attaching the PDF

### 8.6 Compliance Evidence Pitfalls
- **Cut-off pages**: Always visually inspect every page of both input AND output
- **Highlight misalignment**: If the original PDF was scanned at an angle, rectangles placed by coordinates will miss
- **Landscape vs portrait**: Sanctioned plans are often landscape; keep original orientation
- **DO NOT recreate the PDF** from scratch — loses the authority-issued look
- **Don't assume** a condition is a "NOC requirement" when it says "development charges" or "fees"
- After uploading to Drive, verify the link opens correctly in browser before sending

When the user asks about workarounds for a restricted use (e.g. "can we show the swimming pool as a water tank and regularize later?"), provide regulatory analysis first, then offer strategic options neutrally:

### Strategy A — The "not a basement" argument (preferred)

If the structure projects >1.2m above average ground level, it fails ZR 2015's own definition of basement (§3.9(i)). Therefore the restrictive use list in §3.9(v) simply does not apply. This is the cleanest legal argument — no workaround needed.

**Verify the actual projection height** from the architectural drawings before relying on this.

### Strategy B — Draft regularisation (uncertain)

The 2026 Gazette Amendment (draft) allows swimming pools in setback areas. If/when it becomes law, the swimming pool could be constructed legally in the setback instead of the basement. Not useful for an indoor/basement pool unless the amendment changes further.

### Strategy C — "Show as something else" (risk disclosure only)

When the user proposes showing a swimming pool as a "water storage tank" and the changing area as "storage" on paper, then converting later:
- **Do NOT endorse this as a recommendation.** Flag it as a high-risk strategy:
  - ZR 2015 §3.9(vii) explicitly says misused parking area may be municipalised without compensation — this principle could extend to any misrepresented basement use.
  - The plans are submitted to and approved by the authority. Misrepresentation on approved plans may constitute a violation of the Karnataka Town and Country Planning Act.
  - Regularisation (B-Khata / plan deviation approval) is at the authority's discretion and may not be available for this type of use.
- **If the user decides to explore this route**, the correct next step is to have the architect prepare the basement plan showing the official labels, then take it to JDTP / GBA authorities for an informal verbal opinion before submission. Gr
