---
name: draas-marketing-content-brief
description: "Create comprehensive marketing & content briefs for DRAAS real estate projects — target audience, emotional hooks, rational triggers, competitive positioning, messaging, and visual direction. Covers the full lifecycle: user briefing → area research → template reference → LLM generation → Google Doc creation → Gmail draft to content team."
version: 1.0.0
author: DRAAS
tags: [content, marketing, brief, real-estate, gowri, draas, google-docs, email-draft]
---

# DRAAS Marketing & Content Brief

## Trigger Conditions

Load this skill when ndr asks to:
- Create a content/marketing brief for a DRAAS project (Ranka Amber, Ranka Udaya, Serenity Hillview, Ranka Northstar, Ranka Oasis, etc.)
- "Brief Gowri on [project]"
- "Create a positioning document for [project]"
- "Content strategy for [project]"
- "Target audience document for [project]"
- Any request involving giving Gowri (content head) a briefing on a product's content direction

## Workflow

### 1. Gather Project Details

ndr typically gives these via voice message. Extract:

- **Product name & type** (e.g. farm plots, boutique apartments, plotted development)
- **Location** (specific area, landmarks, distances from highway)
- **Pricing** (entry price vs neighbourhood comps)
- **Product size** (number of units/plots, size range)
- **Neighbours & surroundings** (ashrams, colleges, developments, natural features)
- **Target audience profile** (age, income, family stage, psychographics)
- **Key selling points** (why this product is unique)
- **Competitive landscape** (what else exists in the area)
- **Emotional hooks ndr has in mind**
- **Rational/financial triggers**
- **Visual/content direction** (look and feel for brochures, videos, AVs)

### 2. Research the Area (using parallel sub-agents)

**NEVER SKIP THIS STEP.** The user WILL call out a brief as "not detailed enough" if it lacks real research. The first pass from the LLM is always too shallow without research backing.

Launch **parallel `delegate_task` sub-agents** — each covering a different research dimension:

| Agent | What it researches | Typical findings |
|-------|-------------------|-----------------|
| **Holiday home / competitor market** | Comparable projects, pricing, buyer profiles, legacy projects (Gorfshire etc.), demand trends, plotted vs villa dynamics | Specific project names, price ranges per sqft, plot sizes, phase status |
| **Industrial corridor / macro** | BIAL expansion (PAX capacity), Foxconn KIADB (₹₹ Cr, jobs), Metro timelines, Kia/Lepakshi corridor, semiconductor belt | Investment figures, employment numbers, distance markers, CAGR data |

Each sub-agent gets the location details and returns structured findings. Their output (from summaries) feeds into the LLM generation prompt.

**Key dimensions to research for every brief:**

- **Growth corridor dynamics** — airport expansion, industrial parks, metro connectivity, highway upgrades
- **Competitor pricing** — specific project names, price per sqft, plot sizes, distance from property
- **Employment catalysts** — investment in ₹ Cr, projected jobs, company names (Foxconn, Kia, etc.)
- **Real estate trends** — CAGR over 3-5 years, product-type shifts (plots→villas), market phase
- **Landmark context** — educational institutions (colleges), spiritual centres (ashrams, temples), golf courses, tech parks
- **Legacy demand validation** — pioneer projects that validated the corridor (e.g. Gorfshire at Nandi Hills, 2007 onwards)

### 3. Read an Existing Brief as Format Reference

Open an earlier brief (e.g. the Ranka Amber & Northstar brief) to use its structure, tone, and tagging conventions as a template.

The standard brief structure:

