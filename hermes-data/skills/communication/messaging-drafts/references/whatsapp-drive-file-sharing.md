# WhatsApp Messaging + Drive File Sharing

**Workflow:** When the user asks you to send a WhatsApp message that includes a Drive file (PDF, DWG, image, etc.) — share the file with the recipient and include the link in the message.

## Full Workflow

### 1. Find the file on Drive

Use `drive_search` via `gws_skill_bridge.call()`:

```python
data = call('drive_search', service_name='google-draas', query='keywords', max=15, raw_query=False)
```

The `drive_search` function uses `fullText contains '<query>'` by default when `raw_query=False`.  
**Parameters:** `query` (keywords), `max` (page size), `raw_query` (bool — set to `False` for keyword search, or pass a raw Drive API query string as `query` with `raw_query=True`).

**Critical:** The `SimpleNamespace` created by the bridge requires both `query` AND `raw_query` to be passed, because the skill function reads `args.query if args.raw_query else ...`. If you omit `raw_query`, you get `AttributeError: no attribute 'raw_query'`. Always pass `raw_query=False` for keyword search.

### 2. Check current sharing permissions

Use the Drive API directly via `gws_auth.build_service`:

```python
from tools.gws_auth import build_service
svc = build_service('drive', 'v3', service_name='google-draas')
perms = svc.permissions().list(
    fileId=file_id,
    fields='permissions(id,emailAddress,role,type)'
).execute()
```

Check if the recipient's email already has `role: reader` or `role: writer`. If they do, skip the share step.

### 3. Share the file with the recipient

Use `drive_share` via `gws_skill_bridge.call()`:

```python
result = call('drive_share', service_name='google-draas',
    file_id=file_id,
    email='recipient@example.com',
    role='reader',      # 'reader' = viewer, 'writer' = editor
    type='user',        # 'user' or 'group'
    notify=False        # True to send Drive notification email
)
```

**Parameters required by the skill function:** `file_id`, `email`, `role`, `type`, `notify`.  
All must be passed explicitly — omitting `type` or `notify` causes `AttributeError`.

For viewer access (the minimum needed), use `role='reader'`.  
Set `notify=False` unless the user specifically wants a Google notification email sent.

### 4. Get the recipient's phone and alias

Look up the recipient in the NDR DRAAS contacts sheet via `sheets_get`:

```python
data = call('sheets_get', service_name='google-draas',
    sheet_id='1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g',
    range='NDR DRAAS Google contacts.csv!A:CO'
)
rows = json.loads(data)
# Find the row containing the recipient's name
```

**Name resolution order for addressing:**
1. **Col 82 (Alias)** — e.g. `"anbu, unbhu"` → use `"Anbu"` (trim first alias)
2. **Col 0 (First Name)** — check for nickname in parentheses e.g. `"Vinod Kumar Das (Rahul)"` → use `"Rahul"`
3. Fall back to col 0 as-is

**Phone number:** Check cols 27-38 for phone pairs. Prefer `DRA` or `Work` labeled numbers over `Mobile`.

See `contact-phone-lookup` skill for the full column map and number verification protocol.

### 5. Compose the WhatsApp message

- After the text body, add the file link on its own line: `File: <full Drive URL>`
- The `webViewLink` from `drive_search` or `drive_get` is the correct link to include
- Use `*bold*` for the caption/heading (WhatsApp supports `*asterisks*`)
- Follow the tone rules in `references/whatsapp-text-formatting.md`

### 6. Generate the wa.me link

Use your Python script with `urllib.parse.quote()`:

```python
from urllib.parse import quote
phone = "918150029900"  # digits only, no + or spaces
msg = "*Heading*\n\nBody text with link:\nFile: https://drive.google.com/file/d/.../view"
link = f"https://wa.me/{phone}?text={quote(msg)}"
```

**Phone segment verification:** For Indian numbers, the wa.me segment must be exactly 12 digits (`91` + 10-digit mobile). Strip all spaces from the source number — a space converted to `0` instead of removed will silently produce 13 digits and break the link.

**Message content discipline:** Deliver ONLY what the user requested by voice. Do NOT add helpful extras, precautions, or bonus context the user didn't ask for.

## Real Session Example (Jul 2026)

**User request:** Share "NorthStar Allalasandra Site Digital Survey Drawing.pdf" with Anbu via WhatsApp, ensure viewer access, and ask him to check the survey timing + tape measurement issue.

**Steps taken:**
1. `drive_search` with query `"NorthStar Allalasandra"` → found the PDF (id: `0B1Oc8cSaJXPGenJSakZqTll4SXV5ajNsblhCMlJlY1I3d24w`)
2. `drive_get` to confirm owner (`ndr@draas.com`) and get webViewLink
3. Checked permissions via `permissions().list()` — only `sales1.blr@draas.com` and `ndr@draas.com` had access
4. Shared with `pm2.blr@draas.com` (Anbu's DRA email) as `role='reader'`
5. Looked up Anbu in contacts sheet → Alias `"anbu"` (col 82), phone `918150029900` (DRA Mob, col 28)
6. Composed message about surveying + tape zero check
7. Generated wa.me link with the Drive file URL embedded

## Pitfalls

- **`drive_share` requires all params:** `file_id`, `email`, `role`, `type`, `notify` — missing any causes `AttributeError` from the SimpleNamespace
- **`drive_search` needs both `query` and `raw_query`:** Always pass `raw_query=False` for keyword search; pass a raw Drive API query as `query=` with `raw_query=True`
- **Phone number spaces:** Strip ALL spaces from the number before building the wa.me URL — a space converted to `0` instead of stripped produces a 13-digit segment for Indian numbers (broken link)
- **Hash/pound (#) in message text:** Avoid `#` entirely in WhatsApp messages — even URL-encoded, WhatsApp mobile may fail to pre-fill the message
- **Long message + Drive link = chunk risk:** If the text + URL exceeds ~3,000 chars, use the HTML chunk pattern instead (see `references/whatsapp-chunked-message-html.md`)
