# Kelsa Team Email Resolution (verified Aug 2026)

When Nishant dictates a Kelsa team member's name for a calendar invite ("Ashwin kelsa address", "Pawan Kumar kelsa address", "Agne kelsa address"), People API name-search alone FAILS to find most of them. Reliable resolution order:

## Steps

1. **People API `searchContacts` with the domain string `kelsa.io`** — not just the first name. People API matches email addresses too, so `query="kelsa.io"` returns every contact with a kelsa.io email in one shot (both google-draas and google-gmail accounts). This is the highest-yield query.
2. **Gmail search `from:<name>@kelsa.io` / `to:<name>@kelsa.io`** — finds people not in the address book at all (e.g. Aagney Singh was only in Gmail, not as a contact). Also `from:<firstname>` variants.
3. **Registry sheet** "NDR DRAAS Google contacts" (1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g) — good for name spelling (e.g. "Aagney | Singh" row 34), but the sheet columns are sparse; emails live in People/Gmail.

## Known Kelsa team (kelsa.io domain) — resolved Aug 2026

- Ashwin Hegde — ashwin@kelsa.io (also hashwin@o3infotech.com, ashwin.hegde12@gmail.com)
- S Pavan Kumar — pavan@kelsa.io (People API label: "Pavan Kumar O3")
- Aagney Singh — aagney@kelsa.io ← voice "Agne" resolves to Aagney, NOT "Agnes"
- Ajay Haridas — ajay@kelsa.io (ajayharidas9@gmail.com, ajayharidas@o3infotech.com)
- Vikramaditya H — vikramaditya@kelsa.io (h.vikramaditya@gmail.com)
- Umesh C N — umesh@kelsa.io
- Arnav Singh — arnav@kelsa.io
- Rupsa Das — rupsa@kelsa.io
- Tiara Mahdani — tiara@kelsa.io (Kelsa Dubai)
- Apoorv Gupta — apoorv@kelsa.io
- Kuntal Kumar — kuntal@kelsa.io
- Vishal Hemrajani — vishal@kelsa.io
- Guna — gunarka@kelsa.io
- Manohar Singh — msingh@kelsa.io

## Voice-alias pitfalls

- "Agne" → Aagney Singh (aagney@kelsa.io). People API query "Agne" only returns Agnes Chiu (Everstone) — a decoy.
- "Pawan Kumar" → S Pavan Kumar (pavan@kelsa.io). People API query "Pawan" returns Pawan Sawhney/Kodakandla/Sharma (non-Kelsa) — wrong people.
- These are Kelsa (CRM vendor) staff, distinct from DRAAS employees (psingh@draas.com, vkdas@draas.com, etc.).

## Build-service note

`gws_auth.build_service(api, version, service_name='google-draas')` — NO `telegram_id` kwarg (removed; passing it raises `unexpected keyword argument`). Resolve service_name via `gws_resolve_account` first.
