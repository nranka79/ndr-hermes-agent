# Invoice PO Re-Linking (Pipeline 516)

When an invoice is filed as "No PO" but should be linked to an existing One Time PO.

## When to use

User says: "This invoice was filed as No PO but it should be under [vendor]'s PO." Or: "Can you link this invoice to the PO?"

## Steps

### 1. Find the Invoice

Search the DRA Invoice Processing pipeline (ID 516):

```
search_leads(pipeline_id=516, query="PI-30.6.26 DC")
```

Use invoice number, vendor name, or amount to narrow.

### 2. Find the PO

Search the DRA PO-WO Issuing pipeline (ID 537) for the vendor:

```
search_leads(pipeline_id=537, query="Design Cafe")
```

Note the lead ID of the matching PO record.

### 3. Update the Invoice

Use `update_lead` with two field changes:

| Field | Identifier | Format | Example |
|-------|-----------|--------|---------|
| PO Type | `cf_invoice_against` | **Plain string** — the dropdown label | `"One Time PO"` |
| PO Number | `cf_po_number1` | `{"id": <po_lead_id>}` — master field | `{"id": 51007081}` |

```json
{
  "cf_invoice_against": "One Time PO",
  "cf_po_number1": {"id": 51007081}
}
```

### 4. Verify

Check draft status. On success, verify the invoice now shows:
- `PO Type: One Time PO`
- `PO Number: <vendor>-<PO name>-<PO number>` (auto-populated from master)
- `Invoiced amount` and `Yet To be invoiced amount` appear (read from PO)
- `Description R` auto-updates to `"<invoice details>-One Time PO <PO reference>"`

### 5. Add Clarifying Note

After re-linking, add a note on the invoice explaining the pro-forma → actual invoice context:

```
add_note(
    lead_id=<invoice_lead_id>,
    text="Here is the actual Tax Invoice received from [Vendor] for the ₹[amount] payment ([milestone description]). This was initially processed using the pro-forma invoice — attaching the final tax invoice for records. This corresponds to PO #[PO_number] ([Vendor], ₹[PO_total])."
)
```

**Why this matters:** The user explicitly requested this note pattern: "here is the actual invoice — we processed the invoice using a pro-forma invoice." Without this note, the connection between the pro-forma (used for processing) and the actual tax invoice (attached for records) is unclear to downstream viewers.

**Check if already attached first:** Before uploading any file, check the invoice's notes via `list_lead_notes()` — someone else (e.g. Prakash) may have already attached the tax invoice. If already present, just add the contextual note.

## Critical Details

### Dropdown value format for `update_lead` vs `create_lead`

| Action | Format | 
|--------|--------|
| `update_lead` for PO Type | **Plain string** — `"One Time PO"` |
| `create_lead` for dropdowns | `{"id": "value", "label": "Value"}` |

`update_lead` accepts the raw label string. `{"id": "One Time PO", "label": "One Time PO"}` WILL FAIL with `"Invalid dropdown value for po type"`.

### Auto-populated fields

Once the PO is linked:
- `Invoiced amount` shows total invoiced so far across all invoices under this PO
- `Yet To be invoiced amount` shows remaining PO balance
- `PO created By` populates from PO record
- `Description R` auto-generates: `"<invoice details>-One Time PO <PO name>-<PO number>"`

These are computed fields — you don't set them manually.

## Example (Jul 2026)

**Invoice:** #53150335 (PI-30.6.26 DC, ₹1,36,573.51, Design Cafe, DRA Projects Pvt Ltd)
**Status:** Filed as "No PO" at "Invoice received" stage
**PO:** #51007081 (728, Design Cafe, ₹3,22,451 One Time PO, Signed & Issued)

**Update:**
```python
update_lead(
    lead_id=53150335,
    field_values={
        "cf_invoice_against": "One Time PO",
        "cf_po_number1": {"id": 51007081}
    }
)
```

**Result:** ✅ PO Type changed, PO Number linked, invoiced amounts auto-populated.
