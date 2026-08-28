---
name: b2b-lead-research
description: "Multi-source external research to identify industry players, find key decision-makers at target companies, locate their contact information (LinkedIn, Twitter/X, email, ZoomInfo), and compile a structured, prioritized contact database for B2B outreach campaigns. Uses Jina Reader, DuckDuckGo Lite, Twitter/X scraping, News articles. Complements business-dossier (which is internal Drive+Gmail focused)."
version: 1.3.0
author: Hermes Agent
---

# B2B Lead Research — Multi-Source Contact Discovery & Outreach Database

Class-level skill for researching an industry ecosystem from scratch, identifying target companies, finding their key decision-makers, and compiling a structured contact database for a B2B outreach campaign.

## When to Use

- User wants to find contacts at specific companies or across an entire industry for a sales/partnership/real estate outreach campaign
- User asks to "research all players in [industry/city]" and find their decision-makers
- User wants LinkedIn profiles, Twitter handles, and/or email addresses of relevant people
- User names a specific property/location they want to pitch and needs a targeted contact list
- Any multi-source external research task that ends in a contact database for outreach

## User-Specific Conventions

For the current user (Nishant Ranka, CEO of DRA Group):

| Convention | Rule |
|---|---|
| **Company name** | Use **"DRA Group"** in ALL external communications — emails, WhatsApp, contact forms, LinkedIn, Twitter. Never "DRAAS" in outgoing messages. |
| **Coordinator POC** | Prakash Singh <psingh@draas.com>, +91 97399 32078. CC on every outreach email. Use his details (name, email, phone) when filling company contact forms — responses go to him. |
| **Phone on forms** | Enter **9739932078** (10 digits, no +91). Forms with a country-code prefix field strip the `+` before saving, truncating the last 3 digits. |
| **CEO/Founder emails** | Never include property details or PDF attachments. Short ask for referral/intro only. |
| **General company emails** | High-level teaser only, no property specs or PDF. Ask them to forward to the right team. |
| **TMP first rule** | All new docs go to the TMP Drive folder first, never Drive root. |

These are baked into the template examples below. If working for a different user, confirm their company name and coordinator details before starting outreach.

## Trigger Phrases

- "find contacts at..."
- "research [industry] players in [city]"
- "create a database of [target role] at [company type]"
- "find people talking about [topic]"
- "who handles [function] at [company]"
- "reach-out campaign for [property/product]"

## Core Workflow

### Phase 1 — Clarify the Target

Before searching, establish:

1. **Property/Product being offered** — exact location, specifications (size, height, special features), type of space
2. **Target industry/companies** — specific names the user knows, plus room to discover more
3. **Target roles** — who within each company makes the decisions (real estate head, expansion head, supply chain director, logistics manager, etc.)
4. **Target platforms** — LinkedIn, Twitter/X, email, ZoomInfo, SignalHire, ContactOut
5. **Geographic scope** — which city/region the target operates in

**Clarify ambiguous terms before searching.** Voice transcription often mangles brand/location names:
- "Gami Nagar" → clarify → likely "Gandhinagar"
- "Bill Gates" → likely "Blinkit"
- "Amsterdam Art" → likely "Instamart" (Swiggy Instamart)
- "Naikars" → phonetically closest brand in context = "Nature's Basket" (Godrej)
- "Swigia" → "Swiggy"

**When a brand name in a voice message doesn't match known companies, search for phonetically similar alternatives within the target industry context.** Keep a table of resolved mishearings in memory for the user.

**Also ask: "Are there other types of businesses that might need this?"** The user's initial ask often covers only the obvious players. Proactively suggest adjacent categories (retail, pharmacy, D2C, logistics, etc.) — the user will say "yes, search for ALL of them."

### Phase 2 — Map the Industry Players

Research all major players in the target industry using web searches and news articles:

```bash
# Use DuckDuckGo Lite for search (Google blocks automated queries)
curl -s "https://r.jina.ai/https://lite.duckduckgo.com/lite/?q=quick+commerce+dark+store+players+Bangalore+India+2026"
```

**For each player, capture:**
- Company name
- Parent company / ownership
- Market share / scale (dark store count, revenue, growth rate)
- Headquarters location (especially relevant for local decision-making)
- Whether they are expanding or contracting (signals urgency)
- Key recent news (funding, expansion plans, new product lines)

**Key insight:** Understanding who is growing fastest tells you who to prioritize. A company adding 100 stores/month is a hotter lead than one that's paused expansion.

**After mapping the obvious players, expand to adjacent categories.** The user will often say "are there others?" after seeing the initial list. Beat them to it by proactively researching:
- **Retail chains** (grocery, fashion, electronics) moving to quick delivery
- **Pharmacy chains** needing local fulfillment hubs
- **D2C brands** needing in-city warehousing
- **Cloud kitchens** needing ingredient storage hubs
- **3PL / Logistics companies** offering dark store services
- **Milk/daily subscription services**
- **Meat/fresh delivery** with cold chain needs

Search pattern for category expansion:
```
[City] dark store OR micro-fulfillment OR in-city warehouse [category]
[Category] companies Bangalore with dark stores
new grocery delivery apps Bangalore 2026
"dark store" "3PL" Bangalore
```

**Search pattern (generate variants for each player):**
```
[Company] [city] dark store warehouse expansion 2026
[Company] real estate team Bangalore
[Company] dark store count 2025 2026
"quick commerce" [city] warehouse logistics
```

### Phase 3 — Find Decision-Makers by Role

For each company, search for people in decision-making roles:

**Target roles for real estate/warehouse/dark store outreach:**
- Real Estate Head / Director of Real Estate
- Head of Expansion
- Supply Chain Director
- Head of Logistics / Warehousing
- Regional Operations Head (for the target city)
- CEO / Founder (for top-level approach)
- Chief Business Officer

**Search patterns:**
```
[Role] OR [Similar Role] [Company] LinkedIn
[Company] [+ "Head of" OR "Director"] + "Real Estate" + Bangalore
[Company] + "dark store" + LinkedIn + Manager
[Company] + real estate + expansion + team + LinkedIn
```

**Use DuckDuckGo Lite for LinkedIn profile discovery:**
```bash
curl -s "https://r.jina.ai/https://lite.duckduckgo.com/lite/?q=Zepto+real+estate+head+Bangalore+LinkedIn+dark+store+expansion"
```

DuckDuckGo returns LinkedIn profile links in its organic results even when LinkedIn itself blocks unauthenticated access.

### Phase 4 — Extract Contact Details

For each person found, extract:
- **Full name** and current designation at target company
- **LinkedIn profile URL** (the most useful contact — can DM or InMail)
- **Twitter/X handle** (public, can tweet/DM)
- **Email address** (from ZoomInfo, ContactOut, SignalHire, or company email pattern)
- **Phone number** (from ZoomInfo/SignalHire if available)
- **Location** (confirm they operate in the target city/region)
- **Relevance score** — how directly they match the target role

**LinkedIn profile search (no login needed for basic discovery):**
```bash
curl -s "https://r.jina.ai/https://lite.duckduckgo.com/lite/?q=Rohit+Kumar+Zepto+real+estate+LinkedIn"
```

The Jina Reader will surface the LinkedIn profile title, description, and URL without requiring login.

