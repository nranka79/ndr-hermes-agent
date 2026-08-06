# DRA Policies Pipeline (ID: 2112) — Account 5

Insurance policy tracking pipeline for health, car, and tax policies.

## Quick Stats

- **Records:** ~31
- **Created:** Legacy (records date back to 2019)
- **Owner:** Sarthak Sharma (original creator), maintained by Nishant Ranka

## Stages (3)

| Stage | Identifier | Type |
|-------|-----------|------|
| Policy Purchased | `st_prospect` | Active — data_entry prerequisite |
| Policy Lapsed / Terminated | `st_closing` | Terminal/closing — manual_action prerequisite |
| cars sold | `st_retired` | Retired |

### Stage Behaviour

- **Policy Purchased:** Has a `data_entry` prerequisite "Add New Policy Details" that requires ~12 fields including policy type, numbers, dates, nominee, and attachment.
- **Policy Lapsed / Terminated:** Only has a `manual_action` prerequisite. Custom fields may NOT persist here for some records — BUT if the record has been briefly moved to Policy Purchased and back, field writes can succeed even while remaining in terminal (confirmed Jul 2026 on lead 53683206). See umbrella SKILL.md for full nuance.
- **cars sold:** Retired stage. Records here are legacy.

## Field Sets

### Car Insurance Policies
| Field | Identifier | Type | Notes |
|-------|-----------|------|-------|
| policy type | `cf_policy_type1` | dropdown (4 options) | Uses labels: "term life", "health insurance" etc. |
| Vehicle | `cf_vehicle` | text | |
| Vehicle number | `cf_vehicle_number` | text | |
| Policy number | `cf_policy_number` | text | Primary policy number (e.g. LLA0014391000101) |
| Policy Period | `cf_policy_lapse_date` | date | Policy period/expiry |
| Policy taken by | `cf_policy_taken_by` | dropdown (4 options) | e.g. "Royal Sundaram" |
| Attachment of the policy | `cf_attachment_of_the_policy1` | attachment | S3 PDF URL |
| Terms and conditions | `cf_terms_and_conditions` | text | |

### Health Insurance Policies
| Field | Identifier | Type | Notes |
|-------|-----------|------|-------|
| Policy number | `cf_policy_number1` | text | Secondary policy number (e.g. LLA0014391000107) |
| Policy holder name | `cf_policy_holder_name` | text | |
| Policy start date | `cf_policy_start_date` | date | |
| Policy end date | `cf_policy_end_date` | date | |
| Nominee name | `cf_nominee_name` | text | |

### Tax Policies
| Field | Identifier | Type |
|-------|-----------|------|
| Tax Policy Number | `cf_tax_policy_number` | text |
| Tax Policy Holder Name | `cf_tax_policy_holder_name` | text |
| Tax Policy Start Date | `cf_tax_policy_start_date` | date |
| Tax Policy End Date | `cf_tax_policy_end_date` | date |
| Tax Policy Attachment | `cf_tax_policy_attachment` | attachment |
| Tax Policy Nominee Name | `cf_tax_policy_nominee_name` | text |

## Known Pipeline Design Issues

### Policy Type → Other Fields Not Accepted

When `cf_policy_type1` is set to "Health Insurance", the other fields in the **Car Insurance** field set (vehicle details, policy number, taken by, attachment, terms) do NOT accept values properly. This is a confirmed pipeline configuration bug (Nishant Ranka, Jul 2026).

**Workaround:** Set policy type to "term life" temporarily to populate the other car-insurance fields, then switch back to the correct type after the pipeline is fixed.

### No Attachment Field in Health Insurance Field Set

The Health Insurance field set lacks an attachment field. The only attachment field (`cf_attachment_of_the_policy1`) lives under Car Insurance Policies. This means health insurance policy PDFs must use the car insurance attachment field, which only works when policy type is NOT "Health Insurance" (see issue above).

## Recent Records (Jul 2026)

| ID | Lead Name | Stage | Updated | Notes |
|----|----------|-------|---------|-------|
| 53683206 | Kanta Ranka - Royal Sundaram Lifeline Elite (2026-2027) | Lapsed/Terminated | 14h ago | ₹2,09,731 p.a., nominee: Dinesh Devraj Ranka |
| 1075052 | Nishant Ranka - Royal Sundaram (2025-2027) | Policy Purchased | 15h ago | PDF attached |
| 1075050 | Dharmesh D Ranka - Royal Sundaram (2025-2027) | Policy Purchased | 15h ago | PDF attached |
| 1075049 | Manish Dinesh Ranka - Royal Sundaram (2025-2027) | Policy Purchased | 15h ago | PDF attached |

## S3 Attachment Upload Pattern

When uploading a policy PDF to this pipeline:

1. `get_upload_url(pipeline_id=2112, file_name="...pdf", content_type="application/pdf")`
2. `curl` multipart POST to S3 (file field MUST come last, HTTP 201 = success)
3. `register_upload(pipeline_id=2112, file_url=...)` → returns `{url, upload_id, size, name}`
4. `update_lead(lead_id=..., field_values={"cf_attachment_of_the_policy1": {...}})` — only works when lead is NOT in terminal stage
