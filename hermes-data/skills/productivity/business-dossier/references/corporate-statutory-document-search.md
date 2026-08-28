# Corporate / Statutory Document Search (NOC, Registered-Office Consent)

Use when the user asks to find a specific legally-scoped corporate document in Drive + Gmail
— e.g. "find the NOC from [persons] to [company] for using [premises] as its registered
office." Different from open-ended dossier discovery: here the user names a document TYPE,
the counterparties, and a premises, and expects that specific document to exist.

## Step 0 — Restate the query as a search grid
Decompose into searchable columns:
- Document type: NOC / No Objection / consent
- Issuer(s): party names
- Recipient: the corporate entity (DRA Realty Private Limited, etc.)
- Subject/premises: registered office / Queen's Corner / unit no.

Every cell is a Gmail query and a Drive `fullText`/`name` query. Combine them.

## Step 1 — Confirm the premise from the entity's OWN statutory records (do this first)
Before hunting for the NOC, verify the underlying relationship is real. The most reliable
anchor is the target company's **Certificate of Incorporation** on Drive. It states the CIN,
the "pursuant to change of name" history, and — critically — the **registered-office mailing
address as per ROC** (e.g. "201A/202BA, Queens Corner, No.3, Queens Road, Bangalore 560001").

Why this matters: it confirms (a) the company's registered office is indeed the premises the
user named, and (b) the entity is the right one (watch for "pursuant to change of name" —
DRA Realty was formerly SOUTHCITY RETAIL PLUS PRIVATE LIMITED; search the OLD name too).
Drive query that finds it reliably: `name contains 'incorporation certificate'`.

A corporate "firm related documents" folder (recently created during a compliance cleanup)
often consolidates: incorporation cert, AoA, MoA, PAN, GST cert, director KYC. List its
contents — the consent/NOC is frequently filed alongside these.

## Step 2 — Search ladder (each rung narrows)
1. Gmail keyword queries across variants AND across all accounts (google-draas / google-ahfl
   / google-gmail). Pair the premises + entity: `"Queens Corner" DRA`, `NOC Dinesh`,
   `"registered office" Queens`.
2. Drive `fullText contains` + `name contains` for the same variants.
3. If a name is rare, run it alone (`Ayaz`) across ALL accounts and read every hit — few hits
   means the name is either absent or a false positive.
4. Read the bodies of the ROC/CS compliance threads (the company secretary agent, e.g.
   "JAYACHANDRAN K" for DRA entities) — these are where registered-office, reconstitution,
   and director-change consents actually live. Pull `format='full'` and walk payload parts to
   get bodies + attachment filenames; filter bodies for keywords (registered office, NOC,
   no objection, premises, consent).
5. Download + `pdftotext` the candidate property documents (release deed, sale deed for the
   premises) to confirm who owns the premises. Match the unit number from the corporation's
   registered address (e.g. "202B 'A', Block A, 2nd Floor, Queens Corner") to the property
   deed's schedule.

## Step 3 — Voice-transcription disambiguation (critical pitfall)
Voice-note requests frequently contain a mis-heard person name. Doctrine:
- If the named party returns **zero relevant hits** across all accounts (only unrelated false
  positives), AND
- the real counterparty is **deceased / estate-held / a family group** (check: release
  deeds, family-settlement documents, succession filings),
- then the name is almost certainly a **transcription error** — most commonly "heirs"
  ("NOC from the heirs of Late X"), or a garbled family-initial pair (NDR/MDR).
Do NOT fabricate the document or invent a person. Report the confirmed relationship
(registered office + ownership) and state plainly the literal document was not found, offer
the transcription-error interpretation, and ask the user to confirm the exact wording.

## Step 4 — Honest "not found" + options
If the specific NOC does not surface: say so directly. Do not dress it up as found. State
what WAS confirmed (registered office from incorporation cert, premises ownership from the
release deed) and offer concrete next steps:
- The consent may exist only as a **physical/paper record at RoC** filed at incorporation
  (Section 12 registered-office consent is a statutory-register/ROC document, not always
  digitized into Drive/Gmail).
- Offer to **draft** the NOC for signature.
- Ask the user to confirm the exact issuer wording / who the second person is, then re-run.

## Quick pattern
```python
# Confirm the registered office from the incorporation certificate
drive.files().list(q="name contains 'incorporation certificate'", ...)
# -> extract "Mailing Address as per record available in Registrar office:"

# Read compliance-thread bodies (not just headers)
full = gmail.users().messages().get(userId='me', id=mid, format='full').execute()
# walk payload.parts for text/plain and attachments; filter for registered-office/NOC keywords

# Confirm premises ownership
# release deed / sale deed schedule unit no must match the incorporation registered address
```
