# Gandhinagar Dark Store Offer — Database Consolidation & Property Offer Document (Jul 2026)

**Property:** Mamta A&B, Gandhinagar, Bangalore
**Target:** Dark Store / Quick Commerce / 3PL / Pharmacy / Grocery tenants
**Deliverable:** Merged V3 outreach database + HTML offer document with Drive asset hyperlinks

## Context

The user had existing research on Google Drive — a "Dark Store Outreach Database - Gandhinagar" spreadsheet in two versions (V1 = 45 contacts, V2 = 32 contacts). He wanted:
1. Both versions analyzed and merged into one consolidated V3 with communication strategy per contact
2. All Gandhinagar Mamta A&B property documents collected from Drive
3. A single HTML offer document hyperlinking to every asset
4. Google Photos checked for a Gandhinagar album

## What was found on Drive

### Gandhinagar Mamta folder (`1DPZ3gw_cGY5FpuFYhZwqjFjPICG1ypQK`)
- Detailed Internal Survey 29JAN14.dwg
- GANDHINAGAR_09.06.2012.dwg
- GANDHINAGAR AREA CALCULATION.xlsx
- STALL NUMBERING GF.pdf
- STALL NUMBERING IN BASEMENT.pdf
- GANDHINAGAR (Area- 647.66 Sqmt).pdf
- Archived Classic Site — gandhinagar-serviced-offices.zip

### Related Drive files (not in the folder)
- Survey Sketch of Local Area No.80, Gandhi Nagar.pdf
- Lease Deed dtd 10-11-23-IDC Mamata B.pdf
- Gandhinagar Commercial Rentals spreadsheet (market comps)
- Gandhinagar Rental — Brokers spreadsheet
- RND for Glenwood Gardens and Mamta A&B spreadsheet
- Caller list of Gandhinagar — Mamatha — GF/B space for rent (old 2025 call log)
- Gandhinagar spreadsheet (old 2009 retail/film distributor lead list — kept separate)
- SDV_0226mamta.JPG (site photo)

### Photos
- Google Photos Library API was NOT enabled in the project — both ndr@draas.com and nishantranka@gmail.com returned `UnknownApiNameOrVersion`. Only one site photo found on Drive.

## V1 vs V2 Analysis

| Metric | V1 | V2 |
|--------|----|----|
| Rows (incl. header) | 46 | 33 |
| Actual contacts | 45 | 32 |
| Unique companies (not in the other) | 0 (all V1 rows are category summary rows, not actual contacts missing from V2) | 0 |
| Shared companies | 27 identical entries | 27 identical entries |

**Conclusion:** V2 is a strict subset of V1. All shared entries are identical field-by-field. V3 = V1 + strategy columns.

## V3 Structure

| Column | Content |
|--------|---------|
| A-M | (Original columns unchanged) Company, Category, Contact, Designation, Twitter, LinkedIn, Email/Phone, Address, Scale, Priority, Best Channel, Suggested Message |
| N | **Communication Strategy** — per-category pitch direction |
| O | **Suggested Channel Type** — recommended approach per contact |

### Category-to-Strategy Mapping

| Category | Strategy | Recommended Channel |
|----------|----------|-------------------|
| Quick Commerce | Urgent — high growth, needs central BLR dark store space | LinkedIn DM (RE heads) / Twitter DM (CXOs) / Email |
| 3PL/Logistics | B2B pitch — last-mile fulfillment hub in central BLR | Email to business teams / website contact forms |
| Pharmacy | Dark store / pharmacy hub near CBD | LinkedIn DM to Supply Chain heads |
| Grocery Retail | In-city micro-fulfillment for quick delivery | LinkedIn DM / Phone call |
| Fashion/Beauty/D2C | Central BLR distribution point | LinkedIn DM |
| Electronics | Distribution hub for central BLR | LinkedIn DM |

## HTML Offer Document

