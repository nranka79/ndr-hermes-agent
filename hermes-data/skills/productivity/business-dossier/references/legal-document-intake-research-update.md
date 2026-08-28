# Legal Document Intake & Research Note Update

Multi-step workflow for processing a batch of legal documents received via Telegram/file upload, filing them on Drive, and updating an existing research note with multi-agent analysis.

## When to Use

- User uploads multiple legal documents (court orders, letters, brief notes, ownership tables) and asks you to "file them and update the research note"
- User has an existing research/briefing note on a legal matter and new documents need to be integrated
- Documents arrive via Telegram file upload (document_cache) and need to be checked against existing Drive contents before filing

## Workflow

### Phase 1: Document Inventory & Duplicate Check

**Always start here** — do NOT upload anything to Drive before checking for duplicates.

1. **Inventory all incoming files** — check both document_cache and image_cache:
   ```bash
   ls -la /data/hermes/document_cache/
   ls -la /data/hermes/image_cache/
   ```

2. **Search Drive for existing documents on the same matter** to detect duplicates:
   ```python
   from tools.gws_skill_bridge import call
   result = call("drive_search", service_name="google-draas",
       query="Vani Vilas", raw_query=False, max=50)
   ```

3. **Check the matter's folder structure** — identify existing subfolders:
   ```python
   result = call("drive_search", service_name="google-draas",
       query="mimeType='application/vnd.google-apps.folder' and '<parent-id>' in parents",
       raw_query=True, max=20)
   ```

4. **For each incoming file, read its content** (pdftotext or vision_analyze) and compare against what's already on Drive:
   - Same document name variant → duplicate, skip uploading
   - Different content → new document, proceed to Phase 2

### Phase 2: Rename & Upload to TMP

**Hard rule (Nishant):** Every new file goes to TMP folder first before being moved to its final location.

1. **Naming convention:** `YYYYMMDD_CaseName_DocumentType_Description.pdf`
   - Date from the document itself (court order date, letter date)
   - Case abbreviation (e.g., `ComOS13-2019`)
   - Application/IA number if applicable
   - Brief description of what the document IS (not its filename)
   - Example: `20260406_ComOS13-2019_IA58_Order_Attachment_Rejected.pdf`

2. **Upload to TMP folder:**
   ```python
   result = call("drive_upload", service_name="google-draas",
       path="/data/hermes/document_cache/doc_<hash>_<original_name>.pdf",
       parent="<TMP_FOLDER_ID>",
       name="YYYYMMDD_CaseName_Description.pdf",
       mime_type="application/pdf")
   ```

3. **TMP folder ID** for Nishant's ndr@draas.com: `18p74II2uL32sNDzDDwXzmlOUdJJOTmE-`

### Phase 3: Move to Appropriate Subfolder

Move each file from TMP to its correct subfolder in the matter's folder hierarchy. Typical subfolders for legal cases:

| Document Type | Drive Subfolder |
|--------------|-----------------|
| Court orders, IA orders | `Legal Data > Enforcement Suit` |
| Correspondence, letters, settlement docs | `Transaction Documents` |
| Deeds, mortgages, title docs | `Property Documents` |
| Analysis, briefing notes, research | `NDR Notes` |
| JDA, Supplementary Agreements | `JDA` |
| Sanction Plans, NOCs, OC | `Sanction Plans and NOCs` |

Use Drive API directly (not the bridge) for moving:
```python
from tools.gws_auth import build_service
service = build_service("drive", "v3", service_name="google-draas")
service.files().update(
    fileId=file_id,
    addParents=new_parent_id,
    removeParents=old_parent_id,
    fields="id, parents, name"
).execute()
```

### Phase 3a: Also Move Existing Misplaced Docs

If documents from a prior session were filed at the ROOT level of the matter folder (not in subfolders), move them to their correct subfolders. Common pattern: previous session agent files everything at root because they didn't know the subfolder structure.

