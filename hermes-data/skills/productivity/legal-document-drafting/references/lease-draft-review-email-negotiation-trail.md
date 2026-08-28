# Lease Draft Review Against Email Negotiation Trail

**Trigger:** User asks to review a lease deed (or any commercial agreement) draft against the terms agreed in an email thread or multi-party correspondence.

**Context:** Common at DRAAS when a legal draft was prepared but the final commercial terms were negotiated directly between Nishant and the counterparty over email/phone/WhatsApp. The draft often lags behind the actual agreement.

## Workflow

### 1. Find the Email Thread

Search Gmail (draas account — `ndr@draas.com`) by:
- Counterparty name (e.g. Akber, Akbar, Raghu)
- Property name (e.g. Millers Road, Ranka Amber)
- Thread subject keywords

Narrow by date range — negotiations can span months (Apr→Jul 2026 for Millers Road). Use both the counterparty's email and their accounts team's email (e.g., `padirector@ahindia.com` often handles drafts even when Akber handles negotiations).

### 2. Read ALL Emails Chronologically

Do NOT rely on a single email summary. Read every message in the thread from oldest to newest. Terms evolve as each side responds.

**Extract the full negotiation arc:**
- Initial proposal → Counter-offer → Acceptance / Modification → **Final agreed position**
- Note where terms **change** between emails (this is where the draft goes wrong)
- Watch for "as discussed on the phone" patterns — these reference **off-channel agreements** that won't appear in any email
- Note what each side **explicitly accepted** vs what they **did not respond to** (silence ≠ agreement)
- Watch for the counterparty's **accounts/PA team** sending drafts/redlines — they may contain additional agreed terms

**Key data points to extract from every lease negotiation:**
- Parties (LESSOR/LESSEE — note who is who)
- Lease term and lock-in periods (landlord vs tenant)
- Rent amounts (per floor/phase), escalation formula, base month
- Security deposit (amount, timing, conditions)
- Rent-free periods (initial + per-phase)
- Handover dates (each floor/phase)
- Sub-letting restrictions (positive or negative list)
- Terrace rights / usage restrictions
- Renewal terms (if any — often missing)
- Maintenance and statutory charge responsibilities
- Any "extra" items (₹25K adjustments, parking carve-outs, etc.)

### 2a. Essential — Read the Counterparty's Draft (.docx) for Hidden Details

The emails themselves may NOT contain critical factual details like:
- **Co-owner names, PANs, ages, addresses, and share ratios** — these only appear in the counterparty's redlined/corrected draft, not in any email body
- **The exact share structure** (e.g., 30/30/20/20) — confirmed from their draft, never explicitly stated in emails
- **GPA representation** — who signs on behalf of whom
- **Corrected address/contact details** the counterparty wants used

**Workflow for extracting from counterparty's draft:**
1. Find the counterparty's attachment in Gmail (search by subject + "DRAFT" or "MILLERS")
2. Download .docx attachment via Gmail API
3. Extract text using python-docx or zipfile + XML (see Step 4)
4. Search for: "Lessor No.", "co-owner", "share ratio", "PAN", co-owner names, "GPA", addresses
5. **Cross-reference EVERY detail from the counterparty's draft** — they are the authoritative source for their own side's information. Do NOT leave placeholders like "[TO BE INSERTED]" for their details if their draft already has them filled in.
6. If the counterparty's draft differs from what you filled in, update your corrected version before sending it to anyone

**Pitfall (Jul 2026):** The corrected lease was initially uploaded with generic placeholders ("[LESSOR CO-OWNERS — TO BE INSERTED]") because I only checked the email body. The actual co-owner names, PANs, and address were sitting in Atheeq's 3.6MB .docx attachment all along — I just hadn't opened it yet. Always check ALL attachments before declaring a field "not available."

### 3. Find the Latest Legal Draft in Drive

Search Drive for files matching the property/party name. Check for:
- **DRA's legal team version** — named with DRA prefix and date, e.g. `202606xx_LeaseDeed_MillersRoad_DRARealty_vs_[Lessee]_Clean.docx`
- **Counterparty's amended version** — their redlines/edits, e.g. `MILLERS ROAD PREMSIES DRAFT LEASE DEED.docx`
- **Draft vs Clean versions** — there may be a "Draft" (with markup/notes) and a "Clean" (final-looking) version of the same document

The 7 Jul email often has the latest draft as an attachment. Check Gmail attachment IDs too.

