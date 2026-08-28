# DRA Downtown Leasing Brochure — Worked Example (Jun 2026)

## Project
DRA Downtown — Commercial office building @ Egmore, Chennai
- Developer: DRA Homes
- Architect: Kharche & Associates (2/20 Shaffee Mohamed Road, Chennai)
- 8-page A4 landscape leasing brochure, HTML → PDF via weasyprint

## Source files uploaded to Drive folder

| File | Source | Notes |
|------|--------|-------|
| `DRA DOWNTOWN_Weekly_Progress_Report_May1st_Week.pdf` | User upload | 66.58% complete, July 2026 finish |
| `DRA DOWNTOWN_Weekly_Progress_Report_May1st_Week_v2.pdf` | User upload | Duplicate (same report) |
| `DRA_EGMORE_APPROVED_SITE_PLAN_22JUN24.pdf` | User upload | Site dimensions, schedule of joinery |
| `DRA_EGMORE_ARCH_PLANS_STILT_FLOOR_22JUN24.pdf` | User upload | 4 pages: stilt floor, single tenant, multi tenant, business suite |
| `DRA_EGMORE_ARCH_PLANS_BUSINESS_SUITE_24MAY24.pdf` | User upload | 1 page: business suite option |
| `DRA_EGMORE_APPROVAL_PLAN.pdf` | User upload | Additional approval plan |

## Data extracted from plans

**From Stilt Floor Plan (Sheet 01, 22/06/24):**
- Plot Area: 46,251.08 Sq.ft
- Total FSI Area: 91,353.48 Sq.ft
- Achievable FSI: 1.98
- Stilt Floor: 3,112.87 Sq.ft
- **Car parking: 71 (67 required)**
- **Bike parking: 304 (271 required)**
- Typical Floor Area: 88,240.60 Sq.ft
- Tentative Saleable Area: 93,633.74 Sq.ft

**From Weekly Progress Report (May 1st week 2026):**
- Site Area: 46,233 Sq.ft | BUA: 109,353 Sq.ft
- Budget: ₹42.84 Cr (within budget)
- Progress: 66.58% | Net paid: ₹21.11 Cr | Outstanding: ₹0.97 Cr
- Structural milestones all at 100% (foundation → terrace slab)
- External plastering: 90% | Internal finishes: 25%
- Start: Nov 2024 | Finish: July 2026 (21 months)
- Catchup plan active (manpower + multi-level execution)

## Key rendering technique

**Pages 2 & 3 fix — full-page images without cropping**

Original (broken):
```html
<section class="img-slide">
  <img src="file:///path.jpg" style="width:100%; height:100%; object-fit:cover;">
</section>
```
→ Image cropped at edges (user complaint)

Fixed:
```css
.img-slide {
  width: 297mm; height: 210mm;
  background-color: #0F1A33;
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center center;
}
```
```html
<section class="img-slide" style="background-image: url('file:///path.jpg');"></section>
```
→ Full image visible with navy fill bars

## Deliverable structure

| Page | Content |
|------|---------|
| 1 | Cover — render bg with dark overlay, DRA Downtown title, gold accents |
| 2 | Full-page artist impression render (background-size: contain) |
| 3 | Full-page progress photos from weekly report (4-photo layout) |
| 4 | Location — Google Maps screenshot + connectivity/neighbourhood/access |
| 5 | Project Snapshot — 4 KPI cards + 13-row data table + 6-office saleable table |
| 6 | Floor Plans — 4 card grid (Single Tenant / Multi Tenant / 2x Business Suite) |
| 7 | Parking (71 cars / 304 bikes) + STP (110 KLD SBR) + 100% power backup |
| 8 | Contact — enquiry bar + key stats + disclaimer |

## Components used
- **Brand palette:** navy `#0F1A33` / `#1B2A4A`, gold `#C9A84C` / `#D4B96A`, cream `#F8F6F0`
- **Font:** Calibri (via CSS font-family stack)
- **Maps:** Google Maps screenshot as `<img>` wrapped in `<a>` linking to `maps.app.goo.gl/SHORTLINK`
- **Conversion:** `/opt/hermes/.venv/bin/weasyprint input.html output.pdf`
- **Drive:** Sequential upload with delete-old-first + public permission
- **Source files:** All 6 source PDFs uploaded to same folder alongside brochure
