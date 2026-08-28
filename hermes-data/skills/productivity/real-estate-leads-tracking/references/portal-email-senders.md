# Portal Email Senders — Verified Reference (June 2026)

Verified `from:` addresses, subject prefixes, and body patterns for the real estate portals that send leads to DRAAS (`sales1.blr@draas.com` / `ndr@draas.com`).

## MagicBricks

- **Sender:** `MagicBricks <info@magicbricks.com>`
- **Alert sender (separate):** `MagicBricks <alerts@magicbricks.com>` — these are "your listing is going stale" reactivation pings, NOT leads. Filter them out by checking for `Buyer has contacted you` in the subject.
- **Lead subject prefix:** `Buyer has contacted you on MagicBricks for - `
- **Subject example:** `Buyer has contacted you on MagicBricks for - Residential Plot for sale in Sarjapura`
- **Body content:** Buyer's email + 10-digit phone in plaintext; property name + city in the subject. Buyer NAME is usually NOT included in the body.
- **Volume observed (Jun 2026, Ranka Udaya, sales1.blr@draas.com):** 89 raw lead emails in 30 days → 59 unique leads after email/phone dedup
- **Self-lead contamination:** Bharat's own sales number (9900029200, khanbt@gmail.com) sometimes appears as a "buyer" — see PITFALL #3 in SKILL.md for the blocklist pattern
- **Dedup key:** email (most stable). Phone as fallback.

## Housing.com

- **Sender:** `"Housing.com" <noreply@housing-mailer.com>`
- **Lead subject prefix:** `New Lead For [Project Name]`
- **Subject examples:**
  - `New Lead For DRA Ranka Udaya`
  - `New Lead For DRA Ranka Palm Lakeside`
- **Body content:** Name, property type, budget. **NO email/phone** — those are behind the partner portal login.
- **Body example:**
  ```
  <Name> would like to talk to you
  Hi Bharath, We have received a contact request from our user:
  Name: <Full Name>
  Email: Send Email
  Contact: Call Now
  Chat On WhatsApp
  who would like to talk to you regarding your Under Construction Plot property with budget in range 48.0 Lac - 48.0 Lac.
  DRA Ranka Udaya - Sarjapur Bagalur Road
  Price Plot ₹ 48.0 L onwards | Residential Plots
  ```
- **Volume observed (Jun 2026, Ranka Udaya):** 22 lead emails in 30 days
- **Dedup key:** Name + project (no email/phone available)

## 99acres

- **Sender:** `99acres <noreply@99acres.com>` (sometimes `leads@99acres.com`)
- **Lead subject prefix:** `New lead for` / `You have a new inquiry`
- **Body content:** Buyer name, email, phone usually present
- **Volume observed:** Not yet measured for DRAAS — add when first session uses this portal

## CommonFloor

- **Sender:** `CommonFloor <noreply@commonfloor.com>`
- **Lead subject prefix:** `New Lead:`
- **Body content:** Buyer name, email, phone usually present

## NoBroker

- **Sender:** `NoBroker <noreply@nobroker.in>`
- **Lead subject prefix:** `New response for`
- **Body content:** Phone usually present; email sometimes missing

## Internal/operational emails to filter out (NOT leads)

When pulling leads, these are noise — don't include them in the lead table:

- **MagicBricks reactivation alerts** — from `alerts@magicbricks.com`, subject contains `wants to be seen`, `Let buyers see`, `Reactivate your`
- **MagicBricks image approval** — from `info@magicbricks.com`, subject is `Images Approved` / `Images Screened`
- **MagicBricks new listing confirmation** — subject contains `Thanks for posting the Property ID`
- **Housing.com drone / microsite** — from `jagadish.kumar@housing.com` / `anil.raghuwanshi@housing.com` / `jeet.kumar@housing.com`, subjects contain `Drone interactive`, `Microsite`, `Opportunity#`

**Tell-tale filter:** A real lead email addresses the recipient as `Hi Bharath,` (or first name) and contains the phrase `We have received a contact request` (housing.com) or `Buyer has contacted you` (MagicBricks). Anything without those is operational.