**Twitter/X profile search:**
```bash
# Search for company's official Twitter
curl -s "https://r.jina.ai/https://x.com/NousResearch" 2>&1 | head -200

# Search for specific people
curl -s "https://r.jina.ai/https://x.com/search?q=Aadit+Palicha+Zepto&f=live"
```

**Email discovery (ZoomInfo pattern):**
DuckDuckGo Lite searches for `[Name] [Company] email OR contact OR ZoomInfo` often surface pages like `contactout.com/[name]`, `zoominfo.com/p/[name]`, `signalhire.com/profiles/[name]`, and `rocketreach.co/[name]` which sometimes include partially redacted email addresses (e.g., `aadit@zeptonow.com`).

### Phase 5 — Identify Logistics Partners & Supporting Players

Beyond the direct target companies, identify:
- **Third-party logistics (3PL) partners** — companies that run dark stores or handle last-mile delivery for multiple platforms
- **Real estate brokers** specializing in warehousing/logistics in the target area
- **Industry analysts** who cover the sector (can provide intros)
- **Franchise operators** who run partner dark stores

Search pattern:
```
[City] warehouse logistics 3PL dark store
[City] warehouse broker logistics real estate
```

### Phase 6 — Research the Location / Property Value Proposition

Before the outreach, research your property's competitive advantages:

```
[Area name] [city] warehouse godown commercial hub
[Area name] dark store quick commerce
[Area name] rent godown per sqft
```

**Key data points to gather:**
- Location advantages (centrality, connectivity, transit access)
- Typical rental rates for warehouse space in the area
- Whether any competitors have dark stores nearby (validation of demand)
- Demographic density within 2-3 km delivery radius
- Road conditions, width, and accessibility for delivery vehicles

### Phase 6.5 — Consolidate & Enhance Existing Research

When the user already HAS research (a previous spreadsheet, contact list, or database) and wants it extended, merged, or enhanced:

**Step 0 — Enrich lead lists with external research**

If the spreadsheet contains lead names and phone numbers and the user wants external enrichment, use **Firecrawl-backed web_search** as the primary tool — it returns full LinkedIn headlines (company + role), RocketReach listings (email/phone), and Crunchbase pages, not just search snippets. DuckDuckGo (ddgs) is fallback when Firecrawl is unavailable.

1. **Primary: web_search (Firecrawl)** — search `f'"{clean_name}" {phone}'` via `from hermes_tools import web_search`. Firecrawl returns rendered page content, so you get LinkedIn profiles with actual job titles (e.g. "Senior Security Architect at Axis Bank") and RocketReach listings with contact info. Expect ~85% hit rate with much richer detail per result. See `references/lead-enrichment-chat-audit.md` for the complete search loop.
2. **Use phone + name together** — the phone number anchors the search when combined with a quoted name. Phone-only searches occasionally surface RocketReach/similar directories but less reliable.
3. **Secondary: x_search** — use when web_search returns ambiguous results or you need X/Twitter-specific profile info (bio, recent posts, follower count). Especially useful for verifying common-name leads.
4. **Tertiary: ddgs (DuckDuckGo)** — use only when Firecrawl is unavailable. Slower, snippet-based, ~80% hit rate. See reference file for ddgs search loop.
5. **Distinctive names** (full names like "Santosh Mitra Sharma", "Srinivasa Rao Duddupudi") are more likely to yield unique results than common first names
6. **Anonymous identifiers** (chat user IDs like "rcqjxdtg", "cjmizdqj") cannot be researched — skip
7. **Compile findings into a new column** — format as compact text: `[LinkedIn] Company - Role | [RocketReach] phone/email` or "No additional info found"
8. **Use sheets_get and sheets_update** via gws_skill_bridge to write the new column back. See the sheets_get parameter naming pitfall below for correct argument names (use `sheet_id=`, not `spreadsheet_id`)
4. **Distinctive names** (full names like "Santosh Mitra Sharma", "Srinivasa Rao Duddupudi") are more likely to yield results than common first names
5. **Anonymous identifiers** (chat user IDs like "rcqjxdtg", "cjmizdqj") cannot be researched — skip
6. **Compile findings into a new column** — format as compact text: `[LinkedIn] Company - Role | [Instagram] @handle` or "No additional info found"
7. **Use sheets_get and sheets_update** via gws_skill_bridge to write the new column back. See the sheets_get parameter naming pitfall below for correct argument names (use `sheet_id=`, not `spreadsheet_id`)

**Step 1 — Locate existing sources on Drive**
Search Drive for spreadsheets, docs, or markdown files related to the topic/property:
```python
from tools.gws_auth import build_service
drive = build_service('drive', 'v3', service_name='google-draas')
results = drive.files().list(
    q="fullText contains 'dark store' and fullText contains 'Gandhinagar'",
    fields="files(id, name, mimeType, webViewLink)",
    pageSize=20
).execute()
```

**Step 2 — Compare versions**
Load each sheet and compare entries by company name. Identify:
- Companies unique to each version
- Companies present in both (check if any fields differ)
- V2 may be a subset of V1 — verify rather than assume

```python
sheets = build_service('sheets', 'v4', service_name='google-draas')
v1 = sheets.spreadsheets().values().get(spreadsheetId=ID, range='A:Z').execute().get('values', [])
# Compare using company name as key
v1_set = {row[1].strip().lower() for row in v1[1:] if len(row) > 1}
```

**Step 3 — Add strategy columns before merging**
Don't just merge raw data. Add columns that the user's next step needs:
- **Communication Strategy** — per-category pitch direction (e.g., Quick Commerce → "Urgent — high growth, needs central BLR dark store space", 3PL → "B2B pitch — last-mile fulfillment hub")
- **Suggested Channel Type** — per-contact recommendation (Email, LinkedIn DM, Twitter DM, Phone) based on available contact info and company culture

```python
category_strategy = {
    "Quick Commerce": ["Urgent — high growth, needs central BLR dark store space", "LinkedIn DM / Email"],
    "3PL/Logistics": ["B2B pitch — last-mile fulfillment hub in central BLR", "Email / Website"],
    "Pharmacy": ["Dark store / pharmacy hub near central business district", "LinkedIn DM"],
    ...
}
```

**Step 4 — Create a "V3 - Merged" tab**
Write the consolidated data to a new tab in the existing spreadsheet rather than creating a separate file. This keeps everything in one place:

```python
# Create new sheet tab
sheets.spreadsheets().batchUpdate(spreadsheetId=ID, body={
    "requests": [{"addSheet": {"properties": {"title": "V3 - Merged"}}}]
}).execute()

# Write merged data 
sheets.spreadsheets().values().update(
    spreadsheetId=ID,
    range="V3 - Merged!A1",
    valueInputOption="RAW",
    body={"values": merged_rows}
).execute()
```

**Step 5 — Deduplicate intelligently**
- If V2 is purely a subset of V1 (every V2 company exists in V1 with identical fields), V3 = V1 + new strategy columns
- If V2 has unique companies or enriched fields on shared companies, merge the best of both
- Flag and mark stale/outdated contacts from old research (e.g., callers from 2009)

**⚠️ Pitfall:** Old research (retail tenant call lists from 2009-2010) may still sit on Drive alongside current dark store research. Don't merge them into the outreach database — keep them separate as historical records.

### Phase 6.6 — Vendor Review Research (Due Diligence on Service Providers)

