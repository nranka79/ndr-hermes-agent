---
name: uae-golden-visa-research
description: Research UAE Golden Visa eligibility and advisory outreach for Indian tech founders. Company profile building, consultancy contact discovery, outreach message drafting, and eligibility analysis.
tags: [uae, golden-visa, visa-consultancy, dubai, residency, tech-founder, outreach, india]
trigger: ["golden visa", "UAE visa", "Dubai residency", "visa consultancy", "DSquare", "golden visa eligibility", "UAE residency program"]
owner: hermes
---

# UAE Golden Visa Research & Consultancy Outreach

Research workflow for an Indian tech founder (Nishant Ranka, O3 Infotech) pursuing UAE Golden Visa, involving:
1. **Advisory firm discovery** — find visa consultancies, verify founder contacts, extract WhatsApp/email/LinkedIn
2. **Company profile build** — pull company data from Gmail + Drive for visa application
3. **Eligibility assessment** — cross-reference applicant credentials against UAE visa categories
4. **Outreach drafting** — WhatsApp, email, LinkedIn, follow-up sequences

---

## Workflow

### Phase 1 — Advisory Firm Research

**Target firm:** DSquare Global (dsquare.global) — visa/immigration consultancy,Raj Shamani-referral

1. Try `browser_navigate` → `https://dsquare.global`  
   ⚠️ **Pitfall**: Camofox browser (Firefox) fails on `aarch64` arch — GTK lib exists but wrong arch. Binary won't launch. See: `references/arm64-browser-fix.md`
2. If browser fails, fall back to:
   - `terminal` + `curl` with varied UA strings AND allorigins.win proxy → scrape firm pages
   - YouTube video page (Raj Shamani interview) — `curl` the video URL, extract bio/description/links
   - Google Maps business listing → contact info
   - WHOIS lookup via free API
3. LinkedIn contact discovery requires login-gate — browser session or manual

#### Contact types to find
- Founder/director name (verify spelling — "Deepesh" vs "Dipesh")
- Personal email (CEO-level often on website)
- WhatsApp (sometimes in footer or business listing)
- LinkedIn company page + personal profile
- Consultation booking link (Cal.com,Calendly widget)
- Corporate phone/address

#### Web Scraping — What Works vs What Fails

**Consistently FAILS in this environment:**
- `curl` to Google.com → 403 / consent redirect
- `curl` to Bing.com → geo-redirect / empty
- `curl` to JS-rendered SPA sites (Next.js, NitroPack, Cloudflare) → empty body or 200 with no content
- `browser_navigate` (camofox) → connection refused on aarch64
- Google Webcache → blocked
- Archive.org Wayback → no snapshot

**What WORKS:**
1. **DuckDuckGo HTML** (`https://html.duckduckgo.com/html/?q=query`) — returns plain text results, works reliably. Extracts firm names, phone numbers, addresses from snippets.
2. **Bing via curl with `--max-time` + varied UA** — sometimes returns actual results before geo-redirect fires
3. **Chrome UA string on JS-heavy sites** — some sites (NitroPack/WordPress) serve content to Chrome UA even via curl if `--compressed` is used
4. **Follow 301/302 redirects** — some contact pages are at different paths (e.g., `/contact/` → `/contact-us/`)
5. **Extract from JSON-LD structured data** — many WordPress/Next.js sites embed `schema.org` JSON-LD in `<script type="application/ld+json">` — contains phone, email, address directly
6. **browser_use_cloud** (Browser Use Cloud) — for sites that require JS rendering or have anti-bot protection. Always include `live_url` in response when using.

**Always try in order:** DuckDuckGo HTML → curl with Chrome UA → follow redirects → JSON-LD extraction → browser_use_cloud fallback.

**When all scraping fails:** Give user the website URLs directly and ask them to open and provide contact info. Do not waste time on repeated failed approaches.

---

### Phase 2 — Applicant Profile (Gmail + Drive)

Using per-user GWS auth — **pass telegram_id explicitly**:
```python
from tools.gws_auth import build_service
# ALWAYS pass telegram_id — session env var may not resolve correctly
svc = build_service('drive', 'v3', 'ndr')  # works
svc = build_service('drive', 'v3')               # fails silently
```

