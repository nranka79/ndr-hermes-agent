# DRA Land Proposal — Worked Example: Pattandur Agrahara, Whitefield

**Date:** 17 Jul 2026
**Record:** [Pattandur Agrahara - 2.32 Acres Commercial Land Opp Shell, Whitefield - via Lakshmikanth](https://kelsa.io/519/leads?current_item_id=53814737)
**Pipeline:** DRA Land Proposal (ID: 519) under DRA Account (ID: 5)

## Source

- **Broker:** Lakshmikanth (Broker Necia) — via WhatsApp
- **Channel:** WhatsApp forward to Nishant, then forwarded to Hermes

## Raw Broker Data

```
Whitefield
2.32 acres Commercial converted land
BBMP limits A khata
Rs.20,000/- per sqft slightly negotiable
Best suitable for HIGH RISE APARTMENTS
Crystal clear titles
Location: Opp Shell, Whitefield (near Hope Farm)
```

## Data Extracted from Survey Documents

### From Topographical Survey Map (Matrix Surveys, 10/08/2024)

| Field | Value |
|-------|-------|
| Survey No | 41 |
| Village | Pattandur Agrahara Village |
| Hobli | KR Puram Hobli |
| Taluk | Bangalore East Taluk |
| District | Bangalore (East) |
| Road frontage | Whitefield Main Road (North side) |
| Adjacent (East) | Survey No. 40 |
| Adjacent (West) | Remaining portion of Sy No. 41 & Private property |
| Adjacent (South) | Sy No. 42 & Govt Kharab Land |
| On-site features | Borewell (BW), compound walls (0.26m–0.47m width), trees/bushes |

### From Area Statement

| Unit | Value |
|------|-------|
| Sq. Meters | 11,401.2681 |
| Sq. Feet | 1,22,722.109 |
| Acres | 2 |
| Guntas | 32.69 |

### Price Calculation

- Rate: ₹20,000/sqft
- Total outright: 1,22,722 sqft × ₹20,000 = **~₹245.44 Cr**

## S3 Attachment Upload Flow

Three files uploaded via the Kelsa presigned S3 POST flow:

| File | Local path | Field | Size |
|------|-----------|-------|------|
| Topographical Survey Map | `/data/hermes/image_cache/img_7b4219599498.jpg` | `cf_land_sketch` (Land Sketch) | 133 KB |
| Area Statement | `/data/hermes/image_cache/img_557cbeeea75a.jpg` | `cf_revenue_maps_and_documents` (Revenue Maps And Documents) | 58 KB |
| Land Photo (field view) | `/data/hermes/image_cache/img_10cca81ce348.jpg` | `cf_land_pics` (Land pics) | 288 KB |

Each followed the same flow:
1. `get_upload_url(pipeline_id=519, file_name="...", content_type="image/jpeg")`
2. `curl -s -o /dev/null -w '%{http_code}' https://kelsa-clients-production.s3.ap-south-1.amazonaws.com -F key=... -F ... -F 'file=@<local_path>'` → HTTP 201
3. `register_upload(pipeline_id=519, file_url=..., file_name=..., size=...)` → returns `{url, upload_id, size, name}`
4. `update_lead(lead_id=..., field_values={"cf_land_sketch": {url, upload_id, size, name}})` for single-file fields, or `[value]` for multi-file

**Key: S3 POST requires HTTP 201.** If the upload gets 204 or 400, check the form fields match exactly (especially `success_action_status: 201` and the `file` field coming last in the multipart data).

## Record Creation Sequence

### Step 1: Create with minimal required fields

```python
create_lead(
    pipeline_id=519,
    name="Pattandur Agrahara - 2.32 Acres Commercial Land Opp Shell, Whitefield - via Lakshmikanth",
    field_values={
        "cf_city": "Bangalore",
        "cf_date_of_proposal": "2026-07-17",
        "cf_land_size_sqft": 122722,
        "cf_land_size_uom": "Acres",
        "cf_name": "Pattandur Agrahara - 2.32 Acres Commercial Land Opp Shell, Whitefield - via Lakshmikanth",
        "cf_offer_type": "Outright",
        "cf_proposal_source": "Lakshmikanth Broker Necia",
        "cf_proposal_source_details_notes": "Via WhatsApp from Lakshmikanth Broker Necia",
    }
)
```

Note: Do NOT include `cf_additional_team_member` in create_lead — it causes Internal Error. Set assignee separately.

### Step 2: Update with all remaining fields

```python
update_lead(
    lead_id=53814737,
    field_values={
        "cf_district": "Bangalore (East)",
        "cf_expected_rate_per_sqft": 20000,
        "cf_expected_total_outright_cost_of_land": 2454442180,
        "cf_hobli": "KR Puram Hobli",
        "cf_land_location": "Opposite Shell Petrol Bunk, Whitefield Main Road, near Hope Farm, Pattandur Agrahara, Bangalore",
        "cf_land_notes": "Topographical survey by Matrix Surveys dated 10/08/2024. Survey No. 41, Pattandur Agrahara Village, KR Puram Hobli, Bangalore East Taluk. Road frontage on Whitefield Main Road. Borewell on site.",
        "cf_land_size_acres": 2,
        "cf_land_size_guntas": 32.69,
        "cf_land_size_sqmt": 11401,
        "cf_land_zone": "Commercial",
        "cf_location_google_maplink": "https://maps.app.goo.gl/fcEwjVnVDDkFpXDB9?g_st=aw",
        "cf_other_details": "Commercial converted land. BBMP limits. A khata. Crystal clear titles. Suitable for high-rise apartments.",
        "cf_product_type": "Apartment - High Rise (>G+8)",
        "cf_sy_nos": "41",
        "cf_taluk": "Bangalore East Taluk",
        "cf_village": "Pattandur Agrahara Village",
    }
)
```

Then upload attachments in a subsequent update call.

### Step 3: Set assignee and notify

```python
update_lead(lead_id=53814737, assignee_id="36564")  # Prakash Singh
```

```python
add_note(lead_id=53814737, text="Hi @[Prakash Singh](36564), this new land proposal has been entered and assigned to you for initial review.\n\nKey highlights:\n📍 Pattandur Agrahara, Opp Shell, Whitefield Main Road\n📐 2 Acres 32.69 Guntas (1,22,722 sqft)\n💰 ₹20,000/sqft outright (~₹245.44 Cr total)\n🏗️ Commercial converted land with A khata\n📋 Survey No. 41, KR Puram Hobli, Bangalore East Taluk\n🔗 Maps: ...\n📎 Survey map, area statement & land photo attached")
```

## Quirks & Pitfalls Encountered

1. **`cf_additional_team_member` user field causes Internal Error on both `create_lead` and `update_lead`** when passed as `36564` (int), `"36564"` (string), or `{"id": 36564}` (object). Workaround: set via `assignee_id` parameter of `update_lead` instead.

2. **Numeric fields (`cf_land_size_guntas`, `cf_land_size_sqmt`, `cf_land_size_base`, `cf_land_size`) may not persist** on update — the draft completes but the field stays at default (0). These appear to be cosmetic/display fields. The primary sqft field (`cf_land_size_sqft`) persisted correctly.

3. **`cf_proposal_source` accepts free text** despite the pipeline definition listing it as "dropdown (88 options)". Check by looking at existing leads before assuming it's a dropdown.

4. **Auto-assign automation** exists on the Proposed stage (`set_assignee on entry → 36564 [filter: cf_additional_team_member?]`) but since the user field can't be set, the automation never fires. Manual assign is the reliable path.

5. **Google Maps links from Android share** include trailing `?g_st=aw` — include the full URL as provided. It renders fine in Kelsa's attachment/link field.

6. **S3 upload verification will 403** — do not re-upload because a curl against the returned S3 URL returns 403. This is expected (Kelsa proxies attachment access). Verify by checking the HTML output in `get_lead` which renders `<img>` tags with signed URLs that work in the Kelsa web UI.

## Adjacent Leads (Cross-reference)

- [2 Acres of Land Near Prestige White Meadows Apartment Pattandur Agrahara Village](https://kelsa.io/519/leads?current_item_id=37730706) — Sy No. 42, opposite Prestige White Meadows. Same village, adjacent survey number. Useful context for land consolidation or comparable pricing.
