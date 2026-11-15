---
name: google-health-api
description: "Access the Google Health API (health.googleapis.com/v4 — the Fitbit-descended successor to the Fitbit Web API) for NDR's device data: sleep, activity, vitals, nutrition. Covers the exact OAuth scope strings, the mandatory narrow health-only token, endpoint/filter patterns, and the no-sleep-score reality. Use for any 'pull my Fitbit/Google Health data', sleep/steps/vitals reads, or nutrition/exercise write requests."
version: 1.0.0
author: Hermes (auto-generated via user session)
platforms: [linux, macos]
metadata:
  hermes:
    tags: [google-health, fitbit, sleep, activity, vitals, oauth, health-api]
    homepage: https://hermes-agent.nousresearch.com/docs
---

# Google Health API (health.googleapis.com/v4)

The Google Health API is the next-gen Fitbit Web API (NOT legacy Google Fit `fitness.googleapis.com`). Base URL `https://health.googleapis.com/v4`. Everything is a data point under `users/{user}/dataTypes/{data_type}/dataPoints`.

> **Where NDR's data is actually stored →** `ndr-wearable-tracker-map.md` (same directory).
> **As of 2026-11-11 it ALL lives in his Medical Report Index** (sbari-owned copy
> `1gsIQXoVis0TG3eCZFmg0AVzCPG525doPK0ifTIqz2rg`, tabs `Sleep (Wearable)` / `Daily Vitals` /
> `Daily Activity` / `Exercise (Device)` / `Google Health Inventory` / `Wearable Findings`), and the
> standalone `NDR Sleep Analysis` workbook is superseded. Read the map before creating anything new.

## 🔴 MANDATORY pagination + retry/backoff (2026-11-15 incident)

Do not hand-roll a `while nextPageToken` loop for a "pull all my health data" ask.

**Official page-size rules** (Google Health `dataPoints.list`):
- `pageSize` unspecified -> at most **1,440** points per response.
- Maximum **10,000**.
- `sleep` and `exercise`: default **25**, maximum **25**.
- Results are newest-first; loop `nextPageToken` until it is absent.

**What went wrong on 2026-11-15 (Rivaan):** an ad-hoc loop omitted `pageSize` and used
no time filter across 25 types. It made **1,215 pages / ~2,400 HTTPS calls / 25 minutes**;
four dense series hit the loop's `page > 200` guard and were **silently truncated at
~10,000 points**; `steps` and `distance` were lost to two `503 UNAVAILABLE` responses
because the loop `break`s on the first error. The JSON was only written at the end, so
the sheet work had not begun after 25 minutes. It also minted a fresh down-scoped OAuth
token on every page (`google_health_request` called `google_health_access_token`
unconditionally).

**Use these instead:**
- `tools.gws_auth.google_health_list_data_points(data_type, data_filter=..., page_size=None, max_pages=None)`
  sets `pageSize=10000` (25 for sleep/exercise), loops `nextPageToken`, retries
  `429/500/502/503/504` + network errors with exponential backoff + jitter, honours
  `Retry-After`, re-mints once on 401, and **caches the health-only token for ~1 hour**
  so a multi-page pull mints once, not per page. Returns `pages`, `truncated`,
  `last_page_token`.
- `scripts/health_pull.py` / `scripts/health_full_sync.py` for the scripted paths.
- `scripts/health_pull_windowed.py` for a full-history pull: per-type filters, HR
  3-day chunks, SpO2 4-day chunks, other interval types 10-15 days, `pageSize=10000`,
  bounded workers, coverage report.

**Retry rules:** GETs retry on `429`, `500`, `502`, `503`, `504`, `URLError`, timeout
and connection reset. Writes retry only on `429`/`503` (avoid duplicate data points).
Do **not** retry `400` (bad filter/type), `403` (permission/scope) or `404`. The error
catalog maps `429 RESOURCE_EXHAUSTED` to quota/rate limit and `500 INTERNAL_ERROR` to a
server error; `503` is transient. No numeric quota is published, so backoff is generic.

**Always report coverage:** `min(date) -> max(date)`, per-type point/page counts, and
partial boundary days (a 2.83-hour night is the band coming off, not a bad night).
Never restate the user's assumption ("past month is missing") without measuring it.

**Writing to a sheet:** check `files.get(...).capabilities.canEdit` before any
`batchUpdate`/`values` write. `canEdit=false` returns `403 "The caller does not have
permission"`; use `gws_sheets_get_tabs` / `gws_sheets_rename_tab` (title -> sheetId)
and build a workbook owned by the session user if the source is view-only.
`canCopy=true` does not guarantee copy: an external viewer can still get
`403 insufficientFilePermissions` on `files.copy`.

