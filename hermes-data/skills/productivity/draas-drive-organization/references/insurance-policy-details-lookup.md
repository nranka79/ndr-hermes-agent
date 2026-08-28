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

## Pitfalls
- Voice transcription mangles numbers (e.g. digits swapped/dropped). Search variants, don't trust the spoken form.
- Policy bond PDFs are 50+ pages; `pdftotext` works but the Schedule is usually around page 3 — search the text for "Policy Details" / "Sum Assured" / "Email ID" rather than reading sequentially.
- The registered email is NOT necessarily the user's main address — older policies often register an alias/old domain. Confirm with the bond, not with the user's current email.
