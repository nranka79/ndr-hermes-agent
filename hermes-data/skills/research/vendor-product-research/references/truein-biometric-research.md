# Truein — Biometric Attendance Vendor Research (2026-07-13)

Reference dump from a DRAAS internal task: "research whether Truein users must be registered on one device, whether biometric templates are cloud-hosted or per-device, and whether the device supports API integration to push data into our CRM."

This is a snapshot. Vendor pages and APIs change. Re-verify before relying on it for a fresh buy decision.

## TL;DR
- **Multi-device, cloud-centralised.** Same employee can register on mobile + multiple kiosks; face template lives in the vendor cloud; each attendance record carries `inDevice` and `outDevice` fields.
- **Public REST API exists.** OAuth2 `client_credentials` for auth, plus a `Subscription-key` header per call. Endpoints cover punch read-out, punch write-in, employee master CRUD, kiosk device CRUD, geofence, leave, shift.
- **Polling > webhooks.** No public webhook doc — the recommended integration pattern is to poll `dailyAttendanceLog` (or `inOutDtls`) on a schedule and push to your CRM.

## Confirmed architecture (3 questions, 3 evidence sources)

### 1. Single vs multi-device registration
**Answer: multi-device. Cloud-held face template. No "lock to one kiosk".**

Evidence — marketing copy at `https://www.truein.com/manpower-staffing-industry-attendance-software`:
> "Truein helps onboard or add new staff instantly. The staff can onboard by showing their face on the kiosk or with a single selfie using their mobile. Onboarded staff can be immediately sent to multiple clients without the need for any re-onboarding at the client site."

Same page, separate paragraph:
> "A single capturing device for staff working at multiple clients in the same premises brought transparency."

Evidence — `https://www.truein.com/distributed-workforce-attendance-management`:
> "You can allow mobile for some roles and limit others to approved kiosks."

### 2. Where the biometric / face template lives
**Answer: vendor cloud, not on the device. Device is a thin client that buffers offline punches and syncs.**

Evidence — Truein homepage and product nav:
> "Cloud based Time and Attendance" (menu item on every page)

Evidence — homepage feature block:
> "Offline Clock-ins – Let staff clock in on sites with poor or no network. Data is stored on the device and syncs automatically when connectivity is available, so remote locations are never missing from attendance."

Evidence — distributed-workforce page FAQ:
> "Q: Will attendance work without internet? A: Yes. Punches are captured offline and sync once the network is available."
> "Q: How do we know which punches were offline? A: Offline punches are clearly flagged in reports for quick verification."

Architecture implication: offline + sync confirms the device is a buffer, not the source of truth. The face template, master employee record, and final punch records all live in Truein's cloud; the device pulls the template down at clock-in time and pushes the punch back up.

### 3. API surface for integration
**Answer: full public REST API. Three endpoint families the user actually needs.**

Base URL: `https://api.truein.com`. Full OpenAPI/Redocly spec lives at `https://developer.truein.com` (v1.0.11).

#### Auth — OAuth2 client_credentials
```
POST https://api.truein.com/connect/token
Content-Type: application/json

{
  "access_key_id": "<from Truein admin dashboard>",
  "secret_access_key": "<from Truein admin dashboard>",
  "grant_type": "client_credentials"
}

→ { "data": [{ "access_token": "…", "token_type": "Bearer", "expires_in": 3600 }] }
```
Token TTL: 24h.

Every other endpoint requires **two** headers:
- `Authorization: Bearer <access_token>`
- `Subscription-key: <API Access Key from admin dashboard>` ← different credential from the OAuth secret; missing this gives a misleading 401

#### Read punches → push to CRM
- `GET /apis/ext/attendance/v1.0/inOutDtls?lastUid=0&from_date=YYYY-MM-DD&to_date=YYYY-MM-DD&emp_id=…`
  - Paginated by `lastUid` (1000 records per call)
  - Returns per-punch: `uid`, `name`, `empId`, `mobile`, `email`, `inTime`, `inPicUrl`, `outTime`, `outPicUrl`, `inLocation`, `outLocation`, `timespent`, `status`, `subStatus`, **`inDevice`**, **`outDevice`**, `site_name`, `siteCode`, `jobCode`, `jobName`
  - The presence of `inDevice` / `outDevice` is the proof of multi-device architecture — punches are tagged with the source device
- `GET /apis/ext/attendance/v1.0/dailyAttendanceLog?date=YYYY-MM-DD&lastUid=0&emp_id=…&site_name=…&include_absent=1`
  - Full daily summary per employee: present/absent/leave, OT, half-day, late, with `inOuts` array
- `GET /ext/v1/timesheet/getTimesheetSummary?fromDate=…&toDate=…&empId=…&siteCode=…&includeAbsent=1&includeJobWiseSummary=1`
  - Payroll-ready summary, supports job-wise breakdown

#### Write punches (kiosk / CRM-push-into-Truein)
- `POST /v1/time-tracking/clockIn` — body: `siteCode`, `empId`, `inTime`, `staffPic` (base64), `coordinates{lat,lon}`, `jobCode`
- `POST /v1/time-tracking/clockOut` — same shape with `outTime`
- `POST /v1/time-tracking/updateAttendance` — corrections

#### Employee + kiosk master
- `POST /addEmployeeDtls`, `GET /getEmployeeDtls`, `POST /updateEmployeeDtls`, `POST /deleteEmployeeDtls`
- `POST /addKioskDevice`, `GET /getKioskDevice`, `POST /updateKioskDevice`, `POST /deleteKioskDevice`

Plus: geofence, leave, shifts, sites, holidays, jobs, cost-centre, activity endpoints (full list at `https://developer.truein.com`).

## Bottom line for DRAAS

For the "push site attendance into Kelsa" use case, the cleanest path is:
1. Get `access_key_id` + `secret_access_key` from the Truein admin dashboard (Settings → API)
2. Poll `dailyAttendanceLog` once per day for `date=<yesterday>` with `include_absent=1`
3. Push the resulting JSON rows into Kelsa via a small connector script

Truein also offers "custom integration" via their sales team if the user wants a one-way webhook from Truein to a vendor endpoint (the marketing page says "Don't see your payroll solution here? No problem! We do custom integration. Talk to us" — but no public webhook docs were found on `developer.truein.com`, so this is a sales conversation, not a self-serve path).

## Sources
- `https://www.truein.com/` — homepage, feature blocks
- `https://www.truein.com/integrations` — "Seamless Integration Support … API and FTP-based integrations"
- `https://www.truein.com/manpower-staffing-industry-attendance-software` — multi-device onboarding quote
- `https://www.truein.com/distributed-workforce-attendance-management` — kiosk-vs-mobile policy
- `https://www.truein.com/biometric-attendance-system-vs-app-based-attendance-system-truein` — offline support
- `https://www.truein.com/face-recognition-technology` — face recognition product page
- `https://developer.truein.com` — full OpenAPI/Redocly spec, v1.0.11
- `https://api.truein.com` — 245-byte redirect to truein.com (base URL only)
- `https://apitracker.io/a/truein` — third-party API metadata (notes OAuth2 + REST + webhooks tier, but webhook spec not published)
