---
name: web-form-automation
description: "Programmatic web form filling and submission when browser tools are unavailable."
version: 1.0.0
---

# Web Form Automation

Programmatically fill and submit web forms via curl/Python when the local browser or browser_use_cloud is unavailable, blocked by Cloudflare, or overkill for a simple form.

## When to Use

- User provides a URL and asks you to fill a form on their behalf
- A third-party portal requires property/contact details to be submitted
- A form behind basic Cloudflare protection needs to be submitted programmatically
- You need to automate repeated form submissions

## Workflow

### 1. Probe the URL

```bash
curl -s -L -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" "<url>" | head -50
```

If the form HTML is returned, it's scrapeable. If access-denied, try browser_use_cloud instead.

### 2. Extract form structure

Use Python (requests + regex since bs4 is usually unavailable) to find all select options, required inputs, and hidden fields.

### 3. Manage session

Always use `requests.Session()` to maintain cookies across GET/POST.

### 4. Extract CSRF/anti-forgery tokens

Drupal: `form_build_id`. WordPress: `_wpnonce`. Laravel: `_token`. Look for hidden inputs with names like `token`, `nonce`, `csrf`, `_token`.

### 5. Submit the form

Map property/user details to form field names. POST to the form action URL.

### 6. Verify submission

Check for: "Thank you", "submitted", "received" in response. Look for status message divs. Confirm redirect to a different URL.

## Pitfalls

- **Cloudflare blocks**: Use a realistic browser User-Agent. If still blocked, try browser_use_cloud.
- **CSRF tokens change per request**: Always GET the form first to get a fresh token before POSTing. Stale tokens silently reject.
- **Drupal form_build_id**: This token is per-form-instance. Submitting with a stale one returns the form again with no visible error.
- **Conditional fields**: Some fields only show via JS. Submit them only if their parent condition matches, or leave empty.
- **File upload fields**: Can't be submitted via simple POST. Skip them or tell the user.
- **Form re-render = validation failure**: If POST returns the form page at the same URL, parse the response for error messages ("required", "error", "invalid").
- **Use value attributes, not display text**: Submit `value="bengaluru"` not the visible text "Bengaluru".

## References

- `references/blinkit-rent-property-submission.md` — Full walkthrough of submitting to the Blinkit property portal.
