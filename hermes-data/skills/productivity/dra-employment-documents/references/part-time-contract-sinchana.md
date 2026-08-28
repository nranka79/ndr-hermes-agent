# Part-Time / Hybrid Contract — Sinchana (Senior Architect, Trubld) — Worked Example

Session: 2026-07-31. User asked to verify leave details in Sinchana's contract, compare against HR policy, and update it for her part-time schedule. Voice-note instructions; name appears as "Sinchana S" on resume, "Shinchana" in the original filename (misspelled), "Sinchana Gouda" in user's voice. **Anchor on the contract file, not the voice transcript.**

## Source files

| File | Drive ID | Notes |
|---|---|---|
| `01022026_Shinchana_EmploymentContract.docx` (original) | `1TK80jjxw8IjJYwowm3iVrr3HtgY1KPEH` | Trubld Integrated Services Pvt Ltd; parent folder `1bfB0H31c9lIzc8oWGYxj_axEC8a8RzI3` |
| `01022026_Sinchana_EmploymentContract_Updated` (native Google Doc, edited) | `1eZuMyeETq9DaN4ghlIMN4wr0IdCSZaSaBqwLrSu_U3Y` | Created by converting the .docx; all edits in blue #1155CC |
| Resume `Sinchana S.pdf` | `1wbDgcL-tSWwGaXgv3cdmnOPgEJ8hvD7w` | naukri Architects folder |

2026 DRA HR POLICY.docx (full-time policy) = `0BymF3UUrZZYKMnBodl9ILVRVb3c`. Full-time leave: 12 CL + 10 Medical; 8 hrs/day Mon–Fri + 6 hrs Sat.

## Original contract state (before edits)

- Senior Architect, reports to Board of Directors, term from 2025-09-01, CTC ₹300,000/annum (₹25,000/mo), paid on 10th.
- §4.1 said "12:00 AM to 5:00 PM" (typo for 12 PM), 1-hr lunch, "4 hours of work per day" — internally inconsistent.
- §4.2: 20 hrs/week Mon–Fri, Sat/Sun rest.
- §4.4: "Any 3 days of the week for 5 hours at office and work from home for rest 2 days."
- §5.1: 12 earned leaves; §5.2: 10 sick leaves (full-time numbers — the mismatch the user wanted fixed).
- Schedule C "Important Notes" #4: "minimum 40 hours per week required" — contradicted everything.

## Final agreed terms (user's voice instructions, verbatim intent)

- **Hours:** 12:00 PM to 4:00 PM = 4 hours ABSOLUTE work time per day. No lunch break, no breaks.
- **Pattern:** Mon/Wed/Fri in office; Tue/Thu/Sat work from home (6 working days, 24 hrs/week, Sunday rest). With permission she may switch an office day with a WFH day or vice versa.
- **Leave:** 6 (six) paid leaves per annum TOTAL, all-inclusive — earned/casual + sick combined. Deviation from full-time HR policy made explicit. Beyond 6 = salary-deducted.

## Blue-text editing workflow (what worked)

1. Download .docx, extract text via zipfile/XML (python-docx may be absent).
2. Convert to native Google Doc in the SAME folder:
   ```python
   drive.files().create(
       body={'name': '01022026_Sinchana_EmploymentContract_Updated',
             'mimeType': 'application/vnd.google-apps.document',
             'parents': [ORIGINAL_PARENT]},
       media_body=MediaFileUpload('/tmp/contract.docx', mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document', resumable=True),
       fields='id, name, webViewLink').execute()
   ```
3. Clean template artifacts first with `replaceAllText`: `__BOLD_PHRASE_0__` → '' and `**` → '' (offset-safe).
4. Content edits: `replaceAllText` per old→new string (verify each old string occurs exactly once first).
5. Color: locate each new string's range, `updateTextStyle` with `foregroundColor` rgbColor (17/255, 85/255, 204/255), `fields: 'foregroundColor'`.
6. **Pitfall hit:** for the Schedule C note I computed offsets from a paragraphs-only text walk and ran `deleteContentRange`+`insertText` — it landed inside a table cell and corrupted "Payment Method: Direct bank transfer..." into "Payme...th". Fixed by `replaceAllText` for repair, and for re-coloring used the API's authoritative `startIndex` from element metadata (walk ALL content including table cells).
7. Verification: assert full-text contains new values AND does not contain stale full-time values (12:00 AM, 20 hrs, 25 hrs, 40 hrs, 12 earned, 10 sick, "rest 2 days", "5 hours").

## Final blue edits delivered (verbatim)

- §2.3: "The Employee must maintain a minimum of 24 hours of timesheets per week (4 hours per day across 6 working days)."
- §4.1: "The Employee's working hours shall be from 12:00 PM (noon) to 4:00 PM, with no lunch break and no breaks in between. This constitutes a total of 4 hours of absolute work time per day."
- §4.2: "The Employee's regular weekly working hours shall be 24 hours across six working days — Monday, Wednesday and Friday at the office, and Tuesday, Thursday and Saturday work from home. Sunday is designated as a rest day."
- §4.3: Saturday removed from overtime clause; weekly cap 24 hrs.
- §4.4: "on Monday, Wednesday and Friday (in-office days), and work from home on Tuesday, Thursday and Saturday (remote days), for 4 hours each day. With prior permission of the Company, the Employee may switch an in-office day with a work-from-home day, or vice versa."
- §5.1: "5.1 Leave Entitlement (Part-Time): Given the Employee's part-time engagement — 4 hours of work per day, 3 days at the office and 3 days work from home — the Employee shall be entitled to a total of 6 (six) paid leaves per annum. This entitlement is all-inclusive and covers earned/casual leaves as well as sick leaves, and deviates from the general DRA HR Policy, which applies to full-time employees. Leave must be applied for in advance and approved by the reporting manager or the Company."
- §5.2: "5.2 Sick Leaves (Included in 5.1): Sick leave is included within the 6 (six) paid leaves per annum referred to in Clause 5.1 above. Sick leave availed beyond the stipulated 6 paid leaves per annum shall be deducted from the Employee's salary."
- Schedule C note #4: "minimum 24 hours per week required, at 4 hours per day across 6 working days."
