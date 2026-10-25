# GPA / Power-of-Attorney signing-authority audit (regulatory applications)

When NDR asks *"do I / does <company> have the right to sign <application/affidavit/Form> under the GPA the landowners gave us?"* — do NOT answer from memory. Audit the actual GPA document. Verified pattern 2026-09-24 on the Ranka Northstar TDR pack.

## Audit steps (always run these)
1. **Pull the GPA from Drive** (search `name contains 'GPA' or 'Power' or 'Attorney'`), download, OCR if scanned (pdftoppm -r 300 -gray → tesseract eng --psm 6; trust clause layout over stamp-page garble).
2. **Identify the grantee exactly**: company vs individual vs firm. GPAs are frequently made out to a company ("M/s X Projects Pvt Ltd, represented herein by its Director") — the power belongs to the COMPANY, not the director personally and not any successor firm. A director signs *for the company*, and must currently hold that office (board resolution makes it airtight).
3. **Map powers clauses against the specific statute/authority at issue** — look for: applications/petitions/affidavits; appearance before the relevant authority (e.g. "authorities under the Karnataka Town and Country Planning Act"); Land Acquisition Officer appearance; revenue/Tahsildar/DC officials; general all-necessary-acts clause; ratification clause. Two-or-three broad clauses usually cover the ask; quote them by number.
4. **Check the assignment/developer chain** — if the JDA rights were later ASSIGNED to a different entity (e.g. DRAPPL → DRA Ranka Holdings) and the operative addendum names that entity, the old GPA may not be in the current developer/entity's name. If the forms name the assigned entity, you need GPA assignment/ratification or a fresh one-liner from the owners. Ask the user which entity signs rather than guessing.
5. **Read the registration details** off the stamp/chalan pages (SRO, doc no., date) — OCR is unreliable there; verify against the original before submission. Attach the registered copy in the submission pack so the processing officer can see the authority.
6. **Report the exact signature-block wording**, not a bare yes/no: *"For M/s <Company> (GPA holder of the landowners, per GPA dt <date>), as its Director — <name>"*.

## Comfort layers
- A contemporaneous addendum/clause showing the parties INTENDED the agent to pursue the same right (e.g. JDA addendum giving developer the TDR/additional-FAR benefit) materially strengthens a narrow-reading challenge.
- Individual owner signature blocks can be retained alongside the attorney's line — safer for authority acceptance when local owners can sign.

## Project instance
Full Ranka Northstar detail (2014 GPA clauses, Khata/owner list, TDR notice) lives in skill `ranka-northstar-tdr-drc`.