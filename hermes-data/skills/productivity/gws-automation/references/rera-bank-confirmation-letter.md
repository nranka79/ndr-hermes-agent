# RERA Bank Confirmation Letter

A letter on bank letterhead confirming the project's designated RERA bank account. Required for KRERA registration as proof of a dedicated project account under Section 4(2)(l)(D) of RERA Act.

## Standard Format

| Section | Content |
|---------|---------|
| **Letterhead** | Bank name, logo, branch address, IFSC, contact |
| **Date** | Date of issue |
| **To** | The Secretary, Karnataka Real Estate Regulatory Authority (KRERA) |
| **Subject** | Bank Confirmation for the Project "Ranka Amber" — M/S DRA Realty Private Limited |
| **Body** | Confirms that the promoter maintains a designated RERA project account |
| **Account Details Table** | Account holder, number, IFSC, branch, account type, facility type |
| **Confirmation Points** | 7 numbered confirmations (see below) |
| **Signature** | Authorized Signatory with bank seal |
| **Enclosures** | Account statement (usually last 6 months) |

## Account Details for DRA Realty

| Field | Value |
|-------|-------|
| **Account Holder** | DRA Realty Private Limited |
| **Account No** | 8547630957 |
| **IFSC** | KKBK0008068 |
| **Branch** | Kotak Mahindra Bank (confirm specific branch — usually the branch where the account is maintained) |
| **Account Type** | Current Account / Cash Credit / Overdraft (varies by project) |

**⚠️ Common mistake:** The account `8551119387` with IFSC `KKBK0000431` (Kotak Indiranagar) belongs to a different entity/purpose. DRA Realty's RERA account is `8547630957` with IFSC `KKBK0008068`. Always verify against the NDR DRAAS contacts sheet or the account register in memory.

## 7-Point Confirmation Requests

The letter typically asks the bank to confirm:

1. Account is maintained in the name of the promoter/developer
2. Account is designated for the specific project (RERA compliant)
3. All collections from allottees are deposited into this account
4. Withdrawals are permitted only for project-related expenses
5. Bank will provide statements whenever requested by RERA
6. Account is operational and in good standing
7. Any change in account status will be notified to RERA

## Handling "Particulars Not Filled Properly" Feedback

When a user (especially Prakash or Nishant) reports that account particulars in a generated RERA doc are wrong:

1. **Acknowledge immediately** — do not debate or verify before acknowledging
2. **If OAuth allows, read the doc** to show current values:
   ```python
   doc = docs_service.documents().get(documentId=doc_id).execute()
   ```
3. **If OAuth token expired** (RefreshError: invalid_grant):
   - State clearly that the token needs re-authorization
   - Generate auth URL for the document owner's Telegram ID
   - **Ask specific clarifying questions** about what needs to change (account number, IFSC, branch, holder name, etc.) rather than a generic "what's wrong?"
4. **Present the current values** in a table and ask which fields need correction
5. **Once clarified, apply corrections** via Docs API `batchUpdate()` or re-create

### Common Particulars Corrections for DRA Realty Docs

| Field | Often Mistaken For | Correct Value |
|-------|-------------------|---------------|
| Account No | 8551119387 (Kotak Indiranagar — different entity) | 8547630957 |
| IFSC | KKBK0000431 (Indiranagar branch) | KKBK0008068 |
| Account Holder | Individual name / different entity name | DRA Realty Private Limited |

## Pitfalls

1. **Account duplication:** DRA Realty may have multiple accounts at Kotak (CC, OD, Current, FD). The RERA designated account is the **Current Account** used for project collections. Verify which one is registered with RERA.
2. **Bank branch vs account branch mismatch:** The letter may come from one branch while the account is maintained at another. Use the account's home branch IFSC, not the issuing branch.
3. **OAuth token expiry blocks reading the doc:** Always check token validity before trying to read. If RefreshError occurs, you cannot see the current doc state — ask the user for the specific corrections.
4. **Cross-user document access:** If Nishant created the doc but Prakash is reviewing it, the session OAuth (Prakash's) cannot read Nishant's doc. Generate a Nishant auth URL or have Prakash describe what's wrong.