### 4. Read the Draft Content

#### For .docx files (uploaded to Drive as binary)

Google Drive export does NOT support .docx → text conversion. Use this technique:

```python
from googleapiclient.http import MediaIoBaseDownload
import io, zipfile, xml.etree.ElementTree as ET

# Download binary from Drive
request = drive.files().get_media(fileId=file_id)
buffer = io.BytesIO()
downloader = MediaIoBaseDownload(buffer, request)
done = False
while not done:
    status, done = downloader.next_chunk()

# Extract text from .docx (which is a ZIP of XML files)
buffer.seek(0)
with zipfile.ZipFile(buffer) as z:
    xml_content = z.read('word/document.xml')
    root = ET.fromstring(xml_content)
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    texts = []
    for t in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
        if t.text:
            texts.append(t.text)
    full_text = '\n'.join(texts)
```

#### For native Google Docs files

```python
request = drive.files().export_media(fileId=file_id, mimeType='text/plain')
content = request.execute()
text = content.decode('utf-8', errors='replace')
```

### 5. Compare Each Clause Against Email Terms

For every material term in the draft, find the corresponding email agreement. Use these markers:

| Status | Meaning |
|--------|---------|
| ✅ **Match** | Clause correctly reflects the agreed email term |
| ❌ **Mismatch** | Clause contradicts the agreed term (wrong number, wrong party, wrong date) |
| ⚠️ **Partial** | Correct amount/term but wrong trigger event, formula, or condition |
| ❓**Missing** | An agreed term from email that has no corresponding clause in the draft |
| **Extra** | A clause in the draft that was never discussed or agreed in email |

### 6. Structure the Gap Analysis

Present as a comparison table directly — no preamble:

```
| # | Item | Agreed (from emails) | Draft Says | Verdict |
|---|------|---------------------|------------|---------|
| 1 | **Parties** | LESSOR=Akber/co-owners, LESSEE=DRA Realty | REVERSED — DRA shown as LESSOR | ❌ |
| 2 | **Lease Term** | 7 yrs LESSOR lock-in + 3 yrs LESSEE lock-in | 12 years | ❌ |
| ... | | | | |
```

**Order:** Critical structural errors (parties, term, amounts) → Partial matches → Missing clauses → Extras.

Then a short action list of what needs to be fixed.

## Common Pitfalls (from Millers Road Lease Review, Jul 2026)

### Parties Reversed
DRA's legal template was designed for DRA-as-Lessor projects. When DRA is the **tenant**, the LESSOR/LESSEE sections must be swapped. This error was the single biggest issue in the Millers Road draft — the lease listed DRA as the landlord of its own landlords.

Always check the party definition block before anything else. If DRA Realty Private Limited appears as LESSOR, and the counterparty's name doesn't appear at all, the parties are reversed.

### Date Format Confusion
- The email agreed GF handover date: **1 Feb 2028** (India Chai lease expires 31 Jan 2028)
- The draft said: **31 Dec 2027 / TO BE CONFIRMED**
- The counterparty's version said: **Feb 2028**
- **Fix:** Always use the latest email confirmation as authoritative
### Deposit Arithmetic — Multi-Phase Structure

"3 months' rent" is a formula, not a fixed number. For multi-floor leases with phased handover, deposit is calculated per phase:

- **Phase 1 (execution):** 3 × Rs. 4,00,000 (upper floors only) = Rs. 12,00,000
- **Phase 2 (GF handover):** additional 3 months' UF deposit (Rs. 12,00,000) + 6 months' GF deposit (Rs. 10,50,000) = Rs. 22,50,000
- **Total at full occupancy:** Rs. 34,50,000

**Key pitfall (corrected Jul 2026):** The initial draft showed only 3 months' GF deposit (Rs. 5,25,000) at GF handover. The actual agreement was: (a) additional 3 months' UF deposit bringing total UF deposit to 6 months, PLUS (b) 6 months' GF deposit. Always confirm the per-phase deposit formula against the email trail — especially the number of months per floor/phase.

But if calculated at total rent (Rs. 6,25,000/month): 3 × 6,25,000 = Rs. 18,75,000. Check which base rent rate was agreed.

### Escalation Trigger Ambiguity
"5% annual escalation" can mean:
- From the **commencement date** (first increment at month 12)
- From **month 7** (when rent starts — first increment at month 19)
- From **GF handover** (first increment 12 months after GF starts)

Each produces different amounts in different years. Confirm the trigger event from the email trail.

