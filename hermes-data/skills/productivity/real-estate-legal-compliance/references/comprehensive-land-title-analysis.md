# Comprehensive Land Title Analysis — Batch Document Workflow

## When to Use

When the user uploads/share **multiple scanned legal documents** (12+ PDFs) about a single property's title — khathas, court judgments, title flow summaries, BBMP notices, e-khathas — and wants a **comprehensive HTML report** with:
- Complete chain of title (earliest to latest)
- Document index
- Chronological timeline of all events
- Property identifiers summary
- Current division/schedule descriptions
- All legal cases & status
- Risk assessment matrix
- Open questions & hypotheses
- Suggested next steps

## Workflow

### Phase 1: Inventory & Download

1. **List files in Drive folder** using Drive API
2. **Download all PDFs** to local disk via `files.get_media()` using `MediaIoBaseDownload`
3. **Check text layer** with `pdftotext` — if 0-50 chars, assume scanned/image PDFs

### Phase 2: Render to Images

```bash
pdftoppm -jpeg -r 200 "input.pdf" "pages/output_prefix"
```
This creates `output_prefix-01.jpg`, `output_prefix-02.jpg`, etc.

### Phase 3: Vision Analysis

Use `vision_analyze` on rendered JPEG pages to extract:
- All text content from each document
- Dates, case numbers, parties, property identifiers
- Court findings and orders

For Kannada-language documents (BBMP khathas, notices), OCR quality may be limited — cross-reference with English sections.

### Phase 4: Compile Structured Report

Create a comprehensive **HTML report** with these sections:

| Section | Content |
|---------|---------|
| 1. Document Index | Table of all files, dates, content summaries |
| 2. Chain of Title | Full chronological sequence from earliest deed |
| 3. Property Identifiers | PID, khatha numbers, survey numbers, boundaries |
| 4. Current Division | Each portion with owner, area, PID |
| 5. Legal Cases | All suits: parties, court, subject, status |
| 6. Risk Assessment | Matrix: risk factor, level, description |
| 7. Open Questions | Unanswered issues with hypotheses |
| 8. Next Steps | Revenue buildup, case buildup, research needs |

### Phase 4a: Timeline Visualization

Use an HTML `<div class="timeline">` with CSS vertical line and dot markers:
```css
.timeline { position: relative; padding-left: 30px; }
.timeline::before { content: ''; position: absolute; left: 10px; top: 0; bottom: 0; width: 2px; background: var(--accent); }
.tl-item::before { content: ''; position: absolute; left: -24px; top: 6px; width: 12px; height: 12px; background: var(--accent); border-radius: 50%; }
```

Use color-coded tags for event types: `tag-title`, `tag-litigation`, `tag-revenue`, `tag-bbmp`, `tag-resolution`.

### Phase 4b: Property Division Visualization

Use a card grid (`display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr))`) where each sub-property gets its own card with:
- Colored top border (green = retained, blue = sold, amber = other)
- Area in large font
- Owner + PID below
- Optional sub-note about transaction history

### Phase 5: File Renaming (Drive)

Rename source files per convention:
```
YYYYMMDD_Property_DocumentType.pdf
```
Map old filenames to new ones and update Drive via `drive.files().update(fileId, body={'name': new_name})`.

### Phase 6: Upload Report

Upload the HTML report to both:
1. The property's own Drive folder
2. The TMP folder (`18p74II2uL32sNDzDDwXzmlOUdJJOTmE-`) for editor access

Also upload a **Google Doc version** with the same content and append any Q&A notes.

## HTML Report Template Structure

```html
<!DOCTYPE html>
<html>
<head>
  <!-- Title, meta, embedded CSS -->
  <style>
    /* Timeline, cards, tables, risk badges, question boxes */
    /* Mobile-responsive (max-width: 600px) */
  </style>
</head>
<body>
  <div class="container">
    <h1>Property Name — Comprehensive Title Analysis</h1>
    <h2>1. Documents Examined</h2> <!-- Table -->
    <h2>2. Chain of Title</h2>   <!-- Timeline -->
    <h2>3. Current Division</h2> <!-- Cards -->
    <h2>4. Legal Cases</h2>      <!-- Table with status -->
    <h2>5. Risk Assessment</h2>  <!-- Matrix table -->
    <h2>6. Open Questions</h2>   <!-- div.question blocks -->
    <h2>7. Next Steps</h2>       <!-- Bullet lists -->
  </div>
</body>
</html>
```

## Case Law Research Section

When BBMP or a government body claims private property as a lake/tank bed, add a **Case Law Research** section to the HTML report after Risk Assessment. Each case must include **clickable source links** (CaseMine, Google search, or Indian Kanoon) so the user can verify the full judgment. Format:

```html
<div class="case-law">
<h4>1. Case Name</h4>
<p class="cite"><strong>Citation:</strong> 2024:KHC:12560 | <strong>Court:</strong> Karnataka High Court | <strong>Date:</strong> 26 March 2024</p>
<p><strong>Key holding:</strong> ...</p>
<p><strong>Relevance:</strong> ...</p>
<p class="source-link">
  <a href="https://www.casemine.com/search/in/..." target="_blank">View on CaseMine</a>
  <a href="https://www.google.com/search?q=..." target="_blank">Search on Google</a>
</p>
</div>
```

Include:

