# Pipeline 10 — Phone Search via Master Field (DRA Sales Leads)

## The Problem

Pipeline 10 (DRA Sales Leads) stores phone numbers as a **master field** linked to Pipeline 3429 (DRA Sales Contacts), not as a direct text/phone field on the lead.

```
Contact Details:
  + Contact (master → dra_sales_contacts) — cf_contact1
  + Contact Email (master → dra_sales_contacts) — cf_contact_email
  + Contact Phone (master → dra_sales_contacts) — cf_contact_phone
```

This means `search_leads(pipeline_id=10, query="919900571093")` returns **0 results** even if a lead with that phone exists. The phone text is inside the linked contact record, not on the lead itself.

## The Workaround

### Option A: Search contacts first (recommended for one-off lookups)

1. Search Pipeline 3429 (DRA Sales Contacts) by phone:
   ```
   search_leads(pipeline_id=3429, query="990005571093")
   ```
   Use the 10-digit number without 91 prefix. The contacts pipeline stores `cf_contact_phone` as a `(phone)` type field.

2. If found, get the contact's record ID from the search result.

3. Search Pipeline 10 for that contact ID via the master field:
   ```
   search_leads(pipeline_id=10, query="cf_contact1:<contact_id>")
   ```

### Option B: Search by name (fallback)

If the user provides names (as in the Google Sheet), search Pipeline 10 by name:
```
search_leads(pipeline_id=10, query="Akshay Pandey")
```

Names are text fields on the lead itself and are searchable directly.

## Current State (Jul 2026)

- Pipeline 10: **0 records** across all stages
- Pipeline 3429: **0 records**
- This was verified via `get_stats(pipeline_id=10, group_by="stage")` and `get_stats(pipeline_id=3429, group_by="none")`

Both pipelines have full structure (stages, fields, automations) but contain no data. Possible explanations:
1. Records exist but current Kelsa token lacks permissions to read them
2. Pipeline was recently purged/cleaned
3. Pipeline is defined but never had records created

**Before assuming records exist, always call `get_stats(pipeline_id=N, group_by="none")` to verify.**

## Related

- Pipeline 3429 has 0 stages (no workflow) and 9 fields: Contact (compound), Contact Email, Contact Phone, Location, Organization, Designation, SC ID, Identifier, ref checkbox.
- Pipeline 10 has 10 stages (Cold, Warm, PSC, SSV, Hot, Converted, + retired) and 60 fields across field sets: Site Visit Details, Requirement Details, Booking Details, Contact Details, C-Onboarding, Lost Details, Details.
