---
name: kelsa-land-proposal
description: >-
  General Kelsa MCP operations across DRA pipelines — Land Proposal (ID 519),
  DRA Petty Cash (ID 555), Invoice Processing (ID 516), Vendor Shortlisting
  (ID 531), Companies Master (ID 4475), PO-WO Issuing (ID 537). Covers: pipeline discovery, field mapping,
  file upload flow (get_upload_url -> S3 POST -> register_upload), lead creation
  and updates, vendor pre-creation, note management, and stage transitions.
  Use when ndr says "add this land to Kelsa", "post this invoice to Kelsa",
  "create a vendor in Kelsa", "update this lead in Kelsa", "file this as a
  petty cash reimbursement".
metadata:
  hermes:
    tags:
      - real-estate
      - kelsa
      - land-proposal
      - draas
      - pipeline
      - invoicing
      - expenses
related_skills:
  - ranka-udaya-leads-pipeline
  - draas-due-diligence-pack
---

## Finding an existing proposal ("is it already in Kelsa?")

When the user says "both proposals are entered in Kelsa, find them" (or asks whether a proposal exists before adding it):

1. **Name search is NOT sufficient.** `search_leads(pipeline_id=519, query="Foxconn")` or `query="10 acre villa"` only matches the record **name** field. Records whose identifying info (source, location, size) lives only in custom fields will NOT surface. This session: the 10A Nandi-backside villa (source: Nishant Prakash) returned 0 results for "Foxconn", "Nandi", "Manak", "outright villa" — only the cf_proposal_source filter found the source-tagged leads.
2. **Use the Kelsa filter syntax on custom fields:** `search_leads(pipeline_id=519, query="cf_proposal_source:Nishant Prakash")` — returns every record where the Proposal Source dropdown = Nishant Prakash, regardless of name. Semicolons are AND: `stage:Proposed;cf_proposal_source:Nishant Prakash`.
3. **Try size + location keyword variants:** "30 Acre", "plot", "behind", "Chikkaballapur", "villa" — then eyeball the results for the deal.
4. **Disambiguate similar parcels with the map pin:** resolve the shared maps.app.goo.gl link and the lead's `cf_location_google_maplink` via `curl -s -L <url> -w "%{url_effective}"` (extract `@lat,lng`). Identical-ish coordinates = same property; different = different parcel. See `references/duplicate-detection-and-reproposal.md` for the 2026-08-25 Avati 22A duplicate-confirm case (sketch survey-number matching) and the same-land-different-broker note pattern.
5. **Fill village/hobli/taluk/district from a bare map pin via reverse geocoding:** resolve the pin first (`curl -s -L <url> -w "%{url_effective}"`, extract `3d<lat>!4d<lng>` or `@lat,lng`), then Nominatim reverse lookup: `curl -s -G "https://nominatim.openstreetmap.org/reverse" -H "User-Agent: hermes-draas/1.0" --data-urlencode "lat=<lat>" --data-urlencode "lon=<lon>" --data-urlencode "format=jsonv2" --data-urlencode "zoom=16"`. Set `cf_village` (first locality), `cf_hobli`/`cf_taluk`/`cf_district` from address parts. Confirm the suburb matches the user's landmark anchor (e.g. "behind Brigade Meadows") — if not, the pin may be wrong. **Place-name links** (resolved URL carries no coords → Nominatim `/search`), **duplicate re-proposals → evidence bundle + add_note on the existing lead, never a silent duplicate**, and **Kannada survey sketches → pdftotext title-block extraction**: see `references/duplicate-detection-and-sketch-reading.md`.
5. **If not found, say so explicitly and ask for the details** — do not create a duplicate from memory. The user prefers to add missing proposals themselves, then the agent wires up followers/assignees and builds the WhatsApp with links.

## DRA Land Proposal — Operations Guide

## When to use this skill

The user provides land proposal details — location, size, pricing, deal structure, survey numbers — and asks to enter it into the **DRA Land Proposal** pipeline in Kelsa. This skill covers the full workflow from receiving raw data to a created lead record with attachments and notes.

## Workflow

### Step 1: Discover the pipeline

```python
# List accounts
kelsa_call_tool(tool_name="list_accounts")
# -> DRA (ID: 5) is the primary account

# Find land proposal pipeline
kelsa_call_tool(tool_name="list_pipelines", arguments={"account_id": 5, "query": "land"})
# -> DRA Land Proposal (ID: 519)

# Get full pipeline structure (stages, fields, dropdown clues)
kelsa_call_tool(tool_name="get_pipeline", arguments={"pipeline_id": 519})
# -> 92 fields across 6 field sets, 10 stages
```

### Step 2: Understand the field structure

Pipeline field identifiers use `cf_` prefix. Key fields for the initial **Proposed** stage:

| Field Set | Key Fields | Identifiers |
|---|---|---|
| Land Details | Location, City, Size (Acres/Sqft), UoM, Google MapLink, Land Zone, FAR, Sy Nos, Village/Hobli/Taluk/District, Land Sketch, Land pics, Revenue Maps | `cf_land_location`, `cf_city`, `cf_land_size_acres`, `cf_land_size_uom`, `cf_location_google_maplink`, `cf_sy_nos`, `cf_village`, `cf_hobli`, `cf_taluk`, `cf_district`, `cf_land_sketch`, `cf_land_pics`, `cf_revenue_maps_and_documents` |
| Proposal Details | Date, Brief (name), Source, Offer Type, Rate, Total Cost, Product Type, Proposal Notes, Upfront Investment | `cf_date_of_proposal`, `cf_name` (Proposal Brief), `cf_proposal_source`, `cf_offer_type`, `cf_expected_total_outright_cost_of_land`, `cf_product_type`, `cf_proposal_notes`, `cf_total_upfront_investment_expected` |

### Step 3: Extract data from PDFs and images

For **.xlsx financial workings / P&L annexures** (openpyxl often NOT installed on this host): use the stdlib zipfile + sharedStrings recipe in **`references/xlsx-stdlib-parse.md`** — check for sharedStrings.xml (cell values are indices into it, NOT inline) vs inline strings; a parse that ignores `t="s"` looks like an empty sheet of small integers.

Use these tools when the user sends a sketch PDF or checklist:

```bash
# Extract text from PDF
pdftotext /path/to/sketch.pdf - 2>/dev/null

# Convert PDF to PNG for vision analysis
pdftoppm -png -r 200 /path/to/doc.pdf /path/to/output_prefix
# Then use vision_analyze on the resulting PNG
```

**Common data to extract:**
- Survey numbers (Sy Nos) from cadastral maps
- Owner names, extents, and prices from checklists
- Village, Hobli, Taluk, District from sketch title blocks

**AutoCAD plan PDFs (property sketches / layout models) need the quadrant-split recipe** — plain `pdftotext`/full-page OCR returns only the title header. Check `pdfinfo` for Creator "AutoCAD"; if present, render at 300 DPI and split into 4 quadrants via PIL, then `vision_analyze` each quadrant separately. CDP zoning maps (yellow = residential), stage-wise survey tables (Stage 1-4 colour-coded with owner/extent columns), and embedded land-use analysis tables each have their own reading pattern. See **`references/autocad-plan-and-cdp-reading.md`** for the full recipes, including the extent-reconciliation math (stage totals + sketch block = claimed total) and the multiple-owner listing pattern.

**Survey / site-plan PDFs (non-AutoCAD, hand-drawn style):** These carry only dimension numbers, area calculations (sqm), road-width labels ("24 m proposed master plan road"), and percentage splits (e.g. "commercial 54.37% / roads 45.63%"). pymupdf returns ~20 raw numbers with zero context. The pipeline:
1. Render to PNG at 200 DPI via pdftoppm
2. **Use vision_analyze with `also_describe_visually=true`** — the visual + OCR pass reads both the dimensional lines AND the summary table area/road split
3. Use the OCR numbers to extract: commercial parcel area, road area, adjoining road widths, parcel boundary dimensions, percentage breakup
4. Cross-check arithmetic: commercial area + road area = total site area; percentages must sum to 100%

**Excel financial models / P&L annexures:**

### Step 4: Upload files to Kelsa

Files must go through a 3-step pipeline:

```
get_upload_url -> POST file to S3 -> register_upload -> use returned value in create_lead
```

**Step 4a: Get upload URL**
```python
kelsa_call_tool(tool_name="get_upload_url", arguments={"pipeline_id": 519, "file_name": "f.pdf", "content_type": "application/pdf"})
# → upload_url, fields (S3 POST form), file_url
```

**Step 4b: Upload bytes to S3**  
Use Python with `requests` to POST multipart/form-data:  
```python
import requests
S3_ENDPOINT = "https://kelsa-clients-production.s3.ap-south-1.amazonaws.com"
with open(local_path, 'rb') as fh:
    form_fields = {}
    for k, v in fields.items():
        form_fields[k] = (None, str(v))
    form_fields['file'] = (file_name, fh, content_type)
    r = requests.post(S3_ENDPOINT, files=form_fields)
# Expect HTTP 201
```

**Alternative (curl via terminal):** When execute_code string escaping causes issues (f-strings with dict key access), use a shell script instead:
```bash
HTTP_CODE=$(curl -s -o /dev/null -w '%{http_code}' \
  -F "key=$S3_KEY" \
  -F "success_action_status=201" \
  -F "acl=private" \
  -F "x-amz-server-side-encryption=AES256" \
  -F "Content-Type=$CONTENT_TYPE" \
  -F "policy=$POLICY" \
  -F "x-amz-credential=$CREDENTIAL" \
  -F "x-amz-algorithm=AWS4-HMAC-SHA256" \
  -F "x-amz-date=$DATE" \
  -F "x-amz-signature=$SIGNATURE" \
  -F "file=@$LOCAL_PATH" \
  "$S3_ENDPOINT")
# HTTP 201 = success
```
The `-F` (form-field) flag handles multipart encoding correctly. Write the script to a temp file and run via `terminal()`. Can batch multiple files in one script.

**S3 403 on xlsx / non-PDF uploads (observed 2026-08-16):** the presigned policy signs `Content-Type` as a condition. Plain `-F "file=@model.xlsx"` makes curl guess the part's content-type (often `application/octet-stream` or a non-matching guess) → HTTP 403, even though PDFs with the same pattern upload fine (201). **Fix: append the explicit content type to the file field:** `-F "file=@/tmp/model.xlsx;type=application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"` → 201. The PDFs' guessed type already matched, which is why only the xlsx failed. When a mixed batch has one 403, retry just that file with `;type=<mime>` — don't re-request all URLs.

**Curl S3 upload fails when policy string contains parentheses (2026-08-21):** The presigned URL policy (a base64-encoded JSON like `eyJleHBpcmF0aW9uIjoi...`) frequently decodes to content containing `(` and `)` characters. When passed as a literal `-F "policy=$POLICY"` inside bash, the shell sees them as subshell-call syntax and fails with `unexpected EOF while looking for matching ')'`. Even putting the policy in a file and using `-F "policy=$(cat policy.txt)"` has the same problem if the shell processes the quoting first. **Fix: use Python requests** (the preferred pattern in Step 4b) for ALL S3 uploads — the multipart encoding is handled by the library, no shell quoting issues. Only use curl when all field values are known-safe (no `()[]{}` in the policy or credential strings). If you must use curl for a complex policy, write every field value to separate files and use `--data-binary @file` for the non-file fields, but Python requests is simpler.

**Step 4c: Register the upload**
```python
registration = kelsa_call_tool(
    tool_name="register_upload",
    arguments={
        "pipeline_id": 519,
        "file_url": file_url_from_step_4a,
        "file_name": "filename.pdf",
        "size": file_size_in_bytes
    }
)
# Returns attachment value object: {url, upload_id, size, name}
```

**Step 4d: Use in field_values on create_lead**
- Single-file attachment fields: use the object directly
- Multi-file fields (e.g. `cf_land_pics`): use an array of objects

### Step 5: Create the lead record

