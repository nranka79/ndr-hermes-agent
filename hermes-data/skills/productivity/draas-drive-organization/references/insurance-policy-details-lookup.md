# Insurance Policy Details Lookup (by policy number)

Recurring request: "check my emails/drive for <insurer> policy <number> — I want all details including the registered email address."
Verified pattern (Bajaj Life 0444146783, Aug 2026).

## Search order (exhaustive, in this sequence)
1. **Exact number in Gmail** across ALL accounts (`gws_resolve_account` first, then each: `google-draas`, `google-ahfl`, `google-gmail`). Use `q="0444146783"` — Gmail tokenizes digits, so the bare number works.
2. **Number variants** in the primary account: drop leading zero (`129667661`), partial tails (`9667661`, `0129667`), spaced forms (`"0 12966"`). Insurers write policy numbers inconsistently; voice transcription also drops digits.
3. **Drive fullText + filename** across all accounts: `fullText contains '0444146783'`, `name contains 'Bajaj'`, `name contains 'policy'`.
4. **Session history** (`session_search`) — policy disputes often span prior sessions.
5. **Family-member sweep** if the number isn't NDR's own: `to:rnr@draas.com Bajaj`, `to:kdr@draas.com Bajaj`, `"Kanta" insurance policy`, etc.

## Authoritative sources once found
- **Policy bond PDF** (usually on Drive, e.g. `20210320_BajajAllianz0444146783.pdf`): download via Drive API, `pdftotext` it. The bond's cover page + Schedule page carry: policy number, plan name, policyholder + address, **registered Email ID** (often an older alias like `ndr@drahomes.in` — the bond's email is the one the insurer considers registered), phone, Sum Assured, premium + GST, PPT/maturity, nominee. This is the ONLY place the registered email appears reliably.
- **Policy bond delivery email** (`policy.bond@bajajallianz.co.in` / `DONOTREPLY@bajajlife.com`) — subject contains the policy number; To header shows the registered address at issuance.
- **Life_Policy_Payment_Tracker** spreadsheet on Drive — canonical list of NDR's life policies (insurer, plan, policy no., premium, due date). Cross-check any policy number against it.
- **Case-analysis / IRDAI folders** (e.g. "Bajaj Life Insurance" folder) — hold bond PDFs, revival emails, complaint numbers.

## Reporting
- Give full policy profile (plan, SA, premium, term, nominee) + registered email/phone from the bond.
- If a number yields ZERO hits after the full sweep, say so plainly and give the likely explanations (different insurer, general-insurance policy, family member's account, digit transposition) — ask the user where they saw the number before chasing further.

## Premium receipt filing (paid policy, "I just uploaded a receipt" workflow, verified 2026-08-31)

When NDR uploads a fresh premium receipt (e.g. Bajaj Life Smart Protection Goal, policy
0444146783, ₹61,920 paid 31-Aug-2026) to Drive root and asks to rename/file/post:
1. **Find it by createdTime, not name.** Uploads from email-print often keep a generic name
   (`Emailing 3932_0444146783_1788180061351.pdf`). Query `'root' in parents` ordered by
   `createdTime desc` and match today's upload, then `pdftotext` to confirm policy number /
   premium / date from the PREMIUM RECEIPT block (receipt no, policy no, amount, payment mode,
   GSTIN source branch).
2. **Rename per convention** `YYYYMMDD_Entity_Description`, e.g.
   `20260831_BajajLife_Policy_0444146783_Premium_Receipt_61920`.
3. **File into the insurer's Personal folder.** Existing Bajaj Life files live in
   `Personal > Bajaj Life Insurance` (id `1kXXMnzksIvw5ABW18rrlfHRuHUAUedv5`) — walk the
   parents of an existing Bajaj file to discover it rather than guessing. One
   `files().update(fileId, body={name}, addParents=<folder>, removeParents='root')` call.
4. **Post a no-PO already-paid invoice in Kelsa pipeline 516** so the payment is on record —
   see kelsa-write → `references/dra-invoice-processing-pipeline.md` → "No-PO / already-paid
   invoices" for the full 7-step flow (vendor 531 → Nishant Ranka master → no po → receipt
   upload → payment fields → Already paid note).

## Pitfalls
- Voice transcription mangles numbers (e.g. digits swapped/dropped). Search variants, don't trust the spoken form.
- Policy bond PDFs are 50+ pages; `pdftotext` works but the Schedule is usually around page 3 — search the text for "Policy Details" / "Sum Assured" / "Email ID" rather than reading sequentially.
- The registered email is NOT necessarily the user's main address — older policies often register an alias/old domain. Confirm with the bond, not with the user's current email.

## Filing premium receipts (verified 2026-08-31)
Recurring request: "I uploaded a premium receipt to Drive, rename + file it." Pattern:
- Name per convention: `YYYYMMDD_BajajLife_Policy_<policyno>_Premium_Receipt_<amount>`
  (e.g. `20260831_BajajLife_Policy_0444146783_Premium_Receipt_61920`).
- Destination: **Personal > Bajaj Life Insurance** folder (same place as the Feb-2026
  cheque-premium PDF and the case-analysis files). The scan is usually a multi-page PDF
  with no text layer — render page 1 and OCR it to confirm policy no / amount before naming.
- If the uploaded PDF has a generic name like `Emailing 3932_...pdf`, find it at Drive root
  (parent='root') sorted by createdTime desc — name-based search misses it.
- **Folder write-access check before proposing a destination**: not every folder is writable
  by the ndr token. e.g. "Legal documents" (Allalasandra title docs, owner
  sales1.blr@draas.com) has `canAddChildren=False` → upload fails 403
  `insufficientParentPermissions`. Always call files().get(fields='capabilities') and pick a
  writable target (user confirmed: North Star land docs go to **Ranka Northstar** folder root,
  NOT the `01_Approvals_and_Title` subfolder — that empty subfolder was rejected by user).
- After filing, NDR usually wants a Kelsa 516 already-paid no-PO invoice for the premium —
  see kelsa-write skill → dra-invoice-processing-pipeline reference.