When the user asks for reviews/ratings on vendors or service providers they might HIRE (BPO, telecalling teams, agencies, contractors) — a different goal from finding outreach targets, same research muscle. Worked example: real estate pre-sales telecalling vendor shortlist — see `references/vendor-review-telecalling-2026.md`.

**Step 1 — Per-vendor review-platform sweep via web_search.** For each vendor, search `"[Vendor] reviews rating"` and the platform names. Key platforms and what they tell you:

| Platform | Type | Tells you |
|---|---|---|
| Clutch, GoodFirms, G2 | Client reviews | Delivery quality, communication, domain knowledge |
| Sitejabber, ResellerRatings | Client reviews | Volume + star spread |
| Trustpilot | Client reviews | Often thin for Indian BPOs (1–5 reviews) — note low review count |
| Glassdoor, AmbitionBox, Indeed | Employee reviews | Culture, attrition risk, payroll reliability |
| JustDial | Local Indian | Ratings across web (often 3.9ish) |
| SoftwareSuggest, OutsourceAccelerator | Service listings | Unclaimed profiles = ZERO verified reviews (see Step 5) |

**Step 2 — Distinguish CLIENT vs EMPLOYEE reviews. Report both.** Client reviews = delivery quality; employee reviews = churn risk (a vendor with 3.5/5 Glassdoor may have high attrition → quality drift on YOUR campaign). A vendor with 4.9/5 employee satisfaction (e.g. Go4Customer) is a lower-attrition bet.

**Step 3 — Social sentiment via x_search.** Query `[Vendor] reviews experience` and `[Vendor] [service] real estate experience`. Look for: payroll complaints, mass layoffs, scam mentions (red flags), official handles + case studies (positioning). X is usually sparse for Indian BPOs — one payment complaint or one layoff thread carries disproportionate weight, cite it.

**Step 4 — Parent-company check.** Search `[Vendor] owned by / parent company`. Outsource2India is wholly owned by Flatworld Solutions — same review base, don't double-count or treat as separate options. This also explains pricing differences (premium brand vs. delivery brand).

**Step 5 — Unclaimed-profile red flag.** A vendor with an UNCLAIMED SoftwareSuggest/GoodFirms profile and 0 client reviews (e.g. VMG BPO) = no verified client trail. Surface this explicitly and require client references before shortlisting — niche fit is not evidence.

**Step 6 — Filter job-listing noise.** For service-provider discovery, most search hits are JOB LISTINGS (Naukri, Indeed, Instagram "we're hiring telecaller" posts) — those prove demand, not supply. Filter them out; real vendors have service pages (`/telecaller-for-real-estate`, `/industries/real-estate`). Also distinguish "AI calling platform" (₹10–18/call) from "human telecalling team" (monthly/performance) — user's mental model may be either.

**Step 7 — Deliverable.** Per-vendor table: client-review score (platform + count), employee-review score, X/social sentiment, red flags, pricing model. End with a verdict ("best verified client reputation" vs "best all-rounder") and a next action — comparison sheet on Drive or enquiry email asking for real-estate client references.



Structure as a markdown file with:

```markdown
# [Industry] Contact Database — [City]
## Property: [Space description] at [Location]

## 📊 Market Overview (table)
| Metric | Value |
|--------|-------|
| Key stat 1 | data |
| Key stat 2 | data |

## 🏪 Player Profiles & Key Contacts

### 1. [Company Name]
- **HQ:** [City]
- **Market Share:** X%
- **Dark Stores / Scale:** N
- **Key Insight:** Why they're worth targeting

| Name | Designation | Relevance | LinkedIn / Contact |
|------|------------|-----------|-------------------|
| **Name** | Role | Why they matter | [Link](url) / email |

### 2. [Next Company]
...

## 📍 Location Advantages (table or bullets)

## ✅ Prioritized Reach-Out Order
| Priority | Company | Contact | Why |
|----------|---------|---------|-----|
| ⭐⭐⭐ | [Company] | [Name] | Reason |
| ⭐⭐ | [Company] | [Name] | Reason |
| ⭐ | [Company] | [Name] | Reason |

## 📋 Suggested Outreach Template

> Subject: [Relevant subject line]
>
> Hi [Name],
> ...
```

### Phase 7.5 — Build a Property Offer Document (HTML with Drive Asset Hyperlinks)

When the user asks for a deliverable that combines the property description + contact database + all supporting documents into a single reference document, build a **self-contained HTML file** with hyperlinks to every Drive asset.

This is different from a PDF brochure (use `html-presentations` skill for that). This is a **working document** — a hub that links to all source material so the user can click through to plans, photos, and data sheets.

**Step 1 — Gather all Drive assets for the property**

Search the property's Drive folder and parent folders for:
- Area statements (PDF)
- Floor plans (PDF, DWG)
- Stall/shop numbering diagrams (PDF)
- Surveys and site sketches (PDF)
- Photos and images (JPG, PNG)
- Legal documents (lease deeds, agreements)
- Market research (rental comps, broker lists)
- Previous outreach databases

```python
folder_id = "1DPZ3gw_cGY5FpuFYhZwqjFjPICG1ypQK"
files = drive.files().list(
    q=f"'{folder_id}' in parents",
    fields="files(id, name, mimeType, webViewLink, modifiedTime)",
    pageSize=50
).execute()
```

**Step 2 — Check Google Photos for a property album**

Google Photos Library API may not be enabled in the project. If it fails, search Drive for images and note the limitation:
```python
# Try Photos API (may fail — fall back gracefully)
try:
    photos = build_service('photoslibrary', 'v1', service_name='google-draas')
    albums = photos.albums().list(pageSize=50).execute()
except Exception:
    # Photos API not enabled — tell the user
    pass
```

Also search the user's personal Google account if they mention one:
```python
photos2 = build_service('photoslibrary', 'v1', service_name='google-gmail')
```

**Step 3 — Design the HTML**

Use a single-column, card-based layout with:
- **Hero header** — property name, location, key stat badges
- **Property overview card** — area, floors, dimensions (extract from area statement)
- **Document library** — grouped by type (Plans, Legal, Photos, Market Data), each with a clickable Drive link
- **Location advantages** — connectivity, catchment area, demographic context
- **Contact database table** — priority-tiered (HIGHEST / HIGH / MEDIUM) with company, contact, role, channel
- **Communication strategy** — grouped by category with message angles
- **Next steps** — what to do first

**Key design rules:**
- Card-based layout with clean borders and subtle shadows
- Color-code priority tiers (red border for HIGHEST, orange for HIGH, blue for MEDIUM)
- Every Drive asset gets a clickable hyperlink — the HTML is a hub, not a self-contained document
- Use emoji icons for visual scanning (📏 plans, 📊 data, ⚖️ legal, 📸 photos)
- Keep it single-file (no external CSS/JS) so it opens in any browser

**Step 4 — Upload to the property's Drive folder**

```python
from googleapiclient.http import MediaFileUpload

media = MediaFileUpload('/tmp/property_offer.html', mimetype='text/html')
file = drive.files().create(body={
    'name': 'PropertyName Offer Reach-out — Category.html',
    'parents': [PROPERTY_FOLDER_ID],
}, media_body=media, fields='id, name, webViewLink').execute()
```

**Naming convention:** `[Property] Offer Reach-out — [Target Category].html`
Example: `Gandhinagar Offer Reach-out — Dark Stores.html`

