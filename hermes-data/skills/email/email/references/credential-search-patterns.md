# Credential / Password Recovery Search Across Gmail Accounts

Use when the user asks: "did X ever send me a password?", "find my login credentials
for Y in my mail", "check if the hosting company emailed the server password".
Goal: a definitive YES/NO backed by the actual vendor email text.

## Workflow

1. **Resolve accounts first.** Call `gws_resolve_account` (no args) to list every
   vault service + auth status. Known services: `google-gmail` = nishantranka@gmail.com
   (personal), `google-draas` = ndr@draas.com (work), `google-ahfl` = ndr@ahfl.in.
   The user says "all my emails" → search ALL three, not just the default.
   Programmatic invocation: `registry.dispatch("gws_resolve_account", {})` — note the
   `ToolRegistry` method is **dispatch()**, there is no `registry.call()`.

2. **Build a Gmail service per account** and run the query set:
   ```python
   from tools.gws_auth import build_service
   gmail = build_service("gmail", "v1", service_name="google-gmail")
   ```

3. **Query set** (dedupe message IDs across all queries — they overlap heavily):
   - `from:(vendor.com OR vendor.de OR robot@vendor.com)` — sender catch-all
   - `vendor` — anywhere in mail (proves total message count)
   - `vendor (password OR passwort OR credentials OR zugang OR "root password" OR "login credentials" OR "initial password")`
   - `subject:(vendor OR server) (password OR credentials)`
   - `vendor in:trash` and `vendor in:spam` — explicit proof of coverage for the report
     (plain Gmail search already includes Spam/Trash, but running these makes the
     "I checked everywhere" claim verifiable)

4. **Fetch metadata first, bodies only for suspects.** Get `format="metadata"` with
   From/To/Subject/Date headers for ALL matches, then pull `format="full"` bodies only
   for the few that look like they could carry credentials (setup/welcome/access emails).
   This keeps the run fast and the context clean.

5. **Body keyword flags** (bilingual — vendors mail in German too): `password`,
   `passwort`, `zugang`, `einloggen`, `credentials`, `root password`,
   `initial password`, `login details`, `server ready`, `deployed`.

6. **Conclude with the vendor's own wording.** Quote the exact email text that proves
   the answer (e.g. "Password: The password you created when creating your account").
   A bare "no password found" is weak; citing the sentence that says the password was
   never emailed is definitive.

## Vendor quirk: Hetzner (worked example, Aug 2026)

- NDR Hetzner account: client number **K0409884026**, login = nishantranka@gmail.com,
  created 29 Apr 2026 (emails from support@hetzner.com that day: "Your access details"
  + "Your account K0409884026").
- **Hetzner never emails real passwords.** The account-setup email's password field
  literally reads "The password you created when creating your account".
- **Hetzner Cloud never emails server/root passwords.** They are generated inside the
  Cloud Console (console.hetzner.com) and shown ONCE at creation; if lost, reset via
  the console (server → Rescue / "Reset root password"). Same model for dedicated
  servers in Robot. The access-details email promises "another email with login
  credentials for the server as soon as it has been deployed" — for Cloud, that email
  never comes; its absence is normal, not a delivery failure.
- **"Your Hetzner Verification Code is NNNNNN" emails are OTPs, not passwords.** They
  expire and are useless as credentials. Do not report them as "found a password".
- NDR's only Hetzner asset as of Aug 2026: Cloud Server #128476111 "ndr-playground"
  (seen in the Hetzner Status outage email 29 Jul 2026).

## Pitfalls

- `registry.call()` does not exist → use `registry.dispatch(name, args)`.
- OTP / verification-code emails are NOT passwords — flag them as what they are.
- Don't stop at the default (work) account when the user says "all my emails".
- Many vendors (Hetzner, AWS, Google Cloud) never email passwords by policy — when the
  user is hunting for a server password, the correct end-state is often "reset it in
  the provider console", and the email evidence supports that instruction.
