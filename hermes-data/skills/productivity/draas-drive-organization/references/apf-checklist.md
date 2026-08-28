---
name: apf-checklist
description: Fill the Axis Bank APF (builder login) document checklist for DRA projects as a marked PDF. Use when the user sends an "APF Checklist" PDF and a list of available Sr Nos (and/or NA items) per project.
---

# APF Checklist Filler

## Trigger
User sends `APF Checklist Empty.pdf` (or similar) plus a line like `CHECKLIST - AVAILABLE - 1,3,7,8,9,10,11,13,14,15,16` and `other documents - 5,6`, often with `PROJECT NAME` / `DEVELOPER`. Follow-up replies like "11 is available", "ADD NA to 5,12", "other documents - NA to 1,2,3,4" apply to the LAST project discussed — keep per-project configs separate.

## Marking scheme (user preference)
- **Yes** = available → green row, bold status
- **NA** = not applicable → amber row, bold status
- **No** = not available (default) → plain white

## Checklist structure (bank template)
- Title Related Documents: Sr 1–12 (12 has sub-items 12.1 Allotment letter, 12.2 NOC, 12.3 Lease Deed)
- Region Specific Title: Sr 13 Khata/Property card, 14 NA-tax receipt, 15 NEC 30 yrs
- Plan/Approvals: Sr 16 Approved layout+building plans, 17 Commencement cert, 18 Brochure
- Other Documents (post-login): 1 NOCs (Env/Aviation/Fire/Pollution/NGT), 2 Builder Data Sheet, 3 Bank Account, 4 Payment Plans, 5 KYC PANs, 6 Inventory, 7 Price List, 8 Mortgage Declaration, 9 Visit Report

## Known projects
- **Ranka Amber** — builder: DRA Realty Pvt Ltd, Bangalore
- **Ranka Udaya** — developer: DRA Thindlu Land Partners

## Build
Template script: `/tmp/make_apf_checklist.py` (reportlab, landscape A4, per-project config dict `PROJECTS`).
- `title_yes` / `title_na` / `region_yes` / `plan_yes` / `other_yes` / `other_na` sets per project; everything else defaults to No.
- Run with the uv venv python (`source /opt/hermes/hermes-data/venvs/*/bin/activate`), then regenerate ALL projects in the dict (script builds both).
- Header: Project name + builder from config; leave Date of Login / Sales Channel blank.
- Output: `/tmp/APF_Checklist_<Project>_Filled.pdf`.

## Verification
- `pdftotext -layout <pdf> - | grep -E "Yes|NA" | grep -vE "File|Yes/No"` — confirm each Sr shows the intended status.
- Optionally `pdftoppm -png -r 70` + vision check for overlap.

## Pitfalls
- Sr numbers are STRINGS in the config sets — `sr in {"12"}` works, `sr in {12}` silently marks everything No.
- NA on Sr 12 must also include 12.1/12.2/12.3 (block rows).
- Deliver via MEDIA:/path in the reply; send_message channel addressing may be blocked in this environment.
