# Sale Deed Feedback → WhatsApp Delivery Workflow

## When user gives clause-by-clause verbal feedback on a sale deed

### Step 1 — Parse & Structure Feedback

The user often gives rapid voice/verbal feedback referencing specific clauses (e.g., "clause 5.3", "clause 11", "clause 10"). Structure it immediately:

```
Clause X.Y — Issue
- User's proposed fix
- Any references to RERA/statutes
- Specific wording suggestions
```

Flag which items the user says are **done/final** vs which need **Drive data filling**.

### Step 2 — Parallel Drive Data Collection

When the user says "fill in all missing data from Drive", **do not search serially**. Spawn parallel `delegate_task` subagents, one per data category:

| Agent | Searches For | Typical Keywords |
|-------|-------------|-----------------|
| Agent 1 | **Occupancy Certificate** | OC number, date, issuing authority, OC, occupancy certificate, BBMP, completion certificate |
| Agent 2 | **Fire Clearance** | Fire NOC, Fire CC, fire clearance, KSFES, fire department |
| Agent 3 | **Structural Stability** | structural stability report, SSR, structural report, stability certificate |
| Agent 4 | **Project Details** | site area, total sqft, plan sanction, commencement certificate, building specs |

Each agent should use `gws_auth.build_service('drive', 'v3')` and search the relevant Drive folders (Ranka Iris folder, Current Properties, etc.). Also search by file name patterns.

### Step 3 — Compile Findings

After all agents return, compile into:

- **✅ Filled** — data successfully found (document ID, value, source)
- **⚠️ Partial** — related docs found but not the exact document
- **❌ Missing** — not on Drive, needs user input

### Step 4 — Decide Delivery Format

Check the total message length:

```python
url = f'https://wa.me/{phone}?text={urllib.parse.quote(msg)}'
if len(url) > 3500:  # Safety margin below 4096 limit
    # → Create HTML with green WhatsApp button
```

### Step 5 — HTML with WhatsApp Button (for long messages)

When a raw wa.me link exceeds ~3500 chars, create an HTML page:

- **Design**: Clean card-based layout with all filled data visible
- **WhatsApp Button**: Large green `#25D366` button with `📤 Send to [Name] on WhatsApp`
- **JavaScript**: Encode the full message, set `document.getElementById('sendBtn').href` dynamically
- **Visual flags**: Green `✅` for filled data, orange `⚠️` for placeholders
- **File**: Save to `/tmp/` and send via `MEDIA:/path/to/file.html`

### Step 6 — Present Summary

Alongside the HTML, give the user a quick table of what was filled vs what still needs their input. No more than 2-3 lines per item.

## Message Style for Legal Feedback

- Use WhatsApp markdown: `*bold*` for section headings, `_italic_` for sub-headings
- Use `•` for bullet items
- Use numbered lists `(i) (ii) (iii)` for items within a point
- End with "Please incorporate the above and revert."
- Include all data references (document IDs, dates, numbers) inline

## User Preferences (Nishant NDR)

- Do NOT leave placeholders without searching Drive first
- If data isn't on Drive, report what WAS found (related docs, consultants named) and what's missing explicitly
- No clarifying questions about "should I search?" — just search
- Rapid topic switching is normal — execute feedback immediately
- Legal contact for Ranka Iris matters: Piyush (+91 98441 23300)
- **When user uploads a PDF during an active sale deed review:** DO NOT ask "what should I do with it?" — immediately OCR/process it (pdftotext, convert to image, tesseract) to identify what document it is, then incorporate findings into the ongoing review. The user uploaded it because it's relevant to the current task.
- **Name corrections:** When user corrects a misheard name (e.g. "pure shit. Run car" = correcting misheard "Piyush"/"Rancairis"), acknowledge briefly and search the corrected terms immediately. Don't ask "could you clarify" — just re-search with the corrected input.
