# Sale Deed — Party Detail Cross-Verification Against Drive Source Documents

**Use when:** User asks you to verify a sale deed's factual claims (party names, addresses, registration numbers, PAN, CIN, Aadhaar, title chain) against the actual source documents stored in Drive. The user has usually already done a manual check and wants a structured confirmation with red flags identified.

**Do not confuse with:** `standalone-document-review-workflow.md` (typos/formatting/internal consistency), `ranka-iris-sale-deed-clause-review-patterns.md` (RERA clause compliance), or `ats-vs-sale-deed-crosscheck-914-embassy.md` (checking ATS vs final sale deed for scope changes).

## When to Load This

- User says "check the sale deed against the supporting docs in Drive"
- User lists specific items to verify: party names, registration numbers, PAN, CIN, addresses
- User says "I found everything in order but need confirmation"
- User flags a potential discrepancy they spotted and wants you to verify

## Workflow

### 1. Find the Sale Deed Document in Drive

The user may provide a name or a link. If searching:
```python
# Try exact name first, then broader terms
# gws_skill_bridge.call('drive_search', service_name='...', query='Ranka_Oasis_Plot65_Sale_Deed')
# If no results, try just the project name + "sale deed" or "plot" + number
```

Pitfall: The user's stated document name may not match the actual filename in Drive. If exact search returns nothing, use progressively broader terms (project name, plot number, "CLD", "sale deed").

### 2. Read the Full Document Content

```python
# For Google Docs:
call('docs_get', service_name='...', doc_id='FILE_ID')
```
Note: `docs_get` expects `doc_id` parameter (not `document_id`). The skill function accesses `args.doc_id`.

### 3. Identify All Party/Entity References to Verify

Extract from the deed:
- **Vendor/Seller details** — firm name, registration number, PAN, address
- **Each partner's details** — company name, CIN, address, authorized representative (name, designation, Aadhaar)
- **Managing Partner** — full name, father's name, age, address, Aadhaar
- **Confirming Party / Developer** — name, CIN, registered office, authorized representative
- **Purchaser** — name, age, Aadhaar, PAN, address
- **Title chain references** — JDA numbers, sale deed numbers, partition deed numbers
- **Key document references** — layout approval numbers, RERA numbers, gift deed numbers, SPA numbers

### 4. Search Drive for Supporting Source Documents

For each entity/party, search Drive for:
- **Partnership deed** — verify firm name, partners, shareholding, registration date
- **Reconstitution deed** — verify partner changes, retirement, share reallocation
- **PAN card** — verify PAN number matches entity name
- **GST certificate** — verify GSTIN
- **Certificate of Incorporation / CIN** — verify company name, CIN, registered address
- **Board Resolution** — verify authority of the person signing on behalf of the company
- **JDA / Agreement** — verify the document number, date, parties, extent
- **SPA / GPA** — verify attorney authority, document number, date
- **Layout approval** — verify order number, date, authority
- **Gift Deed** — verify document number, date
- **RERA registration** — verify registration number

Search tips:
```python
# Search by entity name
call('drive_search', service_name='...', query='Sevaganapalli Land Partners')

# Search by document type + project
call('drive_search', service_name='...', query='reconstitution Sevaganapalli')

# Search by specific registration number
call('drive_search', service_name='...', query='SPA 276/2025-26')
```

### 5. Check for Reference Summary / Index Documents

Many DRAAS projects have a master reference document or index spreadsheet that lists all available documents with Drive links. Check for these first — they save significant search time.

Look for:
- `*Master Document Reference Summary*` or `*Reference Summary*` (markdown or Google Doc)
- `*Index of Documents*` (spreadsheet)
- Project-level READMEs

To read a summary markdown file:
```python
# Download via drive_download
call('drive_download', service_name='...', file_id='FILE_ID')
# Then read the downloaded file from /opt/data/
```

### 6. Cross-Verify Each Data Point

Compare each detail from the sale deed against the source document. Flag:

| Item | Source to Check | What to Verify |
|------|----------------|----------------|
| Firm Registration No. | Partnership deed / Registration certificate | Exact match of number |
| PAN | PAN card copy | Entity name + PAN match |
| CIN | Certificate of Incorporation / MCA search | Company name + CIN |
| Registered Address | COI / partnership deed / GST cert | Exact match |
| Authorized Representative | Board resolution / partnership deed | Name, designation, authority |
| Aadhaar | Aadhaar copy / KYC docs | Number format (XXXX XXXX XXXX) |
| JDA Reference | Registered JDA copy | Doc no, date, parties, survey numbers |
| SPA Reference | Registered SPA copy | Doc no, date, authority granted |

### 7. Compile Structured Report

Present in this format:

```
## ✅ Verified — In Order
Each verified item with ✓ marker and source reference.

## 🚩 Red Flags / Concerns
Each flagged issue with:
- Description of the problem
- What the sale deed says vs what source says
- Risk/impact assessment
- Recommended action (escalate to Nishant, fix in document, etc.)

## ⏸️ Ignored / Already Cross-Checked
Items the user said not to worry about, noted for completeness.
```

### 8. Output Rules

- **Do NOT make any changes to the original document** unless explicitly instructed
- Present the summary in the chat — the user wants to review before any action
- Offer to draft a WhatsApp/email message to Nishant or the advocate about red flags

## Red Flags Common in DRAAS Sale Deeds

1. **Same entity appearing twice with different representatives** — e.g., DRA Realty appears as Partner 1 in SLP (represented by Director A) AND as Confirming Party/Developer (represented by Director B). This can raise registration questions about authority consistency.

2. **RERA number is a placeholder** — "[TNRERA REGISTRATION NO. TO BE PROVIDED]" indicates RERA not yet received. The deed should not claim it's a "RERA-registered Project" if registration is pending.

3. **Scope ambiguity** — Is the consideration for the plot only, or does it include construction? Check if the deed mentions "bare residential plot (without any constructed structure)" and whether ₹/sq.ft. rate is consistent with market for land-only vs land+construction.

4. **Blank fields** — Purchaser PAN, RERA number, cheque details, boundary survey numbers marked with "[TO BE PROVIDED]" or "_______"

5. **Gift deed doc numbers mismatch** — Cross-check the gift deed numbers against the actual registered gift deeds

## Verified Against

- Ranka Oasis Plot 65 Sale Deed (Nishant Prakash → Prathyusha Vuppala, 27 Jul 2026) — user-requested party detail verification with 3 red flags identified. Supporting documents cross-checked: Partnership Deed, Reconstitution Deed, SPA, JDA, GST Certificate, Master Reference Summary document.
