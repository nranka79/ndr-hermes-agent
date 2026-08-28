---
name: insurance-claim-escalation
description: "Insurance claim escalation & grievance drafting — email evidence analysis, regulatory compliance timeline, grievance email with attachments, IRDAI/Ombudsman preparation."
version: 1.0.0
author: Hermes Agent
license: MIT
---

# Insurance Claim Escalation & Grievance Drafting

Class-level skill for handling insurance disputes — both **motor insurance claim delays** and **life insurance policy revival/rejection** disputes. Covers evidence compilation, regulatory analysis, legal response drafting, and IRDAI/Ombudsman preparation.

## Life Insurance Revival Disputes — Special Considerations

This class of case arises when a life insurer (e.g., Bajaj Allianz Life, LIC, ICICI Prudential) rejects revival of an existing policy or denies a claim. The legal framework differs significantly from motor insurance.

### Key Legal Framework

| Principle | Source | Application |
|-----------|--------|-------------|
| **Section 45, Insurance Act 1938** | After **3 years** from policy issuance, the policy **cannot be questioned on any ground whatsoever** | A 5-year-old policy's revival cannot be rejected on grounds that the insurer could have raised at inception |
| **Revival ≠ New Contract** | Supreme Court in *LIC v. Dharam Vir Anand* (1998) 8 SCC 167 and *LIC v. G.M. Channabasamma* (1991) 1 SCC 357 | Revival restores the original contract; financial re-underwriting at revival is impermissible |
| **Insurer cannot benefit from own wrong** | Contract law + *LIC v. B.R. Kusnoor* (2000) 10 SCC 544 | If the insurer unilaterally reversed the premium without notice and caused the lapse, it cannot then penalize the policyholder |
| **IRDAI PPI Regulations 2024, Reg 8** | Revival decision must be communicated **within 7 days** of receiving all documents | A 94+ day delay with "one more thing" pattern violates the TAT and constitutes deficiency |
| **Section 45 bar includes revival** | The 3-year clock runs from policy issuance (NOT revival) for questioning original underwriting | Insurer cannot revive the right to challenge the policyholder's financial eligibility that was settled at inception |

### Key Case Law for Life Insurance Disputes

| Case | Citation | Holding |
|------|----------|---------|
| **Rekha Jain v. Bajaj Allianz Life Insurance** | Delhi State Consumer Commission, Complaint No. 159/2018 | Bajaj Allianz rejected revival on "financial inconsistency" — held deficiency of service, ₹2L awarded. Most directly on point for Bajaj Life disputes |
| **Avinash Bhosle v. ICICI Prudential Life Insurance** | NCDRC, 2021 SCC OnLine NCDRC 188 | Rejection of revival on financial underwriting grounds held arbitrary, policy ordered revived |
| **LIC v. Dharam Vir Anand** | (1998) 8 SCC 167 (SC) | Revival revives original contract — insurer cannot impose new conditions |
| **LIC v. G.M. Channabasamma** | (1991) 1 SCC 357 (SC) | Revival does not create a new contract |
| **Mithoolal Nayak v. LIC** | AIR 1962 SC 814 (SC) | Landmark Section 45 judgment: after 3 years, policy cannot be questioned except for fraud with strict evidentiary standards |
| **LIC v. B.R. Kusnoor** | (2000) 10 SCC 544 (SC) | If insurer fails to intimate decision on revival within reasonable time, policy deemed revived |
| **K. Rajendran v. LIC** | 2019 SCC OnLine Mad 8910 (Madras HC) | After 3-year Section 45 mark, insurer cannot question policy at revival stage |
| **Surinder Kaur v. LIC** | III (2020) CPJ 253 (NCDRC) | Financial underwriting at revival stage is impermissible |
| **Rekha Jain v. Bajaj Allianz** | (Delhi State Commission) | Most directly relevant — Bajaj Allianz rejected revival on financial grounds, held deficiency of service |

### Life Insurance Dispute Workflow

#### Phase A: Identify the Nature of the Dispute
- Is it a **new claim denial** (policy in force, death/maturity claim rejected)?
- Is it a **revival rejection** (policy lapsed, revival requested, rejected)?
- Is it a **premium/lapse dispute** (insurer reversed premium without notice)?
- Has the policy crossed the 3-year mark under Section 45?