| Case | Relevance |
|------|-----------|
| **K.V. Srinath v. State of Karnataka** (Karnataka HC, 2015) | Nearly identical: private khatha holder vs government lake bed claim. Court gave significant weight to long-standing khatha and tax receipts. |
| **Environment Support Group v. State of Karnataka** (ILR 2012 KAR 3874) | Leading Karnataka lake preservation case — applicable to EXISTING lakes, not disputed land. Distinguish on facts. |
| **Selvam G v. The Deputy Commissioner** (Karnataka HC, Feb 2025) | Government can evict encroachers from proven government land. Distinguish: BBMP has NOT proven government ownership. |
| **H.P. Ranjanna v. Union of India** (NGT, 2021) | Reclaimed lake bed remains government property. Distinguish: lake existence was undisputed in that case. |
| **Sarakki Lake Area Improvement Trust v. State of Karnataka** (Karnataka HC, Feb 2026) | Very recent lake preservation case. Distinguish: undisputed existing lake vs disputed land with pre-Independence title. |

**Research methodology:** Use CaseMine (`casemine.com/search/in/`) with Google for Indian case law since Indian Kanoon is blocked by Cloudflare. Search terms: `BBMP lake bed khatha`, `Section 134 BBMP Act lake tank`, `government lake private property katha Karnataka`.

## Known Pitfalls

1. **pymupdf returns 0 text on registered Indian legal documents** — even when PDF is not scanned, registered deeds (Sale Deeds, Family Arrangements, Judgment copies) from Indian sub-registrar offices commonly return 0 chars via pymupdf. Always try `pdftotext -layout` as second check before assuming scanned. If both return 0, use pdftoppm + vision.

2. **Vision model may miss Kannada text** — Kannala-language content (khatha certificates, BBMP notices, revenue orders) has poor OCR quality with English-optimized vision models. Cross-reference Kannada sections with English headers/structured data in the same document.

3. **Area discrepancies between documents** — Khatha extracts for the same property may show different areas (e.g., 7,200 sq.ft vs 17,200 sq.ft for the same PID). Cross-validate against the title flow document, BBMP notices, and court orders. The most authoritative figure is usually in the court judgment or title flow summary.

4. **BBMP lake-bed claims lack specific evidence** — In at least one verified case (Cunningham Road, PID 78-51-9), BBMP's claim relied on: (a) RTC for a different village's survey number, (b) City Survey PT Sheet No.1002, (c) pleadings from the original owner's 1973 suit. The High Court found "no prima facie material." The key counterarguments: Master Plan shows the property as "Corporation Stadium" (not lake), Miller Tank is 2+ km away, BBMP itself issued khatha and collected taxes for 50+ years.

5. **Property identification from pleadings** — A litigant's reference to a lake/tank in their own pleadings (for boundary description purposes, not as an admission) has negligible evidentiary value against subsequent title holders. The court has rejected this twice.

6. **Trust settlement vulnerability** — If the chain relies on a Trust settlement (e.g., H.C. Dinshaw Trust → Y. Subba Raju → current owners), verify: (a) Trust was properly constituted with Probate, (b) settlement agreement was by competent trustees, (c) the settlement has stood unchallenged for the limitation period.

7. **Always verify critical facts against source documents, not compiled reports** — When the user asks a specific factual question (e.g., "how did Narasamma originally come into possession?"), do NOT rely on the compiled analysis report's interpretation. Go back to the **primary source documents** (rendered JPEG pages or original PDFs) and use vision_analyze to extract the exact text. The compiled report may have assumptions or gaps that the user will spot. Common pattern: user corrects a fact → you verify → find the source document is actually silent or ambiguous on that point. This is better than defending the report's interpretation.

8. **Acknowledge document gaps explicitly** — Documents are often silent on foundational facts (e.g., how a tenant/possession first entered the property). If the source documents do not answer a question, say so directly rather than filling the gap with plausible-sounding assumptions. The user can then decide whether to find additional documents or accept the gap as a known risk. Example from this session: the title flow documents state Narasamma was in possession "ever since Dinshaw purchased" but give no explanation of the legal basis — the correct answer is "the documents don't say" rather than guessing at tenancy, caretakership, or employment.

9. **Drive API access via vault token when gws_auth.build_service fails** — If `gws_auth.build_service()` raises `AttributeError: type object 'Credentials' has no attribute 'from_authorized_user_json'`, the `google-auth` library (confirmed up to v2.55.0) never had that method. The correct method is `from_authorized_user_info()` which takes a parsed dict, not a JSON string. Workaround: read the OAuth token directly from the vault Unix socket and construct credentials manually:
   ```python
   import json, socket
   s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
   s.settimeout(10)
   s.connect('/run/gws-vault/vault.sock')
   req = json.dumps({'op':'get','user_id':'ndr','telegram_id':'ndr','service':'google','session_uid':'ndr'})
   s.sendall((req + '\n').encode())
   # ... read response, parse token_json ...
   from google.oauth2.credentials import Credentials
   creds = Credentials.from_authorized_user_info(json.loads(token_json))
   from googleapiclient.discovery import build
   drive = build('drive', 'v3', credentials=creds)
   ```
   This bypasses the gws_auth.py bug entirely. See `gws-automation` skill reference `gws-auth-build-service-failures.md` for the full pattern.