```
### How to read this document
[Given] — from the user, treated as fact.
[Verify] — claim that anchors the pitch, must be confirmed before going into content.
[Missing] — gap to be filled.

## Snapshot
All key project facts with [Given]/[Verify]/[Missing] tags.

## Positioning statement
One powerful sentence: "For [audience] who [need] — [product] is [unique value]."

## Target audience
Segment profiles with demographics, motivations, and psychographics.

## Differentiators
What makes this project unique vs everything else in the market.

## Reasons to buy
**Rational:** Practical, logical reasons.
**Emotional:** Feelings, identity, aspirations.
**Financial:** Investment returns, appreciation, yield.

## Competitive angle
How to frame the competition — often "there is no direct competitor" for truly unique products.

## (Optional) Special sections
E.g. "The Ashram factor", "The macro thesis", etc.

## Hooks & messaging
**Emotional triggers:** Taglines for feeling-driven messaging.
**Rational/financial triggers:** Taglines for logic-driven messaging.
**Lifestyle triggers:** Taglines for aspirational messaging.

## Visual & content direction
Look and feel for brochures, videos, AVs, social media.
Tagline direction for brochure/video covers.
```

### 4. Generate the Brief Content via OpenRouter

Feed everything to a capable model via `call_openrouter_model`:

**Prompt structure:**
- The existing brief as a format/tone reference
- All user-provided project details
- Online research data
- Clear section-by-section requirements
- Explicit instruction to use [Given]/[Verify]/[Missing] tags

Use a model with strong reasoning and long output (GPT-4.1, Claude Sonnet, Gemini 2.5 Pro). Set `max_tokens=16000` to ensure room for the full brief.

### 5. Create the Google Doc

**Prefer HTML import for rich-formatted docs** — For documents with multiple heading levels, bullet lists, bold/italic, and sections, importing HTML via the Drive API is **10-100x faster** than batchUpdate (3 seconds vs 5+ minutes).

Recipe:

```python
from tools.gws_auth import build_service
from googleapiclient.http import MediaFileUpload

drive = build_service('drive', 'v3', service_name='google-draas')

# Write content as HTML with semantic tags
html_content = '<!DOCTYPE html><html><head><meta charset="UTF-8"></head><body>'
html_content += '<h1>Title</h1><h2>Section</h2><p>Body text</p>'
# ... build full HTML
html_content += '</body></html>'

with open('/tmp/brief.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

media = MediaFileUpload('/tmp/brief.html', mimetype='text/html', resumable=False)
file = drive.files().create(
    body={'name': 'YYYYMMDD ProjectName Marketing & Content Brief',
          'mimeType': 'application/vnd.google-apps.document'},
    media_body=media,
    fields='id,webViewLink'
).execute()
doc_id = file['id']
doc_url = file['webViewLink']

# Move to TMP
drive.files().update(fileId=doc_id, addParents=TMP_FOLDER_ID, removeParents='root').execute()
```

**HTML → Docs mapping** (for rich formatting):

| HTML Tag | Google Docs Format |
|----------|-------------------|
| `<h1>` | Heading 1 |
| `<h2>` | Heading 2 |
| `<h3>` | Heading 3 |
| `<p>` | Normal text |
| `<strong>` / `<b>` | Bold |
| `<em>` / `<i>` | Italic |
| `<ul><li>` | Bullet list |
| `<hr>` | Separator line |

**Fallback — simple text-only docs:** If the brief is only a title + single paragraph, use batchUpdate or the CLI:
```python
docs = build_service("docs", "v1", service_name="google-draas")
doc = docs.documents().create(body={"title": "YYYYMMDD ProjectName Marketing & Content Brief"}).execute()
# One-shot insertText for plain content
```

**Naming convention:** `YYYYMMDD <Project Name> Marketing & Content Brief` (e.g. "20260717 Serenity Hillview Marketing & Content Brief")

**Doc ID to capture** for use in the email draft.

### 5B. (Alternate) Compile Brand Talking Points

When the ask is NOT a full content brief but rather **company/group talking points** to embed in a video, deck, or presentation (e.g. "create all the talking points about DRA and Ranka Group for the content guys to use"):

**Multi-source research pattern:**

| Source | What to look for | Tool |
|--------|-----------------|------|
| Google Drive | Corporate profiles, leadership bios, group structure docs, investor portfolios | `gws_auth.build_service('drive', 'v3')` — search for "profile", "corporate profile", "group profile" |
| Company website | Awards, ratings (CRISIL, India Ratings), certifications, project listings, customer numbers, testimonials | `web_extract` on the company's main pages + `/about_us`, `/awards-and-recognition`, `/our-accolades` |
| Web news | IPO readiness, partnership announcements, project launches, financial numbers (GDV, revenue) | `web_search` for company name + "CRISIL", "India Ratings", "GDV", "portfolio", "award" |

