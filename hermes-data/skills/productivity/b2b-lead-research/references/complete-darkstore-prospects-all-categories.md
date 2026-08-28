# Complete Dark Store Contact Database — Bangalore (Worked Example: Category Expansion)

**Date:** July 2, 2026
**Property:** Warehouse/Godown at Gandhinagar, Bangalore (near Majestic/KBS)
**Campaign:** Outbound B2B lease offering — expanded to 11 categories after initial quick commerce research
**Key Lesson:** The user's first ask covered only quick commerce. After delivering that, they said "are there others?" — prompting a second wave covering 8 additional categories, finding 40+ more companies.

## Categories Covered

| # | Category | Companies Found | Key Contacts |
|---|----------|----------------|--------------|
| 1 | Quick Commerce | 6 (Blinkit, Zepto, Instamart, BigBasket, Flipkart Minutes, Amazon Now) | Chethan Gowda, Rohit Kumar, Hemant Badri |
| 2 | Grocery Retail | 6 (Nature's Basket, Spencer's, More Retail, Reliance Smart, DMart, StarQuik) | Suresh V S (Head of Dark Store Ops, StarQuik) |
| 3 | Pharmacy | 4 (Apollo, 1mg, PharmEasy, NetMeds) | Pan Singh Bisht (Apollo) |
| 4 | Meat/Fresh Delivery | 3 (Licious, FreshToHome, Country Delight) | Co-founders at Licious |
| 5 | Fashion & Beauty | 6 (Myntra, Nykaa, Meesho, Pantaloons, Shoppers Stop, Westside) | Manoj Jaiswal (Nykaa) |
| 6 | Electronics Retail | 5 (Reliance Digital, Croma, Poorvika, Sangeetha, BigC) | Kumar Gaurav (Croma) |
| 7 | Cloud Kitchens | 4 (Rebel Foods, FreshMenu, Box8, EatFit) | Akash Gowda (Rebel) |
| 8 | D2C Brands | 5 (Bombay Shaving Co, Wakefit, Urban Company, Whole Truth, Mamaearth) | Vishal Kumar (BSC) |
| 9 | Milk/Subscription | 2 (DailyNinja, Milkbasket) | DailyNinja → BigBasket |
| 10 | 3PL / Logistics | 7 (Shadowfax, Delhivery, Ecom Express, Xpressbees, DTDC, LoadShare, Porter) | cs@shadowfax.in |
| 11 | Other | 2 (Origin, Zippee) | Origin: 40 Fresh Pods |

## Key Insight

The expanded search revealed **More Retail** (Aditya Birla) — an overlooked player with **45 existing dark stores + 100 more planned**, HQ in Bangalore, yet nobody talks about them. Similarly, **StarQuik (Tata)** has a dedicated Head of Dark Store Operations. These "quiet" players often have more immediate need than headline-grabbing startups.

## Voice Transcription Corrections Table

| User Said | What They Meant | Notes |
|-----------|----------------|-------|
| "Bill Gates" | Blinkit | Quick commerce player |
| "Zato" | Zepto | Quick commerce player |
| "Amsterdam Art" | Instamart (Swiggy Instamart) | Quick commerce |
| "Swigia" | Swiggy | Food delivery + quick commerce |
| "Gami Nagar" | Gandhinagar | Bangalore locality |
| "Naikars" | Nature's Basket (Godrej) | Grocery retail chain |

## Master Contact Database Structure

See `quick_commerce_contacts_database.md` for the quick-commerce-only version.
The full expanded database (51 companies, 11 categories) is at `/opt/data/complete_dark_store_contacts_master.md` on the server.

## Tools Used

- Jina Reader via curl for web page content extraction
- DuckDuckGo Lite for search (Google returned 429)
- Twitter/X profile scraping via Jina Reader
- LinkedIn profile discovery via DuckDuckGo Lite search results
- ZoomInfo / ContactOut / SignalHire for email discovery
- 3 parallel delegate_task subagents for: (a) company research, (b) Twitter search, (c) location research

## Expanded Deliverable Format (Jul 2026 session)

The June 2026 research was extended in July with:
- **Custom outreach messages per channel** — unique email, LinkedIn DM, and Twitter DM for each of the 56 prospects (not a single global template)
- **Google Sheet delivery** — full database exported as a formatted spreadsheet (32 rows in "All Prospects" tab + category breakdown in second tab) with columns: Rank, Company, Category, Contact Name, Designation, Twitter, LinkedIn, Email/Phone, Address, Dark Store Scale, Priority, Best Channel, Suggested Message
- **10-day outreach plan** — day-by-day ranked schedule starting with Shadowfax (aggregator → multiple brands), Swiggy Instamart (385+ stores South India), Zepto (Bangalore-based RE director), Flipkart Minutes (100 stores/month), PharmEasy (office walking distance from property)
- **Drive delivery option** — when user asks for spreadsheet in their "TMP folder on the drive", create via Google Sheets API → provide link. OAuth needs to be configured with correct telegram_id (ndr for Nishant) via `gws_auth.build_service`