**Step 5 — Offer the user next actions**
After delivering the HTML, offer to:
- Adjust content or messaging per contact type
- Begin outreach (draft emails/LinkedIn messages for top-tier contacts)
- Expand to additional contact categories
- Add more property assets (photos from phone, renders etc.)

**⚠️ Pitfall — f-string CSS conflict:** If your HTML template contains CSS with `{` curly braces, build the CSS as a separate string variable and interpolate it. See `html-presentations` skill for the pattern.

**⚠️ Pitfall — Google Photos API:** May not be enabled. Don't let a failed Photos API call block the deliverable — fall back to Drive images and note it to the user.

### Phase 8 — Deliver to User

Send the database as:
1. A saved markdown file (path) for the user's reference
2. Optionally as a Google Sheet or document on Drive
3. Provide a prioritized reach-out order so the user knows who to contact first

### Phase 9 — Channel-Specific Outreach Message Construction

For each high-priority prospect, craft **channel-optimized messages** — never a generic template reused across channels. Each channel has different norms:

**Email (formal, information-rich):**
- **Subject line:** `[Topic] — [Location], [City]` — specific, not spammy
- **Opening:** Name-drop the property's key differentiator (double-height, central location, cold storage, etc.)
- **Body:** 3-4 sentences max. State: (1) what you have, (2) why it's relevant to them (their dark store scale, expansion plans), (3) why it's a good fit (location, specs), (4) open for a call/site visit
- **Closing:** Low friction — "Happy to share details or arrange a visit"
- **CC the coordinator** on EVERY outreach email (e.g., Prakash Singh <psingh@draas.com>) — they are the point of contact for all follow-through and coordination
- **Pattern:**
  > Subject: Warehouse Space — Gandhinagar, Bangalore
  >
  > Hi [Name],
  >
  > I own a [property spec] in Gandhinagar, central Bangalore near Majestic. Noticed [Company] is [relevant expansion detail] — our space could serve as a [fulfillment hub / dark store / distribution point] for this area.
  >
  > [1-2 sentences of spec relevance: size, height, location advantage]
  >
  > Open to sharing details or arranging a site visit at your convenience.

**⚠️ CEO/Founder outreach etiquette (DRA Group rule):**
When the only contact found for a target company is the CEO/Co-founder:
- **DO NOT** send property details, specs, or any pitch content
- **DO NOT** attach the property PDF
- **DO** start apologetically: acknowledge they are the wrong recipient and get spammed
- **DO** ask for a referral: "connect me with your [function] team / in-city warehouse in-charge"
- Keep it to 2-3 sentences. No details — just the ask for an intro
- CC the coordinator (e.g., Prakash) as the point of contact for follow-through