### Phase 3b: Address Extraction from Court Filing Screen Photos

A specialised sub-phase: after filing documents, the user may show screen photos of court filing affidavits that contain landowner addresses. Extract and cross-reference these.

**When this happens:**
- User sends a photo of their laptop/desktop screen showing a document open in a browser/PDF viewer
- The document is a court filing affidavit listing Defendants with their name, age, relationship, and address
- User wants addresses to share with a mediator/MLA/VIP who will help facilitate settlement discussions

**Workflow:**

1. **Run vision_analyze on the photo:**
   ```python
   vision_analyze(image_url="/data/hermes/image_cache/img_<hash>.jpg",
       question="Extract ALL text — full names, ages, parentage, addresses")
   ```

2. **Parse the extracted text** — court filing affidavits use a standard format:
   - Item number (4., 5., 6., etc.)
   - Name in ALL CAPS or bold
   - Age: "Aged XX years"
   - Relationship: "W/o", "S/o", "D/o" followed by name
   - Address: Full address with landmarks, area, taluk, pin code
   - "And also at;" — secondary address (alternative residence)
   
3. **Cross-reference with ownership table** — match the court filing items to your ownership data by name

4. **Check jurisdiction** — note whether each address falls within the relevant jurisdiction (e.g., Yelahanka, Bengaluru North)

5. **Note family relationships for context** — in this case, all 5 landowners (Sunanda, Ravi, Malathi, Chethana, Nandini) were siblings — children of Late G.V. Veerasetty. This changes the settlement dynamic from "5 separate parties" to "one family"

6. **Update the research note** with a new "Owner Addresses" section

**Multiple photos needed:** Court filing affidavits are multi-page. The photo can only capture what's on screen. Tell the user: "If you scroll to show items [range], I can grab those addresses too."

**Key details to extract per landowner:**

| Field | Example |
|-------|---------|
| Item # | 4 |
| Name | Sunanda Vani |
| Age | 73 years |
| Relationship | W/o Late Mr. G.V. Veerasetty |
| Primary Address | Flat C-301, Vani Garden, No.74, Near CRPF Gate, Puttenahalli, Yelahanka Hobli & Taluk, Bengaluru-560 064 |
| Secondary Address | — |
| Jurisdiction | ✅ Yelahanka |

**Pitfalls:**
- Screen photos have glare, reflection, moiré patterns — text may be partially obscured
- The document may be scrolled — you only see what's on screen at that moment
- The relationship field shows family connections — use this to identify siblings vs spouses
- The "And also at" field means the person has a second residence — important for summons/service of notice
- Item numbers in the court filing may not be the same as your ownership table numbering (court starts from D4 which is item 4 in their array, but your table may have different numbering)

### Phase 4: Multi-Agent Parallel Document Analysis

**Use `delegate_task`** to analyze each document in parallel. Each agent gets:
- The full text of one document (pre-extracted via pdftotext or vision_analyze)
- Specific analysis questions tailored to the document type
- The context of the overall matter

**Task breakdown pattern (3 parallel tasks max):**

```
Task 1: Analyze court order → extract: what was ordered, who filed it, legal reasoning, strategic implications
Task 2: Analyze ownership table → structured ownership breakdown per party
Task 3: Analyze letter/agreement → extract: purpose, parties, terms, expiry, annexures
```

**Pass all extracted text in the context — don't make the subagent re-read the file.** The subagent has no direct Drive or file access (leaf agent).

### Phase 5: Compile Multi-Agent Findings into Updated Research Note

1. **Download existing research note from Drive:**
   ```python
   call("drive_download", service_name="google-draas",
       file_id="<existing-note-id>", output="/tmp/existing_note.html")
   ```

2. **Synthesize all 3 agent findings** into a single comprehensive HTML document. The HTML should include:
   - **Updated case status table** — all proceedings with latest orders
   - **Crux of the dispute** — 1-2 paragraph summary for quick reading
   - **Mortgage units breakdown** — per-owner listing with areas
   - **Key contacts** with roles
   - **Strategic analysis** — leverage, risks, recommendations
   - **Document inventory** — what's filed where, what's still missing
   - **Open items** — documents still needed, questions for the user

