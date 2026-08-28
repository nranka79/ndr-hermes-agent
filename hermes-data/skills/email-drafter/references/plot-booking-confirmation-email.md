# Plot Booking-Confirmation Email (Ranka Udaya / DRA plot sales)

Validated 2026-08-25 on Pragya Joythi (Plot 5, Block 5, Ranka Udaya, lead #54917102).

## When to use
Bharat books a plot for a portal lead, the booking amount lands, and he wants the
confirmation email that carries the legal document pack. Voice trigger he uses:
"this document has to be attached to [customer] ... congratulate him for booking ...
confirm the receipt of the amount ... receipt will be followed by tomorrow end of day."

## Workflow (proven sequence)
1. **Pull the booking amount from Kelsa**, never invent it. `search_leads` for the
   customer in Pipeline 10 → `get_lead` → `list_lead_notes`. The amount lives in
   Bharat's notes ("The client has transferred the ₹50,000 booking amount...").
   Also grab final rate / plot / extras (e.g. ₹3,600/sqft all-inclusive + ₹20,000
   legal handling) from the same notes to keep the email consistent.
2. **Locate the legal pack** (see draas-due-diligence-pack skill for building it).
   Usually `Ranka_Udaya_Legal_Document_Pack.pdf` in `/data/hermes/users/sales1.blr/outbound/`.
   If > ~19 MB raw, compress first (see SKILL.md "Gmail attachment cap" pitfall —
   /ebook alone is NOT enough; use the /screen + downsample recipe) and verify pages
   preserved via `pdfinfo` + legibility via `pdftoppm` + vision.
3. **Draft from the SALES mailbox** — `HERMES_SESSION_USER_ID=sales1_blr
   GWS_VAULT_SOCKET=/run/gws-vault/vault.sock`, `service_name="google-draas"`
   (vault resolves to sales1.blr@draas.com). Assert `getProfile()['emailAddress'] ==
   'sales1.blr@draas.com'` before creating. Draft ONLY — never send.
4. **Build MIME with attachment via raw Gmail API** (bridge `draft_create` has NO
   attachment support): MIMEMultipart("mixed"), body part + MIMEBase pdf part,
   `encoders.encode_base64`. Print `len(raw)/1048576` — must be ≤ 33 MB encoded.
   Delete any earlier oversize/duplicate draft first (`drafts().delete` with the
   DRAFT resource id, not message id).
5. **Verify** with `drafts().get(format='full')`: From / To / Subject headers + walk
   payload parts for the attachment filename + size.

## Email body (Bharat's dictated structure)
1. Congratulations on booking Plot No. X, Block Y at [Project] — "delighted to have you on board"
2. Confirm receipt of booking amount: Rs. 50,000 (Rupees Fifty Thousand only)
3. Legal document set attached per our commitment — "for your review and verification"
4. Official booking receipt will follow by tomorrow end of day
5. Offer assistance + sign-off: Bharat H, DRAAS - [Project], sales1.blr@draas.com

## Subject convention
`[Project] | Plot X, Block Y - Booking Confirmation & Legal Documents`

## Attachment naming
Customer-facing display name, e.g. "Ranka Udaya - Legal Document Pack.pdf" — NOT
the internal "Copy of ..." filename from Drive.