---
name: vendor-product-research
description: "When the user asks 'does this SaaS/hardware product do X', 'how does product Y work', 'can we integrate vendor Z with our CRM', or 'is data tied to one device or cloud' — research a third-party product's deployment model, data flow, and integration surface, then write a clear buy-or-integrate assessment. Use when the user names a specific product (Truein, Keka, Darwinbox, a biometric device, a POS terminal, an IoT sensor) and wants to know what it does, where the data lives, and how to plug it into something else. Trigger phrases: 'research [product]', 'how does [product] work', 'can [product] integrate with [our system]', 'is it cloud or on-prem', 'does the API push to CRM', 'device vs cloud', 'multi-device registration'."
version: 0.1.0
metadata:
  hermes:
    tags: [research, vendor, saas, due-diligence, api, integration, india, real-estate, biometric, iot, crm]
    category: research
---

# Vendor Product Research

A class-level skill for "is this third-party product fit for our use, and if so, how do we plug it in?" — distinct from `primary-source-tracing` (which chases *one claim* to *one source*) and from `regulatory-complaint-escalation` (which is about filing complaints, not buying software).

## When to load

- User names a specific product (SaaS, hardware, hybrid) and asks:
  - "What does it actually do / how does it work" (deployment model, data flow, device vs. cloud)
  - "Is data locked to one device or shared across many" (single-device vs multi-device registration, biometric template storage)
  - "Can it integrate with our CRM / HRMS / payroll" (API surface, push vs pull, webhooks, FTP, custom integration)
  - "Should we buy it / what tier / what are the gotchas"
- User says: "research [product]", "look into [vendor]", "is [product] cloud-based or device-based", "does [product] have an API", "can we push [product] data into [our system]".
- Adjacent: comparing two or three vendors on the same axes (often follows an initial research — user asks "and what about Keka vs Truein?").

## What "good output" looks like

A short report (4–6 sections, ~400–700 words) that answers **the three questions the user always actually wants answered**, in this order:

1. **Single-device vs multi-device** — when a product claims "biometric / face / fingerprint / IoT registration", does the user get bound to one piece of hardware, or is the template + master record in the cloud so the same person works on any approved device? Cite a specific marketing or API page that confirms it.
2. **Where the data lives** — on the device, on-prem at the customer, vendor cloud, or hybrid? Look for phrases like "Cloud based", "Offline Attendance with Auto Sync", "data is stored on the device and syncs automatically". Confirm by checking the punch/event records themselves — if each record carries a `deviceId` / `inDevice` / `outDevice` field, the architecture is multi-device + cloud-centralised.
3. **API surface for integration** — does the product expose a public REST API (vs. only Zapier, vs. only file export, vs. nothing)? What auth (OAuth2 client_credentials is the modern norm)? What endpoints cover the user's actual use case (punches out, employee master sync, push events in)? Is there a `Subscription-key` + `Bearer token` dance, or just one credential?

End with a **"Bottom line for [our use case]"** section that names the user's specific scenario (e.g. "for DRAAS: push site attendance into Kelsa") and recommends an integration path (poll endpoint X daily, or ask vendor for custom connector, or build a small script).

## Research workflow

### Step 1 — Start with the product's own site
Hit the homepage, then the obvious product pages (search the sitemap if there is one). Strip scripts/styles, grep for the three question keywords (`device`, `register`, `template`, `cloud`, `sync`, `multiple`, `Kiosk`, `kiosk`, `face ID`, `API`, `FTP`, `push`, `offline`).

```bash
curl -sL -A "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36" "https://www.<vendor>.com/" -o /tmp/<vendor>_home.html
curl -sL -A "Mozilla/5.0" "https://www.<vendor>.com/sitemap.xml" -o /tmp/<vendor>_sitemap.xml
```

Try common paths in a loop:
```bash
for url in "https://www.<vendor>.com/integrations" "https://www.<vendor>.com/pricing" "https://www.<vendor>.com/product" "https://www.<vendor>.com/devices" "https://www.<vendor>.com/api" "https://www.<vendor>.com/kiosk"; do
  status=$(curl -sL -A "Mozilla/5.0" -o /dev/null -w "%{http_code}" --max-time 10 "$url")
  echo "$status  $url"
done
```

