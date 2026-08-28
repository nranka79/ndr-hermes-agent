# Requisition Checklist Reconciliation — Worked Example (Gunjur Sy No 40)

Session 2026-08-07. Context: lawyer Krishna B.R. (BRK Law / Pattanshetti) replied to a title-clearance email saying "furnish remaining documents per our list sent on 06/11/2025". User asked: find the checklist, determine supplied vs pending, deliver the original Word docs + email links.

## What worked
- **Search Gmail on ALL lawyer domains**: `from:krishna@brklaw.in`, `from:krishna_br@pattanshetti.com`, `from:pattanshetti.com`. Only the current-year emails surfaced from `brklaw.in`; the actual checklist came via a FORWARDED chain (Ananya S `ananya.s@pattanshetti.in` → Dharmesh → Nishant), which the `from:` search on the lawyer missed initially. Date-window search `newer_than:540d` + `subject:(Gunjur OR checklist OR requisition)` surfaced it.
- **Thread query bug**: `q=f"thread:{THREAD_ID}"` returned 0 messages even though messages existed. Fix: search with broader terms, collect message IDs from the search results, then fetch each by ID.
- **Attachments**: recursive walk of `payload.parts`; each part with `filename` has `body.attachmentId`; download with `messages().attachments().get(userId="me", messageId=..., id=...)`, base64 decode, save.
- **Magic bytes over extension**: both `Sy_No_40_Req_Ltr_AS.doc` and `Sy_No_40_Add_Req_Ltr_AS.doc` started with `PK\x03\x04` = ZIP = actually .docx. Renamed to `.docx` and extracted via zipfile → `word/document.xml` → regex on `<w:p>` / `<w:t>`.
- **Checklist semantics**: two lists exist — "Requisition list" (28-10-2025) and "Additional Requisition List" (06-11-2025, Ref JMP/AS/158/25). The later one is operative and carries color legend: black = asked earlier, blue = received, red = additional. "Received" annotations mark supplied items.
- **Cross-check Drive**: the reorganized legal-docs Drive folder (Gunjur Dodballapur legal docs, id 1k8EPOZRD1Tu6WCWuHpmJJ3QqHPmbzBJu) held many docs (RTCs, MRs, sale deeds, family trees, caste certs) never formally marked Received. Conclusion to user: ask lawyer to tick off folder contents before re-chasing.
- **Delivery**: send renamed .docx via `MEDIA:/tmp/...docx`; email links = `https://mail.google.com/mail/u/0/#search/<threadId>` (thread links stable; message links not).

## Checklist item categories (recurring in land DD)
Title docs (grant file: application, appendix, DC order, Saguvali Chit, grant register extract, grant sketch, upset-price receipt, caste cert, family tree, death certs) · previous title deeds/chain · revenue/mutations (index of lands, inheritance certs, MR extracts, RTCs by period) · survey (Phodi/LR Tippany, Akarband, Tippany, Hissa Tippany, R.R. Pakka Book, Atlas, Hudbast, new survey numbers, updated village map, survey sketch) · endorsements (Tahsildar 48A/77A, AC 79A/79B, AC PTCL/SC-ST, BIAAPA/KIADB/KHB, NHAI/road widening) · conversion (OM + fine challan + sketch) · CDP zone · tax receipts · ECs (period ranges) · clarifications (raja kaluve, lake, heritage, eco-zone, tower, highways, railway, graveyard/army/monument/defence) · third-party agreements (MoU/JDA/GPA/SPA) · 45A undervaluation · mortgages/cross-collateralization · pending litigation (DRT/NCLT/courts) · originals + Aadhaar/PAN + purpose note.

## Pitfalls seen
- `.doc` files from law firms are frequently .docx in disguise.
- catdoc/antiword/libreoffice NOT installed on VPS — pure-Python zipfile extraction is the reliable path.
- Empty placeholder Google Docs on Drive (VoiceAgent_Feedback_Analysis etc.) return blank via Docs API — the real content lives in the local user folder (`/data/hermes/users/[REDACTED-TID]/Sales_AI_Training_Tool/03_Feedback/`).