```python
kelsa_call_tool(
    tool_name="create_lead",
    arguments={
        "pipeline_id": 519,
        "name": "Thylagere - 10 Acres - Villa Development via Jiraffe Capital GD",
        "field_values": {
            "cf_city": "Bangalore",
            "cf_date_of_proposal": "2026-07-14",
            "cf_land_size_acres": 10,
            "cf_land_size_uom": "Acres",
            "cf_land_location": "Behind Prestige Goldshire, Thylagere, Near Nandi Hills",
            "cf_village": "Thylagere",
            "cf_hobli": "Kundana",
            "cf_taluk": "Devanahalli",
            "cf_district": "Bangalore Rural",
            "cf_sy_nos": "129/1, 129/2, ...",  # comma-separated
            "cf_offer_type": "JV",               # or Outright, Mix
            "cf_product_type": "Villa",
            "cf_proposal_source": "Nishant Prakash",
            "cf_name": "Proposal Brief text",
            "cf_proposal_notes": "Full description of the deal",
            "cf_expected_total_outright_cost_of_land": 550000000,  # 55 Cr
            "cf_total_upfront_investment_expected": 110000000,     # 11 Cr
            # Attachment fields use the register_upload returned value
            "cf_land_sketch": {"url": "...", "upload_id": 123, "size": 243604, "name": "sketch.pdf"},
            "cf_land_pics": [{"url": "...", "upload_id": 456, "size": 4251586, "name": "video.mp4"}],
            "cf_revenue_maps_and_documents": {"url": "...", "upload_id": 789, ...},
            "cf_location_google_maplink": "https://maps.app.goo.gl/xyz",  # URL string
        }
    }
)
```

### Step 6: Check draft status

The record is queued asynchronously. Poll until complete:
```python
kelsa_call_tool(tool_name="get_draft_status", arguments={"draft_id": draft_id})
# Returns "completed" with the lead link, or "still processing"
```

### Step 7: Add notes for supplementary data

```python
kelsa_call_tool(
    tool_name="add_note",
    arguments={
        "lead_id": lead_id,
        "text": "Detailed note with owner-wise extent breakdown, key terms, etc."
    }
)
```

**R&D / corridor-research link belongs in a note (NDR-requested pattern, 2026-08-16):** when NDR says "add the R&D section" / "link the online sheet where the R&D is", put the Drive spreadsheet link + the key per-project numbers directly in an `add_note` on the lead. Don't rely on `cf_rnd_data1` (tabular, fiddly) or `cf_competitor_data` (required only at Info Gathered) — a note renders the link and summary immediately in the activity log. Also include any **tracked discrepancy comment** NDR asked to keep visible (e.g. "Excel says 135 flats vs drawings 133 units — to be resolved at re-planning").

## Deal structure mapping

When the user describes a deal structure, map to Kelsa fields:

