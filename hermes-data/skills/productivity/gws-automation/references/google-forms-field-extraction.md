# Google Forms — Field Extraction for Autofill

Extract every question, entry key, type, and option from a Google Form by parsing its embedded JSON payload, without needing OAuth or the Forms API.

## Why This Exists

Google Forms do not have a simple REST API for reading question structure. The Forms API requires a GCP project, OAuth scopes, and per-form enabling. But every published Google Form embeds its full structure in a JavaScript variable called `FB_PUBLIC_LOAD_DATA_` — parse this and you get the exact `entry.NNNNNNNNN` keys needed for programmatic form filling (browser autofill extensions, curl submissions, etc.).

## Technique

### Step 1 — Fetch the HTML

```bash
curl -sL "https://docs.google.com/forms/d/e/FORM_ID/viewform" -o /tmp/form.html
```

Where `FORM_ID` is the long ID in the URL (e.g. `1FAIpQLSc_b4_9dE9DSoWyHAzL2I8yQYjNuUJyn2Uomi__WCtM5EB1Eg`).

### Step 2 — Extract the JSON payload

```python
import re, json

with open('/tmp/form.html', 'r', encoding='utf-8') as f:
    html = f.read()

match = re.search(r'FB_PUBLIC_LOAD_DATA_\s*=\s*(\[.*?\]);', html, re.DOTALL)
data = json.loads(match.group(1))  # Top-level array
```

### Step 3 — Parse the question items

The payload structure is:

```
data[0] = null (unused)
data[1][0] = description/header text
data[1][1] = array of question items (each is [id, title, null, type_code, entries, ...])
data[1][2..N] = miscellaneous metadata
```

Each question item has this structure:

```
item = [
    question_id,          # Unique numeric question ID
    title_html,           # HTML string of the question label
    null,
    type_code,            # 0=text, 1=paragraph, 2=multiple_choice, 3=dropdown, etc.
    entries,              # Array of [[entry_id, label_html, has_other_flag], ...]
    null, null, null,
    is_required,          # 1 or 0
    ...
    description,          # [null, "HTML description"]
]
```

**Type codes:**
| Code | Type |
|------|------|
| 0 | Short text |
| 1 | Paragraph text |
| 2 | Multiple choice (radio) |
| 3 | Dropdown |
| 4 | Checkbox grid |
| 5 | Linear scale |
| 7 | Date |
| 8 | Section header (page break) |
| 9 | Time |
| 11 | Image |

### Step 4 — Extract entry keys for pre-fill

```python
items = data[1][1]

for item in items:
    if item is None:
        continue
    
    q_id = item[0]
    q_title = re.sub(r'<[^>]+>', '', str(item[1])) if item[1] else None
    q_type_code = item[3] if len(item) > 3 else None
    
    # Entry ID for form submission
    entry_id = None
    options = []
    
    if len(item) > 4 and item[4]:
        for entry in item[4]:
            if entry and len(entry) > 0:
                e_id = entry[0]
                e_label = re.sub(r'<[^>]+>', '', str(entry[1])) if len(entry) > 1 and entry[1] else None
                e_other = entry[2] if len(entry) > 2 else 0
                
                if e_id and entry_id is None:
                    entry_id = e_id
                
                if e_label:
                    options.append({'id': e_id, 'label': e_label, 'has_other': e_other == 1})
    
    # For text/paragraph, the entry_id is in item[4][0][0]
    if q_type_code in (0, 1) and item[4] and len(item[4]) > 0:
        entry_id = item[4][0][0]
    
    entry_key = f"entry.{entry_id}" if entry_id else None
```

### Step 5 — Pre-fill the form URL

```python
# For text fields — append entry key to URL
prefill_url = f"https://docs.google.com/forms/d/e/{FORM_ID}/viewform?entry.{entry_id}={value}"

# For multiple choice / dropdown — use the option's numeric ID
prefill_url = f"https://docs.google.com/forms/d/e/{FORM_ID}/viewform?entry.{entry_id}={option_id}"
```

## Output Format for Browser Plugins

The extracted data should be structured as JSON so browser autofill extensions can consume it:

```json
{
  "form_url": "https://docs.google.com/forms/d/e/.../viewform",
  "fields": [
    {
      "order": 1,
      "label": "Name of Student:",
      "entry_key": "entry.1447900150",
      "type": "text",
      "suggested_value": "Ruhaan Ranka",
      "known": true,
      "needs_input": false
    }
  ]
}
```

Field properties:
- `entry_key` — the exact URL parameter for form submission
- `type` — field type (text, paragraph, multiple_choice, dropdown, date, etc.)
- `options_list` — for multiple choice / dropdown: array of `{id, label, has_other}`
- `suggested_value` — pre-filled value if known
- `known` — whether the agent could fill this from context
- `needs_input` — whether the user still needs to provide data

## Limitations

- Only works for **published** Google Forms (the form must have a public `viewform` URL accessible without login)
- Cannot detect form validation rules beyond `required` flag
- The `FB_PUBLIC_LOAD_DATA_` variable is minified/obfuscated in some copies — always use regex with `re.DOTALL`
- Some complex form layouts (sections with conditional logic) may have additional nesting not shown here
- Form IDs are specific to each form — there is no generic "find all forms for a user" via this method

## Related

- `references/calendar-events.md` — for Calendar API usage
- `references/gws-from-terminal.md` — for running GWS code via the venv Python path