**If the policy is >3 years old**, Section 45 is a complete bar to questioning its validity. Note this as the single strongest argument.

#### Phase B: Gather Evidence
1. **Bank statements** showing premium payments and any reversals
2. **Renewal Payment Confirmation** emails from the insurer (KEY evidence)
3. **Email thread** with the insurer — search Gmail by policy number
4. **WhatsApp chat** with customer service — export and compile as interactive HTML transcript with linked Drive media (see `document-dossier-compilation` skill, `references/whatsapp-evidence-html.md`)
5. **Form 16s, salary slips, IT returns** — income documentation if financials are questioned
6. **Medical records** — if medical underwriting is the basis
7. **Policy bond** — original policy document showing terms

#### Phase C: Analyze the Rejection Grounds
- **"Insufficient financial documents"** → This is legally weak for a >3-year policy. Section 45 bars questioning financial eligibility. Even on the merits, ₹1.2Cr income for ₹3Cr cover is a 2.5x ratio (industry norm is 10-15x). Premium-to-income ratio of 0.6% is negligible.
- **"Medical/discrepancy in health declaration"** → Different analysis — check if the MER (Medical Examination Report) was generated by the insurer's own diagnostic centre and whether the discrepancy is material.
- **"MER error"** → If the insurer's own diagnostic centre produced an inaccurate MER (e.g., statin 20mg vs actual 10mg), the insurer is responsible for its own record. The policyholder cannot be prejudiced by the insurer's error.

#### Phase D: Draft Legal Response Email
The response should be a **Reply-All on the existing email thread** using the MIME approach (gws_auth.build_service + drafts().create()) for correct threading and CC handling.

**Always CC the policyholder's internal team** on insurance/regulatory emails:
- Roshini Ranka — rnr@draas.com
- Eshwari Chamundeshwari — echamundeshwari@draas.com

**Structure of the legal response email:**
1. **Section 45 bar** — Cite the absolute bar after 3 years. Quote the section text.
2. **Revival ≠ new contract** — Cite Supreme Court precedents. Financial re-underwriting is impermissible.
3. **Insurer caused the lapse** — Document the premium reversal without notice.
4. **Financial norms satisfied** — Even on merits, show income-to-cover ratio is within norms.
5. **IRDAI TAT violated** — 94+ days vs mandated 7 days under PPI 2024.
6. **Case law** — Cite Rekha Jain v. Bajaj Allianz (identical facts, compensation awarded).
7. **Demand letter** — Specific demands: reversal of rejection, restoration of cover, apology, interest.
8. **Escalation warning** — IRDAI IGMS → NCDRC → Ombudsman, 7-day deadline.

**Tone:** Strong, legally precise, formal. Cite specific section numbers and case citations. End with a clear deadline and consequences.

#### Phase E: Filing Options
When the user wants to escalate beyond the email:
1. **IRDAI Integrated Grievance Management System (IGMS)** — https://igms.irdai.gov.in — fastest route, IRDAI can direct binding revival
2. **Consumer Court (NCDRC)** — For policies >₹2Cr, the National Commission has unlimited pecuniary jurisdiction for deficiency of service
3. **Insurance Ombudsman** — For claims up to ₹30L (varies by state)
4. **High Court writ petition** — For expedited remedy on high-value policies

### Evidence Compilation for Life Insurance Cases

1. **Email evidence** — Download .eml files from Gmail, convert to PDF using `fpdf2` (see `document-dossier-compilation` reference `eml-to-pdf-conversion.md`)
2. **WhatsApp evidence** — Export chat (with media), rename garbled filenames descriptively from chat context, upload to Drive, create interactive HTML transcript with hyperlinked media (see `references/whatsapp-evidence-html.md`)
3. **Bank statements** — Already PDF, upload to Drive
4. **Create a single Drive folder** with the case name for all evidence
5. **Case analysis document** — HTML document summarizing timeline, violations, legal strategy

## Workflow

### Step 1: Fetch all claim-related emails
Search Gmail with claim number, policy number, vehicle number, surveyor email, and NIC handler email:

```python
from tools.gws_auth import build_service
gmail = build_service('gmail', 'v1')
query = 'CLAIM_NO OR POLICY_NO OR VEHICLE_NO OR surveyor_email'
results = gmail.users().messages().list(userId='me', q=query).execute()
```

