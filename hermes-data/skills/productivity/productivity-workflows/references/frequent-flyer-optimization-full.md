---
name: frequent-flyer-optimization
description: "Research airline frequent flyer programs, alliance structures, and credit card transfer partners to recommend the best mileage program for an Indian traveler. Covers: flight history analysis from Gmail, mileage program comparison, alliance mapping (Star Alliance/Oneworld), retro-credit claims, and credit card point transfer strategy."
version: 1.0.0
author: Nous Research / DRAAS
license: MIT
metadata:
  hermes:
    tags: [airlines, frequent-flyer, miles, loyalty, alliance, credit-card-points, travel]
    homepage: https://github.com/NousResearch/hermes-agent
    related_skills: [google-workspace, equity-research]
---

# Frequent Flyer Optimization Skill

When a user asks to find their flights and recommend a single airline mileage program to collect all their miles — this is the skill that handles the full workflow.

## When to Load This Skill

Trigger phrases:
- "find my flights" / "check my flight history"
- "frequent flyer program" / "mileage program" / "airline miles"
- "which airline should I collect miles with"
- "credit card points transfer" + "airline"
- "claim my miles" / "retro-credit"
- "alliance" + "airline"

## Workflow

### Phase 1 — Flight Discovery (Gmail)

**Step 1.1 — Search multiple accounts**
User may have flight bookings across multiple email accounts (draas.com, drahomes.in, ahfl.in for travel agents). Check forwarded bookings too.

**Step 1.2 — Use airline-specific search patterns**

Each airline has a characteristic sender address:

| Airline | Confirmation sender | Notes |
|---------|--------------------|-------|
| IndiGo | `reservations@customer.goindigo.in` | PNR in subject like "Your IndiGo Itinerary - UF9SME" |
| Air India | `eticket@airindia.com`, `noreply-notification@airindia.com` | e-tickets have PNR in subject |
| Air India Express | `boardingpass@transaction.airindiaexpress.com` | Boarding pass only |
| Malaysia Airlines | forwarded from `ndr@ahfl.in` (travel agent) | Not from malaysiaairlines.com directly |
| Japan Airlines | `info.gst@jal.com` | GST invoices are the ticket evidence — no separate booking email |
| Singapore Airlines | `flightsearch@email.singaporeair.com` | Marketing/search save — not actual bookings |
| Emirates | `do-not-reply@emirates.email` | Booking ref like "Your booking is confirmed - IKP6UB" |
| SpiceJet / GoAir | check standard patterns | Less frequent flyer value |

**Step 1.3 — Search queries that work**

```
# Recent flight bookings (any airline)
(subject:PNR OR subject:flight confirmation OR subject:e-ticket OR subject:itinerary) newer_than:365d

# Japan Airlines — use full name, NOT "JAL" alone
"Japan Airlines" after:2025/05/01

# JAL GST invoices (often all you get for JAL)
from:info.gst@jal.com

# Air India family booking
subject:JBUV4Z

# Malaysia Airlines via travel agent
from:ahfl.in subject:DVAZVS
```

**Step 1.4 — Extract PDF invoices**

For JAL, the GST invoice PDF contains the flight evidence:
- Download via Gmail attachments API
- Extract: `pdftotext -layout invoice.pdf -`
- Key fields: PAX Name, Date of issue, Ticket No. (not PNR), Amount

**Step 1.5 — Compile flight table**

For each flight found, record:
- Date
- Airline
- Route (city pairs)
- Class of travel
- PNR / Ticket number
- Passenger(s)

---

### Phase 2 — Alliance Mapping

**Key Alliances**

| Alliance | Members relevant to Indian travelers |
|----------|-------------------------------------|
| **Star Alliance** | Singapore Airlines (KrisFlyer), Air India, Malaysia Airlines (Enrich), Thai Airways (Royal Orchid Plus), Lufthansa, ANA, EVA Air, Asiana |
| **Oneworld** | Japan Airlines (JAL Mileage Bank), Cathay Pacific (Asia Miles), British Airways (Executive Club), Qantas, Malaysia Airlines (Enrich — also Star Alliance) |
| **SkyTeam** | Vietnam Airlines, Korean Air, China Airlines, Delta, Air France/KLM |

### Critical: IndiGo Has No Alliance

**IndiGo (6E) is NOT part of any airline alliance and has no frequent flyer partnerships with global programs.** Its internal program (6E Rewards) cannot be credited to Star Alliance, Oneworld, or SkyTeam. This means:

- BLR→Colombo flights on IndiGo earn **zero usable miles** in any global program
- Domestic IndiGo flights earn **zero usable miles** in any global program
- This can affect 40–60% of an Indian traveler's flying if they rely heavily on IndiGo

