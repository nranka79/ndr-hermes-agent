# Employee Onboarding — Sai Neha Vaddadi (June–July 2026)

Worked example of the full data-gathering workflow for Google Workspace account creation.

## Trigger

Nishant said via voice: *"Employee in the company... Neha, Vadolia or something. We've given her an offer letter and everything. Can you give me all her details? Because I want to create a draas.com account for her."*

## Step 1 — Name verification

Voice said "Vadolia" but the offer letter filename resolved to **Sai Neha Vaddadi** (also "Sai Neha V" in email signatures). The file was the authoritative source.

## Step 2 — Gmail search for offer letter

**Query:** `from:ndr@draas.com OR from:rnr@draas.com "Sai Neha" OR "Vaddadi" offer letter`

**Result:** Thread ID `19e8c1b15f7e30ab` — Nishant's email with `.docx` attachment:
- `20260603_DRA_SaiNehaVaddadi_OfferLetter_ContentCreator.docx`

**Download:** `gmail.users().messages().attachments().get()` on the `application/vnd.openxmlformats-officedocument.wordprocessingml.document` part.

**Text extraction (no python-docx):** Used zipfile + XML parse of `word/document.xml`:
```python
import zipfile, xml.etree.ElementTree as ET
with zipfile.ZipFile(docx_path) as z:
    with z.open('word/document.xml') as f:
        tree = ET.parse(f)
        text_parts = []
        for t in tree.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
            if t.text:
                text_parts.append(t.text)
        full_text = ' '.join(text_parts)
```

### Data extracted from offer letter:

| Field | Value |
|-------|-------|
| Full Name | Sai Neha Vaddadi |
| Phone | +91 7899398273 |
| Personal Email | esotericarts.ani@gmail.com |
| Role | Content Creator |
| Department | Content & Marketing (user confirmed: use "Marketing") |
| Manager | Gowri Singh — Content & Marketing Head (gsingh@draas.com) |
| Entity | DRA Realty Private Limited (CIN: U70100KA2011PTC058105) |
| Employment Type | Full-time, On Probation (6 months) |
| CTC | ₹40,000/month (Base ₹33,000 + Attendance ₹5,000 + Performance ₹2,000) — offer letter said ₹38,000 all-inclusive with perf pay component |
| DOJ | 16 June 2026 |
| Residential Address | **"Bangalore, Karnataka – [full address to be confirmed at joining]"** — NOT filled |
| Work Location | 204–206, Prism Greystone, Cunningham Road, Bengaluru – 560052 |
| Education | M.A. Animation (University of South Wales, UK), B.Sc. Animation (JAIN) |

## Step 3 — Drive search for resume

**Query:** `name contains 'Vaddadi' or name contains 'Neha'`

**Results:**
1. Google Doc: `20260603_DRA_SaiNehaVaddadi_OfferLetter_ContentCreator` (ID: `1DTukXi6MJTHP_7HF7wi4WisugpscZltfjgWdqfOsJZA`)
2. PDF: `20260603_DRA_SaiNehaVaddadi_Naukri_Resume_0y5m_ContentCreator.pdf` (ID: `1IApjLdMCbtKEWZimsq6CFs5fNfv-bA4R`)

**Resume extraction:** `pdftotext /tmp/neha_resume.pdf -`

### Data extracted from resume:
- **City/Area:** Bangalore - 37, Karnataka (HSR/Koramangala area, PIN 560037)
- **Phone:** +91 7899398273 (matches offer letter)
- **Email:** esotericarts.ani@gmail.com
- **Education:** Confirmed M.A. Animation (USW, UK) + B.Sc. Animation (JAIN)
- **Skills:** 2D Animation, Visual Storytelling, Character Design, Scriptwriting, AI Video, Content Creation, Marketing, 3D Lighting, Creative Direction
- **Tools:** Adobe Suite, Foundry Nuke, Autodesk Maya, Procreate
- **Languages:** English, Hindi (fluent), Telugu (native), Kannada (basic)
- **Prior experience:** KAM Group (AI Engineer & Marketing Associate via Supporting Souls), Bad Wolf Studios (work shadowing)

## Step 4 — Compilation for account creation

Delivered to Nishant as structured fields:

```
Name: Sai Neha Vaddadi
Phone: +91 7899398273
Personal Email: esotericarts.ani@gmail.com
Position: Content Creator
Department: Marketing
Manager: Gowri Singh — gsingh@draas.com
Entity: DRA Realty Private Limited
Type: Full-time, On Probation (6 months)
CTC: ₹40,000/mo (₹33k base + ₹5k attendance + ₹2k performance)
DOJ: 16 June 2026
Address: Bangalore - 37, Karnataka (city/area only — offer letter didn't capture full address)
```

## Step 5 — Address gap identified

The full residential address was never collected in the documentation. Offer letter placeholder: *"[full address to be confirmed at joining]"*. Resume only shows "Bangalore - 37, Karnataka". Recommended:
- Ask **Bharat H** (`sales1.blr@draas.com`) for KYC docs (Aadhaar, address proof)
- Need for emergency contact records

## Email Convention

Nishant created the account as: **nVaddadi@draas.com** (first initial + last name). This is the default DRA convention.

## Key Takeaways

1. **Offer letter is the primary source** for phone, CTC, role, manager, entity, DOJ
2. **Resume adds** city/area, education, skills — but rarely has full residential address
3. **Full address is frequently missing** — offer letter says "to be confirmed at joining". Must flag this separately
4. **Voice transcription may garble names** — always anchor on the file/email, not the transcript
5. **Gmail .docx attachments** need zipfile+XML parsing (no python-docx by default)
6. **Drive may have both Google Doc and PDF versions** of the same document — check both
7. **Email convention:** first-initial + last-name (nVaddadi@draas.com) — confirm with user
