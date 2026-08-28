# Curing - Iris Pipeline (ID: 2335)

Discovered: 2026-07-16 by Anbarasan M
Account: 5 (DRAAS)
Pipeline URL: https://kelsa.io/2335

## Overview

Tracks concrete curing at the Iris project site (Gunjur Palya, Bengaluru). 
Created by Aravindan Jyothi and site team in 2023. 679 records, all in Reported stage, unassigned.

## Stages

| Stage | Identifier | Type |
|-------|-----------|------|
| Reported | st_prospect | Active |
| Retired | st_retired | Retired |

## Fields

| Display Name | Identifier | Type | Details |
|-------------|-----------|------|---------|
| Location of Photo | `cf_location_of_photo` | location | Google Maps pin/address |
| Photos of Curing | `cf_photos_of_curing` | attachment (multi) | S3 upload → register flow |
| Which Floor | `cf_which_floor` | dropdown (16 options) | Ground, 1st, 2nd, 3rd... ~16th |
| Structural Element | `cf_structural_element` | dropdown (2 options) | Column, Slab |

## Prerequisites

**Reported stage — Report Curing Photos (data_entry):**
- Required: cf_location_of_photo, cf_photos_of_curing, cf_structural_element
- Optional: cf_which_floor

**Retired stage — Collect required information (review):**
No specific field requirements.

## Automations

- `add_followers` on entry at Reported stage
  Adds: Nishant Ranka (41), Anbarasan (682), Naveed Khan

## Observations

- All 679 records stuck in Reported stage since 2023 — no records have been retired
- Most location photos show Gunjur Palya / Domlur area (Iris project site)
- "Which Floor" field was only populated on 181/679 records (27%)
- Records auto-numbered by Kelsa (no meaningful record names)
- Original creators: Aravindan Jyothi (most) or system (some)
