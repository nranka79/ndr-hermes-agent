# Batch Lead Creation from Google Sheets → Kelsa Pipeline 10

Full workflow for reading a Google Sheet with lead data and adding each row as a Sales Lead in Kelsa Pipeline 10 (DRA Sales Leads). Covers dedup, two-step contact→lead creation, post-creation notes, and error handling.

## Prerequisites

- Sheet accessible via `google-draas` service (`sheets_get` bridge call or direct Sheets API)
- Kelsa MCP token valid for Pipeline 10 and 3429
- Terminal env: `GWS_VAULT_SOCKET=/run/gws-vault/vault.sock HERMES_SESSION_USER_ID=[REDACTED-TID]` (Bharat's sales account)

## Workflow

### Step 1: Read the sheet and identify columns

Typical lead sheet columns (confirmed for Ranka Udaya - Meta sheet, Sheet ID `1yaUwSos6DO56Oni2iiVJ0L26K-rRn7wzYsHKweNxUB0`):

| Col | Content | Kelsa Field |
|-----|---------|-------------|
| A (0) | Date (DD/MM/YYYY) | Added as note after creation (see Step 5) |
| B (1) | Investment range (e.g. "₹ 50 L+") | Max Budget (`cf_max_budget`) — parsed number (see Step 4) |
| C (2) | Visit preference ("This Weekend", "I need more details") | Requirements (`cf_requirements`) |
| D (3) | Full name | `cf_contact.name` in pipeline 3429 |
| E (4) | Phone Number | `cf_contact.phone` — split into country code + number (see Step 4) |
| F (5) | Email | `cf_contact.email` in pipeline 3429 |
| G (6) | City | — (reference only, can add to notes if useful) |
| H (7) | Status | Stage mapping (see Stage Mapping section) |
| I (8) | Remarks | Added as notes after creation (see Step 5) |

### Step 2: Determine source mapping

Check the sheet name/tab to decide the Pipeline 10 source values:

| Sheet Tab Name | Source | SourceDetails | Channel |
|----------------|--------|---------------|---------|
| "Ranka Udaya - Meta" or "I Am Here" | `I Am Here Software Labs` | `Meta` | `DigitalAds` |
| Contains "MagicBricks" | `Magicbricks` | `MB` | `Portals` |
| Contains "Housing" | `Housing` | — | `Portals` |
| Contains "99acres" | `99acres` | — | `Portals` |

**⚠️ Do not guess.** Verify the sheet name. Using the wrong source corrupts marketing attribution.

### Step 3: Parse phone — country code + number split

**⚠️ Kelsa quirk (Jul 2026):** Pipeline 3429's `cf_contact` compound object breaks when `phone` is included — returns "Name can't be blank". Always pass `email` (or placeholder `{phone}@temp.lead`) + `name` in the compound, and `phone` as separate `cf_contact_phone` field.

**Bharat's preference (confirmed Jul 2026):** Phone numbers must be stored with country code and number separate.

- `919900571093` (12 digits starting with `91`) → **Country Code:** `+91`, **Phone:** `9900571093` (last 10 digits)
- `919535580898` (12 digits starting with `91`) → **Country Code:** `+91`, **Phone:** `9535580898`
- For Kelsa contact creation (pipeline 3429), the phone field accepts `91` + 10-digit number with NO `+` prefix: `919900571093`
- For other country codes (rare in this sheet): preserve the full prefix as country code, keep last 10 digits as number

**Edge cases:**
- 10-digit number (e.g. `9900571093`) → Country Code: `+91`, Phone: `9900571093`, Kelsa format: `919900571093`
- Number with `+` prefix (e.g. `+919900571093`) → strip `+`, treat as above
- Number starting with `0` (e.g. `09900571093`) → strip leading `0`, treat as 10-digit
- Non-91 prefixes → preserve as-is in Kelsa format

### Step 4: Column value parsing

**Investment → Max Budget:**
| Sheet Value | Budget (₹) |
|------------|-----------|
| `₹ 50 L+` | 50,00,000 |
| `₹ 70 L+` | 70,00,000 |
| `₹ 1 CR & Above` | 1,00,00,000 |
| *Anything else* | Skip (leave empty) |

**Visit Preference → Requirements:**
Map verbatim from column C (e.g. "This Weekend", "Next Weekend", "I need more details first").

### Stage Mapping (Status → Kelsa Stage)

The 'Status' column H determines the initial stage:

| Sheet Status | Kelsa Stage | Notes |
|-------------|-------------|-------|
| *"Hot"* | **SSV** | Already visited site or confirmed visit date. Fill site visit date from Remarks if available. |
| *"Warm"* | **Warm** | Expressed interest, communicated back and forth, asked for details. |
| *"Cold"* or *(empty)* | **Cold** | Default. Info may have been shared but no response received. |
| *"Dead"* | **Dead** (retired) | Not interested in location/pricing. |

**⚠️ For the Ranka Udaya - Meta sheet specifically:** All 687 rows have empty Status → all default to **Cold** stage. Do not infer stage from Remarks — use Status column as the single source of truth for stage mapping.

### Step 5: Post-creation notes (two mandatory notes)

**Note 1 — Date record:**
Immediately after creating the lead, add a note:
> "Contact received on **{DD/MM/YYYY from column A}**. Uploaded to system on **{today's date}**."

This is required because Kelsa auto-records the creation date (today), but the actual lead came in earlier.

**Note 2 — Remarks (if non-empty):**
If column I (Remarks) has meaningful content (not just "NA" or empty), add it as a second note verbatim. This preserves context like "Client asked to discuss next week" or "Details shared on WhatsApp."

### Step 6: For each row — check duplicate, then create

```python
import os, sys, re, asyncio
os.environ['GWS_VAULT_SOCKET'] = '/run/gws-vault/vault.sock'
sys.path.insert(0, '/opt/hermes')

from tools.kelsa_auth import get_valid_access_token
import httpx
from mcp.client.streamable_http import streamable_http_client
from mcp import ClientSession

def parse_investment(raw: str) -> int | None:
    """Parse investment string like '₹ 50 L+' to integer. Returns None if unparseable."""
    raw_clean = raw.replace('₹', '').replace(',', '').strip()
    if 'CR' in raw_clean or 'Cr' in raw_clean:
        match = re.search(r'([\d.]+)', raw_clean)
        return int(float(match.group(1)) * 10000000) if match else None
    if 'L' in raw_clean:
        match = re.search(r'([\d.]+)', raw_clean)
        return int(float(match.group(1)) * 100000) if match else None
    return None

def parse_phone(raw: str) -> tuple[str, str] | None:
    """Normalize phone to 91XXXXXXXXXX (12 digits no prefix). Returns (normalized, 10digit) or None."""
    clean = raw.strip().replace(' ', '').replace('-', '').replace('+', '')
    if clean.startswith('91') and len(clean) == 12:
        return (clean, clean[-10:])
    elif len(clean) == 10:
        return ('91' + clean, clean)
    elif clean.startswith('0') and len(clean) == 11:
        return ('91' + clean[1:], clean[1:])
    return None

async def process_row(session, row, source, sourcedetails, channel, project,
                      upload_date="22/07/2026"):
    name = row[3].strip() if len(row) > 3 else ''
    phone_parsed = parse_phone(row[4]) if len(row) > 4 else None
    if not phone_parsed or not name:
        return ('FAILED', name, row[4] if len(row) > 4 else '', 'Bad name/phone')
    phone, phone10 = phone_parsed
    email = row[5].strip() if len(row) > 5 else ''
    date_received = row[0].strip() if len(row) > 0 and row[0].strip() else ''
    investment_raw = row[1].strip() if len(row) > 1 and row[1].strip() else ''
    visit_pref = row[2].strip() if len(row) > 2 and row[2].strip() else ''
    status_val = row[7].strip() if len(row) > 7 and row[7].strip() else ''
    remarks = row[8].strip() if len(row) > 8 and row[8].strip() else ''
    
    # STEP 1: Check Pipeline 10 by phone (CRITICAL — prevents duplicates)
    sr = await session.call_tool('search_leads', arguments={
        'pipeline_id': 10, 'query': phone10
    })
    count_m = re.search(r'(\d+) result', sr.content[0].text)
    count = int(count_m.group(1)) if count_m else 0
    if count > 0:
        ids = re.findall(r'\[#(\d+)\]', sr.content[0].text)
        return ('SKIPPED', name, phone, f'Already exists: {", ".join(ids[:2])}')
    
    # STEP 2: Create contact in Pipeline 3429
    contact_fields = {'name': name, 'phone': phone}
    if email:
        contact_fields['email'] = email
    cr = await session.call_tool('create_lead', arguments={
        'pipeline_id': 3429,
        'field_values': {'cf_contact': contact_fields}
    })
    cm = re.search(r'ID: (\d+)', cr.content[0].text)
    if not cm:
        sc = await session.call_tool('search_leads', arguments={
            'pipeline_id': 3429, 'query': phone10
        })
        cm = re.search(r'\[#(\d+)\]', sc.content[0].text)
    contact_id = int(cm.group(1)) if cm else None
    if not contact_id:
        return ('FAILED', name, phone, 'No contact ID')
    
    await asyncio.sleep(1)
    
    # STEP 3: Build pipeline 10 field values
    lead_fields = {
        'cf_contact1': {'id': contact_id},
        'cf_source': source,
        'cf_sourcedetails': sourcedetails,
        'cf_campaign': channel,
        'cf_project': project
    }
    
    # Investment → Max Budget
    budget = parse_investment(investment_raw)
    if budget:
        lead_fields['cf_max_budget'] = budget
    
    # Visit preference → Requirements
    if visit_pref:
        lead_fields['cf_requirements'] = visit_pref
    
    # Create lead in Pipeline 10
    lr = await session.call_tool('create_lead', arguments={
        'pipeline_id': 10,
        'field_values': lead_fields
    })
    lt = lr.content[0].text
    
    # Get actual lead ID
    dm = re.search(r'draft ID: (\d+)', lt)
    draft_id = int(dm.group(1)) if dm else None
    lead_id = None
    if draft_id:
        await asyncio.sleep(2)
        dr = await session.call_tool('get_draft_status', arguments={'draft_id': draft_id})
        lm2 = re.search(r'ID: (\d+)', dr.content[0].text)
        lead_id = int(lm2.group(1)) if lm2 else None
    
    if not lead_id:
        return ('FAILED', name, phone, 'Lead not created')
    
    # STEP 4: Add date-received note
    note_text = f"Contact received on {date_received}. Uploaded to system on {upload_date}."
    await session.call_tool('add_note', arguments={
        'lead_id': lead_id, 'text': note_text
    })
    
    # STEP 5: Add remarks note if meaningful
    if remarks and remarks.lower() not in ('na', 'none', 'no', 'n/a', ''):
        await session.call_tool('add_note', arguments={
            'lead_id': lead_id, 'text': f"Remarks: {remarks}"
        })
    
    lead_url = f'https://kelsa.io/10/leads?current_item_id={lead_id}'
    return ('CREATED', name, phone, lead_url)


async def batch_create(sheet_rows, source='I Am Here Software Labs', 
                       sourcedetails='Meta', channel='DigitalAds', project='Ranka udaya',
                       upload_date="22/07/2026"):
    token = get_valid_access_token('[REDACTED-TID]')
    http_client = httpx.AsyncClient(headers={'Authorization': f'Bearer {token}'})
    
    async with streamable_http_client('https://kelsa.io/mcp', http_client=http_client) as streams:
        read_stream, write_stream, get_session_id = streams
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            
            results = {'CREATED': 0, 'SKIPPED': 0, 'FAILED': 0}
            rows = [r for r in sheet_rows if len(r) > 3 and r[3].strip()]
            
            for i, row in enumerate(rows):
                status, name, phone, detail = await process_row(
                    session, row, source, sourcedetails, channel, project, upload_date
                )
                results[status] = results.get(status, 0) + 1
                icon = {'CREATED': '✅', 'SKIPPED': '⏭️', 'FAILED': '❌'}[status]
                print(f'{icon} {i+1}/{len(rows)} | {name} | {phone} | {detail}')
            
            print(f'\n{"="*60}')
            print(f'Done: ✅ {results.get("CREATED",0)} added | '
                  f'⏭️ {results.get("SKIPPED",0)} skipped | '
                  f'❌ {results.get("FAILED",0)} failed')
```

## Known Failure Modes

### Ghost Contact Record
**Symptom:** `FAILED` — contact phone "uid has already been taken" but existing contact can't be found.
**Cause:** Pipeline 3429 async processor created a phantom record that consumed the phone UID but never materialized.
**Fix:** Kelsa super admin must purge orphaned contacts in Settings → Data. After cleanup, re-run the row individually.

### Phone Number Edge Cases
- Numbers with `+` prefix → strip `+`, then normalize to 12-digit `91XXXXXXXXXX`
- Numbers starting with `0` → replace `0` with `91`
- 10-digit numbers → prepend `91`
- Non-91 country codes → flag for manual review (rare in sheet data)
- Landline numbers with area codes → flag for manual review
- **Bharat's rule:** Always split into country code (+91) + 10-digit number. The Kelsa contact field stores phone as `91XXXXXXXXXX` (no `+` prefix, 12 digits).
- **⚠️ Phone fields with non-numeric text:** Some sheet rows may have descriptive text in the phone column instead of a number (e.g. "interested ," or "not shared"). These will fail at contact creation. Flag for manual review.

### Name Field Issues
- **Unicode/emoji characters:** Names using Unicode bold/italic (e.g. `𝐒𝐇𝐀𝐒𝐇𝐀𝐍𝐊 𝐆𝐀𝐔𝐑`) or circled letters (`🅷🅴🅼🅽🆃`) cause contact creation to fail with "Error creating record: Invalid name." Skip these for manual entry via web UI.
- **Descriptive text in name field:** Names like "Ravi Gupta-whats app me" or "Sumit Guitarist | Acoustic C" contain extra text that may not block creation but should be cleaned. Add a note flagging the extra content.
- **Single-word / very short names:** Names like "Arun", "Santosh", "Vivek", "Kumar" are prone to ghost contact failures — the email or phone UID conflicts with an existing ghost. These need manual resolution via super admin cleanup.

### ⚠️ Kelsa MCP — Single-Connection Limit (Critical)
**Kelsa MCP does NOT support multiple concurrent connections from the same OAuth token.** Attempting to run >1 parallel batch process sharing the same token causes all-but-one to stall with zero output (MCP initializes but blocks at `session.initialize()`). Runs fine sequentially — do NOT attempt parallel processing via `delegate_task` or background terminals.

**Expected throughput (sequential, single connection):**
| Lead Type | Rate | Notes |
|-----------|------|-------|
| Already Exists (dupe check only) | ~2-3/sec | Just one `search_leads` call — very fast |
| New lead (full create flow) | ~0.3-0.6/sec | Create contact + 1s wait + create lead + 2s wait + 2× add_note |
| Mixed batch (typical 2:1 dupes:new) | ~0.8-1.8/sec | Depends on ratio |

**Scale estimates for 661 leads (actual observed):**
| Chunk | Size | New : Dupes : Failed | Time | Rate |
|-------|------|---------------------|------|------|
| First 220 (earlier dates) | 220 | 33 : 155 : 32 | 255s (4.3 min) | 0.86/s |
| Middle 220 | 220 | 62 : 153 : 5 | 398s (6.6 min) | 0.55/s |
| Last 221 (newer dates) | 221 | 103 : 110 : 8 | 587s (9.8 min) | 0.38/s |
| **Total** | **661** | **198 : 418 : 45** | **~1240s (21 min)** | **0.53/s** |

The last chunk is slowest because most leads are new (higher ratio of full-create flows).

### Stage Assignment Pitfall
- Do NOT infer stage from Remarks column content. The Status column is the single source of truth for stage mapping.
- When Status is empty, default to **Cold** — even if Remarks suggest interest. If the sheet admin wanted it Warm, they'd have filled the Status.

## Post-Processing: Update the Sheet (Column J + K)

After processing all leads, **update the source sheet** to record results for traceability. Use the `sheets_update` bridge call:

**Write to columns J and K:**
| Column | Content | Example |
|--------|---------|---------|
| **J** | Status: "Added" / "Already Exists" / "Failed" | Added |
| **K** | Kelsa URL to the lead record | https://app.kelsa.io/5/leads/53950724 |

**Implementation:**
```python
from tools import gws_skill_bridge
import json

# Build [status, url] pairs for every row processed
rows_data = []
for row_num in sorted(results.keys()):
    status, url = results[row_num]
    rows_data.append([status, url])

range_str = f"SheetName!J{min_row}:K{max_row}"
gws_skill_bridge.call("sheets_update",
    service_name="google-draas",
    sheet_id="<sheet_id>",
    range=range_str,
    values=json.dumps(rows_data))
```

The sheet update lets the admin filter by status to see which leads were added, which were duplicates, and which failed.

## Reusable Script

A complete, production-tested script is available at:
**`/data/hermes/scripts/batch_import_leads.py`**

Usage:
```bash
python3 /data/hermes/scripts/batch_import_leads.py <chunk_file.json> <output_results.json>
```

The script handles:
- Reading lead data from a JSON chunk file
- Phone normalization (91XXXXXXXXXX format, no + prefix)
- Duplicate check via Pipeline 10 phone search
- Two-step contact → lead creation (Pipeline 3429 → Pipeline 10)
- Date-received and remarks notes
- Investment parsing (₹50L+, ₹70L+, ₹1 CR)
- Incremental result saves every 10 leads
- Final stats + results output