### Step 2 — Always check `developer.<vendor>.com` and `api.<vendor>.com`
For SaaS with any claim of an API, the developer docs are usually at a predictable subdomain. Even if not linked from the marketing site, `developer.<vendor>.com` typically returns 200 with a Redocly / Swagger UI page. **This is the highest-signal page** — it tells you:
- Exact endpoint paths (`/connect/token` for OAuth, `/apis/ext/attendance/v1.0/inOutDtls` for punches, etc.)
- Auth method (look for `access_key_id` + `secret_access_key` + `grant_type: client_credentials`, or a `Subscription-key` header, or both)
- Schema (look for response samples — they tell you what fields each record carries, which tells you the data model)
- Whether punches / events carry a `deviceId` field (proof of multi-device architecture)

### Step 3 — When the browser is down: terminal + Python is fine
If `browser_navigate` returns a "Camofox not running" error, do not give up. `curl` with a real User-Agent and `python3 -c "import re; ..."` to strip tags is fast and works for documentation-grade sites. The `scripts/scrape_docs.py` helper in this skill does the cleanup in one shot.

### Step 4 — Quote, don't paraphrase
When you find a sentence on the vendor's own page that directly answers the user's question (e.g. "Staff can onboard by showing their face on the kiosk or with a single selfie using their mobile. Onboarded staff can be immediately sent to multiple clients without the need for any re-onboarding at the client site."), quote it with a > block and cite the URL. Marketing copy is sometimes the most reliable source for "what does the vendor claim", which is what the user wants to know.

### Step 5 — One-line confidence check
End with a sentence that says what you directly verified vs. what you inferred. E.g. "Verified by hitting `developer.truein.com` (returned full OpenAPI spec) and `dailyAttendanceLog` response sample (carries `inDevice` and `outDevice`). Inferred multi-device usability from the marketing claim + the presence of the `addKioskDevice` API endpoint."

## Pitfalls

- **Don't trust only the homepage.** The home page is full of positioning language ("AI-powered", "robust", "seamless"). The product pages and developer docs are where the actual architecture is described. Always read at least one of: pricing page, integrations page, developer docs.
- **Don't infer from "Zapier integration" that there's a real API.** Many products claim to integrate with "1000+ apps" via Zapier/Make without exposing any actual API. Check for `developer.<vendor>.com` and look for `OAuth2 client_credentials` or `API key` auth — if neither appears, the product has no real API surface and the user's CRM-push question is a sales conversation, not a code one.
- **Don't fabricate the API spec.** If `developer.<vendor>.com` is down or 403s, say so. Do not write plausible-looking endpoint paths from memory. The user will try to call them and waste a day.
- **Offlined devices ≠ cloud central.** "Offline support" only means punches buffer locally and sync later — it does NOT mean data is locked to that device. Confirm by checking the API response for device IDs.
- **`Subscription-key` + `Bearer token` = two credentials, not one.** Many modern APIs (Truein, UKG, some Microsoft Graph surfaces) require both: an OAuth2 access token in `Authorization: Bearer …` AND a per-account `Subscription-key` header. Missing the second gives a misleading 401.
- **"Custom integration" = a sales call.** When the vendor's integrations page says "Don't see your payroll? We do custom integration. Talk to us", the user is being told to email sales, not to expect a self-serve API. Note this in the "Bottom line" so they don't waste time looking for a non-existent endpoint.
- **Browser tool may be unavailable in this environment.** `browser_navigate` can return "Cannot connect to Camofox". Don't assume browser-only — go straight to `curl` if you see that error.
- **Don't open gated PDFs with synthetic data.** Knight Frank / JLL / Colliers / Anarock / vendor whitepapers behind email gates will spam the address you register. Always ask the user before filling a form on their behalf.
- **Quoted research ages fast.** Vendor pages change. The reference docs in this skill are a snapshot — re-fetch before relying on them for a fresh vendor decision.

## Support files
- `references/truein-biometric-research.md` — full reference research dump from a 2026-07-13 session on Truein (biometric attendance, kiosk, multi-device, API). Read this as a worked example when the next vendor-research task lands.
- `scripts/scrape_docs.py` — drop-in helper to fetch + strip a vendor's marketing and developer pages. Pass a list of URLs and a keyword list; returns matching context snippets ready to drop into a report.

## Related skills
- `primary-source-tracing` — for chasing *one* claim to *one* source. Different shape (this skill maps an entire product).
- `regulatory-complaint-escalation` — sometimes a vendor-research report leads to "this vendor is non-compliant, escalate to regulator"; that skill owns the second half.
- `regulatory-complaint-escalation` also lives in the same DRAAS-vendor-evaluation orbit (e.g. investigating an insurer's grievance policy before escalating).
