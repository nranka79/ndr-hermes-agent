# Sale Deed — Recital Construction for DRAAS

## Source Documents & Where to Find Recitals

When drafting a Sale Deed for DRAAS (buyer → DRA Realty Pvt Ltd), the recital chain comes from these source documents:

| Source Document | What It Provides |
|---|---|
| **Deed of Partnership** (R3N / DRA KAAJ etc.) | Recitals about who originally held title, how lands were partitioned, the consideration structure |
| **Deed of Reconstitution** (DRA KAAJ PALYA NAGENDRA etc.) | Schedule B with survey numbers, exact extent, and base valuation for C.R. Nagendra lands |
| **Partition Cum Settlement Deed** (SRJ-1-10373-2023-24) | The actual title transfer from Satvik Developers to individual partners |
| **Mortgage Deed** (19.02.2024) | Encumbrance disclosure — mortgage from vendor to Nishant Ranka |
| **GPA / Agreement of Sale** (11.01.2023) | For Sy. No. 223 — provides boundaries and extent if available |

## Standard Recital Structure (6-part)

When the vendor IS the confirming party (Variant A — CP sells directly), use
the 6-part structure below. When the confirming party merely consents and the
original owners sell directly (Variant B), use the 9-part lettered recital
structure documented in `references/confirming-party-sale-deed.md`.

### Recital A — Vendor's ownership
> "The VENDOR is the sole and absolute owner of, and in possession of, the agricultural lands bearing Survey Nos. [X, Y, Z], total measuring [N] Acres [M] Guntas..."
### Recital B — Source of title (chain from the Partnership)

> "The VENDOR was a partner of M/s. [Firm Name], a partnership firm. The said firm was dissolved and its assets were partitioned amongst its erstwhile partners vide a Registered Partition Cum Settlement Deed dated [date], registered as Document No. [number]. Under the said Partition Deed, the VENDOR was allocated inter alia the immovable agricultural lands comprising Survey Nos. [X, Y, Z]..."

**Key detail**: Always mention the firm name (e.g. M/s. Satvik Developers), the dissolution, and the Partition Deed registration number.

### Recital B2 — Third-party funding acknowledgment (Partnership-dissolution deeds)

When the original acquisition was funded by a **third party who was not the vendor** (e.g., the other partner of a dissolved firm funded the purchase during the partnership period), add a separate recital:

> "The VENDOR acknowledges that the funds for the original acquisition of the Schedule Properties by M/s. [Firm Name] were advanced by the erstwhile partner [Third Party Name], who paid a sum of Rs. [amount] towards the purchase of the Schedule Properties, and the said amount stands duly settled and accounted for under the said Partition Cum Settlement Deed."

**Use when:** The user explicitly tells you about a third-party payment and asks to capture it. Only add if instructed — this is a factual statement, not a legal covenant. The amount and party name come from the user, not from source docs.

### Recital C — Vendee's interest
> "The VENDEE is a company engaged in the business of real estate acquisition, development, and monetization and is desirous of purchasing the Schedule Property from the VENDOR."

### Recital D — Agreement to sell & consideration
> "The VENDOR has agreed to sell, and the VENDEE has agreed to purchase, the Schedule Property for a total sale consideration of Rs. [amount]..."

### Recital E — Encumbrance disclosure
> "The VENDOR has confirmed that the Schedule Property is free from all encumbrances... save and except the Mortgage Deed dated [date] executed by the VENDOR in favour of [mortgagee] which mortgage shall be simultaneously discharged and released upon execution of this Deed."

### Recital F — General agreement
> "The VENDOR has agreed to sell absolutely to the VENDEE the Schedule Property for valid and proper sale consideration..."

## Handling Extent Discrepancies

Source documents often disagree on exact extents. Typical inconsistency:

