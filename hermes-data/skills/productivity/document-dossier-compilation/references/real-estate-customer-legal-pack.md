# Real-Estate Customer Legal Pack — Ranka Udaya (DRAAAS/Sevaganapalli)

**Scenario (verified 2026-08-25):** Bharat wants to share Ranka Udaya legal/title documents with a customer (Pragya Joythi, booking Plot/Block No. 5). He does NOT want to hand over the internal Drive folder link — wants ONE clean compiled PDF dossier instead.

**Folder:** `Ranka Udaya - Legal Documents` (Drive folder id `1zvvtbBtedFiJ4XdcY-9LO4AzJ7V46N9t`, owned by Bharats' `sales1.blr@draas.com` account — `service_name='google-draas'`).

## Ordering convention (Bharat's words)
- "Make an index from this page to this page so this is a document" → index table with page ranges per doc.
- "Whatever the document is, based on the year/date, segregate; documents which don't have dates, put at the last." → dated docs oldest→newest, undated at end. "You decide what would work."

## Downloaded inventory (27 PDFs; allotment draft .docx excluded on user request)
Dated docs (oldest → newest in final pack order):
1. **FMB / Survey Sketch** — 02.02.2001 (3p, text)
2. **Gift Deed** Nanjamma→Prakash Reddy et al, Doc 10658 — 07.06.2022 (24p, text)
3. **Rectification Deed** Doc 10658/2022 — 14.06.2022 (17p, text)
4. **Legal Heir Certificate + Family Tree attestation** (Subba Reddy) — 28.05.2024 (2p, text)
5. **Partition Deed** Doc 11721 — 18.06.2024 (34p orig / 37p colour copy, scanned) — keep ONE (orig colour copy), drop duplicate
6. **GPA** Naveen Kumar → Ramesha — 29.07.2024 (15p, text)
7. **Legal Scrutiny Report K. Velayudham** — 21.09.2024 (9-10p, scanned) — two versions exist; keep the DRA-facing one (names DRA Thindlu Land Partners as present owner), drop the earlier 8-owner version
8. **Legal Scrutiny Report J. Sudha Reddy** — 17.10.2024 (9p, scanned)
9. **Absolute Sale Deed → DRA Thindlu Land Partners** Doc 20527/2024-25 — 24.10.2024 (32p, scanned)
10. **Thasildar NOC** — 19.11.2024 (1p)
11. **Thasildar NOC certificate** — 04.12.2024 (1p, text)
12. **Adangal** — 17.12.2024 (1p, text)
13. **No AD / No Temple certificate** — 17.12.2024 (1p, text)
14. **EC 1980-2024** — issued 03.01.2025 (5p, text)
15. **Relinquishment Deed 1632** (DTLP + Panchayat President) — 24.02.2025 (17p, scanned) + **Relinquishment Deed 1634** (DTLP & TANGEDCO) — 24.02.2025 (13p, scanned) — group together
16. **Approved Layout Plan** — 05.05.2025 (1p, text)
17. **RERA Order / Registration** TNRERA/30/LO/0642/2026, filed 18.02.2026 (1p, text)
18. **EC 01.01.1975 – 16.02.2025** — issued 21.05.2026 (8p, text)

Undated docs (at END, after all dated):
19. **Village Map** (Sevaganapalli, Hosur Taluk, survey map) — 1p, scanned
20. **VAO Register extract** (Village Administrative Officer register) — 2p, scanned
21. **TOPO Sketch** — 1p, text
22. **Notarized Family Tree Subba Reddy** — 1p, text
23. **ICICI Unit Nomenclature sheet** — 3p, text — ⚠️ internal (unit naming format); user-agreed to EXCLUDE from customer pack

## Exclusion decisions (state these in the confirmation list)
- Duplicate partition colour copy (two colour copies exist; keep one)
- Duplicate Velayudham legal report version
- ICICI Unit Nomenclature sheet (internal, not legal)
- Allotment letter DRAFT (agent's own artifact; user explicitly said exclude)

## Extraction helpers that worked
- `import pymupdf` (NOT `fitz` — deprecated alias) to read text + page counts.
- `vision_analyze` needs PNG — convert page with `page.get_pixmap(dpi=150).save('out.png')` first; PDFs rejected.
- OCR page-1 of scanned PDFs (legal reports, registers, village maps) to confirm doc type/author/survey no before classifying.
- Download via Drive API `MediaIoBaseDownload` with `build_service('drive','v3', service_name='google-draas')` + `HERMES_SESSION_USER_ID=sales1_blr GWS_VAULT_SOCKET=/run/gws-vault/vault.sock`.