# Invoice-WO Payment Verification Workflow

Verify an invoice against its associated PO/WO document to determine if the amount is due and which milestone it corresponds to.

## The Workflow

When a user says "check this invoice against the PO/WO and tell me if it's due":

### Step 1: Find the invoice in Kelsa

The user typically provides a Kelsa link. Extract the lead ID from the URL:
- URL pattern: `https://kelsa.io/516/leads?current_item_id=52230402`
- The number after `current_item_id=` is the **lead_id**

If no link is provided, search Pipeline 516 by invoice number or vendor name:
```
search_leads(pipeline_id=516, query="cf_invoice_number:ABC123")
```

### Step 2: Get invoice details

```
get_lead(lead_id=<invoice_lead_id>)
```

Note the following fields:
- `cf_invoice_number` — Invoice number
- `cf_amount` — Invoice amount (number)
- `cf_po_number1` — Master field linking to the PO record (contains `{"id": <po_lead_id>}`)
- Current stage — to understand where in approval pipeline
- `cf_vendor_n` — Vendor name

### Step 3: Find the linked PO/WO record

The PO record is in Pipeline 537 (DRA PO-WO Issuing). Get its details:

```
get_lead(lead_id=<po_lead_id>)
```

Key fields to extract:
- `cf_ponumber` — PO reference number (e.g. "740")
- `cf_jobs` — Scope description
- `cf_po_type` — **"One Time PO"** or milestone-based (critical distinction)
- `cf_total_value_of_order__without_tax_` — Base work value
- `cf_total_amount` — Total including tax
- `cf_advance_to_be_paid` — Advance amount
- `Issued PO-WO` — **S3 URL to the WO document (.docx)**
- `cf_narration` — Payment terms / narration text
## Stepping from Step 3 to the PO content

### Step 3.5: Cross-check project, scope & PO type — before reading the WO

**Do NOT assume the PO is correctly linked to the invoice.** A PO may be for a different project, scope, or vendor. Always cross-check:

| Check | Invoice Field | PO Field | Alarm Signal |
|-------|--------------|----------|-------------|
| **Project** | `cf_description` (or invoice doc text) | `cf_project` | Invoice says "Serenity Hillview", PO says "Ranka Amber" → **wrong PO** |
| **Scope** | Invoice description / line items | `cf_jobs` | Invoice says "compound wall", PO says "barrication" → **wrong PO** |
| **Amount** | `cf_amount` | `cf_total_amount` | Invoice > PO total → **over-invoiced or wrong PO** |
| **PO Type** | Invoice's PO Type field | `cf_po_type` | Invoice says "Recurring PO", PO says "One Time PO" → **mismatch** |
| **Balance** | N/A | `cf_yet_to_be_invoiced_amount` | Negative → invoicing exceeded PO → **over-invoiced** |

**If ANY mismatch:** flag to user immediately. Do NOT proceed to milestone analysis against the wrong PO. Recommend raising a new PO for the correct project/scope.

### Step 3.6: Distinguish .docx vs scanned PDF WOs

The `Issued PO-WO` URL may point to either a .docx or .pdf file. Check the URL extension or download and inspect:

```bash
curl -sL "<s3_url>" -o /tmp/wo_document
file /tmp/wo_document
```

- **.docx** → extract with `python-docx` (paragraphs AND tables)
- **.pdf** → may be scanned (image-based). Convert to image with pymupdf, then OCR with `vision_analyze`:

```python
import pymupdf
doc = pymupdf.open('/tmp/wo_document.pdf')
for page_num in range(len(doc)):
    page = doc[page_num]
    pix = page.get_pixmap(dpi=200)
    pix.save(f'/tmp/wo_document_p{page_num+1}.png')
# Then call vision_analyze(image_url='/tmp/wo_document_p1.png',
#   question="Extract all text — especially payment terms, milestones, and amounts")
```

## Step 4: Extract payment details from the WO

### For .docx files:

```bash
curl -sL "<s3_url>" -o /tmp/wo_document.docx
```

Then extract text using python-docx:

```python
from docx import Document
doc = Document('/tmp/wo_document.docx')

# Extract paragraphs (main body text)
for para in doc.paragraphs:
    if para.text.strip():
        print(para.text)

# Extract tables (payment schedules, milestones live here)
for table in doc.tables:
    for row in table.rows:
        cells = [cell.text.strip() for cell in row.cells]
        print(cells)
```

**⚠️ Payment details are in tables, not paragraphs.** The word "Payment Details:" may appear as a section heading in paragraphs, but the actual amounts, milestones, and breakdowns are in one or more tables. Always check both `doc.paragraphs` AND `doc.tables`.

If `python-docx` is not installed, install it with `uv pip install python-docx` then run via `uv run python3 -c "..."`.

### Step 5: Analyze payment structure

**Case A: One Time PO**

The WO has no milestones — the entire scope is a single payment. The table typically shows:

| Item | Amount |
|------|--------|
| Work Value | ₹X |
| GST @ 18% | ₹Y |
| TDS @ 10% | -₹Z |
| **Net Payable** | **₹X+Y-Z** |

