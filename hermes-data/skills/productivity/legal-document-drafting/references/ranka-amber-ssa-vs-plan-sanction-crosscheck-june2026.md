# Ranka Amber SSA vs. Plan Sanction Cross-Check
**Session date:** June 3, 2026
**User:** Bharat (Telegram: sales1.blr@draas.com)
**Documents:** SSA Google Doc (`1EnY77qQ-UXeMV7Pr49l6kiK_RTITK_jQ09gvljTthWI`) + Plan Sanction PDF (uploaded to chat)

---

## Document Identification
- **SSA:** `Ranka_Amber_SSA_FINAL_v3` — Google Doc, created May 30 2026, modified Jun 2 2026. 26 clauses + 6 schedules. Full text extracted via `export_media(text/plain)`.
- **Plan Sanction PDF:** `Copy of Amber Plan Sanction GBA_BECC_0540_25-26 (2).pdf` — 2-page BBMP area statement + drawing. Text extracted via PyMuPDF (`fitz.open().get_text()`). Project ref: `GBA/BECC/0540/25-26`.

---

## Discrepancies Found

### 1. ❌ CRITICAL — Addendum to JDA: Registered vs. Unregistered
- **SSA Recital 2:** "the parties have also executed an Addendum to the Joint Development Agreement registered as Document No. SHV-1-02227-2025-26"
- **Fact:** The Addendum was **not registered**
- **Severity:** Critical — false statement of registration in the document

### 2. ❌ Katha No. Mismatch — Schedule A
- **SSA Schedule A:** `7055785976` (E-Katha/PID)
- **Sanction Plan:** `7057785976` (Khata)
- Fourth digit differs — 5 vs 7. E-Katha (PID) and Khata are different numbering systems; verify against original Khata Extract.

### 3. ⚠️ Project Name — Typo
- **SSA §3 and throughout:** `RANKEA AMBER` (extra "E")
- **Should be:** `RANKA AMBER`

### 4. ⚠️ RERA Status Inconsistent Within Same Document
- **§2:** "All necessary approvals... including RERA registration" — RERA pending
- **§15:** "target date: 7th November 2028" — countdown from date of RERA registration (implies registered)
- **Schedule F:** "RERA Registration No.: To be filled upon receipt"
- Three conflicting positions in the same document.

### 5. ⚠️ Spouse Name Spelling Inconsistency
- **SSA Recital (page 1):** "Mrs. Faridah Iyer"
- **SSA Schedule A footnote [a]:** "Mrs. Farida R Iyer"
- **JDA Addendum (referenced in recitals):** "Mrs. Faridah Iyer"
- Inconsistency across documents; pick one spelling and use consistently.

---

## Items That MATCH (confirmed correct)
- Plot: 1-B, CS No. 4/124, Ward 83, D'Silva Layout, Pattandur Agrahara ✓
- BBMP LP formats differ but both point to same sanction ✓
- Total FAR: 2,559.82 sq.m (plan) ≈ 2,558.9 sq.m (SSA) — minor rounding ✓
- All 20 unit BUA figures match exactly ✓
- Built-up area totals: 2,225.08 sq.m (SSA and plan agree) ✓
- 50:50 sharing, 10 units per party ✓
- Possession target: 7th November 2028 ✓

---

## User Feedback (verbatim)
1. Landowner details — taken from JDA as-is, modified ✓
2. Developer details — modified from separate source document ✓
3. Addendum to JDA not registered — CRITICAL, must correct ✓
4. FAR figure 2,558.9 sq.m confirmed as from BBMP Plan Sanction only — no relation to Bhuvanesh area statement
5. Parking — ignore; do not mention in feedback

---

## Bharats stated preferences (June 3, 2026 session)
- "only give me the report which is not matching" — suppress matching items in all future cross-checks
- "don't mention parking" — parking discrepancy was flagged but user said ignore it
- "analyze only, we are not going to edit the document" — analysis-only sessions, no Drive uploads
- User wants: mismatch list only, then wait for confirmation before doing more