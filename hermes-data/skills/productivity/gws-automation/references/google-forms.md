# Google Forms: Field Extraction & Programmatic Submission

## Overview
Google Forms can be inspected and submitted programmatically without a browser. The form definition is embedded in the page as `FB_PUBLIC_LOAD_DATA_` JSON. Submission uses the `/formResponse` endpoint with `entry.XXXXXXXXX` keys.

## Extracting form fields

1. **Fetch the form HTML:**
   ```python
   import urllib.request, re
   req = urllib.request.Request(form_url, headers={'User-Agent': 'Mozilla/5.0'})
   resp = urllib.request.urlopen(req)
   html = resp.read().decode('utf-8')
   ```

2. **Parse FB_PUBLIC_LOAD_DATA_:**
   ```python
   match = re.search(r'FB_PUBLIC_LOAD_DATA_\s*=\s*(\[.*?\]);', html, re.DOTALL)
   data = json.loads(match.group(1))
   items = data[1][1]  # Array of question items
   ```

3. **Question item structure:**
   ```python
   # Each item: [question_id, title, null, type_code, entries, ...]
   # type_code: 0=text, 1=paragraph, 2=multiple_choice, 3=dropdown,
   #            4=checkbox_grid, 5=linear_scale, 7=date, 8=section_header
   # entries[0][0] = entry_id for text/paragraph questions
   
   entry_key = f"entry.{entries[0][0]}"  # e.g. "entry.1447900150"
   ```

4. **Entry keys for prefilling:** The prefill URL format is:
   ```
   https://docs.google.com/forms/d/e/{FORM_ID}/viewform?entry.NNNNNNNNN=value
   ```

## Submitting a form programmatically

1. **Get a fresh fbzx token** (required, expires per session):
   ```python
   fbzx = re.search(r'name="fbzx"[^>]*value="([^"]*)"', html).group(1)
   ```

2. **POST to /formResponse with all required params:**
   ```python
   import urllib.request, urllib.parse
   
   form_url = form_url.replace('/viewform', '/formResponse')
   data = {
       'entry.1447900150': 'Student Name',
       'entry.577507828': 'Class',
       # ... all entry fields ...
       'fvv': '1',
       'partialResponse': 'null',
       'pageHistory': '0',
       'fbzx': fbzx,
       'submissionTimestamp': '-1',
   }
   
   encoded = urllib.parse.urlencode(data)
   req = urllib.request.Request(form_url, data=encoded.encode(), headers={
       'User-Agent': 'Mozilla/5.0',
       'Content-Type': 'application/x-www-form-urlencoded',
   })
   resp = urllib.request.urlopen(req)
   # Status 200 + no error body = success
   ```

## Pitfalls

- **fbzx token changes** per page load — always fetch fresh before submitting
- **Multi-page forms** require `pageHistory=0` for first page; include ALL field entries even if from later pages (single POST for entire form)
- **Required fields** — if a field is required and left blank, submission gets a 400. Check `item[8] == 1` for required flag
- **Hidden fields must be included**: `fvv`, `partialResponse`, `pageHistory`, `fbzx`, `submissionTimestamp`
- **Form URL variations**: `/viewform` is the display page; `/formResponse` is the submit endpoint
- **User-Agent header** required — Google blocks non-browser requests without it
