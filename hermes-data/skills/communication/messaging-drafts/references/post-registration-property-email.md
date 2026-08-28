# Post-Registration Property Task Assignment Email

**Trigger:** A flat/apartment has been registered at the SRO. Nishant wants to email the team (Rahul, Bharat, Roshni) with priority tasks and document links.

## Key Principles

1. **Instructions in the email body only** — Do NOT create separate Google Docs with task instructions or property summaries. They clutter the Drive and get deleted.
2. **Drive folder = 3 types of docs only:**
   - Draft letters to be signed (Letter to Association, BESCOM app, eKhata app)
   - Signed/scanned reference docs from the seller
   - Nothing else (no summaries, no instruction docs)
3. **Apologize for earlier errors** — If this is a corrected resend, lead with "Apologies — please ignore the earlier emails."
4. **Clear role assignment** — Each person's tasks clearly listed:
   - **Rahul (Vinod Das):** Government submissions (eKhata transfer, BESCOM meter transfer). He prepares draft letters, gets Roshni to sign, submits to the respective office.
   - **Bharat (Hawaldar):** Coordination. Scans and uploads seller's signed documents, coordinates Association letter (print → Roshni signs → submit → get acknowledgement → scan → file).
   - **Roshni Ranka:** Signs letters. All draft letters are addressed FROM her.

## Email Structure

### Subject
`Flat No. E914, {Project Name} — {status/instruction}`

### Opening
```
Dear Rahul,

Apologies — please ignore the earlier emails. {OR direct start}

We have successfully registered Flat No. {number} at {Project}, {Address} in the name of Mrs. Roshini Ranka (PAN: X, Aadhaar: Y) vide registered Deed of Absolute Sale dated {date} bearing Document No. {number}, SRO {office}.
```

### Task sections (one per person)
H3 headers, prioritised:
- **TASK 1 — BESCOM ELECTRICITY METER TRANSFER** (Rahul): RR number, application draft link, signed docs available
- **TASK 2 — E-KHATA TRANSFER** (Rahul): Khata number, application draft link
- **BHARAT'S ROLE**: Scan signed docs from seller + coordinate association letter

### Drive Documents section
Split into two subsections:

**📁 DRAFT LETTERS (to be signed by Roshni):**
- Letter to Association: {link}
- BESCOM Transfer Application: {link}
- eKhata Transfer Application: {link}

**📁 SIGNED/SCANNED COPIES (for reference):**
- Registered Sale Deed PDF: {link}
- Khata Certificate: {link}
- Latest EB Bill: {link}
- *(Bharat to add scanned Ravi docs here)*

### Closing
"Please coordinate with each other. Both tasks are urgent — target completion at the earliest."

## CC Field
Always: `sales1.blr@draas.com` (Bharat), `rnr@draas.com` (Roshni)

## Drive Folder Structure
Parent: `914 EH Sale Agreements/`
Folder: `E914 - Post Registration/`

Contents:
```
E914 - Post Registration/
├── 20260608 E914 Letter to Association - Ownership Change to Roshni Ranka (Google Doc)
├── 20260608 E914 - BESCOM Meter Transfer Application (Roshni Ranka) (Google Doc)
├── 20260608 E914 - eKhata Transfer Application (Roshni Ranka) (Google Doc)
└── (signed/scanned PDFs uploaded by Bharat)
```

## Email Address Confirmation
Before sending, confirm the email addresses verbally stated in the voice message:
- Rahul's correct email: `vkdas@draas.com` (NOT vkdaas, NOT drahomes.com)
- Always spell-check letters from voice: V-K-D-A-S, not V-K-D-A-A-S

## Tools Used
- per-user GWS token (`the gws-vault daemon (no token files exist on disk — see api-references/google-workspace-api/references/token-access-canonical.md)`) for Gmail + Drive
- Gmail API via `googleapiclient.discovery.build("gmail", "v1", credentials=creds)`
- Drive API for folder creation, doc creation, sharing
- Docs API for creating draft letters
- Telegram `send_message` for post-email updates to each person
