# Batch Note Addition — Utility/Follow-up Messages

Add a standardized note to hundreds of existing Pipeline 10 leads in bulk, based on a Google Sheet with name + phone columns.

## Trigger

User shares a Google Sheet URL with "~250 leads" containing columns `Lead | Contact` (name + phone with country code). All leads already exist in Pipeline 10. User wants a standard note added to every lead.

**Variant — uploaded Excel file:** User uploads a `.xlsx` file via Telegram (e.g. from a bot campaign export). The file has columns like `lead_name`, `lead_contact` (phone), `chat_summary`, and other campaign metadata. Read it with `openpyxl` instead of Google Sheets.

## Key Rule

**Do NOT modify the user's sheet.** Work only with Kelsa. The user explicitly said: "you are not doing any tracking any changes in that DRA tracker sheet."

## Workflow

### Step 1: Read sheet

**For Google Sheets:**
```python
import sys, json
sys.path.insert(0, '/opt/hermes')
from tools.gws_skill_bridge import call

output = call('sheets_get', service_name='google-draas', 
              spreadsheet_id='<sheet_id>', range='A:B')
rows = json.loads(output)

leads = []
for i, r in enumerate(rows):
    if i == 0: continue  # skip header
    if len(r) >= 2 and r[1].strip():
        name = r[0].strip() if r[0].strip() else 'Unknown'
        phone = r[1].strip().replace('+', '').replace(' ', '').replace('-', '')
        leads.append({'name': name, 'phone': phone, 'row': i+1})
```

**For uploaded Excel file (`.xlsx` via Telegram):**
```python
import openpyxl
wb = openpyxl.load_workbook("/data/hermes/document_cache/<filename>.xlsx")
ws = wb.active

leads = []
for row in ws.iter_rows(min_row=2, max_row=ws.max_row, values_only=True):
    name, phone, summary = row[col_name_idx], row[col_phone_idx], row[col_summary_idx]
    leads.append({
        "name": str(name).strip() if name else "",
        "phone": str(phone).strip().replace('+', '').replace(' ', '') if phone else "",
        "chat_summary": str(summary).strip() if summary else None
    })
```

Phone numbers come with `91` prefix (e.g. `919066784784`). Strip `+`, spaces, hyphens.

### Step 2: Save leads to temp file for background processing

```python
import json
with open('/tmp/leads_to_note.json', 'w') as f:
    json.dump(leads, f)
```

### Step 3: Write processing script

Create `/tmp/add_notes_to_leads.py` that:
1. Loads leads from `/tmp/leads_to_note.json`
2. Gets Kelsa MCP token via `tools.kelsa_auth.get_valid_access_token("7449813913")`
3. For each lead:
   - `search_leads(pipeline_id=10, query="<phone>")` via POST to `https://kelsa.io/mcp`
   - If phone with `91` prefix fails, try without prefix and vice versa
   - Extract lead ID from response (#\d+)
   - `add_note(lead_id=int(id), note="<note_text>")` via same MCP endpoint
4. Rate-limit: 0.3s delay between calls, brief pause between batches of 25
5. Track: found_and_noted, not_found, failed list

### Step 4: Run

**Option A — Directly from execute_code (preferred, Jul 2026):**

The `execute_code` tool has access to the GWS vault socket when you set it explicitly. This avoids subprocess overhead:

```python
import sys, os, json, re, time
sys.path.insert(0, '/opt/hermes')
os.environ['GWS_VAULT_SOCKET'] = '/run/gws-vault/vault.sock'

from tools.kelsa_auth import get_valid_access_token
token = get_valid_access_token("7449813913")

# ... processing loop with httpx POST to kelsa.io/mcp ...
```

The vault socket (`/run/gws-vault/vault.sock`) is only available inside the `execute_code` sandbox child process — **not** from `terminal()` subprocesses. Running MCP calls directly from `execute_code` is the simplest and most reliable approach.

**Option B — Background terminal process (fallback):**

```python
terminal(command="python3 /tmp/add_notes_to_leads.py", 
         background=True, notify_on_complete=True, timeout=600)
```

The subprocess approach needs the token passed in or re-fetched inside the script. Use this when the processing will take >5 minutes (execute_code has a 5-min timeout).

### Step 5: Report results

Present a clean summary:
- Total leads processed
- ✅ Found & Noted count
- ❌ Not found in Pipeline 10 count
- ⚠️ Failed list (first 5-10)

## ⚠️ Critical Pitfall — Parameter Name Is `text`, Not `note`

The Kelsa MCP `add_note` tool expects the parameter `text`, NOT `note`. Using `note` returns `isError: true` with "Missing required arguments: text" — but the HTTP status is 200, so it looks like success.

```python
# ✅ CORRECT
add_note(lead_id=int(id), text=note_text)

# ❌ WRONG — silent failure
add_note(lead_id=int(id), note=note_text)
```

**Always check `result.isError`** in the MCP response when calling via direct HTTP:

```python
data = resp.json()
if data.get("result", {}).get("isError", False):
    err = data["result"]["content"][0]["text"]
    # handle failure
```

The MCP SDK (`session.call_tool`) handles error checking automatically. This pitfall only applies to **raw HTTP POST** calls to `https://kelsa.io/mcp`.

## Note Content Pattern

**Standard utility message:** The user provides the exact message text they sent. Format the note as:

```
Follow-up utility message sent via WhatsApp: "<message_text>" - Company Name
```

**Outreach campaign tracking:** After sending a campaign message (e.g. site visit invitation) to Warm/SSV leads via wa.me links, add a note to each lead recording the action:

```
Site Visit WhatsApp message sent to client via 919900029200 on 23-Jul-2026.
```

The Kelsa note timestamp auto-captures date/time — do not insert a manual timestamp.

**Bot conversation summary (from campaign exports):** When the lead comes from a WhatsApp bot campaign (e.g. Healla Talk) and the Excel file has a `chat_summary` column, add two notes per lead:

1. **Note 1 — Welcome message:** `"Marketing message / Welcome note sent to customer via WhatsApp campaign (<campaign_name>)."`
2. **Note 2 — Bot summary:** `"Bot conversation summary: <chat_summary content from the file>"`

If `chat_summary` is null in the file, use a generic fallback: `"Bot conversation initiated via <campaign> campaign; lead responded to initial outreach."`

## Common Variations

**Phone search fallback:** Try `91` + 10-digit first. If not found, try just the 10 digits. Some leads stored without country code prefix.

**Rate limits:** MCP API handles ~2 calls/second fine. Use `time.sleep(0.3)` between iterations. For 250 leads (500 calls total), expect ~10-15 min runtime.

**Ghost contacts:** `search_leads` returns "0 result(s)" for ghosted contacts even though the phone UID is taken in Kelsa. Report these as "not found."

## Key IDs

| Item | Value |
|------|-------|
| Pipeline ID | 10 (DRA Sales Leads) |
| MCP URL | `https://kelsa.io/mcp` |
| search_leads response | `#<lead_id>` extracted via regex |
| add_note parameter | `lead_id` (int), `text` (str) — NOT `note` |
| Kelsa auth | `tools.kelsa_auth.get_valid_access_token("7449813913")` |
