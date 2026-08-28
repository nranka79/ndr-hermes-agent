# Land Record Table (4-Stage) Extraction — Worked Example

**Session:** Jul 2026, Chikkaballapur Land Proposal (Nishant Prakash via WhatsApp)
**User:** Nishant Ranka (DRAAS)

## Trigger

Voice message: "40 acres in Chikbalapur... left towards Nandi Hills... outright purchase, target 4.8 Cr/acre... CLU conversion part of it, 14-15 acres already converted... 25 acres available for registration... Jiraffe Capital (Vineet Agrawal) participating... Nishant submitting to Adv. Uday (HSR)... legal opinions exist for some survey numbers."

User sent 5 images: 2x land record tables, 1x cadastral map, 1x broader land-use map, 1x Sy 47 layout subdivision.

## Extracted Data

### Location
- **Villages:** Arasanahalli & Kuppahalli
- **Hobli:** Nandi Hobli
- **Taluk:** Chikkaballapura Taluk
- **District:** Chikkaballapura District
- **Route:** Chikkaballapur town → left turn towards Nandi Hills road

### Stage-wise Breakdown

| Stage | Color | Sy Nos | Total Extent | Karab | Net Extent | Remarks |
|-------|-------|--------|-------------|-------|-----------|---------|
| **1** | Green | 58/2, 58/3, 57/3, 57/5, 57/2A, 57/2B, 47/6, 47/7 | 4A 27G | 0 | 4A 27G (4.67 Ac) | Conv / C & Cst |
| **2** | Yellow | 47/2, 57/4, 57/1A, 57/1B, 57/6, 44/1, 44/2A, 44/2B, 43/1, 43/2 | 2A 29G | 1G | 2A 28G (2.70 Ac) | Conv |
| **3** | Blue | 45/1, 45/2, 47/3, 112/2, 113/2, 114/2, 115/2 | 9A 13.5G | 6G | 9A 7.5G (9.19 Ac) | Court Stay on 2 entries |
| **4** | Purple | 116/1, 116/2, 117, 118, 120/1-4, 121/1-3, 122/1-6, 123/1-4, 124/1A-6 (30 sub-divisions) | 13A 3G | 6G | 12A 37G (12.93 Ac) | — |
| | | **Total** | **29A 12.5G** | **13G** | **~29.5 Ac** | |

### Owner Summary (for legal due diligence)

**Stage 1 owners:** Krupal & Others (5 sy), V Rama (2 sy), Gowramma (1 sy), Dhyan Estates (1 sy)
**Stage 2 owners:** A M Amaranarayanaswamy (3 sy), Muninarayanappa (2 sy), Manishami, Munishamappa, Reddappa (3 sy)
**Stage 3 owners:** A N Nanjundegowda (2 sy), M Nanjappa (1 sy), Dodda Nanjappa & Oth (2 sy), Gowramma (2 sy)
**Stage 4 owners:** 22 distinct owner entries — Ramakrishnappa, R Srinivaschowdari, Channarayappa, Munivenkatappa (multiple entries), Bangara Hanumantha, K Venkatesh, K N Srinivas, Talari Appayya, Maddarappa, and 13 more

### Documented vs Claimed Extent

| Source | Extent | Notes |
|--------|--------|-------|
| 4-stage table | ~29.5 Ac | Documented net extent |
| User voice claim | ~40 Ac | May include Sy 47 layout subdivision |
| User voice: "25 Ac available for registration" | ~25 Ac | Likely Stages 1+2+4 (~20 Ac) or similar |
| User voice: "14-15 Ac already converted" | ~14-15 Ac | Likely Stages 1+2 (7.4 Ac) + part of 3 |

**Key gap:** ~10.5 acres difference between documented table and user claim. Possible explanations:
1. Sy 47 layout subdivision (image 4 shows 47/1 through 47/7000+ as subdivided layout plots)
2. Additional survey numbers not included in the 4-stage grouping
3. Rounding by the user

### Contact Lookup Results

| Spoken Name | Correct Name | Org | Phone | Email |
|-------------|-------------|-----|-------|-------|
| Vinit Agarwal | Vineet Agrawal | Jiraaf | +91 97390 99290 | Vineet@jiraaf.com |
| Jiraffe Capital | Jiraaf | Jiraaf | — | — |
| Nishant Prakash (Zara) | Nishant Prakash Zara | — | +91 99996 73483 | nishantprakash@theyelloweye.com |

## Workflow Used

1. **Voice message → parse deal parameters** (rate, type, acres, partners, legal contacts)
2. **Images arrive** → vision_analyze on each for OCR + spatial understanding
3. **Tabular data extraction** → survey numbers, extents, owners per stage
4. **Map correlation** → confirm villages/hobli/taluk from map title, match phase colors
5. **Drive folder creation** → DRA Realty > [Project Name] folder (check canAddChildren first)
6. **Kelsa Pipeline 519 entry** → create lead with proposal details and Drive hyperlinks
7. **Research** → Chikkaballapur/Nandi Hills corridor land rates
8. **Document upload** → upload the images as supporting documents to Drive

## Pitfalls Encountered

- **build_service returns Resource, not Credentials**: `build_service('drive', 'v3', service_name='google-draas')` returns a ready-to-use Resource, not Credentials. Do NOT pass it to `build()` again. Use it directly: `svc = build_service(...)` then `svc.files().get(...)`.
- **Nested Python in heredoc**: Avoid nested f-strings with quotes inside heredocs passed to `terminal()`. Use temp files instead.
- **gws_skill_bridge drive_search return format**: Returns a JSON string that is a **list** of files (not an object with a 'files' key). Parse via `json.loads(result)` and iterate the list directly.
- **Voice-to-text name errors**: "Vinit Agarwal" → "Vineet Agrawal", "Jiraffe Capital" → "Jiraaf". Always search both the spoken variant and the corrected variant.
