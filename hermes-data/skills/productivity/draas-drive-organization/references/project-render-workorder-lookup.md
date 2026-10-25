# Locating project renders / proposed office visuals & matching them to a work order

Trigger: NDR says "we had a proposed office space / render for <project> somewhere in the drive; they created a work order; can you find it?" Verified 2026-09-14 for Ranka Udaya's prefab marketing office (Moduli outreach).

## ⚠️ CROSS-PROJECT TRAP (NDR corrected me 2026-09-14)

- Bharat's **"Ranka Oasis - Design & Marketing"** (`1BRnGlLOAk9ZIt64L7cccvgXyC7kAdFVA`, owner sales1.blr) → `1Pq35uw9K0i36pW30c66Go1_mfP2zmaR3` → **"Marketing Office Renders"** (`1c_mcHGC8Wg2vBh_XAk7Umor78qikYrpq`) contains the **RANKA OASIS** marketing office renders — `20260616_RankaOasis_MarketingOffice_3DRenders_Original_Bhuvanesh.pdf`, `20260616_RankaOasis_MarketingOffice_3DRenders_Bhuvanesh.pdf`, `Ranka Oasis Marketing Office 3D Render ChatGPT Earthy.jpg` (cover), `NP Marketing Office final all 25.05.26.dwg`.
- On 2026-09-14 I sent these to vendor Moduli believing they were the Ranka Udaya design. **They are NOT.** NDR: "This is actually Ranka OS's marketing office 3D render — not the one I was referring to." The design scope overlaps (both are marketing/site offices) but the projects are DIFFERENT.
- **Red flag that should have stopped me:** the folder is nested under a folder literally named "Ranka Oasis - Design & Marketing". When the folder name / parent chain names a DIFFERENT project than the one asked for, do not use it. The correct Ranka Udaya design came from NDR himself (WhatsApp/chat attachment), saved as `RankaUdaya_SiteOffice_Moduli_Reference_20260914.jpg` in Ranka Udaya → Marketing and Content (`1fRYtiqclzInfz2rVZHFNziou9KSEg77B`).
- **Consequence workflow when you sent the wrong render:** (1) delete the wrongly-placed copy from the requested project's folder (the Oasis originals stay in Oasis), (2) resubmit the vendor query with a body that EXPLICITLY says the earlier visual was the wrong design (another project of ours) and disregard it, (3) delete the old email draft and recreate it with the correct render attached (raw MIME, verify the attachment part), (4) check note on the issued Kelsa WO — NDR already asked Anbu to add reference images of the desired office look to the WO.

## Kelsa WO state — TWO records for the same scope (do not report the first hit)

Search `search_leads(537, "marketing office")` AND `"Ranka Udaya"` — the same scope has multiple records:

| # | Lead ID | Vendor | Stage | ₹ incl GST | Note |
|---|---|---|---|---|---|
| 750 | 53744737 | AM Office Solution | **PO-WO Created (NOT issued)** | 5,21,560 | cabin 20x10ft ACP+glass narration; NDR's July notes hold it / seek alternate vendor |
| 761 | 55195693 | **EXOTIC PORTABLE CABINS** | **HoD Approved (ISSUED)** | 10,33,680 | "WO for preparation & supply of marketing office container for Ranka Udaya"; Issued PO-WO PDF `Ranka Udaya-WO-Marketing Office.pdf`; NDR note: add reference images of desired look |

- The ISSUED work order for the Ranka Udaya marketing office is **#761** (`https://kelsa.io/537/leads?current_item_id=55195693`), not #750. Check stage (PO-WO Created ≠ issued) and the presence of an `Issued PO-WO` attachment before telling NDR "the work order".
- Related but distinct: `20260620_RankaUdaya_IamHere_WorkOrder` (digital marketing retainer, NOT the office); `DRA PO - Ranka Udaya.pdf` (Trubld architectural/marketing development PO ₹2.95L, also not the office).

## Search ladder (in order)

1. Canonical project folder children walk (`'<id>' in parents and trashed=false`).
2. **Sibling/colleague folders**: renders and design assets often live under the DESIGNER's folder or the adjacent project — search `name contains '<render|office|3D>'` and inspect "Ranka Oasis" / "Design & Marketing" / "Renders" / "Marketing Office Renders" style folders across owners. **BUT treat same-named / sibling-project folders as evidence of a DIFFERENT project until the contents + parent chain prove otherwise.**
3. **Kelsa cross-reference**: search PO/WO pipeline 537 by narration keyword; the narration tells you the cabin spec (e.g. #750's "20x10ft prefab container ACP cladding, full glass front, interiors & pantry") but ONLY the stage + Issued PO-WO attachment tell you which record actually got issued.
4. **fullText name-search variants are weak**: `fullText contains 'site office'` and `name contains 'office'` + project name return nothing for image-only render PDFs (no text layer) — prefer folder walks and owner-scoped searches.
5. If still missing, tell NDR plainly and point him to WhatsApp (his stated fallback) — do not fabricate.

## Outreach supporting artifacts

- Only copy a render into the target project folder AFTER you've verified it actually belongs to that project (check the source folder name + parent chain + naming). The 2026-09-14 mistake: I created `20260914_Moduli_Outreach_SiteOffice_Renders` inside Ranka Udaya with the Ranka OASIS render — deleted after NDR's correction; the Oasis originals stayed in Bharat's folder.
- When the render must be emailed to a vendor, attach the original PDF/JPG via raw MIME (EmailMessage `add_attachment`) and include drive links; the render PDF is image-only so never rely on OCR/text of it. After creating the corrected draft, verify the attachment part exists via `payload.parts` walk before telling NDR it's attached.