# Indian Government Officer Contact Lookup

**Trigger:** User asks for contact details (name, phone, email) of a specific Indian government officer — District Registrar, Joint Registrar, DEO, Tahsildar, Sub-Registrar, etc.

**Class of task:** Find the phone/email/name of a government officer at the district or state level, in India, from official sources.

## Core architecture: District vs State department

Indian government officer contact info is split across **two entirely separate systems**. Confusing one for the other is the #1 failure mode.

### Level 1 — District Administration (district .nic.in)

- **Who is listed:** Collector, Superintendent of Police, District Revenue Officer (DRO), District Forest Officer, etc.
- **Source:** `https://<district>.nic.in/about-district/whos-who/`
- **Example:** `krishnagiri.nic.in/about-district/whos-who/` → Collector C Dinesh Kumar IAS (04343-239400, collrkgi@nic.in), SP Tmt G.S. Anitha IPS (9498168000), DRO Tmt T. Manjula (04343-231300, dro.tnkgi@nic.in)
- **URL pattern:** `<district>.nic.in/about-district/whos-who/` — sometimes `/resources/whos-who/` redirects there
- **Accessibility:** Usually reachable from a VPS (no geo-block)

### Level 2 — State Department (state.gov.in or department portal)

- **Who is listed:** District Registrar (Registration Dept), Joint Registrar of Co-operative Societies, District Educational Officer, AD Welfare, Joint Director of Health, etc.
- **Source:** The STATE department's portal, NOT the district nic.in site
- **Example:** TN Registration = `tnreginet.gov.in/portal/districtwise_contact.jsp` (geo-blocked from datacenter IPs)
- **Accessibility:** Often geo-blocked / unreachable from VPS datacenter IPs. The portal is designed for Indian citizens on Indian networks.

## Diagnosis ladder

1. **Identify the department:** Is this a district administration officer → Collector, DRO, SP? → Level 1 (district .nic.in whos-who).
   Is this a state department officer (District Registrar, DR of Co-op, DEO, JT Director, etc.)? → Level 2 (state department portal).

2. **State department search:** If Level 2, try:
   - `web_search` for `<state> <department> contact` or `<state> <department> <district> officer`
   - Browser navigate to the state department's known portal URL
   - Jina reader (`r.jina.ai`) to fetch the state department contact page

3. **If portal is geo-blocked** (TCP timeout, ERR_TUNNEL_CONNECTION_FAILED, 502 WAF proxy error):
   - Do NOT loop retries — hand off to the user's Indian-IP phone
   - Suggest the user call the DRO office (their contact IS on the district whos-who) — they can connect to the department

4. **If no official source accessible:** The DRO's office is the best local escalation path. They know who the state department officers are in the district.

## Verified failure modes (Aug 2026)

| Source | Status from VPS (Aug 2026) |
|--------|---------------------------|
| krishnagiri.nic.in | ✅ Reachable — whos-who has Collector, SP, DRO |
| tnreginet.gov.in | ❌ SOCKS connection failed / TCP timeout |
| tn.gov.in | ❌ SOCKS connection failed |
| Google SERP | ❌ CAPTCHA (unusual traffic) |
| Bing | ❌ Anti-bot junk content |
| DuckDuckGo html | ❌ Block page |
| Tavily | ❌ 432 Payment Required |
| Smart Browser | ⏱ Timeout |
| Browser Use Cloud | ❌ Insufficient credits ($0.02) |
| Wayback Machine CDX | ⏱ Empty / timed out |

## What actually worked this session

- **krishnagiri.nic.in** — browser navigate to whos-who page confirmed Collector/SP/DRO
- **DRO office as referral path** — suggested calling 04343-231300 to connect to Registration Dept
- **Ashlar Law / KHR Chambers** — they do TN property due diligence and would have the DR's direct contact

## Template message for user

> "The District Registrar doesn't appear on the district website (krishnagiri.nic.in) — only the Collector, SP, and DRO are listed there because the Registration Dept is a state-level body. The TN Registration portal (tnreginet.gov.in) has the DR contact but is geo-blocked from this server. Two options:
> 1. Call the DRO's office at **04343-231300** — they can connect you to the DR's office
> 2. Your law firm (Ashlar Law / KHR Chambers) likely has the DR's direct contact from their TN registration work"