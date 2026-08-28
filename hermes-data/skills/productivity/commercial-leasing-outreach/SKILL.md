---
name: commercial-leasing-outreach
description: "End-to-end email outreach campaigns for commercial property leasing — target identification, Gmail outreach, response monitoring, web-form submission, and lead-sheet tracking."
version: 1.0.0
author: DRAAS
tags: [outreach, email-campaign, property-leasing, quick-commerce, leads, google-sheets, gmail]
---

# Commercial Leasing — Email Outreach Campaign

## Trigger Conditions

Load this skill when the user asks to:
- Run an email campaign for a property
- Check responses to a property outreach blast
- Submit a property to a quick-commerce / warehouse platform form
- Update a lead tracking sheet with outreach results

## Workflow

### 1. Identify the Campaign

Search Gmail (`ndr@draas.com`) for sent emails matching the property name and timeframe:

```
query = "Gandhinagar after:2026/07/14"
```

Use `tools.gws_skill_bridge.call("gmail_search", service_name="google-draas", query=...)` 

The response returns both **sent** and **received** messages in the thread. Identify:
- Outgoing message → confirms which companies were targeted
- Incoming replies → responses needing action

### 2. Process Responses

Classify each response:

| Signal | Action |
|--------|--------|
| Positive with URL/form link | Open the URL and submit the property details |
| Positive — interested | Note contact info, forward to team |
| Negative — "no requirement now" | Log as "details noted for future" |
| Auto-reply / ticket confirmation | Track the ticket ID |
| No response | Log as "awaiting response" |

### 3. Submit Property Forms (Quick Commerce / Warehouse Platforms)

Many platforms (Blinkit, Zepto, etc.) use Cloudflare-protected Drupal webforms.

**Blinkit rentyourproperty form** (https://blinkit.com/rentyourproperty):

```
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ..."}
```

Steps:
- GET the form page via `requests.Session()` to get cookies
- Extract `form_build_id` from hidden input via regex
- POST with all required fields:
  - `you_are_a`: "Landowner"
  - `name`, `email`, `phone`, `locality`, `pincode`, `city_select`, `state`
  - `property_carpet_area`: match to available range options
  - `property_preference`: "Commercial" or "Empty land / bare shell"
  - `google_location`: Google Maps link
- **Conditional fields**: selecting "Commercial" for `property_preference` triggers extra required fields (`property_tax_receipt`, `commercial_electricity_meter`) — these must also be submitted
- On success, the page shows: "Thanks for your application. Someone from our team will be in touch soon."

### 4. Update Lead Tracking Sheet

Find the relevant sheet via Drive search:

```python
drive.files().list(q="(name contains 'lead' or name contains 'campaign' or name contains 'tracking') and mimeType='application/vnd.google-apps.spreadsheet'")
```

**Dark Store Outreach Database** schema (columns A-M):
- `#` | Company | Category | Contact Name | Designation | Twitter | LinkedIn | Email/Phone | Address | Dark Stores Scale | Priority | Best Outreach Channel | Suggested Message

Add a **Notes column (N)** at `Outreach Status & Notes` if one doesn't exist:

```python
sheets.spreadsheets().values().update(
    range="N1:N1", valueInputOption="USER_ENTERED",
    body={"values": [["Outreach Status & Notes"]]}
)
```

Log each outreach row with:
- 📧 Email sent + date
- Contact email used
- Response received (or pending)
- Any action taken (form submitted, ticket ID, etc.)
- Use emoji prefixes: ✅ success, ❌ negative, 📧 sent, 📋 auto-reply

Update contact info (column H) if the actual email used differs from what's listed.

## Properties Reference

### Gandhinagar Mamatha Apartments (Dark Store / Warehouse)
- **Address**: No. 14, Mamatha Apartments, 3rd Cross, 4th Main Road, Gandhinagar, Bengaluru – 560009
- **Google Maps**: https://maps.app.goo.gl/SgJZ9JT75GBFWhta6
- **Coordinates**: 12.977716°N, 77.577864°E
- **Area**: ~5,200–7,200 sq.ft. (basement ~3,200 sq.ft. Block A&B + ground floor ~2,000 sq.ft.)
- **Nearby**: 500m from Majestic Bus Stand, central Bangalore

## Pitfalls

- **Cloudflare blocking**: The Blinkit `/rentyourproperty` page blocks curl without a proper browser User-Agent. Always set `User-Agent: Mozilla/5.0 (...) Chrome/...` and use a session to maintain cookies.
- **Drupal form_build_id**: This token changes per request. Always GET the form first to extract the fresh `form_build_id` before POST.
- **Conditional form fields**: Some platforms use Drupal states API — fields are hidden+not-required until a specific dropdown value is selected. Selecting "Commercial" for property_preference reveals Property Tax Receipt and Commercial Electricity Meter fields. Submit these too or the form validates them as required.
- **Sheet structure varies**: Always read the sheet first to determine existing columns and row data before appending or updating. Don't assume column positions.
- **Notes column may not exist**: Many lead sheets only have columns A-M. Add column N header first.
- **Quick-commerce platform URLs change**: Platform URLs (like https://blinkit.com/rentyourproperty) may redirect or change. Verify the URL works and the form loads before writing submission logic.
