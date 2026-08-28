# Project NOC / Sanction Audit — Ranka Northstar (Allalasandra) Worked Example

Worked example from Jul 2026: user asked (voice) to check PCB/KSPCB NOC, find latest BBMP sanction, and give Prakash (psingh@draas.com) viewer access. Voice said "Alala Sindhra" — that is **Allalasandra** (Ranka Northstar location, Yelahanka Hobli, Bangalore).

## Folder map (verified Jul 2026)

- **Allalsandra Legal opinion** — `16ZGzDaNA-5CmzipOuerKEm1sCoTV3Y-W` (project root; owner admin2.blr@draas.com)
  - **NOC's AND PLAN SANC** — `1PgyOSuuVhqlYZecIxGuSY1F5vdW0rC4A` — THE folder with both old sanction + old NOCs
    - `PRJ_0987_21-22.pdf` — BBMP sanctioned plan (copy also in "Old sanction Plan North Star")
    - `KSPCB_ConsentForEstablishment_2021_ValidTill2026` — `1HgRKyV5iTAYiO4FckvVdsd3-SFzjEILI`
    - `20151008 Fire Noc Ranka North Star.pdf`
    - `AAI_HeightClearanceNOC_2015/2016_Expired`, `BESCOM_PowerSanctionNOC_2016_Expired`, `BWSSB_WaterAndSewageNOC_2016_Expired`, `GFTS_HeightClearanceConfirmation_2015_Expired`
    - `Noc Documents and Expiry Status` — `1Zy0geB_PT7BDrJa02Do2ktg9jMCyFfb-jIzU5HSGny4` (index: 6 rows, KSPCB CFE row 1)
  - **Old sanction Plan North Star** — `1I4YiQVcQRH77P5HVw_wEW0IA-BHvMCaf` (contains PRJ_0987_21-22.pdf)
  - **Documents submitted for Plan Approval 2026** — `1dQn6bLlsbyJvSsfKE8fWeSUcen5rTPZB` (affidavits/bonds to BNCC — application in flight, NOT a sanction)
- **North star approval folder 2026 April** — `1dw-BzPEmoWdiQ-ePcanYA0INvVfQxJfB` (2026 BBMP 24M plan DWGs + SHEET 1-3 — submitted drawings, not sanctioned plan)

## KSPCB NOC facts (Ranka Northstar)

- **Consent for Establishment (CFE)** — Consent No. **CTE-325651**, PCB ID 103327
- Dated **09-Jul-2021**, valid till **07-Jul-2026** (expired ~3 weeks before the Jul-2026 audit — renewal needed)
- Entity: DRA Projects Pvt Ltd, Sy.No.14/1, Khata No. 591/1077/14/1/1, Allalasandra Village, Yelahanka Hobli
- Covers Water (Prevention & Control of Pollution) Act 1974 + Air Act 1981. Scale LARGE, Colour ORANGE.
- Drive: `1HgRKyV5iTAYiO4FckvVdsd3-SFzjEILI`

## BBMP sanctioned plan facts

- **PRJ/0987/21-22IN**, File No. BBMP/Addl.Dir/JDNORTH/0006/21-22
- Sanctioned 15 Jun 2022, digitally signed by JDTP Manjesh (BBMP)
- Scope: Block A (A) Wing A-1 (A) — Basement + GF+4UF residential apartment
- Drive: `1Xzy6gGDJ75aEWEe3HsDAvBl7n9FY_qFX` (NOC folder copy) / `111Xbk0djC0PTdPHMy1oi4SEtNYb4aOmg` (Old sanction folder)
- 2026 drawings/affidavits exist but NO new sanction on Drive as of Jul 2026.

## Critical pitfall — same-looking NOC sets belong to different projects

Two nearly identical dated-NOC bundles exist on Drive:
- `NOC dated 23.11.2010 issued by KSPCB` + BESCOM 5.10.2010 + BWSSB 7.2.2011 + BSNL 30.8.2010 + AAI 8.9.2012 + DGP 15.11.2010 → **Veracious Vani Vilas** (`1yE0lV1hG4b7cG0JHe0pwXGGSQtX0Jr3v`), NOT Northstar
- Ranka Northstar's KSPCB doc is the 2021 CFE above

Always walk parents before attributing.

**Cross-project shortcut contamination (re-verified Aug 2026):** the "NOC's AND PLAN SANC" folder also holds `20260615_RankaAmber_BESCOM_TemporaryPowerSupply_SanctionLetter` — a SHORTCUT to a Ranka Amber file (different project). When listing sanction files for Northstar, flag it rather than listing it as an Allalasandra doc. Sanction links re-verified Aug 2026: `PRJ_0987_21-22.pdf` at `1Xzy6gGDJ75aEWEe3HsDAvBl7n9FY_qFX` (NOC folder) and `111Xbk0djC0PTdPHMy1oi4SEtNYb4aOmg` (Old sanction folder); 2026 approval folder (`1dw-BzPEmoWdiQ-ePcanYA0INvVfQxJfB`) holds 24M DWGs + SHEET 1-3 (submitted drawings, not a sanction).

## Granting viewer access (code, verified)

```python
from tools.gws_auth import _load_credentials_direct
from googleapiclient.discovery import build
creds = _load_credentials_direct('google-draas')
svc = build('drive', 'v3', credentials=creds)

svc.permissions().create(
    fileId='16ZGzDaNA-5CmzipOuerKEm1sCoTV3Y-W',  # root
    body={'type': 'user', 'role': 'reader', 'emailAddress': 'psingh@draas.com'},
    sendNotificationEmail=False, supportsAllDrives=True).execute()
# repeat for '1PgyOSuuVhqlYZecIxGuSY1F5vdW0rC4A' (NOC folder)

# verify
svc.permissions().list(fileId=fid, fields='permissions(id,type,role,emailAddress)',
                       supportsAllDrives=True).execute()
```

Result: psingh@draas.com had reader on "Old sanction Plan North Star" + 2026 folder already, but NOT on root or NOC folder. Added reader to root + NOC folder; verified both.

## Prakash contact (for the notification WhatsApp)

- psingh@draas.com, DRA phone +91 99000 93816 (verified WhatsApp number — see contact-phone-lookup skill verified table; do NOT use 9739932078 which is a wrong primary-mobile round)