## 🔴 `dailyRollUp` / `rollUp` RETURN ZERO POINTS — aggregate minute-level points instead
(verified 2026-11-11, NDR's account)

Every rollup data type — `steps`, `distance`, `heart-rate`, `active-minutes`,
`active-zone-minutes`, `time-in-heart-rate-zone`, `active-energy-burned`, `total-calories`,
`sedentary-period`, `floors`, `calories-in-heart-rate-zone` — returned `dataPoints: []` with **no
error** across 7/8/14-day windows, both CivilTimeInterval and physical RFC-3339 bodies, with
`windowSize` and `windowSizeDays` set. Silent zero, indistinguishable from an unworn device.

**Fix:** list the ~1-minute interval points with a civil-time filter and aggregate in Python
(`steps.count`, `distance.millimeters` ÷1e6, count points per `heartRateZoneType` for time-in-zone,
count per `heartZone` for Active Zone Minutes, sum `activeEnergyBurned.kcal`, sum
`(endTime − startTime)` for sedentary). It is verbose (52,541 `active-energy-burned` points over
10 weeks, ~10 pages at `pageSize=10000`) but it is the only thing that works. Chunk 10–15 days.

> **Wrapper-key trap, same pass:** the daily-metric wrapper key is the **camelCase dataType**
> (`p["dailyRestingHeartRate"]`), NOT the kebab name with dashes stripped. Looking up
> `p["dailyrestingheartrate"]` returns zero days for all five daily series while printing no error.


NDR's setup (verified 2026-09-05): device = **Google Fitbit Air**, account = **nishantranka@gmail.com** (vault service `google-gmail`), legacy Fitbit ID `DH8DZ6`, healthUserId `9056947863530977435`. He wants recurring Sheets pulls + nutrition pushes.

## The ONE rule that makes or breaks every call

**Google Health rejects any access token that carries non-health OAuth scopes.** Error: `403 DISALLOWED_OAUTH_SCOPES` with `disallowed_scopes: cl,cp,drive,mail_modify,...` (calendar/gmail/drive/sheets/etc. all banned on the same token).

ALWAYS mint a **narrow health-only token** from the stored refresh token, then call the API with that token:

```python
import sys, json, urllib.request, urllib.parse
sys.path.insert(0, "/opt/hermes")
import tools.gws_auth as ga
creds = ga.load_credentials("google-gmail")   # vault creds carry client_id/client_secret/refresh_token
body = urllib.parse.urlencode({
    "client_id": creds.client_id,
    "client_secret": creds.client_secret,
    "refresh_token": creds.refresh_token,
    "grant_type": "refresh_token",
    "scope": " ".join(HEALTH_SCOPES),        # ONLY googlehealth.* strings
}).encode()
req = urllib.request.Request("https://oauth2.googleapis.com/token", data=body,
    headers={"Content-Type": "application/x-www-form-urlencoded"})
tok = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())["access_token"]
```

`HEALTH_SCOPES` = the full suffixed set in `scopes-and-endpoints.md`. Verify with tokeninfo (`oauth2.googleapis.com/tokeninfo?access_token=...`) that only googlehealth scopes are on it. Ready-to-run version: `../scripts/health_pull.py`.

## One-time prerequisites (all done 2026-09-05, re-check if errors change)

1. **API enabled in the GCP project** — `SERVICE_DISABLED` error means: open `https://console.developers.google.com/apis/api/health.googleapis.com/overview?project=<project_id>` (the error message includes the exact URL) and click Enable. Propagates in ~2–3 min. Project: 353166898892.
2. **Suffixed scopes in the OAuth client scope list** — `/opt/hermes/tools/gws_auth.py` `HERMES_GWS_SCOPES` must carry the suffixed `googlehealth.*.readonly/.writeonly` strings. The legacy unsuffixed forms (`googlehealth.activity_and_fitness`) are dead — the API requires `.readonly`/`.writeonly` (release notes: "Replacing read/write scopes with .writeonly"). File is root-owned; patching needs root (no sudo in container). Existing vault tokens keep working after scope-list changes (2026-07 fix in gws_auth loads stored scopes), only NEW consents use the updated list.
3. **User consent** via `send_oauth_url` — the user must authorize with the updated scope list. Verify the token actually has the suffixed health scopes with tokeninfo before coding.

## Common reads

- Identity: `GET /v4/users/me/identity` → `legacyUserId` (Fitbit ID) + `healthUserId`. Use it as the access smoke test.
- Sleep: `GET /v4/users/me/dataTypes/sleep/dataPoints?filter=<urlencoded>` — session record type; filter on `sleep.interval.civil_end_time >= "YYYY-MM-DD" AND sleep.interval.civil_end_time < "YYYY-MM-DD"` (yesterday = [today-1, today)).
- Daily rollups (clean daily totals for interval types): `POST /v4/users/me/dataTypes/{steps|active-minutes|active-energy-burned|...}/dataPoints:dailyRollUp` with body `{"range": {"start": {"date": {...}, "time": {...}}, "end": {...}}}` (CivilTimeInterval), `windowSizeDays` default 1.
- Daily metric types (`daily-resting-heart-rate`, `daily-heart-rate-variability`, `daily-oxygen-saturation`, `daily-respiratory-rate`): `GET ...?filter=<dataType snake>_snake.date >= "YYYY-MM-DD"`. Value fields are camelCase JSON keys (`dailyRestingHeartRate.beatsPerMinute`, `dailyHeartRateVariability.averageHeartRateVariabilityMilliseconds`, etc.).

## `service_name` is SESSION-RELATIVE — the same key is a different person

`"google-gmail"` is not a person, it is *the session user's own Gmail identity*. In NDR's
session it is nishantranka@gmail.com; in Ruhaan's session it is rankaruhaan88@gmail.com.
Always confirm with `gws_resolve_account` before quoting any health numbers as someone's.

**Ruhaan's identity (verified 21-Oct-2026):** `legacyUserId` **DHD2R9**,
`healthUserId` **5628948378093662985**, device **Fitbit Air**, `platform: FITBIT`,
profile `age: 14`, `membershipStartDate` **2026-09-05**.

**Rivaan's identity (verified 15-Nov-2026, `rankarivaan@gmail.com` / `google-gmail`):**
`legacyUserId` **G92ZJV**, `healthUserId` **8816765116094150302**, device **Fitbit Air**,
profile `age: 27` (almost certainly a setup default — flag it, do not quote it as fact),
`membershipStartDate` **2026-10-10**. Body measurements exist only as a single MANUAL entry
from 10-Oct-2026: `weightGrams: 45000` (45.0 kg), `heightMillimeters: "1549"` (154.9 cm) —
they surface via `sample_time.physical_time`, not the interval filter.

## A 404 HTML page from health.googleapis.com is a TOKEN problem, not missing data

`GET /v4/users/me/identity` returning a **404 with an HTML body** (not JSON) means the
minted token was not acceptable — it does **not** mean the account has no health profile,
and it does not mean the API is disabled. Verified 21-Oct-2026: the same account, same
session, went 404 → **200** the moment the mint was narrowed.

Cause: the helper `ga.google_health_request()` (and `scripts/health_pull.py`'s
`HEALTH_SCOPES`) mints against the **full** list including `.writeonly`, `.ecg`, `.irn`,
`.location`. If the user's consent covered a narrower set, the resulting token is rejected.
**Fix: mint with only the readonly scopes actually granted, verify with tokeninfo, then
call.** This exact set worked:

```python
SC = ["https://www.googleapis.com/auth/googlehealth.activity_and_fitness.readonly",
      "https://www.googleapis.com/auth/googlehealth.health_metrics_and_measurements.readonly",
      "https://www.googleapis.com/auth/googlehealth.sleep.readonly",
      "https://www.googleapis.com/auth/googlehealth.profile.readonly"]
# → users/me/identity 200 {"legacyUserId":"DHD2R9","healthUserId":"5628948378093662985"}
```

Debug order for any 4xx here: (1) tokeninfo the token and read its `scope`;
(2) confirm the scope the endpoint needs is present; (3) only then believe a data absence.
Never conclude "no data" from a 404 HTML body.

## Sleep payload — read `summary`, and know the two timezone facts

- **`sleep.summary` already carries the numbers.** `minutesInSleepPeriod`, `minutesAsleep`,
  `minutesAwake`, `minutesToFallAsleep`, `minutesAfterWakeUp`, and
  `stagesSummary[{type,minutes,count}]` (AWAKE / LIGHT / DEEP / REM). Read them; don't
  recompute from the `stages[]` interval list.
- **`shortAwakenings[]` is a different metric from `minutesAwake`.** It is a list of
  30 s–3 min micro-arousals (13–43 per night on Ruhaan's data) and can be high while
  `minutesAwake` is only 8. Report them as separate columns or you will describe a calm
  night as a wrecked one.
- **`interval.startTime` / `endTime` end in `Z` and ARE UTC.** Convert with
  `dt.fromisoformat(t.replace("Z","+00:00")).astimezone(IST)`. Verified across 12 nights
  21-Oct-2026: conversion produced a coherent band (bed **00:02–02:55**, wake
  **09:08–11:17** IST), which is the sanity check to run. If the band looks wrong, ASK the
  user to confirm one row — do not silently ship plausible-looking clock times.

## Endpoints and coverage actually observed (21-Oct-2026 pull)

All of these returned data on the filter `<snake>_snake.date >= "…" AND … < "…"`:

| dataType (path, kebab) | points in a 29-day window |
|---|---|
| `sleep` | 12 |
| `daily-resting-heart-rate` | 29 |
| `daily-heart-rate-variability` | 29 |
| `daily-oxygen-saturation` | 26 (sparsest) |
| `daily-respiratory-rate` | 29 |
| `daily-sleep-temperature-derivations` | 29 |

**CORRECTED 2026-11-08 — the "~12 records in a 29-day window is normal" reading was
PAGINATION, not device wear.** A single `GET .../sleep/dataPoints?filter=…&pageSize=200`
over 25-Aug→9-Nov returned **13** points; the same filter with `nextPageToken` paging
returned **63**. The API caps what one response carries regardless of `pageSize`.
**Always loop on `nextPageToken`** (`?pageToken=…` until absent) before concluding
anything about coverage. `scripts/health_backfill_sheets.py` does this.

Once paginated, the real picture is near-complete: 63 sleep points (main + naps) from
6-Sep (device connect) to 8-Nov, 62 main nights. Genuine gaps do exist (e.g. no record
at all for wake dates 23–25 Oct) — but they are the exception, not the norm, and you
can only identify them after paging. Never read a missing date as missing sleep, and
always state the coverage count alongside the table.

## No sleep score

The API has **no single numeric Fitbit-style sleep score** — `SleepSummary` carries only minutes: `minutesAsleep`, `minutesAwake`, `minutesInSleepPeriod`, `minutesToFallAsleep`, `minutesAfterWakeUp`, `stagesSummary[]` (per-stage `type/minutes/count`: AWAKE, LIGHT, DEEP, REM). When asked for a "sleep score", state this explicitly and give stage minutes. Same for "activity score" — no composite; give steps, active minutes, active energy, zone minutes.

## Field-shape traps that silently produce empty columns (verified 2026-11-08, Ruhaan)

Four independent ways a correct-looking pull returns blank or zero rows. Each one
cost a debugging pass; check all four before believing a data absence.

1. **`mainSleep` lives INSIDE `sleep`, not at the top of the dataPoint.**
   `p["metadata"]["mainSleep"]` is always `None` → you filter out every night and
   report zero. Correct path: `(p.get("metadata") or p["sleep"].get("metadata") or {})["mainSleep"]`.
   Sibling keys: `processed`, `stagesStatus`.
2. **Every numeric field arrives as a STRING.** `"minutesInSleepPeriod": "495"`,
   `"minutesAsleep": "449"`, `"minutes": "46"`, `"count": "5"`, `"countSum": "424"`.
   `summ["minutesAsleep"] / summ["minutesInSleepPeriod"]` raises
   `TypeError: unsupported operand type(s) for /: 'str' and 'str'`. Coerce with
   `int(round(float(x)))` at the boundary and keep a `num()` helper. This applies to
   the sleep summary, stagesSummary, all rollups and all daily-metric values — not
   just `dailySleepTemperatureDerivations` (the only one previously documented).
3. **Rollup values are NESTED under a camelCase wrapper named after the dataType**,
   not top-level. `p["activeMinutesRollupByActivityLevel"]` → `None`; the real path is
   `p["activeMinutes"]["activeMinutesRollupByActivityLevel"]`. Verified mapping:

   | dataType (path) | value path |
   |---|---|
   | `steps` | `p["steps"]["countSum"]` |
   | `distance` | `p["distance"]["millimetersSum"]` (/1e6 → km) |
   | `active-minutes` | `p["activeMinutes"]["activeMinutesRollupByActivityLevel"][{activityLevel,activeMinutesSum}]` |
   | `active-energy-burned` | `p["activeEnergyBurned"]["kcalSum"]` |
   | `total-calories` | `p["totalCalories"]["kcalSum"]` |
   | `sedentary-period` | `p["sedentaryPeriod"]["durationSum"]` ("27120s" → /60) |
   | `heart-rate` | `p["heartRate"]["beatsPerMinuteAvg"/"…Min"/"…Max"]` |
   | `time-in-heart-rate-zone` | `p["timeInHeartRateZone"]["timeInHeartRateZones"][{heartRateZone,duration:"41100s"}]` |

4. **Points come back NEWEST-FIRST**, so an unsorted write reverses the sheet. Sort on
   `civilStartTime` / `interval.endTime` before writing.

## Prove WHOSE data it is from `identity`, not from the email address

`gws_resolve_account()` told the truth and the remembered address was still wrong:
in Ruhaan's session `google-gmail` resolved to **`rankaruh@gmail.com`** on 2026-11-08 —
a *third* Ruhaan address, neither `rankaruhaan88@gmail.com` nor `pebblyshark69@gmail.com`.
Do not treat any remembered email as the expected answer, and do not conclude "wrong
person" or "wrong token" from an unfamiliar address.

The authoritative check is one call:

```
GET /v4/users/me/identity → {"legacyUserId": "DHD2R9", "healthUserId": "5628948378093662985"}
```

`DHD2R9` = Ruhaan's Fitbit. Print this before quoting any number as someone's, and
quote it in the report so the ownership claim is auditable. Two accounts can both be
"his" (one owns the sheets, another carries the health link) — they are different
Google identities and authorizing one grants nothing to the other.

## dailyRollUp coverage + the extra vitals fields (verified 2026-10-22, Ruhaan)

`POST users/me/dataTypes/{dt}/dataPoints:dailyRollUp` — **14-day cap**, so chunk 7 days.
Supported (verified): `heart-rate` → `heartRate.{beatsPerMinuteAvg,beatsPerMinuteMax,beatsPerMinuteMin}`;
`time-in-heart-rate-zone` → `timeInHeartRateZone.timeInHeartRateZones[{heartRateZone,duration:"41100s"}]`
(zones LIGHT/MODERATE/VIGOROUS/PEAK, duration in seconds → /60 for minutes);
`steps` (`countSum`), `active-minutes` (`activeMinutesRollupByActivityLevel[{activityLevel,activeMinutesSum}]`,
levels LIGHT/MODERATE/VIGOROUS), `active-energy-burned` (`kcalSum`), `total-calories` (`kcalSum`),
`distance` (`millimetersSum` → /1e6 km), `sedentary-period` (`durationSum:"27120s"`).
**NOT supported**: `oxygen-saturation`, `sleep`, `exercise` (rollup), and `floors` returns an empty rollup.
Rollup points come back **newest-first** — sort by `civilStartTime` before writing a sheet.

Intraday `heart-rate` list filter is `heart_rate.sample_time.physical_time >= "…T00:00:00Z"` (NOT
`interval.*`); ~1000+ points/day, so use the rollup for daily aggregates rather than paging samples.

**CORRECTED 14-Nov-2026 — intraday HR is far denser than "~1000/day": 107,266 points in a single
3-day chunk (~36k/day), 318,888 over 9 days.** So: chunk intraday `heart-rate` at **3 days** and
`oxygen-saturation` at **4 days**, both with `pageSize=10000` and `nextPageToken` paging. It is
fine to pull that volume — just do not interpolate 300k points directly, downsample (e.g. a
60-sample rolling median) before plotting, and expect ~60 s for the whole sweep.

Two conversion traps when using those points alongside other data:
- `sampleTime.physicalTime` is **UTC** while the sibling `utcOffset` (`"19800s"`) and
  `civilTime` are local. Parse, strip tzinfo to naive UTC, *then* add the offset. Adding a timedelta
  to an aware datetime and later comparing it with a naive window start raises
  `TypeError: can't subtract offset-naive and offset-aware datetimes` far downstream.
- `daily-resting-heart-rate` / `daily-heart-rate-variability` / `daily-oxygen-saturation` came back
  with only **8–9 points for an 11-day window** — sparse but stable; do not read that as a token
  problem. Intraday `oxygen-saturation` gave 715–1,554 samples per 4-day chunk over the same days.

Extra value fields worth capturing beyond the basics: `dailyHeartRateVariability.nonRemHeartRateBeatsPerMinute`,
`dailyOxygenSaturation.upperBoundPercentage`, and HR zone minutes from the rollup above.
`execute_code` caps a script at **50 tool calls** — a 9-type × 7-chunk rollup pull will hit it mid-run;
split the date range across two calls.

## Sheet home for Ruhaan's device data

Write device pulls to `20261021_Ruhaan_Medication_Sleep_Vitals_Log`
(`19OE2ItXkWf7UcdUc0fg-Yj_01MtPgQwNTidej8M-S8M`) — **owned by rankaruhaan88@gmail.com, writable**
(tabs: Summary / Medications / Incidents / Sleep / Daily Vitals / Daily Activity). Do NOT try to append
to the family Report Index or Master Tracker from his session: 403 "The caller does not have permission".

## Write support

Nutrition and exercise ARE writable via the same dataPoints create pattern — exact payloads in `scopes-and-endpoints.md`. Scope: `.nutrition.writeonly` / `.activity_and_fitness.writeonly`. Writes return an **Operation** wrapper (`{"done": true, "response": {..., "name": "users/<id>/dataTypes/<dt>/dataPoints/<id>"}}`) — persist `name` for PATCH/batchDelete. Server-generated IDs only (custom client IDs not yet supported).

## Absorbed: google-health bundled stub (2026-09-06)

The bundled `google-health` skill (platform-unsupported stub) has been folded into this skill —
it surfaced as the canonical home for health.googleapis.com work. One convenience it documented
is worth noting: `tools.gws_auth` exposes a `google_health_request(method, path, params=...,
json_body=...)` helper that mints the narrow token and returns parsed JSON (raises RuntimeError on
non-2xx; `service_name` defaults to `"google-gmail"`). The manual narrow-token recipe in this
skill and the helper do the same job — prefer the helper when you just need a quick read.

## Pitfalls

- **Chunked rollups drop the LAST day of each chunk (verified 2026-11-01).** The rollup `range.end` is
  EXCLUSIVE at midnight, so looping `d0 → d1 = d0+13d` silently loses `d1` itself — a 14-day window
  returned steps for every day except the newest one. Set the end to `chunk_end + 1 day` (or
  `today + 1 day`) and the missing day appears.
- **`values().append()` targets the first EMPTY ROW of the range you give it, not the sheet end.**
  `append(range="'Summary'!A1:B1", INSERT_ROWS)` on a Summary tab that has a blank row 6 inserts the
  whole block at row 7 and shifts every section below it (verified 2026-11-01). For a header-block
  sheet, write to an explicit `A<n>:B<m>` with `values().update` instead; to undo a mis-append,
  `batchUpdate` → `deleteDimension` on the exact row span.
- **Prove the timezone from the payload, not from the clock (verified 2026-11-01).** Every sleep
  interval carries `startUtcOffset`/`endUtcOffset` (a google-duration string like `"19800s"` =
  +05:30 = IST). When a user disputes a bedtime, quote that field plus Google's REST reference
  ("startTime ... uses RFC 3339, generated output is always Z-normalized") and add 5h30m — that
  settles it without guessing. `civilStartTime`/`civilEndTime` come back ABSENT on FITBIT-platform
  sleep points, so the offset field is the only local-time anchor available.
- **A backfilled sleep block is not a night (verified 2026-11-01, Ruhaan 22-Oct).** Check
  `sleep.createTime`: normal nights are created within hours of waking; a point created days later
  is a late backfill and must be treated as low confidence. Cross-check with intraday `steps`
  dataPoints inside the claimed window — zero samples there means the band logged either real
  sleep or an unworn/charging block, and the API cannot tell you which. Flag it in the sheet,
  exclude it from averages, and never present it as a normal night.
- **`dailySleepTemperatureDerivations.baselineTemperatureCelsius` can come back
  as a STRING** (verified 2026-10-13) → `TypeError: unsupported operand type(s)
  for -: 'float' and 'str'` when computing the nightly-vs-baseline delta.
  `float()` BOTH fields before subtracting. The resulting delta is also **NaN on
  days with no baseline** — run it through the `clean()` sanitiser (below) before
  any `values().update`, or the whole Sheets payload is rejected with
  `Unexpected token. , NaN`.
- **Daily-vitals pull recipe (verified 2026-10-13, 5 types over 6 weeks).**
  snake_case in the FILTER, kebab-case in the PATH:
  `GET users/me/dataTypes/daily-resting-heart-rate/dataPoints?filter=daily_resting_heart_rate.date >= "2026-09-01" AND daily_resting_heart_rate.date < "2026-10-14"`.
  Value fields are camelCase: `dailyRestingHeartRate.beatsPerMinute`,
  `dailyHeartRateVariability.averageHeartRateVariabilityMilliseconds`,
  `dailyOxygenSaturation.averagePercentage`,
  `dailyRespiratoryRate.breathsPerMinute`,
  `dailySleepTemperatureDerivations.{nightlyTemperatureCelsius,baselineTemperatureCelsius}`.
  Returns 31–39 points each (SpO2 is the sparsest). The date is nested as
  `{year, month, day}` — key it as `"%04d-%02d-%02d"` to join onto the sleep
  night's WAKE date.
- **Custom exercise `displayName` is NOT stored** (verified 2026-09-11): the API normalizes it server-side to the exerciseType label ("Strength training" / "Aerobics") — GET always returns the generic label regardless of what you POST/PATCH. Per-set detail (weights/reps/exercise names) cannot live on exercise dataPoints. Keep a set-by-set detail log elsewhere (Sheet/notes); Health only holds type + interval + activeDuration. Also: `metricsSummary` written manually comes back empty `{}` on GET for non-device points — device-synced points (Fitbit) carry full metrics; manual ones don't.
- **Bare `terminal()` subprocess resolves the WRONG vault user** (2026-09-11): `load_credentials("google-gmail")` from `terminal()` (no `HERMES_RPC_SOCKET`) reads `HERMES_SESSION_USER_ID` from env and resolved to `psingh-8502281203` instead of NDR → `VaultNoTokenError: No google-gmail token for user psingh-…`. Run health writes via **execute_code** (sandbox sets `HERMES_RPC_SOCKET`, routes through `gws_fetch_token` RPC to the trusted gateway, resolves NDR correctly). Do not retry the same token-mint recipe in terminal — it will keep failing.
- **DISALLOWED_OAUTH_SCOPES** → you sent a bundled token. Mint the narrow token (rule above).
- **SERVICE_DISABLED** → enable the API in Cloud Console (prereq #1) and wait a few minutes.
- **ACCESS_TOKEN_SCOPE_INSUFFICIENT** → token lacks the suffixed scope the method needs (e.g. sleep needs `.sleep.readonly`); re-consent with the updated scope list.
- **Sandbox env has no `HERMES_OAUTH_CLIENT_ID`/`SECRET`** — don't look for them via os.getenv in execute_code; `load_credentials()` returns Credentials that already carry `.client_id`/`.client_secret`/`.refresh_token`.
- **`send_oauth_url` can hit Telegram flood control** ("Flood control exceeded. Retry in ~531s") after repeated button sends — wait the cooldown (background `sleep <N>` + notify), then resend; do not spam.
- **Data history can be shallow after migration** — on first connects the API may hold only the current night's sleep + today; don't assert long history exists. Older Fitbit data may still be backfilling or only in the legacy Fitbit Web API.
- **Filter syntax** is a strict AIP-160 subset: only `>=` (inclusive) and `<` (exclusive), only `AND` (no OR), no mixed civil/physical time. Data type in filter is **snake_case** (`sleep.interval.civil_end_time`), in the URL path it's **kebab-case** (`dataTypes/sleep`). URL-encode the filter.
- **Averaging a clock time (bedtime) needs midnight rollover** (verified 2026-10-22).
  `mean(minutes-of-day)` over bedtimes spanning 22:33 → 04:11 lands in the middle of the DAY and
  prints a nonsense "avg bedtime 11:38". Map times before 12:00 to `+1440`, average, then `% 1440`
  (correct answer for that series: **00:09**). Wake times never cross midnight, so they need no fix.
- **Sleep-session selection:** build the nightly table from `metadata.mainSleep == True` only. A
  `mainSleep` false/absent segment is a nap or a sensor artifact — merge it and you invent a second
  bedtime. Report excluded segments in a note row rather than silently dropping them.
- **Writing the pull into Sheets:** use `valueInputOption="RAW"` so ISO dates and `h:mm` strings stay
  text and JSON numbers stay numbers (USER_ENTERED re-parses both and reorders the column). Clear the
  target range first — a shorter rewrite leaves orphan rows below. Sanitise `NaN`/`Inf` to `""`
  before `values().update` (see the NaN pitfall above) — one NaN rejects the whole payload with
  `400 Invalid JSON payload received. Unexpected token`.
- `personal-health-intelligence` handles lab/protocol health work; this skill is device/API data. Cross-reference when combining.

## "Pull ALL of it" — sweep the catalog before writing anything (2026-11-11)

A request for *"everything that is available from the Google Health API — sleep, all the sleep
parameters, SpO2, body temperature, HRV, heart rate, everything"* is **not** answerable from the
six types the backfill script happens to write. The account may also hold weight, body-fat,
blood-glucose, core-body-temperature, exercise sessions, hydration/nutrition logs or ECG — or
genuinely none of them, and the two look identical if you write first.

Correct order:

1. **Sweep first, write second.** `scripts/health_inventory.py --start <device-start> --end <today>`
   probes all ~35 data types across the three filter families and prints point counts plus the
   real value-field names. Read-only; run it inside `execute_code`.
2. **Then run the verified writer** `scripts/health_backfill_sheets.py … --write` for the tabs it
   covers (Sleep / Daily Vitals / Daily Activity / Sleep (Wearable)) — it is the tested path and
   handles pagination, string-typed numbers, the `sleep.metadata` nesting and the rollup wrapper
   keys.
3. **Report absences as absences.** "No `weight`, `body-fat`, `blood-glucose` or `exercise` points
   exist on this account" is a real, useful answer. Do **not** create empty tabs or zero-filled
   columns to look complete — but do **not** conclude absence from a rejected filter either: the
   sweep prints `FILTER-ERR`, never a bare zero, for that reason.

State the coverage window explicitly (device connect date → today) in the reply, and quote the
`legacyUserId` from `identity` so the ownership of the numbers is auditable.

## Full-coverage sync — verified recipe (2026-11-11, Ruhaan, 6 Sep → 11 Nov)

`scripts/health_inventory.py` probes **every** data type first (`--start/--end`, prints
points + value keys + which filter member worked). `scripts/health_full_sync.py` does the
whole write: gap diff, 3 raw tabs, `Sleep (Wearable)`, plus `Exercise (Device)`,
`Sleep Respiration` and `Google Health Inventory`.

**Probe result that matters (37 types, one account):** 17 carry data, 20 are empty. Present:
`sleep`, all six `daily-*`, `heart-rate`, `steps`, `distance`, `active-minutes`,
`active-zone-minutes`, `active-energy-burned`, `sedentary-period`, `time-in-heart-rate-zone`,
`activity-level`, `exercise`, `swim-lengths-data`, `oxygen-saturation` (714 samples/11 days),
`heart-rate-variability`, `respiratory-rate-sleep-summary`. Empty: `weight`, `body-fat`,
`height`, `blood-glucose`, `core-body-temperature`, `vo2-max` ×3, `nutrition-log`,
`hydration-log`, `electrocardiogram`, `irregular-rhythm-notification`, `altitude`, `floors`.
**"Body temperature" on a Fitbit Air = `daily-sleep-temperature-derivations` (skin, nightly vs
baseline). There is no core-temperature record — say so rather than leaving a blank column.**

### Filter member per family — one wrong guess reads as "no data"

| family | working filter member | examples |
|---|---|---|
| interval / workout / log | `<snake>.interval.civil_start_time` | steps, exercise, nutrition-log |
| sleep | `<snake>.interval.civil_end_time` **only** — `civil_start_time` is rejected | sleep |
| daily metric | `<snake>.date` | daily-oxygen-saturation |
| sample / measurement | `<snake>.sample_time.physical_time` (RFC-3339 `Z`) | oxygen-saturation, weight, blood-glucose, respiratory-rate-sleep-summary |
| rollup-only | list returns `400 List is not supported` → use `dailyRollUp` | total-calories, floors, calories-in-heart-rate-zone |

A `400 INVALID_DATA_POINT_FILTER_DATA_TYPE_MEMBER` is a **wrong filter**, never evidence of
absent data. `dailyRollUp` DOES work on this account (68 activity days) — the "rollups return
zero" finding is account-specific, so re-test before falling back to minute-level aggregation.

### `health_inventory.py` mis-classifies the sample/measurement types — re-probe manually

Verified 15-Nov-2026 on Rivaan's account: the sweep listed `weight`, `height`, `body-fat`,
`blood-glucose`, `core-body-temperature`, `heart-rate-variability` and
`respiratory-rate-sleep-summary` under `INTERVAL` (filter `<snake>.interval.civil_start_time`),
so all seven came back `FILTER-ERR 400` — which reads exactly like "no data" and is not.
Re-probing them with `<snake>.sample_time.physical_time` returned **weight 1, height 1,
respiratory-rate-sleep-summary 40, and 0 for body-fat / blood-glucose /
core-body-temperature**. Two of those are real, clinically useful records the sweep hid.
The `INTERVAL`/`PHYSICAL` lists in the script have been corrected — but **treat any
`FILTER-ERR` on a measurement type as a taxonomy mistake and re-probe before writing
"none on this account" into a sheet or a reply.**

Scope errors are a third category, distinct from both. `electrocardiogram` and
`irregular-rhythm-notification` returned `403 Required OAuth scope(s) are missing for this
operation` — the user simply did not grant `.ecg.readonly` / `.irn.readonly`. Record that as
"scope not granted", never as "no data" and never as "the device can't do it".

### The user's belief about the coverage window is not evidence

Asked for "everything, except the past month because it hasn't been connected", the account
in fact held continuous daily data **through the current day** (Rivaan: nightly sleep
11-Oct → 15-Nov, daily vitals 33 days, activity 37 days, 83 exercise sessions — while
`membershipStartDate` was only 10-Oct). The band had not been idle; the *expectation* was
wrong. Always quote the measured window (`min(date) → max(date)` and per-type point counts)
instead of restating the user's assumption, and mark the boundary days that are genuinely
partial (a 2.83-hour "night" on the last day is the device coming off, not a bad night).

### Four write-safety defects fixed this pass — all four were silent

1. **`health_backfill_sheets.py` dies on `429 ReadRequestsPerMinutePerUser` (quota 60/min).**
   It calls `gap()` once per tab per pass *plus* once per append — N+1 reads. Fix: read each
   tab exactly ONCE into a set, compute every gap in memory, then write. 3 s sleep between
   Sheets calls, 20 s retry on 429.
2. **A swallowed tab read duplicates a whole tab.** `read_col()` caught every exception and
   returned `None` → `or []` → empty "have" set → 64 nights appended on top of 27 existing.
   Never `except: return None` around a values().get; a missing/renamed tab MUST raise.
3. **Rebuilding a curated tab loses its annotations.** `dict[date] = row` is last-wins: the
   generated blank row overwrote the curated row and **11 clinical notes in column T were
   wiped**. If a rewrite is unavoidable, keep the curated row for any date that already has
   one, and never regenerate column T.
4. **`NaN` in any cell rejects the whole payload** — `400 Invalid JSON payload received.
   Unexpected token ... NaN`. `json.dumps(float('nan'))` emits bare `NaN`. Sanitise every
   float (`x != x` → `""`) at the append boundary, not at the source.

### Recovering a wiped column from Drive revisions — the only path that worked

Sheets cell history is not in the API, but **file revisions are**:

```python
drv = build_service("drive", "v3", service_name="google-gmail")
revs = drv.revisions().list(fileId=SID, fields="revisions(id,modifiedTime)", pageSize=1000).execute()["revisions"]
# pick the newest revision whose modifiedTime is BEFORE your first write
resp, blob = drv._http.request(
    "https://docs.google.com/spreadsheets/export?id=%s&revision=%s&exportFormat=xlsx" % (SID, rid))
import openpyxl, io; ws = openpyxl.load_workbook(io.BytesIO(blob), data_only=True)["Sleep (Wearable)"]
```

`data_only=True` returns native types — `datetime` for dates, `time` for clock cells, `float`
for numbers — so serialise before re-writing (`%d/%m/%Y`, `%H:%M`, `""` for NaN) and write
with `RAW`. Compare a column against the live sheet first; regenerated API values matched the
curated ones exactly, so only the annotation column actually needed restoring.

### Two ordering rules the append path breaks

- **A gap can be OLDER than the last row.** Backfilling 22-Oct appended it below 8-Nov, and
  24-Oct landed below 31-Oct. If any missing date precedes the sheet's last row, sort the
  whole tab by date and rewrite (after reading it once) instead of appending.
- **A date the API returns with no metric values is still a real day, not a blank row to
  drop** — 24-Oct had total kcal 1443 and zero steps (band off-wrist most of the day). Keep
  it, sort it into place, and say in the Summary that it is a partial day.

**Never write a duplicate for a night the sheet already annotates.** The two
`2026-10-22 (1st/2nd session — LOW CONFIDENCE)` rows are the record; the diff reports them as
"orphans" and a naive backfill adds a third plain 22-Oct row. Delete the plain one.

## Support files

- `scopes-and-endpoints.md` — full OAuth scope catalog, data type ↔ scope map, endpoint list, write payloads (nutrition/exercise/sleep), filter examples, doc URLs.
- `tools.gws_auth.google_health_list_data_points` — mandatory paginated reader (pageSize=10000, 25 for sleep/exercise, nextPageToken, retry/backoff, cached token). Use this instead of a hand-written loop.
- `../scripts/health_pull_windowed.py` — windowed full-history puller (chunked filters, bounded workers, coverage.json).
- `../scripts/health_pull.py` — runnable narrow-token mint + sleep/activity/vitals pull (the verified recipe).
- `../scripts/health_inventory.py` — probe ALL 37 data types for a window; prints points, value keys and the filter member that worked. Run this first on any "pull everything" ask.
- `../scripts/health_full_sync.py` — full write: gap diff (one Sheets read per tab), Sleep / Daily Vitals / Daily Activity / Sleep (Wearable), `Exercise (Device)`, `Sleep Respiration`, `Google Health Inventory`. `--write` to append; prefer this over `health_backfill_sheets.py`, which trips the 60-reads/min quota.
- `../scripts/health_inventory.py` — read-only sweep of every data type for a window, so "pull all of it" is answered by evidence rather than by a fixed list (authored 2026-11-11, not yet exercised end-to-end — cross-check its first run against `health_backfill_sheets.py`).