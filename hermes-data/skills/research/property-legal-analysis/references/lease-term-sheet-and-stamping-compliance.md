# Executed lease — key-terms extraction + stamping/registration compliance

**Trigger:** *"pull me the details of the lease agreement we have executed"*, *"what are the lease
terms"*, *"give me the rent / term / deposit / notice for <premises>"*, *"is this lease
registered?"*. This is the **term-sheet** job — distinct from `lease-deed-term-extraction.md`
(expiry/term only) and the `lease-renewal-extension-risk*` files (can the tenant stay on).

Worked example: **BHC (British High Commission) at Prestige Hermitage, Apartment 601, 6th floor**
— executed 11-Dec-2024, pulled 2026-10-13. Bharat asked by voice; "BHC"/"BDHC" = the British
Deputy High Commission, and "Prestige Homitage" (voice) = **Prestige Hermitage**.

## 1. Discovery — the lease family, and which copy is the executed one

`gws_drive_list(query="name contains 'Lease'")` returns ~30 files spanning many properties
(GBIT/Redsol, Serenity HillView lease-cum-sale, TruBuild sub-lease, Ranka Chambers 1984/1986).
Filter to the right property, then classify **each** hit before reading:

| Artifact | Meaning |
|---|---|
| `... Signed & Unregistered Lease Deed.pdf` | the **executed** copy — this is what "we have executed" means |
| `... Deed Of Lease (unsigned Copy).pdf` | pre-signature draft — never summarise this as the deed |
| `241127_<Property> Lease Deed` (Google Doc, owned by `*@ashlarlaw.com`) | external counsel's working draft |
| `... Deed of Lease dtd <earlier year>` | the **predecessor** lease (here 29.11.2021) — quote it only to establish the renewal chain |

Cross-check the mailbox for the execution trail: `gws_gmail_search(query="lease agreement <party>")`
surfaced the *"BDHC Lease renewal at Prestige Hermitage"* thread (NDR → Roshan Jacob @ashlarlaw →
Bharat), including NDR's *"is the renewed lease with BHC signed & executed?? Please confirm asap"*
— that thread is what establishes the deed was actually executed and who approved it.

## 2. Download + extract

```python
import io, sys
sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service
from googleapiclient.http import MediaIoBaseDownload

svc = build_service('drive', 'v3', service_name='google-draas')   # Bharat's own token
req = svc.files().get_media(fileId=FILE_ID)
with io.FileIO('/tmp/lease.pdf', 'wb') as fh:
    dl = MediaIoBaseDownload(fh, req)
    done = False
    while not done:
        _, done = dl.next_chunk()
```

Then `pymupdf` → `page.get_text()`. **Check the text layer per file — do not assume:**
the e-stamp/signed 2024 deed carried **27,000 chars over 17 pages** (clean text), while the 2021
original in the same folder returned **0 chars** (pure scan → needs OCR). Report the scanned one as
"needs OCR if you want it summarised" rather than silently skipping or burning OCR time on it.

## 3. The term-sheet field set (what a lease summary must carry)

Parties (with the representative + PoA chain) · Demised premises (unit, floor, parking slots, common
areas) · predecessor lease + its expiry · **Term** (duration + the exact commencement date, which is
also the Rent Commencement / Possession date) · **Rent ladder — every year, with the escalation %
and the monthly + annual figure** · payment frequency and invoice basis · **Security deposit**
(amount, interest-bearing or not, refund trigger) · parking charges (included or separate) ·
**Maintenance** (who provides, current annual figure, paid with rent, how increases are handled, and
the Annexure scope list) · repairs split (day-to-day vs structural) · utilities · taxes (who bears
property tax vs tax-on-rent) · permitted use · renewal clause (notice period, escalation, fresh deed)
· **termination** (no-cause notice period; cure period on breach) · indemnity · force majeure
restoration window · sale/transfer restriction · **dispute resolution** (arbitration seat + court
jurisdiction) · notices (addresses/emails) · **who bears stamp duty & registration** · witnesses.

Present it as labelled bullets with the rupee figures verbatim — NDR/Bharat read this to quote
numbers (rent, deposit) in a meeting, so never round or omit a year of the ladder.

## 4. Two compliance checks to run on EVERY executed lease (both fired here)

1. **Does the e-stamp certificate's article/classification match the actual term?** The certificate
   page (page 1, before the deed text) carries *Description of Document*, *Consideration Price*,
   *Stamp Duty Paid By*, *Stamp Duty Amount* and **Article**. Here it read
   **"Article 30(1)(a) Lease of Immovable Property Not exceeding 1 year" with ₹500 duty** — while the
   deed itself grants a **3-year** term. Flag the mismatch for a legal eyeball; do not silently
   "correct" it, and do not assert it is wrong — say what the certificate says and what the deed says.
2. **Is the executed copy actually registered?** The filename said *Signed & Unregistered*, and the
   deed makes registration the lessee's obligation (lessee bears stamp duty + registration fees) and
   requires a fresh **registered** deed on renewal. Ask whether a registered copy exists — the Drive
   family here contained none. For any lease ≥ 12 months, registration status is the first question a
   lawyer or a bank will ask.

Also sanity-check the escalation arithmetic across the ladder (Y1 ₹5,78,812/mo → Y2 ₹6,07,753 (+5%) →
Y3 ₹6,38,141 (+5%)) — a mis-stated percentage in a summary propagates straight into demand notes.

## 5. Sharing the executed deed with a colleague

When Bharat says "share it with <person>, I'll tell him" (no approval needed):
`gws_drive_permissions_add(file_id=..., email=..., role=...)` — resolve the address from the mailbox,
not the contacts sheet (internal staff; see `contact-phone-lookup` → `contact-email-lookup.md` §2b).
**Match the role already in use on that file** — read `gws_drive_permissions_list` first: this file's
DRA collaborators were all `writer` (Bhagya, Eshwari, NDR, sbari), so `writer` was the consistent
grant. State the role you granted and offer the downgrade to view-only in one line; don't send a
notification email when he says he will tell the person himself.