| User says | Kelsa field |
|---|---|
| 'Outright sale' | `cf_offer_type`: 'Outright' |
| 'JV / JDA' | `cf_offer_type`: 'JV' |
| 'Mix' (part outright, part JV) | `cf_offer_type`: 'Mix' |
| 'GD' (partner buys land, gives to DRAAS on GD) | `cf_offer_type`: 'Outright' + note structure in Proposal Notes |
| 'Buy together with partner' (e.g. Jiraffe Capital) | `cf_offer_type`: 'Outright' |
| 'Value-add / Brownfield / Built-up' (existing building) | Same pipeline: use 'Sqft' UoM, cf_land_size_sqft, cf_expected_total_built_up_area_in_sqft |
| 'Villa / Villas' | `cf_product_type`: 'Villa' |
| 'Apartments' | `cf_product_type`: 'Apartment - ...' |
| 'Plots / Plotted' | `cf_product_type`: 'Plots' |
| 'Commercial / Office / Co-working' | `cf_product_type`: 'Commercial' (no 'Office' option; use 'Commercial') |
| 'Info Memo (IM)' / 'PPTX presentation' | `cf_offer_document` — single-file attachment field |
| 'Hospital conversion presentation' | Note in Proposal Notes + add_note |
| 'Marketing document for hospital/other use' | `cf_land_legal_set` (fallback — no perfect field; document in notes too) |
| 'Google Maps link' | `cf_location_google_maplink` — accepts URL string directly (despite being "attachment" type) |
| 'Advance ₹X Lakhs/acre' (JV refundable) | `cf_expected_refundable` = X × 100000 ÷ 43560 (per-sqft); `cf_expected_total_refundable_amount` = X × 100000 × acres. Worked example: ₹75L/acre → 172.18/sqft, 21A → ₹15.75 Cr |
| 'Goodwill ₹X Lakhs/acre' (JV non-refundable) | `cf_expected_goodwill` = X × 100000 ÷ 43560 (per-sqft); `cf_expected_total_non_refundable_amount` = X × 100000 × acres. Worked example: ₹80L/acre → 183.65/sqft, 21A → ₹16.8 Cr |
| 'Market Value ₹Y Cr/acre' | `cf_expected_total_outright_cost_of_land` = Y × 10000000 × acres (use as the market-value benchmark). Worked example: ₹6.5 Cr/acre × 21A → ₹136.5 Cr |
| 'Total upfront expected' | `cf_total_upfront_investment_expected` = refundable total + non-refundable total (e.g. 15.75 + 16.8 = ₹32.55 Cr) |
| 'DRA takes X% stake in a purchase SPV / Pvt Ltd, balance monetized jointly to a developer' | `cf_offer_type`: 'Outright' (landowner is bought out; matches the GD precedent). `cf_expected_total_outright_cost_of_land` = ₹/acre × acres (full land cost); `cf_total_upfront_investment_expected` = stake% × full land cost. Full structure → Proposal Notes + add_note. Worked example (2026-08-24, #54916166): ₹2.5 Cr/acre × 50A = ₹125 Cr; DRA 25% stake = ₹31.25 Cr upfront |

## From analysis to action: broker WhatsApp + Kelsa note workflow

When NDR reviews the analysis and says "put these questions to the broker" / "send this as a WhatsApp to [broker]" — the deliverable is BOTH a Kelsa note AND a WhatsApp link, done in parallel.

### Step 0: Draft the WhatsApp message from NDR's voice correction

NDR will speak his version of the message (often a restatement of the key questions in his own words). The draft must:
1. **Use his exact framing** — he frequently reorganises the questions into his preferred order (e.g. "first clarify quantum/inventory, then deal structure, then timeline/docs")
2. **Use his tone** — for brokers: direct, numbered items, "Boss" or "Chief" if he used it, no greeting boilerplate
3. **Keep it conversational Indian English** — "appreciate your help", "once I have these clarities I can prepare for the meeting"

### Step 0.5: Look up the broker's contact info (phone number for WhatsApp link)

NDR often says "find his phone number, it should be in our contact sheet." After drafting the message, BEFORE posting to Kelsa or generating the link:

1. **Search the NDR DRAAS contacts sheet** (Sheet ID `1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g`) for the broker's name — scan the First Name column (col A, index 0) with the name as NDR said it AND any phonetic variants.
2. **Cross-check with People API** `searchContacts` across all 3 accounts (google-draas, google-ahfl, google-gmail).
3. **Voice-name correction pattern:** NDR's voice may say "Avni" / "Amni" but the sheet stores "Anvi" — search by partial + phonetic matches. The sheet's Organization Name column (col K, index 10) is especially useful for company-name lookups.
4. **Phone number extraction** — the sheet's phone columns start at col 28 (Phone 1 - Value) through col 38 (Phone 6 - Value). Use range `A:AM` to capture all phone pairs. Check for `type: "Mobile"` or `type: "Work"` labels; verify the number is valid (12-digit wa.me segment for India: 91 + 10 digits).
5. **If the broker's name is not immediately found** by the spoken name, try the organization name (e.g. "Avni Consultancy" → search "Anvi" in col K). The contact may be stored under the company name, not the person's name.

### Person resolution: NDR says "add X to the lead" / "and X"

Recurring pattern (observed 2026-08-21 "and Prasad", plus earlier sessions): NDR finishes a complex instruction with "and X" — meaning "also find person X and associate them with this Kelsa lead." The resolution chain is multi-step and often fails on the first attempt:

1. **Try `contact_resolver(query="X", context="<project>")`** first — fastest path. May fail if the session's gws_service isn't configured (observed `"User has no gws_service configured"` — this is a config gap, not a data gap; fall through to manual methods).
2. **Try `entity_resolver(query="X")`** — searches contacts + projects + land proposals + topics. Catches voice-transcription errors.
3. **FALLBACK: Likely the person is NOT in the resolver indexes.** NDR's contacts live in three overlapping places: Google Contacts (People API), the NDR DRAAS Google Contacts Sheet, and Gmail email threads. Each has different discoverability:
   - **People API**: `build_service('people', 'v1', service_name='google-draas')` → `people.connections().list(...)` or `people.searchContacts(query='X', ...)` — works for contacts synced to Google. Use `write_file` to a .py file + `terminal` with `/opt/hermes/.venv/bin/python3` (see code-execution pitfall below).
   - **Contacts Sheet**: Sheet ID `1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g`, range `A:Z`. Also accessed via `build_service('sheets', ...)`. Look for the name across all columns — voice transcriptions often mangle names but the Free-text search finds fragments.
   - **Gmail**: `gmail.users().messages().list(userId='me', q='<name>', ...)` — recent emails from or about the person. Cross reference from: field.
4. **Once a candidate is found**, check if they're a Kelsa user: `list_users(pipeline_id=519, query="<name>")`. If they ARE → add_note with @mention + update_lead assignee. If they're NOT → tell NDR explicitly: "X is not a Kelsa user. Found their details: <email/phone>. Can't assign them in Kelsa unless they have a Kelsa account."

**Code-execution pitfall (execute_code + f-strings + bash heredoc):** Python scripts that need to call `build_service('people', ...)` or `build_service('gmail', ...)` from multiple accounts CANNOT be run inline in `execute_code` when they contain f-strings — the shell passes the code via stdin and bash interprets curly braces in f-strings as heredoc syntax, producing `syntax error near unexpected token '('`. The reliable approach is:

```python
# ❌ DON'T — inline execute_code with f-strings inside terminal()
# ✅ DO:
write_file(path="/tmp/find_person.py", content="""...Python code...""")
terminal("/opt/hermes/.venv/bin/python3 /tmp/find_person.py")
```

This applies to any Python script that uses f-strings with dict access (e.g. `f"Name: {n.get('displayName')}"`) — always write to a temp file and run via venv python.

### Step 1: Post the message as a Kelsa note

```python
kelsa_call_tool(
    tool_name="add_note",
    arguments={
        "lead_id": lead_id,
        "pipeline_id": 519,
        "text": "=== WhatsApp Message Draft for [Broker Name] ([Company]) — [Date] ===\n\n\"Full message text...\"\n\n---\nDrafted by: Nishant Ranka | Not yet sent"
    }
)
```

The note header should include the broker name, company, and date so it's searchable in the activity log. The `---` footer marks the draft boundary if NDR later adds follow-up notes.

### Step 2: Generate the WhatsApp link

```python
whatsapp_link(
    phone=broker_phone,  # from Step 0.5 contacts lookup — pass when found
    text=message_text,   # no raw & — rewrite to "and" first
    platform="telegram"
)
```

- **If NDR provided the broker's phone number** (or you found it via Step 0.5 contacts lookup), pass it to the tool for a one-tap link
- **If no phone number is available** (broker not in contacts, number not found), omit the phone parameter — NDR will pick the contact from his WhatsApp chat history with the broker
- **The `whatsapp_link` tool** handles all URL encoding
- **Step 0.5 lookups should be attempted BEFORE reaching the "no phone" fallback** — NDR has explicitly asked to have the phone number included when available

### Step 3: Report both deliverables

Tell NDR:
1. ✅ Message posted as note on Kelsa lead #[id] — [link]
2. ✅ WhatsApp link ready — use the display_link to open WhatsApp with message pre-filled

### Broker response follow-up

When the broker replies (on WhatsApp) and NDR shares the response, the pattern repeats:
1. Post the broker's response as another note on the same Kelsa lead
2. Draft NDR's follow-up as a new WhatsApp link
3. Post the follow-up draft as a note too — creates a complete correspondence trail on the Kelsa record

This keeps every broker negotiation step auditable on the Kelsa record without requiring NDR to copy-paste WhatsApp messages manually.

## Pre-creation analysis: evaluating a land proposal from a broker brief

When NDR shares a raw broker WhatsApp proposal (text + map link + maybe a brief), the Kelsa record isn't the first deliverable. Do the **analytical walk-through** with NDR first so he can sanity-check the deal before it's entered:

### Step 1: Land Math (always start here)

Convert every size field and compute saleable area:

| Conversion | Formula | Example |
|---|---|---|
| **Acres → Decimal** | `acres + guntas/40` | 17A 6G = 17 + 6/40 = **17.15 acres** |
| **Total sqft** | `decimal_acres × 43560` | 17.15 × 43,560 = **7,46,734 sqft** |
| **Sqm → Sqft** | `sqm × 10.764` | 2,202 sqm × 10.764 = **23,702 sqft** |
| **Total outright cost (rate/sqft)** | `sqft × rate` | 23,702 × ₹6,000 = **₹14.22 Cr** |
| **Sellable sqft (plotted dev @ 55%)** | `total_sqft × 0.55` | 7,46,734 × 0.55 = **4,10,704 sqft** |
| **Sellable sqft (plots @ 60%)** | `total_sqft × 0.60` | Use for higher-efficiency layouts |

The 55% factor accounts for roads, parks, civic amenity spaces. Seller's claim of "4,00,000 sqft" vs computed 4,10,704 → difference of ~2.6%, well within rounding.

**Always flag what NDR flags:** Phase 1 size not disclosed, 98 sites remaining but no sqft per site, total project vs unsold-only ambiguity.

### Step 2: Identify what's actually on offer

Three common ambiguity patterns in broker proposals:

| Pattern | What to ask |
|---------|------------|
| **"Phase 1 fully sold out"** | Size of Phase 1? Sold sqft / number of sites? |
| **"98 sites remaining"** | Average site size? Total sqft of unsold inventory? |
| **"4,00,000 sqft saleable"** | Does this include or exclude Phase 1 sold area? |
| **"₹2,400/sqft SR Value"** | When was the SR valuation done? Does it reflect current market? |

### Step 3: Market rate reality check

Compare the offered rate against adjacent projects (use web_search for portal listings):

- Adjacent project rates (Vrunda City, Artha Midas/Serene)
- Portal data (MagicBricks, Roof&Floor, NoBroker)
- NDR's own estimate: "fully developed layout with landscaping = ₹4,000–₹4,500/sqft"

If the offered rate (₹2,400) is well below market (₹4,000+), flag the *why*: litigation cloud, ex-partner holding docs, incomplete development, distress.

### Step 4: Deal structure thinking

NDR's preferred structure pattern for brownfield layout buyouts:

| Layer | Rate Band | Who Gets What |
|-------|-----------|---------------|
| **Base Cost (SR Value)** | ₹2,400/sqft | Seller (covers outstanding dues) |
| **DRAAS Margin** | ₹2,400 → ₹4,800 | DRAAS (branding, marketing, balance development) |
| **Upside Share** | Above ₹4,800 | 80% DRAAS / 20% Seller (profit share) |

This gives the seller floor certainty + upside participation, while DRAAS gets a healthy margin window.

### Step 5: Key questions for the seller

Before accepting the proposal, these questions must be answered:

**On Inventory:**
- Phase 1 total area (sqft/sites)? What's the site mix?
- 98 remaining sites — sqft breakdown by size?
- Total project site count? All phases?

**On What's Being Sold:**
- Entire 4L sqft (including sold Phase 1)? Or only unsold 98 sites?
- If only 98 sites — total sqft is ~1.5-2L, not 4L. Which is it?

**On Title & Legal:**
- Current title holder? Developer? Landowner? Artha?
- Fox Mandal opinion — shareable? Caveats?
- When exactly are original docs released from ex-partner?

**On Development:**
- Cost to complete clubhouse + landscaping?
- Are all 98 sites fully developed (roads, drains, water, electricity)?
- Any pending approvals / violations?

**On Structure:**
- Open to profit share above threshold (e.g., 20% above ₹4,800/sqft)?
- Timeline for Tranche 2 pricing discussion?

See **`references/hoskote-brownfield-deal-analysis.md`** for a worked example of this analysis applied to a live brownfield layout buyout (17A 6G, Artha litigation, ₹2,400 base + profit share structure).

## Known dropdown values (DRA Land Proposal, pipeline 519)

These are observed from existing records — verify against live pipeline before use. New-session gotchas: `references/proposed-stage-gotchas-and-broker-source-verification.md`.

- **City**: Bangalore (observed). **Dropdown is NOT all-India — no hill
  stations / non-metro TN cities.** Verified 2026-08-16: Coonoor (Nilgiris)
  is NOT an option; the only Tamil Nadu option is **chennai**. When the
  parcel is in a TN city absent from the dropdown (Coonoor, Ooty, Kotagiri),
  use `cf_city: "chennai"` as the state anchor and **flag the mismatch in
  `cf_proposal_notes` + an add_note** (e.g. "City field = Chennai — Coonoor
  not in dropdown; property is Nilgiris district"). Never invent a city
  value — the dropdown rejects unknown values.
- **Land Size UoM**: Acres, Sqft (use Sqft for built-up commercial properties)
- **Land Status on Offer**: Tax Document, Converted, Compounded, etc.
- **Land Zone**: Agricultural, Industrial, Commercial, Residential, etc.
- **Offer Type**: Outright, JV, Mix (and 5 others from 8 total)
- **Proposal Source**: Agent/broker names (88 options — Nishant Prakash, Sahil Khan, Rajesh Talreja, Kiran, Deepak Lehar Singh, Prakash(Roopa), etc.)
- **Product Type**: Villa, Row House, **Apartment - High Rise (>G+8)**, **Apartment - Mid Rise (<G+8)**, **Apartment - Low Rise (<G+4)**, Plots, Farm Plots, **Commercial**, etc. — verify with `get_stats(pipeline_id=519, group_by="cf_product_type")`, which returns the live option list + record counts. **G+4 / 5-floor apartment buildings → "Apartment - Mid Rise (<G+8)"** (matches the "<g+8" option; low rise is "<g+4").

## Proposal Source handling rule (user preference, confirmed 2026-07-24)

**NDR's rule:** When the proposal comes from a broker or partner:
1. If the person's name IS in the `cf_proposal_source` dropdown → use it directly
2. If the person is a known contact (in NDR's phone/contacts, a known business associate like Raghav Rao, Rameshwaram Cafe founder) → try to use their name directly as the source. Since the MCP cannot reliably add new dropdown values, use "Nishant Ranka" as the source and put the actual person's name + full details (who they are, how connected) in `cf_proposal_source_details_notes`. Add a note "Please add [Name] to Proposal Source dropdown" in the lead notes so the admin team can add it.
3. If the person is an unknown broker/agent → use "Nishant Ranka" as the source, put the broker name in `cf_proposal_source_details_notes`
4. Always document HOW the proposal was received in `cf_proposal_source_details_notes` (e.g. "Received via WhatsApp by NDR on [date]", "Received via email", "Received via phone call")

This keeps the dropdown clean while maintaining traceability.

## Matching a voice-note broker name to the dropdown

When NDR forwards a broker's WhatsApp proposal with a voice note, the spoken broker name is often garbled. Before creating the lead:

1. **Enumerate the actual dropdown values:** `get_stats(pipeline_id=519, group_by="cf_proposal_source")` — returns every source in use (~93 options) with record counts. This beats guessing or asking NDR to spell it.
2. **Phonetically match the spoken name against that list.** The dropdown uses lowercase informal spellings ("bhuran sait", "kaushik broker", "nafeesa broker", "nishant prakash"). A partial match is usually the right broker.
3. If the name IS in the dropdown → use it directly as `cf_proposal_source`. Only fall back to "Nishant Ranka" when no phonetic match exists.
4. **Check the broker's other records before creating** (`search_leads` query `cf_proposal_source:<broker name>`) — confirms the match and doubles as part of the duplicate check.

Detailed worked examples (voice transcription patterns, Bhuran Sait marker facts, Aranyam/Ravi Sir parcels): `references/voice-broker-matching-and-aranyam-deals.md`.

## Scope of this pipeline

While named "DRA Land Proposal", this pipeline has been used for **both raw land AND built-up commercial property** proposals. Existing precedents:
- Lead #44363936 — 60,000 Sqft commercial property (built-up) on Devanahalli Main Road
- Lead #49236801 — 1.23 A in Veerasandra for Commercial Development on Outright

For built-up properties:
- Use `cf_land_size_uom: "Sqft"` and `cf_land_size_sqft` instead of acres/guntas
- Use `cf_expected_total_built_up_area_in_sqft` for leasable/saleable built-up area
- Use `cf_product_type: "Commercial"` for office/commercial
- Location fields (village/hobli/taluk) can be filled with local area details
- Financial fields like `cf_expected_rate_per_sqft` work natively for built-up

## Critical: OAuth must complete before tools are available in-agent

Even when `hermes mcp list` shows `Kelsa-Read  ✓ enabled  all`, the MCP tool functions (e.g. `kelsa_call_tool`, `mcp_Kelsa_Read_*`) are **NOT registered in the agent's tool list** until OAuth PKCE authorization completes and a token is stored. The `all tools enabled` status only means the MCP server endpoint is reachable and the client is registered for OAuth — it does NOT mean tokens exist.

**To verify real availability:** check whether any `mcp_Kelsa_Read_*` tool appears in the agent's tool list (`hermes tools list`). If they're absent, OAuth is the blocker regardless of `hermes mcp list` output.

## Pitfalls

1. **DO NOT pass incorrect stage_id.** Stage IDs are NOT pipeline IDs. Omit `stage_id` from `create_lead` to default to the first stage (Proposed).

2. **JV Developer Ratio shows negative/incorrect after save.** The field `cf_expected_jv_ratio_for_developer` in pipeline 519 behaves unreliably — passing 35 stored as -64 in at least one case (Bidadi proposal, Aug 2026). This appears to be a system-level computation bug. Always verify the stored value via `get_lead` after creation. If incorrect, note the discrepancy in lead notes and flag for admin correction in Kelsa. Do NOT re-submit via `update_lead` — it may fail the same way.
2. **Draft processing is async.** After `create_lead`, always poll with `get_draft_status` before searching for the record.
3. **Attachment field types.** `cf_location_google_maplink` accepts a URL string directly even though it is an "attachment" type. Other attachment fields need the `register_upload` object.
4. **Google Maps links.** These are often shortened `maps.app.goo.gl/...` URLs — use them directly as strings in the field value.
5. **Drop down values are not returned by `get_pipeline`.** The API response says "dropdown (N options)" but doesn't list them. To discover valid options:
   - **Fastest: `get_stats(pipeline_id=519, group_by="cf_product_type")`** — returns every option IN USE across records, with record counts. Use this as the first approach for any dropdown you need to discover. Works for ANY dropdown field: `cf_city`, `cf_proposal_source`, `cf_offer_type`, `cf_land_zone`, `cf_status_on_offer`, `cf_land_size_uom`, etc. The option name shown by get_stats IS the exact label the create call expects.
   - **Fallback:** examine an existing lead via `get_lead` (works but only shows ONE record's value).
6. **File upload order is critical.** `get_upload_url` returns single-use presigned URLs that expire in minutes. Upload to S3 immediately after receiving them. Do not batch-get all URLs before uploading.
7. **S3 POST must include ALL returned fields** (key, policy, x-amz-credential, x-amz-signature, etc.) plus a `file` field at the end. Missing any field returns HTTP 403.
8. **Curl upload fails (exit code 26) when filename has spaces or special characters.** The S3 POST `file=@` parameter doesn't handle spaces well from within shell scripts. Workaround: copy the file to `/tmp/simple_name.pdf` first, then upload from there. Verify HTTP 201 response.
9. **If `assignee_id` fails with "me"**, try omitting it — the record will be unassigned, which is fine at the Proposed stage.
10. **Site visit videos go in `cf_land_pics` (multi-file field).** They display as images/videos inline in Kelsa.

10b. **To ANALYZE a site-visit video, extract a frame first.** `vision_analyze` rejects video files ("Only real image files are supported"). Grab a representative frame with ffmpeg, then analyze the frame:
    ```bash
    ffmpeg -y -i video.mp4 -ss 2 -frames:v 1 /tmp/frame.jpg
    # check duration/resolution with: ffprobe -v error -show_entries format=duration -show_entries stream=width,height video.mp4
    ```
    One frame is usually enough to characterize the parcel (terrain, road access, boundaries, water body, fencing). For a longer drive-through (80s+), a frame at ~2s shows the road approach; a later frame can show land parcels. The video itself still goes to Kelsa via `cf_land_pics`.
11. **Checklist PDFs with owner names** go in `cf_revenue_maps_and_documents`.
12. **Values should be numeric without INR symbol or commas** — `550000000` not `5,50,00,000` or `₹55 Cr`.
13. **`cf_sy_nos` format** — comma-separated list of survey numbers (e.g. `"129/1, 129/2, 127/1, 150/1"`). Do NOT include spaces after commas if the existing records omit them — check an existing lead first for consistency.
14. **Dropdown discovery** — `get_pipeline` returns "dropdown (N options)" but NOT the actual option values. To discover valid options: search for an existing lead with `get_lead` on a matching proposal type, or browse leads in Kelsa's web UI.
15. **The pipeline handles built-up commercial** — not just raw land. For office buildings, use `cf_land_size_uom: "Sqft"` and `cf_product_type: "Commercial"`.
16. **`cf_status_on_offer` (Land Status On Offer) is finicky.** Not all values work for all records. "Compounded, Converted" (observed in an existing lead #44363936) may fail on a new record with `Invalid dropdown value`. When in doubt, omit this field on creation — it's not required at the Proposed stage. Add via update_lead later once you confirm valid values by examining a similar existing lead.

17. **`register_upload` does NOT require `size`.** The parameter is optional — omit it if you don't have the exact bytes. The `name` field is also optional but recommended for display.

18. **Create-then-attach pattern.** When you have many files (7+ photos, videos, docs), you don't need to upload+register everything before creating the lead. Two-phase approach:
    - Phase 1: create_lead with basic fields (text, dates, dropdowns, location) → get lead_id
    - Phase 2: get_upload_url → curl upload → register_upload → update_lead to set attachment fields
    This avoids holding up the record creation while waiting on multiple file uploads.

19. **`cf_revenue_maps_and_documents` is a MULTI-file attachment** (confirmed 2026-08-01): pass an array of register_upload objects to attach multiple RTC images / revenue docs in one field — `[{"url": "...", "upload_id": N, "name": "rtc1.jpg"}, {...}]`. It renders each as an inline `<img>`. Same array pattern applies to `cf_land_pics` (videos + PDFs + images all accepted in one array).

19. **Hospital/dual-use properties.** When a commercial building also has a hospital conversion presentation, document it in `cf_proposal_notes` and add a separate `add_note` call with the details. There's no dedicated field for "alternative use study."

20. **`cf_offer_document` is the right field for the IM (Info Memo).** PPTX files go here. Marketing documents for alternative uses (hospital, etc.) have no perfect field — use `cf_land_legal_set` as a fallback, but note in the lead activity that it's not a legal document.

21. **Kelsa MCP integer-argument bug (intermittent — first observed 2026-07-14, confirmed working 2026-07-16).** On 2026-07-14 the Kelsa MCP server rejected every integer-typed argument at the JSON-RPC validation layer with `Invalid arguments: value at /<field> is not an integer`. This affected `pipeline_id`, `lead_id`, `account_id`, `per_page` across all tools. **However, as of 2026-07-16, all integer arguments worked correctly** — suggesting the bug was a transient server-side issue. If you encounter it: try once, and if it fails, switch strategies immediately (see fallback below). Do not retry the same call shape more than once — the bug is server-side and retries will fail identically within the same session. Surface the lead-URL fallback to the user after the first confirmed failure.
    - **If you only need to LOOK at a lead the user references:** ask the user to paste the lead URL or just the lead ID. The Kelsa web UI is read-only and renders without auth for the user's own account.
        - **URL format (any pipeline):** `https://kelsa.io/{pipeline_id}/leads?current_view=list&current_item_id={lead_id}&page=1&account_id={account_id}`
        - **Known pipeline IDs:** 519 (Land Proposal), 537 (PO-WO Issuing), 516 (Invoice Processing), 531 (Vendor Shortlisting), 4475 (Companies Master), 2033 (Project Budgets)
        - **Known account ID:** 5 (DRA)
    - **If Kelsa MCP AND browser are both unavailable, but you have lead_id + pipeline_id from a past session:** reconstruct the URL directly from session-derived values. Search past conversations with `session_search(query="kelsa lead_id OR lead * pipeline 537")` to find the lead's pipeline and ID from the session trace (the `create_lead` response contains both `lead_id` and `pipeline_id`). Then construct: `https://kelsa.io/{pipeline_id}/leads?current_view=list&current_item_id={lead_id}&page=1&account_id=5`. Example: Kelsa PO-WO #750 (AM Office Solutions, pipeline 537, lead_id 53744737) → `https://kelsa.io/537/leads?current_view=list&current_item_id=53744737&page=1&account_id=5`. The `filter_id` parameter is optional — omit it if not known.
    - **If you need the S3 image URLs from a lead:** the lead page renders them inline; ask the user to right-click → "Copy image address" on each, OR to share a screenshot of the lead so vision_analyze can OCR the URLs. The bucket `kelsa-clients-production.s3.ap-south-1.amazonaws.com` is fully private (HTTP 403 on every prefix guess) — no public listing works.
    - **Do not announce "I'll try one more time" repeatedly.** Confirm the bug once, then surface the workaround to the user.

22. **Voice-note project disambiguation.** Skylark group properties all have similar names (Ithaca, Zenith, Dasos, WestBury) and easily get confused in voice notes / Drive search. Before pulling any data for a Skylark project, **confirm the exact project name from the user** — even if Drive already has a folder called "Skylark" with content. The user said "Skylark" out loud; that is NOT enough to pick a folder. Ask which one (Ithaca / Zenith / Dasos / WestBury) before reading 18 PDFs from the wrong deal. Same risk applies to any multi-project developer family (Prestige, Brigade, Sobha, etc.). Real cost of getting this wrong: pulled the entire Skylark Dasos `Brochure.pdf` (commercial), `Skylark_DesignPresentation.pdf`, and 18 Dasos legal PDFs before the user corrected me — Skylark Dasos is residential too, the actual deal was Skylark Zenith, and the file-fetch was a 4-minute waste. If the user's first message is short or ambivalent ("this is a Skylark deal"), ASK before reading files. The 5 seconds of clarification saves minutes of misaligned file reads.

23. **Retry-loop discipline on the MCP.** If Pitfall 20 (integer-arg bug) fires, **the first failed call is enough evidence.** Don't retry the same call shape 2+ times to "be sure" — the bug is server-side and if it's active, every retry will fail identically. However, the bug is **intermittent** (broke 2026-07-14, worked 2026-07-16), so if a call fails, try once with a different parameter shape (e.g. string instead of integer for stage identifiers), then switch to the lead-URL fallback or ask the user to retry later.

24. **"Already in S3" does not mean you can reach the S3 bucket.** When the user says "the images are already uploaded to S3" they almost always mean Kelsa's private bucket behind per-lead URLs — NOT a publicly-listable bucket. Treat any "fetch the S3 images" request as gated by either (a) a working Kelsa MCP call to fetch the lead, or (b) the user pasting the URLs. Do not try to enumerate S3 prefixes; the bucket returns 403 on every variant.

24. **Kelsa-Read MCP server may be `enabled: false` in config.yaml.** This was observed on 2026-07-24: the `Kelsa-Read` MCP server had `enabled: false` in `/data/hermes/config.yaml`, so no Kelsa tools (`kelsa_call_tool`, `mcp_Kelsa_Read_*`) were available in the agent's tool list. Fix:
    1. Enable the server: `hermes config set mcp_servers.Kelsa-Read.enabled true`
    2. Verify it's listed: `hermes mcp list` — should show `Kelsa-Read` with status `✓ enabled`
    3. Check tools are registered: `hermes tools list` — look for `MCP servers: Kelsa-Read all tools enabled`
    The native MCP client connects and registers tools immediately after config change (no restart needed in most cases).

25. **OAuth required for Kelsa MCP — headless workaround.** The Kelsa-Read MCP server requires OAuth 2.1 PKCE. In a headless environment, the local callback server at `http://127.0.0.1:<port>/callback` is unreachable from the user's browser. Three approaches:
    - **Option A (preferred — URL capture technique):** Run `hermes mcp test Kelsa-Read` (NOT `login`) in background with `notify_on_complete=true`. The `test` command reliably prints the authorization URL after 5-15s, then waits ~85s for the callback. Capture the URL via `process(action='wait', timeout=90)` and read the full log. Send the URL to the user and ask them to open it in their browser. **Gotcha:** `hermes mcp login` in background mode may buffer all output until timeout (never printing the URL) — prefer `test` over `login` for URL capture. If the user opens the URL on their machine and the redirect to localhost fails after authorization, ask them to paste back the error-page URL (it contains the `?code=` parameter) so you can complete the flow manually.
    - **Option B (fallback):** If OAuth cannot be completed, use Kelsa's web UI directly. Ask the user to create leads manually or paste lead URLs. Do not block on MCP availability.

26. **`cf_expected_jv_ratio_for_developer` displays a wrong value no matter what you set (observed 2026-08-11: -49 for 50; 2026-08-16: -24 for 75).** It is NOT "-49 always" — it renders some wrong offset of the true value. Setting via `create_lead` OR `update_lead` both render wrongly in the MCP response — a field-rendering quirk (the web UI may show the correct value). Do NOT retry-loop updates trying to fix it: one correction attempt is enough, then move on. The landowner side (`cf_expected_jv_ratio`) renders correctly, and the true split MUST be captured in `cf_proposal_notes` (e.g. "JD Ratio 50:50 (slightly negotiable)" / "25% profit share to landowner") so the record is unambiguous regardless of the display bug.

27. **`execute_code` with f-strings in Python breaks when the code is inside a bash heredoc (observed 2026-08-21).** When you call `execute_code(code="...")` and the code contains Python f-strings with dict access (e.g. `f"Name: {n.get('displayName')}"`), the shell's heredoc parsing interprets the curly braces as subshell syntax and fails with `syntax error near unexpected token '('`. The fix: `write_file` the Python code to `/tmp/script.py`, then `terminal("/opt/hermes/.venv/bin/python3 /tmp/script.py")`. This applies to any non-trivial Python that mixes f-strings, dict access, and multi-line string literals. Simple Python (no f-strings, no dict `.get()` calls) works fine in execute_code.

28. **Omitting `cf_product_type` at create_lead silently defaults the record to `Apartment - High Rise (>G+8)`** (observed 2026-08-24 on #54916166, a 50A agricultural parcel — clearly wrong). Always pass `cf_product_type` explicitly when the product is known; if it was omitted and defaults badly, correct immediately with a follow-up `update_lead` — a plain string label works for dropdowns in update_lead too (e.g. `{"cf_product_type": "plots"}`), no {id,label} object needed.

28. See ref gejjegadahalli-50a-sibling-parcel.md

## Finding existing proposals (search patterns) — added 2026-08-01

When the user asks "find the proposal for X / check whether these two proposals are in Kelsa", the record name is NOT the only searchable surface. Search exhaustively before declaring a proposal missing:

1. **Record-name keywords** — `search_leads(pipeline_id=519, query="Foxconn")`, size (`"30 Acre"`), product (`"villa"`, `"plot"`), location (`"Chikkaballapur"`, `"behind"`).
2. **Source-field filter** — proposals often carry the broker in `cf_proposal_source` even when the name doesn't mention them: `query="cf_proposal_source:Nishant Prakash"` returns the 20-30 records sourced from that broker. This is the most reliable "find all proposals from X" query.
3. **Recent-first sweep** — `query="stage:Proposed"` + `sort="updated_at"` + `order="desc"` lists the newest proposals; if the user believes the proposal was entered recently, check the top of this list even if keyword search misses.
4. **Only after 3+ variants return nothing** do you declare "not in Kelsa" — and then tell the user explicitly (they may add it themselves, or it may be in a different pipeline / under a different name). Do NOT silently create a duplicate.

### Property alias search ("the land is also known as X")

When the user says a parcel has an alternate name (e.g. "Bestamanahalli is also known as Sanchaya land"), search BOTH names, and search across related pipelines (Land Proposal 519 + DRA R&D 2000), before concluding. **If Kelsa comes up empty, search Drive + Gmail BEFORE declaring absence** — the deal may exist only as documents (MOU / Addendum / meeting minutes) that were drafted in-house and never entered into Kelsa. Observed 2026-08-03 (Bestamanahalli = "Sanchaya lands"): `Sanchaya` in 519 returned only an unrelated Mysore Road lead and `Sanchaya` in 2000 returned 2 old retired Electronic City files, but Drive held the full deal — `20241001 MOU Dra Realty & Sachaya Land & Estate Pvt Ltd Besthamanahalli`, `20241214 ADDENDUM DRA Realty & Sanchaya Phase1Part1 7Acres`, `20240928 Meeting Minutes - Sanchay Lands Team Besthamanahalli`, `20241209-MOU Bestamanhalli Phase 2.pdf` — owned by vkdas@draas.com (Vinod) + ndr@draas.com, matching the user's "proposal mostly by Vinod/Rahul/NDR". Drive search pattern: `drive.files().list(q="name contains '<alias>' or fullText contains '<alias>' and trashed=false")` across service_name google-draas (try both the correct AND misspelled alias — the MOU filename spells it "Sachaya"). Gmail: `gmail.users().messages().list(q='<alias>')` catches Drive share-request notifications and forwarding threads that name the document. See **`references/sanchaya-bestamanahalli-deal.md`** for the full deal record.

**Search-quirk refinement:** `search_leads(query=...)` is NOT strictly name-only — `Sanchaya` matched #1284804 whose record name contains no "Sanchaya" (the term lives in some other field/note). So: (a) a hit on an unrelated-looking record means the term appears somewhere in it — check its fields before dismissing; (b) absence from name search is still not proof of absence from Kelsa, and definitely not proof the deal doesn't exist on Drive/Gmail.

Report honestly: "alias X found no matching Kelsa record" instead of stretching an unrelated hit — then surface the Drive document trail and offer to create the proposal.

### Person names (Ajay, Pawan Kumar Nahar) are often NOT on the record

When the user names people involved in a proposal (owner, broker, contact) and asks you to "find the proposal with Ajay" or says "we uploaded Pawan Kumar Nahar", do not expect the name in the record name — search `Nahar`, `Pawan`, `Ajay`, `cf_proposal_source:<name>` (all returned 0 on 519 for Bestamanahalli leads), then read the lead's notes/events before declaring. Often the person genuinely hasn't been attached yet. Deliver the proposal links anyway, state explicitly which names are NOT on which record, and offer to add them (add_note with @mention adds follower + notifies; or update proposal source details).

**⚠️ The person may belong to a DIFFERENT deal entirely.** Observed 2026-08-03: user insisted "Ajay" was involved in the Bestamanahalli/Sanchaya proposal. Kelsa + email + Drive search for Ajay only surfaced **Ajay Singh Bist**, an investor in **Sevaganapalli Land Partners (Ranka Oasis SLP, Krishnagiri TN)** via a 2025-07-05 Loan-cum-Investment Agreement (₹1,03,95,000) — a completely different project from Bestamanahalli. Name collisions across the DRA portfolio are common (Ajay Singh, Sanjay, Srinivas, Praveen, Rahul all recur). Before connecting a person to a parcel, verify the PROJECT (check the agreement's counterparty/folder: "investor Loan cum investment Agreement Sevaganapalli" was the giveaway) — never assume a name that surfaces in Drive/email belongs to the deal under discussion.

**Worked example (2026-08-01, morning):** user asked to verify two proposals "both from Nishant Prakash" — a 10-acre villa outright behind Foxconn, and a 30-acre plotted before Chikkaballapur. Searches: `Foxconn` (0), `Fox` (1 unrelated), `Chikkaballapur` (18, none matching), `cf_proposal_source:Nishant Prakash` (26, none matching), `30 Acre` (21, none), `Manak` (0), `behind` (60). Conclusion: both missing → user said they'd add them. Closest decoys were Thylagere 10A villa (Jiraffe GD, different deal) and Iranganahalli 30A (2024, Kaushik Broker) — check deal structure (offer type, source, GD vs outright) before assuming a lookalike is the same deal.

**Worked example sequel (2026-08-01, evening) — SIZE CORRECTION REOPENS THE SEARCH, and the dismissed "closest hit" WAS the deal:** later that day the user corrected the second property: "approximately 40 acres, not 30". Re-searching with the corrected size exposed that the **40A Arasanahalli/Kuppahalli proposal ALREADY EXISTED** — #54039174, created by **Bharat H on 25 Jul**, source Nishant Prakash, same rate (₹1,102/sqft = ₹4.8 Cr/acre), same Sy Nos (S1–S4 stages), and the map link resolved to **exactly the same pin (13.391932, 77.716490)** as the user's freshly shared link. The 30A-sized search had missed it because the record says 40A. Lesson: **when the user corrects a property fact (size, location, offer type), RE-RUN the pipeline search with the corrected facts and re-examine every previously-dismissed "closest hit" before creating anything** — a record you wrote off under the old facts can be the same deal under the new ones.

## "Which land does this R&D / research PPT pertain to?" (identify + link the doc)

Recurring pattern (2026-08-02, Thylagere): Prakash sends an R&D / market-research PPTX for a land parcel, and the user isn't sure which parcel/Kelsa proposal it maps to. Workflow:

1. **Find the deck on Drive, not by guessing.** Prakash's research decks are native Google Slides owned by `psingh@draas.com` and often NOT filed under the R&D folder (`R&D/Research Reports` is empty) — they sit at Drive root. Search by owner + recency + mimeType:
   ```python
   drive.files().list(q="modifiedTime > '2026-07-25T00:00:00' and trashed=false",
                      pageSize=100, fields='files(id,name,mimeType,modifiedTime,owners)',
                      orderBy='modifiedTime desc').execute()
   # filter results where owners contain psingh@draas.com and mimeType is a presentation
   ```
   The just-sent deck is almost always the newest psingh-owned presentation.
2. **Read the deck's content to identify the land — don't trust the title alone.** Export Slides → PPTX via Drive (`files().export_media`, Slides API may be disabled) and extract `<a:t>` text runs from the slide XML. The **joint-sketch slide** carries village/hobli/taluk + survey numbers; the overview slide carries project name/location. Cross-check those against candidate Kelsa records (village/taluk/district fields + map pin).
3. **Map to the Kelsa proposal** by searching `search_leads(pipeline_id=519, query="<village>")` — the record's `cf_village`/`cf_hobli`/`cf_taluk`/`cf_district` should match the deck exactly. Report the match with the lead link and the deal structure, and explicitly say when it is NOT the parcel the user assumed (e.g. Thylagere R&D ≠ the LG/Chikkaballapur deal — different taluk, different map pin).
4. **Flag survey-number mismatch.** The PPT joint sketch often lists a BROADER survey set than the Kelsa record's `cf_sy_nos` (which holds only the initial-buy subset). Document this rather than silently picking one:
   - `add_note` with the broader list + the user's explanation of the boundary (e.g. "initial ~10A lies WEST of the nala shown in the sketch; the balance behind the nala is the future aggregation extent, not part of the initial acquisition").
   - `update_lead` `cf_sy_nos` to the broader list with the subset parenthesised: `"129, 132/1-26, 133/1-2, ... (initial ~10A west of nala: 129/1-7, 127/1-2, 150/1-4)"` — keeps both facts on the record.
   - Add a separate note with the R&D link (original + any updated version) credited to the author: "R&D (Market Research) prepared by <name> (date) — Drive link(s): ...".

**Duplicate created anyway? MERGE, don't keep both.** If you already created a duplicate (map pin resolves identical to an existing lead), do NOT delete blindly and do NOT leave both live:
1. Identify the **canonical** record — usually the OLDER one (it often has richer notes: CLU status, market research, legal contacts — e.g. #54039174 had "Phase1 CLU converted, 25Ac registerable, Legal Adv Uday, Capital Jiraaf/Vineet Agrawal").
2. `update_lead` the canonical record with all the new media (sketch, layout, video, CDP map, owner table) + any new notes. Attachments are registered uploads — safe to reuse on the other record.
3. `update_lead` canonical with `assignee_id` and `add_note` with the `@[Name](id)` follower mention + RD brief.
4. On the duplicate you created, `add_note`: `"DUPLICATE — same parcel as #<canonical_id> (<name>, created by <X> <date>). Map pins identical (<lat>,<lng>). All media attached to canonical record #<id>. Please delete this duplicate."` — the admin team removes it from the web UI.

**Verify the pin BEFORE creating, not after.** The skill's disambiguation rule (resolve both the shared map link and the candidate lead's `cf_location_google_maplink`) must run as a PRE-CREATE gate when any near-hit exists in search results — not as a post-create fix. `curl -s -L <maps.app.goo.gl link> -w "%{url_effective}"` and compare the `@lat,lng` / `3d..4d` coordinates; identical coordinates = same property.

**⚠️ The "absent" conclusion can be WRONG — duplicate-prevention check (2026-08-01 evening session):** the user later corrected the second property to "~40 acres Chikkaballapur (not 30)". I created a fresh lead with all media, then discovered the SAME parcel was ALREADY in Kelsa: #54039174 "Chikkaballapur - 40 Ac Arasanahalli/Kuppahalli", created by **Bharat H on 2026-07-25**, with richer data (CLU status, market research, legal contacts Adv Uday / capital Jiraaf-Vineet Agrawal, ₹1,102/sqft). Why the earlier search missed it: the morning session searched when the parcel was described as "30 acres" and dismissed the 40A as "closest, not matching"; the actual deal was 40A all along.

**Mandatory duplicate check BEFORE create_lead on a land parcel:**
1. **Resolve the user's map link to a pin FIRST** (`curl -s -L <maps.app.goo.gl link> -w "%{url_effective}"`, extract `@lat,lng` / `3d<lat>!4d<lng>`). This is the definitive parcel identity — cheap and instant.
2. **Search by source filter + size variants** — `query="cf_proposal_source:Nishant Prakash"` with `sort="created_at"` `order="desc"` (recent-first) is the most reliable "what does this broker have in the system" query. Also try the village/survey-number words.
3. **If an existing lead's map pin matches the user's link → it is the SAME parcel.** Do NOT create a duplicate. The record may be created by a team member (Bharat H) under a different name and with different source-details — the name and assignee do NOT make it a different deal.
4. If the existing record is missing media the user just provided (sketch, video, CDP map, owner table), **merge into the existing record instead**: `update_lead` to attach the new files, then assign/mention as needed (see "Assignee + follower on an existing proposal"). Add a note on any accidentally-created duplicate: `"DUPLICATE — same parcel as #<canonical_id> (map pins identical: <lat>,<lng>). All media attached to canonical record. Please delete this duplicate."` There is no MCP delete tool — the admin removes it in the web UI.
5. **Rate sanity check:** ₹4.8 Cr/acre ≈ ₹1,102/sqft (48,000,000/43,560). If a pre-existing lead shows the same per-sqft rate as the user's per-acre figure, that's another same-deal signal.

## Mapping an "R&D" / market-research PPT to a Kelsa proposal

Recurring ask (2026-08-02 + earlier): Nishant receives a land market-research deck from **Prakash (psingh@draas.com)** — files are Google Slides named `<Village> ~<size> Acres — <Type> Development Market Research (vN)` (e.g. "Thylagere ~10 Acres — Villa Development Market Research (v5)") — and asks "which land does this R&D pertain to / which Kelsa proposal is it?"

Workflow:
1. **Find the deck on Drive**: search presentations owned by psingh@draas.com with recent `modifiedTime` (the just-sent deck is almost always the newest psingh-owned presentation). Query: `mimeType='application/vnd.google-apps.presentation' and modifiedTime > '<2 weeks ago>' and trashed=false`, filter results by owner email `psingh@`. Don't search by "R&D" name alone — many unrelated files (folders, spreadsheets) match.
2. **Read the slide content, don't trust the title alone** — but in practice the title is accurate for these decks. Key identifying slides: slide 2 (Project at a Glance: location/taluk/area), slide 3 (JOINT SKETCH — village, hobli, taluk, survey numbers), closing slide (Prepared by: Prakash Singh, DRA Group).
3. **Match to Kelsa**: `search_leads(pipeline_id=519, query="<Village>")`, then confirm with `get_lead` — village/hobli/taluk/district + product type must match. Worked example: Thylagere R&D (v5, 2 Aug 2026) → **#53691609** "Thylagere - 10 Acres near Prestige Goldshire - Villa Development via Jiraffe Capital GD" (Proposed, outright w/ Jiraffe Capital, ₹5.5 Cr/acre, ~₹55 Cr).
4. **⚠️ Survey-number mismatch pitfall**: the PPT joint sketch can list a BROADER survey-number set than the Kelsa record's `cf_sy_nos` (Thylagere: PPT lists 129, 132/1-26, 133/1-2, 134/1-2, 135/2-6, 136/1-2, 137/1-6, 138/1-7; Kelsa has 129/1-7, 127/1-2, 150/1-4). Likely the sketch covers a larger aggregatable extent than the initial parcel. **Flag the discrepancy to the user** — do NOT silently update `cf_sy_nos`; ask whether to reconcile.
5. **Offer to attach the deck** to the matched lead via `cf_offer_document` (single-file attachment field for IM/PPTX) — this is the sanctioned home for these decks.
6. **Distinguish from the LG-land style deals**: the LG Champions/Chikkaballapur deal (#48679748, 80A) is a different parcel entirely — check village/taluk before assuming a deck is for any in-flight deal.

## Assignee + follower on an existing proposal

To make a user a follower AND assignee on a proposal (e.g. for RD/diligence):

```python
# 1. Find the user's Kelsa ID
kelsa_call_tool(tool_name="list_users", arguments={"pipeline_id": 519})
# -> Prakash Singh <psingh@draas.com> — id=NNN

# 2. Assign (assignee_id is a STRING, not int)
kelsa_call_tool(tool_name="update_lead", arguments={
    "lead_id": lead_id, "assignee_id": "NNN"})

# 3. Add as follower via @mention note (adds follower + notifies)
kelsa_call_tool(tool_name="add_note", arguments={
    "lead_id": lead_id,
    "text": "@[Prakash Singh](NNN) — RD required on this proposal ASAP..."})
```

Both are async — poll `get_draft_status` to confirm. The @mention note is the only follower mechanism; there is no standalone add-follower tool.

## DRA PO-WO Issuing pipeline (ID 537)

### When to use
NDR says "create a purchase order / work order", "add this to PO pipeline", or "issue PO/WO" for a vendor. This creates a record in the DRA PO-WO Issuing pipeline that tracks approval, budget linkage, and issuance.

### Pipeline architecture
- **Pipeline name:** DRA PO-WO Issuing
- **Pipeline ID:** 537 (DRA account ID: 5)
- **6 stages:** PO-WO Created → HoD Approved → Chairman Approved → Signed & Issued → Cancelled [retired] → Rejected [retired]
- **Key master-linked pipelines:**
  - DRA Companies Master (ID 4475) — `cf_company_name1`
  - DRA Project Budgets (ID 2033) — `cf_company_name_budget`, `cf_project_new` (Budget Sub Head)
  - DRA Vendor Shortlisting (ID 531) — `cf_vendor1`

### Pre-checks before creating

Before creating the PO/WO record, gather these from Kelsa:

1. **Vendor** — search `pipeline_id: 531` for the vendor name. Get its `lead_id`. If not found, create it first.
2. **Company** — search `pipeline_id: 4475` for the entity name (e.g. "DRA Thindlu Land Partners"). Get its `lead_id`.
3. **Budget** — search `pipeline_id: 2033` for `"<Project> <Category> <BudgetHead>"` pattern to find the right budget item. e.g. "Ranka Udaya Marketing Execution" → find Matching project + category + head. Get its `lead_id`.
4. **Users** — use `list_users(pipeline_id: 537)` to find assignee and @mention IDs.

### CRITICAL GOTCHA — Budget Sub Head is a master link, NOT text

From the pipeline fields:
- `cf_project_new` (Budget Sub Head) is a **master field** → `dra_project_budgets`
- `cf_company_name_budget` is a **master field** → `dra_project_budgets`

These **must** be passed as `{"id": budget_lead_id}` — passing a text string like `"Miscellaneous"` causes `Validation failed: Invalid master value`. Always search the Project Budgets pipeline first and pass the lead ID.

However, `cf_project_new1` (Project name like "Ranka Udaya") accepts a plain text string — it's not a master field.

### Required fields at PO-WO Created stage

From the pipeline prerequisites (list them with `get_pipeline(pipeline_id: 537)`):

| Field ID | Type | Description |
|---|---|---|
| `cf_po_type` | dropdown | "One Time PO" (precedent from old records) |
| `cf_company_name1` | master → 4475 | Company entity lead `{"id": company_id}` |
| `cf_vendor1` | master → 531 | Vendor lead `{"id": vendor_id}` |
| `cf_why_vendor` | text | Justification for selecting this vendor |
| `cf_jobs` | dropdown | e.g. "supply of Container office" |
| `cf_special_instruction___notes` | text | **REQUIRED** — detailed PO clauses |
| `cf_due_date` | date | Based on delivery timeline |
| `cf_total_value_of_order__without_tax_` | number | Quote amount (no ₹/commas) |
| `cf_total_tax` | number | GST amount |
| `cf_advance_to_be_paid` | number | Advance amount |
| `cf_narration` | text | Brief description of order |
| `cf_nature_of_order` | dropdown | "Turnkey" (precedent) |

Optional but useful: `cf_quote_provided` (attachment), `cf_status` ("Active"), `cf_company_name_budget` (master → budgets), `cf_project_new1` (text), `cf_category` (text), `cf_budget_head` (text), `cf_project_new` (master → budgets).

### Creating a PO/WO record

```python
# Step 1: Upload the quote PDF first
result = kelsa_call_tool(
    tool_name="get_upload_url",
    arguments={
        "pipeline_id": 537,
        "file_name": "quote.pdf",
        "content_type": "application/pdf"
    }
)
# extract upload_url, fields from result
# POST file to S3 with multipart/form-data (see file upload section)
# register_upload...

# Step 2: Create the PO/WO
kelsa_call_tool(
    tool_name="create_lead",
    arguments={
        "pipeline_id": 537,
        "name": "Vendor Name - Description - Project",
        "field_values": {
            "cf_po_type": "One Time PO",
            "cf_company_name1": {"id": company_lead_id},
            "cf_vendor1": {"id": vendor_lead_id},
            "cf_why_vendor": "Prior work satisfactory, competitive rate",
            "cf_jobs": "supply of Container office",
            "cf_special_instruction___notes": "**TIME IS OF THE ESSENCE** — detailed clauses here...",
            "cf_due_date": "2026-08-10",
            "cf_total_value_of_order__without_tax_": 442000,
            "cf_total_tax": 79560,
            "cf_advance_to_be_paid": 221000,
            "cf_narration": "Brief description of what's being ordered",
            "cf_nature_of_order": "Turnkey",
            "cf_status": "Active",
            "cf_company_name_budget": {"id": budget_lead_id},
            "cf_project_new1": "Ranka Udaya",  # text field
            "cf_category": "Marketing",
            "cf_budget_head": "Execution",
            "cf_project_new": {"id": budget_lead_id},  # MASTER field — pass lead ID
            "cf_quote_provided": {"url": "...", "upload_id": 123, "name": "quote.pdf"},
            # Total Amount = Value + Tax
            "cf_total_amount": 521560,
        }
    }
)
```

### Step 3: Poll draft status

```python
kelsa_call_tool(tool_name="get_draft_status", arguments={"draft_id": draft_id})
# Fix validation errors if any, then re-create
```

### Step 4: Update assignee and notes

```python
# Find user IDs
kelsa_call_tool(tool_name="list_users", arguments={"pipeline_id": 537})

# Change assignee to Anbarasan (Anbu)
kelsa_call_tool(tool_name="update_lead", arguments={
    "lead_id": lead_id,
    "assignee_id": "682"  # from list_users output
})

# Add comprehensive note with @mention
kelsa_call_tool(tool_name="add_note", arguments={
    "lead_id": lead_id,
    "text": "@[Anbarasan](682) — Full instructions with clauses..."
})
```

### PO/WO comprehensive clause checklist

When the user wants a PO/WO covering all bases for a container office (or similar relocatable asset), include these sections in `cf_special_instruction___notes` and the note:

1. **Time is of the essence** — delivery period, delay penalty (₹X/day)
2. **Scope of work** — detailed description of deliverables, materials, finishes
3. **Reference image compliance** — must match reference image 100%
4. **Quality & inspection** — factory inspection mandatory before dispatch; balance payment only after approval
5. **What's included in vendor scope** — detailed list pushing maximum vendor responsibility
6. **Re-transportation** — bolted connections (not welded), lifting hooks rated for relocation, vendor to confirm shiftable without breakage/repair, re-transport support when shifting project sites
7. **Freight & handling** — transport terms (extra/actual, loading vs unloading scope split)
8. **Warranty & maintenance coverage** — specifically WHAT IS COVERED and WHAT IS NOT COVERED
9. **Payment terms** — advance %, balance %, GST, transport
10. **Coordination** — who does what (e.g. Kantesh issues PO/WO, Gauri for interiors)

### Reviewing an issued PO/WO + posting scope-clarification comments

Recurring ask (2026-08-12, PO-WO #759): NDR says "I need a comment on this PO asking Anbu…" or "examine the attached purchase order with Annexure A / full BOQ". The PO attachment usually lives **in Kelsa, not in Telegram** — when no file arrived in chat, don't ask for it. Recover it:

1. **session_search first** — search past sessions for the PO context ("underground services work order Anbu") to get pipeline + lead ID.
2. **get_lead(pipeline 537)** for the record (narration, vendor, total, stage) and **list_lead_attachments** for the issued PO document — returns a pre-signed S3 URL; `curl -sL -o /tmp/po.pdf <url>` downloads it. Signed URLs expire (~7 days) — download promptly.
3. **Issued PO PDFs are scans.** `pdftotext` returns ~0 bytes → render with `pdftoppm -png -r 150 po.pdf pg`, OCR with `tesseract pg-N.png stdout --psm 4 -l eng` (vision_analyze may have no provider configured; tesseract is the reliable path). BOQ tables with qty/rate columns OCR poorly at 150 DPI — re-render BOQ pages at 300 DPI and re-OCR to nail quantities (e.g. A2.1 600mm dia 39 RMT @ 600 = ₹23,400).
4. **Post the comment via add_note** on the PO lead. NDR's preferred comment format for engineer scope-confirmation: plain English, numbered checklist, one item per line, "included? yes/no", and end with "if any of the above is NOT covered, tell me exactly what needs to be added." @mention the engineer (Anbu = Anbarasan, id 682) so they're notified.
5. **Deliver the plain-English scope explanation** (NDR wants layman's terms + gap analysis, not a recital): state the contract type up front (e.g. "labour-only — DRA supplies all materials + excavation; vendor supplies labour/tools/PPE"), the total value incl. GST, then the systems covered (stormwater, sewerage, water supply, irrigation, electrical conduit), then **explicitly what is NOT covered** — that is the part he cares about.

**Recurring scope gaps in DRA plotted-development infra BOQs** (check every time):
- **Acres extent is never stated** — BOQs quantify in RMT/Nos, not acres. Ask the engineer how many acres the work covers.
- **Electrical "underground services" often means conduit only** — BOQ says "DWC HDPE conduit + GI fish wire **for future cable pulling**" → actual cable laying, feeder-pillar boxes, transformer yard, streetlights are OUTSIDE the WO. Flag this explicitly.
- **STP connection line** — sewerage goes to manholes; whether the line continues into the STP is usually unstated → confirm.
- **RWH (rainwater harvesting) pits** are often absent even when stormwater catch basins are included.
- Sump/OHT/pump house, water meters, STP construction are separate scopes not in a pipe-laying BOQ.

## Updating proof fields on an existing invoice

After an invoice is created and is in the approval flow, you may need to add drone photos, site images, or quality proof. The proof fields are:

- `cf_upload_prove_of_completion_of_work` (Proof of completion) — attachment field
- `cf_proof_of_quality` (Proof of quality) — attachment field

**Flow (same as initial upload):**

```python
# 1. Get upload URL
result = kelsa_call_tool(tool_name="get_upload_url", arguments={
    "pipeline_id": 516,
    "file_name": "DJI_0084.JPG",
    "content_type": "image/jpeg"
})

# 2. POST file bytes to S3 (see file upload flow section)
# Use Python requests with multipart/form-data, or curl -F

# 3. Register the upload
registration = kelsa_call_tool(tool_name="register_upload", arguments={
    "pipeline_id": 516,
    "file_url": file_url_from_step_1,
    "file_name": "DJI_0084.JPG"
})
# Returns {"url": "...", "upload_id": N, "name": "DJI_0084.JPG"}

# 4. Update the lead's proof field
kelsa_call_tool(tool_name="update_lead", arguments={
    "lead_id": lead_id,
    "field_values": {
        "cf_upload_prove_of_completion_of_work": {"url": "...", "upload_id": N, "name": "file.jpg"},
        "cf_proof_of_quality": {"url": "...", "upload_id": N, "name": "file.jpg"}
    }
})
```

The `update_lead` call is async — poll with `get_draft_status` to confirm.

**Proof field quirks:**
- `cf_upload_prove_of_completion_of_work` (Proof of completion) accepts a **plain URL object** without upload_id. You can directly set a Google Drive folder link: `{"url": "https://drive.google.com/drive/folders/...", "name": "Full Drone Shoot - 43 photos + 57 videos"}`. This renders as a clickable link in Kelsa.
- `cf_proof_of_quality` (Proof of quality) is a **multi-file attachment field**. Pass an array of upload objects: `[{"url": "...", "upload_id": N, "name": "file1.jpg"}, ...]`. Each renders as a separate preview in the UI.
- Neither field is required to use `upload_id` — URLs without S3 upload work fine, especially for Drive-linked content.

**Preferred pattern for drone shoot / site photo proof (confirmed by NDR 2026-07-16):**
- **Proof of completion** → Google Drive folder link to the full shoot
- **Proof of quality** → 2-3 representative sample photos uploaded via S3 (multi-file array)
- **Note** → total file count (e.g. "43 photos + 57 videos — 100 files, ~30 GB")

This avoids uploading 30+ GB through Kelsa's S3 while still providing visual samples in the UI and a link to the comprehensive record.

**Practical approach when you have 30+ files (e.g. full drone shoot):**
1. Download 2-3 representative JPGs from Drive (see Google Drive → Kelsa file transfer below)
2. Upload them to S3 and register (get_upload_url → S3 POST → register_upload)
3. Set proof of quality to the array of upload objects
4. Set proof of completion to the Drive folder URL object `{"url": "...", "name": "Full set label"}`
5. Add a note with total file count and reference

### Google Drive → Kelsa file transfer

When files need to go from Google Drive directly into Kelsa attachment fields:

```python
from tools.gws_auth import build_service
import requests, os

# Step 1: Download from Drive
service = build_service('drive', 'v3', service_name='google-draas')
request = service.files().get_media(fileId=drive_file_id)
with open(local_path, 'wb') as fh:
    fh.write(request.execute())

# Step 2-4: Follow the Kelsa upload flow above (get_upload_url → S3 POST → register_upload → update_lead)
```

For video files (hundreds of MBs to GBs), downloading and re-uploading is impractical — just link the Drive folder in a note instead.

### Pitfall: PO advance_to_be_paid ≠ actual payment made

When checking how much was paid to a vendor:

| Data Source | What it means |
|---|---|
| PO `cf_advance_to_be_paid` | **Planned** advance amount in the PO — what was agreed, NOT what was paid |
| Invoice `cf_advance_recovered` | Advance amount **deducted** from this invoice — ₹0 means no deduction was applied |
| Invoice `cf_outstanding_debits_adjusted` | Any prior debit adjustments |
| Invoice `cf_tds_deduction` | TDS withheld (if applicable) |

**None of these fields alone tell you whether cash actually moved.** The PO advance may have been paid outside Kelsa (via NEFT, cheque, etc.) and never recorded as "recovered" against the invoice. Common patterns:

1. **Advance paid outside Kelsa** → balance = invoice amount - advance (but system shows full invoice as due)
2. **No advance paid** → full invoice amount is genuinely due
3. **Invoice is the advance itself** (50% advance billed as invoice) → description usually says "50% Payment has to be released now and rest after work completion"

**How to handle:**
- Check the invoice's `cf_description` / `cf_description_final` for clues (e.g. "50% advance release")
- Check latest notes on the invoice — someone may have clarified the payment situation
- If ambiguous, flag to the user: "System shows advance_planned=X, advance_recovered=0, invoice_amount=Y. Could not confirm if advance was actually paid. Balance is either ₹Y (if no advance) or ₹(Y-X) (if advance was paid outside Kelsa)."

### Known pitfalls specific to PO-WO Issuing

1. **`cf_project_new` (Budget Sub Head) is a master field**, not a text field. Always pass `{"id": budget_lead_id}`. Passing a string like `"Miscellaneous"` fails with "Invalid master value".
2. **`cf_special_instruction___notes` is required** — don't omit it even for a placeholder. Include the comprehensive clauses here.
3. **Balance budget goes negative** when no budget is allocated for this item. The Marketing>Execution>Miscellaneous budget at Ranka Udaya had ₹0 budget and -₹2,00,000 already used. The PO pushes it further negative. This is informational — the PO still creates but the budget needs allocation.
4. **The S3 upload via curl fails with exit code 26** when the source filename has spaces or commas. Fix: copy the file to `/tmp/simple_name.pdf` first before uploading.
5. **Vendor record may be stale** — if the vendor was created years ago (e.g. 2021), always update the key contact info (`cf_key_contact_name`, `cf_key_contact_mobile`) from the new quote before creating the PO/WO.
6. **Draft processing is async** — after `create_lead`, always poll with `get_draft_status`. On failure, read the error message carefully (it tells you exactly which fields are missing/invalid) and retry the create, not a patch of the failed draft.

## "When the Kelsa MCP is down" — fallback recipe

When you hit Pitfall 20 (integer args rejected), don't abandon the task. Here is the working fallback path used on 2026-07-14 for the Skylark Zenith teaser:

## Vendor payment / work order investigation flow

### When to use
NDR asks you to "check the work order value, check the invoice value, check payment details, what's the balance payment due" for a vendor. Or says "find the invoice for [vendor]", "what's the status of PO/WO #[N]", "is [vendor] in the system."

### Correct priority order: Kelsa FIRST

The user corrected this session (2026-07-16): when asked to investigate vendor payment status, **always start with Kelsa**. Documents found in Google Drive or Gmail may not have been entered into Kelsa at all.

**Wrong (what happened this session):**
1. ❌ Search Google Drive TMP → find a work order document
2. ❌ Present it as the answer → user asks "where did you get it, is it in Kelsa?"
3. ❌ Realize it's a standalone Google Doc that was never entered into Kelsa

**Correct order:**

```
Kelsa (3 pipelines) → Google Drive → Gmail
```

### Step 1 — Search Kelsa PO-WO Issuing (pipeline 537)

Search by vendor name, project name, or PO number:

```python
# By vendor name
kelsa_call_tool(tool_name="search_leads", arguments={
    "pipeline_id": 537,
    "query": "SidPhoto OR sidphoto OR Sid"
})

# By PO-WO number
kelsa_call_tool(tool_name="search_leads", arguments={
    "pipeline_id": 537,
    "query": "742"
})

# By project name
kelsa_call_tool(tool_name="search_leads", arguments={
    "pipeline_id": 537,
    "query": "Serenity"
})
```

If found, call `get_lead` for full details (vendor, amount, advance paid, balance, stage, issued PO document URL).

### Step 2 — Search Kelsa Vendor Shortlisting (pipeline 531)

The vendor must exist here before a PO/WO or invoice can reference it:

```python
kelsa_call_tool(tool_name="search_leads", arguments={
    "pipeline_id": 531,
    "query": "SidPhoto OR sidphoto OR Sid"
})
```

If found, `get_lead` the vendor record to get contact info, onboarding status.

### Step 3 — Search Kelsa Invoice Processing (pipeline 516)

Search for invoices linked to the same vendor or work order:

```python
kelsa_call_tool(tool_name="search_leads", arguments={
    "pipeline_id": 516,
    "query": "SidPhoto OR sidphoto OR 11800"
})
```

Invoice records link back to PO-WO via `cf_po_number1` (master field → pipeline 537).

### Step 4 — If NOT found in Kelsa, check Google Drive

Search Drive for supporting documents that may or may not have been entered into Kelsa:

```python
drive.files().list(q="fullText contains 'SidPhoto' or name contains 'SidPhoto'", ...).execute()
```

Check:
- **TMP folder** — recently drafted documents
- **RnD/Bangalore** — regulatory/legal documents (preferred for this class of content)
- **Project-specific folders** — Ranka Udaya, Serenity Hill View, etc.

### Step 5 — If still not found, check Gmail

Search both work (`google-draas`) and personal (`google-gmail`) accounts for email threads mentioning the vendor or work order:

```python
gmail.users().messages().list(userId='me', q='SidPhoto OR sidphoto OR "Sid Photo"', maxResults=10).execute()
```

Follow up by reading the relevant email thread body and attachments.

### Worked example: SidPhoto drone photography (2026-07-16 session)

NDR asked to check the work order/invoice for SidPhoto drone photography at Ranka Udaya / Serenity Hill View.

**✅ Records DID exist in Kelsa across all 3 pipelines.** The initial "not found" was a search failure:
- **Vendor Shortlisting** (PI 531): `sidphoto.in` as Prospect — found when query was `sidphoto` (lowercase). Not found earlier due to incorrectly scoped search.
- **PO-WO Issuing** (PI 537): PO #743, `Dra realty pvt ltd.-sidphoto.in-743`, ₹11,800 (`Serenity hillview` — lowercase 'h', no space). Initial search used `"Serenity Hill View"` (capital H+V) which didn't match.
- **Invoice Processing** (PI 516): Invoice E080 for ₹11,800, stage `Approved by the Issuer of PO/WO` with proof of completion & quality already uploaded.

The Google Doc in Drive had draft number `DRA/PO-WO/742` but the Kelsa record is **#743** — the draft number on the doc didn't match the system-generated number.

**Lesson:** When a Kelsa search returns nothing, immediately try:
1. All-lowercase vendor name (e.g. `sidphoto` not `SidPhoto`)
2. Partial word matches (e.g. `Serenity` not `Serenity Hill View`)
3. Check if the PO doc number in Drive matches the Kelsa system number (they can differ)
4. Search all 3 pipelines independently, with multiple query variants, before concluding "not found"

### Pitfall: Google Doc does not equal Kelsa record

A document in Google Drive with a PO-WO number like "DRA/PO-WO/742" does NOT mean that work order exists in Kelsa. The number may be a draft reference that was never entered, or it may conflict with a real Kelsa record for a different vendor. Always verify in Kelsa first.

## DRA Petty Cash pipeline (ID 555)

### When to use
NDR sends a receipt / expense image (petty cash, coffee, F&B, travel) and says "file this as a petty cash reimbursement" or "reimburse me for this". Creates a record in the **DRA Petty Cash** pipeline (ID 555, "Cash request").

### Key automations that shape the flow (read from get_pipeline 555)
- **`cf_request_type: Reimbursement` auto-jumps to `Issued & Debited`** on entry (entry_stage_jump filter), and skips the "Submit Details" data-entry task (create_task_skip_prerequisite1 filter). So a reimbursement lands straight past Requested→Approved→Issued.
- **`created_by:Nishant Ranka` auto-approves** (entry_skip_prerequisite3 on Approved) AND auto-fills `cf_total_approved_expense = cf_amount_requested` (entry_update_formula). So NDR's reimbursements are approved instantly at the full amount.
- **Reimbursement assignee → Roshini Ranka (id 11652)** when `cf_fromcompany: DRA Realty Pvt Ltd` (create_task_set_assignee1 on Approved).

Net effect (observed 2026-08-19): a reimbursement created by NDR for DRA Realty ends at **"Expense Details Submitted"** assignee **Roshini Ranka** immediately after create_lead — no manual stage moves needed.

### Required fields at creation
`cf_request_type` (dropdown: Reimbursement | Cash request), `cf_fromcompany` (master → Companies Master 4475, pass `{"id": <company_lead_id>}`), `cf_amount_requested` (number, no ₹/commas), `cf_cash_needed_for` (text), `cf_narration` (text), optional `cf_account_to_be_debited` (dropdown, e.g. "DRA Realty Pvt Ltd"), `cf_other_expense_tags` (dropdown, e.g. "business development"), `cf_date`, attachment `cf_receipts___vouchers`.

`cf_user1` is read-only autofilled to the creator. The Petty Cash ID (`cf_petty_cash_id1`) auto-formats as `<date>_<name>` (e.g. `2026-08-07_Nishant Ranka`) — you don't set it.

### Full flow
1. **Crop the receipt image & convert to PDF** (PIL: autocontrast + contrast boost, save as PDF). Naming convention: `YYYYMMDD_<Venue>_<Category>_<amount>.pdf` (e.g. `20260807_MaverickFarmerCoffee_FnB_599.pdf`).
2. **Upload + register the receipt**: `get_upload_url(pipeline_id=555, file_name, content_type="application/pdf")` → POST to S3 (curl `-F "file=@/tmp/<simple_name>.pdf;type=application/pdf"`) → `register_upload` → returns value object `{url, upload_id, size, name}`.
3. **`create_lead(pipeline_id=555, name="<date>_<name>", field_values={...})`** with `cf_receipts___vouchers` = the register_upload object, `cf_fromcompany` = master object, plus the text/number/dropdown fields above.
4. Poll `get_draft_status` — for NDR reimbursement to DRA Realty the record self-routes to Expense Details Submitted / Roshini.
5. Report the Kelsa link.

### Pitfall — S3 content-type on PDF upload
The presigned URL signs `Content-Type`. If curl guesses the type wrong it 403s — append the explicit type: `-F "file=@/tmp/x.pdf;type=application/pdf"`. (Same rule as the general S3 upload pitfall in this skill; xlsx/non-PDF are the usual offenders, but be consistent.)

### Worked example (2026-08-19)
Maverick & Farmer Coffee, Cunningham Rd receipt ₹599 → `20260807_MaverickFarmerCoffee_FnB_599.pdf`, DRA Realty Pvt Ltd (company lead 2562312), tag "business development", narration "Reimbursement to Nishant Ranka - Coffee for landowners…". Created → **#54778550**, stage Expense Details Submitted, assignee Roshini Ranka, Amount Approved ₹599 (auto). <https://kelsa.io/555/leads?current_item_id=54778550>

## DRA Invoice Processing pipeline (ID 516)

### When to use
NDR sends an invoice/receipt (fuel bill, vendor invoice, expense) and says "post this to Kelsa" or "put this through the invoice pipeline." This creates a record in the DRA Invoice Processing pipeline for tracking, approval, and payment/reimbursement.

### Pipeline architecture
- **Pipeline name:** DRA Invoice Processing
- **Pipeline ID:** 516 (DRA account ID: 5)
- **8 stages:** Invoice received → Approved by PO/WO Issuer → Approved by Chairman → Invoice paid. Retired stages: Already Paid, Invoice Rejected, Retired, Duplicates.
- **Key master-linked pipelines:**
  - DRA Companies Master (ID 4475) — `cf_invoiced_to_the_company1`
  - DRA Vendor Shortlisting (ID 531) — `cf_vendor_n`
  - DRA PO-WO Issuing (ID 537) — `cf_po_number1`

### Critical prerequisite: Vendor must exist FIRST
Before creating an invoice, the vendor must already exist in **DRA Vendor Shortlisting** (pipeline ID 531). Steps:

1. **Search for the vendor:**
```python
kelsa_call_tool(tool_name="search_leads", arguments={"pipeline_id": 531, "query": "vendor name"})
```
2. **If not found, create it FIRST:**
```python
kelsa_call_tool(tool_name="create_lead", arguments={
    "pipeline_id": 531,
    "name": "Vendor Name",
    "field_values": {"cf_company_name": "Vendor Name"}
})
# Note lead_id from result
```
3. **Then reference the vendor in invoice creation:**
```python
"cf_vendor_n": {"id": vendor_lead_id}
```

### File upload flow (same as land proposals)
Attachments for `cf_upload_invoice` use the same 3-step flow:
1. `get_upload_url(pipeline_id=516, file_name, content_type)` → returns S3 fields + file_url
2. POST the file bytes to S3 as multipart/form-data (use curl or Python requests)
3. `register_upload(pipeline_id=516, file_url, file_name)` → returns attachment value object

### Creating the invoice record
```python
kelsa_call_tool(tool_name="create_lead", arguments={
    "pipeline_id": 516,
    "name": "Short description (e.g. 'HP Fuel - Innova - 15 Jul 2026')",
    "field_values": {
        "cf_description": "Full description",
        "cf_invoiced_to_the_company1": {"id": company_lead_id},  # from Companies Master
        "cf_vendor_n": {"id": vendor_lead_id},                    # from Vendor Shortlisting
        "cf_invoice_number": "G4145",
        "cf_invoice_date": "2026-07-15",
        "cf_amount": 3999.80,                                      # numeric, no ₹ or commas
        "cf_upload_invoice": attachment_value_from_register_upload,
        "cf_narration": "Already paid on NDR Kotak CC. Reimbursement due from DRA Realty."  # optional but recommended
    }
})
```
Always poll with `get_draft_status` after creation — processing is async and may fail (e.g. missing required fields).

### When invoice is already paid (reimbursement scenario)
NDR often pays company expenses on his Kotak credit card and needs reimbursement from DRA Realty. In this case:

1. Create the record at "Invoice received" stage with all available info
2. Add a note:
```python
kelsa_call_tool(tool_name="add_note", arguments={
    "lead_id": lead_id,
    "text": "ALREADY PAID on NDR Kotak Credit Card on [date]. Reimbursement of Rs. X due from DRA Realty Pvt Ltd to NDR. No PO/WO required."
})
```
3. Update the narration field:
```python
kelsa_call_tool(tool_name="update_lead", arguments={
    "lead_id": lead_id,
    "field_values": {"cf_narration": "Already paid on NDR Kotak CC..."}
})
```
4. The record stays at "Invoice received" for accounting team review — they have an "Already Paid" retired stage to move it to.

### Post-creation: Task reassignment & follower management

After an invoice is created, it may have a pending task (e.g. "Issuer of PO-WO to verify all details of the invoice and work done or material delivered and then approve invoice for payment"). The user may ask you to reassign this task to a specific person.

**The task's assignee follows the lead's assignee.** There is no separate "update task" tool — changing the lead's assignee via `update_lead` also updates the task's assignee:

```python
# Step 1: Find the user's Kelsa ID
kelsa_call_tool(tool_name="list_users", arguments={"pipeline_id": 516})
# -> Anbarasan <pm2.blr@draas.com> — id=682

# Step 2: Change the lead (and therefore task) assignee
kelsa_call_tool(tool_name="update_lead", arguments={
    "lead_id": lead_id,
    "assignee_id": "682"   # user ID as string from list_users
})
# Returns draft ID — poll with get_draft_status to confirm

# Step 3: Add as follower via @mention note
# add_note with @mention adds the user as a follower AND notifies them
kelsa_call_tool(tool_name="add_note", arguments={
    "lead_id": lead_id,
    "text": "@[Anbarasan](682) — Invoice [number] for [vendor] ([amount]) assigned for verification and approval. Please review all details and process."
})
```

**Key points:**
- `assignee_id` takes the user ID as a **string** (e.g. `"682"`), not an integer
- `add_note` with `@[Name](id)` syntax adds the user as a follower automatically — no separate "add follower" tool needed
- Both operations are async — poll `get_draft_status` to confirm before reporting completion
- Works across all pipelines (Invoice Processing 516, PO-WO Issuing 537, Land Proposal 519)

### Known pitfalls specific to Invoice Processing
1. **Vendor must exist before creating invoice.** `create_lead` will fail with "Required fields not present: Vendor Name" if cf_vendor_n is missing or references a non-existent vendor.
2. **PO Number (`cf_po_number1`) is technically required** in the pipeline prerequisites but for routine expenses (fuel, toll, small purchases) there is no PO. Create the invoice without it — the accounts team handles the gap.
3. **`cf_amount_accepted` validation fails** if you set it to the same value as `cf_amount`. Only set `cf_amount_accepted` when the accepted amount differs from the invoice amount.
4. **Draft processing is async** but typically completes within seconds. Always poll with `get_draft_status` after create/update operations.
5. **DRA Companies Master** lookup: search for the company name to find its lead_id. DRA Realty Pvt Ltd = lead_id 2562312 (confirmed).

### Chairman approval flow (pipeline 516) — the move IS the approval

When NDR says "approve the PO/invoice on my behalf" for an invoice already at **"Approved by the Issuer of PO/WO"**:

1. **`list_lead_tasks`** to find the pending **"Review & Approve"** task (assigned to `Nishant ahfl`, due ~5 days out).
2. **Attempt `complete_task(task_id, note_text="Approved by Nishant Ranka (chairman) ...")`. It can fail with `Kelsa tool call failed: Internal error`** (observed 2026-08-17, twice in a row). Do NOT retry-loop — the failure is on the server side.
3. **The working path is `move_stage(stage_id="st_approved__by_chairman")`** — note the double underscore `st_approved__by_chairman`. The target stage has a data_entry prerequisite ("Verify Correctness of Hard Copy Invoice") whose fields are REQUIRED at move time; the first bare move fails with `Validation failed: Required fields not present: Is Invoice Format Correct, Previous Invoices Checked, Previous debits checked`. Pass them in the same call:
   ```python
   kelsa_call_tool(tool_name="move_stage", arguments={
       "pipeline_id": 516,
       "lead_id": lead_id,
       "stage_id": "st_approved__by_chairman",
       "field_values": {
           "cf_is_invoice_format_correct": True,
           "cf_previous_invoices_checked1": True,
           "cf_previous_amount_debited": 0,   # Outstanding Debits — ₹0 unless flagged
       }
   })
   ```
4. **The stage move itself IS the chairman's approval** — the event log shows "Nishant Ranka — stage: Stage changed to Approved by chairman". The Review & Approve task disappears from the pending list. Record auto-assigns to **Accounts - DRA** for hard-copy verification + accounting entry → payment.
5. The invoice also carries auto-approval dates (`cf_date_for_auto_approval`, `cf_date_for_auto_progress`) — e.g. "Date For Auto Approval: 2026-08-19T09:00:00+05:30" means it would auto-approve even without the manual move. Report these as the SLA.

**Finding an invoice from a garbled voice-note vendor name:** NDR's voice transcripts mangle vendor names ("ad lab's kelsa in voice" → **I Am Here Software Labs Pvt Ltd** — "lab" fragment + "in voice" = in-voice). Search pipeline 516 by fragments: `query="lab"` (returns 700+; sort by created_at desc) or `query="Software Labs"` — the invoice record NAME embeds vendor + company + invoice number, so vendor-name fragments surface the right record. When the user says "in voice" / "invoice" ambiguously, check the **DRA Invoice Processing** pipeline, not Sales Leads (10) or Land Proposal (519).
 They will share something like `https://kelsa.io/519/leads?current_view=list&current_item_id=53692993&page=1&account_id=5&filter_id=10644&sort=created_at&order=desc`. Extract `current_item_id` (the lead ID) and `account_id`.

## DRA PO-WO Issuing pipeline (ID 537)

### When to use
NDR or a team member asks to create a Purchase Order or Work Order for a vendor's quote — e.g. "add this PO to Kelsa", "create a PO/WO for this quote", "register the purchase order in the PO/WO pipeline." This covers container offices, construction materials, services, and any other procured item.

### Pipeline architecture
- **Pipeline name:** DRA PO-WO Issuing
- **Pipeline ID:** 537 (DRA account ID: 5)
- **6 stages:** PO-WO Created → HoD Approved → Chairman Approved → Signed & Issued. Retired: Cancelled, Rejected.
- **Key master-linked pipelines:**
  - DRA Companies Master (ID 4475) — `cf_company_name1`
  - DRA Vendor Shortlisting (ID 531) — `cf_vendor1`
  - DRA Project Budgets (ID 2033) — `cf_company_name_budget`, `cf_project_new1`, `cf_category`, `cf_budget_head`, `cf_project_new`, `cf_balance_budget`

### Critical prerequisite: Vendor + Company must exist FIRST
Before creating a PO/WO, both the vendor and company must already exist in their respective pipelines:
1. **Search for the vendor** in Vendor Shortlisting (pipeline 531)
2. **Search for the company** in Companies Master (pipeline 4475)
3. **If vendor not found**, create it first in Vendor Shortlisting
4. **If company not found**, create it first in Companies Master

### Detailed reference file
See **`references/dra-po-wo-issuing-pipeline.md`** for the complete field structure, field identifiers, prerequisite requirements by stage, automation rules, creation workflow with code examples, known pitfalls, and common patterns including:
- Full field mapping for PO/WO creation
- S3 upload flow for quote attachment
- Adding notes with @mentions
- Changing assignee
- Updating Special Instructions with full PO clauses

   1. **`kelsa.io/s/<slug>` CAN be resolved via curl.** Run `curl -s -L "https://kelsa.io/s/<slug>" -w "%{url_effective}"` — the redirect target contains `current_item_id=<lead_id>`. This works even when the browser is offline. Only fall through to asking the user to paste the full URL if curl also fails.
2. **Ask the user to paste the image URLs** from the lead page (right-click each → "Copy image address") OR screenshot the lead and run vision_analyze to OCR the URLs.
3. **Build the deliverable against the user-pasted URLs** — never block on a working MCP for "just to verify the S3 URL works."
4. **If the task itself is creating a teaser / proposal from Kelsa data, draft it against voice-note facts + user-pasted URLs.** The teaser is a derivative work; the source-of-truth lead content can be re-verified by the human reader.
5. **Do not promise to retry the MCP later in the same session** — if the bug is server-side, retries within the same session will all fail. Suggest the user run `hermes tools` to reload, or open an MCP-server ticket, but only as a side note, not as the plan.
