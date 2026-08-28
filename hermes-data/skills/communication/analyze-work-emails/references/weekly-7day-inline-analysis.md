# Weekly (7-day) Inline Analysis — verified pattern (17 Aug 2026)

Use when the ask is "analyze my work emails for the last week / N days" and you
want one clean pass instead of the bundled `analyze.py` (whose classifier still
flags Kelsa attendance reports, Royal Sundaram surveys, TCS iON / Apify /
smarterdharma marketing, and HDFC UPI alerts as NEEDS RESPONSE).

## Run this instead
```
/opt/hermes/.venv/bin/python3 /data/hermes/skills/communication/analyze-work-emails/scripts/weekly_analysis.py 7
```
Re-runnable script: direct Gmail API (`tools.gws_auth.build_service('gmail','v1', service_name=...)`),
list() pagination, thread reconstruction, noise-filtered, AWAITING/NEEDS/INFO output.

## Calibration (ndr@draas.com)
- 7 days, `in:inbox` + `in:sent` → **~450 unique messages**, ~220 after noise
  filter, ~165 threads. One pass per folder with `nextPageToken` pagination is
  fine — no two-window split needed below ~600 msgs/window.
- Runtime ~1–2 min via terminal (not execute_code). It runs in a subprocess fine
  because it uses `build_service`, not the bridge.

## Reading the output
- Redirect stdout to a file and read the top: `> /data/hermes/tmp/weekly_out.txt`
  — the NOISE section (Kelsa sign in/out can be 60+ lines) floods the tail.
- ACCOUNT_OK / ACCOUNT_FAIL lines go to stderr: a failed account means
  `invalid_grant` → send the `send_oauth_url` button and re-scan after auth
  (see below).

## Hand-curation rules (classifier over-matches)
- Any subject containing `fwd:` / `fw:` lands in NEEDS RESPONSE — forwards
  (invoice fwd, family/kids activity fwd, property-sale fwd) are usually FII.
  Present them under NEEDS RESPONSE only if the body asks for a decision.
- Vendor sends addressed to **info@draas.com** leak into AWAITING RESPONSE
  because NDR's address is in To: BLACKbox (Dinesh Ranka), Dell/Inflow laptops,
  Justdial listing, OBO Bettermann, REFCOLD awards. Filter by recipient address,
  not just sender domain — match `to:info@draas.com` and drop them.
- Calendar invites (Flameback, Kelsa Issue Discussion) carry 'Invitation:' in the
  subject — treat as watch/FII, not action.

## Multi-account note
Loop `build_service` per account. On `invalid_grant: Token has been expired or
revoked`, note that `gws_resolve_account` may STILL report `has_token: true` for
that service — the resolve flag is not proof of a live token. Send `send_oauth_url`
(button label = the account) and re-scan that account once the user authorizes.