**What to extract from each source:**
- **Legacy & history**: years in operation, founding story, pioneer claims, families served, sq.ft. delivered
- **Leadership credentials**: education, prior roles (Deutsche Bank, PE firms), exits (sold company to...), tech/entrepreneurship background
- **Ratings & awards**: CRISIL/India Ratings/ISO certifications, year-by-year award list (developer of the year, on-time delivery, customer centricity)
- **Project portfolio**: ongoing projects with unit counts and sq.ft., proposed mega projects with values, partnership projects with co-developer names
- **Strategic partnerships**: developer names, deal values, JV structures
- **Financial scale**: GDV, revenue, valuation, IPO readiness
- **Customer innovations**: proprietary tools (Customer Delight Meter, Construction Timeline Meter), technology initiatives

**Output structure:**
1. Group Legacy & History (founding, milestones)
2. Founder's Vision / Succession
3. Current Leadership & Credentials
4. Ratings, Awards & Certifications (with dates and awarding bodies)
5. Landmark Projects & Portfolio
6. Proposed Mega Developments
7. Strategic Partnerships
8. Customer-Centric Innovations
9. Financial Strength & Scale
10. **Suggested 60-second script** — ready-to-use VO script for video insertion

**Where to append:** Add the talking points as an appendix to the primary document (video analysis, deck, or brief), separated by a clear horizontal rule and an "APPENDIX: TALKING POINTS" heading.

### 6. (Optional) Build HTML Presentation