3. **Upload updated note to NDR Notes folder** (not root):
   ```python
   call("drive_upload", service_name="google-draas",
       path="/tmp/updated_note.html",
       parent="<NDR_NOTES_FOLDER_ID>",
       name="YYYYMMDD_MatterName_ResearchNote_v2.html",
       mime_type="text/html")
   ```

   NDR Notes folder ID for Veracious Vani Vilas: `1A5hIQeTDXfF_zRhCVExPB9rtW43MUCkq`

4. **Also move the old research note** from root to NDR Notes (if it was at root level).

### Phase 6: Deliver Summary to User

Structure the response as:
1. ✅ **What was filed** — table with new documents and their Drive locations
2. ❌ **Duplicates detected** — what was skipped and why
3. ⚠️ **Files not delivered** — if the zip file was too large for Telegram
4. 📋 **Case status quick reference** — key numbers, updated case table, crux
5. ❓ **Open items** — what's still needed

## Subfolder Reference (Veracious Vani Vilas Case)

| Folder Name | Drive ID | Description |
|------------|----------|-------------|
| Veracious Vani vilas (root) | `1yE0lV1hG4b7cG0JHe0pwXGGSQtX0Jr3v` | Matter root |
| NDR Notes | `1A5hIQeTDXfF_zRhCVExPB9rtW43MUCkq` | Briefing notes, analyses |
| Transaction Documents | `1VOyhFzqQrZd5TLjFs2O4rhD2UItmGAHb` | Letters, agreements, settlement docs |
| Property Documents | `1BHtJA0vmJQUfpd7cVVWFpE60vQ6j1m-5` | Deeds, title docs, ownership tables |
| Legal Data > Enforcement Suit | `1Sl7Rqisu1TD5uTBGweELefstH-KutPqH` | Court orders, IA applications |
| Legal Data > NCLT Avoidance Matter | `1aF1pgNuA7y1wXlAisCiv9yoIQbdifbwQ` | NCLT proceedings |
| Legal Data > Liquidation | `17zHDiVIrN5J_yfqBUu3tGX3IFo1FakCQ` | Liquidation proceedings |
| Legal Data > High Court Writ Petition | `1tggWo91Fq0NWsLa17k1cNWxbYEXwee9l` | WP proceedings |
| Legal Data > Criminal | `1tdl-hxJAHzhVaTaWfQAS1MutQHM8k2Bc` | Criminal complaints |
| Legal Data > PG Suit | `1m4lzlZ-hFJl3TUI_TlhtU00ih1oAqD9-` | Other suits |
| JDA | `1O_sq97mFkPHNlHdtUVxx1p7Et9hfQlZo` | Joint Development Agreements |
| TMP | `18p74II2uL32sNDzDDwXzmlOUdJJOTmE-` | Staging area (all new files go here first) |

## Pitfalls

- **gws_skill_bridge parameter names:** `drive_upload` takes `path` (not `local_path`), `name` (not `target_name`), `parent` (not `parent_id`), and `mime_type` is REQUIRED even though optional in the function signature (AttributeError if omitted)
- **gws_skill_bridge drive_search for raw queries:** Must pass `raw_query=True` as a kwarg, otherwise it wraps your query in `fullText contains '...'`
- **Duplicate documents may already be in Drive** from a previous session's filing — always check BEFORE uploading
- **Zip files > 20MB are rejected by Telegram** — tell the user to share via Drive link instead
- **Agent analysis is self-reported:** Subagents may claim "document analyzed successfully" but include hallucinations. Always verify key numbers (areas, amounts) against the original extracted text
- **Research note HTML:** Use inline CSS only (no external dependencies), dark theme for readability, tables for data, color-coded verdict badges (green for wins, red for losses)
