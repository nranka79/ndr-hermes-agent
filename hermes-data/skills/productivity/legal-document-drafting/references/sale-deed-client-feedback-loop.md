# Sale Deed — Post-Review Client Feedback Loop

**Trigger:** Client (Nishant/DRAAS) gives clause-by-clause feedback after receiving a sale deed review.

## Workflow

```
Phase 1: Present Review
  → Deliver clause-by-clause analysis (issues found, RERA gaps, risks)
  → Use structured format: Clause #[X] — Issue — Recommended Fix

Phase 2: Receive Client Feedback (voice message, typically)
  → Client addresses each clause with corrections/preferences
  → May also introduce new terms not in original review

Phase 3: Confirm Understanding
  → Summarise ALL feedback back to client in structured format
  → Use same clause numbering as original review
  → Flag anything ambiguous or unclear
  → Wait for explicit confirmation ("this is correct") before proceeding

Phase 4: Draft Advocate Response
  → Incorporate all client corrections into final clause suggestions
  → Include exact suggested wording changes where possible
  → Structure as a response addressed to the advocate/lawyer (e.g. Piyush)
  → Deliver via WhatsApp (see delivery section below)
```

## Delivery to Advocate

For long legal responses (500+ words, 4+ paragraphs):

1. **First check:** Will it fit in a single wa.me URL?
   - wa.me URL length limit = ~4096 chars total
   - Message body must be short enough after URL encoding
   - Keep under ~2000 chars of message text for safe margin

2. **If short enough:** Generate `api.whatsapp.com/send?phone=...&text=...` link with:
   - Bold caption using `*...*` WhatsApp markdown
   - Full-width ampersand `＆` (U+FF06) replacement BEFORE encoding
   - Phone as `91XXXXXXXXXX` (no `+`)

3. **If too long:** Generate HTML card
   - Write to `/data/hermes/cron/output/whatsapp-{contact}-{topic}.html`
   - Card contains wa.me link with full encoded text
   - Deliver via `MEDIA:` path
   - See `messaging-drafts` skill → "Long Messages — HTML Card Fallback"

## Specific RERA Knowledge — OC-Closed Projects

When the project has ALREADY received Occupancy Certificate (OC):

### Clauses NOT needed (project closed, OC received):
- **~70% carpet area price clause** — Not required post-OC
- **Separate RERA account clause** — Project funds already deployed
- **Escalation-free pricing** — Already determined
- **Dispute resolution under RERA** — Standard civil remedies suffice
- **Conveyance timeline** — Sale deed itself conveys title

### Clauses that ARE needed:
- **Fire OC + Fire CC** — Reference the received fire completion certificates
- **Structural Stability Report** — Reference with consultant name and date
- **Deed of Declaration / Deed of Adherence** — Under Karnataka Apartment Ownership Act
- **Defect Liability** — As per RERA (5-year, not more)
- **Undivided Share** — Total site area ÷ total SBUA (placeholder OK)

### Defect Liability Nuances (Nishant's approach, June 2026)

**Core principle:** Reference RERA defect liability period without explicitly stating "5 years". Keep it vague but legally grounded:

> "Defect liability shall be as provided under RERA. Once the sale deed is registered, association is formed, all common amenity documents and maintenance corpus are handed over with up-to-date accounts and NOC obtained — the promoter's obligations are discharged except where RERA continues to impose liability."

**Equipment:** Lifts, generators, and other machinery — cover under manufacturer warranties and guarantees, not under builder defect liability.

**Basement CPH (Seepage):** Add technical language that:
- Water has been diverted via engineering measures
- Minor CPH/seepage at Basement 3 is natural and expected
- Will require continuous dewatering and management
- Not a defect — it's normal for the water table conditions

**Minor wear:** Cracks, shade differences, minor chips — state as normal wear & tear. Defects at time of delivery covered by snag list under RERA.

### Carpet Area Definitions (Nishant's tri-categorization, June 2026)

Always provide THREE values in the sale deed:

| Category | Definition | Source |
|----------|------------|--------|
| **RERA Carpet Area** | As defined under RERA (excludes external walls, balcony, etc.) | OC / Sanctioned Plan |
| **Usable Carpet Area** | RERA Carpet Area + exclusive lobby + balcony | Developer's measurement |
| **Super Built-up Area** | Includes common areas, staircase, lifts, etc. | Sale deed / previous agreements |

Both "Usable Carpet Area" and "Super Built-up Area" lack statutory definitions — address this in the deed by stating they are developer-defined for commercial disclosure, while RERA Carpet Area is the statutory metric.

### OC Deviations — How to handle

**DO NOT** declare specific deviations in the sale deed. Instead:

> "OC has been received (OC No. [X], dated [Y], issued by [Authority]). The as-built drawing has been submitted to [Authority] per OC requirements. Minor permissible deviations under law have been accepted as part of the as-built drawing and OC. As-built drawings will be handed over to the Association upon formation under the Deed of Declaration. Each purchaser may obtain a set of as-built drawings upon request."

Key points:
- Never enumerate what the deviations are
- Reference "minor permissible deviations under law"
- State SBUA hasn't changed materially
- Acknowledge minor common area changes (extra store room) without specifics

### Fire Clearance Clauses

Reference BOTH:
- Fire Occupation Certificate (Fire OC) — received
- Fire Completion Certificate (Fire CC) — received
- Look up the actual document numbers from Drive before finalising

### Car Parks

Include a dedicated section specifying:
- Number of car parks allotted to the apartment (typically 2)
- Specific car park numbers/identifiers
- Car park plan as an annexure with the allotted spot(s) shaded
- Exclusive right of use language

### Structural Stability Report

Include a clause referencing:
- Report received from [Consultant Name]
- Dated [Date]
- Available for purchaser's review

## Contact Search — When Client Says "It's in My Contacts"

When Nishant says "his number is in my contact sheet / Google Phone":
1. Search the NDR DRAAS Google Contacts sheet (gws_sa for sheets)
2. Search Google People API (gws_auth for people/v1)
3. Try MULTIPLE name variations — voice transcriptions can mishear names
4. If still not found after trying 3+ variations, ask the client for the number directly — but only as last resort
