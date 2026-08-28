# TN RERA (Tamil Nadu) Portal & Application Status Checking

**Trigger:** User asks to check the status of a Tamil Nadu RERA application/registration, or shares a TN RERA portal screenshot (application list, project row, "View Step 1/2/3" links) and asks what it means / wants live verification.

## Portal facts

- **Official portal: `https://rera.tn.gov.in`** (NOT `www.tnrera.in` — that is a parked domain; verify before deep-diving)
- Registered project listings: `/registered-building/tn` (building projects), `/registered-layout/tn` (plotted layouts)
- Contact: 044-2231 0989; 044-2232 1090
- **Access constraint:** portal geo-blocks non-Indian datacenter IPs at TCP level. From this server, every route fails (curl timeouts, browser ERR_TIMED_OUT/502 from their WAF, proxies fail). See `research-web-tools` → `references/indian-government-portal-geoblock-diagnosis.md` for the full diagnosis and hand-off pattern. When blocked: ask the user to open it on their phone (Indian IP) and share a screenshot, then interpret.

## Application number formats (as seen on the application list page)

| Field | Example | Meaning |
|-------|---------|---------|
| Application/PLI No. | `TNPLI31682026` | Portal application ID — `TN` + project type + sequence |
| RERA Ref | `TNRERA/PLI/3747/2026` | Registration reference — `TNRERA` / type / serial / year |
| Applicant | Nisant Ranka | Promoter/applicant name |
| Project | Ranka Oasis | Project name |

- `PLI` = plotted/layout-type application (Ranka Oasis is a plotted layout). Building projects use `BLG` (e.g. `TNRERA/29/BLG/0001/2026`).
- The row shows three `View Step` links — the application is in the multi-step processing workflow.

## Status ladder (plain-English interpretation)

| Portal status | Meaning |
|---------------|---------|
| **Application yet to verify by Scrutiny Officer** | Submitted and queued; scrutiny officer has NOT started reviewing. Pre-verification stage. Next milestone: scrutiny verification, then (objections) then approval/registration. |
| (After scrutiny) | Expect stages like verification, objections/compliance, then registration certificate. |

## Ranka Oasis project data (as of Jul 2026)

- Application: `TNPLI31682026` → Ref `TNRERA/PLI/3747/2026`, filed **22-05-2026**
- Status: **Application yet to verify by Scrutiny Officer** (pending scrutiny verification)
- Applicant: Nisant Ranka; project: Ranka Oasis (Krishnagiri, TN)
- If the user shares a newer screenshot, compare against this baseline and report the delta (e.g. moved to verification, objections raised, registered).

## Workflow

1. Check the screenshot/row the user shares — identify application no., ref no., filed date, status text.
2. If live verification is requested, attempt the portal (browser/curl); expect geo-block from this server.
3. If blocked: report honestly, ask user to check on their phone and share the status line (or the existing screenshot is already the live view).
4. Interpret the status and next steps; offer follow-up actions (draft nudge email/letter to TNRERA with contact numbers, tracking reminders).
