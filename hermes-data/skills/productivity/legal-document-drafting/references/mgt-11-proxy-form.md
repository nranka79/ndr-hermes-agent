# MGT-11 Proxy Form — Fill, PDF, Draft (AGM workflow)

Verified 2026-08-13: DRA Aadithya South City AGM — filled MGT-11 proxy on behalf
of Roshni Ranka (shareholder) appointing NDR as proxy, produced a signature-ready
PDF, created a forward draft email to her only with the proxy + full AGM pack attached.

## When this applies
User says "fill proxy for the AGM", "MGT-11", "appoint me as proxy" for any
DRA-group AGM (DRA Aadithya South City / DRAASCPPL, DRA Homes, etc.).

## Workflow

1. **Find the AGM notice** — usually in NDR's PERSONAL Gmail (nishantranka@gmail.com,
   vault `google-gmail`), from the compliance officer (e.g. Balaji Natarajan, DRA
   Homes CEO office). Search `subject:"AGM" subject:"Aadithya"`. The MGT-11 form is
   attached as a **legacy .doc** (application/msword), plus a Route Map PDF and a
   large compressed AGM pack PDF (notice + directors report + FS, ~15MB).

2. **Download attachments** — Gmail API `messages().attachments().get()` with
   base64 decode; walk `payload.parts` recursively for `attachmentId`.

3. **Read the .doc template** — magic bytes `\xd0\xcf\x11\xe0` = OLE2 legacy .doc
   (python-docx/zipfile CANNOT read it). Use `strings -n 6 file.doc` to dump the
   form text: CIN, company name, registered office, meeting clause, field labels.

4. **Get shareholder details** — the AGM notice PDF (pymupdf) contains the
   shareholding table ("Details of Shares held by shareholders holding more than
   5%"): name, no. of shares, %. This is the authoritative source for the member's
   share count (e.g. Mrs. Roshini Ranka — 34,144 shares, 16.49%).

5. **Build the filled PDF** — reportlab, mirror the statutory text EXACTLY:
   - Header: FORM NO. MGT-11 / Proxy Form / statutory citation
   - Company block: CIN, name, registered office (from the .doc text)
   - Member block: name (bold), registered address (leave blank if unknown),
     email, folio (leave blank), no. of shares held (from notice table)
   - Appointment clause: "I/We, being the member(s) of N shares... hereby appoint"
   - Proxy block: name, address, email, signature line
   - Meeting clause (date/time/venue copied verbatim from notice)
   - "Signed this ___ day of ___ 2026" + signature boxes (Affix Revenue Stamp /
     Signature of shareholder / Signature of Proxy holder) with generous padding
   - Note: deposit ≥48h before meeting
   - Verify with pymupdf `get_text()` and render a preview PNG.

6. **Create the draft email** (raw Gmail API, never send):
   - From WORK account `ndr@draas.com` (DRA-group director work → google-draas
     even though the notice arrived in personal Gmail — per email-drafter rule)
   - To the shareholder ONLY (family member, e.g. rnr@draas.com), no CC
   - Subject: `Fwd: Notice of AGM on <date>...` — it's a FORWARD, so build the
     body with a `---------- Forwarded message ---------` block from the original
     notice (extract original body text, strip HTML crudely if needed)
   - Attachments: filled MGT-11 PDF + the original AGM pack PDF
   - `MIMEMultipart("mixed")` + `MIMEBase` attachments; create via
     `drafts().create()` with `{'message': {'raw': ...}}`

7. **Verify the draft** — `drafts().list()` must contain it (authoritative check,
   NOT `drafts().get()` alone), `labelIds` contains `DRAFT` (never SENT), To =
   shareholder only, both attachments present. Deliver the filled PDF to NDR via
   `MEDIA:/path` for review. Flag what's blank (registered address, folio) and the
   deposit deadline (48h before meeting).

## Pitfalls
- The AGM pack PDF can be 15MB+ — fine for a draft, but don't paste its text into
  context; extract only the shareholding table page.
- Roshni's registered address was not on file — leave the address line blank and
  flag it, don't invent one.
- The filled PDF is a REPLICA, not the official printed form — state that plainly.
- Drafts with malformed References can land in SENT — verify labelIds contains
  DRAFT after creation.