When the user wants a **polished, presentation-ready document** (they will say this if the Google Doc alone isn't enough — the clue is "I want it like a proper detailed briefing document I can give my content head"):

1. **Create an HTML template** with brand-appropriate styling:
   - Color palette: dark forest greens (`#1a3a2a`, `#2d6b4a`), warm gold (`#d4a843`), warm white background (`#fdfbf7`)
   - Serif headings (Georgia) + sans-serif body (system font stack)
   - Colored badge-style tags: `.badge-given` (green), `.badge-verify` (yellow), `.badge-missing` (red)
   - Pull quotes with gold left border for positioning statements
   - Competitive comparison tables with highlighted row for Serenity Hillview
   - Tagline cards with color-coded category tags
   - Content pipeline timeline
   - Footer: "DRA Realty Private Limited — Confidential"
   - Self-contained HTML (all CSS inline, zero external dependencies)

2. **Inject the full content** into the template — replace ALL placeholders with real brief content. Verify zero placeholders remain.

3. **Upload to Drive** — move to the project's Content Marketing folder (not TMP):
   ```
   TMP > [Project Name] > Content Marketing > YYYYMMDD_[Project]_Marketing_Content_Brief.html
   ```
   
   Use `drive.files().update()` with `addParents` + `removeParents` to move the file.

### 7. Share with Stakeholders (when requested)

When the user says "share this with [name]" or "send it to Prakash":

1. **Share on Drive** with viewer access:
   ```python
   drive.permissions().create(
       fileId=FILE_ID,
       body={'type': 'user', 'role': 'reader', 'emailAddress': 'person@email.com'}
   ).execute()
   ```

2. **Generate WhatsApp message** using `whatsapp_link` tool:
   - Get the recipient's phone number from Google Contacts (People API searchContacts)
   - Ask them to review the document and give feedback via voice note

3. **Report back** to the user with the WhatsApp link so they can tap to send.

### 8. Create Gmail Draft to Gowri

Create a Gmail draft (NEVER send — always draft-only) addressed to:

- **To:** Gowri Singh `<gsingh@draas.com>`
- **CC:** Roshni Ranka `<rnr@draas.com>`
- **Subject:** `<Project Name> — Marketing & Content Brief for Your Review`

```python
from email.mime.text import MIMEText
import base64

message = MIMEText(body_text)
message['to'] = "Gowri Singh <gsingh@draas.com>"
message['cc'] = "Roshni Ranka <rnr@draas.com>"
message['subject'] = subject
message['from'] = 'Nishant Ranka <ndr@draas.com>'

encoded = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
draft = gmail.users().drafts().create(
    userId='me',
    body={'message': {'raw': encoded}}
).execute()
```

The email should:
- Mention this follows the same format as the Amber/Northstar brief
- Include the Google Doc link
- Summarise what the brief covers (section list)
- Ask Gowri to review and discuss

## 8. Legal Document Filing & Email Response

When ndr sends a scanned legal document (OS petition, sale deed, court order, legal notice) related to a project — file it properly and respond to the associated email thread.

### Workflow

**Step 1 — OCR the document**
Scanned PDFs (image-only, no text layer) need OCR. Extract each page as a PNG via `pymupdf`, then run `vision_analyze` on each page.

**Step 2 — Extract key fields**
From OCR output, identify: case type (OS, Misc, etc.), court, plaintiff/defendant, case number, legal provision, survey number, village, taluk, property extent, key dates.

**Step 3 — Rename per convention**
`YYYY_<CaseType>_<Party1>_Sy<No>_<Village>_<Project>.pdf`
Example: `2026_OS_GodwadBhavanJainTrust_Sy93-2_Hurulagurki_SerenityHillview.pdf`

**Step 4 — File in Drive**
Upload to `TMP > [Project Name] > Legal/` via `MediaFileUpload`.

**Step 5 — Find the relevant email thread**
Search Gmail for project name + survey number + advocate email to locate the thread where this document was requested. Typically the legal DD checklist thread.

**Step 6 — Draft reply-all with context**
Reply with structured explanation of what the document means. For an OS petition under S.92 CPC, the standard context:
1. OS filed by Trust seeking court permission to sell Sy.No.[X]
2. Process: Misc petition allowed → OS filed → ~6-7 hearings → court grants permission if no objections
3. Currently at [active stage]
4. Link to filed document

Thread the reply properly (In-Reply-To / References headers matching original message).

### Common Legal Document Types

| Type | What It Is | Implication for Sale |
|---|---|---|
| O.S. under S.92 CPC | Trust seeking court permission to sell | In process, ~6-7 hearings expected |
| Misc Petition | Preliminary application before main suit | Allowed → OS filed |
| Sale Deed | Title transfer document | Proof of ownership chain |
| CLU Conversion Order | Agri→Residential conversion permission | Already done |
| JDA | Landowner-developer agreement | Shows rights acquired |
| GPA | General Power of Attorney | Verify cancellation status |

## References

### Existing Briefs (format templates)
- **Ranka Amber & Northstar**: `1bhhFLuEOq-VkJP9p1rf9hqN7yttL_qMepEI0za3Fn4k` (Doc ID)
- **Ranka Udaya PDF**: `1M8cnDxlPd5ntuG0O8-ZRNePmRckgJU7P` (Drive file ID)
- **Serenity Hillview Doc**: `17m02SADmt7gN7UUGk-Ps8ciUmboNiMoTXoubv6kcXHs` (Doc ID)
- **Serenity Hillview HTML**: `1R5xzqlZPmnecMyQ3EpTmKFjR_5pdnUs9` (Drive file ID)

### Key Contacts
- **Gowri Singh** — Content Head, DRAAS. gsingh@draas.com / gowrisingh72@yahoo.com
- **Roshni Ranka** — rnr@draas.com
- **Prakash Singh** — Bus Dev Head, DRA Realty. +91 97399 32078, psingh@draas.com
- **Vinodhvi Advocate** — Legal counsel. vinod@advocatev.in / rovinod@advocatev.in
- **Nishant Prakash (Zara)** — Project coordination. nishantprakash1@gmail.com

### Session Reference
- **`references/serenity-hillview-session.md`** — End-to-end walkthrough of the Serenity Hillview brief cycle (dictation → multi-agent research → HTML delivery → legal doc filing).

## Pitfalls

- **The first brief is never the final brief.** The user will call it out as "not detailed enough" or lacking research if you skip the research phase. Expect at least one iteration. Save time by doing research BEFORE the first generation — launch parallel sub-agents before calling the LLM.
- **HTML presentations must be self-contained.** No external CSS/JS/font dependencies. The file will be viewed offline, shared via Drive download, or opened in a browser. Everything must be inline in a single HTML file.
- **Research files created by sub-agents don't persist to disk.** Sub-agents run in isolated sandboxes. Capture their findings from the summary output returned by `delegate_task` — don't expect saved files at paths they reported. Feed that summary text directly into the LLM prompt.
- **Voice message transcription**: ndr often gives project briefs via voice. These contain rich detail but can be stream-of-consciousness. Systematically extract the structured fields (location, pricing, audience, hooks) from the transcript rather than treating it as a single block of text.
- **Verify vs Given**: When the user provides pricing comps ("they're ₹5,500/sqft"), always tag as [Verify] if you haven't independently confirmed the number online. The user's own facts are [Given]; market claims they reference are [Verify].
- **Research first**: Don't skip the research step even if the user gives comprehensive area details. The research provides macro credibility (CAGRs, investment figures, distance markers) that transforms a subjective pitch into an evidence-based brief.
- **Model choice for generation**: Use a model with strong structure-following ability (GPT-4.1, Claude Sonnet, Gemini 2.5 Pro). Avoid smaller or weaker models for this task — the brief needs consistent formatting across multiple sections.
- **Email is draft-only**: Per system rules, NEVER send the email — always create a Gmail draft and tell the user it's in their Drafts folder ready to send.

---

## Expanded Brief Structure (14-Section Format)

For particularly detailed projects, use this expanded 14-section brief structure instead of the standard 8-section format. This was developed for Serenity Hillview and subsequent briefs.

1. **How to read this document** — [Given] / [Verify] / [Missing] tagging convention
2. **Snapshot** — Project details table + pricing gap analysis vs all competitors
3. **Macro thesis** — Why this area/location, infrastructure catalysts
4. **Area/region deep-dive** — Historical context, market evolution, demand drivers
5. **Positioning statement** — One powerful sentence
6. **Target audience** — Break into 2-3 detailed segments (see template below)
7. **Emotional hooks** — 8-10 hooks with billboard-ready taglines
8. **Rational triggers** — 8-10 data-backed reasons
9. **Differentiators** — What makes this project unique
10. **Reasons to buy** — Rational / Emotional / Financial (all expanded)
11. **Competitive angle** — Head-to-head vs each competitor, with table
12. **Advantages & disadvantages** — Honest assessment with mitigations
13. **Visual & content direction** — Color palette, imagery themes, video concepts, brochure structure
14. **Content pipeline** — Priority-ordered production sprint timeline

### Target Audience Segment Template

Each segment should include:

| Field | What to Capture |
|-------|-----------------|
| **Name** | Human-readable label (e.g. "Empty-Nester Sanctuary Seeker") |
| **Profile** | Age, income, life stage, occupation, lifestyle |
| **Motivations** | What drives their purchase decision |
| **Fears / Objections** | What holds them back |
| **Messaging Approach** | How to speak to them — tone, trigger words, framing |
| **Emotional Hooks** | Specific hooks for this segment |
| **Rational Triggers** | Specific data points for this segment |

### Self-Contained HTML Presentation Tips

When building the styled HTML presentation (Step 7 in the main workflow):

- **Color palette**: Nature greens (`#1a3a2a`, `#2d6b4a`), warm earth tones, gold accents (`#d4a843`), warm white background (`#fdfbf7`)
- **Typography**: Serif headings (Georgia) + sans-serif body (system font stack)
- **Badge tags**: Green for [Given], yellow for [Verify], red for [Missing]
- **Comparison tables**: Highlighted row for the subject project
- **No external dependencies** — all CSS inline, zero CDN/font URLs (must render offline)
- **Footer**: "DRA Realty Private Limited — Confidential" + version + date

See the reference `references/20260717-serenity-hillview-session.md` for a complete worked example of the 14-section format with full HTML presentation.