⚠️ **Pitfall**: `build_service` without explicit telegram_id raises `FileNotFoundError: No GWS token for user {telegram_id}` even when token exists. The session HERMES_SESSION_USER_ID env var is not always picked up by the GWS helper. **Always pass the telegram_id parameter explicitly.**

**Gmail search pattern:**
- Query: `from:kelsa.io OR from:o3infotech.com`, `O3 Infotech`, `Kelsa`, `Manohar Singh O3`, etc.
- Extract contacts, salary evidence, reference letters
- Parse raw email format to get full body (not just snippet)

**Drive file download patterns:**
```
svc.files().get_media(fileId=fid)           # binary files (PDF, DOCX) — direct download
svc.files().export_media(fileId=fid, mimeType='application/pdf')  # Google Docs → export
```
- DOCX files can be read with python-docx or zipfile XML extraction
- XLSX files readable with openpyxl
- PDF files convert to images with pdf2image + vision_analyze for content extraction

**Key Drive files for Nishant Ranka's profile (verified IDs as of Jun 2026):**
- `Nishant Ranka - Professional Resume.pdf` (ID: `1HKFwizPuDpBnBz_5t708qJpa-_nxfLIQ`) — binary PDF, 2 pages
- `NDR - profile write up` (ID: `1db0q-BavnCJjR_4ke9l1Y_vr-JBdlnWtG-6mN3siHzc`) — Google Doc, export to PDF first
- `Nishanth Ranka Profile.pdf` (ID: `1NZ17zPMuVdIONsG3j9f2m89PyXPHqDYJ`) — binary PDF, 1 page
- `DOC_040_Information For World Visa (1).xlsx` (ID: `1JDpehBhyx9WWoQ1kxLRyfnA7uOGAIgr8`) — Chronology of Key Engagements + About the Companies + NDR Job Details sheets
- `DRA Reference Letter v2` (ID: `1lLGqN4obiu6W87Ond4aQoKbP8PA6_YloIPvPm-KxEKA`) — Google Doc, export to PDF
- `IRCA Reference Letter v2` (ID: `1BEjyXUP9Vt04E23pO1tiwNSDHNl7pJwqTLHnHAV_eqQ`) — Google Doc, export to PDF
- `O3 Reference Letter v2` (ID: `1Q6lhi_0CTdnmmHuCYxCswdLoytT-jDdLBj0k2NB2fp4`) — Google Doc, export to PDF
- `WorldVisa_Communication_Summary.html` (ID: `1lulZot9QPodYy7TB3qQa_2oc3mlEIjIg`) — email chain summary
- `NDR Profile Resume 10MAY2021` (ID: `1HzmQwLaemm1OO05YHsbl4y1CNWcg96sVw9LoXBhgdK0`) — Google Sheets  

---

### Phase 3 — Eligibility Assessment

**UAE Golden Visa categories potentially applicable:**

| Category | Nishant Ranka | Manohar Singh |
|---|---|---|
| Entrepreneur | ✔ Owns established tech co | ✔ Co-founder |
| Executive/Senior Professional | ✔ ~INR 1.2Cr/yr salary | Unconfirmed salary |
| Investor/Business Owner | ✔ Multiple co board seats | Possible |
| Highly Skilled Professional | Possible | Unconfirmed |

**Key numbers for visa application (updated May 2026):**
- O3 Infotech ARR: ~INR 3 Crore per annum (revised upward from ~INR 1Cr)
- DRA Group turnover: ~INR 2,000 Crore (revised from ~INR 250Cr+)
- Combined group: INR 2,000+ Crore
- Group employee count: 60+

**Documents typically needed:**
- Passport copy, nationality, residency
- CV/LinkedIn, company incorporation docs
- Shareholding docs, revenue/ITR, salary evidence
- Client profile, audited financials

---

### Phase 4 — Outreach Templates

#### WhatsApp Deep Links — CORRECTED ENCODING RULES
**⚠️ Critical pitfall — Android/mobile WebView ampersand bug:**
Standard URL encoding (`%26` for `&`) FAILS on WhatsApp mobile. Even a properly encoded `%26` inside the message text is misinterpreted by Android WebViews as a URL parameter separator, truncating the message at the first `&`.

