# Kanta Ranka (KDR) — US Visa Renewal Reference

**Date:** 2026-06-04 (updated 2026-07-11)

---

## KDR Personal Profile

- **Name:** Mrs Kanta Ranka (KDR's wife, Nishant's mother)
- **DOB:** 21/06/1958 (per MRZ + visa — passport typed field shows 1953 which is wrong)
- **Age/Sex:** 68 / Female
- **Address:** 1503, Embassy Habitat, Opp. St. Anne's College, Bengaluru — 560 052
- **Hospital:** Manipal Hospital Millers Road (Dr. Vasunethra Kasargod — Respiratory Medicine & Pulmonology; Dr. Sunil Dwivedi — Cardio; Dr. Haldipur — ENT/Trustwell)
- **Upcoming procedure:** Stapedectomy under GA; pulmonology clearance in progress (PASP 54 on echo, planned CT Pulmonary Angiogram)
- **STT voice garble:** User pronounces "Kanta" as "Kanda/Kandaranka" — always map back to Kanta Ranka

---

## Drive Folder Structure (CORRECT — verified Jul 2026)

**Do NOT invent a "Medical → Kanta Ranka" hierarchy. The actual structure is:**

```
Personal/
  KDR/                              ← KDR = Dinesh Devraj Ranka (Nishant's father)
    KDR Medical/                    ← All KDR + Kanta Ranka medical docs go here
      [prescriptions, OPD notes, medical reports, advices]
      Invoices/                     ← ONLY for receipts, payment invoices, bills
```

**Filing rules:**
- **Prescriptions, OPD notes, medical reports, advices** → `KDR/Medical/` (root)
- **Invoices, payment bills, receipts** → `KDR/Medical/Invoices/`
- **Filename convention:** `YYYYMMDD_Hospital_Doctor_PatientType_Description_Amount.pdf`
- **Share invoices with:** Eshwari (Chamundeshwari, accounts) + Roshni (rnr@draas.com)
- **Accounting entry:** Dr. KDR / Cr. NDR

**Pitfall (verified this session, Jul 2026):** I proposed `Medical → Kanta Ranka` as the folder hierarchy. User corrected: there is no per-patient subfolder — everything goes under `KDR/Medical/`. Always verify existing folder structure via Drive before proposing new ones.

---
**Context:** Nishant Ranka (telegram: ndr@draas.com) asked about renewing his mother Kanta Ranka's US B1/B2 visa.

---

## Document Locations

### Current Indian Passport (Z4799082)
- **File:** `KDR Passport 2028.pdf` (ID: `1MvS0eYpkrt0P6Y_0sbiR7gQ0JQqZbBVQ`)
- **First page image:** `KDR Passport 2028 First Page.jpg` (ID: `1SPjS47iXnQ_TFsQIJuefzb6Vu-FBZD7_`)
- **Last page image:** `KDR Passport 2028 Last Page.jpg` (ID: `1cOQatDYGl8JFDMZz3wHPONLsWEvgZ9gG`)
- **Passport No.:** Z4799082
- **Issue Date:** 02/05/2018
- **Expiry:** 01/05/2028
- **Place of Issue:** Bengaluru
- **DOB (typed):** 21/06/1953
- **DOB (MRZ):** 5806218 → 21/06/1958 ⚠️ DISCREPANCY — see below

### US Visa (in older passport G8444080)
- **File:** `KDR USA Visa JUL2017-JUN2027.pdf` (ID: `1qWJu2aRy-ef954DH4qGn07St5aD9XFNB`)
- **Visa No.:** M6185126
- **Type:** B1/B2 (Tourism/Business)
- **Issue Date:** 05/07/2017
- **Expiry:** 29/06/2027
- **Entries:** Multiple
- **Issuing Post:** Chennai (Madras)
- **Passport No. on visa:** G8444080 (different from current Z4799082)
- **DOB on visa:** 21JUN1958 ⚠️ CONFLICT — see below

---

## ⚠️ DOB Discrepancy — Must Be Resolved Before Filing

| Document | DOB |
|----------|-----|
| Current passport (Z4799082) — typed entry | 21/06/1953 |
| Current passport MRZ line 2 | 5806218 → **21/06/1958** |
| US Visa (G8444080) | 21/06/1958 |

The MRZ on the current passport and the US visa BOTH show 1958. The typed entry in the current passport shows 1953. The visa was issued in 2017 using the older passport (G8444080) which presumably matched the visa's DOB of 1958.

**Possible explanation:** The current passport (2018) may have been renewed from an older passport where the DOB was 1958. The new passport's typed field may have been entered incorrectly as 1953, while the MRZ (machine-readable zone) carries the correct/consistent 1958.

**Action required:** Before filing for visa renewal, Nishant must verify which DOB is correct by checking the original old passport (G8444080). If 1958 is the correct DOB, the typed entry error in the current passport should be corrected via re-issuance.

---

## Visa Renewal Rules (B1/B2 — India)

### Earliest Application Window
- **12 months before expiry** — confirmed rule. Kanta's visa expires 29/06/2027, so she can apply **now** (June 2026).
- Can also apply after expiry (within the validity window allowed by current policy).

### Can She Apply Right Now?
- ✅ **Yes.** 29/06/2027 − 12 months = 29/06/2026. She is already within the renewal window.

### Passport vs Visa Renewal Sequence
- ✅ **Renew passport first, then renew visa** — this is the recommended sequence.
- Her current passport expires 01/05/2028. Renewing now (June 2026) gives maximum validity for the visa application.
- Submit: new passport + old passport (G8444080) with valid B1/B2 visa.

### Biometrics (Fingerprint)
- Kanta was fingerprinted when her visa was issued in July 2017 (10-fingerprint scan + photo).
- For renewals, previous biometrics on file generally exempt the applicant from re-biometric collection.
- **Confirm at time of filing** — policy can change; the VAC may call her in for fresh biometrics if the previous data has expired from the system.

### Interview Waiver (Drop Box)
- Indian B1/B2 renewal applicants **may qualify for interview waiver** if:
  - Previous visa was B1/B2
  - Previous visa was issued by **Chennai consulate** (confirmed: it was)
  - No refusals or violations
  - Renewal filed within eligible window
- She likely qualifies for **drop box** — no interview required.

### Application URL
- **https://www.ustraveldocs.com/in-en/**

### Documents Required
1. New passport (Z4799082)
2. Old passport with valid B1/B2 visa (G8444080)
3. DS-160 confirmation
4. Appointment confirmation
5. Photo (US visa spec)
6. Visa fee receipt

---

## Recommended Sequence

1. **Resolve DOB discrepancy first** — check old passport G8444080 for correct DOB; correct current passport if needed
2. **Renew Indian passport** — can be done now at any passport Seva Kendra; current expiry May 2028
3. **File DS-160** for B1/B2 renewal — no interview needed (Chennai-post, previous visa, no violations)
4. **Schedule appointment** at VFS Global / US Consulate VAC
5. **Drop off documents** — new passport + old passport with visa + appointment confirmation

---

## Related Skills
- `messaging-drafts/references/whatsapp-url-encoding-research.md` — WhatsApp URL encoding (fullwidth ampersand pattern for wa.me)
- `messaging-drafts/references/contacts-lookup.md` — Drive PDF contact discovery (used to find Dr. Kenneth F.H. Tan's number in this session)