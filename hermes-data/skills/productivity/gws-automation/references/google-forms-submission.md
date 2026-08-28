# Google Forms — Programmatic Submission

Google Forms can be submitted programmatically via the `/formResponse` endpoint. This is useful for filling medical intake forms, school health forms, surveys, etc. without the browser.

## Endpoint

```
POST https://docs.google.com/forms/d/e/{FORM_ID}/formResponse
```

Where `FORM_ID` is the ID in the viewform URL between `/d/e/` and `/viewform`.

## Required Parameters

### 1. Entry Fields

Each form question is identified by an `entry.XXXXXXXXX` parameter. Extract these from the form's embedded JSON:

```python
import re, json, urllib.request

url = "https://docs.google.com/forms/d/e/{FORM_ID}/viewform"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req)
html = resp.read().decode('utf-8')

match = re.search(r'FB_PUBLIC_LOAD_DATA_\s*=\s*(\[.*?\]);', html, re.DOTALL)
data = json.loads(match.group(1))
items = data[1][1]  # Array of question items

for item in items:
    if item is None:
        continue
    q_id = item[0]
    q_title = re.sub(r'<[^>]+>', '', str(item[1])) if item[1] else None
    q_type = item[3]  # 0=text, 1=paragraph, 2=multiple_choice, etc.
    
    # Entry ID is in item[4][0][0] for text/paragraph
    entry_id = None
    if len(item) > 4 and item[4]:
        entry_id = item[4][0][0]
    
    print(f"entry.{entry_id} = {q_title}")
```

### 2. Hidden / Anti-CSRF Fields

Fetch the form page FIRST to get a fresh `fbzx` token (token expires per session):

```python
fbzx = re.search(r'name="fbzx"[^>]*value="([^"]*)"', html).group(1)
```

Always include these hidden fields in your submission:
- `fvv = 1`
- `partialResponse = null` (or the fbzx value in array format)
- `pageHistory = 0`
- `fbzx = <freshly fetched token>`
- `submissionTimestamp = -1`

## Complete Submission Example

```python
import urllib.request, urllib.parse, re

def submit_google_form(form_id, field_values):
    """
    Submit a Google Form programmatically.
    
    Args:
        form_id: The ID from the form URL (after /d/e/, before /viewform)
        field_values: Dict of {entry_key: value}, e.g. {'entry.1447900150': 'Ruhaan Ranka'}
    
    Returns:
        bool: True if successful (HTTP 200)
    """
    # 1. Get fresh tokens
    view_url = f"https://docs.google.com/forms/d/e/{form_id}/viewform"
    req = urllib.request.Request(view_url, headers={'User-Agent': 'Mozilla/5.0'})
    html = urllib.request.urlopen(req).read().decode('utf-8')
    
    fbzx = re.search(r'name="fbzx"[^>]*value="([^"]*)"', html).group(1)
    
    # 2. Build submission data
    data = dict(field_values)
    data.update({
        'fvv': '1',
        'partialResponse': 'null',
        'pageHistory': '0',
        'fbzx': fbzx,
        'submissionTimestamp': '-1',
    })
    
    # 3. Submit
    encoded = urllib.parse.urlencode(data)
    form_url = f"https://docs.google.com/forms/d/e/{form_id}/formResponse"
    req2 = urllib.request.Request(form_url, data=encoded.encode(), headers={
        'User-Agent': 'Mozilla/5.0',
        'Content-Type': 'application/x-www-form-urlencoded',
    })
    
    try:
        resp = urllib.request.urlopen(req2)
        return resp.status == 200
    except urllib.error.HTTPError:
        return False
```

## Pitfalls

- **fbzx token expires** — Always fetch fresh before each submission. Never reuse from a cached HTML file.
- **Multi-page forms** — Google Forms with sections/pages may require all fields from all pages to be submitted together. Partial submission (page 1 only) will get HTTP 400.
- **Form-level validation** — Some forms have required fields enforced server-side. Missing required fields = HTTP 400.
- **Rate limiting** — Google may rate-limit rapid submissions from the same IP. Add a small delay between bulk submissions.
- **Multiple submissions** — Submitting the same form twice for the same person will create duplicate entries. There's no idempotency key.
- **No confirmation of success** — HTTP 200 means the submission was accepted, but there's no response body to parse. To verify, check the linked response spreadsheet if you have access.
