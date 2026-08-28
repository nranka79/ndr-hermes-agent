# Insurance Claim Escalation Email — Workflow & Template

**Trigger:** User reports an insurance claim that is being delayed by the insurer or surveyor, and instructs you to "write a strong email" citing regulations.

## Context (from Jun 2026 session)
- Insurer: National Insurance Company Ltd (public sector)
- Policy: Motor Private Car Package (UIN: IRDAN058RP0034V01100001)
- Claim: Windscreen replacement (Own Damage) — straightforward, no third-party
- Issue: Glass replaced, invoice raised, surveyor unresponsive for 3+ weeks
- Surveyor using 24hr disappearing WhatsApp messages — evading accountability

## Core IRDAI Regulations to Cite

| Regulation | Provision | Key Detail |
|---|---|---|
| **IRDAI (Protection of Policyholders' Interests) Regulations, 2017 — Reg 10(4)** | Surveyor must submit report within **30 days** of appointment | Insurer can extend up to 6 months (aggregate) but MUST communicate to policyholder |
| **IRDAI (PPI) Regulations, 2017 — Reg 10(5)** | Insurer must settle or reject claim within **30 days** of receiving final survey report | If report incomplete, insurer must request docs in writing within 15 days; clock resets |
| **IRDAI (PPI) Regulations, 2017 — Reg 10(5A)** | **Interest at 2% above RBI bank rate** payable from date claim ought to have been settled | Consumer courts routinely award 12-18% p.a. for deficiency |
| **IRDAI (Surveyors & Loss Assessors) Regulations, 2015 — Reg 10** | Surveyor must submit report within 30 days | Non-compliance attracts de-empanelment |
| **Consumer Protection Act, 2019 — Sec 2(11)(c)** | "Deficiency" includes delay in insurance claim settlement | Grounds for consumer complaint |
| **IRDAI Master Circular on Motor Insurance (Jan 2018)** | Cashless repair authorisation within **3-8 hours** of receiving estimate | For network garages |

## Pre-Escalation Check — Did They Respond?

**⚠️ ALWAYS check Gmail for replies BEFORE drafting a new escalation email or researching escalation contacts.** The insurer may have responded while the user was unaware, changing the strategy needed.

### Workflow
1. Search Gmail for emails from the insurer's domain (`from:nic.co.in`, `from:customer.support@nic.co.in`, `from:broclaims@nic.co.in`, `from:grievance@nic.co.in`, etc.) since the last email was sent
2. Also search for replies from the surveyor (`from:venkateshg.surveyor@gmail.com`)
3. If a reply exists:
   - Read the full body (not just snippet) to understand the insurer's position
   - If it's an auto-acknowledgement/forward (e.g. "we have received your email and are forwarding it to the concerned team"), note this to the user and proceed with escalation
   - If it's a substantive response (explanation, offer, request for documents), present it to the user and adjust the escalation strategy accordingly
4. If no reply at all, proceed with escalation as planned

### Why this matters
The user explicitly asked in Jun 2026: "First check if the insurance company has responded at all or not, first let us check on that before we do anything else." Drafting escalation emails without checking wastes time if the insurer has already responded.

## Workflow (6 phases)

### Phase 1: Discover the insurance policy on Drive
- Search Drive: `name contains 'insurance' and name contains '<car brand>'`
- Also search: `name contains 'motor' and name contains 'policy'`
- Download the PDF and extract text via `pdftotext`
- Extract: Policy Number, UIN, IDV, Policy Period, Customer Care email/phone, Insurer name
- Also extract the **previous policy numbers** (found in the schedule) for context on loyalty

### Phase 2: Mine Gmail for the claim timeline
- Search: `'(car brand) (windscreen/windshield) insurance claim'`
- Search: `'Policy Number: <policy-number>'`
- Search: `'APPOINTMENT OF FINAL SURVEYOR' + vehicle number`
- Get full bodies (not just metadata) of each relevant email
- Reconstruct the timeline: Intimation → Response → Surveyor appointment → Workshop communication → Present status

### Phase 3: Find the surveyor's details
- From the surveyor appointment email: Name, email, mobile, firm
- Note: Surveyor's email may be a personal Gmail — flag this in the escalation

### Phase 4: Research IRDAI regulations (see table above)
- Use `delegate_task` if needed for deep regulatory research

### Phase 5: Draft the escalation email

**Structure:**
```
To: customer.support@nic.co.in, broclaims@nic.co.in (claims dept)
CC: surveyor@email, surveyor-appointer@insurer.co.in
BCC: complaints@irdai.gov.in (for awareness — do NOT mention in body)

Subject: URGENT: Claim Delay — Policy No. [XXXX] — Vehicle [XX-XX-XXXX] — [X] Days of Negligence

Dear Sir/Madam,

I am writing to formally escalate the unacceptable delay...

[Body sections:]
1. Claim Details (policy no, claim no, vehicle, IDV, incident)
2. Timeline (numbered from intimation to present — make the delay obvious)
3. Regulatory Violations (specific sections with numbers)
4. Demands (immediate payment, alternative coordinator, compensation, interest)
5. Ultimatum (24-48hr response or IRDAI/Ombudsman/Consumer Forum)

Regards,
[Name]
Policyholder
[Contact]
```

### Phase 6 — Alternative: Save as Gmail Draft + Cron Follow-Up Check

When the user says "save as draft and check tomorrow before sending" (or equivalent):

1. **Save both escalation emails as Gmail drafts** (NIC grievance + IRDAI complaint) — do NOT send
2. **Set a one-shot cron job** for the next morning (9 AM IST = 3:30 AM UTC):
   - Prompt: Check Gmail for replies from the insurer/surveyor since the drafts were saved
   - If no response: Notify user "No response yet from [insurer]. Drafts are ready in your Gmail Drafts. Shall I send?"
   - If response received: Summarise it and ask user how to proceed
   - Deliver result to origin chat
3. **Tell the user:** "Drafts saved to your Gmail Drafts folder. Tomorrow at 9 AM I'll check if they've responded and ask for your approval before sending anything."

**This is a deferred-action-with-monitoring pattern** — the user retains full control (nothing sent without approval) while the automatic check saves them from having to remember to follow up.

```python
# Pattern — save draft
from email.mime.text import MIMEText
import base64

msg = MIMEText(body)
msg['To'] = 'grievance@nic.co.in'
msg['Cc'] = 'nodal.officer@nic.co.in, ...'
msg['Subject'] = 'Subject'

raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
draft = gmail.users().drafts().create(userId='me', body={'message': {'raw': raw}}).execute()
```

```python
# Pattern — cron follow-up
cronjob(action='create',
    schedule='2026-06-12T03:30:00',  # 9AM IST
    name='Insurance Claim Follow-up Check',
    prompt='Check Gmail for replies from [domains]. Notify user of result.',
    deliver='origin')
```

### Phase 7: Present for approval → Send only after user confirms

**⚠️ CRITICAL:** Present the full draft to the user with all addresses and ask for explicit approval before sending. Do NOT send without confirmation.

## Email Addresses to Use

- **Insurer customer care:** customer.support@nic.co.in (or equivalent — found on policy PDF)
- **Insurer claims/bro:** broclaims@nic.co.in (if known)
- **IRDAI complaints:** complaints@irdai.gov.in
- **IRDAI IGMS portal:** https://igms.irdai.gov.in
- **Insurance Ombudsman:** File after insurer rejects/delays beyond regulatory timeline

## Key Phrases for Strong Tone

- "appalling service and absolutely appalling response time"
- "car has been out of service for close to [X] weeks"
- "24-hour disappearing messages on WhatsApp — highly unprofessional and raises concerns about accountability"
- "We have been a loyal customer with continuous insurance coverage since [year]"
- "If we do not receive a satisfactory response within 48 hours, we will be compelled to file a formal complaint with IRDAI"
- Cite specific regulation numbers — this signals you know your rights

## Stage 2 — Follow-Up Escalation (After Surveyor Responds)

After sending the Stage 1 strong legal email, the surveyor may reply with information (report submission date, manager's contact). The follow-up email shifts target and tone:

**New target:** The insurance manager (not the general support address or surveyor)

### Stage 2 Tone Variants — Choose Based on User Instruction

| Variant | Tone | When to Use | Escalation threats in body? | Regulations cited? | Specific deliverables requested? |
|---------|------|-------------|-----------------------------|-------------------|----------------------------------|
| **A — Frustrated but cooperative** | Firm, cites regulations, expresses confusion about delay, asks for communication | General follow-up | Yes — 24-48hr ultimatum | Yes | No |
| **B — Soft on surveyor, hard on insurer** | Acknowledges surveyor's circumstances ("for whatever his personal compulsions"), full regulatory citations against insurer | User says "go soft on Venkatesh" | Yes — against insurer only | Yes | No |
| **C — No threats, just push** | Factual timeline + regulations as context (not threats), requests call, no ultimatum | User says "let's not threaten IRDA or anything, just push it" | **No** — omit all escalation references | **Yes** — regulations as factual context, not threats | No |
| **D — Pure Cooperative (no regulations, no threats)** | Purely factual request, no legal framing. Expresses surprise at delay. Offers to mediate surveyor/insurer mismatch. | User says "let's not talk about regulations" or "don't cite regulations" | **No** — omit all escalation references | **No** — omit ALL regulatory citations | No |
| **E — Cooperative but Firm** | Regulations cited as factual context (not threats). Asks for three specific deliverables. Emphasizes "no fault of ours". | User says "cooperative but firm" or wants regulations mentioned without escalation threats. | **No** — omit all escalation references | **Yes** — cited as factual context | **Yes** — receipt ack, payment date, vehicle release date |

**⚠️ CRITICAL (Nishant, Jun 2026, updated Jun 12):** When the user says "don't threaten escalation" or similar, FIRST clarify how much of the legal framing they want:

| "let's not threaten" or "let's not escalate" | Omit escalation references (Ombudsman, IRDAI, Consumer Court). Regulations OK as context. → **Variant C** |
| "let's not talk about regulations" or "don't cite regulations" | Omit ALL regulatory citations AND escalation threats. → **Variant D** |
| "cooperative but firm" or "regulations as context not threats" | Regulations as factual context, no escalation threats. Ask for specific deliverables. → **Variant E** |

**Variant D — Pure Cooperative (no regulations, no threats):** (see below)

**Variant C — No threats, regulations as context:**
- Omit: IRDAI Ombudsman / IGMS portal, Consumer Court / Consumer Protection Act, legal counsel / legal action, deadlines/ultimatums
- Keep: Regulations cited as factual statements ("Regulation 10(5) requires settlement within 30 days of receiving survey report")
- Keep: Timeline stated neutrally ("Survey report was filed on X, it has been Y days since")
- Request a call to understand the status
- Close politely ("We look forward to your response at the earliest")

**Variant D — Pure Cooperative (no regulations, no threats):**
- Omit: ALL regulatory citations (IRDAI, Consumer Protection Act, any regulation numbers)
- Omit: ALL escalation threats (Ombudsman, IRDAI, Consumer Court, legal action, deadlines)
- Instead: Factual statement of the situation. Express surprise at the delay.
- Key framing: "How is this MY responsibility as the customer?" or "How am I responsible for your surveyor submitting his report?"
- **"Put it on record" challenge** — If the insurer claims the delay is the customer's fault (e.g., surveyor didn't submit report), flip it: "If you believe it is my responsibility as the customer to ensure your agent submits his report, please put that on record in writing. I am glad you are confirming this is a failure of your internal team, and nothing to do with me."
- Offer to mediate the mismatch: "If there is confusion between what [surveyor] says and what you say, let's get on a call together to sort it out and get to the truth"
- Request: "Please ensure payment is cleared and the car is released at the earliest"
- Close cooperatively

### Drafting as Reply in Existing Thread (Jun 2026)

When the user wants the email to be part of the existing conversation (not a new thread):

1. Find the existing thread ID from Gmail (search by keywords / participant emails)
2. Get the latest message's `Message-ID` for `In-Reply-To` header
3. Collect all `Message-ID` values (the original + replies) for `References` header
4. Include `threadId` in the draft body:
```python
draft = gmail.users().drafts().create(
    userId='me',
    body={'message': {'raw': raw, 'threadId': '19eb4d5cbea7dfd5'}}
).execute()
```
5. Use the same CC list as the previous emails in the thread (add new ones if needed)
6. Tell the user: "Saved as a reply in the existing thread — open Gmail → Drafts to review"

### Parallel Communication — WhatsApp / Separate Email to Surveyor (Jun 2026)

When there is a discrepancy between what the surveyor claims (report submitted) and what the insurer says (report not received), the user may want:

**1. A separate stern email to the surveyor** (NOT in the insurer thread):
- To: surveyor's email
- Subject: "Demand for Email Proof & Clarification — Claim [No.]"
- Tone: Stern, demanding facts
- Demand: Email proof of submission (forwarded email with timestamps and acknowledgements)
- Demand: Why report not submitted alongside workshop invoice
- Call out: The discrepancy between what he claims and what the insurer says
- CC: Internal team (rnr, Bharat, Eshwari) + the insurance manager for transparency

**2. A WhatsApp message to the surveyor** (via api.whatsapp.com link):
- Tone: Stern but direct (same content as the email, condensed)
- Content: Demand email proof of submission, express surprise at delay, demand the truth
- Phone number: Extract from the surveyor's email signature
- Delivery: Generate a deep link (api.whatsapp.com format, full-width ampersand for any & characters)

**Key argument to include in both channels:**
- "You claim the report was submitted. The insurer says it wasn't. I need to know the truth."
- "I had demanded email proof earlier and you have not provided it. I need it urgently."
- "This is a basic requirement — submitting the report alongside the invoice."

### Delivery Mode — Gmail Draft

When the user says they want to review and possibly edit before sending, use the Gmail API to **save the email as a draft** (not send):

```python
import base64
from email.mime.text import MIMEText

message = MIMEText(body)
message['To'] = 'manager@insurer.com'
message['Cc'] = 'cc1@example.com, cc2@example.com'
message['Subject'] = 'Subject line'

raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
draft_body = {'message': {'raw': raw}}
draft = gmail.users().drafts().create(userId='me', body=draft_body).execute()

print(f"Draft ID: {draft['id']}")
# Tell user: Open your Gmail → Drafts folder to review and send
```

The user can then find the draft in their Gmail Drafts folder, make any edits, and send it themselves. This gives them full control.

**Preference (Nishant, Jun 2026):** For legal/insurance emails with regulatory citations, save as Gmail draft rather than sending directly. The user will review the exact text, may add their own signature styling, confirm addresses, and send manually.

### Drafting as Reply in Existing Thread (Jun 2026)

When the user wants the email to be part of the existing conversation (not a new thread):

1. Find the existing thread ID from Gmail (search by keywords / participant emails)
2. Get the latest message's `Message-ID` for `In-Reply-To` header
3. Collect all `Message-ID` values (the original + replies) for `References` header
4. Include `threadId` in the draft body:
```python
draft = gmail.users().drafts().create(
    userId='me',
    body={'message': {'raw': raw, 'threadId': '19eb4d5cbea7dfd5'}}
).execute()
```
5. Use the same CC list as the previous emails in the thread (add new ones if needed)
6. Tell the user: "Saved as a reply in the existing thread — open Gmail → Drafts to review"

### Parallel Communication — WhatsApp / Separate Email to Surveyor (Jun 2026)

When there is a discrepancy between what the surveyor claims (report submitted) and what the insurer says (report not received), the user may want:

**1. A separate stern email to the surveyor** (NOT in the insurer thread):
- To: surveyor's email
- Subject: "Demand for Email Proof & Clarification — Claim [No.]"
- Tone: Stern, demanding facts
- Demand: Email proof of submission (forwarded email with timestamps and acknowledgements)
- Demand: Why report not submitted alongside workshop invoice
- Call out: The discrepancy between what he claims and what the insurer says
- CC: Internal team (rnr, Bharat, Eshwari) + the insurance manager for transparency

**2. A WhatsApp message to the surveyor** (via api.whatsapp.com link):
- Tone: Stern but direct (same content as the email, condensed)
- Content: Demand email proof of submission, express surprise at delay, demand the truth
- Phone number: Extract from the surveyor's email signature
- Delivery: Generate a deep link (api.whatsapp.com format, full-width ampersand for any & characters)

**Key argument to include in both channels:**
- "You claim the report was submitted. The insurer says it wasn't. I need to know the truth."
- "I had demanded email proof earlier and you have not provided it. I need it urgently."
- "This is a basic requirement — submitting the report alongside the invoice."

### Structure

```
To: [Insurance Manager email] (direct — from surveyor's reply)
CC: Surveyor, all previous CCs, Bharat (for internal tracking)

Subject: Re: [Original Subject] (same thread)

Dear Mr. [Manager],

1. Acknowledge surveyor's confirmation (report submitted on [date])
2. Express confusion/frustration about the gap between report submission and today
3. Reference regulatory timelines (IRDAI: payment within 30 days of report) — OMIT for Variant D
4. Explain personal impact (car out of service X days, part from overseas, etc.)
5. Request: at least communicate the status — if there's an issue, tell us
6. Close cooperatively (looking forward to hearing from you)
```

### Variant E — Cooperative but Firm (Regulatory Context + Specific Deliverables)

**Trigger:** User says something like "send a cooperative but firm email" or "I want regulations cited but not as threats" — they want IRDAI regulations mentioned as factual context, want to emphasize "no fault of ours," and want specific deliverables requested (not demanded).

**When to use:** The user wants regulations referenced (unlike Variant D) but does NOT want escalation threats or ultimatum language (unlike Variants A/B). This is the middle ground between C (no threats, regulations as context) and D (pure cooperative).

**Tone:** Factual, respectful, frustrated but not confrontational. Acknowledge the insurer's position ("we understand documents were misplaced") while firmly stating the customer has done everything required.

| Escalation threats in body? | Regulations cited? | Ultimatums? | Specific asks for deliverables? |
|---|---|---|---|
| **No** — omit all escalation references | **Yes** — cited as factual context (not threats) | **No** — no 24-48hr deadlines | **Yes** — acknowledgement, payment date, release date |

**Key differences from Variant C:**
- Variant C = push them to act (no threats, but still pressuring)
- Variant E = request clear next steps (cooperative framing, specific asks)
- Variant E explicitly asks for **three deliverables**: (1) acknowledgement of receipt, (2) expected payment date, (3) expected vehicle release date

**Structure:**

```
Subject: Re: [Thread Subject] — [Status Update] — Awaiting Acknowledgment & Timeline

Following up on the below thread.

As requested, [documents have been resubmitted / action taken].

Two specific requests:

1. Kindly acknowledge receipt. We cannot afford another [misplaced/critical issue] — that is at [insurer's] end, not ours.
2. Please provide a clear timeline for [payment/next step] and [final deliverable].

The vehicle has now been out of service for [X] days — for a straightforward [incident] that was completed on [date]. The delay since then has been entirely on [insurer's] side.

Under the IRDAI (Protection of Policyholders' Interests) Regulations, 2017, a claim ought to be settled within 30 days of receiving the survey report. We are well past that timeline with no communication.

We have been consistent policyholders and have done everything required from our end.

Please confirm:
1. Receipt of [documents/submission] ✓
2. Expected [payment/approval] date
3. Expected [final deliverable] date

Regards,
[Name]
Policyholder
```

**Real example (Jun 2026, NIC Jaguar claim — after documents were misplaced):**

Documents were resubmitted after Venkatesh confirmed the originals were lost at NIC's end. Azeem had not responded for 2 days. The email:
- Acknowledged the resubmission
- Requested acknowledgement (to avoid another "misplaced" incident)
- Cited IRDAI Regulation 10(5) as context (30-day settlement window)
- Asked for three deliverables: receipt confirmation, payment date, vehicle release date
- Emphasized "no fault of ours" — the delay was entirely on NIC's side
- Tone: cooperative but firm. No threats, no ultimatums, but clear expectations

### Key Phrases for Stage 2

- "I am writing to you on the advice of [Surveyor], who has confirmed..."
- "It is now [X] days since the report was filed, and we have heard nothing"
- "I am struggling to understand why a straightforward [incident type] claim is seeing this kind of delay"
- "If there is any issue, I would genuinely appreciate it being communicated to us"
- "Our vehicle has been out of service for over a month — between [part arrival], [servicing], [survey report], and now the delay at your end"
- "I would request you to kindly look into this and at least let us know the status"
- **Variant E specific:**
  - "Kindly acknowledge receipt of the resubmitted documents. We cannot afford another instance of documents being misplaced — that is an issue at [insurer's] end, not ours."
  - "The vehicle has now been out of service since [date] — over [X] days — for a straightforward [incident] that was completed on [date]. The delay since then has been entirely on [insurer's] side."
  - "Please confirm: (1) Receipt of documents ✓, (2) Expected payment date, (3) Expected date for vehicle release"

### Real example (Jun 2026, NIC Jaguar claim)

The first legal email (Stage 1) cited IRDAI regulations and demanded resolution. Venkatesh replied confirming report submitted 25/05/2026 with manager email azeem.ph@nic.co.in. The Stage 2 follow-up was directed at Azeem with tone: "frustrated but cooperative, not confrontational" — acknowledging the surveyor's response while expressing confusion about the 15-day payment gap and asking for communication rather than issuing new ultimatums.

The user may say "for whatever his compulsions, go a little soft on Mr. Venkatesh" while still wanting strong language against the insurance company. Draft strategy:
- **Toward the insurer:** Full regulatory citations, ultimatums, demands for compensation
- **Toward the surveyor:** Mention the unresponsiveness and 24hr disappearing messages factually, but add "for whatever his personal compulsions may be" to soften. Offer to work with an alternative coordinator instead.
