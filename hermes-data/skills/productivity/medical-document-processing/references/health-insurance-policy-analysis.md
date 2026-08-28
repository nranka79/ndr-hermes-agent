# Health Insurance Policy Analysis — Workflow

When the user asks about a health insurance policy they hold (e.g. Royal Sundaram Lifeline Elite for Kanta Ranka), follow this pipeline to extract contacts, procedures, and compile a reference document.

## 1. Find the Policy Document

### 1.1 Search Google Drive

Search by the insured's name + "insurance" or the insurer name + policy type:

```python
from tools.gws_auth import build_service
drive = build_service('drive', 'v3', service_name='google-draas')

results = drive.files().list(
    q="name contains 'Kanta' and (name contains 'insurance' or name contains 'Insurance' or name contains 'Royal')",
    spaces='drive',
    includeItemsFromAllDrives=True,
    supportsAllDrives=True
).execute()
```

Known naming convention: `{Insurer}-{Product}_{insured-name}_{PolicyNo}_{YYYY-MM}.pdf`
Example: `RoyalSundaram-Lifeline-Elite_kanta-ranka_LLA0016946000107_2026-06.pdf`

### 1.2 Search Kelsa

If the user says "check Kelsa pipeline too":

```python
# Search DRA PO-WO Issuing pipeline (most common for insurance-related POs)
search_leads(pipeline_id=537, query="Royal Sundaram")
# Also check other pipelines: DRA Commitments (2002), DRA Invoice Processing (516)
```

Note: Insurance policies are often NOT in Kelsa — they live on Drive as PDFs. Don't spend too long searching Kelsa if nothing obvious turns up.

## 2. Extract Text from the PDF

Use pdftotext (works for digitally-created PDFs with embedded text):

```bash
pdftotext "/path/to/policy.pdf" /tmp/policy_text.txt
cat /tmp/policy_text.txt
```

If the PDF is scanned (image-based), fall back to ocrmypdf or vision analysis via `vision_analyze`.

## 3. Extract Key Policy Fields

From the text, identify these fields and their locations in the document:

| Field | Where to find | Worked example (KDR Royal Sundaram) |
|-------|--------------|-------------------------------------|
| **Policy No** | Cover letter or schedule | LLA0016946000107 |
| **Product / Plan** | Schedule | Lifeline Elite |
| **Insured Name & DOB** | Schedule | Kanta D Ranka, 21/06/1958 |
| **Policy Period** | Schedule | 14/06/2026 – 13/06/2027 |
| **Sum Insured** | Schedule | ₹15,00,000 + NCB ₹12,00,000 = ₹27,00,000 |
| **Premium Paid** | Schedule | ₹2,09,731 |
| **Co-payment %** | Special Conditions section | 20% |
| **Exclusions / Pre-existing** | Schedule | Middle ear (H65-H75), Arthrosis (M15-M19), Ischaemic Heart (I20-I25) |
| **TPA Details** | Service Provider section | Medi Assist Insurance TPA Pvt. Ltd — 1800 345 3322 |
| **Customer Service** | Footer / Contact section | care@royalsundaram.in, 1860 258 0000 |
| **Cashless TPA Address** | Service Provider section | Tower D, 4th Floor, IBC Knowledge Park, 4/1 Bannerghatta Road, Bangalore 560029 |
| **Worldwide Emergency Provider** | Service Provider section | Europ Assistance India Pvt. Ltd — +91-22-67872035 |
| **Nominee** | Schedule | Dinesh Devraj Ranka (Husband) |
| **First Inception Date** | Schedule | 20/11/2018 (continuous since) |
| **Intermediary / Broker** | Schedule | Beena G (Code: OA507645) |

## 4. Research Claim Procedures

### 4.1 When web tools ARE available (FIRECRAWL_API_KEY configured)

Search for:
- `{Insurer} {Product} claim process reimbursement`
- `{Insurer} health insurance claim form download`
- `{Insurer} claim dispute underpayment grievance redressal`

### 4.2 When web tools are NOT available (FIRECRAWL not configured)

Use `call_openrouter_model` with a verified-working model slug as a research proxy:

```python
call_openrouter_model(
    model="google/gemini-2.5-flash",
    prompt="""Research [Insurer Name] [Product Name] health insurance claim procedures...

Include:
1. Contact numbers, emails, mailing addresses
2. Reimbursement claim process (step by step)
3. Pre-hospitalization / pre-operative expense claim process
4. Dispute / grievance escalation matrix
5. Cashless claim process through TPA

Policy details for context: [paste relevant fields from Stage 3]"""
)
```

