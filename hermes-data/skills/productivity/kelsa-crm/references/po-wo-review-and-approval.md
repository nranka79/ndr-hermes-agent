# PO-WO Review and Approval Workflow

A repeatable pattern when Nishant asks: "Check the work order just posted in Kelsa" or "Review the PO/WO against these conditions."

## The workflow

### 1. Find the record

Search the DRA PO-WO Issuing pipeline (ID: 537) for the vendor name or project name. The user may describe it by who posted it ("Bharat just posted") or what it's for ("Joys AI robocalling").

```python
search_leads(pipeline_id=537, query="<vendor or keyword>")
```

### 2. Read the full record

`get_lead(lead_id)` shows:
- Stage, assignee, followers
- All field values
- Attached quote (signed URL to S3 PDF)
- Issued PO-WO (signed document)
- Outstanding prerequisites

### 3. Check the signed PO-WO document

The `Issued PO-WO` field (cf_issued_po_wo) is a PDF attachment accessible via signed S3 URL. Download and OCR it — most signed POs are scanned images, not text PDFs.

```bash
# pdfimages to extract pages as PNG
pdftoppm -png -r 200 signed_po.pdf /tmp/po-page
# Then OCR each page with vision_analyze or local tesseract
```

### 4. Verify conditions against the document

Nishant often wants these checked:
- **Number/call ownership** — whose name is the number registered in?
- **Termination clause** — can they cut off after a quarter?
- **Conversation flow basis** — are submitted planning docs the basis?
- **Accents/voice quality** — are specific accent/voice requirements mentioned?
- **Entity name** — Is the correct company entity used (e.g. DRA Thindlu Land Partners vs DRA Realty)?

### 5. Add a single comprehensive note on Kelsa

**Do NOT add separate notes per item.** Collate ALL findings into ONE note with the responsible person @-mentioned:

```python
add_note(lead_id=<id>, text='''@[Bharat H](<user_id>), items from Nishant's review to resolve:

1. [MISSING ITEM] — description of what's not in the WO
2. [CLARIFICATION] — what needs to change / what's incorrect
3. [QUESTION] — specific ask to the vendor'''
)
```

**Structure each item with two parts:**
- What's missing or wrong (quote the document gap)
- What the user wants instead (the specific amendment)

**When user names multiple conditions**, check them ALL in one pass through the document and include ALL findings in a single note. Do NOT iterate finding-by-finding.

**Distinguish between:** items that need to be *incorporated in the WO itself* (e.g. accent/voice clauses) vs items that need to be *checked/confirmed separately* (e.g. whether the vendor can deliver a specific accent). Label each item accordingly — `[INCORPORATE IN WO]` vs `[CONFIRM WITH VENDOR]`.

### 6. Stage approval flow

The PO-WO pipeline has these stages:
1. **PO-WO Created** (current after creation)
2. **HoD Approved** — review prerequisite "Approve PO by HoD?"
3. **Chairman Approved** — review prerequisite "Approve PO-WO"
4. **Signed & Issued**

Nishant saying "approve the PO/WO" typically means move it to Chairman Approved (he is the chairman). But the HoD review prerequisite must be completed first — it's a manual action/review that moves the record.

Prerequisites between stages:
- `data_entry: Collect required information` at PO-WO Created stage — marks that all required fields are filled
- `review: Approve PO by HoD?` at HoD Approved — HoD must manually approve
- `review: Approve PO-WO` at Chairman Approved — Chairman must approve

### 6.5. Verify requested items arrived BEFORE approving (approval gate)

When Nishant says *"I commented last week asking for X — I need to approve it now"*, do NOT complete the approval task until you have confirmed the vendor actually responded:

1. `list_lead_notes(lead_id)` — check for the vendor's replies AFTER Nishant's comment date.
2. Confirm the specific asks were met: competing quotes attached (note shows `[attachment]` lines), clarification questions answered point-by-point.
3. Only then complete the task — and cite what arrived in the `note_text` of the approval (quotes attached, clarifications answered) so the approval is self-documenting.
4. If the asks were NOT met, report to the user instead of approving (e.g. "Anbu has attached only one quote, not two — hold?").

Verified 2026-08-14 (PO-WO #759 Vardhan): Anbu attached Alpha + Marabou quotes and answered all 6 BOQ clarifications the same day; approval proceeded with those facts in the note.

### 6.6. complete_task can advance MULTIPLE stages in one shot

Completing a review prerequisite (`complete_task`) does not just unlock the next stage — **automations may cascade it forward two or more stages**. Verified 2026-08-14: completing "Approve PO-WO" (Chairman review) on a record at HoD Approved advanced it through **Chairman Approved AND Signed & Issued** in one call (event log showed two `Stage changed to` entries).

Implications:
- After any `complete_task`, re-read with `get_lead` — don't assume the record stopped at the next stage.
- A **data_entry prerequisite may remain outstanding at the final stage** (e.g. "Issue PO" at Signed & Issued) even though the record is there — that is the issuer's step (assignee usually auto-set to the creator), not a blocker for the approval itself. Say so in your report.
- This makes the `perform_manual_action`-vs-`complete_task` distinction (below) less critical in practice for review tasks: `complete_task` on a review task does advance the record through the chained review stages automatically.

### 7. Conditional approval (flag-and-advance)

A common pattern: Nishant says *"Go ahead and approve, but first add these conditions as notes for Bharat to resolve."*

**The workflow:**
1. Add the comprehensive note (Step 5) with all conditions listed
2. After the note is on the record, advance to the approval stage
3. Do NOT wait for the conditions to be resolved — the note IS the resolution for now
4. If the record has a `review: Approve PO by HoD?` prerequisite blocking advancement:
   - Check what stage the record is currently in via `get_lead`
   - If at "PO-WO Created" and HoD approval is needed first, tell the user the HoD prerequisite blocks Chairman approval — don't attempt to bypass
   - If the user confirms "go ahead", complete the HoD review prerequisite via `perform_manual_action`, then advance to Chairman Approved

**Key principle:** The note documents the conditions. The advancement is a separate action. The user explicitly says "go ahead and approve" — don't hold back because of unaddressed notes.

## Pitfalls

- **Signed documents are scanned images** — always use OCR (pdftoppm + vision_analyze), not pdftotext. They will have zero extractable text.
- **Stage IDs are not shown in get_pipeline** — the output shows slug names (st_po_wo_created, st_hod_approved, etc.) but move_stage needs numeric IDs. Check the lead for the current stage slug and reference transitions.
- **Review prerequisites** are satisfied via `perform_manual_action(lead_id, prerequisite_id)`, not `complete_task`. Data_entry prerequisites use `complete_task`.
- **If the vendor agreement is already signed** but the record is still at "PO-WO Created", the document was attached at creation. The stages are still locked by prerequisites — the record won't advance automatically.
- **Check ALL conditions in one pass through the document.** The user often lists 4-6 conditions in a single voice message. Do not read the document once per condition — OCR the entire document once, then check all conditions against the extracted text. Report all findings in one note, not iteratively.
- **Distinguish stage-advancement actions from note-adding actions.** `add_note` does NOT satisfy review prerequisites. `perform_manual_action` does. If the user says "approve", check what's blocking stage advancement — it's usually a review prerequisite, not a missing note.
