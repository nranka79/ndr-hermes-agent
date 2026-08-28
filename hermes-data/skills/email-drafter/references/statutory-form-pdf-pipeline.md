# Statutory Form PDF Pipeline (MGT-11 proxy, consent forms, etc.)

Trigger: user asks to "fill the proxy form", "fill MGT-11", "prepare a form for signature",
or send any statutory/corporate form (Companies Act forms, consent letters) as a signed PDF.

Validated 2026-08-13: DRA Aadithya South City AGM — filled MGT-11 proxy for Roshni Ranka
appointing NDR, sent as draft to rnr@draas.com with the AGM notice forwarded.

## The shape of the task

The company sends a Word/PDF template (e.g. `Form MGT-11.doc`) + a big notice pack PDF.
You must fill the form with member/shareholder data, produce a clean PDF for signature,
and create a DRAFT email (never send) forwarding the original notice to the signer with
the filled form attached.

## Step 1 — Download attachments from Gmail

Use the raw Gmail API (terminal + `/opt/hermes/.venv/bin/python3`, NOT execute_code —
sandbox lacks `gws_fetch_token`). Walk the payload recursively for `attachmentId`:

```python
service = build_service('gmail', 'v1', service_name='google-gmail')  # account where the notice lives
res = service.users().messages().list(userId='me', q='subject:"AGM" subject:"Aadithya"', maxResults=10).execute()
for m in res.get('messages', []):
    detail = service.users().messages().get(userId='me', id=m['id'], format='full').execute()
    # walk detail['payload']['parts'] recursively; for each part with
    # part['body']['attachmentId']:
    att = service.users().messages().attachments().get(
        userId='me', messageId=m['id'], id=part['body']['attachmentId']).execute()
    data = base64.urlsafe_b64decode(att['data'])
```

## Step 2 — Read the legacy .doc template WITHOUT LibreOffice

Templates often arrive as legacy Word `.doc` (magic bytes `D0 CF 11 E0` = OLE compound, not
docx zip). On the Hermes VPS there is no libreoffice/antiword/catdoc and no sudo/pip. Two
working approaches:

1. **`strings` extraction (fast, usually sufficient for forms):**
   ```bash
   strings -n 6 "Form MGT-11.doc"
   ```
   The MGT-11 text (CIN, company name, registered office, all field labels, statutory note)
   came out cleanly this way — the form body is stored as readable UTF-16/ANSI runs.

2. **Dedicated env via uv (when you need real parsing):** pip is absent and the system is
   PEP 668, so create an isolated env:
   ```bash
   uv venv docenv --python 3.13
   uv pip install --python /tmp/docenv/bin/python pymupdf reportlab   # + python-docx olefile if parsing
   ```
   (`python-docx` only handles .docx; legacy .doc needs olefile or just `strings`.)

## Step 3 — Extract member/shareholder data from the notice PDF

The AGM notice pack (pymupdf) usually contains the shareholding table in the Notes to
Financial Statements ("Details of Shares held by shareholders holding more than 5%"):

```python
import pymupdf
doc = pymupdf.open('notice.pdf')
for i in range(len(doc)):
    t = doc[i].get_text()
    if 'Roshni' in t or 'shareholding' in t.lower(): print(i, t[:2500])
```

Real example: *Mrs. Roshini Ranka — 34,144 shares, 16.49%* (of 207,109 issued, Rs. 10 each).
Pull: CIN, company name, registered office, AGM date/time/venue, member's share count,
proxy's name/email. Do NOT invent the member's folio/address — leave blank and flag to the
user instead of guessing.

## Step 4 — Rebuild the filled form as a PDF (reportlab)

Do NOT try to edit the original .doc — rebuild the form with reportlab platypus so the
output is clean and typed:

- `BaseDocTemplate(A4)` + one `Frame` + `PageTemplate` (or SimpleDocTemplate).
- Header: `FORM NO. MGT-11` / `Proxy Form` / the Companies Act citation line, centered.
- Company block as a `Table` (CIN | Company name / Registered office), boxed with
  `TableStyle([('BOX',...), ('INNERGRID',...)])`.
- Member fields as a field table: Name / Registered address / E-mail / Folio No. / No. of
  shares — filled values bold (`ParagraphStyle fontName='Helvetica-Bold'`), blanks as
  underscored lines (`'___________'`).
- The statutory "I/We, being the member(s)..." paragraph verbatim, with bolded meeting
  date/time/venue.
- Signature row: three boxes side-by-side — "Affix Revenue Stamp" / "Signature of
  shareholder" / "Signature of Proxy holder(s)" — with `TOPPADDING/BOTTOMPADDING` ~30 for
  signing space.
- End with the note (e.g. "deposited at the Registered Office not less than 48 hours
  before the Meeting").

## Step 5 — Verify the PDF before emailing

```python
import pymupdf
doc = pymupdf.open('filled.pdf')
print(doc[0].get_text())          # confirm all fields render
pix = doc[0].get_pixmap(dpi=100); pix.save('/tmp/preview.png')   # optional visual check
```

## Step 6 — Draft email with attachments (raw Gmail API)

`gws_skill_bridge.draft_create`/`draft_reply_create` do NOT support attachments — use the
raw API, exactly as `templates/draft-with-attachments.py` in this skill:

- `MIMEMultipart('mixed')`, `MIMEText(body_html, 'html')` + one `MIMEBase('application','pdf')`
  per attachment with `encoders.encode_base64` + `Content-Disposition: attachment`.
- To = signer ONLY (user said "to her only" — no CC).
- **From the WORK account (ndr@draas.com)** for DRA-group corporate matters even when the
  notice arrived in personal Gmail — work artefacts live in the work account
  (user correction 2026-07-13).
- Body: short personal note (sign + return by the deadline) then a
  `---------- Forwarded message ---------` block of the original notice (or forward the
  original email's pack as a second attachment).
- Create via `service.users().drafts().create(userId='me', body={'message': {'raw': ...}})`.

## Step 7 — Verify the draft

```python
d = service.users().drafts().get(userId='me', id=DRAFT_ID).execute()
msg = d['message']
print(msg.get('labelIds'))            # MUST be ['DRAFT']
h = {x['name']: x['value'] for x in msg['payload']['headers']}
print(h.get('To'), h.get('From'), h.get('Subject'))
# walk payload parts to list attachment filenames
```

Confirm: To contains ONLY the intended signer, From is the work account, DRAFT label,
all attachments present. Then tell the user it's a draft — they send it themselves.

## Pitfalls

- **Never send** — drafts only, even when the user says "send to her".
- **Shareholding data comes from the notice PDF, not memory** — the member's share count
  must be read from the actual document; do not guess folio/address.
- **Legacy .doc ≠ .docx** — check magic bytes first; `strings` beats installing converters.
- **Execute_code sandbox cannot build Gmail services** — always terminal with the Hermes
  venv for both reading and drafting.
