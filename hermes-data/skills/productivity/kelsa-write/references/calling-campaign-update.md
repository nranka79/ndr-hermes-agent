# Calling Campaign Result Update (Bulk Lead Stage Update)

A recurring DRAAS workflow: after a telecalling team completes calling a batch of leads, the results need to be bulk-updated in Kelsa Pipeline 10 (DRA Sales Leads).

## Trigger

Bharat shares an Excel export of leads from Kelsa (via Teams/SharePoint link or uploaded file) saying the calling team has processed the leads and the stages need updating.

## Source: Excel File from Teams/SharePoint

Bharat's files often come as **Microsoft Teams/SharePoint links** (not local uploads). When you can't find the `.xlsx` on the filesystem:

1. Ask Bharat to **share the link again** or **upload directly to Telegram**
2. If a SharePoint link is provided, download via terminal (SharePoint/Teams links are typically direct file download URLs)
3. If no link is available and the file isn't in `/mnt/uploads/`, ask for a direct upload

## Prerequisites

- Kelsa MCP access (`kelsa_list_tools` / `kelsa_call_tool`)
- Pipeline 10 (DRA Sales Leads) — stage IDs: Cold → Warm (**2**) → PSC (**281**) → SSV (**6**) → Hot → Converted, Dead/Junk/Lost (retired)
- The calling team typically only processes the **first N leads** (e.g. first 196) — respect this constraint

## File Format: CSV from Kelsa (not always .xlsx)

The export Bharat provides may arrive as a **CSV file** (via Telegram attachment), not always as `.xlsx`. The CSV encoding may contain non-UTF8 bytes (e.g. `\xa0` = non-breaking space in remarks text) — read with `encoding='latin-1'` or `encoding='cp1252'` in those cases.

Expected columns:
- **S.no** — sequential row number
- **Client Name** / **Client Phone** / **Client Email**
- **Channel** / **Source** / **Source Detail** / **Project**
- **Assigned To** / **Assigned Date**
- **Call Status** — `Answered`, `Not Answered` (or `0` for blank/empty)
- **Lead Stage** — `Unqualified`, `Incoming`, `Prospect`, `Opportunity` (Kelsa lead stage, not call outcome)
- **SV Status** — `0` (not set), `Not Scheduled`, `Confirmed`, `Tentative`, `Scheduled`
- **Remarks** — free-text notes from the calling team

⚠️ The decision tree uses **THREE separate columns**, not a single call-outcome field. Always read all three.

## Decision Tree for Each Lead