**Verification:** Compare the invoice amount against the Net Payable. If they match, the amount is correct. Since it's a one-time payment, ask Anbu to confirm all deliverables are complete before releasing payment.

**Case B: Milestone-based PO**

The WO contains a payment schedule table with multiple milestones. Each milestone has:
- Milestone number / description (e.g. "1st Running Bill", "Completion of Foundation")
- Percentage or amount
- Cumulative total

**Verification:** Identify which milestone the invoice corresponds to. The invoice description (e.g. "Final Bill", "1st RA Bill") or the amount should match a specific milestone.

### Step 6: Draft the verification note

Since `add_note` often returns "Internal error" (Kelsa server-side bug, write operations unreliable), provide the user with a ready-to-paste note. Include:

1. **Invoice identification** — number, amount, vendor
2. **WO reference** — PO number, WO date
3. **Payment structure finding** — One Time PO vs Milestone-based
4. **Amount match check** — Does invoice match WO net payable?
5. **Scope/project cross-check result** — matched or flagged
6. **Clear question for Anbu** — Confirm deliverables and which milestone

**Template — One Time PO (all matched):**
```
@[Anbarasan](682) — This invoice ({number}, ₹{amount}) is against PO #{po_number} ({vendor}, {project}).
I reviewed the WO dated {wo_date} — it is a One Time PO, not a milestone-based payment.
The scope says "{scope}" with a net payable of ₹{net_payable}
(₹{base} + {gst_pct}% GST - {tds_pct}% TDS) which matches the invoice.
Please confirm: Is this the complete final bill? Have all deliverables
as per the WO been completed and accepted before we release payment?
```

**Template for Milestone-based PO (amount mismatch):**
```
@[Anbarasan](682) — This invoice ({number}, ₹{amount}) is against PO #{po_number} ({vendor}, {project}).
The WO dated {wo_date} lists these milestones:
  {milestone_list}
The invoice amount ₹{amount} does not match any single milestone amount.
Please clarify: which milestone is this payment against, and is the amount correct?
```

**Template — Wrong PO / Project-Scope Mismatch (do NOT proceed with payment):**
```
@[Anbarasan](682) — I reviewed Invoice #{number} (₹{amount}, {vendor}) against PO #{po_number}.

⚠️ ISSUES FOUND:
• Project: Invoice says "{invoice_project}", PO says "{po_project}" — mismatch
• Scope: Invoice says "{invoice_scope}", PO says "{po_scope}" — mismatch
• Amount: Invoice ₹{amount} vs PO total ₹{po_amount} — exceeds PO value
• PO Type: Invoice says "{invoice_po_type}", PO record says "{po_type}" — mismatch

This invoice should NOT be paid against this PO. Please raise a new PO for {invoice_project} — {invoice_scope} work with the correct budget head, then relink this invoice.
```

### Step 6.5: How to present the full analysis to the user

When reporting results, lead with the verdict first, then details:

1. **Verdict** — "This looks in order" / "Amount matches" / "⚠️ Mismatch found — do not pay"
2. **Red flags** (if any) — bullet list of what's wrong
3. **Key numbers** — invoice amount, PO total, net payable, milestones
4. **Recommendation** — what to do next

### Step 7: Try posting the note

```
add_note(lead_id=<invoice_lead_id>, text="<note_text>")
```

If it returns "Internal error", tell the user Kelsa notes are failing and give them the ready-to-paste text to manually paste on the invoice lead page.

## Key Field References

### Invoice Pipeline 516 — PO/WO Verification Fields

| Field Identifier | Used For |
|-----------------|----------|
| `cf_po_number1` | Master field → PO record ID |
| `cf_amount` | Invoice amount to verify |
| `cf_invoiced_amount` | Amount invoiced against PO |
| `cf_yet_to_be_invoiced_amount` | Balance remaining |
| `cf_description` | Work done description |

### PO Pipeline 537 — Key Fields

| Field Identifier | Used For |
|-----------------|----------|
| `cf_po_type` | "One Time PO" or milestone-based |
| `cf_issued_po_wo` | S3 URL to .docx document |
| `cf_total_value_of_order__without_tax_` | Base amount |
| `cf_total_tax` | Tax component |
| `cf_total_amount` | Full PO value |
| `cf_advance_to_be_paid` | Advance amount |
| `cf_narration` | Payment terms text |
| `cf_jobs` | Scope description |

## Common Patterns Found

- **"One Time PO" with "Final Bill" scope** — A single closing payment. No milestones exist. The invoiced amount should equal the entire net payable.
- **"One Time PO" with no "Final Bill" designation** — Same pattern: one-off task, single payment, no milestones.
- **Milestone-based POs** — Typically for construction/execution vendors (civil contractors, MEP). Has a payment schedule table in the WO with % or ₹ per milestone.
- **TDS @ 10%** — Standard for service contracts (professional fees, consulting). TDS deducted at source.
- **GST @ 18%** — Standard IGST for inter-state or CGST+SGST intra-state services.
- **S3 .docx URL handling** — The URL in `Issued PO-WO` is pre-signed and time-limited. If expired, re-read `get_lead()` for a fresh URL.
