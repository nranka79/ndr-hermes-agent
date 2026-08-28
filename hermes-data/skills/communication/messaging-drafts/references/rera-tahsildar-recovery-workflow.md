# RERA & Tahsildar Legal Recovery Notices — Workflow Reference

This reference documents the workflow for receiving, translation-verifying, filing, and escalating official Kannada recovery notices (e.g., Tahsildar Final Notice / Japti Hukum) concerning RERA orders for DRAAS projects (e.g., Mirabilis).

## 1. Trigger Conditions
- Receipt of an official Kannada notification, notice, or order from the Revenue Department/Tahsildar.
- Mentions of DRAAS projects (Mirabilis, Ranka Amber, etc.) or Ranka family members (Dinesh D. Ranka, Nishant Ranka) alongside third-party complainants.

## 2. Multi-Phase Analysis Workflow

### Phase A: OCR & Vision Translation
- Never rely purely on the PDF text layer. Scanned Kannada documents often have scrambled, corrupted, or missing OCR layers (e.g., "3tdteoo dod totəFe").
- Render the PDF page to a high-DPI JPEG and run `vision_analyze` to extract:
  - **Issuing Authority:** Name, design, location (e.g., Special Tahsildar, Bengaluru East, K.R. Puram).
  - **Complainant (Decree Holder) Name:** (e.g., Sabyasachi Behera).
  - **Reference Numbers:** RERA Order Ref, DC Memo Ref, Office File No.
  - **Demand Amount & Bank Account Details:** Exact rupees demanded and designated deposit bank account details (A/c, IFSC, Branch).
  - **Deadlines:** Typically 10 to 15 days from notice receipt.
  - **Consequences of Non-Compliance:** Property attachment, public auction, family asset targeting.

### Phase B: Asset & Stakeholder Risk Assessment
- Check co-recipients list. If any direct Ranka names (e.g., Dinesh D. Ranka) are targeted, assess the immediate risk to personal movable and immovable properties of the family.
- Flag the 10-day strict timeline prominently as a high-integrity blocker.

### Phase C: Google Drive Filing
- File the document in the corresponding Project folder under `Legal/RERA Complaints & Orders/`.
- File naming convention (**YYYYMMDD Project Entity DocumentType**):
  - **Original:** `20260601 Mirabilis KPDL Tahsildar Recovery Notice SabyasachiBehera_original.pdf`
  - **Professional Translation:** `20260601 Mirabilis KPDL Tahsildar Recovery Notice SabyasachiBehera_English.pdf`
- Use ReportLab to generate a clean, professionally typeset English translation PDF containing all reference numbers, bank details, and warnings. Upload both to the same folder.

### Phase D: Family Escalation & Actions
- Draft a WhatsApp message to Key Stakeholders (e.g., Roshni/Manish) communicating:
  - Exact nature of the notice.
  - Attachment risk for personal/family assets (e.g., "Nashankar assets").
  - Clear steps (e.g., Manish/legal team to intercept urgently).
  - Web links to both papers on Google Drive for immediate access.
- **WhatsApp link parameters requirement:** Pre-escape any ampersands in URLs or text as full-width ampersands `＆` (U+FF06, encoded as `%EF%BD%86`) so the link never truncates on mobile WebViews.
