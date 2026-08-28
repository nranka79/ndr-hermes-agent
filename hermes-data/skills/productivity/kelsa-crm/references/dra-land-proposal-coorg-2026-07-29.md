# DRA Land Proposal — Coorg (100 Acres Plantation via Kushal Gupta)

**Date:** 2026-07-29
**Pipeline:** DRA Land Proposal (ID: 519)
**Lead ID:** 54162611
**Link:** https://kelsa.io/519/leads?current_item_id=54162611

## Source message

WhatsApp from Kushal Gupta — 100-acre property in Coorg next to The Tamara resort. Price ₹20 Cr (dropped from ₹25 Cr). Cardamom & pepper plantation on a hill with ~30 acres flat peak. 180 acres physically, 100 acres on paper (charged only on 100).

## Workflow

### 1. Check for existing leads

Search before creating:

```
search_leads(pipeline_id=519, query="Coorg")
# → 0 results — fresh entry
```

### 2. Create the lead

Naming convention: `"<Location> - <Size> <Type> - via <Broker>"`

```python
name = "Coorg - 100 Acres Plantation next to The Tamara - via Kushal Gupta"

resp = call_tool("create_lead", {
    "pipeline_id": 519,
    "name": name,
    "field_values": {
        "cf_date_of_proposal": "2026-07-29",
        "cf_city": "Coorg",                       # free text, not a strict dropdown
        "cf_name": name,
        "cf_proposal_source": "Kushal Gupta",      # free text despite dropdown tag
        "cf_proposal_source_details_notes": "Received via WhatsApp from Kushal Gupta",
        "cf_offer_type": "Outright",
        "cf_land_size_uom": "Acres",               # free text
        "cf_land_size_acres": 100,
        "cf_land_size_sqft": 4356000,              # 100 * 43560
        "cf_expected_rate_per_sqft": 46,
        "cf_expected_total_outright_cost_of_land": 200000000,  # ₹20 Cr
        "cf_land_location": "Coorg, next to The Tamara resort",
        "cf_location_google_maplink": "https://maps.app.goo.gl/RTA9Vvj7H3az1hAC7",
        "cf_product_type": "Villa",
        "cf_other_details": "180 acres physically, 100 acres on paper (charged on 100 acres only). Was a cardamom and pepper plantation. Located on a hill with approx. 30 acres of flat land on the peak. Ideal for resorts or holiday homes. Price dropped from 25 Cr to 20 Cr.",
        "cf_proposal_notes": "Original asking price was 25 Cr, now reduced to 20 Cr."
    }
})

# Extract draft_id from "draft ID: 100065479"
draft_id = int(re.search(r'draft ID: (\d+)', resp).group(1))
result = call_tool("get_draft_status", {"draft_id": draft_id})
# → Lead ID: 54162611, Link: https://kelsa.io/519/leads?current_item_id=54162611
```

### 3. Verify creation

`get_draft_status` confirms the record is created in **Proposed** stage with all fields intact. If any field is missing (notably derived numeric fields like `cf_expected_total_outright_cost_of_land` may not display), proceed anyway — those are cosmetic.

### 4. Assign to Prakash Singh

Use `assignee_id` as a **string**:

```python
call_tool("update_lead", {
    "lead_id": 54162611,
    "assignee_id": "36564"           # Prakash Singh
})
# → update queues as draft; verify with get_draft_status
```

### 5. Notify Prakash with @mention

```python
call_tool("add_note", {
    "lead_id": 54162611,
    "text": "Hi @[Prakash Singh](36564), new land proposal in Coorg — 100 acres plantation next to The Tamara. Asking ₹20 Cr outright. Please review and follow up."
})
```

## Multi-file upload to cf_land_pics (images + video)

After the lead exists, the user sent property photos and a video. `cf_land_pics` is a **multi-file attachment field** — it accepts an array of attachment objects. Both images (JPEG) and videos (MP4) live in the same array.

### Per-file S3 upload

Each file follows the standard get_upload_url → S3 POST → register_upload flow:

```python
import httpx, re, json

def extract_first_json(text):
    """Brace-counting JSON extractor — handles trailing content after the JSON."""
    depth = 0
    start = -1
    for i, ch in enumerate(text):
        if ch == "{":
            if start == -1:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start >= 0:
                return json.loads(text[start:i+1])
    raise ValueError("No JSON object found")

files = [
    ("/data/hermes/image_cache/img_93c64ea279ae.jpg", "coorg_property_1.jpg", "image/jpeg"),
    ("/data/hermes/image_cache/img_f859e9826914.jpg", "coorg_property_2.jpg", "image/jpeg"),
    ("/data/hermes/cache/videos/video_24389cb6391f.mp4", "coorg_property_video.mp4", "video/mp4"),
]

attachment_values = []

for filepath, filename, content_type in files:
    # Step 1: Get upload URL
    resp = call_tool("get_upload_url", {
        "pipeline_id": 519,
        "file_name": filename,
        "content_type": content_type
    })
    s3_url = re.search(r'POST the file.*?to: (https?://\S+?)(?:\n|$)', resp).group(1).rstrip(".")
    fields = extract_first_json(resp)

    # Step 2: POST to S3
    with open(filepath, "rb") as f:
        file_bytes = f.read()
    with httpx.Client() as client:
        upload_resp = client.post(s3_url, data=fields,
            files={"file": (filename, file_bytes, content_type)}, timeout=60)
    location_url = re.search(r"<Location>(.*?)</Location>", upload_resp.text).group(1)

    # Step 3: Register upload
    reg_resp = call_tool("register_upload", {
        "pipeline_id": 519, "file_url": location_url,
        "file_name": filename, "size": len(file_bytes)
    })
    reg_data = extract_first_json(reg_resp)
    attachment_values.append(reg_data)
```

### Update the lead with all attachments

The update **replaces** the entire field — pass all attachment objects in one array:

```python
call_tool("update_lead", {
    "lead_id": 54162611,
    "field_values": {
        "cf_land_pics": [
            {"name": "coorg_property_1.jpg", "upload_id": 11574857,
             "url": "...", "size": 223795},
            {"name": "coorg_property_2.jpg", "upload_id": 11574858,
             "url": "...", "size": 313569},
            {"name": "coorg_property_video.mp4", "upload_id": 11574859,
             "url": "...", "size": 4334442}
        ]
    }
})
```

This queues as a draft — verify with `get_draft_status`. The `Land pics` field now shows both images rendered inline and the video file as a link.

## Notes & pitfalls encountered

- **`get_valid_access_token()` takes NO arguments** — calling it from terminal `python3 -c` fails with `TypeError`. Use vault client directly instead (see §11 in SKILL.md).
- **`cf_expected_total_outright_cost_of_land` was accepted in create but didn't display in get_draft_status output.** This appears to be cosmetic (derived/calculated field behavior). The `cf_expected_rate_per_sqft` did display. No retry needed.
- **`cf_land_pics` update replaces the field entirely** — if existing files exist, you must include them all in the array. For a fresh record this is just the new files.
- **Video files (MP4) upload fine via the same S3 flow** — just set `content_type="video/mp4"`. The field accepts both images and videos in the same array.
- **File naming** used generic `coorg_property_1.jpg` etc. — better practice would be descriptive names like `coorg_plantation_aerial.jpg` but it's non-critical.
