# Senior Appointment Letter Template — Business Development Head / CEO's Office

## Source Session
30 June 2026 — Prakash Singh appointment letter (DRA Realty Private Limited)

## When to Use This Template
- Converting a consultant to full-time employee (retrospective effective date)
- Senior dual-hatted role (Business Development + CEO's Office / Chief of Staff)
- Role with no monthly performance pay — incentive covered by a separate plan
- Employee who has already served 6+ months and gets probation waived

## Document Location
- **Drive ID:** `1sYoltUWdHGp2IomEy2A4wCHrRqlkt-tU9yTdaBG2Y_4` (as of 30 Jun 2026 — HTML-imported version, see Formatting section)
- **Folder:** HR (`0B1Oc8cSaJXPGMFJWaXVFenFleFk`)
- **Name:** `20260630_DRA_PrakashSingh_AppointmentLetter_BDHead`

## Formatting — HTML→Google Doc Import (Proven Pattern for Appointment Letters)

The user expects appointment letters to be **visually appealing, professionally formatted** — not text-heavy Google Docs. The proven approach:

1. **Write the full document as HTML+CSS** with:
   - Company letterhead (centered, navy `#1a3a5c`, bottom border)
   - Document title in navy uppercase
   - Section headers (`<h2>`) with navy left border + light background (`#e8edf2`)
   - CTC table with dark navy header row (`#1a3a5c`), white text, alternating rows
   - Callout boxes with left navy border and light blue background (`#f8f9fb`)
   - Signature block with flex layout
   - **DO NOT use `<ol>` or `<li>`** — use `<ul>` with `list-style-type: disc` for bullet lists, and manual numbering for numbered lists

2. **Upload the HTML to Drive as a Google Doc:**
```python
media = MediaFileUpload('/path/to/file.html', mimetype='text/html', resumable=True)
body = {
    'name': 'YYYYMMDD_DRA_EmployeeName_AppointmentLetter_Role',
    'parents': ['0B1Oc8cSaJXPGMFJWaXVFenFleFk'],  # HR folder
    'mimeType': 'application/vnd.google-apps.document'
}
doc = drive.files().create(body=body, media_body=media, fields='id,name,webViewLink').execute()
```

3. **Delete the old version** after the new doc is verified.

4. **Share** the new doc as editor to the employee's DRAAS email.

5. **Reuse the same HTML content** as the email body (see "Email Delivery Pattern" below).

This replaces the older approach of building docs via Docs API `batchUpdate` which produced plain text-heavy documents.

## Key Structural Differences from Offer Letters

| Section | Offer Letter (New Hire) | Appointment Letter (This Template) |
|---------|------------------------|-------------------------------------|
| Opening | "We are pleased to offer you the position of..." | "We are pleased to confirm your full-time employment with... effective 1 April 2026" |
| Background paragraph | "During our interactions..." (personalised from resume) | "Your contributions to the company since June 2025 have been valuable, and we are happy to formalise your role..." |
| Probation | Standard 6-month clause | "Since you have already served as a consultant with DRA Realty for more than six (6) months, your probation period is waived." |
| Compensation | Base + Attendance + Performance (standard 3-part) | Base + Attendance only (fixed CTC), plus Incentive Advance (adjustable) |
| JD section | High-level, often deferred to KPI matrix | Detailed multi-section JD required (user expects specificity) |
| Company mobile | Not typically included | Required section: "All official communication via company-issued mobile number only" |
| Email to | Candidate's personal email | Company email (psingh@draas.com) + CC HR |

## CTC Section - Senior Incentive Advance Pattern

Use a table with these exact rows:

| Component | Monthly (Rs.) | Annual (Rs.) |
|-----------|--------------|--------------|
| Base Salary | 45,000 | 5,40,000 |
| Attendance Allowance | 5,000 | 60,000 |
| Fixed Monthly CTC | 50,000 | 6,00,000 |
| Incentive Advance (adjustable against earned performance incentive) | 25,000 | 3,00,000 |
| Total Monthly Payout | 75,000 | 9,00,000 |

Always add this note below the table:

"Incentive Advance: The Rs. 25,000/month Incentive Advance is paid as an advance against the earned performance incentive under the Business Development Incentive Plan (May 2026). The detailed performance incentive framework - including KPIs, stage milestones, close incentives, and margin verification - will be documented separately and shared with you for formal agreement. The Incentive Advance will be adjusted against earned incentive payouts as and when they crystallise under that framework."

## Probation Waiver Section

"Since you have already served as a consultant with DRA Realty for more than six (6) months (since June 2025), your probation period is waived. You are confirmed as a full-time employee effective from your date of employment, 1 April 2026."

## Company Communication Section

"All official communication - including participation in company WhatsApp/Telegram groups, client calls, vendor coordination, and internal team communication - must be carried out using the company-issued mobile number that has already been provided to you. Personal mobile numbers are not to be used for any company-related communication. This is to ensure professional consistency and record-keeping."

## Email Delivery Pattern

- **To:** psingh@draas.com
- **CC:** sales1.blr@draas.com (Bharat H - HR/onboarding)
- **Subject:** Confirmation of Employment - Appointment Letter - DRA Realty Private Limited
- **Body:** HTML-formatted (reuse the same HTML from the Google Doc, adapted for email — strip the letterhead, add inline styles for email client compatibility, wrap in `<div class="container">` for width constraint, add document links)
- **Attachments:** None (appointment letter accessible via Drive share, not emailed as attachment); HR Policy shared as viewer link

### Dual-Purpose HTML Pattern (Same Source → Doc + Email)

Write ONE HTML document, then use it for TWO purposes:

1. **For the Google Doc:** Upload the complete HTML file with letterhead, full styling, signature block, and footer via Drive API as described above. This becomes the formal appointment letter.

2. **For the email body:** Extract the same content but adapt for email delivery:
   - Remove the full letterhead (use a simpler heading instead)
   - Add a CTC summary table inline
   - Add clickable document links (Appointment Letter + HR Policy)
   - Add a signature block with just the sender's name/title
   - Keep the inline CSS but use email-safe properties (no flexbox, simple tables)
   - Wrap in a `<div class="container" style="max-width:650px;margin:auto">` for constrained width
   - Wrap in MIMEMultipart('alternative') with plain text fallback

```python
# Email creation pattern
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import base64

msg = MIMEMultipart('alternative')
msg['Subject'] = 'Subject line'
msg['From'] = 'Sender Name <email@draas.com>'
msg['To'] = 'recipient@draas.com'
msg['Cc'] = 'cc@draas.com'

plain_part = MIMEText(plain_text, 'plain')
html_part = MIMEText(email_html, 'html')
msg.attach(plain_part)
msg.attach(html_part)

raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
gmail = build_service('gmail', 'v1')
draft = gmail.users().drafts().create(
    userId='me',
    body={'message': {'raw': raw}}
).execute()
```

3. Document links in the email body should link directly to the shared Google Doc (Appointment Letter as editor, HR Policy as viewer). Do NOT attach files to the email — the employee accesses via Drive.

This pattern saves time, ensures visual consistency between the doc and email, and avoids managing two separate sources of truth.

## HR Policy Sharing

Share the HR Policy document (`0BymF3UUrZZYKMnBodl9ILVRVb3c`) with viewer access to the employee's DRAAS email address. Reference the link in the appointment letter.

## Key Vocabulary from User

- "Monthly CTC is Rs. 50,000" = fixed component only
- "Rs. 25,000 is being paid as an advance towards potential future incentives to be earned and will be adjusted against any future earning of incentives"
- "He's a complete assistant to the CEO... CEO's office he works in, my office basically"
- "all jobs that normally I would be performing as a CEO that I assign to him to perform on my behalf"
- "Parachute him into critical administrative work, legal work, financial work which is stuck"
- "Co-chairing with me on those and handling all of those jobs"
- "Everything related to sometimes recruitment, sometimes site visits for physical inspections, everything is covered"