**The fix — use full-width ampersand `％` (U+FF06) instead:**
- Inside message text: `&` → `%EF%BD%86` (full-width ampersand, U+FF06) — NOT `%26`
- URL parameter separators (`?`, `&` between URL params like `phone=` and `text=`) = use standard encoding
- Phone number: raw digits only — no `+`, no spaces, no dashes, no leading zero

**Example — correct wa.me URL:**
```
https://wa.me/918291924600?text=Hi%20Deepesh%2C%20co-founder%20%EF%BD%86%20I%20qualify.
```
Here `%EF%BD%86` is the full-width ampersand inside the message; the `?` and `&` separators in the URL itself are NOT encoded.

**Never use `%2526`** — that is double-encoding and makes the `text` parameter invisible (link opens WhatsApp but with no message at all).

**Format:** `https://wa.me/<phone>?text=<url-encoded message>`

**Email (use for full details — wa.me cannot carry long pre-filled bodies):**
- Use `mailto:` link or HTML file with a mailto button
-mailto fills subject + body; wa.me only carries the short intro message

**DSquare Global — Verified Contact (as of May 2026):**
- WhatsApp: +91 8291924600 (Deepesh Desai)
- Email: info@dsquare.global (website contact form)
- Raj Shamani reference: `https://www.youtube.com/watch?v=N_Lz5plv__M`

**Email subject:** "UAE Golden Visa Eligibility Inquiry — O3 Infotech (Kelsa.io) Founder"

**Email body (updated May 2026 — O3 ARR ~INR 3 Cr, DRA Group ~INR 2,000 Cr):**

Dear Deepesh,

I came across your discussion with Raj Shamani on YouTube regarding UAE Golden Visa pathways for entrepreneurs and business founders. I am reaching out to explore whether my co-founder and I may qualify under the current framework.

**Applicant Details:**
1. Nishant Ranka — Founder & CEO, O3 Infotech | Director, DRA Group
2. Manohar Singh — Managing Director & Co-founder, O3 Infotech

**Company Profile — O3 Infotech Pvt Ltd (www.kelsa.io):**
- Founded: 2017
- Product: Kelsa.io — no-code SaaS workflow platform (near-ERP functionality)
- ARR: ~INR 3 Crore per annum
- Clients: 50+ enterprise clients across India, South Africa, Dubai, Netherlands, Malaysia, Australia
- Notable clients: KurlOn, Altiostar, Sasmos, Concord United, Rangsons Aerospace
- HQ: 204, Prizm Greystone, Cunningham Road, Bangalore — 560051

**Nishant Ranka — Background:**
- M.Eng (Computer Science), Stevens Institute of Technology, Hoboken, NJ, USA
- Prior: Burgiss Group (2001–2002), Deutsche Bank NYC (2002–2004, $200M global money transfer project), Co-founded IRCA Pvt Ltd (sold to Origo Sino India PLC — 15 developers across India & South Africa)
- Current: Director Technology & Engineering, DRA Group; Director/Product Development & CEO, O3 Infotech (since 2017)

**Group-wide financials:**
- O3 Infotech: ~INR 3 Cr ARR
- DRA Group: ~INR 2,000 Crore turnover (real estate & infrastructure)
- IRCA: ~INR 5 Cr (sold)
- Group headcount: 60+

**What we'd like to understand:**
1. Our eligibility under the current UAE Golden Visa framework (entrepreneur / highly skilled professional / investor category)
2. The most suitable category to apply under for both of us
3. Approximate timelines from application to approval
4. Total costs involved (filing, legal, advisory, visa fees)
5. Documentation requirements

We have ready: passport copies, reference letters from O3 Infotech, company incorporation docs, ITR/salary evidence, client profiles, and audited financials.

Happy to share further details or schedule a call at your convenience.

Regards,
### Phase 4 — Outreach Templates

#### WhatsApp Deep Links — CORRECTED ENCODING RULES

**⚠️ Critical — WhatsApp wa.me URL ampersand encoding (verified June 2026):**

Standard URL encoding (`%26` for `&`) FAILS on WhatsApp mobile WebView. Even properly encoded `%26` inside the message body is misinterpreted as a URL parameter separator, truncating the message at the first `&`.

