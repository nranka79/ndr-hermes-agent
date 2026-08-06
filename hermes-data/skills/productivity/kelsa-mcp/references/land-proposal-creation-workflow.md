# Land Proposal Creation (Pipeline 519) — From WhatsApp/Extracted Data

## Pipeline Context

DRA Land Proposal (ID: 519) tracks land deals from initial proposal through to agreement. The first stage is **Proposed** — and the data_entry prerequisite "Report New Land Proposal" requires ~30 fields.

## Source: WhatsApp / Image / Voice Message

When the user shares a property proposal via WhatsApp image or text, extract these fields:

| WhatsApp Data | Kelsa Field Identifier | Type | Example |
|---------------|----------------------|------|---------|
| Location / Address | `cf_land_location` | location | "Hoodi Main Road, Whitefield" |
| City | `cf_city` | dropdown | "Bangalore" |
| Land Size (number) | `cf_land_size_acres` | number | 4 |
| Land Size UoM | `cf_land_size_uom` | dropdown | "Acres" |
| Area in sqft | `cf_land_size_sqft` / `cf_land_size` | number | 174340 |
| Road Width | `cf_adjoining_road_width` | number | 80 |
| Offering price | `cf_expected_total_outright_cost_of_land` | number | 3250000000 |
| Rate per sqft | `cf_expected_rate_per_sqft` | number | 18642 |
| Brief description | `cf_name` (Proposal Brief) | text | "4 Acres on Hoodi Main Road" |
| Source / Broker | `cf_proposal_source` | dropdown | "Sudhir Ramakant" |
| Source notes | `cf_proposal_source_details_notes` | text | "Via WhatsApp, ref by..." |
| Offer type | `cf_offer_type` | dropdown | "Outright" |
| Offer document (PDF) | `cf_offer_document` | attachment | Upload proposal PDF |
| Product type | `cf_product_type` | dropdown (multi) | "Commercial, Residential" |
| Land zone | `cf_land_zone` | dropdown | "Industrial" |
| Status on offer | `cf_land_status_on_offer` | dropdown | "Compounded, Converted" |
| Additional team member | `cf_additional_team_member` | user | "Prakash Singh" |
| Land notes | `cf_land_notes` | text | "Near metro, frontage 510 ft" |
| Proposal notes | `cf_proposal_notes` | text | "Asking Rs 325 Cr, negotiable..." |
| Other details | `cf_other_details` | text | "Nearby landmarks, best offer received" |
| Date of proposal | `cf_date_of_proposal` | date | "2026-06-17" |
| Image/sketch | `cf_land_sketch` | attachment | Upload image separately |

## Common Dropdown Values (confirmed via existing records)

- **City:** "Bangalore", "Chennai"
- **Land Size UoM:** "Acres", "Sqft", "Sqmt", "Cents", "Grounds", "Guntas"
- **Land Status On Offer:** "Compounded, Converted", "Open Land", "Agricultural", "Green Belt"
- **Land Zone:** "Industrial", "Residential", "Commercial", "Mixed", "Agricultural"
- **Offer Type:** "Outright", "Joint Venture", "Joint Development", "Lease", "Revenue Share"
- **Product Type (multi-select):** "Apartment - High Rise (>G+8)", "Apartment - Mid Rise (G+4 to G+8)", "Villa / Row House", "Plotted Development", "Commercial", "Mixed Use", "Warehousing"
- **Proposal Source:** Broker names typically — search by name; if not found, the entry will still be queued with the text value (Kelsa may accept a non-conforming value for new brokers)

## Image / Sketch Attachment

The WhatsApp image (site sketch/location layout) belongs in the **Land Sketch** field (`cf_land_sketch` — attachment type). See Pipeline 519 field details:

- `cf_land_sketch` — "Land Sketch" — best for site layout/property boundary images
- `cf_land_pics` — "Land pics" — for actual site photos
- `cf_location_pics` — "Location Pics" — for location maps
- `cf_offer_document` — "Offer Document" — for full proposal PDFs/offer letters

## Creating with a PDF Attachment (One-Shot)

Proposal PDFs (offer letters, brochures) can be uploaded and attached **at creation time** in a single `create_lead` call — no need for a two-step create-then-update workflow.

**Full workflow from `execute_code`:**

```python
# Step 1: Upload to S3
s3_fields = get_upload_url(pipeline_id=519, file_name="proposal.pdf", content_type="application/pdf")
file_url = s3_fields["file_url"]

# Parse JSON fields from get_upload_url response and POST to S3
import subprocess
cmd = ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}"]
for k, v in s3_fields["form_fields"].items():
    cmd.extend(["-F", f"{k}={v}"])
cmd.extend(["-F", f"file=@/path/to/proposal.pdf"])
subprocess.run(cmd)  # Expect HTTP 201

# Step 2: Register upload
attachment = register_upload(pipeline_id=519, file_url=file_url, file_name="proposal.pdf")

# Step 3: Create lead with attachment in field_values
create_lead(pipeline_id=519, name="Proposal Brief", field_values={
    "cf_name": "Proposal Brief",
    "cf_date_of_proposal": "2026-07-23",
    "cf_city": "Bangalore",
    "cf_proposal_source": "Broker Name",  # Accepts plain string even if not in dropdown
    "cf_proposal_source_details_notes": "Via WhatsApp...",
    "cf_land_size_uom": "Sqft",
    "cf_land_size_sqft": 23641,
    "cf_offer_type": "Outright",
    "cf_offer_document": {
        "url": attachment["url"],
        "upload_id": attachment["upload_id"],
        "size": attachment["size"],
        "name": attachment["name"]
    }
})
```

**Key points:**
- Attach to `cf_offer_document` for full proposal PDFs (not sketches/photos)
- `cf_proposal_source` accepts plain string labels — new/unlisted broker names work without editing the dropdown options
- The `name` top-level parameter AND `cf_name` in field_values should both be set to the proposal brief
- Attachments must be uploaded via S3 first using `get_upload_url` → `register_upload` — they're identified by `{url, upload_id, size, name}`

## Post-Creation Updates

If the record needs updates after creation (e.g., user said "please also add Prakash Singh"), you'll need to find the lead ID once indexed. If `create_lead` says "queued for processing," the record may take time to appear in search. The user can check directly at `https://kelsa.io/519` for the latest records.

## Complete Example (Jun 2026)

WhatsApp proposal for 4 Acres on Hoodi Main Road, Whitefield:
- Extent: 4 Acres (1,74,340 sqft), 80 ft road, 510 ft frontage
- Price: ₹325 Cr (₹18,642 psf), best offer ₹315 Cr
- KIADB allotted, freehold, 2 brothers + 1 sister
- CLU & NOC from KIADB = buyer's scope
- Source: Broker Sudhir Ramakant, contact N. Nagaraja Naik (KIADB)
- Product: Commercial/Residential/Mixed Use
- Created with: `cf_proposal_source: "Sudhir Ramakant"`, `cf_offer_type: "Outright"`, `cf_additional_team_member: "Prakash Singh"`
