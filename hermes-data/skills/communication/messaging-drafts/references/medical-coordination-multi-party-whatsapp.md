# Multi-Party Medical Coordination — WhatsApp Pattern

**Trigger:** User coordinates pre-surgery medical tests, specialist consults, and appointments for a family member. Needs separate WhatsApp messages to different stakeholders.

## The Pattern

When the user shares medical documents (echos, ECGs, audiology, lab reports, pre-op evaluations) and needs care coordination, send **separate, role-tailored WhatsApp messages** to each stakeholder:

| Stakeholder | Message Content | Tone |
|---|---|---|
| **Treating specialist** (cardiologist, anesthesiologist) | Full clinical summary with key findings (echo, lab, ECG values). State the surgical context, the specific question they need to answer, and your request for an appointment. | Respectful, concise, data-driven. Lead with findings, end with the ask. |
| **Operation coordinator** (hospital contact / surgeon's team) | Status update. State which reports are ready, what's still pending (cardiology clearance), and when you'll share the full set. Keep them in the loop so they don't chase. | Professional, timeline-aware. Don't send attachments piecemeal — batch when clearance is obtained. |
| **Internal team member** (for appointment booking) | Clear instruction: who to book (doctor name, specialty, hospital), for whom (patient name), by when (timing coordination with patient). | Direct, actionable. Include all details they need in one message. |
| **Accounts/admin** (for salary/finance documents) | Specific document request (salary slips, letterhead, stamp), the purpose (insurance), and a deadline (end of day). | Urgency signaled upfront. State the exact documents, format (stamped/sealed), and timeline. |

## Key Rules

1. **One message per person** — Do NOT combine messages or CC-style send to multiple people. Each stakeholder gets their own tailored message.
2. **Deep reasoning model for medical analysis** — Use Claude Opus 4.8, DeepSeek R1, or GPT-5.5 Pro via OpenRouter for analyzing medical reports. Never use vision-tier or Flash models for clinical interpretation.
3. **File naming convention for medical docs** — `YYYYMMDD_Patient_Content_Hospital.pdf` (e.g. `20260709_KDR_2DEcho_Report_Trustwell.pdf`). File in patient-specific Drive folders (NDR Medical / KDR Medical) with an `Invoices/` subfolder for bills.
4. **Coordinate before sharing** — Don't send partial report sets. If clearance is pending (e.g., cardiology review), tell the coordinator it's pending and share everything once complete.
5. **Reference the doctor's full name + hospital** in every message so there's no ambiguity. Voice transcriptions often garble names ("Diweli" → "Dwivedi").

## Stakeholder-Specific Details

### To a treating specialist (first contact)
- **Subject line first:** "Good morning Dr. [Name]. This is [Sender Name]."
- **Patient context:** Age, scheduled procedure, date, primary surgeon, hospital
- **Findings summary:** ECG (normal/abnormal), Echo (key values), CXR, blood work
- **The consultation ask:** 2-3 specific questions you need answered
- **Appointment request:** "Could we come by at your convenience today?"
- **Sender's phone number:** Include for easy follow-up

### To an operation/hospital coordinator (status update)
- **Acknowledge their prior request** — referencing what they asked for
- **State what's ready** — list all reports prepared
- **State what's pending** — what clearance you're waiting for and why
- **Commit to next action** — "Once cleared, I'll share the full set"
- **Keep it brief** — they manage many cases, one paragraph is enough

### To internal team for appointment booking
- **Doctor name + specialty + hospital** clearly stated
- **Patient name** clearly stated
- **Action:** "Coordinate with the clinic for available timing, then coordinate with [patient] to confirm"
- **Reference any parallel actions** — "I'm sending a clinical summary to the doctor separately"

### To accounts/admin for financial documents
- **Purpose upfront** — "for life insurance"
- **Exact documents needed:** type (salary slips), period (last year, last 3 months), format (stamped & sealed on letterhead)
- **Specific salary figure** if they need to show a modified amount
- **Hard deadline** — "by end of day today"
