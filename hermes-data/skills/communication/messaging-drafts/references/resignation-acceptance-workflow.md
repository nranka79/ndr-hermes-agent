# Resignation Acceptance Email Workflow

## Overview

When an employee sends a resignation email, the reply must be:
- **Legally solid**: references appointment letter, HR policy, employment agreement
- **Professionally courteous**: gratitude, well wishes, punctuality reminder
- **Operationally complete**: deliverables list, handover, settlement terms, last working day
- **Saved as draft** — never auto-sent

## Step-by-step

### 1. Find the resignation email
```
Gmail search: from:{employee_email} subject:resignation
```
Fetch full thread to get `threadId` and original message date.

### 2. Locate employment documents on Google Drive
Search Drive for:
- `"Offer Letter - {Employee Name}"` — the appointment/offer letter
- `"Employment Agreement - {Employee Name}"` — the employment contract
- `"HR Policy Document"` — company HR policy (shared folder)

Download locally before attempting text extraction.

### 3. Extract key legal terms

**From HR Policy (text-based PDF):**
- Notice period: confirmed employees = 30 days, probation = 15 days
- Salary-in-lieu-of-notice option
- Leave deduction policy

**From Employment Agreement / Appointment Letter (often scanned PDFs):**
- `pdftotext` often returns empty on scanned PDFs → use `fitz` (PyMuPDF) or tesseract OCR
- Key clauses: notice period, leave encashment, bond/lock-in, settlement terms, penal deductions

### 4. Cross-check the resignation against contract

| Check | Question |
|-------|----------|
| Notice period | Did they serve full contractual notice (e.g., 30 days)? |
| Shortfall | If < 30 days, do you enforce or waive? |
| Employment status | Probation or confirmed? (Determines applicable notice period) |
| Last working day | Did they state one? Confirm it's feasible. |
| Deliverables | What did they work on? List pending project deliverables. |
| Leave balance | Any unused EL/PL to encash or adjust? |
| Settlement | Salary through last day, deductions per appointment letter clause |

Present this as a structured table to the user before drafting.

### 5. Draft email structure

```
Subject: Re: Resignation — [Employee Name], [Role], TruBld

Dear [Name],

Thank you for your email dated [date]. We accept your resignation and confirm
your last working day as [date].

[Notice period note — waive or enforce]

Settlement: Salary will be processed through [last working day], subject to
[due contracted deductions for unused leaves / other deductions per your
appointment letter].

Before your exit, we request the following pending deliverables to be
transferred/discussed with [supervisor name]:
1. [Deliverable 1 — Ranka Amber project]
2. [Deliverable 2]
...

We request your full presence and punctuality through [last working day].

[Gratitude + well wishes]

Sincerely,
[Nishant Ranka / Employer Name]
```

### 6. Save as Gmail draft — NEVER auto-send

Use MIME-based draft creation (no `threadId` in API body). Direct user to:
`https://mail.google.com/mail/u/0/#drafts`

## Key Legal Terms (TruBld / Finding Form Design Studio reference)

- Confirmed employees: **30 days notice** (HR Policy §1.3)
- Probation employees: **15 days notice**
- Employer may pay salary in lieu or require full notice to be served
- Settlement: salary through last working day, subject to deductions per appointment letter
- Deductions: contracted leaves and others per appointment letter clause (specifics vary by employee)

## Amrutha Bimal Kumar — TruBld Case Data (2026-05-05)

- Role: Architect, Finding Form Design Studio / TruBld
- Joined: 26/05/2025 (confirmed employee, not probation)
- Resignation email: amrutha.bk@gmail.com, subject "Resignation", received 2026-05-05 18:19
- Offered last working day: 31/05/2026 (26 days notice — shortfall of 4 days vs 30 required)
- Deliverables pending: Ranka Amber — joints for plan sanctions, GFC set for execution team; engineering deliverables: deal methodology statement, material recommendation, trading elevation details
- Supervisor: Bhuvanesh (email not confirmed; not expected to reply)
- Decision: waive 4-day notice shortfall (employer's right per HR Policy)
