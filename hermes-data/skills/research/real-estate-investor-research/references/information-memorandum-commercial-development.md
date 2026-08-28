# Information Memorandum — Commercial Development Feasibility (DRAAS Worked Example)

**Date:** June 2026
**Property:** ~1.23 Acres, Garudacharpalya Metro Station, Whitefield, Bangalore
**Requesting user:** Prakash Singh (psingh@draas.com), for Nishant Ranka
**Proposed Use:** Commercial Development (Office + Ground Floor Retail)

---

## Document Structure (12-Section IM)

The Information Memorandum follows this structure:

1. Executive Summary (1-page: FAR, built-up area, current rents, vacancy, recommendation)
2. Property Overview & Site Details (survey area, location highlights, strategic advantages)
3. Location & Connectivity (distance matrix, transport infrastructure table)
4. Development Analysis — FAR & Building Norms (zone, FAR table, building metrics, compliance)
5. Current Developments in Vicinity (table: project, developer, size, distance, occupancy)
6. Upcoming Developments & Infrastructure Catalysts (table: project, size, status, impact)
7. Commercial Market Report — Rentals & Occupancy (tabular: Grade A/B rates, recent lease transactions, co-working rates, metro premium analysis)
8. Comparable Projects Analysis (land comparable sales, asset value comparison)
9. Demand Drivers & Tenant Mix (segments, target tenant profile)
10. Financial Projections (indicative rental income, capital value, cost assumptions)
11. Resources & Market Trend Sources (industry reports, portals, government, infrastructure)
12. Key Recommendations (priority-coded action items)

---

## Research Workflow (this session)

### Step 1 — Image OCR for Site Details

User sent a site sketch image. Extracted with tesseract:

```bash
tesseract /data/hermes/image_cache/img_xxx.jpg - 2>/dev/null
```

Output delivered:
- Survey total area: 5,796.400 sqm / 62,391.933 sqft
- 1 Acre & 17.291 Guntas (~1.175 Ac)
- Existing Garments Area: 618.534 sqm (6.113 Guntas)
- Front Open Area: 594.383 sqm (5.875 Guntas)

**Pitfall:** tesseract output on site sketches is noisy. Use `-` for stdout parsing. Multiple passes may be needed for layout-style images.

### Step 2 — Parallel Subagent Research (4 tasks)

| Task | Focus | Toolsets |
|------|-------|----------|
| A | BBMP building norms, FAR, TOD policy, setbacks, ground coverage | web |
| B | Current & upcoming developments within 3 km | web |
| C | Recent commercial lease transactions (2024–26) | web |
| D | Residential market context (already had from earlier research) | web |

**Pitfall:** Subagent files don't persist — always compile from subagent summaries directly in the main session. Do NOT rely on delegate_task to write files to the filesystem.

### Step 3 — BBMP Building Norms Research (Initial — WRONG path, corrected to KIADB)

**🔴 This was the WRONG path for this site.** The land turned out to be KIADB, not BBMP. BBMP numbers are documented here for reference only. The corrected KIADB norms are in `references/kiadb-building-norms-commercial.md`.

BBMP numbers (for comparison):

| Parameter | Value | Source |
|-----------|-------|--------|
| Zone | Commercial (C) — RMP-2031 | BDA Master Plan |
| Base FAR | 3.25 (RMP-2031) | BBMP Bye-laws |
| TOD Bonus FAR | +1.25 (50% of base, capped at 4.5) | GoK UDD 179/2018 |
| **Max Achievable FAR** | **4.50** | Combined |
| Max Built-up (1.23 Ac) | ~22,500 sqm (~2,42,000 sqft) | Derived |
| Ground Coverage | 45% max | BBMP Bye-laws |
| Setbacks | Front 12m, Sides 9m, Rear 9m | BBMP Bye-laws |
| Parking | ~300 ECS (basement G+2) | 1 ECS/75 sqm BUA |
| Metro Buffer | 10–15m no-construction zone | BMRCL |