Delivered as a single self-contained HTML file uploaded to the Gandhinagar Mamta folder:

**`Gandhinagar Offer Reach-out — Dark Stores.html`**
→ https://drive.google.com/file/d/18xL7Lf3MxxbIrnphizmd1Hv0q4FXtsmH/view

### Document structure
1. **Hero header** — "Gandhinagar · Mamta A&B — In-city Warehouse & Dark Store Opportunity"
2. **Property overview** — 647.66 sqm (~6,970 sqft), GF+Basement, near Majestic
3. **Document library** — grouped by type (Plans & Surveys, Site Context, Legal & Lease) with hyperlinks
4. **Location advantages** — connectivity, catchment, double-height potential
5. **Outreach DB by priority tier** — HIGHEST / HIGH / MEDIUM tables
6. **Communication strategy** — per-category with message angles
7. **Next steps**

## Communication Strategy Per Vertical

### Quick Commerce (Swiggy, Zepto, Blinkit, Flipkart Minutes, BigBasket)
**Channel:** LinkedIn DM (RE heads) / Twitter DM (CXOs) / Email where available
**Message angle:** "Central BLR dark store. 6,970 sqft, double-height, 500m from Majestic. Ready for fit-out."

### 3PL / Logistics (Shadowfax, Delhivery, Navata, StoreSpace, WareIQ)
**Channel:** Email to business teams / website contact forms
**Message angle:** "In-city fulfillment hub at Gandhinagar. Cut last-mile delivery time by 40% for central BLR."

### Pharmacy (PharmEasy, Apollo)
**Channel:** LinkedIn DM to Supply Chain heads
**Message angle:** "Pharmacy hub near Majestic for medicine delivery across central BLR."

### Cloud Kitchen / D2C / Others
**Channel:** Website contact + LinkedIn DM
**Message angle:** Central location ideal for delivery radius.

## Key HIGHEST-Priority Contacts

| Company | Contact | Role | Channel | Details |
|---------|---------|------|---------|---------|
| Shadowfax | Business Team | Launching 100 dark stores | Email | hello@shadowfax.in |
| Swiggy Instamart | Chethan S Gowda | Regional Head RE — South India | LinkedIn DM | linkedin.com/in/chethan07 |
| Zepto | Rohit Kumar | Associate Director RE | LinkedIn DM | linkedin.com/in/rohit-kumar-168a3b42 |
| Flipkart Minutes | Hemant Badri | SVP Supply Chain | Twitter DM | @BadriHemant |
| Swiggy Instamart | Mahesh Patwardhan | Regional Head Leasing & Infra | LinkedIn DM | linkedin.com/in/mahesh-patwardhan-6356a766 |
| Blinkit | Albinder Singh Dhindsa | Group CEO, Eternal | Twitter DM | @albinder |
| Zepto | Aadit Palicha | Co-founder & CEO | Email | aadit@zeptonow.com |

## Tools Used

- **Google Sheets API** — read both versions, add "V3 - Merged" tab, write 690 cells
- **Google Drive API** — search all Gandhinagar/Mamta related files, list folder contents, upload HTML
- **Google People API** — find Bhuvanesh's phone number for WhatsApp link
- **Google Photos Library API** — attempted but not enabled in project (fallback handled)
- **whatsapp_link tool** — generated wa.me links for outreach
- **gws_skill_bridge** — gmail operations (search, get, draft_reply_create) — note: `gmail_search` needs `max=` not `max_results=`
- **build_service** — fallback for Drive searches when `gws_skill_bridge.drive_search` has attribute errors (`raw_query` missing)

## What Was NOT Done (User Decisions Pending)

1. Google Photos search was blocked by API permissions — user needs to enable Photos Library API or share album links manually
2. No outreach was actually sent — user wanted to review the HTML offer document first, then decide per-contact messaging
3. Old historical call lists (2009-era retail/film distributor contacts) were left as-is — not merged into the active outreach DB
