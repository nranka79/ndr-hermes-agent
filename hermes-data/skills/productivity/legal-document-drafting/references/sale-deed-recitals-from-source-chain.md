# Sale Deed Recitals — Building the WHEREAS Section from Source Chain Documents

## When to Use This

The user asks you to draft or update a **sale deed** where the VENDOR acquired title through one or more **prior source documents** (earlier sale deeds, agreements of sale, GPA, partition deeds, court decrees, settlement deeds). You need to:

1. Find the source chain documents (often scanned PDFs in Drive)
2. Extract the recitals from each source document
3. Build a complete WHEREAS section that accurately traces the VENDOR's title
4. Update the Google Doc template

## Workflow

### Step 1: Identify the Source Chain

From the transaction brief or existing draft, identify:
- The **VENDOR** and their title to the property
- The **source documents** through which they acquired it
- The **survey numbers** and **extents** involved

Key questions to answer:
- Did the VENDOR buy via **Sale Deed**, **Agreement of Sale**, **GPA**, **Partition Deed**, or **Court Decree**?
- Are the source documents in Google Drive folders organized by survey number?
- What are the registration details (date, document number, SRO) of each source document?

### Step 2: Locate Source Documents in Drive

```python
from tools.gws_skill_bridge import call

# Search by folder ID (if user shared a folder link)
result = call("drive_search", service_name="google-draas",
    query="", raw_query="'<FOLDER_ID>' in parents",
    max=50)

# Search by name
result = call("drive_search", service_name="google-draas",
    query="", raw_query="name contains 'Nagendra' and mimeType='application/pdf'",
    max=30)
```

**Pitfall:** The bridge's `drive_search` maps kwargs to `SimpleNamespace` — the skill function uses `args.query`, `args.raw_query`, and `args.max`. Always pass `query=""` (falsy string) AND `raw_query="..."`. If you only pass one, the function crashes with `AttributeError`. See `google-workspace/references/gws-bridge-pitfalls.md`.

### Step 3: Download the Source Documents

```python
call("drive_download", service_name="google-draas",
    file_id="<FILE_ID>",
    output="/tmp/source_doc.pdf")
```

**Pitfall:** The bridge's `drive_download` requires an `output` parameter — without it, `args.output` access crashes with AttributeError.

### Step 4: OCR Bilingual Documents

For scanned Indian legal documents (typically bilingual English + Kannada/Tamil/Telugu):

```bash
# 1. Convert PDF to images
pdftoppm -png -r 300 "document.pdf" /tmp/ocr/pages

# 2. Download Kannada language pack if needed
curl -sL "https://github.com/tesseract-ocr/tessdata/raw/main/kan.traineddata" -o /tmp/kan.traineddata
cp /usr/share/tesseract-ocr/5/tessdata/eng.traineddata /tmp/

# 3. OCR with bilingual language pack
export TESSDATA_PREFIX=/tmp
for f in /tmp/ocr/pages*.png; do
    tesseract "$f" stdout -l kan+eng 2>/dev/null >> output.txt
done
```

See `ocr-and-documents/references/tesseract-bulk-ocr.md` for detailed OCR guidance including pitfalls.

### Step 5: Extract Recitals from OCR Output

From the OCR'd text, extract the following **for each source document**:

| Field | What to Extract |
|-------|----------------|
| **Parties** | VENDOR (seller) and VENDEE (buyer/C.R. Nagendra) names, relationship, addresses |
| **Property** | Survey numbers (old + new), extent (Acres-Guntas), village, hobli, taluk, district |
| **Consideration** | Total sale consideration, advance amounts paid, payment mode (DD/cheque/cash) |
| **Registration** | Date, Document No., CD No., SRO, Book No. |
| **Title chain** | How the VENDOR'S predecessor acquired the property (grant orders, earlier mutations) |
| **Boundaries** | East/West/North/South boundary descriptions |
| **Nature** | Absolute Sale Deed, Agreement of Sale (with/without possession), GPA |

### Step 6: Build the WHEREAS Recitals

Construct a numbered recital sequence that tells the complete title story:

```
WHEREAS:

A. The VENDOR acquired the Schedule Property vide a [type of document] dated [date], registered as Doc No. [number], executed by [predecessor] in favour of the VENDOR.

B. Brief description of how the predecessor held title (prior chain — from the source doc's recitals).

C. The VENDEE [purchasing entity] is desirous of purchasing the Schedule Property.

D. The VENDOR has agreed to sell, and the VENDEE has agreed to purchase, for a total sale consideration of Rs. ______.

E. Encumbrance disclosure (mortgages, liens, or declaration that property is free from encumbrances).

F. Agreement to sell absolutely.
```

**For multiple survey numbers acquired through different documents:** Create separate Recital sub-sections (A1, A2) or a consolidated Recital A that references the full title history.

