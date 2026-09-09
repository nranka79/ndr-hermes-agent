# GWS auth: service key is derived from the email DOMAIN (resolved)

Date: 2026-09-09. Fixed same-day for Sarthak Sharma (admin3.blr@draas.com).

## Resolution
The OAuth callback NO LONGER derives vault service keys from the email
local-part (which produced wrong keys like `google-admin3-blr`). Since
2026-09-09 the service key is derived from the account's email DOMAIN via
`tools.gws_auth._service_for_email()`:

- any @draas.com account  -> `google-draas`
- any @ahfl.in account    -> `google-ahfl`
- any @gmail.com account  -> `google-gmail`
- any other @domain       -> `google-<registrable-domain>`

So admin3.blr@draas.com now files under `google-draas`, the SAME key as every
other draas.com account. A brand-new @draas.com user needs NO registration,
NO mapping, and NO manual rename.

## Symptoms of the old bug (historical)
- `gws_resolve_account` returned `has_token: false` for all well-known
  services while a token actually existed under a local-part fallback key
  like `google-admin3-blr`.
- `gws_fetch_token(service_name="google-draas")` errored with
  `No google-draas token for user ... Authorize first.` — a false negative.

## What to do if a token ever appears under a wrong service key
1. Derive the expected key from the email domain (`google-<registrable-domain>`).
2. Confirm the token location via `list_services` / `gws_resolve_account`.
3. If it is under a legacy wrong key, the vault copy is safe — rename the
   token file (+ `.meta`) to the domain-derived key, or re-authorize
   (the callback now files it under the correct key automatically).
4. Do NOT tell the user to re-authorize based only on a missed key —
   verify the actual service list first.