**Pattern:**
> Hi [Name],
>
> Apologies for writing to you directly — I know you must get a thousand such emails. I tried to find the right person for [function/topic] at [Company] but couldn't locate a direct contact.
>
> We are a [city]-based [industry] firm and have something that could be relevant to [Company]'s [expansion/work in area]. Would it be possible to connect me with whoever handles [function] on your team?
>
> My colleague [Name] (CC'd) will coordinate further.
>
> Thank you,

Store this as a draft in Gmail — it stays there until the right contact is found.

**LinkedIn DM (semi-formal, conversational):**
- **Opening:** Reference their role and company expansion context
- **Body:** 2-3 sentences. Lighter than email, skip formalities
- **Call to action:** "Let me know if this is worth a conversation"
- **Pattern:**
  > Hi [Name] — saw you handle [Company]'s real estate expansion in [City]. We have a [property spec] in [location] that could work as a [dark store / warehouse] for your network. If relevant, happy to share specifics.

**Twitter/X DM (brief, high-signal):**
- **Opening:** Direct, no preamble
- **Body:** 1-2 sentences max
- **Call to action:** single next step
- **Pattern:**
  > Hi [Name] — [Company] expanding [scale] in [City]? We have [spec] space in [location], central [City]. DM me if worth a look.

**WhatsApp (if phone number available):**
- **Opening:** Friendly, reference any prior connection
- **Body:** 2-3 sentences
- **Pattern:**
  > Hi [Name], this is Nishant from DRA Group. We have a warehouse space in Gandhinagar — central Bangalore, double-height container structure. Noticed [Company] is expanding [dark stores / fulfillment] in this area. Would it make sense to share the specs?

  *(For messages sent on behalf of the coordinator — Prakash — use: "Hi [Name], this is Prakash from DRA Group. Nishant Ranka suggested I reach out...")*

**Key rules for all channels:**
- Always reference the recipient's specific role/company context — never send blind
- Lead with THEIR need (expansion, coverage gap) not YOUR property features
- Keep it to 1 paragraph per channel (shortest for Twitter, longest for email)
- End with an open question, not a close-ended "interested?" — invite a reply

### Phase 10 — Prioritized Outreach Scheduling

Create a ranked outreach plan by day:

```
## 📅 10-Day Outreach Plan

| Day | Channel | Target | Action |
|-----|---------|--------|--------|
| 1 | Email | #1 priority — fastest growing, most urgent need | Send full pitch |
| 1 | LinkedIn DM | #2 priority — key decision maker accessible | Send connection request + note |
| 2 | Twitter DM | #3 priority — CEO/Founder who tweets publicly | Direct message |
| 2 | Email | #4 priority — established player, medium urgency | Send full pitch |
| 3 | LinkedIn DM | #5 priority — local office near property | Send note |
| ... | ... | ... | ... |
```

**Ranking criteria (priority score):**
1. **Growth velocity** — stores added per month (highest weight)
2. **Decision-maker accessibility** — CEO email known > LinkedIn accessible > cold email
3. **Location relevance** — already operating in target area vs. expanding into it
4. **Urgency** — known expansion plan in next 3-6 months vs. speculative
5. **Aggregator potential** — 3PL that can bring multiple brands (Shadowfax > single brand)

**Pattern after creating the plan:**
Present the top 5 as an action-ready shortlist with the exact message ready to send, then offer the full plan for remaining prospects.

### Phase 10.5 — Second-Wave General Company Email Outreach

After sending individual pitches to known contacts, always research and send a **second wave to general company email addresses** (info@, contact@, customerservice@, etc.) asking for referral to the right internal team.

**When to do this:** The user will often say "since we only have 2-3 email addresses, why don't we search the websites of all targets and find general contact emails?"

**Workflow:**

1. **Visit each target company's website** using `browser_navigate` to find contact pages
2. **Look for contact emails** in:
   - Footer of homepage (common: info@, hello@, contact@)
   - Dedicated "Contact Us" page
   - "Partner with Us" / "Become a Partner" page
   - "For Partners" section (especially for delivery/warehouse companies)
   - Use `browser_console` with JS expression `document.body.innerText.match(/[\w.+-]+@[\w-]+\.[\w.]+/g)` to extract all emails from the page at once
3. **If no public email** found, note "contact form only" — prepare the message for copy-paste
4. **Draft a referral-seeking email** — no property details, just:
   - Brief intro (who you are, what you have at a high level)
   - Request to forward to the relevant department
   - "My colleague [Name] (CC'd) will coordinate"
5. **CC the coordinator** on every draft (e.g., Prakash Singh <psingh@draas.com>)
6. **Keep the message generic** — one template works for all general-contact emails

**Tone for general email outreach:**
> Hi Team at [Company],
>
> I'm [Name] from [Firm], a [city]-based [industry] firm.
>
> We have a [property type] in [location] that could be relevant to [Company]'s [expansion/operations] in this area.
>
> I'm not sure who handles [specific function] on your team, so writing here. Could you please forward this to the right person or department?
>
> My colleague [Name] (CC'd) will coordinate further.
>
> Best regards,

**Common general email patterns found in the wild:**
| Company | Found Email | Where Found |
|---------|------------|-------------|
| Blinkit | info@blinkit.com | Footer of website |
| BigBasket | customerservice@bigbasket.com | Contact Us page |
| Shadowfax | hello@shadowfax.in | Known |
| StoreSpace | hello@storespace.in | Common pattern |
| LoadShare | partnerships@loadshare.net | Common pattern |

**Do NOT** include property details (size, photos, floor plans) in general emails — they may be forwarded out of context or ignored as spam. Keep it to a high-level teaser.

**Do NOT** include the property PDF attachment in general emails — the attachment is reserved for direct contact with known decision-makers.

**⚠️ Pitfall — Companies with no public email:** Swiggy, Flipkart, Zepto, PharmEasy, Nykaa, Licious, and many large consumer companies do not list a public email for business inquiries. For these, recommend:
- LinkedIn DM to relevant team members (not general contact)
- **Website contact form submissions (see Phase 10.6)**
- Twitter/X DM to company account

---

### Phase 10.6 — Website Contact Form Filling (Browser-Automated)

For companies that do NOT have a public business-inquiry email but DO have a "Contact Us" form on their website, use browser tools to fill and submit the form directly.

**Two approaches available:**

| Approach | When to Use | How |
|---|---|---|
| **browser_use_cloud** (autonomous) | Form is standard (name, email, phone, message) | Give it a goal prompt describing what to fill and submit. Handles navigation, typing, and clicking autonomously. Faster for single-page forms. |
| **Step-by-step browser tools** (manual) | Form is unusual (Google Forms, accordions, modals, SPAs) | Use `browser_navigate` → `browser_snapshot` → `browser_type` / `browser_console` JS for each field. More control for complex forms. |

**Try browser_use_cloud first** for standard contact forms. Fall back to step-by-step tools when it gets stuck or paused for human input.

**When to do this:** After Phase 10.5 email search, for any target where no public email was found. This is often faster than searching for individual decision-makers.

**Contact info pattern (use the project coordinator's details):**
- Name: Prakash Singh
- Email: psingh@draas.com
- Company: DRA Group
- Phone: 9739932078 (Prakash's number — strip the +91 prefix for Indian forms)
- Role/Occupation: Consultant
- Coordinator CC: Prakash Singh <psingh@draas.com> (responses go to him)

**Standardized message for dark store / warehouse / real estate outreach:**
> Hi team,
>
> I'm Prakash Singh from DRA Group, a Bangalore real estate firm. We have a commercial space in Gandhinagar, Bangalore (500m from Majestic, ~7,200 sq.ft.) available for a dark store / warehouse. Please connect me with your business development head for Bangalore warehouse real estate.
>
> Best regards,
> Prakash Singh | DRA Group | psingh@draas.com

**Workflow:**

**Step 1 — Find the contact form URL**
Navigate to the company website and look for:
- `/contact`, `/contact-us`, `/contactus`
- Footer links: "Contact Us", "Partner With Us", "Get in Touch"
- Dedicated partner pages: `/partner-with-us`, `/partners`, `/become-a-partner`
- For logistics/warehouse companies specifically: B2B / Enterprise pages

**Step 2 — Identify form fields**
Use `browser_snapshot` to see the accessibility tree. If fields show as `[disabled]` (common with Google Forms and some SPA forms), they may still be interactive — test by clicking and typing.

**If the form fields aren't visible in the snapshot, use `browser_console` with JS to enumerate them:**
```javascript
// List all visible input fields with their selectors
let inputs = document.querySelectorAll('input:not([type="hidden"]), textarea');
JSON.stringify(Array.from(inputs).map((el, i) => ({
  index: i,
  tag: el.tagName, type: el.type, name: el.name,
  placeholder: el.placeholder || '',
  id: el.id || ''
})), null, 2)
```

**Step 3 — Fill text fields**
Use `browser_type(ref, text)` for standard inputs. The ref IDs are shown in square brackets in the snapshot output (e.g., `@e28`).

**Step 4 — Handle special form elements via browser_console**

**Radio buttons** that don't respond to `browser_click` (common in Google Forms):
```javascript
// Click by ARIA role
document.querySelector('div[role="radio"][aria-label="Consultant"]').click()
// Verify it worked
document.querySelector('div[role="radio"][aria-label="Consultant"]').getAttribute('aria-checked')
```

**Submit buttons** that don't fire with `browser_click` (common in Google Forms, React forms):
```javascript
// Try by text content
document.querySelector('span:has(> .NPEfkd)').click()
// Or by button text
Array.from(document.querySelectorAll('button, div[role="button"]'))
  .find(el => el.textContent.trim() === 'Submit')?.click()
```

**Fill fields by ID directly** (for forms in modals or SPAs where type doesn't work):
```javascript
document.querySelector('#form-field-name').value = 'Prakash Singh'
// Trigger any listeners (optional — often not needed for basic forms)
```

**Step 5 — Verify submission**
Check the page state after submit:
- **Google Forms:** Success page shows "Submit another response" link and the heading
- **Generic contact forms:** Check for success messages, redirects, or button state change
- **Button shows "Sending…" with `[disabled]`:** Submission is in progress — good sign

**Step 6 — Document results**
Record what was submitted and for which company. If no form exists, note the best alternative contact method found.

**Known contact form types and their behaviors:**

| Type | Signal | Handling |
|------|--------|----------|
| **Google Forms** | "Sign in to Google" link at top; fields show `[disabled]` in snapshot | Use JS console for radio buttons and submit. Accessibility tree lies — fields ARE interactive. |
| **Elementor/WordPress** | Well-structured divs with `#form-field-*` IDs | Fills easily via `browser_type` or direct JS value assignment |
| **Accordion-based (e.g., LoadShare)** | Multiple section buttons (General Enquiry, Warehousing, etc.) | Click the relevant accordion header first to expand the form region |
| **Modal/dialog popups** | Appears after clicking "Partner With Us" or "Get Started" | Click the CTA button first — the form is in the dialog. Use `browser_snapshot` after to see the new fields |
| **SPA forms (React/Vue)** | Dynamic rendering, fields may not have stable IDs | Use JS console `document.querySelectorAll('input')` to enumerate and fill |
| **HubSpot forms** | Inline iframes, complex DOM | May need JS injection into the iframe context. Skip if too complex — note the company |

**Known real-estate-specific forms found in the wild (valuable shortcuts):**

| Company | Form Type | URL | Notes |
|---------|-----------|-----|-------|
| **Swiggy Instamart** | **Google Form "Rent Your Property"** | `https://docs.google.com/forms/d/e/1FAIpQLSftnUKOA73mxg15M0LyNnBYk2CvW56I7UJkfAJTQOJR-H_kQQ/viewform` | Direct dark store property submission form. Fields: Name, Contact, Identity (Self-Owner/Consultant), City, Locality, Lat/Lng, Address, Pin Code, Sq.ft., Floor, Rental expectation. Requirements: Min 2,000 sq.ft., 20 kVA, truck access, 20+ bike parking, 2 washrooms. ⚠️ Phone field expects 10-digit Indian mobile — any +91 prefix gets stripped silently, dropping the last 3 digits. |
| **Delhivery** | B2B Enterprises form | On their `/solutions/b2b-enterprises` page | Simple 4-field form: Name, Company, Email, Phone. No message/textarea. |
| **StoreSpace** | WordPress Elementor form | `/contact-us/` | Fields: Name, Designation, Company Name, Phone, Official Email, Product Category. No message field. |
| **LoadShare** | Multiple accordion forms | `/contact` | General Enquiry, First Mile/Last Mile, Line Haul, Warehousing, Partner sections. Click the accordion header to expand the relevant form. Each has: Full Name, Work Email, Company, Phone, Vertical dropdown, How can we help? textarea. The Warehousing accordion opens the most relevant form for property outreach. |

**⚠️ Phone number formatting pitfalls:**
- Indian forms with a country-code prefix field (e.g., fixed "+91" display) will **strip the "+" from " +919739932078"** — you end up with only `919739932` (9 digits, missing the last 3)
- **Fix:** Enter the phone number WITHOUT the +91 prefix: just `9739932078`
- Some forms expect exactly 10 digits of the Indian mobile number, not 12 with country code
- **Google Forms phone fields** also silently strip the "+91" prefix, leaving a 9-digit truncated number. Always enter raw `9739932078` format.
- **Always check the submitted value** in the snapshot before clicking Submit — look for alert messages near the phone field, or verify the field's value attribute via `browser_console` after typing
- **Test pattern:** After typing a phone number, snapshot the page or use `browser_console` with `document.querySelector('input[type="tel"]').value` to confirm the visible value isn't truncated

**⚠️ Known websites WITHOUT contact forms (use alternative channels):**

| Company | Alternative Channel |
|---------|-------------------|
| **Xpressbees** | Email customercare@xpressbees.com or call +91 (020) 4911 6100. No generic contact form — only franchise partner flows. |
| **Pikndel** | "Partner With Us" dialog is for ecommerce brands (asks for order volume) — not relevant for property owners. Skip or use LinkedIn. |
| **Flipkart (including Minutes)** | No public form for warehouse partnerships. Flipkart Minutes is invite-only for sellers. Email partnerservices@flipkart.com. |
| **Apollo Pharmacy** | Emails only: customerservice@apollopharmacy.org (corporate), brandlisting@apollopharmacy.org, contactusnow@apollopharmacy.org |
| **Licious** | Email talktous@licious.com or call 1800-4190-786 |
| **PharmEasy** | Use LinkedIn outreach (Gaurav Chandak or similar) — no working contact form on website |
| **BigBasket** | Email customerservice@bigbasket.com — no dedicated contact form found |
| **Nykaa / Croma / More Retail / Spencer's** | Use LinkedIn outreach to the specific decision-makers listed in the V3 contact sheet |

**Also check for dedicated "Partner With Us" pages before giving up:** Some logistics companies (Xpressbees, LoadShare, Delhivery) route business inquiries through separate partner flows rather than a generic contact page. These often have their own specialized forms.

### Phase 10.7 — Document Results & Update Outreach Compilation

After completing all form submissions and email research, update the outreach reference document with:

1. **✅ Submitted** — which forms were successfully filled and with what info
2. **❌ No form found** — companies where only alternative channels exist
3. **📋 Already drafted** — email drafts ready to review
4. **📋 Copy-paste required** — LinkedIn / Twitter messages prepared

This keeps the outreach document as the single source of truth, preventing duplicate work in future sessions.

### ⚠️ Pitfall — Never claim search results you haven't obtained

**This is a correctness-critical pitfall.** When a user asks you to research a list of leads by name, phone number, or any identifier, you must perform the actual searches and report what the tools returned. Never:

- Claim a lead has "no public presence" or "an X profile exists" without having run the search
- Attribute a profession, industry, or background to a lead based on a common-name match
- Say "our search shows / we found" when the search wasn't actually executed
- Combine multiple common-name matches into a composite profile that doesn't belong to any one person

**Why this matters:** Common Indian names (Manas, Shardul, Raj, Amit, Sandeep, Ravi, etc.) each match dozens of unrelated people across X, LinkedIn, and the web. A lead named "Manas Paul" could be a startup founder, an energy policy analyst, a political volunteer in Jamshedpur, or an HR professional — and you have no way to pick the right one without the lead's location, company, or a phone number linkable via web search.

**What to do instead:**
- **Run the actual search** (x_search, web_extract, or whatever tool is available) and report what it returned verbatim
- **If the tool returned ambiguous results** (multiple profiles for the same name, or no clear match to the lead's known context), say so honestly: "X returned N profiles for this name; none clearly match without location/company context"
- **If no tool can search the available identifier** (e.g., phone number without a reverse-lookup API), say "I can't search phone numbers with the tools currently configured — this needs [specific setup]"
- **If the identifier is too generic to research** (first name only, chat user ID, short name like "AD" or "Thenu"), note it and skip rather than guessing

**The litmus test:** If you haven't called a search tool and inspected the result, you don't know anything about that lead. Report honestly that the data was not found or the search was not possible.

### ⚠️ Pitfall — gws_skill_bridge sheets_get parameter naming

When calling `gws_skill_bridge.call('sheets_get', ...)`, the underlying function expects `sheet_id` and `range` as parameter names (SimpleNamespace attributes), not `spreadsheet_id`/`spreadsheetId` or `ranges`. This is because the bridge creates a SimpleNamespace from kwargs and the skill's function reads `args.sheet_id` and `args.range`.

**Wrong (causes AttributeError: has no attribute 'sheet_id'):**
```python
call('sheets_get', service_name='google-draas', spreadsheet_id='abc123', ranges=['Sheet1!A:Z'])
```

**Correct:**
```python
call('sheets_get', service_name='google-draas', sheet_id='abc123', range='Sheet1!A:Z')
```

Note the difference from the Google SDK's Python client which uses `spreadsheetId` and `range` as parameter names. The bridge wraps it differently.

### ⚠️ Pitfall — gws_skill_bridge drive_search requires raw_query=True and max=N

When calling `gws_skill_bridge.call('drive_search', ...)`, the underlying `google_api.drive_search()` function wraps query strings in `fullText contains '...'` by default — unless you pass `raw_query=True`. It also requires `max=N` for page size. Both are SimpleNamespace attributes set from kwargs.

**Wrong (causes AttributeError: has no attribute 'raw_query'):**
```python
call('drive_search', service_name='google-draas', query="name contains 'Dark Store'")
```

**Correct:**
```python
call('drive_search', service_name='google-draas', query="name contains 'Dark Store'", raw_query=True, max=50)
```

Without `raw_query=True`, the query becomes `fullText contains "name contains 'Dark Store'"` — a free-text search, not a file-name filter. Without `max=N`, the function errors on `args.max`.

Also note: `drive_search` from `gws_skill_bridge` returns a JSON **string** (printed to stdout), not a Python dict — the skill functions print their output. The bridge captures this via `contextlib.redirect_stdout`. Parse with `json.loads()` if you need structured access.

---

## Phase 11 — Multi-Channel Outreach Compilation & Delivery

After the contact database is finalized and channel-specific messages are drafted (Phase 9), compile everything into an actionable outreach package.

This phase bridges strategy → execution: the user gets a single reference document with ALL messages organized by channel and priority, plus any API-created drafts ready to review.

### Step 1 — Classify each contact by reachable channel

Segment the contact list by what's actionable via tools vs. what needs manual copy-paste:

| Classification | What It Means | Action |
|---|---|---|
| **📧 Email (actionable)** | Email address known + Gmail API available | Create a Gmail draft via `draft_create` |
| **🐦 Twitter DM (actionable if xurl installed)** | @handle known | Send via `xurl dm @handle "message"` or prepare for copy-paste |
| **💼 LinkedIn DM (copy-paste only)** | LinkedIn profile URL known | Prepare message text for user to paste |
| **🔍 LinkedIn Search (copy-paste)** | Company+role known, no profile URL | User searches LinkedIn, then pastes message |
| **🌐 Website Form (copy-paste)** | No individual contact, only company website | Prepare a standardized message for the contact form |
| **📱 WhatsApp (actionable)** | Phone number known | Generate `wa.me` link via `whatsapp_link` tool |

### Step 2 — Create actionable drafts where tools permit

**Email drafts** — create LIVE Gmail drafts via `gws_skill_bridge.call('draft_create', ...)`:

```python
from tools.gws_skill_bridge import call
call('draft_create', service_name='google-draas',
     to='contact@company.com',
     subject='Subject Line — Property, City',
     body='Email body with property details...',
     html=False)
```

⚠️ **Remember:** You can only CREATE drafts — NEVER send. The rule is hard-coded: `gmail_send` and `gmail_reply` are blocked operations in `gws_skill_bridge` and raise `PermissionError`.

⚠️ **Attachments:** `call('draft_create', ...)` does NOT support file attachments. For emails that need a PDF/brochure attached, use the Gmail API directly via `build_service('gmail', 'v1')` with MIMEMultipart.

⚠️ **Verify after creating:** After creating any draft whose body mentions an attached file, RE-VERIFY the draft via `drafts().get(format='full')` that the MIME structure actually contains the attachment. The body text saying "I have attached..." is NOT proof — `draft_create` silently produces no attachments.

```python
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import base64

gmail = build_service('gmail', 'v1', service_name='google-draas')
msg = MIMEMultipart('mixed')
msg['To'] = recipient
msg['Cc'] = coordinator
msg['Subject'] = subject
msg['From'] = 'Your Name <email@company.com>'

# Body
body = MIMEText(body_text, 'plain')
msg.attach(body)

# Attachment
with open(pdf_path, 'rb') as f:
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename="{pdf_name}"')
    msg.attach(part)

raw = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')
draft = gmail.users().drafts().create(userId='me', body={'message': {'raw': raw}}).execute()
```

⚠️ **Note:** `build_service('gmail', 'v1')` works in `execute_code()` (which has vault socket access) but NOT in `terminal()` subprocesses. Always use `execute_code` for MIME-based Gmail operations.

**Twitter DMs** — if `xurl` CLI is installed and configured:
```bash
xurl dm @handle "Brief DM message with property pitch"
```

If `xurl` is not installed, prepare the message text for copy-paste and note it.

**WhatsApp links** — use the registered `whatsapp_link` tool directly.

### Step 3 — Compile a single Google Doc with all messages

Create a Google Doc that serves as the user's copy-paste reference:

**Document title:** `[Property] Outreach — All Messages (DD MMM YYYY)`

**Section hierarchy:**
1. **📧 Priority 1 — Email Drafts (Ready in Gmail)** — Subject + full body text, status badge
2. **🐦 Priority 2 — Twitter/X DMs (Copy-Paste)** — Handle + message
3. **💼 Priority 3 — LinkedIn InMail Messages (Copy-Paste)** — Profile URL + full InMail
4. **🔍 Priority 4 — LinkedIn Search Required** — Table of companies + common template
5. **🌐 Priority 5 — Website Contact Forms** — Standardized message + URL list
6. **📊 Summary Table** — Channel | Count | Status

**Key Doc design rules:**
- Use HTML formatting with `<h2>`, `<blockquote>`, `<table>`
- Color-code priority tiers (red/orange/blue) matching the contact sheet
- Status badges: ✅ draft created, 📋 copy-paste, 🔍 need search
- Every message is channel-appropriate (email = formal pitch, LinkedIn = conversational, Twitter = brief)

### Step 4 — Move to TMP folder

Per Nishant's hard rule, all new documents go to TMP folder first:

```python
from tools.gws_auth import build_service
drive = build_service('drive', 'v3', service_name='google-draas')

tmp_folders = drive.files().list(
    q="name='TMP' and mimeType='application/vnd.google-apps.folder' and trashed=false",
    fields="files(id, name)"
).execute()
tmp_id = tmp_folders['files'][0]['id']

file = drive.files().get(fileId=DOC_ID, fields="parents").execute()
drive.files().update(
    fileId=DOC_ID,
    addParents=tmp_id,
    removeParents=",".join(file.get('parents', []))
).execute()
```

### Step 5 — Deliver the summary to the user

Present as a structured summary:
- **Document link** — the Google Doc URL
- **What's actionable now** — Gmail Drafts to review, LinkedIn messages to paste
- **What needs manual setup** — Twitter DMs (xurl install), LinkedIn search contacts
- **For emails:** "Go to Gmail → Drafts → review & send" — never send yourself
- **Coordination handoff line** — Every outreach email should include a clear handoff to the coordinator: *"My colleague [Name] (CC'd) will coordinate next steps — whether it's a site visit, a discussion on specifications, or anything needed to take this forward."* This ensures the loop doesn't die with the first email.

### Reference Files

- `references/gandhinagar-darkstore-outreach-messages.md` — Worked example: multi-channel outreach compilation for Gandhinagar Mamata Apartments dark store campaign. 30 contacts across 5 channels with message texts, priority tiers, and channel-specific formatting.

## Research Tool Reference

| Tool | URL Pattern / Invocation | Use Case |
|------|-------------------------|----------|
| **Firecrawl/web_search (PRIMARY)** | `from hermes_tools import web_search` — call `web_search(query)` directly in execute_code | **Best for lead enrichment.** Returns rendered page content — LinkedIn profiles with full job titles + company names, RocketReach listings, Crunchbase pages. Use `name + phone` or `name + city` as query. Requires FIRECRAWL_API_KEY in .env. |
| **Jina Reader** | `curl -s "https://r.jina.ai/URL"` | Full page content extraction from any URL (Twitter, news, LinkedIn search results) — bypasses paywalls and login walls for public content |
| **DuckDuckGo Lite** | `curl -s "https://r.jina.ai/https://lite.duckduckgo.com/lite/?q=QUERY"` | Web search when Google returns 429 (rate limited). DuckDuckGo doesn't block automated queries |
| **Twitter/X (curl)** | `curl -s "https://r.jina.ai/https://x.com/ACCOUNT"` | Read Twitter profile page + recent posts without login. Also: search.x.com for keyword search |
| **x_search (Hermes tool)** | Call `x_search` directly — available as a top-level tool when the `x_search` toolset is enabled | Search X/Twitter for profiles, posts, and discussions by name, handle, or keyword. Returns structured results with bio, follower count, recent posts. More reliable than curl-scraping for name-based lead profiling. Works even when web_search (Firecrawl) is not configured. |
| **News articles** | `curl -s "https://r.jina.ai/https://example-news.com/article"` | Full article text extraction without paywall |
| **DuckDuckGo (direct)** | `curl -s "https://lite.duckduckgo.com/lite/?q=..."` | Raw search results page (minimal HTML, parse with grep/head) |
| **ddgs (Python library)** | `from ddgs import DDGS` — call `DDGS().text(query, max_results=3)` | Fallback when Firecrawl unavailable. No API key needed. Indexes LinkedIn, social media. Slower, snippet-based. |
| **Browser website visit** | `browser_navigate` + `browser_console` with JS email regex | Visit company website's contact page, footer, or "Partner" section to find public contact emails. Use `browser_console` with `document.body.innerText.match(/[\\w.+-]+@[\\w-]+\\.[\\w.]+/g)` to extract emails from rendered page. Best for: info@, hello@, contact@, careers@ — emails that are visible on the site but not indexed by search engines. |

### Checking Search Tool Availability

Before beginning research, verify which tools are available in your current session:

- **web_search / web_extract** — uses Firecrawl. Check FIRECRAWL_API_KEY in .env or try `from hermes_tools import web_search; result = web_search("test")` in execute_code. When configured, this is the **primary recommendation** for lead enrichment — it returns full rendered page content (LinkedIn profiles, RocketReach) rather than snippets.
- **x_search** — available when the `x_search` toolset is enabled (check in toolsets config)
- **DuckDuckGo / ddgs** — fallback when Firecrawl is unavailable. Requires `uv pip install ddgs`. No API key needed.

**Priority order for lead enrichment:** web_search (Firecrawl) → x_search → ddgs.

## Parallel Research via delegate_task

For large campaigns covering multiple companies or multiple research dimensions, use `delegate_task` to fan out:

```json
// Research 3 companies in parallel
[
  {"goal": "Research Company A — find real estate head, LinkedIn/Twitter", "toolsets": ["web", "terminal"]},
  {"goal": "Research Company B — find real estate head, LinkedIn/Twitter", "toolsets": ["web", "terminal"]},
  {"goal": "Research Company C — find real estate head, LinkedIn/Twitter", "toolsets": ["web", "terminal"]}
]
```

Or for multiple dimensions on the same campaign:
```json
[
  {"goal": "Research all major industry players in [city]", "toolsets": ["web", "terminal"]},
  {"goal": "Search Twitter for people discussing [topic]", "toolsets": ["x_search"]},
  {"goal": "Research [area/location] for target viability", "toolsets": ["web", "terminal"]}
]
```

**x_search toolset for subagents:** When using delegate_task subagents for X/Twitter research, pass `"toolsets": ["x_search"]`. Note that x_search subagents may time out after 600s if rate-limited or if many names are searched sequentially — keep batch sizes small (10-15 names max per subagent).

## Pitfalls

- **Google blocks automated searches** with 429 errors. Always use DuckDuckGo Lite as the primary search engine for automated queries. Google can be used for specific article/company lookups via Jina Reader.
- **LinkedIn requires login** for full profiles. DuckDuckGo Lite search results still surface LinkedIn profile pages with their title, description headline, and URL — which is often enough to identify the person and their role.
- **Jina Reader can't bypass Twitter's login wall** for the main feed. It CAN read individual tweet pages and the initial profile page with pinned tweet. Use the profile page for bio/follower count, and search for specific tweets.
- **ZoomInfo/ContactOut/SignalHire** show redacted emails (d***@company.com) unless you have a paid subscription. Still useful for confirming the email format/domain.
- **Deduplicate across sources.** The same person may appear in LinkedIn search, ZoomInfo, and Twitter. Use full name + company as the dedupe key.
- **Name misspellings in voice transcriptions.** The user may say "Bill Gates" when they mean "Blinkit," or "Gami Nagar" when they mean "Gandhinagar." Clarify before researching.
- **Not all companies have a real estate team in the target city.** Some (like Blinkit) operate centrally from Gurugram. Note the company HQ and adjust the outreach approach accordingly.
- **delegate_task web research returns summaries only** — subagent search results are NOT returned. Structure subagent goals to produce structured text summaries, not file outputs. Compile the database yourself in the main session from subagent summaries.
- **Subagent file outputs need a known path.** If you instruct a subagent to write results to a file, specify an absolute path under /opt/data/ and read it back with read_file after the subagent completes. Subagents can write files but you must know where.
- **Multiple subagents produce multiple async messages.** When using 3+ parallel delegate_task calls, their results arrive as separate messages at unpredictable times. Structure each subagent's goal to be self-contained so you can merge results from each independently. Use a todo list to track subagent completion status.
- **Jina Reader may truncate long content.** Feedparser (RSS) results, Twitter feeds, and long article pages may be truncated. Use `head -200` to see the beginning and `| tail -200` for the end.
- **Property portal URLs return 403.** 99acres, MagicBricks, NoBroker block automated access. Use Jina Reader's DuckDuckGo search results (snippets with pricing) as secondary data.

## Reference Files

- `references/blinkit-zepto-instamart-darkstore-contacts.md` — Worked example: quick commerce dark store contact database for Bangalore, with prioritized reach-out order for Gandhinagar property. Covers all 7 major players with specific contacts found.
- `references/complete-darkstore-prospects-all-categories.md` — Expanded worked example: complete category expansion covering 51 companies across 11 categories (quick commerce, grocery retail, pharmacy, meat/fresh, fashion, electronics, cloud kitchens, D2C, milk subscription, 3PL/logistics, other). Includes voice transcription corrections table. Use this as a reference when the user says "are there others?" after the initial round.
- `references/gandhinagar-darkstore-offer-consolidation.md` — Full lifecycle follow-through: merging existing V1/V2 outreach databases into V3 with strategy columns, building a property offer HTML document with hyperlinks to all Drive assets, and communication strategy per vertical. Covers the "already have research, now consolidate and package" workflow.
- `references/website-contact-form-filling-darkstore.md` — Session-level reference: concrete URLs, field names, and techniques for filling contact forms on 20+ target company websites using browser tools. Covers Swiggy Instamart Google Form submission, accordion forms (LoadShare), Elementor forms (StoreSpace), and fallback channels for companies with no contact form. Anchors the Phase 10.6 workflow with real examples.
- `references/gandhinagar-darkstore-outreach-messages.md` — Worked example: multi-channel outreach compilation for Gandhinagar Mamata Apartments dark store campaign. 30 contacts across 5 channels with message texts, priority tiers, and channel-specific formatting.
- `references/lead-enrichment-chat-audit.md` — Lead enrichment from CRM/chat audit spreadsheets: what identifiers are researchable, x_search patterns by confidence tier, interpreting ambiguous results, phone number limitation, and a worked example (Ranka Udaya Chat Audit, Jul 2026). Anchors the Phase 6.5 workflow with real session findings.
## Related Skills

- `business-dossier` — Internal (Drive+Gmail) intelligence gathering for known entities. Use this skill for external research, business-dossier for internal document analysis.
- `real-estate-investor-research` — Property-level investment research (competitor pricing, FAR, location analysis). Use when the need is investor presentation, not contact discovery.
- `real-estate-leads-tracking` — Portal lead extraction from Gmail (inbound leads). Different from outbound B2B contact research.