- **Partnership Deed Recital**: Total of Sy. 221/2 + 176/2 + 223 = 5 acres 18 guntas
- **Deed of Reconstitution Schedule B**: Sy. 223 listed separately as 2 acres 00 guntas
- **Mathematical check**: Sy. 221/2 (3Ac 38Gu) + Sy. 176/2 (1Ac 20Gu) = 5Ac 18Gu exactly. Adding Sy. 223 (2Ac) gives 7Ac 18Gu.

**Resolution approach**: 
1. The Partnership Deed's "5 acres 18 guntas total" likely refers to only 221/2 + 176/2
2. Sy. 223 is a separate/additional parcel listed in the same Partnership Deed as part of the C.R. Nagendra allocation
3. Use the Reconstitution Deed Schedule B as the authoritative source for individual extent
4. Flag the total in the Schedule header as needing legal verification

## Workflow: Building a Sale Deed from Scratch

### Step 1: Gather source documents
Search Drive for:
- `name contains '[Firm]' and name contains 'Partnership'` — find the Partnership/Reconstitution Deed
- `name contains 'Partition' and name contains 'Satvik'` — the title chain document
- Check the `Byadarahalli Legal files` folder and its subfolders

### Step 2: Extract recitals from Partnership Deed
The Partnership Deed's WHEREAS section contains:
- Recital C (for Nagendra-style): Who got what land under the Partition Deed
- Recital D (for Nagendra-style): The consideration/funding arrangement

### Step 3: Check Reconstitution Deed for Schedule B
The Schedule B of the Reconstitution Deed (if one exists) gives:
- Exact survey numbers with old Sy. Nos.
- Exact extent per item (in acres and guntas)
- Base valuation / Mutually Agreed Value

### Step 4: Cross-reference survey number folders
Check the survey-number-specific folders under "Byadarahalli Legal files":
- They may be **empty** — the actual scanned documents (Mortgage Deed, GPA, original Sale Deeds) may be stored elsewhere
- If empty, note which extents/boundaries still need manual filling

### Step 5: Draft the document
Create the Sale Deed as a Google Doc using the standard structure above.

### Step 6: Update via batchUpdate
Use `gws_auth.build_service('docs', 'v1', service_name='google-draas')` with `batchUpdate`/`replaceAllText` to fill in placeholders:

```python
from tools.gws_auth import build_service
service = build_service('docs', 'v1', service_name='google-draas')
requests = [
    {
        'replaceAllText': {
            'containsText': {'text': 'PLACEHOLDER_TEXT', 'matchCase': False},
            'replaceText': 'Actual Value'
        }
    },
]
service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
```

### Step 7: Verify
Read back the doc with `gws_skill_bridge.call('docs_get', ...)` and check that replacements landed.

## Drive Search Parameters

When searching for source documents, use the correct bridge parameters:

```python
# Correct — pass the query in query=, raw_query is a boolean flag
call('drive_search', service_name='google-draas',
     query="'PARENT_FOLDER_ID' in parents", raw_query=True, max=50)

# For text search across all Drive
call('drive_search', service_name='google-draas',
     query="name contains 'Partnership' and name contains 'Nagendra'", raw_query=False, max=20)

# For metadata lookup
call('drive_get', service_name='google-draas', file_id='FOLDER_ID')
```

Note: `raw_query` is a **boolean flag** that tells the wrapper to use the query string as-is rather than wrapping it in `fullText contains`. Do NOT pass the query text as `raw_query` — that results in an empty query and returns unfiltered results.

## Common Issues

- **Empty survey folders**: Sy. 221/2 and Sy. 223 folders under "Byadarahalli Legal files" exist but contain no source documents. The actual recital docs (Mortgage Deed, GPA) need to be uploaded separately.
- **Extent totals that don't add up**: When three survey numbers = 5Ac 18Gu in one doc but the sum of two items already reaches that total, Sy. 223 is likely a separate additional parcel.
- **Boundaries for Sy. 223**: Not available in source docs found in Drive — needs manual reference to the GPA/Agreement Deed.
- **Ownership**: The "Byadarahalli Legal files" folder is owned by `presales.blr@draas.com` — documents searched via `psingh@draas.com`'s token may have scope limitations.
