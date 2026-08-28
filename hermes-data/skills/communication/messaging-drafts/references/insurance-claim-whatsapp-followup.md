# Insurance Claim — WhatsApp Follow-Up After Escalation Email

**Trigger:** User has sent a legal escalation email to the insurance company. The surveyor then calls claiming the report was submitted. User wants a **strong WhatsApp message** to hold the surveyor accountable, with specific references to call times and broken promises.

## Workflow (5 phases)

### Phase 1: Understand the email thread
- Search Gmail for the claim: use policy number, vehicle registration, or "surveyor" + "insurance"
- Extract the surveyor's name, email, mobile, and the insurance manager's email/contact
- Note the timeline: when was the report allegedly submitted, claim intimation date, days elapsed
- Key regulations: IRDAI mandates surveyor report within 30 days, insurer settlement within 30 days of report

### Phase 2: Identify the surveyor from the email
Surveyors often reply from personal Gmail addresses (e.g. venkateshg.surveyor@gmail.com). The email signature usually includes name, designation as "Surveyor", and mobile number. Extract all of this.

### Phase 3: Analyze the WhatsApp call log screenshot
When the user shares a call log screenshot:
- Use OCR (`tesseract` via terminal, or `pytesseract`) to extract message timestamps and call details
- Look for:
  - When the user first messaged (evening/night before)
  - When the surveyor replied (next morning)
  - When the user asked for proof
  - Whether there's an unanswered voice call attempt
- Cross-reference the WhatsApp chat with what the surveyor promised on the phone call

### Phase 4: Draft the WhatsApp message

**Tone:** Strong but factual. No threats — just a clear timeline of broken promises and a demand for proof.

**Structure:**
```
*HEADLINE — SHORT, PUNCHY*

You called me this morning. You told me you would share:
1. [Promise 1 — e.g. proof of report submission]
2. [Promise 2 — e.g. manager's number]

I asked for proof at [time]. You replied [their inadequate response] — but sent nothing.

I tried calling you at [time] — no answer on WhatsApp, no answer on regular call.

I need right now:
1. The report you submitted — or proof of submission with timestamp
2. The manager's contact number

If you cannot provide these, tell me immediately so I can escalate. Do not leave me chasing you.
```

**Key rules for this specific message type:**
- Reference exact times from the screenshot (shows you have evidence)
- Mention IRDAI timelines (8-10 working days for surveyors) vs actual days elapsed (44+, etc.)
- No sender signature ("Nishant here") — the recipient already knows who is messaging
- WhatsApp markdown: `*bold*` for emphasis, `~strikethrough~` if needed, plain text for body

### Phase 5: Delivery

Since the user is adding their own screenshot image, deliver as a **markdown code block** for copy-paste (see Copy-Paste Mode in SKILL.md). Do NOT generate a deep link — the user will paste the text into their existing WhatsApp chat with the image attached.

## Example from session (Jun 2026)

- **Vehicle:** Jaguar KA-04-MR-1001
- **Policy:** 602200312510001783
- **Insurer:** National Insurance Company Ltd
- **Surveyor:** G. Venkatesh (venkateshg.surveyor@gmail.com, +91 9611501955)
- **Insurance Manager:** Azeem Ph (azeem.ph@nic.co.in)
- **Timeline:** Report allegedly submitted 25/05/2026, claim pending 44+ days
- **WhatsApp chat:** User messaged at 21:46, surveyor replied at 06:49 saying "report submitted", user asked for proof at 06:50, surveyor said "Last Monday" but provided nothing
- **Call attempt:** User called at ~12:30 — no answer on WhatsApp call or regular call
