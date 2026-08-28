---
name: vehicle-fleet-management
description: Manage DRAAS fleet & personal vehicles — insurance policy filing, service estimate analysis, fuel/E20 compatibility research, resale valuation, and sell-vs-keep disposition guidance.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [vehicle, fleet, insurance, service, draas]
    related_skills: [google-workspace, gws-automation]
---

# DRAAS Fleet Vehicle Management

Umbrella for managing the DRAAS fleet — insurance document workflows and service estimate analysis.

## Reference Files

| Topic | File | Description |
|-------|------|-------------|
| Insurance Management | `references/insurance-management.md` | Upload policy PDFs, update master XLSX, set calendar renewal reminders |
| Service Estimate Analysis | `references/service-estimate.md` | Analyse dealer estimates, research parts/pricing, draft authorization messages |
| Vehicle Research & Disposition | `references/vehicle-research-disposition.md` | Fuel compatibility research (E20/flex-fuel), resale valuation across platforms, sell-vs-keep guidance, disposal channels, vehicle asset register creation & Drive upload |

## Key Distinction — E20 Only Affects Petrol Vehicles

**E20 (ethanol-petrol blend) is a PETROL-only mandate.** Diesel vehicles are completely unaffected — there is no ethanol blending requirement for diesel in India. When a user asks about E20 compatibility across a fleet, the first triage step is fuel-type classification:

- **Diesel** → No E20 concern. Continue normal diesel use.
- **Petrol / Petrol Hybrid** → Check MFG year for E20 compatibility.
- **All vehicles post-April 2023** → E20 compatible by law.
- **Pre-2017 petrol vehicles** → Highest risk; sell recommendation most common outcome.

## Common Pitfalls

- **XLSX is NOT a Google Sheet** — download via Drive API, edit with openpyxl, upload back
- **openpyxl path:** not in system Python; use `/opt/hermes/.venv/lib/python3.13/site-packages/openpyxl` or set PYTHONPATH
- **Merged cell traps in XLSX** — always write to Column B (top-left of merged B:D range), unmerge first if needed
- **Battery registration on modern cars** — new battery must be registered with ECU; dealer vs aftermarket pricing comparison needed
- **Vehicle model confusion** — owners often misidentify their car's variant; verify from RC document
- **`drive_search` raw_query quirk** — the skill's `drive_search` accesses `args.query if args.raw_query else ...`. When calling from `gws_skill_bridge.call()`, you MUST pass BOTH `raw_query=True` AND the full Drive query string in `query=`. Passing only one raises `AttributeError`.
- **`drive_download` expects `output`, not `path`** — parameter name is `output` (destination file path), not `path`
- **`drive_upload` parent folder** — to place files in a specific Drive folder (e.g. TMP), pass `parent="FOLDER_ID"`. Without it, file lands at Drive root.
- **`gmail_labels` / `gmail_search` work as direct kwarg pass-through** — no raw_query quirk, just pass parameters directly
- **Insurance data lives on Bharat's PERSONAL Drive, not the workspace Drive** — the insurance master XLSX (`1tLZRVTyrQR1iu4aSNTawVuf4JkEjXgi5`) and insurance folder (`16R5MtZRoQrLM64Hpxejuij_wV08hfQ4E`) are in Bharat's **personal Google account**, NOT the DRAAS workspace (`google-draas` / `sales1.blr@draas.com`). Any attempt to access these from the work account returns 404/403. To get insurance data: either ask Bharat to share individual files with `sales1.blr@draas.com`, get the data directly from him, or have him authorize his personal Gmail via OAuth.

## Consolidation Note

This umbrella merges two previously separate skills: `vehicle-insurance-management` and `vehicle-service-estimate`. Their full content remains archived at `~/.hermes/skills/.archive/<name>/SKILL.md` for detailed reference.