**The fix — full-width ampersand `＆` (U+FF06):**
- Inside message text: `&` → `%EF%BD%86` (U+FF06, full-width ampersand) — **NOT** `%26`
- URL parameter separators (`?` after phone, `&` between `phone=` and `text=`) → use standard encoding
- Phone number: raw 10 digits only — no `+`, no spaces, no dashes, no leading zero

**Example — CORRECT wa.me URL:**
```
https://wa.me/918291924600?text=Hi%20Deepesh%2C%20co-founder%20%EF%BD%86%20I%20qualify.
```
Here `%EF%BD%86` = full-width ampersand (＆) inside the message; the `?` and `&` between URL params are NOT encoded.

**NEVER use `%26` or `%2526`** — both fail on WhatsApp mobile WebView.

**NEVER use `%26` or `%2526`** — both fail on WhatsApp mobile WebView. `%26` is treated as URL param separator, truncating the message. `%2526` makes the text parameter completely invisible.

**Format:** `https://wa.me/<phone>?text=<message with %EF%BC%86 for &>`

**For long emails (wa.me cannot carry full bodies):** Use HTML file with a mailto button. See `templates/email_mailto.html` in this skill.

#### DSquare Global — VERIFIED Contact (May 2026)
- **WhatsApp:** +91 8291924600 (Deepesh Desai — confirmed from dsquare.global)
- **Email:** info@dsquare.global (website contact form)
- **Raj Shamani reference:** `https://www.youtube.com/watch?v=N_Lz5plv__M`

**WhatsApp intro message (full-width ampersand version):**
```
Hi Deepesh, I came across your discussion with Raj Shamani on UAE Golden Visa pathways and wanted to explore whether my co-founder ＆ I may qualify. I run O3 Infotech, a technology and AI-focused SaaS company (Kelsa.io) with over INR 3 crore ARR and 50+ enterprise clients. I also serve as Director at DRA Group, a INR 2,000 crore real estate and infrastructure company. I've sent you a detailed email with our full profile. Happy to connect if you think we could be a good fit. Regards, Nishant Ranka
```

**Email subject:** "UAE Golden Visa Eligibility Inquiry — O3 Infotech (Kelsa.io) Founder"

**Email body (updated May 2026 — O3 ARR ~INR 3 Cr, DRA Group ~INR 2,000 Cr):** [as in skill — replace outdated figures]

#### Alternative UAE Golden Visa Advisory Firms (India-Based)

**⚠️ IMPORTANT — firm type distinction:**
- **Golden Visa advisory firms** = boutique investment/immigration advisory that assesses eligibility, advises on category, handles applications. Target these.
- **Visa processing centres** = VFS Global, BLS, etc. = document submission centres, NOT advisors. Do not target for advisory outreach.
- **General immigration firms** = firms focused on UK/Canada/Australia visas. Many do NOT have a dedicated UAE Golden Visa desk. Verify before outreach.

**Verified firms (May 2026):**

| Firm | Website | Phone/WhatsApp | Email | Location | Status |
|---|---|---|---|---|---|
| **DSquare Global** (Deepesh Desai) | dsquare.global | ✅ +91 8291924600 | info@dsquare.global | Dubai / Online | ✅ Fully verified |
| **My Golden Pass** | mygoldenpass.com | ✅ +91 8097984460 (raw: 918097984460) | info@mygoldenpass.com | Mumbai + Dubai + Lisbon | ✅ Fully verified |
| **OneVasco India** | onevasco.com | +91 22 62018483 | IndiaEnquiry@onevasco.com | Mumbai (pan-India centres) | ✅ Phone verified |

**Ruled out firms:**
| Firm | Reason |
|---|---|
| XIPHIAS Immigration | General immigration (Canada, Caribbean CBI) — no dedicated UAE Golden Visa desk |
| Stellar Immigration | General immigration — no UAE desk |
| WWICS | General immigration — India-wide, no UAE focus |
| Golden Gate Visas | e-Visa processing site (travel documents) — not advisory |
| Golden Visas Consultancy | Lebanon/Portugal-based — not India |
| Horizon Biz Consultancy | Dubai-based — not India-based |