**For multiple survey numbers acquired through different source deeds but same firm/entity:** Use lettered subsections (A, B, C) where each source deed gets its own title chain section, followed by a Partition/Consolidation section (C) that bridges to the current VENDOR's title. See `references/karnataka-sale-deed-byadarahalli-pattern.md` §9 for the full pattern.

**Partnership → Partition → Individual Sale recital pattern:**
When the VENDOR acquired title through a dissolved partnership firm, the recitals must follow a three-part structure:

1. **Recital A/B — Firm's acquisition:** Full title chain from original grant → ... → registered sale deed in favour of the partnership firm (represented by the VENDOR as partner)
2. **Recital C — Partition Deed:** The firm's dissolution and allocation of the specific survey numbers to the VENDOR, with registration details
3. **Recital D — Agreement to Sell:** Current sale arrangement

**Acknowledging a partner's prior funding:**
When a non-vendor partner originally funded the acquisition, add a separate recital clause (not part of the consideration):

> "The VENDOR acknowledges that the funds for the original acquisition of the Schedule Properties by M/s. [FIRM NAME] were advanced by the erstwhile partner [NAME], who paid a sum of Rs. [AMOUNT] towards the purchase of the Schedule Properties, and the said amount stands duly settled and accounted for under the said Partition Cum Settlement Deed."

This is a **recital of fact** (historical source of funds), not a consideration clause. Do not place it in the operative part of the deed.

### Step 7: Update the Google Doc

Use the Docs API's `batchUpdate` with `replaceAllText` to update placeholder text:

```python
from tools.gws_auth import build_service
service = build_service('docs', 'v1', service_name='google-draas')

requests = [
    {
        'replaceAllText': {
            'containsText': {'text': 'OLD_TEXT', 'matchCase': False},
            'replaceText': 'NEW_TEXT'
        }
    },
    # Multiple replacements batched in one call
]
service.documents().batchUpdate(
    documentId=doc_id, body={'requests': requests}
).execute()

# Verify
from tools.gws_skill_bridge import call
result = call("docs_get", doc_id=doc_id, service_name="google-draas")
if "NEW_TEXT" in result:
    print("✅ Verified")
```

**Pitfall:** `replaceAllText` returns `occurrencesChanged: 0` silently if the search text doesn't exist — no error raised. Always verify by reading the doc back.

### Step 8: Handle the Schedule of Property

The Schedule section must include for each survey number:
- Survey number (old and new)
- Extent in Acres-Guntas
- Boundary descriptions (East/West/North/South)
- Village, Hobli, Taluk, District

**For missing boundaries:** Note in the response which boundaries need manual filling and from which source document they can be obtained.

### Step 9: Flag Remaining Blanks

At the end, provide a clear table of what still needs manual filling:

| Item | Required Info | Source |
|------|-------------|--------|
| Sy. ___ boundaries | E/W/N/S boundaries | (identify missing doc) |
| Sale consideration | Amount in words & figures | Transaction agreement |
| Date of execution | Day & Month | Transaction date |
| Vendor's father's name & Aadhaar | For party description | Vendor's KYC |
| Witness details | 2 witnesses | Execution |

## Example Summary Format

For the user, present the extracted recitals as:

---

**Source Document 1: [Type] dtd [Date] — Sy. [Number]**

Registered: Doc No. [...] | CD No. [...] | Dt. [Date] at [SRO]

**Parties:** [Vendor Name(s)] → [Purchaser Name]

**Property:** Sy. Old [X], New [Y], [Village] — [Extent] Ac [Guntas]

**Consideration:** ₹ [Amount]

**Title Chain (from recitals):**
- [Predecessor] acquired per [order/document] dated [date]
- [Chain events] → [VENDOR acquired as described]

---

## Common Pitfalls

- **Total extent inconsistency:** When adding extents from different source docs, verify the total. A contradiction between documents (e.g., Recital says 5Ac 18Gu total but individual items add to 7Ac 18Gu) must be flagged.
- **Registration date vs. execution date:** Registered documents have a presentation/execution date AND a registration date (which may be months later). Use the execution date for the Recital, and note the registration date separately.
- **Empty folders:** Survey-number folders in Drive may be empty. The actual source documents might be elsewhere or yet to be uploaded. Tell the user explicitly rather than silently skipping.
- **Bilingual documents (Kannada+English):** The English portions contain the formal recitals; use `tesseract -l kan+eng` for best results. The agent's own language model can read and translate Kannada OCR output for survey numbers, extents, and party names.

## Trigger Phrases

- "extract the recitals from this document"
- "find the sale deed in the name of [person]"
- "check survey nos and find the sale deed"
- "generate new sale deed draft between [A] and [B]"
- "build the WHEREAS section"
