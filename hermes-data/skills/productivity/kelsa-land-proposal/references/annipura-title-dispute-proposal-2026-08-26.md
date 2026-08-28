# Annipura (Lalbagh Road) — Varnika 33 Guntas Land Proposal Entry (26 Aug 2026)

## Session summary
Created a Kelsa Land Proposal (Pipeline 519, Lead #54965107) for 1a 33½g Inam land at Sy.15, Annipura Village, Kasaba Hobli, Bengaluru North Taluk — Hosur Highway/Lalbagh Road. Originated via Rupa Gangadharapa + VK Reddy meeting, with Etesh Reddy quoting ₹18,000/sqft.

## Key lessons

### `cf_name` (Proposal Brief) requires BOTH `name` param AND field value
`create_lead` has two separate fields: the record-level `name` parameter and the `cf_name` custom field. Pipeline 519's Proposed stage requires `cf_name` as a data-entry prerequisite. Passing only `name` fails with:

```
Validation failed: Required fields not present: Proposal Brief
```

**Fix:** Always pass the same value in both:
```python
create_lead(
    pipeline_id=519,
    name="Location - Size - via Broker",
    field_values={
        "cf_name": "Location - Size - via Broker",
        ...
    }
)
```

### User name resolution — try multiple name variations
`list_users(pipeline_id=519, query="Rahul")` → 0 results for "Vinod Kumar Das (Rahul, vkdas@draas.com)". His Kelsa display name is **"Vinod Kumar"**, not "Rahul" or "Vinod Kumar Das".

**Search strategy:**
1. Email prefix: `query="vinod"` → hit (matches "Vinod Kumar")
2. Full Kelsa display name: Firstname Lastname format
3. People API search (google-draas) to find the Google contact, extract the Kelsa display name, then search that
4. Familiar name alone ("Rahul") rarely works — Kelsa doesn't index aliases

Vinod Kumar's Kelsa user ID: **31363** (vs Prakash Singh: 36564).

### Scanned document workflow
The title report PDF had **no text layer** (pdftotext returned empty, 6 pages, 5.5MB). Used:
- `pdfinfo` → 6 pages, no tags, no metadata
- `pdftoppm -png -r 200` → 6 PNGs (~3-4.8 MB each)
- `vision_analyze` per page → complete text extraction

See kelsa-crm skill §4.1 (Scanned PDF path) for the full recipe.

### Fields that persisted vs silently failed (confirming existing documented pitfalls)
| Field | Value | Persisted? |
|---|---|---|
| cf_land_size_sqft | 80,042 | ❌ (silent fail — documented) |
| cf_expected_total_outright_cost_of_land | ₹1,44,07,56,000 | ❌ (silent fail — documented) |
| cf_land_size_acres | 1.8375 | ✅ |
| cf_expected_rate_per_sqft | ₹18,000 | ✅ |
| cf_land_legal_set | Title report PDF | ✅ |
| cf_key_legal_points_to_cover | Full title dispute summary | ✅ |
| cf_land_notes | Property background notes | ✅ |
| cf_proposal_notes | Strategic notes | ✅ |

### Google Maps link field
`cf_location_google_maplink` is an **attachment-type field** but takes a plain URL string, NOT an S3 upload. Pass the Google Maps URL as a bare string:
```
"cf_location_google_maplink": "https://maps.app.goo.gl/tR3ejH9VWcVNUp6U7"
```
This peristed correctly.

### Notification workflow
After creating the lead, added two notes with @mentions:
1. `@[Prakash Singh](36564)` — full briefing on VK Reddy meeting, Etesh Reddy quote, SDC status, both claimants dead
2. `@[Vinod Kumar](31363)` (Rahul) — preliminary DD tasks: RTC, Mutation, 30-yr EC, legal analysis of competing grants under KLRA vs Inam Abolition, SDC live status check

Each @mention in add_note auto-adds the person as a follower and sends them a notification. The record URL was included in the note output.