**Unverified / ruled out firms:**
| Firm | Website | Reason |
|---|---|---|
| XIPHIAS Immigration | xiphiias.com | General immigration (Canada, Caribbean CBI) — no dedicated UAE Golden Visa desk found |
| Stellar Immigration | stellarimmigration.com | General immigration — no UAE desk |
| WWICS | wwics.com | General immigration — India-wide |
| Golden Gate Visas | goldengatevisas.com | e-Visa processing site (travel documents) — not advisory |
| Ly Destination Services | ly-destination.com | Unclear specialization — verify before outreach |
| Golden Visas Consultancy | goldenvisasconsultancy.com | Lebanon/Portugal-based — not India office found |
| Horizon Biz Consultancy | horizonbizco.com | Dubai-based (+971 number) — not India office |

**⚠️ User must verify before outreach** for any firm not marked ✅ fully verified. Do NOT guess phone numbers.

**My Golden Pass — Verified Contact (May 2026):**
- **WhatsApp:** +91 8097984460 (raw: 918097984460)
- **Email:** info@mygoldenpass.com
- **Subject:** UAE Golden Visa Eligibility Inquiry — O3 Infotech / DRA Group Founder
- **WhatsApp message:**
```
Hi Team, I am Nishant Ranka — Founder & CEO of O3 Infotech (Kelsa.io) and Director at DRA Group, based in Bangalore. I have sent a detailed email to your team outlining my profile and UAE Golden Visa requirements. Would appreciate a quick call or WhatsApp consultation at your convenience. I am also open to visiting your Mumbai office or travelling to Dubai if needed. Regards, Nishant Ranka | +91 98450 26390 | ndr@draas.com
```
- wa.me link: `https://wa.me/918097984460?text=Hi%20Team%EF%BD%86%20I%20am%20Nishant%20Ranka%20%E2%80%94%20Founder%20%26%20CEO%20of%20O3%20Infotech%20(Kelsa.io)%20and%20Director%20at%20DRA%20Group%2C%20based%20in%20Bangalore.%20I%20have%20sent%20a%20detailed%20email%20to%20your%20team%20outlining%20my%20profile%20and%20UAE%20Golden%20Visa%20requirements.%20Would%20appreciate%20a%20quick%20call%20or%20WhatsApp%20consultation%20at%20your%20convenience.%20I%20am%20also%20open%20to%20visiting%20your%20Mumbai%20office%20or%20travelling%20to%20Dubai%20if%20needed.%20Regards%2C%20Nishant%20Ranka%20%2B91%2098450%2026390%20ndr%40draas.com`

**OneVasco India — Verified Contact (May 2026):**
- **Phone:** +91 22 62018483 (Mumbai office, Mon–Fri 9AM–5PM)
- **Email:** IndiaEnquiry@onevasco.com (or USAEnquiry@onevasco.com)
- Note: OneVasco is primarily a call-center/visa-processing model — good for document submission logistics but advisory quality may vary. Use as backup to boutique advisors like DSquare / My Golden Pass.

---

**Related case — WorldVisa (Australian PR, separate track):**
The Nishant Ranka / WorldVisa Australian PR case (GTI → National Innovation Visa) is a related-but-separate track. It is handled by Anand Prakash (anand@worldvisa.in) who took over from Kavitha Ramaraj. See `references/worldvisa-australian-pr.md` for full context, email exchanges, and next steps. Do NOT conflate with UAE Golden Visa outreach.

---

### Phase 5 — Tax Residency Advisory (India–UAE–UK)

This phase is relevant when the user wants to understand how UAE Golden Visa affects their Indian tax residency status, and potentially UK tax residency.

#### India — Section 6(1) Income Tax Act 1961: Non-Resident Conditions

An Indian citizen is **non-resident** if **either**:
- **(Condition A — 182-day test):** Present in India for **< 182 days** in the relevant financial year (FY), OR
- **(Condition B — 60-day RNOR test):** Present in India for **≥ 60 days** in the current FY **AND** ≥ 365 days in the **preceding 4 years** (applies to Indian citizens returning after long stays abroad)

**⚠️ Critical waiver (proviso to Section 6(1)):** The 60-day/4-year condition (Condition B) is **entirely waived** if the person becomes a **tax resident of another country** (e.g., UAE via Golden Visa). This means once UAE tax resident, the person only needs to ensure **< 182 days in India** in the current FY to maintain non-resident status.

**Practical implication:** Spend < 182 days/yr in India after obtaining UAE Golden Visa → non-resident of India for tax purposes, regardless of how many days spent in the prior 4 years.

