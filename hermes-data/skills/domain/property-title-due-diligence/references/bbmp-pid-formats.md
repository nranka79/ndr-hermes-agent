# BBMP Property ID Formats — Old PID vs New ePID

> Domain knowledge for Bangalore property due diligence.
> Correction source: Vinod Das (DRAAS Property Title Due Diligence), June 2026.

## Two Systems, Same Area

Properties in the same locality (e.g., Domlur 2nd Stage, Bangalore) can carry
different property ID formats depending on whether specific BBMP transactions
have occurred.

## Old PID Format: `72-1-B1-740`

- **Legacy/manual system** from the pre-digital era
- Structure: `Ward_Number - Block_Number - Building_ID - Unit_Number`
- Example breakdown:
  - `72` = Old BBMP Ward Number (Domlur used to be in this ward)
  - `1` = Block/zone within that ward
  - `B1` = Building identifier
  - `740` = Individual unit/shop number
- **What it means:** This property has **NOT** been through improvement charge
  payment or plan sanction that would trigger ePID assignment

## New ePID Format: `4372453357` (10-digit)

- **Electronic Property ID** — a computer-generated unique number
- **Assigned when:**
  1. **Improvement charges** are paid to BBMP (typically by developer), OR
  2. **Plan sanction** is applied/approved for the property
- NOT triggered by:
  - Simple property tax payment
  - Ownership transfer (unless linked to plan sanction)
  - General system migration
- The 10-digit number is a database key — no inherent geographic meaning

## Why Both Exist in the Same Area (e.g., Domlur 2nd Stage)

| Property Status | PID Format |
|---|---|
| Old property, no improvement charges paid, no plan sanction | Old PID (`72-1-B1-740`) |
| Developer paid improvement charges to BBMP | New ePID (10-digit) |
| Plan sanction applied/approved | New ePID (10-digit) |
| New construction post-digitisation | New ePID (10-digit) |

## ⛔ Common Misconception (Avoid This)

Do **NOT** say the ePID came from a "general digitisation drive" or "system
migration" by BBMP. The correction from Vinod Das:
> "If the property have paid improvement charges in BBMP or before the plan
> sanction than coming epid number 10 digit"

The ePID is transaction-triggered, not migration-triggered.

## How to Verify

1. **BBMP Property Tax Portal:** https://paytax.bbmp.gov.in
   - Enter the PID or old format number — still works for many legacy properties
2. **BBMP e-Aasthi:** For e-Khata linked to ePID
3. **Physical Tax Receipt:** Shows which format the property uses
4. **Plan Sanction Order:** Will show the assigned ePID
5. **Improvement Charge Receipt:** Will show the generated ePID

## Practical Use for Due Diligence

- When a property shows **old PID**: May need plan sanction / improvement
  charges verified before proceeding with certain transactions
- When a property shows **ePID**: Digital records exist — easier to verify
  online through BBMP portals
- **Both are valid** for property tax payment, but only ePID properties can
  typically get e-Khata online