**Search pattern for FAR/TOD research:**
```⚠️ FIRST, check if land is KIADB or BBMP. Use different search patterns below.

For BBMP land:
```
BBMP building bye-laws 2019 FAR commercial zone
RMP-2031 BDA master plan FAR table
Karnataka TOD policy UDD 179 2018 metro corridor bonus FAR
BBMP commercial building setbacks height restrictions
metro station buffer zone construction restrictions BBMP
```

For KIADB land:
```
KIADB building bye-laws 2019 amendment commercial FAR
KIADB premium FAR circular Whitefield industrial area
KIADB height relaxation commercial buildings 30m
KIADB vs BBMP building norms Bangalore
GoK UDD 179 TOD policy KIADB land applicability
```

### Step 4 — Competitor & Infrastructure Mapping

**Current developments** — Found 12 major projects within 3 km:
- Adjacent: Prestige Tech Park (~32L sqft, 95%+ occupancy)
- 1 km: Max Tech Park (~14L sqft)
- 1.5 km: ITPL (~51L sqft)
- 2 km: Ecoworld (~20L sqft), Phoenix Marketcity (~21L sqft)
- Total operational: ~1.58 Cr sqft within 3 km

**Infrastructure catalysts:**
- Metro Purple Line: ✅ Operational (already built into pricing)
- Metro Blue Line (to airport): 🏗 Under construction (estimated 2028)
- Peripheral Ring Road: 📝 DPR/Land acquisition stage
- NH 48 widening to 6 lanes: ✅ Substantially complete

**Search patterns:**
```
[Project Name] [City] office park size sqft occupancy
Whitefield Bangalore office market vacancy rate 2025 2026
Prestige Tech Park Kadubeesanahalli size sqft
ITPL Whitefield expansion Ascendas Phase 2
Peripheral Ring Road Bangalore status 2025 2026 land acquisition
Namma Metro Blue Line KR Puram airport status
```

### Step 5 — Lease Transaction Mining

Search industry reports for signed leases in the last 12–18 months:

```
Whitefield commercial lease signed 2025 2026 rent per sqft
Prestige Tech Park recent lease transactions rates
ITPL Whitefield new leasing 2025 2026
Bangalore office leasing whitefield GCC BFSI
```

### Step 6 — Compile IM Document

Written as comprehensive markdown with:
- Numbered sections (12)
- Every data point has a source URL or report name
- Tables for all structured data
- Financial projections clearly marked as "Indicative"
- Recommendations priority-coded (Immediate / Planning / DD Phase)

### Step 7 — Drive Upload + Cross-User Sharing

When the requesting user (Prakash, TG:psingh) has no GWS OAuth token:

```python
# Upload using Nishant's token
TOKEN_PATH = "the gws-vault daemon (no token files exist on disk — see api-references/google-workspace-api/references/token-access-canonical.md)"
drive = build("drive", "v3", credentials=creds)

# Upload
media = MediaFileUpload(local_path, mimetype="text/markdown", resumable=True)
uploaded = drive.files().create(
    body={"name": "YYYYMMDD_Project_Information_Memorandum.md"},
    media_body=media,
    fields="id, name, webViewLink"
).execute()

# Share with requesting user
drive.permissions().create(
    fileId=uploaded["id"],
    body={"type": "user", "role": "writer", "emailAddress": "psingh@draas.com"},
    sendNotificationEmail=False
).execute()
```

**Naming convention:** `YYYYMMDD_Project_Information_Memorandum.md`
**For Prakash with no token:** Upload via NDR's Drive (ndr), share with psingh@draas.com. Offer auth URL for future direct uploads.

---

## Key Pitfalls (This Session)

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| Subagent files don't persist | Subagent reports "file created" but it doesn't exist | Always compile from subagent summaries directly |
| Site sketch OCR is noisy | tesseract returns garbled numbers, scattered text | Run multiple passes; extract key numbers (area, guntas) manually |
| Land value vs capital value mismatch | User corrected: land rate and capital value were inconsistent. ₹4.5 Cr/acre land with ₹13,500/sqft capital value is only 2.5% of GDV, but actual market is 25-40% | Always cross-check: GDV = Plot × FAR × Capital Value/sqft. Land should be 25-40% of GDV. Verify against Karnataka guidance value (circle rate) for the area |
| User has no GWS token but wants Drive upload | Can't upload to user's Drive | Use NDR's token (ndr), share via permission, offer auth URL |
| Multiple OAuth retries fail | User reports "automation failed" repeatedly | Check agent.log for callback errors. In 2026, Prakash couldn't complete OAuth even after 4+ attempts from external browser |
| Markdown upload acceptable | Drive accepts .md files natively | Use `mimetype="text/markdown"`; render preview works |
| User rounds land area | User says "1.23 Ac" but survey shows 1.175 Ac | Note both; use precise survey data in all calculations, reference user's figure as reference |
| **KIADB vs BBMP land** | User corrects mid-session: land is KIADB not BBMP | Always verify land type FIRST: KIADB has FAR 3.00 (not 4.5), TOD not applicable, 40% coverage, 6m setbacks, KIADB Chief Architect approvals |
| HTML→Docs image insertion requires public access | Docs API returns "could not retrieve image" error | Make image `type: "anyone", role: "reader"` before inserting; use thumbnail URL format |
| Docs API reports empty paragraph text on HTML imports | `docs.documents().get()` returns text as empty strings | Document visually has content; use structural indices (table/heading positions) for image insertion |
| User wants Google Doc not markdown | User says "make a docs file with images" | Convert HTML→Google Docs via Drive API instead of sharing markdown |

---

## Deliverables From This Session

| Document | Format | Size | Drive ID |
|----------|--------|------|----------|
| R&D Document (v1) | Markdown | 9.1 KB | `1oXg11xKsVnGa91_CBuR-MbSdOIECutlG` |
| Information Memorandum | Markdown | 22.4 KB | `1dmUbC9UAY41-9bpBpjTvPwiWYuf34sNt` |
| IM (KIADB-corrected) | Google Doc | — | `1JccHaaJHtH4GviSp70v516EkOpbkIvnGWNz085crHXs` |

## Related References
- `references/kiadb-vs-bbmp-building-norms.md` — Full KIADB/BBMP building norms comparison for Bangalore commercial development
