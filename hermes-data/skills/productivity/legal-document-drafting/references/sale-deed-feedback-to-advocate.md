# Sale Deed Feedback — Advocate WhatsApp Response

**Trigger:** Client (Nishant) provides detailed clause-by-clause feedback on a sale deed review that you had previously prepared. They want the feedback consolidated and sent to the advocate (e.g., Piyush) as a structured WhatsApp message.

## Workflow

### 1. Acknowledge & Confirm Feedback
- Restate each clause/issue back to the client in a structured summary
- Confirm your understanding is correct before drafting to the advocate
- Note: the client may correct names — lawyer's name may come through as "Piyush" not "Shranta" (voice transcription trap)

### 2. Consolidate Feedback by Clause
Group feedback into structured sections. Each clause should cover:

```
## Clause X.Y — [Issue Name]

**Original Issue:** [What the earlier review flagged]

**Client's Fix:** [Client's suggested approach in their own words]

**Suggested Clause Language:**
> [Draft the proposed amended clause text based on the client's direction]

**Notes:**
- [Any guardrails, RERA references, or edge cases to flag]
```

### 3. Common Clause Patterns (June 2026, Bangalore Project)

| Clause | Pattern |
|--------|---------|
| **5.3 — Promoter Discharge** | Say defect liability is as per RERA. Promoter discharged after: sale deed registered, association formed, common docs handed over, corpus maintenance fund handed over with up-to-date accounts, NOC obtained. Beyond RERA obligations, no further liability. Avoid explicit "5 years" — keep it referenced to RERA. |
| **11 — Defect Liability** | As per RERA. Lifts/generators/equipment covered by manufacturer warranties. Basement seepage/CPH: add technical language about water diversion, continuous dewatering, and management as normal maintenance. Normal wear & tear, minor cracks, shade differences excluded. Delivery defects covered by snag list under RERA. |
| **Carpet/Built-up Areas** | Three values: (1) RERA Carpet Area (from OC/sanctioned plan), (2) Usable Carpet Area (includes exclusive lobby + balconies), (3) Super Built-up Area. No strict definitions for usable/SBA — pragmatic listing. |
| **OC Deviations** | Don't declare deviations. State: OC received with [OC number, date, issuing authority]. As-built drawings per OC with minor permissible deviations under law. Super built-up area unchanged. Minor common area changes (store room etc.) part of as-built. Hand over as-built drawings to association. |
| **Deed of Declaration** | Register under Karnataka Apartment Ownership Act. Placeholder for registration no. and sub-registrar. Each purchaser to sign deed of adherence and become association member. |
| **Undivided Share** | Total site area ÷ total SBUA. Get from sanctioned plan. Leave blank with note to fill. |
| **Terrace** | X sqft exclusive right of use to 13th floor. Others have no objection. |
| **RERA Mandatory Clauses** | Not needed — project closed, OC received. No need for: 70% carpet area price, separate account, escalation-free pricing, dispute resolution under RERA, conveyance timeline. |
| **Fire Clearance** | M Fire OC + Fire CC received. Find docs in Drive. Reference in document. |
| **Car Parks** | 2 car parks. Section specifying car park numbers. Annexures: floor plan + car park plan. Car park allotted for exclusive use. |
| **Structural Stability** | Mention report received from [consultant] dated [date]. Find in Drive. |

### 4. Determine Delivery Format

If the consolidated feedback is **short enough** (under ~1500 chars message text after encoding → total URL under ~4000 chars):
- Generate a single `api.whatsapp.com/send?phone=...&text=...` link
- Add bold caption: `*[Project Name] — Sale Deed Feedback*\n\n`
- Present as clickable link in Telegram

If the feedback is **long** (500+ words, 4+ substantive paragraphs, multi-section legal content):
- Generate an **HTML Card** instead of a plain deep link
- Write to `/data/hermes/cron/output/whatsapp-{contact}-{project}-{topic}.html`
- The HTML file contains the wa.deep link inside an `<a href>` tag so Telegram never sees the raw URL (which would get split)
- Deliver via `MEDIA:/data/hermes/cron/output/whatsapp-...html`

### 5. WhatsApp Message Structure

```
Bold caption
*[Project Name] — Sale Deed Feedback to [Advocate Name]*

Dear [Advocate Name],

Please find below the client's feedback on the sale deed review, clause by clause:

1. **Clause 5.3 — Promoter Discharge:**
   [Suggested approach]

2. **Clause 11 — Defect Liability:**
   [Suggested approach]

...

Please incorporate these changes and share the revised draft for review.

Regards,
Nishant Ranka
```

### 6. Ampersand Encoding

Apply the standard ampersand fix from `messaging-drafts/SKILL.md`:
```python
msg = message.replace("&", "\uFF06")  # ＆ (U+FF06) before URL-encoding
```

### Pitfalls
- **Voice transcription traps:** The advocate's name may be misheard (e.g., "Shranta" → "Piyush"). Ask the client to confirm or repeat the name if unsure.
- **Missing contact:** The advocate's phone number may not be in memory/sessions. The client may expect you to already have it. Ask explicitly if not found.
- **Length check:** Always assess message length before deciding delivery format. Long legal feedback almost always needs the HTML card path.
- **Drive references:** When the client says "find the fire CC in Drive" or "find structural stability report in Drive", search and verify before mentioning document dates/references in the feedback.