**Implication for recommendation:** If the user flies IndiGo frequently on routes to Colombo or Bangkok, those flights are structurally un-creditable. The mileage program recommendation must be made on the flights that CAN be credited (Air India, Malaysia Airlines, Singapore Airlines, Thai Airways) — not on what the user wishes they could credit.

---

### Phase 3 — Mileage Program Recommendation

**Step 3.1 — Score programs by user's flight pattern**

For each airline the user flies:
1. Identify which alliance(s) it belongs to
2. Identify which programs accept credit from that airline
3. Score by:
   - Number of partner airlines that can credit here
   - Credit card transfer availability (from Indian cards)
   - Redemption options for user's geography (SE Asia, Far East)
   - Expiry rules

**Step 3.2 — Single best program logic**

For an Indian family traveling primarily to **SE Asia and Far East**, with some domestic India flights and occasional Europe:

**Winner: Singapore Airlines KrisFlyer (Star Alliance)**

Rationale:
- Malaysia Airlines (their Bali flights) → credit to KrisFlyer
- Air India (Star Alliance) → credit to KrisFlyer
- Singapore Airlines itself → KrisFlyer is the native program
- Thai Airways (Star Alliance) → credit to KrisFlyer
- Most Indian credit cards with airline transfer partners include KrisFlyer

**Runner-up options:**
- **Air India Flying Returns** — native to Air India, but limited credit card partners
- **JAL Mileage Bank** — best for Japan-only travel, Oneworld
- **Cathay Pacific Asia Miles** — strong for Far East, but user doesn't fly Cathay

---

### Phase 4 — Credit Card Transfer Analysis

For IndusInd Bank Indulge (user's card):
- 5 pts / ₹100 on international spend (best among Indian premium cards)
- Check reward portal for airline transfer partners
- Typical transfer: 1:1 or 2:1 to KrisFlyer, Cathay, JAL

**For a future session:** When user switches to HDFC / ICICI premium cards, research AXIS ICICI credit card avios transfer partners.

---

### Phase 5 — Retro-Credit Claims

Most airlines allow claiming miles up to **12 months** after travel date.

**Action checklist when flights are found:**
- [ ] Enroll in the recommended program (if not already)
- [ ] Submit retro-credit claim at airline website with PNR/ticket number
- [ ] For JAL: visit jal.com/jalmileagebank
- [ ] For Malaysia Airlines: visit malaysiaairlines.com/enrich
- [ ] For Air India: visit airindia.com/flyingreturns

---

### Critical: KrisFlyer Enrollment Requires Manual Verification — NOT Automatable

**Singapore Airlines KrisFlyer enrollment CANNOT be completed programmatically.** The enrollment process requires:
1. **Email OTP** — a verification link sent to the applicant's email address
2. **SMS OTP** — a one-time password sent to the applicant's registered mobile phone
3. **Email verification link** — must be clicked within the activation window

This means: each family member must personally complete enrollment from their own email/phone. You cannot fill and submit the form on their behalf.

**What you CAN do programmatically:**
- Prepare all required information (name, DOB, passport, nationality, address) for each family member
- Research the enrollment URL
- Guide the user step-by-step

**What you CANNOT do:**
- Submit the enrollment form for another person
- Receive/verify OTPs sent to their email/phone

**Enrollment URL:** `singaporeair.com/in/enroll`

---

## Supporting Files

- `references/airline-alliance-map.md` — Full alliance member list, key program details, transfer ratios
- `references/indigo-colombo-route-finding.md` — Session notes on IndiGo BLR→Colombo (Jun 2024) finding, EaseMyTrip email retrieval, IndiGo alliance limitation confirmed
- `references/jal-flight-analysis.md` — Session notes on the Nov 2025 JAL tickets found for Ranka family
- `references/krisflyer-enrollment-process.md` — KrisFlyer enrollment flow, OTP requirements, why automation fails

## Pitfalls

1. **JAL has no booking confirmation email** — only GST invoices. The GST invoice IS the ticket. Look for `from:info.gst@jal.com` not `from:jal.com`.
2. **`from:@jal.com` is invalid in Gmail** — wildcard domains don't work. Use full sender address or phrase match.
3. **Malaysia Airlines bookings are forwarded** — the sender is the travel agent (ahfl.in), not malaysiaairlines.com directly.
4. **Miles CANNOT be transferred between programs** — each program is siloed. You cannot merge JAL miles into KrisFlyer. Choose ONE program per flight at time of credit.
5. **Indulge card transfer partners change** — always verify current transfer ratio in the IndusInd reward portal, not from older research.
6. **Business class tickets cost ~₹2L+ per person** — if the JAL tickets were ₹1.96L + GST each, they were business class. This earns significant miles.