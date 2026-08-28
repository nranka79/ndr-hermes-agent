# Email Requisition → Drive Document Matching with Confidence Classification

**Trigger:** A legal firm, advocate, or authority sends a requisition list (in email body text, not as an attached checklist) asking for specific documents. The user needs you to systematically check their Drive for each item and report what's available, what's uncertain, and what's missing — with explicit confidence levels.

**Unlike:** `drive-sheet-document-audit.md` (which uses a Google Sheet as the source checklist), or `gmail-attachment-checklist-extraction.md` (which extracts from .docx attachments). This workflow handles requisition lists that are **plain text in the email body**.

## Workflow

### Phase 1 — Read the Requisition from Email

Get the email body containing the requisition list. The requisition may be in the email itself (not an attachment), organized in tables or bullet points.

```python
from tools.gws_auth import build_service
import base64

service = build_service("gmail", "v1", service_name="google-draas")
results = service.users().messages().list(
    userId="me", q="from:SENDER subject:REQUISITION", maxResults=1
).execute()
mid = results["messages"][0]["id"]
msg = service.users().messages().get(userId="me", id=mid, format="full").execute()

def get_text(parts):
    for part in parts:
        if part.get("mimeType") == "text/plain":
            data = part["body"].get("data", "")
            if data:
                return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
        if part.get("parts"):
            result = get_text(part["parts"])
            if result:
                return result
    return ""
```

### Phase 2 — Map Each Requisition Item to a Drive Search

For each document in the requisition list, design a targeted Drive query. The requisition typically has 3 categories:

1. **Entity docs** (Partnership Deed, Reconstitution Deed, Registration, Form A) — search by entity name
2. **Transaction docs** (Sale Deed by date/registration number, Payment details) — search by date, document number, amount
3. **Litigation docs** (IA petitions, court orders, counters) — search by case number, court, document type

**Before searching:** Get the full folder tree first. Knowing the folder structure (numbered subfolders, naming conventions) helps you target searches efficiently and avoids false negatives from narrow search terms.

### Phase 3 — Classify Each Result into 3 Confidence Tiers

| Tier | Label | Criteria | When Used |
|------|-------|----------|-----------|
| **FOUND (100% sure)** | Exact match by name, date, document number, or entity | The filename explicitly states what it is | Clear filename + matching metadata |
| **PARTIALLY FOUND / Maybe** | Likely contains the document but can't fully verify | May be inside a larger scanned PDF, or filename is ambiguous but context suggests it's right | Scanned PDF with no extractable text, or generic name |
| **NOT FOUND** | No file matching the description exists in Drive | Exhaustive search across all relevant folders and name variants found nothing | Clear gap |

### Phase 4 — Map Each Item to Correct Drive Path

For FOUND items, note the exact Drive location so the user knows where to find them.

### Phase 5 — Compile Consolidated Report

Present as a structured table with status, location, and notes. Follow with one-line explanations for any non-obvious items.

### Phase 6 — Offer Next Steps

- For PARTIALLY FOUND items: offer to view scanned PDF via browser/vision to verify contents
- For NOT FOUND items: suggest checking email attachments not yet filed, or physical records
- Offer to create Drive subfolders for pending items

## Known DRAAS Patterns

### Saveganapalli CMA 742/2026 (Jul 2026)
Entity docs (1-3): Found in Saveganapalli Legal Docs folder.
Form A (4): Only Form C (Acknowledgement) exists — no standalone Form A.
Sale Deed 16.10.2023 (5): Found in Ranka Oasis and Registered sale deeds folders.
Payment Details (6): Found as Google Sheet.
IA 1/2025 Affidavit (7) & Orders 16.06.2025 (8): Likely inside scanned CourtPapers PDF — classified as PARTIALLY FOUND.

## Key Pitfalls
### The Scanned PDF Black Hole

Large scanned PDF bundles cannot be searched via text extraction. Options:
1. Use pdftoppm + vision_analyze for selected pages — see `ocr-and-documents` skill's `references/vision-ocr-from-scanned-pdf.md` for the index-driven page discovery pattern
2. State the limitation clearly — document likely EXISTS but can't verify programmatically
3. Do NOT mark as "FOUND (100%)" — belongs in PARTIALLY FOUND tier initially

**Upgrade path:** Items initially classified as PARTIALLY FOUND (inside a scanned PDF) can be **upgraded to FOUND** after you verify them via the index-driven discovery pattern. Read the PDF's index → identify page numbers → convert only those pages → confirm content with vision_analyze. Report the upgrade to the user with the specific details you found.

### Name Variants
Same entity spelled differently across folders (Sevaganapalli vs Saveganapalli vs Sevganapalli). Always search multiple variants.

### Duplicate Files
Same document appearing in 5+ locations. Report one authoritative location, mention duplicates exist.

### Scanned PDFs from Email Attachments
If user uploaded email attachments to Drive earlier, check the Litigation case folder for files named with email date prefix (e.g., `20260619_CMA742_CourtPapers_Served.pdf`).