**Verified working model slug:** `google/gemini-2.5-flash`

The response will contain generic Indian insurance industry procedures that are mostly correct for the insurer. Cross-reference with specific details from the policy document (TPA name, co-payment %, exclusions) to annotate with actual policy-specific information.

### 4.3 Try direct website access via curl

Some insurer websites block browsers but serve curl requests with a User-Agent header:

```bash
curl -sL "https://www.{insurer}.in/claims/health-claims" -A "Mozilla/5.0" 2>/dev/null | grep -i "claim\|form"
```

Most will block (Akamai/Cloudflare) — don't spend more than 2 attempts.

## 5. Compile into a Structured Google Doc

### 5.1 Create the document

```python
from tools.gws_auth import build_service
docs = build_service('docs', 'v1', service_name='google-draas')
drive = build_service('drive', 'v3', service_name='google-draas')

doc = docs.documents().create(body={
    'title': '{Insured Name} — {Insurer} {Product} Insurance — Claim Contacts & Procedures'
}).execute()

doc_id = doc.get('documentId')
```

### 5.2 File in the TMP folder

```python
TMP_FOLDER_ID = '18p74II2uL32sNDzDDwXzmlOUdJJOTmE-'  # verified TMP folder for NDR

drive.files().update(
    fileId=doc_id,
    addParents=TMP_FOLDER_ID,
    removeParents='root',
    fields='id, parents'
).execute()
```

### 5.3 Populate with structured content via batchUpdate

```python
full_text = """# Title
...
## 1. Insurer Contact
...
## 2. TPA Contact
...
## 3. Emergency Services
...
## 4. Grievance Escalation
...
## 5. Reimbursement Claim Process
...
## 6. Pre-operative / Pre-hospitalization Claims
...
## 7. Cashless Claim Process
...
## 8. Key Policy Notes
...
"""
requests = [{'insertText': {'location': {'index': 1}, 'text': full_text}}]
docs.documents().batchUpdate(
    documentId=doc_id,
    body={'requests': requests}
).execute()
```

### 5.4 Document sections (template)

Include these sections in order:

1. **Title header** — Insured name, insurer, product, date prepared
2. **Policy Summary Table** — Key fields in a clean table format
3. **Insurer Contact** — Phone, email, mailing addresses, grievance email
4. **TPA Contact** — Phone, email, claim submission address, mobile app
5. **Emergency Services** — Worldwide provider contact
6. **Insurance Ombudsman** — For dispute escalation when internal grievance fails
7. **Reimbursement Claim Process** — Required documents, where to submit, timelines
8. **Pre-operative / Pre-hospitalization Expenses** — Coverage period, how to claim
9. **Claim Dispute / Underpayment Escalation** — Step-by-step grievance matrix
10. **Cashless Claim Process** — Planned vs emergency, how pre-auth works
11. **Key Notes from Policy** — Co-payment, exclusions, waiting periods, broker info
12. **Quick Reference Card** — Table of all contacts by purpose

## 6. Post-Completion

1. **Report the Drive URL** to the user so they can open and review
2. **Offer to save as a skill** if it was a complex multi-step research task
3. **Note any specific policy quirks** (e.g. 20% co-payment, specific pre-existing disease codes) that would matter in a future claim

## Pitfalls

### P1. The research model may produce generic info, not policy-specific details

Gemini/OpenRouter research will return *standard* Indian health insurance claim procedures that are 80% correct but may miss policy-specific nuances (e.g. exact pre-hospitalization days, specific waiting periods, niche exclusions). Always annotate the research output with actual policy document data before presenting to the user.

### P2. Multiple Royal Sundaram customer service emails exist

The policy letter says `care@royalsundaram.in` but the footer says `customer.services@royalsundaram.in`. Include both — the first is for general queries, the second for escalated service requests.

### P3. The TPA address in the policy may differ from the TPA's corporate website

Use the address printed ON THE POLICY DOCUMENT for claim submission, even if the TPA's website shows a different address. The policy document address is what the insurer has on file.

### P4. Kelsa may not contain the insurance record

Health insurance is often managed via the insurer's portal and documents on Drive, not in Kelsa. Don't spend excessive time searching Kelsa pipelines — if two searches (PO-WO and Invoices) turn up nothing, report that it wasn't found in Kelsa and proceed with Drive data.

## Related

- `medical-document-processing` umbrella skill — this reference covers policy analysis only. For actual claim filing (discharge summary → TPA submission), see the main skill.
- `ocr-and-documents` — if the policy PDF is a scan
- `google-workspace` — Drive search, Docs API, Gmail for finding related emails
