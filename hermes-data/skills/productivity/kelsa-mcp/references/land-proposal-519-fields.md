# DRA Land Proposal (Pipeline 519) — Field Reference

## Quick Reference

| Item | Value |
|------|-------|
| Pipeline ID | 519 |
| Account | DRA (ID: 5) |
| Total records | 135 (as of Jul 2026) |
| Stages | 10 (Proposed → Info Gathered → Feasibility Checked → Site Visited → Proposal Made → Commercial Closure → Legal OK → Agreement → Lost Opp. [retired] → Rejected [retired]) |
| Fields | 92 |
| Record URL | `https://app.kelsa.io/5/leads/{lead_id}` |

## Stages

| # | Stage | Identifier | Prerequisite |
|---|-------|-----------|-------------|
| 1 | Proposed | st_proposed | Report New Land Proposal (data_entry) |
| 2 | Info Gathered | st_info_gathered | Perform Preliminary RnD (data_entry) |
| 3 | Initial Feasibility Checked | st_feasibility_approval_taken | Perform Initial Financial Model Feasibility (data_entry) |
| 4 | Site Visited And Approved | st_site_visited_and_approved | Visit Site (data_entry) |
| 5 | Proposal Made | st_proposal_made | Share Preliminary Offer (data_entry) |
| 6 | Commercial Closure & Token Done | st_commercial_closure___token_done | Collect required info (review) |
| 7 | Legal OK Obtained | st_legal_ok_obtained | Collect required info (review) |
| 8 | Agreement Done | st_agreement_done | Collect required info (review) |
| 9 | Lost Opportunity [retired] | st_lost_opportunity | — |
| 10 | Rejected [retired] | st_rejected | — |

## Key Fields by Field Set

### Land Details
| Display Name | Identifier | Type | Required in Stage 1 |
|-------------|-----------|------|---------------------|
| Land Location | cf_land_location | location | No |
| City | cf_city | dropdown (7) | **Yes** |
| Land Size UoM | cf_land_size_uom | dropdown (8) | **Yes** |
| Land Size Sqft | cf_land_size_sqft | number | **Yes** |
| Land Size Acres | cf_land_size_acres | number | No |
| Land Size Guntas | cf_land_size_guntas | number | No |
| Land Size Cents | cf_land_size_cents | number | No |
| Adjoining Road Width | cf_adjoining_road_width | number | No |
| Land Status On Offer | cf_status_on_offer | dropdown (5) | No |
| Land Zone | cf_land_zone | dropdown (5) | No |
| FAR Applicable | cf_far_applicable | number | No |
| Sy Nos | cf_sy_nos | text | No |
| Village | cf_village | text | No |
| Hobli | cf_hobli | text | No |
| Taluk | cf_taluk | text | No |
| District | cf_district | text | No |
| Land Sketch | cf_land_sketch | attachment | No |
| Land Legal Set | cf_land_legal_set | attachment | No |
| Land pics | cf_land_pics | attachment | No |
| Revenue Maps And Documents | cf_revenue_maps_and_documents | attachment | No |
| Location Google MapLink | cf_location_google_maplink | attachment | No |

### Proposal Details
| Display Name | Identifier | Type | Required in Stage 1 |
|-------------|-----------|------|---------------------|
| Proposal Brief | cf_name | text | **Yes** (maps to record name) |
| Date of Proposal | cf_date_of_proposal | date | **Yes** |
| Proposal Source | cf_proposal_source | dropdown (90) | **Yes** — also accepts arbitrary plain strings |
| Proposal Source Details Notes | cf_proposal_source_details_notes | text | **Yes** |
| Offer Type | cf_offer_type | dropdown (8) | **Yes** |
| Expected Rate Per Sqft | cf_expected_rate_per_sqft | number | No |
| Expected Total Outright Cost | cf_expected_total_outright_cost_of_land | number | No |
| Expected JV Ratio (Owner) | cf_expected_jv_ratio | number | No |
| Expected JV Ratio (Developer) | cf_expected_jv_ratio_for_developer | number | No |
| Product Type | cf_product_type | dropdown (12) | No |
| Proposal Notes | cf_proposal_notes | text | No |
| Correspondence Email | cf_correspondence_email | email | No |

### Offer Details
| Display Name | Identifier | Type |
|-------------|-----------|------|
| Offer Document | cf_offer_document | **attachment** — use for proposal PDF |
| Offered JV Refundable | cf_offered_jv_refundable | number |
| Offered Type | cf_offered_type | dropdown (5) |
| Offered Outright Rate | cf_offered_outright_rate | number |
| Offered Total Outright Price | cf_offered_total_outright_price | number |
| Offered JV Non-Refundable | cf_offered_jv_non_refundable | number |
| Offered Built-up Area Ratio (Owner) | cf_offered_built_up_area_ratio_to_land_owner | number |
| Offered Built-up Area Ratio (Developer) | cf_offered_built_up_area_ratio_for_developer | number |

### Other Fields
| Display Name | Identifier | Type |
|-------------|-----------|------|
| ProposalID | cf_proposalid | text (auto) |
| Additional Team Member | cf_additional_team_member | user |
| Project name | cf_project_name1 | text |
| Contact information | cf_contact_information | contact |
| comments | cf_comments | text |

## Known Dropdown Values

### City (7 options)
Bangalore is the default/correct choice for Bengaluru-area properties.

### Offer Type (8 options)
Common values: `Outright`, `JV`, `Lease`, `Joint Development`, `Sale`, `Leasehold`, `JV + Outright`

### Land Zone (5 options)
Values like: `Residential`, `Commercial`, `Industrial`, `Agricultural`, `Mixed Use`

### Land Status On Offer (5 options)
Values like: `Vacant`, `With Structure`, `Under Construction`, `Agricultural`, `Others`

### Land Size UoM (8 options)
`Sqft`, `Acres`, `Sqmt`, `Guntas`, `Cents`, `Grounds`, `Hectares`, `Sq Yards`

### Product Type (12 options)
`Apartment - High Rise (>G+8)`, `Apartment - Low Rise (G+4)`, `Villa`, `Row House`, `Plotted Development`, `Commercial`, `Industrial`, `Warehousing`, `Mixed Use`, `Farm Plot`, `Others`

## Create Lead — Mandatory Fields (Stage 1: Proposed)

When using `create_lead(pipeline_id=519, ...)`, these field_values are required:

1. `cf_date_of_proposal` — YYYY-MM-DD format
2. `cf_city` — plain string (e.g. "Bangalore")
3. `cf_name` — Proposal Brief / record name
4. `cf_proposal_source` — plain string works even for unlisted options
5. `cf_proposal_source_details_notes` — source description
6. `cf_land_size_uom` — "Sqft", "Acres", etc.
7. `cf_land_size_sqft` — numeric
8. `cf_offer_type` — plain string (e.g. "Outright")

Also pass `name` (top-level parameter) matching `cf_name`.

## Offer Document Attachment

For attaching the proposal PDF, use `cf_offer_document` (Offer Details field set, single-file attachment). Workflow:

1. `get_upload_url(pipeline_id=519, file_name="Proposal.pdf", content_type="application/pdf")`
2. Upload to S3 via curl multipart POST
3. `register_upload(pipeline_id=519, file_url=..., file_name=..., size=...)`
4. Pass the returned `{url, upload_id, size, name}` object as `cf_offer_document`

## Automations

- On entry at Proposed: adds followers Nishant Ranka, Bharat H, Vinod Kumar
- On entry at Proposed: auto-assigns to user 36564 (if cf_additional_team_member is set)
- On entry at Proposed (if Product Type = Warehousing): adds additional followers