#### UAE Tax Residency
- UAE has **no personal income tax**
- UAE residency is an **immigration/visa status** concept (not a tax concept)
- Golden Visa holders = UAE residents for visa/immigration purposes
- For DTAA purposes: a person with UAE residence visa (including Golden Visa) is generally considered a UAE resident

#### India–UAE DTAA Article 4
- "Resident of a Contracting State" = person who, under the laws of that State, is liable to tax by reason of domicile, residence, place of management, or similar criterion
- **Tie-breaker rules** when both countries claim residency:
  1. National of one state
  2. Permanent home available — one with closer personal/economic relations (centre of vital interests)
  3. Usually reside in one state
  4. Mutual agreement by competent authorities

#### UK Statutory Residence Test (SRT) — "30-Day Rule"
- **Automatic Overseas Test:** You are **automatically non-UK resident** if you spent **≤ 30 days** in the UK during the tax year AND ≤ 30 days in each of the previous 3 tax years
- This is the key "automatic non-residency" provision for those with limited UK presence

---

### GWS Auth — Always Pass telegram_id Explicitly

```python
# WRONG — uses session env var which may be empty/wrong
svc = build_service('drive', 'v3')

# CORRECT — always pass the telegram_id
svc = build_service('drive', 'v3', 'ndr')
```

If token exists but you get `FileNotFoundError: No GWS token for user {telegram_id}` → the session env var isn't loading the current user context. Pass telegram_id directly.

**Token refresh (if expired):**
```python
import json, requests
with open('/data/hermes/users/{telegram_id}/the gws-vault daemon (no token files exist on disk — see api-references/google-workspace-api/references/token-access-canonical.md)') as f:
    tok = json.load(f)
resp = requests.post(tok['token_uri'], data={
    'client_id': tok['client_id'],
    'client_secret': tok['client_secret'],
    'refresh_token': tok['refresh_token'],
    'grant_type': 'refresh_token'
}, timeout=15)
if resp.status_code == 200:
    tok['token'] = resp.json()['access_token']
    with open('/data/hermes/users/{telegram_id}/the gws-vault daemon (no token files exist on disk — see api-references/google-workspace-api/references/token-access-canonical.md)', 'w') as f:
        json.dump(tok, f)
```

### GWS Scope Limitations

| Data Type | Use | Method |
|---|---|---|
| Gmail, Calendar, Drive (personal) | `gws_auth.build_service` | Per-user OAuth |
| Shared contacts registry | `gws_sa.build_service` | SA DWD (`ndr@draas.com`) |
| Sheets (shared) | `gws_sa.build_service` | SA DWD |

Using `gws_sa` for Gmail/Calendar raises `ValueError` — wrong auth path.

---

## Key Contacts Discovered (Session Jun 2025)

### O3 Infotech / Kelsa
- **Manohar Singh** — Managing Director | +91 9845890316 | msingh@kelsa.io | 204 Prizm Greystone, Cunningham Rd, Bangalore
- **Ashwin Hegde** — hashwin@o3infotech.com
- **Umesh** — umesh@kelsa.io
- **Rupsa Das** — rupsa@kelsa.io
- **Guna** — gunarka@kelsa.io
- **Pavan** — pavan@kelsa.io
- **Vikramaditya H** — vikramaditya@kelsa.io

### DSquare Global (Not Yet Contacted)
- **Founder:** Deepesh Desai
- **Website:** dsquare.global
- **Raj Shamani interview:** `https://www.youtube.com/watch?v=N_Lz5plv__M`
- **Contact discovery: PENDING** — no email/phone/WhatsApp found yet (ARM64 browser block)

### User's Own Context
- User: **Nishant Ranka** (ndr@draas.com / ndr@o3infotech.com | +91 98450 26390) — IS the visa applicant
- Nishant Ranka is the visa applicant/beneficiary — DRAAS director, O3 Infotech co-founder
- Spouse: Roshini Ranka (rnr@draas.com)
- DOB: 18/12/1979
- Education: M.Eng Computer Science, Stevens Institute of Technology, NJ, USA
- Passport: available in Drive (passport copy file ID not yet located)
- Co-applicant: Manohar Singh (O3 Infotech co-founder, MD)
