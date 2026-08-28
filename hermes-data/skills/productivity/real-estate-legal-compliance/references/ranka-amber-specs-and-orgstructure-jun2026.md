# Ranka Amber — Specs Review & Org Structure Update (June 2026)

## Session context

Nishant reviewed the Project Specifications document for Ranka Amber and corrected the mid-market benchmarks to be more basic. He also provided team member assignments for the Level 3 Project Team table in the Organizational Structure document.

## Specs corrections applied

| Item | Original (over-specced) | Nishant-approved (basic mid-market) |
|------|------------------------|-------------------------------------|
| Internal Finish | Premium emulsion | Oil-bound distemper |
| Flooring | 8'x3' marble-finish vitrified | Standard 2'x2' vitrified tiles |
| Doors | Teak frame + designer veneer | Hardwood frame + laminated finish |
| Sanitary | Premium CP + full-height cladding | Standard CP + 7ft cladding |
| Electrical | 8kW → recommended 10kW | 5kW (compact 3BHKs) |
| Elevators | Schindler only | Schindler/Johnson/OTIS/KONE or eq. Indian brand |
| Water Supply | Basic statement | Hydro-pneumatic + CPVC supply + UPVC SWR drainage + gray/black water separation |
| Fire Safety | ABC extinguishers all floors | Not Applicable (building <15m) |
| Security | IP CCTV + manned security | Compound wall with gate only |
| Sewage | STP per KSPCB norms | No STP — connected to municipal main line |

## Org Structure Level 3 — Team member sources

| Role | Found in | Value |
|------|----------|-------|
| Structural Engineer | Gmail: tushar patil <structure.pune@gmail.com> exchanging "1385-AMBER" structural GFC drawings with architect | Tushar Patil (+91 9011076607) — **NOTE:** Nishant's voice said "Tushar Giri" initially; Gmail search corrected to "Tushar Patil" |
| Project Manager / Site Supervisor | Gmail: Anbarasan M <anbarasan@draas.com> in Ranka Amber document threads | Anbarasan Murugaperumal (Anbu) |
| Legal & Compliance Advisor | Known contact: vkdas@draas.com, DNR Associates | Vinod Kumar Das, DNR Associates |
| Accounts & Finance | Gmail: echamundeshwari@draas.com — multiple emails | Eshwari Chamundeshwari |
| Sales & Marketing | Known contact: sales1.blr@draas.com | Bharat Hawaldar |
| Contractor / Builder | Work Order DOCX in RERA folder shows `[Name of Contractor / Vendor]` — still blank. Name "Jairaj" then corrected by Nishant to "Jayram" — still not found in Gmail. | Needs Nishant to provide firm name/contact directly |

## Dual upload pattern confirmed working (Jun 2026)

After editing the Project Specifications DOCX with python-docx red text:

1. **DOCX update** — `drive.files().update(fileId=ORIGINAL_FILE_ID, media_body=media)` — replaced the original file in-place. Red formatting preserved ✅
2. **Google Doc copy** — created via `drive.files().create()` with mimeType override — conversion preserved red font color in browser ✅ (verified via Docs API: table cells showed foregroundColor.red > 0.5)
3. **Both files in the same RERA folder** — user can open either

This contradicts the earlier assumption that DOCX→Docs conversion strips inline colors. Font color (RGBColor set via python-docx) survives conversion. Highlights (WD_COLOR_INDEX) may not survive.

## Turnaround time for spec reviews

From user's message to final approved doc: ~3 rounds of feedback in a single session (~20 min total). The user expects the HTML table → feedback → doc edit cycle to happen in rapid succession, not spread across separate sessions.

## Voice transcription quirks (Jun 2026 update)

| Voice said | Actual correct name | Source |
|-----------|-------------------|--------|
| "Tushar Giri" | Tushar Patil | structure.pune@gmail.com (Gmail thread: "1385-AMBER" structural GFC drawings) |
| "Jairaj" then "Jayram" | Not found in Gmail — contractor not yet finalized | Work Order shows `[Name of Contractor / Vendor]` |
| "Anbarasan" / "Anbu" | Anbarasan M | anbarasan@draas.com |
| "Chamundeshwari" / "Eshwari" | Eshwari Chamundeshwari | echamundeshwari@draas.com |
| "Vasundhara Rajya" (voice said) | Dr. Vasunethra Kasargod | Manipal Hospital (Respiratory Medicine & Pulmonology) — confirmed via Pharmacy Tax Invoice PDF text extraction |

**Medical name trap:** When Nishant says a doctor's name by voice, the transcription is often completely wrong. The actual name on the document (prescription, OP bill, pharmacy invoice) is the authoritative source. For Manipal Hospital: always check the PDF attachment for the exact doctor name in the "Doctor" field — it appears on both OP-Bill Receipts and Pharmacy Tax Invoices.

## Key workflow lessons

1. **Voice transcription name trap** — When Nishant says a name in a voice message, it may be phonetically mangled (e.g., "Tushar Giri" → actual "Tushar Patil", "Jairaj" → "Jayram"). Always cross-reference with Gmail before accepting a name as fact. Run multiple Gmail queries (first name, last name, project context) before presenting.

2. **Org Structure role sourcing from Gmail** — The architect is usually pre-filled. For the other 6 roles:
   - Search Gmail with role keyword + "Amber" / "Ranka Amber"
   - Structural engineer: search "Amber structural" or "amber GFC" — reveals the structural consultant exchanging drawings
   - Site supervisor: search "Amber" + "site" or look for Anbarasan/Anbu in RERA document threads
   - Accounts: search "Chamundeshwari" or "Eshwari" in Gmail
   - Contractor/Builder: Work Order template in Drive is blank; no email trail found for "Jayram" — must ask Nishant directly

3. **Always present findings for confirmation before editing** — Show the user what you found for each role. Highlight any uncertainties (name spelling discrepancies). Do NOT edit the document until the user explicitly confirms.

4. **HTML table pattern for specs** — For multi-row tabular data that needs decision-making (like 16 spec items), generate a self-contained HTML file with color-coded rows (green for no-change, amber for change-recommended). The user opens it, scans, and tells you which changes to apply. Do NOT dump the table in Telegram — the HTML is faster for the user to scan.