Get **all** messages in the conversation, not just search hits. Resolve the full thread for each message to ensure no gaps.

### Step 2: Extract full metadata per email
For each email, capture:
- Full Date (RFC 2822 format preserved)
- From / To / Cc
- Subject (full, unshortened)
- Body text (first 500 chars for summary, full for key emails)
- Attachment names and counts

### Step 3: Build chronology
Sort all emails by date. Identify phases:
- **Phase 1 — Initiation**: Claim intimation, acknowledgment, document submission
- **Phase 2 — Survey**: Surveyor appointment, inspection, report submission
- **Phase 3 — Silence**: Any period >7 days without insurer communication = 🔴 flag
- **Phase 4 — Escalation**: First follow-up, internal forwarding, ticket creation
- **Phase 5 — Failure**: Document loss admission, resubmission, broken communication

Highlight gaps between events — e.g. "43 days of silence from NIC" is a key fact.

### Step 4: Create A4-printable timeline document
Create an HTML document designed for **print-to-PDF (A4)** with:

**Required sections:**
- **Cover header**: Claim no., policy no., vehicle, all parties, date prepared
- **Status bar**: Visual flow showing each phase (color-coded green→amber→red)
- **Key stats row**: Days since claim, days at workshop, days since survey, days since IRDAI deadline
- **Full timeline**: Every email as a card with date, who→whom, key statement, badge (compliant/failure/disputed)
- **"Who said what to whom" table**: Quick-scan reference showing each communication
- **Regulatory compliance table**: IRDAI regulation vs prescribed timeline vs actual vs violation status
- **Failure analysis**: Each NIC/insurer failure listed separately with evidence quotes from emails
- **"What insured did right"**: Counterpoint showing insured's compliance at every step
- **Executive summary**: 2-3 paragraph overview

**Naming convention for output files:**
- Timeline document: `YYYYMMDD_ClaimTimeline_CLAIMNO.html`
- Grievance email draft subject: `GRIEVANCE: Claim No. [no] — Policy [no] — [X] Days & Regulatory Violations`

**"Who said what to whom" communication table format:**
Create a phased table with columns: Date | From | To | Key Statement. Group rows by phase:
- Phase 1: Initiation (claim → surveyor appointed)
- Phase 2: [Silence period marked with 🔴 header noting duration]
- Phase 3: Escalation & Discovery of Failures
- Phase 4: Resubmission & [Current Status]

Each entry should quote the key statement verbatim from the email. Use bold for admissions (e.g. "documents were misplaced"). This table is what the user specifically requests for "some educating party to read and understand."

