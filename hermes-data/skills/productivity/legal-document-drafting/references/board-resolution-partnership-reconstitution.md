# Board Resolution — Partnership Reconstitution

## When to Use

When drafting a **Board Resolution** for a corporate partner (e.g. DRA Realty Pvt Ltd) approving:
- Change of firm name
- Change of profit-sharing ratio
- Contribution of new properties to the reconstituted firm
- Authorisation to execute and register the reconstitution deed

## Key Requirements (Nishant's Preferences)

| Requirement | Detail |
|-------------|--------|
| **Letterhead** | Company name (bold, 18pt, centered) + CIN/PAN line + Registered Office (both 9pt, centered) + horizontal separator |
| **Managing Partner** | Explicitly state that the company is the **Managing Partner** of the reconstituted firm |
| **CA Attestation** | Must include a CA attestation block at the end (CA signature, Membership No., UDIN, FRN) |
| **Authorisation** | Authorise the Director by name as the **designated representative of the Managing Partner** |
| **Language** | Direct and functional — avoid over-narration of background facts |
| **Format** | Google Doc → Drive (HTML import). Arial 11pt body, headings 13-14pt bold |

## Core Structure

### Header (Letterhead)
```
DRA Realty Pvt Ltd                     ← Bold, 18pt, centered
CIN: U70100KA2011PTC058105 | PAN: AAPCS9730H   ← 9pt, centered
Registered Office: [Full Address]              ← 9pt, centered
═══════════════════════════════════════════    ← Separator
BOARD RESOLUTION                                ← Bold, 14pt, centered
[Passed by the Board of Directors on dd.mm.yyyy]
```

### Resolution Clauses

**1. RESOLVED THAT** ... the Board approves, ratifies and confirms:

| Clause # | Content |
|----------|---------|
| **Managing Partner** | Acknowledge company as Managing Partner of reconstituted firm, represented by its Director |
| **Name Change** | Old name → New name + effective date |
| **Profit Ratio** | Before → After (e.g. 50:50 → 51:49) |
| **Property Contribution** | Table of all schedules (A, B, C etc.) with description, extent, value, contributed by |
| **Capital Contribution** | Total commitment, broken down: already deployed + paid + balance with conditions |
| **Authorisation** | Authorise Director by name as designated representative of Managing Partner to execute deeds, make applications (Section 281 IT Act), appear before authorities, do all incidental acts |

**2. RESOLVED FURTHER THAT** — certified copy to be furnished to authorities, banks, Registrar of Firms, IT authorities.

### Signing Block
```
_________________________
Mr. [Name]
Director, [Company Name]
(Designated Representative of the Managing Partner)

_________________________
Company Secretary / Authorised Signatory
```

### CA Attestation Block
```
═══════════════════════════════════════════

CA ATTESTATION

Certified that the foregoing is a true and correct copy of the Resolution
passed by the Board of Directors of [Company Name] at its meeting held on
______________ [date], and the same has been recorded in the Minutes Book
of the Company.

Place: Bangalore
Date: ______________

_________________________
Chartered Accountant
(Firm Name: ____________________)
Membership No.: ____________________
UDIN: ____________________
FRN: ____________________
```

## Implementation

Use **HTML → Drive API import** (`google-doc-formatting-template` approach). Inline CSS handles letterhead styling, tables, and signature blocks better than Docs API batchUpdate.

## Cross-References

- `references/covering-letter-deed-registration.md` — companion covering letter when filing the reconstitution deed
- `references/form-2-notice-of-change.md` — Form 2 filing with Registrar of Firms
- `references/reconstitution-deed-drafting-pattern.md` — the underlying deed being approved
