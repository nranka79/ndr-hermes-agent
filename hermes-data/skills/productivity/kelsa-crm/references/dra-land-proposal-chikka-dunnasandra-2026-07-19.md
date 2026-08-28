# DRA Land Proposal — Chikka Dunnasandra (via Satya Kateel)

Created 2026-07-19. 18-acre villa site, ₹324 Cr outright.

## Data Source

Satya Kateel (liaisoning agent, existing contact) sent details via
WhatsApp. User fed data piecemeal — first the location/price/survey
details, then the Google Maps link + map PDF, then product type
("Villa"), then offered "Go ahead now" signal.

## Piecemeal Data Pattern

The user does NOT give all details at once. They send one or two fields
at a time. The agent must **accumulate** and NOT create the record until
the user says "Go ahead", "All done", or "Create it". A table of
accumulated fields should be shown to confirm completeness.

## Kelsa Record

- **Lead #:** 53857201
- **Pipeline:** DRA Land Proposal (519)
- **Name:** Chikka Dunnasandra - 18 Acres Villa - via Satya Kateel
- **Stage:** Proposed
- **Assignee:** Prakash Singh (36564)
- **Followers:** Nishant Ranka, Vinod Kumar, Prakash Singh
- **Link:** https://kelsa.io/519/leads?current_item_id=53857201

### Fields set

| Field | Value |
|---|---|
| Date of Proposal | 2026-07-19 |
| City | Bangalore |
| Land Location | Chikka Dunnasandra, Near Azim Premji University, Sarjapur Road, Bengaluru East Taluk |
| Land Size UoM | Acres |
| Land Size Acres | 18 |
| Sy Nos | 68/1, 68/2, 68/3, 77, 78, 75, 76, 79, 70 |
| Village | Chikka Dunnasandra |
| Hobli | Sarjapur |
| Taluk | Bangalore East |
| District | Bangalore Urban |
| Offer Type | Outright |
| Product Type | Villa |
| Expected Rate Per Sqft | ₹4,132 (₹18 Cr/Acre) |
| Expected Total Outright Cost | ₹3,24,00,00,000 (not persisted in summary view) |
| Proposal Source | Satya Kateel |
| Proposal Source Details | Received via WhatsApp from Satya Kateel, liaisoning agent. Off-market deal. |
| Revenue Maps And Documents | ✅ Map PDF attached (survey boundaries) |
| Location Google MapLink | https://maps.app.goo.gl/xrzB3TJXG5vZNKDn8 |

### Land Status
- 9 Acres: Converted (commercial)
- 9 Acres: Yellow Zone
- 6 family owners for 15.05 Acres

## Vault Socket Limitation

Kelsa `get_valid_access_token` requires `GWS_VAULT_SOCKET` which is
available from **terminal** (`/opt/hermes/.venv/bin/python3`) but NOT
from **execute_code**. All Kelsa write operations were run via terminal
scripts under the Hermes venv.

## Draft Queue Pattern

- `create_lead()` → "Record queued for processing (draft ID: 98949742)"
  → `get_draft_status(draft_id=98949742)` → actual lead + link
- `update_lead()` → may also queue as draft → verify with
  `get_draft_status` or `get_lead`

## S3 Upload Notes

- `get_upload_url` returns a **text string** with S3 form fields in a
  JSON block. Extract fields with regex (not json.loads on the whole
  response).
- S3 POST response is XML. Extract `<Location>` with regex
  `r'<Location>(.*?)</Location>'`.
- `register_upload` returns a text block with a trailing JSON blob.
  Find the `{` index and parse from there.

## Assignee

- `assignee_id` must be a **string** (`"36564"`), not an integer
  (`36564` fails with "value at /assignee_id is not a string").
- Note with @mention was added to notify Prakash.
