# Gandhinagar Dark Store — Multi-Channel Outreach Compilation (Jul 2026)

**Property:** Mamta A&B, No. 14, 3rd Cross, 4th Main Road, Gandhinagar, Bengaluru – 560009  
**Space:** Basement ~3,200 sq.ft. + GF ~2,000 sq.ft. (double-height, expandable ~4,000 sq.ft.) | Total ~5,200–7,200 sq.ft.  
**V3 Contact Sheet:** "Dark Store Outreach Database - Gandhinagar" (Sheet ID: `1AdnonBPS1TFrMLfqYz3UT2xIIKWiEYgOIBWdDZ1bT9A`)  
**Document:** "Gandhinagar Dark Store Outreach — All Messages (15 Jul 2026)" (Doc ID: `1TvRlkSj4fmxjKnlZqMcWqHoGhoMq8SSmKTtRdA90E2o`)

## Multi-Channel Contact Segmentation

From the 45 contacts in the V3 sheet, classified by reachable channel:

| Channel | Count | Actionable? | Method |
|---------|-------|-------------|--------|
| 📧 Email | 2 | ✅ Yes (Gmail API) | Draft via `draft_create` |
| 🐦 Twitter DM | 2 | ❌ No (xurl not installed) | Copy-paste text prepared |
| 💼 LinkedIn InMail (known handle) | 8 | ❌ No (no LinkedIn API) | Copy-paste text prepared |
| 🔍 LinkedIn Search + DM | 11 | ❌ No (need profile discovery) | Common template + table |
| 🌐 Website Contact Form | 7 | ❌ No (manual form fill) | Standardized message prepared |
| **Total** | **30** | | |

## Channel-Specific Message Patterns Used

### Email (formal, information-rich)
- Subject: `[Topic] — [Location], [City]`
- Opening: Name-drop property differentiator
- Body: 3-4 sentences — what you have → why relevant → location/spec fit → CTA
- Signed: Full name + company + email + phone

### Twitter DM (brief, high-signal)
- No greeting preamble
- 1-2 sentences max
- End with open question inviting reply
- Pattern: "Hi [Name] — [Company] expanding [scale] in [City]? We have [spec] space in [location]. DM me if worth a look."

### LinkedIn InMail (semi-formal, conversational)
- Reference their specific role + company expansion context
- 2-3 sentences, lighter than email
- Call to action: "Would you be open to a quick conversation?"
- Tailored per company's specific scale/expansion plans

### Website Contact Form (standardized)
- Single message used across all 7 logistics companies
- Compact: property details in 3 bullet points + request for right contact person

## Google Doc Structure

The outreach doc was organized as:

```
1. 📧 PRIORITY 1 — Email Drafts (Ready in Gmail Drafts)
   [Subject, full body, status: ✅]

2. 🐦 PRIORITY 2 — Twitter/X DMs (Copy-Paste)
   [Handle, message text]

3. 💼 PRIORITY 3 — LinkedIn InMail (Copy-Paste)
   [Profile URL, designation, full InMail text]

4. 🔍 PRIORITY 4 — LinkedIn Search Required
   [Table of 11 contacts needing profile discovery + common template]

5. 🌐 PRIORITY 5 — Website Contact Forms
   [Standardized message + 7 company URLs]

6. 📊 Summary Table
   [Channel | Count | Status]
```

## Priority Tier (HIGHEST First)

1. **Shadowfax** — hello@shadowfax.in — 100 new dark stores — 📧 Email draft
2. **Swiggy Instamart** — Chethan S Gowda (linkedin.com/in/chethan07) — 385+ stores — 💼 LinkedIn
3. **Zepto** — Rohit Kumar (linkedin.com/in/rohit-kumar-168a3b42) — 250+ stores — 💼 LinkedIn
4. **Flipkart Minutes** — Hemant Badri (@BadriHemant) — 1,000+ stores (100/mo) — 🐦 Twitter DM
5. **Blinkit** — Albinder Singh (@albinder) — 2,027→3,000 stores — 🐦 Twitter DM
6. **Zepto** — Aadit Palicha (aadit@zeptonow.com) — Co-founder — 📧 Email draft
7. **Swiggy Instamart** — Mahesh Patwardhan (linkedin.com/in/mahesh-patwardhan-6356a766) — 150+ stores — 💼 LinkedIn

## Tools Used

| Tool | Method | Purpose |
|------|--------|---------|
| `gws_skill_bridge.call('drive_search', ...)` | raw_query=True, max=50 | Find Dark Store spreadsheet on Drive |
| `gws_skill_bridge.call('sheets_get', ...)` | sheet_id, range | Read V3 - Merged tab for all 45 contacts |
| `gws_skill_bridge.call('draft_create', ...)` | to, subject, body, html=False | Create 2 email drafts in Gmail |
| `gws_skill_bridge.call('docs_create', ...)` | title, body (HTML) | Create outreach reference document |
| `build_service('drive', 'v3')` | file.update with addParents/removeParents | Move doc to TMP folder |
| `whatsapp_link` tool | phone, text, platform='telegram' | WhatsApp links for team coordination |
