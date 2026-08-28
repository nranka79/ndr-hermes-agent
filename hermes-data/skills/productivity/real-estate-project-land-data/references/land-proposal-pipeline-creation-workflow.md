# Land Proposal Pipeline Creation — Worked Example (Chikkaballapur RC40)

**Session Date:** 2026-07-25
**Project:** Ranka Chikkaballapur 40 (RC40) — 40Ac Arasanahalli/Kuppahalli
**Kelsa Lead ID:** 54039174
**Drive Folder ID:** 1_bstNNtjLY8ndkixWoDQGKQh-Xl6MgfD

## Source Documents

The user provided 5 images via WhatsApp:
1. Stage-wise land record table (4 stages with Sy No, extent, owners)
2. Phase colour map (cadastral with green/yellow/blue/purple zones)
3. Chikkaballapur Town Planning zoning map
4. Sy 47 layout subdivision map
5. Clear version of the stage-wise table

## Step-by-Step

### 1. Extract Data via Vision

Used `vision_analyze` on the table images to extract:
- 4 stages with survey numbers, extents (Acres+Guntas), Karab, Net Extent
- Owner names and father/husband names
- Remarks ("Conv", "Court Stay", "C & Cst")
- Colour legend (Green=Stage1, Yellow=Stage2, Blue=Stage3, Purple=Stage4)
- Title box: Arasanahalli & Kuppahalli Villages, Nandi Hobli, Chikkaballapur Taluk

### 2. Contact Lookup — Capital Partner

Searched for "Vinit Agarwal" and "Jiraffe Capital" via People API + contacts sheet:
- **Correct spelling:** Vineet Agrawal (not Vinit Agarwal)
- **Company:** Jiraaf (not Jiraffe Capital)
- **Phone:** +91 97390 99290 (contacts sheet row 4073)
- **Email:** Vineet@jiraaf.com
- Voice-to-text routinely produces "Jiraffe Capital" — always correct to "Jiraaf"

### 3. Create Drive Folder

```python
bridge_call("drive_create_folder",
    name="Ranka Chikkaballapur 40 (RC40) - 40Ac Arasanahalli Kuppahalli",
    parent="1vuUfqKcbldp4tkW0cHyE4S7zSwaKVOom",  # DRA Realty folder
    service_name="google-draas")
```

Then uploaded 5 images:
```python
bridge_call("drive_upload",
    path="/data/hermes/image_cache/img_74d42120798b.jpg",
    name="Chikkaballapur_40Ac_Stage_Wise_Land_Record.jpg",
    parent=FOLDER_ID, mime_type="image/jpeg",
    service_name="google-draas")
```

### 4. Create Kelsa Land Proposal Entry

**Pipeline:** DRA Land Proposal (ID: 519)
**Stage:** Proposed (st_proposed)

**Key field values used (plain strings for dropdowns):**
```python
FIELD_VALUES = {
    "cf_date_of_proposal": "2026-07-25",
    "cf_city": "Bangalore",
    "cf_name": "Chikkaballapur - 40 Ac Arasanahalli/Kuppahalli - Land Proposal",
    "cf_proposal_source": "Nishant Prakash",
    "cf_proposal_source_details_notes": "Proposal by Nishant Prakash (Zara). Legal: Adv. Uday, HSR. Capital: Jiraaf/Vineet Agrawal.",
    "cf_land_size_uom": "Acres",
    "cf_land_size_sqft": 1742400,  # 40 × 43560
    "cf_offer_type": "Outright",
    "cf_land_size_acres": 40,
    "cf_land_location": "Arasanahalli & Kuppahalli, Nandi Hobli, Chikkaballapur Taluk, Chikkaballapur District",
    "cf_village": "Arasanahalli, Kuppahalli",
    "cf_hobli": "Nandi Hobli",
    "cf_taluk": "Chikkaballapur",
    "cf_district": "Chikkaballapur",
    "cf_sy_nos": "S1:58/2,58/3,57/3,57/5... | S2:47/2,57/4... | S3:45/1,45/2... | S4:116/1-124/6",
    "cf_expected_rate_per_sqft": 1102,  # 4.8 Cr / 43560
    "cf_expected_total_outright_cost_of_land": 1920000000,  # 40 × 4.8 Cr
    "cf_product_type": "Plots",
}
```

**Pitfall encountered:** First attempt passed dropdown values as `{"id": "Bangalore", "label": "Bangalore"}` — got "Invalid dropdown value for City" error. Fixed by using plain strings like `"Bangalore"`.

**Pitfall encountered:** `cf_status_on_offer` set to `"Available"` was rejected — the 5-option dropdown doesn't include "Available". Omitted it.

### 5. Add Structured Notes

**Note 1 — Analysis:** Full proposal summary with stage breakdown, CLU status, Jiraaf details, CUDA zoning links.

**Note 2 — Clarification (for broker):** Flagged that docs show ~29.5 Ac vs 40 Ac claimed. Listed specific items needing clarification:
- Documentation for remaining ~10.5 Ac
- Exact Phase 1 converted acreage (~7.95 Ac?)
- Court stay status on 2 Stage 3 entries
- Google Maps pin
- Included a ready-to-send WhatsApp message draft.

**Note 3 — Market Research:** Nandi Hills land rates, CUDA Master Plan links, rate analysis at ₹4.8 Cr/acre.

## Key Contacts Verified

| Contact | Details | Source |
|---------|---------|--------|
| Vineet Agrawal (Jiraaf) | +91 97390 99290, Vineet@jiraaf.com | Contacts sheet row 4073 + People API |
| Nishant Prakash (Zara) | +91 99996 73483, nishantprakash@theyelloweye.com | Contacts sheet row 2316 |
| Adv. Uday (HSR) | No contact info available | Referenced by user |