| Call Status | Lead Stage (Kelsa) | SV Status | Target Action | Target Stage | Notes |
|---|---|---|---|---|---|---|
| Answered | Unqualified | any | Mark as Junk | **Junk** (retired) | Add note, then mark as Junk via Kelsa UI (move_stage can't reach retired stages) |
| Answered | Prospect | 0 / Not Scheduled / blank | Promote to Warm | **Warm** (2) | Requires `cf_requirements` — fill from remarks or generic text |
| Answered | Prospect | Confirmed | Promote to PSC | **PSC** (281) | Cold→Warm→PSC sequential (2 moves) |
| Answered | Prospect | Tentative / Scheduled | Promote to SSV | **SSV** (6) | Cold→Warm→PSC→SSV (3 moves); need `cf_interested_in_site_visit_=True` |
| Answered | Opportunity | 0 / Not Scheduled / blank | Promote to Warm | **Warm** (2) | Requires `cf_requirements` |
| Answered | Opportunity | Confirmed | Promote to PSC | **PSC** (281) | Cold→Warm→PSC (2 moves) |
| Answered | Opportunity | Tentative / Scheduled | Promote to SSV | **SSV** (6) | Cold→Warm→PSC→SSV (3 moves); need `cf_interested_in_site_visit_=True` |
| Answered | Incoming | any | Keep current stage | **Keep** | Just add note with outcome |
| Not Answered | Incoming | any | Keep current stage | **Keep** | Add note: "Attempt by Chennai team - Not Answered" |
| 0 / blank | 0 / blank | any | Skip | **Skip** | No data — may be duplicate or invalid row |

**⚠️ SSV prerequisite:** `move_stage` to SSV (stage 6) requires `cf_interested_in_site_visit_ = True`. Set it via `update_lead` first, then move.

**⚠️ Pipeline 10 is sequential:** From Cold → only Warm (2) is allowed. From Warm → only PSC (281). From PSC → only SSV (6). No jumps. If a lead was already at Warm and qualifies for PSC, move it to PSC first.

**⚠️ Stage moves are async:** Each `move_stage` returns a draft ID. Verify with `get_draft_status` before issuing the next move in a chain.

## Workflow Steps

### 1. Read the Excel File

```python
# Use openpyxl to read the export (check /opt/data/.venv-docx/bin/python3 or install openpyxl via uv)
# Expected columns: S No, Client Name, Phone, Source, Status (call outcome), Remarks
import openpyxl
wb = openpyxl.load_workbook(file_path)
ws = wb.active
headers = [ws.cell(1, c).value for c in range(1, ws.max_column + 1)]
```

### 2. Only Process the First N Rows

```python
LIMIT = 196  # Bharat specifies how many were actually called
leads = []
for row_num in range(2, min(LIMIT + 2, ws.max_row + 1)):
    name = ws.cell(row_num, 2).value  # col B = Client Name
    phone = ws.cell(row_num, 3).value  # col C = Phone
    source = ws.cell(row_num, 6).value  # col F = Source
    call_status = ws.cell(row_num, X).value  # identify the call outcome column
    leads.append({"name": name, "phone": phone, "source": source, "call_status": call_status, "row": row_num})
```

### 3. Match Each Lead to Kelsa Pipeline 10

Search by 10-digit phone:
```python
# Bare 10-digit phone search DOES match via IDEN identifier line
result = kelsa_call_tool("search_leads", {"pipeline_id": 10, "query": phone_10_digits})
# Also verify against contacts pipeline 3429 for authoritative dedup
```

### 4. Apply the Decision Tree (3-Column Logic)

For each matched lead, classify using (Call Status, Lead Stage, SV Status):

```python
cs = row['Call Status']  # Answered / Not Answered / 0
ls = row['Lead Stage']   # Prospect / Opportunity / Unqualified / Incoming
sv = row['SV Status']    # 0 / Confirmed / Tentative / Scheduled

if cs == 'Not Answered':
    # Keep current stage — just add note
    add_note(lead_id, "Attempt by Chennai team - Not Answered")

elif cs == 'Answered':
    if ls == 'Unqualified':
        # Mark as Junk (note only — Junk is retired, can't move_stage)
        add_note(lead_id, "Attempt by Chennai team - Answered - Unqualified - Junk")

    elif ls == 'Prospect':
        if sv in ('Confirmed',):
            # Cold→Warm→PSC (need cf_requirements for Warm)
            update_lead(lead_id, {"cf_requirements": "Customer interested, confirmed site visit (no date)"})
            move_stage(lead_id, 2)  # Warm
            # then warm→PSC
            update_lead(lead_id, {"cf_interested_in_site_visit_": True})
            move_stage(lead_id, 281)  # PSC
            add_note(lead_id, "Attempt by Chennai team - Answered - Prospect - confirmed site visit (date not given)")
        elif sv in ('Tentative', 'Scheduled'):
            # Cold→Warm→PSC→SSV (3 moves)
            update_lead(lead_id, {"cf_requirements": "Customer interested, tentative site visit date given"})
            move_stage(lead_id, 2)  # Warm
            update_lead(lead_id, {"cf_interested_in_site_visit_": True})
            move_stage(lead_id, 281)  # PSC
            move_stage(lead_id, 6)  # SSV
            add_note(lead_id, "Attempt by Chennai team - Answered - Prospect - tentative site visit date given")
        else:
            # Promote to Warm
            update_lead(lead_id, {"cf_requirements": "Customer enquired about Ranka Udaya plots"})
            move_stage(lead_id, 2)  # Warm
            add_note(lead_id, "Attempt by Chennai team - Answered - Prospect")

    elif ls == 'Opportunity':
        # Same SV logic as Prospect — see decision tree table
        ...

    elif ls == 'Incoming':
        add_note(lead_id, "Attempt by Chennai team - Answered")
```

⚠️ **Stage moves are all async** — each `move_stage` returns a draft ID. Verify with `get_draft_status` before the next move in a chain. Otherwise the second move may fail because the lead hasn't reached Warm yet.

### 5. Carry Forward Existing Remarks

Before updating, read existing notes:
```python
notes = kelsa_call_tool("list_lead_notes", {"pipeline_id": 10, "lead_id": lead_id})
# Include existing remarks when adding the new note
existing_remark = extract_latest_remark(notes)
if existing_remark:
    new_text = f"{new_text}\nPrevious remarks: {existing_remark}"
```

## Pitfalls

- **Teams/SharePoint links expire** — if the download URL doesn't work, ask for a fresh direct upload
- **Only process the first N rows** Bharat specifies — don't assume the entire file was processed
- **Stage moves are sequential in Pipeline 10** — from Cold only Warm, from Warm only PSC, from PSC only SSV
- **Warm requires `cf_requirements` field** — every move_stage to Warm will fail validation if `cf_requirements` is empty. Fill it from the remarks column or with a generic statement about the customer enquiry. Rejected errors say "Required fields not present: Requirements"
- **SSV requires `cf_interested_in_site_visit_ = True`** — set this before moving to SSV
- **Move chains need draft verification between steps** — moving Cold→Warm→PSC→SSV needs `get_draft_status` after each move. If you chain moves without waiting, the second rejects because the record hasn't reached the intermediate stage yet.
- **CSV encoding: non-UTF8 bytes (`\\xa0`) in remarks** — read with `encoding='latin-1'` or `encoding='cp1252'`
- **Already-exported leads may have matching phone numbers** in the IDEN identifier line of Pipeline 10 — use 10-digit phone search as dedup
- **Bharat's own phone (9900029200)** may appear in the export — skip it
- **Kelsa stage moves are async** — each returns a draft ID; verify with `get_draft_status` before proceeding
- **⚠️ "Record is already in stage" is a no-op, not a failure** — when a lead is already at the target stage (e.g. already in Warm), `move_stage` returns an error. This is harmless — the note was already added. The lead was processed by a previous batch. Log it and move on. Verified in batch 2 (Aug 2026): 3 of 13 warm leads were already in Warm.
- **⚠️ Cannot jump backward to an earlier stage** — leads in a later stage (e.g. Opportunity) cannot be moved back to Warm via `move_stage`. The error is: "The record cannot jump to 'Warm' from its current stage. Allowed targets: Hot (hot), PSC (psc)". The note is still added; the stage move is skipped. Verified in batch 2 (Aug 2026): ArunCD (lead #54864650, in Opportunity) could not be moved to Warm. Correct action: add the note and leave the record at its current stage — do NOT try to move it backward.
- **⚠️ Retired stages (Junk, Dead, Lost, Others) are not reachable by `move_stage`** — the Junk stage is retired in Pipeline 10; `move_stage` only accepts active stages (Cold, Warm, PSC, SSV, Hot, Converted). When marking leads as Junk, add the note documenting the call outcome and skip the `move_stage` call. The Kelsa UI is needed to move records to retired stages. Verified in batch 2 (Aug 2026): 3 junk leads — notes added, stage move skipped.
- **⚠️ `kelsa_call_tool` / `kelsa_list_tools` may fail with "No session user context"** — in cron jobs, auto-reset sessions, or when the resolved session identity doesn't hold a Kelsa token, the dedicated MCP tools fail. The fallback is the direct httpx JSON-RPC approach via `terminal()`:
  ```python
  import os, sys, json, httpx
  os.environ['GWS_VAULT_SOCKET'] = '/run/gws-vault/vault.sock'
  sys.path.insert(0, '/opt/hermes')
  from tools.kelsa_auth import get_valid_access_token
  token = get_valid_access_token()  # No args — identity from session env
  headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
  init = {"jsonrpc":"2.0","method":"initialize",
          "params":{"protocolVersion":"2025-03-26","capabilities":{},
                    "clientInfo":{"name":"hermes","version":"1.0"}},"id":1}
  httpx.post("https://kelsa.io/mcp", json=init, headers=headers, timeout=10)
  def mcp_call(name, args=None, id=2):
      payload = {"jsonrpc":"2.0","method":"tools/call",
                 "params":{"name":name,"arguments":args or {}},"id":id}
      resp = httpx.post("https://kelsa.io/mcp", json=payload, headers=headers, timeout=30)
      data = resp.json()
      content = data.get("result", {}).get("content", [])
      return content[0].get("text", "") if content else str(data)
  ```
  See `kelsa-mcp` → `references/kelsa-auth-from-execute-code.md` for the full reference.

- **⚠️ Batch runs over ~100 leads drop MCP connection (verified 2026-08-28, 195-lead run):** `process_batch_json.py` on ~110 leads caused `MCP server 'kelsa-read-pilot' connection lost` and `McpError: Internal error` on `move_stage`. **Proven split strategy:** (1) process notes-only actions (not_answered, note_only, junk) in one batch — 56 leads ran clean. (2) handle stage-move leads (warm, ssv) via direct `kelsa_call_tool` calls. Keep each batch ≤ ~60 leads. Build split JSON files in a small Python script, resume from the last succeeded index on failure.
- **⚠️ Export xlsx may have VLOOKUP formulas pointing at `[1]consolidated File`:** The evaluated values live in a sibling `(Data).csv` in the same document_cache folder. Read with `encoding='latin-1'`. Always check for the companion CSV before concluding the sheet has no call data.
