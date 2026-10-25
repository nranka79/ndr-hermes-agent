# Channel Partner / Sales Associate Empanelment FORM — build pattern (DRA's own form)

The CREATE side of the channel-partner class: DRA drafts its OWN empanelment form for
selling a project through channel partners / sales associates (as opposed to
channel-partner-sales-mandates.md, which is the REVIEW side — analyzing third-party
mandate proposals). Built 2026-09-25 (Ranka Udaya, TN RERA, v2.0) and 2026-10-07
(Ranka Amber, KRERA, v1.1) — the two builds are direct siblings; clone the second from
the first.

## Form anatomy (parts 1–5 HTML → branded PDF + DOCX, fillable overlay)

- Part 1: cover (project name, promoter, RERA regn no., unit summary) + PART A
  application: applicant type, name/firm, PAN, GSTIN, address, contact person, mobile,
  email, bank for commission payout, experience, state RERA agent registration
  (number + validity + certificate annex + status boxes registered/applied/not yet),
  other projects represented, referrer, market/geography, customer segments, team
  size, lead-gen channels.
- Part 2: PART B sales commitments (units committed — per project type, e.g. 2 BHK/3
  BHK or Plot+Const vs Plot-only; target period; first-booking-in-days; qualified
  leads/month; site visits/month; lead-gen budget; support expected; RERA agent reg
  number) + PART C starts — definitions (Sale Consideration, Realised Value,
  Conversion/Closed Sale), obligations of Partner and Company.
- Part 3: code of conduct, RERA compliance, price discipline, marketing/collateral
  approvals, commission structure + payout + recovery, lead management (Kelsa),
  commitments review gates, termination, indemnity, confidentiality/anti-poaching,
  misc.
- Part 4: RERA compliance clauses 16–21 (see below), declarations (D.1 a–i incl.
  RERA-specific: not debarred, no criminal record, keep registration current), D.2
  RERA particulars table, D.3 signature blocks (both signatories + two witnesses),
  Company signatory block identifying the RERA promoter.
- Part 5: SCHEDULE A project snapshot, B commission slabs + payout milestones,
  C lead registration & protection procedure (Kelsa), D commitments record, E state
  RERA compliance annexure (checklist, particulars to display, statutory notes for
  Legal/Finance, partner RERA declaration).

## Commission structure (the slab-by-effort ladder) — DRA standard

- Four slabs by how much of the closure effort the Partner performs, paid on
  **Realised Value** (amounts actually received, net of refunds/cancellations — never
  on bookings):
  - S1 Referral 0.50% (introduces + registers lead only; DRA closes)
  - S2 Assisted close 1.00% (sources/qualifies/visits/supports; DRA closes)
  - S3 Co-close 1.50% (full selling cycle to booking; DRA documents)
  - S4 Full-cycle close 2.00% (end-to-end through registration/full realisation)
- Volume accelerator: +0.25pt at 3–5 units, +0.50pt at 6–9, +0.75pt at 10+ in a
  rolling 12 months, added to the slab rate per closed unit.
- Payout milestones tied to realisation AND registration (user-dictated 2026-10-07,
  under-construction project):
  1. 50% of commission on Customer execution of sale/construction agreements AND
     receipt of at least **20%** of Sale Consideration — paid within 15 working days
  2. Balance 50% on receipt of **50%** of Sale Consideration AND expiry of the
     cancellation-risk window (in either case not later than 90 days) — within 15
     working days
- **Under-construction note (projects still building):** customer payment is linked
  to the construction plan — state explicitly in B.2 AND clause 10.4 that the partner
  is paid on the milestones above as consideration is actually realised. Keep the two
  tables in lockstep or the form contradicts itself.
- Clawback: cancellation → proportionate clawback; partner misrepresentation → ENTIRE
  commission clawed back; survives termination. Company may set off against pending
  payouts.
- **Aggregate slab+accelerator capped at the state's notified brokerage ceiling**
  (clause 18 + Schedule B.3 + E.3 confirmation box) — protects DRA when S4 2.00% +
  0.75% accelerator would breach a 2% cap.

## Lead management (Kelsa) — non-negotiable block

- Registration before/within 24h of first substantive contact, tagged with partner as
  source; mandatory fields incl. verified mobile + requirement + budget + source.
- 60-day protection window, renewable once on documented activity; no activity 60
  days → lapse/reassign.
- First-registered-wins on duplicates (timestamp).
- Company-origin leads (website, walk-ins, ads, events, corporate tie-ups) NOT
  commissionable unless the partner introduced + registered the customer first.
- CRM record is the SOLE evidence of entitlement; all follow-ups logged in Kelsa.

## State RERA compliance clauses 16–21 (both TN and KA builds) — adapt per state

1. **Promoter/developer compliance (16):** project RERA regn no., no sale without
   registration (s.3), 70% of collections in separate project account
   (s.4(2)(l)(D)), truthful ads (s.12), registered agreement for sale — no money
   beyond 10% without it (s.13), adhere to sanctioned layout (s.14), refunds with
   interest (s.18). Statutory text prevails.