### Renewal Clause Missing
Standard lease templates assume a fixed non-renewing term. For DRAAS leases where the tenant makes large capital investments (structural upgrades, facade, interiors), the renewal clause is critical:

**What was agreed but missing:** After the 7-year lock-in, if the LESSEE wishes to continue:
1. Determine market rate via comparable properties OR two independent IPCs
2. LESSOR gives 20% discount to that market rate
3. All tenant improvements become property of the building but the tenant benefits from the discount

### Counterparty's Redlined Version
The counterparty often sends back a modified draft (e.g. Atheeq at padirector@ahindia.com). This draft may contain:
- Co-owner share ratios (30/30/20/20)
- Adjusted rent-free periods
- Modified handover dates
- Requests to remove names (e.g., "India Chai")

Always check the counterparty's draft for items Nishant agreed to that never made it back to DRA's legal team.
### Off-Channel Agreements (Phone / WhatsApp)

Terms agreed on phone calls and confirmed in follow-up emails are findable. But terms agreed ONLY on WhatsApp or phone are not. Common off-channel items:
- Extra ₹25,000/month adjustment
- Specific parking allocation
- Terrace usage relaxation
- Move-in date flexibility

If a term the user mentions doesn't appear in any email, flag it as "not in email trail — may be from WhatsApp/phone" and ask the user to share that source.

## Producing the Corrected Draft — Purple-Marked .docx

**Trigger:** After completing the gap analysis, the user wants you to produce a corrected lease draft with changes visibly marked.

**Technique — Create a new .docx from scratch using python-docx:**

Since the original .docx is a binary ZIP format and the corrections are structural (parties reversed, term changed, new clauses added), it's often easier to create a fresh document than to edit the existing one in-place. python-docx preserves paragraph formatting, font sizes, and alignment.

**Workflow:**
1. **Define color constants:**
   ```python
   PURPLE = RGBColor(0x80, 0x00, 0x80)    # RGB(128,0,128) — changed text
   BLACK = RGBColor(0x00, 0x00, 0x00)    # original/unmodified text
   ```
2. **Build the document section by section** — use `add_para()` and `add_mixed_para()` helper functions:
   ```python
   def add_mixed_para(parts, align=None):
       """parts = [(text, is_purple, bold), ...]"""
       p = doc.add_paragraph()
       for text, is_purple, bold in parts:
           run = p.add_run(text)
           run.font.size = Pt(10)
           run.font.color.rgb = PURPLE if is_purple else BLACK
           run.bold = bold
   ```
3. **Mark ALL changes in purple:**
   - Changed clause headers: `"2. TENURE AND DURATION [CORRECTED — was 12 years]"` in purple
   - Changed numbers/dates: purple bold
   - New clauses (e.g., renewal clause): entire section in purple with `[NEW CLAUSE]` tag
   - Changed amounts: purple
4. **Upload to Drive** as a new .docx file with a descriptive name including date and `_PurpleMarked` suffix
5. **Delete the old corrected version** if re-uploading (avoid file clutter)

**When to rebuild from scratch vs edit in-place:**
- **Rebuild from scratch:** Parties reversed, term changed, new clauses added, multiple structural changes. The original docx structure (paragraph indices) becomes unreliable after 3+ edits.
- **Edit in-place:** Minor corrections (one date, one amount, one clause title) where you can find-and-replace within the existing paragraph structure.

## Multi-Step Approval Workflow

**Trigger:** After creating the corrected lease draft, don't send it directly to the counterparty. Use a staged approval chain:

1. **Internal confirmation first** — WhatsApp or email to a joint-venture partner/team member who was involved in negotiations:
   - "Please reconfirm these commercial terms are correct before I share the updated lease"
   - Present the full term sheet as structured bullets
   - Include the actual co-owner names and share ratios (from the counterparty's draft)
2. **Wait for confirmation** before proceeding
3. **Only after internal confirmation** — send the corrected draft to the counterparty with:
   - Apology for the earlier incorrect draft
   - Summary of all key terms
   - Reference to the purple-marked changes
   - Request for review and confirmation
4. **Parallel WhatsApp nudge** — optional short message to the counterparty saying the corrected draft has been shared and the earlier version should be ignored

## Verified Against
- Millers Road / India Chai lease negotiation (Akber Hussain, Apr–Jul 2026)
- 10+ email thread across 3 Gmail accounts
- .docx lease draft from Drive (19KB, 26k chars extracted)
