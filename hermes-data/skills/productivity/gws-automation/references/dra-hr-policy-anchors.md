# DRA Realty Private Limited — HR Policy & Offer Letter Anchors

Reference for future sessions pulling DRA Realty HR / offer-letter / employee data. All file IDs were verified on **3 June 2026** during a pull for Nishant Ranka.

## Master HR Policy docs (3 versions, current → oldest)

| Version | File ID | Format | Key change |
|---|---|---|---|
| **2026 DRA – HR POLICY.docx** *(current)* | `0BymF3UUrZZYKMnBodl9ILVRVb3c` | `.docx` (binary) | Office timing **10:00am–6:30pm**, Kelsa sign-in, structured late-coming penalty |
| **DRA HR POLICY Final.docx** (May 2025) | `1qdwC-jolb661JIqPwyPd7vvQhel1QMB227McAAUlmPA` | Google Doc (native) | Office timing **9:30am–6:30pm**, biometric attendance |
| **DRA HR POLICY Final.docx** (May 2025, duplicate) | `1xscTonu1YJ5fJMSbRTwlavpkWCoH_XoFSN_XOePV3FI` | Google Doc (native) | Identical content to above |
| **HR Policy for DRA.odt** (oldest) | `0B1Oc8cSaJXPGYTBiRGRaQ0dob0libU5zaVlNbjhub3BqWXpB` | `.odt` (binary) | Earliest version |

**Read method by format:**
- `.docx` → `drive.files().get_media(fileId)` + `python-docx` `Document(io.BytesIO(buf))` → `paragraph.text`
- Google Doc → `drive.files().export(fileId, mimeType='text/plain')` → decode utf-8, OR `docs.documents().get(documentId=...)` for structured JSON
- `.odt` → `get_media` + odfpy parse

## DRA Realty master folder

Shortcut: `1tgnPcAT8GjAGE5WGXHcMEkn6toOV42ob` → resolves to folder `1-DH4-G1xarpbE8WlQNbKk5uGIN_eeRLw`. List children with `q="'1-DH4-G1xarpbE8WlQNbKk5uGIN_eeRLw' in parents"`.

## Key offer-letter email threads (Gmail, search for these subjects)

- **Vinitha R — EA / Executive Operations Lead** (Nov 2025) — most recent. Final offer: Base ₹35k + Attendance ₹5k = ₹40k fixed + Performance Pay (1.2L/yr retained 2 yrs, 60% quarterly payout after) + Project Bonus (1L+ target). Multiple negotiation emails on title.
- **Abhishek Kaushik — Accounts** (Jun 2025) — probation extension letter referencing offer letter terms.
- **Rakshith Sherugar — Finance & Accounts Analyst** (Nov 2024) — most detailed offer template. Joined 15 Nov 2024, CTC ₹2.5L on probation, Base ₹19k + Attendance ₹2k.
- **Archana A K — Accountant** (May 2024) — offer made, candidate declined.
- **Vidya — Architect** (Jul 2024) — offer letter withheld pending onboarding formalities.

## Key offer-letter docs in Drive

- 20240912 Vinod Das (Rahul) — employment offer letter: `17mVr5ha3sGldiPw_kGKzJn-xCnMoM0ykazbIHEW23UI`
- Vidya offer & Appointment letter: `1_Q_ieZNrN2hjSECWmt9yASTNPAMMfUFqDF-vzVhjoM8`
- DRA Site Engineer Siddhesh Offer Letter: `1Nobtvirbz2d2ROOpB4Lv68kYdnkBv7Z5Eb5CvHmdr2c`
- Vibha Offer Letter: `1cyFFnuoPr-COE2Pw4p2Fv7rhHXCnbM6ESsRgN4uK_VI`
- Bhuvanesh offer letter: `1pLeZhq1pEArUd-gqhQaZHo3ML4M3ofLlcaXBnTQ8Vck`
- Vibha - Joining Letter: `19mJMxrMfuqc3GMS5B6jv7_v74NEEwNzV`
- Letter of Appointment dtd 19-04-2019: `13ilqIcit_tMLBvoJ3L5GCCDhYAwT8OZP`
- 20231110 Acceptance letter: `1AgzACYaH2CyCGY9777DBN1HU_yAzB21V`
- 20240621 DRA REALTY LETTER HEAD: `1oVYjmRJJWavPpDfhgsD4UTc_-OKGVxxfUJXO51Kb-xo`
- Bhavesh Compensation Offer – DRA Ventures (spreadsheet): `1k_Ml54u5md1ldkfJLvcOFA7BSXyOAJ-uysCM3bDO09Y`
- DRA Engineering Director – JD & KPA Based Performance Pay Structure: `1gbIe7mAHqoTTpED0piOeuQGQwSX7oJtjD_HHV6wAM4U`
- DRA Realty Attendance_Payroll_Pipeline_Design_v2 (Kelsa integration): `1CsStXfP2JzqI2ik2BJPfBNNnl14g28TS8yzaTT1ATDI`
- DRA Key Roles – Job Descriptions & KPAs: `1aTy1BbxHKPf79Cb1j-muptiMBIoHWHe7ZKk55rKCrJw`
- DRA Marketing & Design – Job Descriptions & KPAs: `10VVmEu3gkupNssZqVB-yxDqaiD-JQvxNvoGMDRGgJ3M`
- Latest Employee ID – DRA: `18WwDJUS16j4_9ZXvx_h1XqeHn9q755TVi5ZnJncONYY`

## Timing-change gotcha (2025 → 2026)

The 9:30am → 10:00am shift appears in offer letters issued before vs after the 2026 policy. When drafting new offer letters or salary letters, check the **current** policy version (the .docx, not the older Google Doc) — the older 9:30am reference can still surface in emails and will be wrong.

## DRA Realty entity details (CIN/GST/addresses)

Lives in the "Important Information" Google Doc: `17qG23od-hRioDFj0yXSBfTraiuFXM019UwVBvRLlpR0`. Read via `docs.documents().get(documentId=...)` (not `drive.files().get_media` — returns 403 for native Docs).
- DRA Realty Pvt Ltd: CIN `U70100KA2011PTC058105`, PAN `AAPCS9730H`, GSTIN `29AAPCS9730H1ZO`
- Registered office: 4, Ranka Chambers, 31 Cunningham Road, Bangalore - 560052
- Operational office (Prism Greystone): 204, 205, 206, Cunningham Road, Bengaluru - 560052
