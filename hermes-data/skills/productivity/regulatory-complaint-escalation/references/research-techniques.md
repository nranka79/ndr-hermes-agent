# Research techniques for regulatory complaint escalations

Concrete, working patterns captured from the Bajaj Life Insurance dispute (11 Jul 2026). Update this file as new patterns emerge in other disputes.

## 1. Finding the counterparty's GRO / Internal Ombudsman / Nodal Officer

The Insurance Regulatory and Development Authority of India (IRDAI) requires every insurer to disclose its Grievance Redressal Officer (GRO) name, email, postal address under the IRDAI (Protection of Policyholders' Interests, Operations and Allied Matters of Insurers) Regulations, 2024. The disclosure is in the insurer's own published Grievance Redressal Policy PDF.

### Working URL patterns (Bajaj Life — example)

| What | URL |
|------|-----|
| Grievance Redressal Policy | `https://www.bajajlifeinsurance.com/content/dam/balic-web/pdf/customer-services/grievance-redressal-policy.pdf` |
| Citizen Charter | `https://www.bajajlifeinsurance.com/content/dam/balic-web/pdf/citizen-charter.pdf` |
| Service TAT | `https://www.bajajlifeinsurance.com/content/dam/balic-web/pdf/customer-services/services-tat.pdf` |
| Sitemap discovery | `https://www.bajajlifeinsurance.com/sitemap.xml` |
| About Us / Leadership | `https://www.bajajlifeinsurance.com/about-us.html` |

### How to find the same on any insurer

1. Fetch `https://www.<insurer-domain>/sitemap.xml` and grep for `pdf`, `grievance`, `disclosure`, `charter`, `tat`, `ombuds`.
2. If sitemap is empty, try common paths: `/grievance-redressal.html`, `/grievance.html`, `/contact-us.html`, `/customer-services.html`, `/disclosures.html`, `/policies.html`.
3. Watch for 301 redirects — Bajaj's old `bajajlife.com` redirects to `bajajlifeinsurance.com` but the PDFs live on the new domain. Follow the redirect.
4. Once you have the Grievance Redressal Policy PDF, download it and `pdftotext -layout` it. Grep for `Grievance Redressal Officer` — name + email + address always appears in the same place (the "Escalation Matrix" section).
5. Confirm via the About Us page — search for `Leadership`, `Board`, `CEO` and look for `<Name>Managing Director and Chief Executive Officer`.

### Generic GRO email patterns (try in order)

- `gro@<domain>` (e.g. `gro@bajajlife.com`)
- `grievance@<domain>`
- `grievances@<domain>`
- `nodal@<domain>` (banks use this)
- `principal.nodal.officer@<domain>` (banks)
- `complaints@<domain>`
- `customercare@<domain>` (escalation only — TAT is much longer)

## 2. Gmail tools — patterns that work

### Resolve the account
```python
from tools.gws_auth import build_service
account_info = gws_resolve_account("ndr@draas.com")  # -> {"email": ..., "service_name": "google-draas", "has_token": true}
service = build_service('gmail', 'v1', service_name=account_info['service_name'])
```

**Hard rule**: NEVER pass an email address as `service_name`. Always resolve via `gws_resolve_account` first. Email-as-service-name looks identical to "not authorized" but is a different error.

### Iterate on multi-thread disputes
1. First pass: `format='metadata'` for all messages matching a query — get thread IDs, dates, subjects. Cheap.
2. Second pass: `format='full'` for the relevant threads only — get bodies.
3. Third pass: `format='raw'` for messages where the body came back empty (this means it was `multipart/related` with inline images). The raw format gives you the full base64-decoded MIME.

### The empty-body trick
If `format='full'` returns an empty body, switch to `format='raw'`:
```python
msg = service.users().messages().get(userId='me', id=mid, format='raw').execute()
import base64
raw = base64.urlsafe_b64decode(msg['raw']).decode('utf-8', errors='ignore')
```
The body is in there as quoted-printable or as a `text/plain` part inside a `multipart/related` block. Look for `Content-Type: text/plain` followed by `Content-Transfer-Encoding: quoted-printable` and decode any `=E2=80=93` sequences (they're UTF-8 en/em dashes).

### Create a draft (NEVER send)
```python
from tools.gws_skill_bridge import call
result = call(
    "draft_create",
    service_name="google-draas",
    to="primary@x.com; secondary@x.com",
    cc="cc1@x.com; cc2@x.com",
    bcc="gro@x.com; user_self_bcc@x.com",
    subject="Re: [Original Subject] — Formal Complaint [GRO Escalation]",
    body=email_body_text
)
# Returns: {"status": "draft_created", "draft_id": "...", "message_id": "...", "threadId": "..."}
```

### Save the plan as a Google Doc
```python
result = call(
    "docs_create",
    service_name="google-draas",
    title="[Counterparty] — Plan & Violation Analysis — [Date]",
    body=markdown_content,
    folder="TMP"   # or "Work" / "Projects" / etc.
)
# Returns: {"status": "created", "documentId": "...", "url": "https://docs.google.com/document/d/.../edit"}
```

Note: the parameter is `body`, not `content`. The earlier skill bridge used `content`; current is `body`.

## 3. The IRDAI / Insurance Ombudsman infrastructure (as of Jul 2026)

### Bima Bharosa (IRDAI's online complaint portal)
- URL: `https://bimabharosa.irdai.gov.in`
- All insurers must integrate their CRM with this — every grievance is logged with a unique ID
- Policyholder can file here if not resolved within 30 days
- Helpline: `155255` / `1800-4254-732`
- Email: `complaints@irda.gov.in`
- Postal: Sy.No.115/1, Financial District, Nanakramguda, Gachibowli, Hyderabad – 500 032

### Insurance Ombudsman (17 centres)
- Master list: `https://www.cioins.co.in/Ombudsman`
- Jurisdiction: based on policyholder's residence, not insurer's location
- For Bangalore-residing policyholders: `oio.bengaluru@cioins.co.in`
- All centres follow `oio.<city>@cioins.co.in` pattern (kolkata, mumbai, chennai, delhi, hyderabad, ahmedabad, bhopal, bhubaneswar, chandigarh, guwahati, jaipur, kochi, lucknow, noida, patna, pune)
- Award limit: up to ₹30 lakh (raised to ₹50 lakh in 2024 amendments)

### Key turnaround times Bajaj's own PDF commits to
| Service | Bajaj's TAT |
|---------|-------------|
| Policy Revival decision (after all requirements) | 7 days |
| Grievance acknowledgement | Immediately |
| Action on complaint + intimation of decision | 14 days |
| Communication of Ombudsman option if unresolved | 14 days from original receipt |
| Death claim (no investigation) | 15 days |
| Death claim (with investigation) | 45 days |

## 4. Voice message → complex task workflow

This is the most efficient way to receive a complex multi-stakeholder dispute:

1. Listen to the entire voice message — don't interrupt
2. Set up a TodoList immediately (5–8 items is normal)
3. Identify the four parallel research streams:
   - Pull email chain (Gmail, may take 30–60s)
   - Wait for the WhatsApp transcript (user attaches after the voice note)
   - Find counterparty's GRO/leadership
   - Find counterparty's TAT commitments
4. Run all four in parallel
5. Build the chronology table from the email + WhatsApp data
6. Map violations to regulations
7. Write the draft email
8. Save the plan as a Google Doc
9. Present a tight summary — no padding, no "I can also do X" menus

## 5. Common phishing patterns to avoid in the counterparty's own PDFs

- **Don't take the insurer's word for TATs.** Always cross-check with the regulator's published regulations.
- **Don't accept the insurer's framing of their own grievance policy.** Read the actual PDF, not the executive summary.
- **Watch for "subject to discretion" language** in the Grievance Redressal Policy (Bajaj's PDF has: "The Company will review the decision on a complaint reopened, subject to discretion"). This is a regulatory red flag — flag it in the complaint.
