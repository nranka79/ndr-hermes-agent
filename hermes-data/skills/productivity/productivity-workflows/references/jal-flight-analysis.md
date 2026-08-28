# JAL Flight Analysis — Ranka Family (Nov 2025)

## What Was Found

4 JAL GST invoices from `info.gst@jal.com`, emailed Dec 25, 2025, tickets issued **2025-11-09**.

These represent a **family of 4 business class flights to Japan/Far East**, booked via DRA Realty Private Limited (company account).

## Passenger Data

| Passenger | Invoice No. | Amount | Ticket Format |
|-----------|-------------|--------|---------------|
| Nishant (RANKA/NISHANTMR) | 131-2144036356 | ₹2,37,344 | Adult business |
| Roshini (RANKA/ROSHINIMS) | 131-2144036357 | ₹2,37,344 | Adult business |
| Ruhaan (RANKA/RUHAANMR) | 131-2144036358 | ₹1,83,775 | Child business |
| Rivaan (RANKA/RIVAANMSTR) | 131-2144036359 | ₹1,83,775 | Child business |

**Total: ~₹10.4 Lakhs** — consistent with a round-trip business class family fare to Japan.

- Date of issue: 2025-11-09
- Seller: Japan Airlines Co. Ltd, Bangalore office (WeWork Galaxy, Residency Road)
- Buyer GSTIN: 29AAPCS9730H1ZO (DRA Realty Private Limited)

## Key Finding: No JAL Booking Email Exists

JAL does NOT send a booking confirmation email to the passenger. The GST invoice (sent to NDR@draas.com) is the only evidence of the ticket. The sender was `info.gst@jal.com` — not a booking confirmation address.

This is unusual compared to IndiGo/Air India which send itinerary emails. JAL only issues GST invoices.

## How to Find the PNR/Ticket Number

The GST invoice PDFs were extracted using `pdftotext -layout`. The text shows:
- Invoice number: `131-2144036356` (format: `131-<ticket_number>`)
- PAX Name: `RANKA/NISHANTMR` (surname/FIRSTNAME + MR/MS/MSTR suffix)
- Date of issue: 2025-11-09

The actual ticket number (13-digit e-ticket number) is NOT visible in the GST invoice text. To claim JAL miles, the user will need to:
1. Log into their JAL booking at jal.net or through the booking agency
2. Find the 13-digit ticket number (starts with 131-)
3. Submit retro-credit at jal.com/jalmileagebank

## Retro-Credit Deadline

- Flight date: November 9, 2025 (ticket issue date; actual travel likely within days of this)
- JAL Mileage Bank claims: up to **12 months** from travel date
- Deadline: approximately **November 2026**
- Status: still claimable — user must act soon

## Alliance Context

- JAL = **Oneworld** alliance
- JAL miles are held in **JAL Mileage Bank**
- Cannot be transferred to Star Alliance programs (KrisFlyer, etc.)
- The user CAN choose to credit JAL flights to a DIFFERENT Oneworld program (e.g., Cathay Pacific Asia Miles or British Airways Executive Club) at time of ticketing — but since tickets are already issued, this option may no longer be available
- Recommendation: claim JAL miles in JAL Mileage Bank; use KrisFlyer (Star Alliance) for all other flights

## Comparison: JAL vs KrisFlyer for Ranka Family

| Factor | JAL Mileage Bank | KrisFlyer (Star Alliance) |
|--------|-----------------|--------------------------|
| JAL flights | Native — full miles | Not creditable |
| Malaysia Airlines | Via Oneworld connection | Native — full miles |
| Air India | Not partner | Native — full miles |
| Singapore Airlines | Not partner | Native — full miles |
| Indulge card transfer | Possibly available | Likely available |
| Best for Japan routes | Yes | No (Star Alliance weak in Japan vs ANA) |
| Recommended for this user | For JAL flights only | For all other flights |