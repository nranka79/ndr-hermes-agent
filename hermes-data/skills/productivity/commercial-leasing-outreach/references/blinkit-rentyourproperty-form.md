# Blinkit — Rent Your Property Form (Drupal Webform)

**URL**: https://blinkit.com/rentyourproperty  
**Platform**: Drupal 8 webform (Cloudflare-protected)  
**Form ID**: `webform_submission_new_rent_property_paragraph_1528_add_form`

## Form Fields (as of Jul 2026)

### Required Fields

| Field Name | Type | Options / Notes |
|---|---|---|
| `you_are_a` | Select | `Landowner`, `Property Consultant`, `Broker` |
| `name` | Text | Max 255 chars |
| `email` | Email | Max 254 chars |
| `phone` | Text | Pattern: `^([\d() +-]+)$` |
| `locality` | Text | Max 255 chars |
| `pincode` | Text | Max 255 chars |
| `city_select` | Select (Select2) | 2000+ Indian cities. Value is lowercase slug: `bengaluru`, `delhi`, `mumbai`, etc. |
| `state` | Text | Max 255 chars |
| `property_carpet_area` | Select | `< 500 sqft`, `500-1000`, `1000-1500`, `1500-2000`, `2000-2500`, `2500-3000`, `3000-3500`, `3500-4000`, `4000-4500`, `4500-5000`, `5000-6000`, `6000-7000`, `7000-8000`, `> 8000 sqft` |
| `property_preference` | Select | `Commercial`, `Residential`, `Empty land / bare shell` |
| `google_location` | Text | "lat-long or gmaps link" — Google Maps URL or coordinates |

### Optional Fields

| Field Name | Type | Notes |
|---|---|---|
| `expected_rent` | Text | Monthly rent expectation |

### Conditional Fields (shown when `property_preference = "Commercial"`)

| Field Name | Type | Options |
|---|---|---|
| `do_you_have_a_property_tax_receipt_ptr_` | Select | `Yes`, `No` |
| `do_you_have_a_commercial_electricity_meter` | Select | `Yes`, `no` |

### File Upload

| Field Name | Notes |
|---|---|
| `files[property_photos]` | Image file, 2 MB limit, accepted: gif/jpg/png/jpeg |

### Hidden / System Fields

| Field Name | Notes |
|---|---|
| `form_build_id` | Must be fetched fresh from GET response |
| `form_id` | Always `webform_submission_new_rent_property_paragraph_1528_add_form` |
| `op` | Always `Submit` |

## Submission Flow

```python
session = requests.Session()
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ..."}

# 1. GET form page
resp = session.get("https://blinkit.com/rentyourproperty", headers=headers)
fb_match = re.search(r'name="form_build_id" value="([^"]+)"', resp.text)
form_build_id = fb_match.group(1)

# 2. POST with all fields
form_data = {
    "you_are_a": "Landowner",
    "name": "Nishant Ranka",
    "email": "ndr@draas.com",
    "phone": "+91 9880055634",
    "locality": "Gandhinagar, 3rd Cross, 4th Main Road",
    "pincode": "560009",
    "city_select": "bengaluru",
    "state": "Karnataka",
    "property_carpet_area": "3000 to 3500 sqft",
    "property_preference": "Commercial",
    "expected_rent": "",
    "google_location": "https://maps.app.goo.gl/SgJZ9JT75GBFWhta6",
    "do_you_have_a_property_tax_receipt_ptr_": "Yes",
    "do_you_have_a_commercial_electricity_meter": "Yes",
    "form_build_id": form_build_id,
    "form_id": "webform_submission_new_rent_property_paragraph_1528_add_form",
    "op": "Submit",
}

resp2 = session.post(url, data=form_data, headers=headers)
```

## Success Confirmation

The success response stays on the same URL but contains a Drupal status message:

```html
<div role="alert" class="...messages messages--status...">
  Status message
  Thanks for your application
  Someone from our team will be in touch soon.
</div>
```

Search `resp2.text` for `"Thanks for your application"` to confirm.

## Pitfalls

- Always extract `form_build_id` from a **fresh GET** — it changes per session and expires.
- The City select (`city_select`) uses Select2 and has 2000+ options. The value is the lowercase slug — `bengaluru`, not `Bengaluru` or `Bangalore`.
- Setting `property_preference = "Commercial"` makes two extra fields required. If you leave them empty, the form re-renders with validation errors and no visible error message — you must check for the re-rendered form vs success message.
- The form does NOT redirect on success. Check for the Drupal status message div to distinguish success from validation failure.
- Cloudflare blocks requests without a real browser User-Agent. Always use a recent Chrome UA string.
