# Drive search for FSA-era loan allocation letters

Pattern for finding loan / debt allocation letters executed around a Family Arrangement Deed (or similar family-settlement context), when multiple legal heirs allocate estate loans to specific beneficiaries.

## When to use

User asks: "find the document where [Heir A] owes [Heir B] a loan", "the loan allocation letter from the family settlement", "who got what loan from the estate", etc. The trigger is a family-settlement context where:
- Multiple Class-I legal heirs of a deceased parent are involved
- Loans receivable from various companies (DRA group, partnerships, etc.) need to be reallocated among the heirs
- The trigger date is the Family Arrangement Deed (FSA) execution date

## Workflow

### 1. Find the FSA date first

The FSA date is the anchor — every loan allocation letter will be dated within a few days before/after it. Search for documents with names like:
- "FAMILY ARRANGEMENT DEED"
- "Family Settlement"
- "Family Understanding & Settlement"
- "[Names] Family Arrangement"

Open the latest dated one (there are often 3-5 drafts) and read the FSA date. Family arrangement deeds at DRAAS have been:
- 06/08/2025 (KDR + DDR + NDR + MDR + MRR, DRA group, 6-7 letters)
- 28/09/2022 (earlier DRA family understanding)

### 2. Search Drive with name + fullText for the relevant parties

```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

creds = Credentials.from_authorized_user_file("/data/hermes/google_token.json")
drive = build("drive", "v3", credentials=creds)

queries = [
    "name contains 'Mamta'",
    "name contains 'Rathod'",
    "fullText contains 'Mamta Rathod'",
    "fullText contains 'Ramkal'",  # common OCR/typo for Ranka
]
seen, all_files = set(), []
for q in queries:
    for f in drive.files().list(q=q, pageSize=50,
        fields="files(id,name,mimeType,createdTime,modifiedTime,webViewLink)"
    ).execute().get("files", []):
        if f["id"] not in seen:
            seen.add(f["id"]); all_files.append(f)
```

Then filter results by `modifiedTime` near the FSA date (e.g. ±30 days).

### 3. Classify the candidates by counterparty

The loan allocation letters are typically addressed to the company whose loan is being reallocated, and signed by all 5 legal heirs. Naming pattern:
- `Ltr DR Heirs to [CompanyName] for Loan Allocation`
- `Ltr [HeirInitial] [HeirInitial] 2 [CompanyCode] Board for [DR/MRR] Loan Recording`
- `Ltr [HeirInitial] 2 [CompanyCode] - Assignment of Loan to [HeirInitial]`
- `Board Resolution for [HeirInitial] Loan Acknowledgement & Repayment`

Counterparty codes seen in DRA group (June 2025 FSA):
- **DRAPL** = DRA Projects Private Limited (Bangalore, Queens Road)
- **DRASCP** = DRA Aadithya South City Projects Private Limited (Chennai, Royapettah)
- **DRA Investments** (Bangalore)
- **DRA Finance and Investments** (Chennai)
- **Eastern Farmlands (India) Private Limited** (Bangalore)
- **Canara Housing Development Company**

### 4. Read each candidate with the right method

Google Docs native → `drive.files().export_media(fileId, mimeType='text/plain')` then decode utf-8.
The first 2000-3000 chars of each letter is usually enough to see the subject, amount, and counterparty.

### 5. Match what the user actually asked

User phrasing matters. "Nishant owes Mamta" can mean three different things in an FSA context:

| User said | What it usually is |
|---|---|
| "Nishant owes Mamta a loan" | Letter allocating estate loan TO Mamta (where DR estate's receivable is now hers) |
| "Nishant took a loan from Mamta" | Private debt between siblings, may NOT be in Drive |
| "The loan capture from the family settlement" | The full set of allocation letters + the board resolution approving them |

When in doubt, list the candidates and let the user pick — do NOT guess which one is "the" document.

## Key gotcha — "the loan letter" is plural

The FSA-era loan allocation set typically includes:
- 5-6 letters (one per company with a loan receivable)
- 1-2 board resolutions (one per company acknowledging the allocation)
- 1 master letter of instruction

If user asks for "the loan letter" and there are 6 candidates, surface all of them with the company + amount, and let them pick.

## Token path for this workflow

The DRA group FSA-era documents sit in `ndr@draas.com`'s Drive. The current working pattern uses the **global token** at `/data/hermes/google_token.json` (not the per-user token at `the gws-vault daemon (no token files exist on disk — see api-references/google-workspace-api/references/token-access-canonical.md)`). This token has Drive scope only. The global token is loaded as:

```python
creds = Credentials.from_authorized_user_file("/data/hermes/google_token.json")
```

No `HERMES_SESSION_USER_ID` needed, no `HOME=` prefix. If the per-user token is needed (e.g. for a different user's Drive), use the per-user path documented in PITFALL #1b.

## Verified example (June 2026, Mamta Rathod / FSA 06/08/2025)

8 documents found across 2 searches (`Mamta` + `Rathod` + `Mamta Rathod` + `Ramkal`):

| Counterparty | Doc | Amount |
|---|---|---|
| DRA Projects Pvt Ltd (DRAPL) | "Ltr DR Heirs to DRAPL Board for Loan to MRR" | ₹2,14,93,238 to MRR |
| DRA Aadithya South City (DRASCP) | "Ltr MDR 2 DRASCP - Assignment of Loan to MRR" | ₹4,99,00,000 from MDR's share |
| DRA Developers & Projects | "Ltr DR Heirs 2 DRADPL Board for DR Loan Recording" | ₹6,08,80,206 split 42.5/42.5/15 |
| DRA Finance & Investment (Chennai) | "Ltr DR Heirs 2 DRA Finance & Investment Board" | ₹2,00,00,000 split 42.5/42.5/15 |
| DRA Investments (Bangalore) | "Ltr DR Heirs to DRAInvestment for Loan Allocation" | ~₹2,00,00,000, conditional on Gunjur sale |
| Eastern Farmlands | "Ltr DR Heirs to Easternfarmland 4 Loan Allocation" | ~₹97,00,000 split 42.5/42.5/15 |
| DRA Projects (board resolution) | "DRAPL Board Resolution for MRR Loan Acknowledgement & Repayment" | Records the ₹2,14,93,238 allocation |

The "Loan_Settlement_Letter_To Mamta Ranka" doc (Canara Housing loan settlement, ₹15 Cr) is a **different** document — older (Apr 2025) and unrelated to the FSA loan allocations. Don't confuse them.

## When NOT to use this pattern

- The user wants a single specific document by name → just `name contains` query
- The user wants to file a NEW loan document → use `drive-document-routing-workflow`
- The user wants to find a private sibling-to-sibling loan (not estate allocation) → search broader, fullText queries, may not be in Drive
