# MagicBricks Leads → Camp / "teller talk" Upload Format

Bharat's recurring monthly request: pull ALL MagicBricks leads from the mailbox
for a period (e.g. "month of August") and produce a file in the Camp upload
format, which he calls "teller talk" (voice-transcription of the upload target).

## Target format (Camp sheet convention)
- Sheet: `Camp_Magic_Client_WhatsApp_List_updated (1)` — tab `Clients`
  - ID: `1eaOfED6TDNb3RnBkoj4ya4tH7gvLzrY_wiXa1KAXJaM`
- Two columns ONLY: **Lead** (contact name) | **Contact** (phone as `91XXXXXXXXXX`, no `+`, no spaces)
- Header row 1; data from row 2. This is the WhatsApp bulk-upload / teller-talk list format.

## Gmail query
```
(from:magicbricks.com OR from:magicbricks) after:2026/07/31
```
(adjust `after:` for the requested window). Use `service_name='google-draas'`
with `tools.gws_auth.build_service('gmail','v1', service_name='google-draas')`.

## Email format (as of Aug 2026) — parse these fields from BODY, not subject
Subject: `Buyer has contacted you on Magicbricks for - Residential Plot for sale in Sarjapura`
Body (text after stripping HTML):
```
Sender's Name: Dariavali (Individual) Mobile: 8147009212 Email: dariyavali.sk@gmail.com
Message: I am interested in your property...
```
Regexes:
- name: `Sender's Name:\s*([A-Za-z .'\-]+?)\s*\(([^)]*)\)`
- phone: `Mobile:\s*([6-9]\d{9})`
- email: `Email:\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})`
- property id: `ID\s+(\d+):` and description: `ID\s+\d+:\s*([^,]+?)\s*,`
- subject contains `has contacted you` → it IS a lead email (also `Hot Lead - ...` prefix variants)

**PITFALL — old parse patterns are stale.** Earlier sessions parsed a different
body format (`Name: X / Phone: Y` or subject-anchored `X has contacted you on
Magicbricks`). The current emails use `Sender's Name:` / `Mobile:` / `Email:` in
the body. Always debug on 2-3 raw bodies first before bulk parsing.

**PITFALL — Date header trailing space.** Gmail `Date` header is
`Sat, 8 Aug 2026 16:25:43 +0530 (IST)`. `date[:25]` includes a trailing space
(`'Sat, 8 Aug 2026 16:25:43 '`) which breaks `strptime("%a, %d %b %Y %H:%M:%S")`.
Use `date[:25].strip()`.

## Dedupe
- Primary key: phone. If no phone: email (lowercased). Else msg_id.
- Filter to requested month: `d.year == 2026 and d.month == 8`.
- Exclude leads with no phone from the Camp file (upload needs contact numbers);
  report the count + names of excluded ones to the user.

## Excel build
- openpyxl may be missing from the sandbox/hermes venv. Fix:
  `uv pip install --python /opt/hermes/.venv/bin/python openpyxl`
  (then run the build script with `/opt/hermes/.venv/bin/python`).
- Output: `/data/hermes/cron/output/MagicBricks_Leads_<Month><Year>_CampFormat.xlsx`
- Sheet name `Clients`, columns `Lead | Contact`, freeze panes A2, autofit widths (A≈30, B≈16).
- Always deliver via `MEDIA:<path>` plus a summary (count, window, projects, excluded).

## Session flow observed (Aug 2026)
78 MagicBricks emails since Aug 1 → 72 in August → 55 unique → 54 with phone → file.
Projects seen: Sarjapura plots (ID 84675109), Bagalur Sarjapur Road (84608849),
Bangalore (84653835), Hosur Road (85116917), Bagalur Road (85117141/85117007).
