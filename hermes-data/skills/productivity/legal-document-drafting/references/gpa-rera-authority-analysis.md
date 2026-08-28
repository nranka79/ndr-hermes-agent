# GPA Clause Analysis — RERA Document Signing Authority

**Pattern:** User holds a General Power of Attorney (GPA / Irrevocable GPA Coupled with Interest) from landowners and asks: *"Can I sign [specific document] for RERA / statutory compliance under this GPA?"*

Follow this workflow.

---

## 1. Find the GPA Document

| Step | Action | Example |
|------|--------|---------|
| a) Check local files | Search filesystem for project name + "GPA" | `search_files(pattern="*GPA*Amber*")` |
| b) Check Google Drive | Use Drive API via `gws_auth.build_service('drive', 'v3')` — search by project name + "GPA" | `q="name contains 'GPA' and name contains 'Amber'"` |
| c) Known Drive locations | Check the project's RERA docs folder and Project Legal Documents subfolder | `RANKA AMBER - RERA DOCUMENTS/ → Project Legal Documents/` |
| d) Download | `service.files().get_media(fileId=...)` → save to local | Save to user data dir `/data/hermes/users/<uid>/` |

**Pitfall:** GPA filenames often have OCR typos ("Irrvocalbe" for "Irrevocable", "Coupled" for "Coupled"). Use broad search terms.

---

## 2. Extract Text from GPA PDF

| Method | When | Command |
|--------|------|---------|
| **pdftotext** | Text-layer PDFs (most registered GPAs have a typed text layer) | `pdftotext <input.pdf> <output.txt>` |
| **pdftoppm + vision_analyze** | Scanned/image PDF (no text layer) | See `ocr-and-documents` skill references |

---

## 3. Identify Relevant GPA Clauses

Map the user's question to GPA clauses. The standard DRAAS GPA structure (from Ranka Amber template) has these key clauses:

| # | Clause Title | Authority Conferred | Relevance |
|---|--------------|-------------------|-----------|
| 1 | **Approvals & Permissions** | Apply/represent before **RERA**, BBMP, BDA, Revenue Dept, BESCOM, KSPCB, etc. to obtain Approvals, NOCs, licenses, certificates | ✅ RERA explicitly named |
| 7 | **Legal Proceedings** | Sign & verify **affidavits**, plaints, written statements, compromise petitions before court/tribunal/arbitrator | ✅ "Affidavits" explicitly mentioned |
| 10 | **Statutory Compliance — RERA** | Act as **"Promoter" for the entire Project under RERA** | ✅ Strongest — covers all promoter obligations |
| 11 | **General Powers** | Do all acts necessary/expedient for developing the property "as fully and effectually as the Principals could do if personally present" | ✅ Catch-all residual clause |
| 5 | **Representation at Registration** | Appear before Sub-Registrar, present documents for registration | 🔶 For registration, not RERA filings |
| 6 | **Project Finance** | Mortgage/charge ONLY Developer's Share | 🔶 Banking, not RERA |

### Key Insight: RERA Title Indemnity Affidavits

For the specific question of signing **title indemnity affidavits** under RERA:

1. **Clause 1** — RERA is explicitly listed → you can represent the landowners before RERA, which includes submitting any document RERA requires
2. **Clause 10** — You're designated the **Promoter** for the **entire project**. Under Section 4 of RERA, the Promoter must submit title declarations/indemnity affidavits. This clause gives you that authority directly
3. **Clause 7** — Explicitly mentions signing **affidavits**. Though in the legal-proceedings context, it establishes the GPA contemplates affidavit-signing by the Attorney
4. **Clause 11** — Catch-all for anything "necessary or expedient" for the project

---

## 4. Answer Structure

When presenting the analysis:

1. **Short answer** — Yes/No/Qualified, in one sentence
2. **Clause table** — Which clauses apply and how (see table above)
3. **Full clause text** — Quote the actual wording from the GPA (verbatim)
4. **Risk note** — Any nuance the user should be aware of (e.g., "title indemnity is you swearing to the landowners' title — the GPA authorizes it, but the title risk remains with you as the signing Promoter")

---

## 5. Known GPA Structure (DRAAS Ranka Amber Template)

Registered 16 Aug 2025, DRO/SJN/GPA/1088/2025-26, landowners Farida Iyer & Raghu Iyer → DRA Realty Pvt Ltd.

11 numbered clauses covering: Approvals & Permissions (incl. RERA), Plans & Construction, Marketing/Sale of Developer's Share, Marketing/Sale of Landowner's Share (limited), Representation at Registration, Project Finance, Legal Proceedings, FERA/FEMA Compliance, Post-Completion Formalities, Statutory Compliance as RERA Promoter, and General Powers.

**Critical details:**
- "Irrevocable GPA Coupled with Interest" — survives death/incapacity of landowners
- Granted under and pursuant to the JDA
- Attorney acts "as fully and effectually as the Principals could do if personally present"

---

## 6. When the Answer Is NO

The GPA may NOT authorize the specific document if:

| Pattern | Example |
|---------|---------|
| Execution of final Sale Deed for Landowner's Share | Expressly excluded (Clause 4: "expressly excludes the execution of the final Sale Deed") |
| Authority to sell landowner's units | Requires "specific written authorization" from landowners |
| Anything outside development of the Schedule Property | Limited to the property described in the GPA schedule |
| Actions after GPA termination | GPA termination provisions in JDA Clause 14.2 |

---

## Reference: Ranka Amber GPA (Example)

- Registration: DRO/SJN/GPA/1088/2025-26 (also No. 277/2025-26)
- Landowners: Mrs. Farida R Iyer (through SPA Holder Mr. Raghu Iyer) and Mr. Raghu Iyer
- Attorney: M/s DRA Realty Private Limited, represented by Director Mr. Nishant Ranka
- Document in Drive: `1D4D3cF9IJivaqmCSulICWXYs_q88jbEj` (in "RANKA AMBER - RERA DOCUMENTS/Project Legal Documents/")