**HTML timeline document visual structure (see templates/timeline-html-template.html):**
- `@page { size: A4; margin: 1.8cm 1.5cm; }` — print-to-PDF ready
- Cover header: Claim/policy/vehicle/parties in a 2-column grid
- Status bar: Phases in sequence (green → green → amber → red → gray) with dates
- Stats row: 4 stat cards showing elapsed days per phase
- Timeline: vertical line (2.5px, #d5dbdb) with circular dot indicators per event
  - `.event.positive::before` = green dot (insured did right)
  - `.event.negative::before` = red dot (insurer failure)
  - `.event.warning::before` = amber dot (disputed/questionable)
  - `.event.neutral::before` = blue dot (standard process)
  - `.event.failure::before` = red dot (critical failure)
- Event cards: date (uppercase, small), title, body, meta with badge
- Badge classes: .badge-green (✅ COMPLIANT), .badge-red (🔴 VIOLATED), .badge-amber (⚠️ DISPUTED), .badge-blue (ℹ️ STANDARD)
- Regulatory table: .reg-table with .violation and .compliant cell classes
- Failure analysis: .blame-box with red border
- "What insured did right": .right-grid with green-bordered cards (2-column grid)
- Communication table: .comm-table with .phase-header rows grouping phases
- Page breaks before major sections: `.page-break { page-break-before: always; }`

**Gmail attachment extraction pattern:**
```python
from tools.gws_auth import build_service
import base64

gmail = build_service('gmail', 'v1')
msg = gmail.users().messages().get(userId='me', id=MSG_ID, format='full').execute()

def extract_attachments(msg, download_dir='/tmp/attachments'):
    os.makedirs(download_dir, exist_ok=True)
    attachments = []
    parts = [msg['payload']]
    while parts:
        part = parts.pop(0)
        if 'parts' in part:
            parts.extend(part['parts'])
        if part.get('filename') and part.get('body', {}).get('attachmentId'):
            att = gmail.users().messages().attachments().get(
                userId='me', messageId=msg['id'],
                id=part['body']['attachmentId']
            ).execute()
            data = base64.urlsafe_b64decode(att['data'])
            fpath = os.path.join(download_dir, part['filename'])
            with open(fpath, 'wb') as f:
                f.write(data)
            attachments.append(fpath)
    return attachments
```

**MIME multipart draft creation (HTML body + multiple attachments):**
```python
import email.mime.multipart, email.mime.base, email.mime.text, email.utils, base64, os, mimetypes

def create_draft_with_attachments(gmail, to_list, cc_list, subject, html_body, attachment_paths):
    msg = email.mime.multipart.MIMEMultipart('mixed')
    msg['To'] = ', '.join(to_list)
    msg['Cc'] = ', '.join(cc_list)
    msg['Subject'] = subject
    msg['Date'] = email.utils.formatdate(localtime=True)
    msg['From'] = 'me'

    # HTML part
    alt = email.mime.multipart.MIMEMultipart('alternative')
    alt.attach(email.mime.text.MIMEText(html_body, 'html'))
    msg.attach(alt)

    # Attachments
    for fpath in attachment_paths:
        with open(fpath, 'rb') as f:
            part = email.mime.base.MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
        email.encoders.encode_base64(part)
        filename = os.path.basename(fpath)
        part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
        ct, _ = mimetypes.guess_type(fpath)
        if ct:
            part.set_type(ct)
        msg.attach(part)

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    draft = gmail.users().drafts().create(userId='me', body={'message': {'raw': raw}}).execute()
    return draft['id']
```

**Visual design rules:**
- A4 page size (`@page { size: A4; margin: 1.8cm 1.5cm; }`)
- Color-coded events: 🟢 positive/green, 🔴 failure/red, 🟡 warning/amber, 🔵 neutral/blue
- Timeline with vertical line and dot indicators
- Tables with dark headers and alternating row colors
- Event badges for quick scanning
- Page breaks before major sections
- Max font size 10-11pt body, compact spacing

### Step 5: Check contacts before sending
Always check if all email recipients exist in:
1. **DRAAS Google Contacts sheet** (use `gws_sa.build_service('sheets', 'v4', 'ndr@draas.com')`)
2. **Google Contacts / People API** (use `gws_auth.build_service('people', 'v1')`)

If missing, add the contact to both. Use the dual-store pattern:
- Google Contacts: `people.contactGroups().create()` or `people.otherContacts().copyOtherContactToMyContactsGroup()`
- DRAAS Sheet: Append row with name, email, phone, role, organization, notes

### Step 6: Draft grievance email
**IMPORTANT — always create as DRAFT, never send without user confirmation.**
(This is Nishant's specific preference: "confirm draft first for outbound email.")

Compose the email with:

- **To**: Grievance officer + NIC CS + broclaims
- **CC**: Handler (Azeem), Surveyor, internal team (Bharat, Roshini), any relevant parties
- **Subject**: `GRIEVANCE: Claim No. [no] — Policy [no] — [X] Days & [Status]`

**Body must include:**
- Complete timeline (condensed)
- Regulatory violations table
- Specific demands numbered (payment, acknowledgment, interest, compensation, explanation)
- Escalation warning (Ombudsman → IRDAI → Consumer Court)
- Attachment list

**Attachments — extract from email chain:**
1. Find the surveyor's email with the most attachments (typically Venkatesh's resubmission email with 30+ files)
2. Download every attachment via Gmail API: `gmail.users().messages().attachments().get()`
3. Also attach the timeline HTML document created in Step 4
4. Upload all to a temp dir, then attach via multipart MIME message in Gmail API draft

### Step 7: Confirm with user
Present the user with:
- Draft link (Gmail drafts URL)
- Summary of TO/CC/Subject/attachment count
- Ask: "Review & approve", "Send now", or "Make changes"

## User style preferences (Nishant)
- A4-printable HTML documents preferred over PDF generation via libraries
- "Who said what to whom" event mapping — chronological communication table with quotes
- IRDAI regulation vs actual timeline comparison table — always include this
- Color-coded event badges: green=compliant, red=failure, amber=warning, blue=neutral
- Key stats row at top showing days elapsed for each phase
- Executive summary at end for quick reading by adjudicating party
- All attachments from original email chain must be included — not just referenced

## Follow-Up on Existing Complaint

This is a distinct workflow from drafting a new grievance — the complaint was already filed, the insurer/IRDAI acknowledged it, and now you need to check whether a response has arrived.

### When to use

The user says "check if there's any reply from [insurer]" or "any update on my IRDAI complaint" — referring to an existing complaint, not a new one.

### Phase A: Gather identifying details

Every insurance complaint has up to three tracking IDs. Collect whichever are known:

| ID | Format | Source |
|----|--------|--------|
| **Policy number** | `0444146783` | Policy bond, earlier emails |
| **Service request / complaint ref** | `142016013` | Insurer's auto-acknowledgement email |
| **IRDAI Bima Bharosa token** | `07-26-018199` | IRDAI acknowledgement email (`igmsemailacknowledgement@irdai.gov.in`) |

If the user only mentions "the complaint" without IDs, search Gmail for the insurer's domain (`@bajajlife.com`, `@irdai.gov.in`, etc.) and the user's known policy numbers to find the thread first.

### Phase B: Search Gmail for replies

Run **three separate searches** across the user's accounts (primary and forwarded):

```python
# Search 1 — by policy number (most reliable)
gmail_search(query='0444146783', max=20)

# Search 2 — by IRDAI token
gmail_search(query='07-26-018199 OR 07.26.018199', max=10)

# Search 3 — by insurer domain + service request number
gmail_search(query='bajajlife.com AND 142016013', max=10)
```

**Multi-account check:** Insurance emails may arrive on a different email than the one used to file the complaint (e.g., complaint filed from `ndr@draas.com` but insurer replies to `ndr@drahomes.in`). Check:
1. The primary inbox (`google-draas`) — forwarder labels may catch secondary-account replies
2. Try `gmail_search(query=..., service_name='google-ahfl')` if the secondary account was involved

### Phase C: Interpret IRDAI Bima Bharosa status emails

IRDAI sends auto-generated status updates from `igmsemailacknowledgement@irdai.gov.in`. The status text is embedded in fixed HTML boilerplate — extract the key line from the body:

| Status phrase in email | Meaning | Action needed |
|---|---|---|
| `has been Acknowleged to by` (sic) | Insurer received your complaint from IRDAI portal | None — complaint is in queue |
| `has been Pending to by` (sic) | Insurer has taken up the complaint, pending resolution | Await response, note the date as start of 14-day clock |
| `has been Resolved to by` | Insurer submitted resolution to IRDAI | Check Gmail for insurer's resolution email next |

**Spelling note:** IRDAI emails consistently misspell "Acknowledgement" as "Acknowlegement" in the subject and body. This is normal — don't flag it.

**Timeline expectations (per IRDAI PPI Regulations 2024):**
- Insurer must **acknowledge** the complaint within the same working day (IRDAI auto-update confirms this)
- Insurer should **resolve** within **7 calendar days** of acknowledgement (what they typically commit to)
- IRDAI allows up to **14 calendar days** maximum
- If the 14-day window passes with no resolution, the user should escalate via IRDAI Bima Bharosa portal: https://bimabharosa.irdai.gov.in/ or call 155255

### Phase D: Key fields to report to the user

When presenting the results, include:

- **Who replied** — name, designation (e.g., Darshana Darwatkar, Assistant Manager – Escalation & Grievance Management)
- **Service request / complaint reference** — the tracking number the reply references
- **What they said** — e.g., "reviewing as priority, 7-14 day timeline"
- **Deadline** — calculate the 7-day and 14-day dates from the reply timestamp
- **Any attachments** — resolution letters, updated policy documents
- **Unread flag** — note if the email is still unread (important prompt to user)

### Phase E: When deadline has passed with no resolution

If the 14-day window has lapsed and only "pending" status updates exist:

1. Advise the user to escalate via IRDAI Bima Bharosa portal
2. Draft a follow-up email referencing the original complaint + service request + token number
3. Note the regulatory violation (missed IRDAI TAT) in the escalation
4. Recommend contacting the insurer's Grievance Redressal Officer (typically `gro@[insurer].com`)

### Phase F: Resolution & premium-payment delegation (the victory lap)

When the insurer finally approves renewal/revival and asks the policyholder to pay missed premiums, the drafting pattern flips from adversarial to grateful-but-delegating. Confirmed on Bajaj Life policy 0444146783 (Aug 2026):

**Reply-all structure:**
- **To**: the insurer contact who confirmed (e.g. Rohit Sundarka, Cluster Manager — Branch Operations, Bangalore 1, `Rohit.Sundarka@bajajlife.com`, 9692241533)
- **Cc**: internal team — **Roshini Ranka (rnr@draas.com)** + **Eshwari Chamundeshwari (echamundeshwari@draas.com)** (same CC pair used for grievance emails)
- **Thread**: reply on the existing thread (same threadId), so all prior escalation context is preserved for the internal team

**Body elements (user-specified order):**
1. Thank the insurer team; acknowledge the long follow-up but note satisfaction that it's resolved fairly — especially as a long-term paying customer
2. **@Eshwari** — explicit instruction block: (a) review the premium being sought and verify it wasn't already paid earlier, (b) pay via the insurer's online app, failing which bank transfer, (c) notify once done so the user can confirm to the insurer, (d) track this and all future payments until acknowledgement is received
3. **Interest-waiver clarity** — state explicitly that interest is waived (as assured personally) and only the missed premiums are payable since this is a continuation of the existing policy
4. Re-attach the insurer's original attachments — **when CC'ing internal team on a reply-all, the original attachments must be included** so the team receives them (user preference: "they should receive the attachment as well")

**Pitfall — the "premium demand" attachment may be medical reports, not a bill:** In this case the attachment Rohit sent was the policyholder's 2021 medical examination reports (ECG + lab), NOT a premium demand. The premium figure (annual ₹73,066, sum assured ₹3 Cr) had to be reconstructed from earlier thread emails. Don't assume the attachment contains the amount — if it doesn't, report that and note the annual premium from thread history, flagging that the exact figure must be confirmed from the app/renewal demand before payment.

#### Phase G: Post-payment chase (interest waiver + policy-live confirmation) — Aug 2026

After payment is made, the ball is with the insurer. Verified flow on Bajaj Life policy 0444146783:

**The interest-waiver protocol (from Rohit Sundarka, 10 Aug 2026):** "Inform us an hour before paying. We will waive off the Interest just before the payment. As, once the Interest is waived we have to make payment on same day." → i.e. the waiver is applied by the insurer immediately before payment, and payment MUST land same-day. The user's confirmation email to the insurer must state explicitly: payment made, interest waiver to be applied as assured, confirm no further payment pending, confirm policy live.

**Dead addresses on the Bajaj Life thread (all bounce 550 recipient-not-found — never use again):**
- `Kalpana.M@bajajlife.com`
- `Livish.J509@bajajlife.com`
The working channel is **Rohit.Sundarka@bajajlife.com** (he replies reliably). Also `nayana.as@bos.bajajlife.com`, `Mohd.042@bajajlife.com`, `Manohar.Sur@bajajlife.com`, `Prashant.Chaudhari@bajajlife.com`, `Aarti.Patil@bajajlife.com`, and `customercare@bajajlife.com` (Rohit Gupta, Deputy Manager — Escalation & Grievance Management). Sending to the dead addresses generates postmaster bounces in the thread — strip them from To when chasing.

**Chase email structure (once payment made, awaiting confirmation):**
1. State cheque/UTR + "payment made, gone to bank, cleared"
2. Ask them to: update policy account to reflect payment, apply interest waiver as assured, confirm no further payment pending
3. Ask: confirm policy is now live and active + send updated policy documents
4. Await their confirmation — this is now an AWAITING RESPONSE item, chase again if no reply within 48h (Rohit has been responsive within ~1-3 days on this thread).

**UTR-level confirmation chase (insurer confirms UTR1, requests bank statement for UTR2) — Aug 2026:**
When the insurer credits multiple premiums and confirms only some UTRs, expect a per-UTR chase. Verified on Bajaj Life policy 0444146783 (12 Aug 2026):
- Rohit confirmed **UTR1 KKBKH26221976647000625 (₹61,920) credited**, but for **UTR2 KKBKH26223627389000626 (cheque 000626)** his Finance team "requirement was raised seeking bank statement".
- The draft reply-all pattern that worked: **To**: insurer contact (drop the two dead addresses Kalpana.M / Livish.J509); **Cc**: internal handler **Sarthak Sharma <admin3.blr@draas.com>** + Roshini + Eshwari + the working Bajaj CCs (Manohar Sur, Mohd 042); body acknowledges the confirmed UTR, states the second amount was indeed debited, and gives Sarthak a precise task block: obtain bank statement showing the second debit (UTR + cheque no.), **highlight only that debit entry, redact/blacken ALL other transactions and account details**, attach the redacted statement to the thread so the insurer's Finance team can confirm receipt.
- Key framing the user wants repeated to insurers: *"the amount has indeed been debited from our bank account and should reflect as a credit to Bajaj Life"* — i.e. debit proof ⇒ credit must exist.
- Bank-statement redaction for proof-of-payment is a recurring need: highlight one row, blacken everything else, send as attachment. Never send a raw full statement.

**IRDAI escalation already filed:** Bima Bharosa token **07-26-018199**, plus direct email to `irda@irdai.gov.in` (8 Aug 2026). Keep the token handy for the next escalation rung.

## Health Insurance TPA Claim (MediAssist / Royal Sundaram) — KDR Pre-op Reimbursement

Distinct sub-workflow: a **health reimbursement claim** (pre/post-hospitalization) filed through TPA **MediAssist** for insurer **Royal Sundaram** — as opposed to the life-insurance revival dispute above. Same drafting discipline, different entities and a classic TPA-vs-insurer pass-the-parcel failure mode.

### Key entities (verified Aug 2026 — Kanta Ranka claim, policy LLA0016946000107/LLA1/Elite)
- **Patient**: Kanta D. Ranka (KDR, mother of policyholder), DOB 21/06/1958
- **Insurer**: Royal Sundaram General Insurance — policy LLA0016946000107/LLA1/Elite, sum insured ₹1.5 Cr, continuously renewed since 2018
- **TPA**: Medi Assist India — `claims@mediassistindia.com` / `claims@mediassist.in` / `customercare@mediassist.in` (auto tickets: 37878743, 38884946)
- **Royal Sundaram contacts**:
  - Mohammed Aliraza — `Mohammed.Aliraza@royalsundaram.in`, +91 7259253339 (asked for docs, responsive)
  - Iqbal Singh Panesar — `Iqbalsingh.Panesar@royalsundaram.in` (escalation target)
  - Sabeena Sulthana N — `care@royalsundaram.in` (customer service, replies in ~1 day, says "revert in 2 working days")
  - ⚠️ **`grievance@royalsundaram.in` is DEAD (550 access denied)** — bounced twice (8 & 10 Aug 2026). Do NOT use for escalation; use `care@royalsundaram.in` or Iqbal Panesar directly.
- **Broker / coordinator**: Sudhish K T — `sudhish@eurydice.co.in` (Ashwin Bni Insurance / Eurydice), "Business Head"; escalates on the client's behalf. The user's trusted insurance point of contact.
- **Internal (DRAAS) handlers**: Sarthak Sharma (`admin3.blr@draas.com` — the "Sartak" the user refers to) sends documents to the insurer; Eshwari Chamundeshwari, Roshini Ranka, Bharat Hawaldar on CC.

### The pass-the-parcel failure mode (this claim, Jul–Aug 2026)
1. Claim submitted to MediAssist 16 Jul (pre-op ₹52,110, stapedotomy, Trustwell Hospital) → auto-ticket, then canned "submit via portal" replies.
2. Broker Sudhish escalates to Iqbal Panesar (Royal Sundaram) 31 Jul.
3. Royal Sundaram's Mohammed Aliraza asks for documents 4 Aug → Sarthak sends full set same day.
4. User escalates 8 Aug → `grievance@` bounces; MediAssist creates new ticket.
5. **11 Aug: Royal Sundaram says "our claims team has not received the claim documents till now — kindly provide us the acknowledgement copy."** → Insurer claims no docs despite broker+TPA+handler all confirming submission.

**Lesson:** when the insurer claims non-receipt, the fix is to send the **acknowledgement receipts** (TPA ticket IDs + the email chain where the insurer's own rep requested docs and the handler sent them) back to the insurer's care address, cc broker + escalation. Never assume the TPA and insurer share a document pipeline — prove submission with receipts.

**Escalation email drafting pattern (user-specified, Aug 2026) for the TPA pass-the-parcel:**
1. **Recipients**: ALL Royal Sundaram addresses in To (care@, Mohammed.Aliraza@, Iqbalsingh.Panesar@, renewal.info@) + the TPA's customercare@; Cc broker Sudhish + internal handler Sarthak + Roshini + Eshwari + Bharat + all MediAssist claim addresses (claims@mediassistindia.com, claims@mediassist.in). Never send to dead `grievance@royalsundaram.in` — it bounces.
2. **Structure**: numbered facts list (submission date + ticket ID → follow-up + ticket → resubmission on request → escalation → "claims team has not received" claim), then the reframe: *"We bought this policy from Royal Sundaram — we have nothing to do with Medi Assist, which is YOUR appointed TPA"*; the client is a top-premium payer (₹1.5 Cr Elite, renewed since 2018) being run pillar-to-post.
3. **Explicit demands**: (a) acknowledge receipt + give a claim number and processing timeline; (b) **do NOT send another generic "no documents received" email** — proof of submission is on the thread; (c) if a different format is required, say so explicitly.
4. Draft via **direct MIME** (build_service + drafts().create with In-Reply-To/References/threadId) so To/Cc are exact — the bridge `draft_reply_create` auto-populates To from the last message's sender and cannot reliably hit multiple To addresses.

### Reimbursement claim email skeleton (worked for KDR)
- Subject: `Reimbursement Claim - <Patient> - Policy <No>/<Plan> - <Expense Type> - <Procedure> - <Hospital> (<Month Year>)`
- Body blocks: policy holder/patient details table (policy no, insurer, sum insured, commencement, DOB, contact, PAN, bank account+IFSC), hospitalization details, expenses claimed with amounts, 30-day pre-hosp window dates, attached bills/documents.
- CC: broker, internal team (Eshwari, Roshini, Bharat).

### Claims follow-up cadence
- Submit → auto-ack ticket. If no substantive reply in **13 days** → follow-up email (user did this 29 Jul).
- Canned replies ("submit via portal", "post-hosp only after main claim") → escalate via broker to insurer's named contact.
- After insurer asks for docs → handler sends same day; log exactly when.
- If insurer claims non-receipt → reply with acknowledgement copy + ticket IDs (this is where the claim stands Aug 2026).


## Templates
- `templates/timeline-html-template.html` — Reusable A4-printable HTML scaffold for timeline documents. Copy, fill `[PLACEHOLDERS]`, add events, and deliver to Drive as an HTML file (Open in Drive → File → Print → Save as PDF).

## References
See `references/` directory for:
- `irdai-regulations.md` — Key IRDAI (Protection of Policyholders' Interests) Regulations, 2017 timelines and provisions

## Pitfalls
- **Email search might miss CC'd emails** — always resolve the full thread, don't rely on search alone
- **Surveyor emails may not have been CC'd to the insured** — the submission email to "Madam" was not CC'd to Nishant. You may need to rely on the surveyor's later confirmation email
- **Document loss admission is often buried** — the surveyor may tell the insured separately from the insurer. Read all emails carefully
- **30-day vs 45-day payment window** — IRDAI Reg 10(5) = 30 days from survey report; Reg 10(5A) = 45 days max. Always calculate both deadlines and note which is approaching
- **Attachments in Gmail API** — `users.messages().attachments().get()` returns base64-encoded data. Decode with `base64.urlsafe_b64decode()` before saving
- **Large attachments** — Gmail 25MB limit. If total attachment size exceeds this, use Drive folder share instead and note in email body
- **Cloud IP blocks on YouTube** — If trying to fetch video evidence/transcripts from YouTube, note that cloud-hosted IPs (this server) are blocked by YouTube. Use `web_search` to find video descriptions/titles via oEmbed API, but transcript extraction will fail. Workaround: ask user to paste transcript text manually.
- **Client-side Gmail draft link format**: `https://mail.google.com/mail/u/0/#drafts?compose=r-<DRAFT_ID>`