2. **Agent registration (17):** mandatory s.9, at partner's cost, state-specific
   format, 5-year validity, renewal, certificate with application, 7-day notice of
   lapse, auto-suspension of empanelment while not in force; s.10 duties (records,
   no unfair practice, full disclosure); penalties s.61 (up to 1 yr / fine up to 10%
   of cost), continuing up to ₹10,000/day cumulative 5%.
3. **Commission ceiling (18):** capped at notified ceiling; excess unpaid.
4. **Advertising (19):** every ad carries project RERA number + promoter name +
   partner's own agent number; no assured-return/RG claims beyond approved
   literature.
5. **Buyer protection (20):** customers' RERA rights (s.18 refund, s.31 complaint)
   preserved; partner cannot obstruct.
6. **General (21):** severability, updates by notice.

State differences verified 2026-09/10:
- **TN RERA:** agent format `TN/Agent/xxxx/yyyy` (from TN RERA's own agent register);
  project no. format `TNRERA/30/LO/xxxx/2026`. Portal rera.tn.gov.in.
- **KRERA (Karnataka):** agent application Form G; fees ₹25,000 individual / ~₹2 lakh
  for firms; 5-year validity; format shown as `KA/RERA/Agent/____/____` — actual
  published prefix NOT confirmed from a primary source, so mark "(as per the
  certificate)" and let Legal confirm; portal rera.karnataka.gov.in. Exact notified
  brokerage ceiling also unconfirmed — draft as "the ceiling notified from time to
  time" with a Legal/Finance confirmation box, never invent a percentage.

## HARD HOUSE RULE (Prakash correction 2026-10-07): NO PRICE REFERENCES IN THE FORM

"Remove mentioning any of the costing details / sale price details… prices may change
time to time as per Company/Management decision; the Company will provide the current
price list and any changes will be informed through official communications (e-mail,
WhatsApp)."

- Sweep EVERY part for ₹ / bands / "approx Cr" / illustrative rupee columns:
  cover unit cell, Schedule A price range + key selling proposition rows, clause 2
  obligations, clause 8 price discipline, cover footer.
- Delete the "Illustrative on a ~₹X Cr unit" column from the commission slab table —
  keep only the slab RATES (percentages); no rupees anywhere.
- Replace the price row with: "As per the Company's current approved price list,
  communicated to the Partner at empanelment and on every change through official
  communications (e-mail / WhatsApp); prices may change as per Company/Management
  decision."
- Clause 8.1 = quote only current approved price list; company issues changes via
  official comms taking effect from the date stated; partner must obtain current list
  from coordinator before quoting if in doubt.
- Keep ₹10,000/day + 10% "of the cost" figures ONLY where they are statutory penalty
  text (Schedule E.3 penal provisions) — that is legal text, not pricing; flag to
  Legal if even that should change.
- Sweep for clone artifacts too: when building the sibling project's form, grep the
  old project's product-specific phrases (e.g. "Rental Guarantee" from Udaya must NOT
  survive into Amber) and price strings.

## Fillable overlay specifics (see professional-documents → references/fillable-form-acroform-overlay.md)

82-widget overlay across Parts A/B/D + Schedules D/E. Field-name convention:
`SD_units`, `E1_s1`…`E1_s8`, `E4_confirm`, `SigP_*`/`SigC_*`/`W1_*`/`W2_*`.

**PITFALL — page-index drift after content edits:** the overlay script hardcodes page
indices (P_A, P_B, P_D, P_D3, P_SD, P_SE, P_E4). ANY content edit that changes
pagination (e.g. adding the B.2 under-construction note pushed Schedules D/E down one
page) silently drops fields — observed 82 → 64 widgets with SD_units/E1_s1/E4_confirm
missing. Always re-detect page indices by searching PART/SCHEDULE markers before
re-running the overlay:
```python
for i, pg in enumerate(doc):
    for needle in ['PART D', 'D.3 Signature', 'SCHEDULE D', 'E.1 Empanelment', 'E.4 Declaration']:
        if pg.search_for(needle): print(i, needle)
```
Then edit the P_* constants to match. Verify widget count + must-have names after
every rebuild (64 unique names should still be 82).

## Deliverables / delivery

- Branded PDF (navy/gold DRA palette, logo badge) + editable DOCX companion; DOCX
  built by the structural HTML→python-docx converter (skips the graphic cover by
  design — tell the user so they don't report it as a bug).
- Fillable PDF replaces the static one; upload/update in place via Drive
  `files().update` with same file IDs so share links survive; verify perms
  (anyone-reader + owner), md5 readback, then give the links.
- 21 pages (20 after spacing fixes) for the Udaya build; 21 for Amber after the
  under-construction note; uniform margins, no blank/orphan pages, all table rows
  keep-together.