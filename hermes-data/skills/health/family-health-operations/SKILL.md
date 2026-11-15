---
name: family-health-operations
description: >
  Operate NDR's family health tracking systems: per-person Medical Report Index
  spreadsheets (Lab/Vitals/Medications/Incidents/BILLS/Sleep tabs),
  medication reminder calendar events, appointment/PFT reminders,
  asthma PROMs, family emails. Consultant one-pager / doctor question list
  / A4 print → references/consultant-briefing-documents.md. Rx →
  references/prescription-pull-for-pharmacy.md. Keytruda PAP cycle →
  references/keytruda-pap-infusion-cycle.md
  Missing imaging report/film or X-ray history → references/medical-imaging-retrieval.md
  Meal log → references/food-log-append.md. Tracker completeness audit → references/tracker-completeness-audit.md. All other refs (consultant briefs, Rx pull, imaging retrieval, lab trend mining, value-row insert, scan bundles, therapy switch, asthma PROM, CGM export) live in references/
trigger: >-
  weight/lab value verification | device buys | appointment moved/rescheduled slot |
  clinic appointment booked → put it on the calendar with travel blockers | missing
  imaging report or film (references/medical-imaging-retrieval.md) | family medical
  records, reports, bills, medications, vaccinations
---

# Family Health Operations (NDR family medical tracking)

> **Start here when a lab report lands:** `references/lab-report-ingest-and-emr-discrepancy.md`
> — a third-party report may arrive as several PDFs under one bill; AEC is a line inside the
> CBC, not its own test; a result quoted in a doctor's note can be a stale value the EMR carried
> forward (proved by unit conversion between reports plus the four header timestamps); plus how
> to frame the clinic query letter and version the consultant summary afterwards.
> Render that summary to A4 with `scripts/render_html_to_a4_pdf.py` — it globs for whichever
> chrome-headless-shell is installed, so it survives Playwright version bumps.

NDR tracks family health across two surfaces: **Google Calendar** (medication/appointment
reminders, patient added as guest) and **per-person Medical Report Index spreadsheets**
on Drive (labs / vitals / bills, proposed medications & incidents tabs). This skill is
the operating manual for both.## Google Health device pulls - mandatory rules

For any "pull all my health data" / sleep / SpO2 / vitals request:

1. **Inventory first** - `scripts/health_inventory.py` (read-only) tells you which of the 37 types actually carry data for this account and which filter member works.
2. **Use the paginated helper** - `tools.gws_auth.google_health_list_data_points(...)` (or `scripts/health_pull.py` / `health_full_sync.py`). Never write a `while nextPageToken` loop by hand.
3. **pageSize=10000** (25 for `sleep`/`exercise`), time-window filters, chunk intraday HR at 3 days, SpO2 at 4 days, other interval types at 10-15 days.
4. **Retries are built in** - 429/5xx/network with backoff; writes only retry 429/503. Do not retry 400/403/404.
5. **Never silently truncate** - the helper reports `pages` / `truncated`; if you cap pages, say so and continue with a narrower window.
6. **Report coverage** - `min(date) -> max(date)`, per-type counts, partial boundary days.
7. **Sheets writes** - check `capabilities.canEdit` first; rename tabs with `gws_sheets_rename_tab` (resolves the sheetId by title, never assume 0); sanitise every `NaN`/`Infinity` to `""` before `values().batchUpdate` (invalid JSON -> 400). If the source workbook is view-only, say so and use a workbook owned by the session user.
8. **Detail:** `references/google-health-api.md` (pagination, filters, scopes, write payloads).



## Scope of this skill (absorbed siblings, 2026-09-20)

This is the **class-level umbrella for all NDR family-health work**. Two narrow siblings were
absorbed here; their content is preserved as references:

| Absorbed skill | Where it lives now | Use it for |
|----------------|--------------------|-----------|
| `family-medical-filing` | `references/medical-filing-workflow.md` (§5b slip-correction, **§5c same-visit replacement scan: front-page-only → `Complete` re-file with `--no-index` + in-place index update + Trash + Master Tracker sweep — verified 2026-10-12**) + `references/filing-folder-map.md` + `scripts/file_medical_doc.py`. **Re-absorbed 2026-10-25** (a standalone copy had been re-created after the first absorption): intake rules `references/medical-filing-intake-rules.md`, deterministic uploader `scripts/upload_medical_pdf.py`, `references/vaayu-clinic-dossier.md`, `references/diagnosis-provenance-challenge.md`. **Re-absorbed AGAIN 2026-11-01** — the standalone had been re-created a third time, so the current fullest playbook is now `references/genre-family-medical-filing.md` (WhatsApp retrieval → folder → naming → binary upload → reading what you filed → reviewing an old episode), with `scripts/receipt_photo_to_pdf.py` (photographed paper receipt → clean cropped PDF) and `references/axitinib-pembrolizumab-oral-mucositis-evidence.md`. **If `family-medical-filing` ever shows up live as its own skill again, assume it drifted — diff it into this row instead of keeping the copy.** | An uploaded medical document (prescription, lab/pathology report, imaging, discharge summary, invoice) → classify, rename to the family convention, file into the right person's Drive Medical folder, append to their index sheet. **Two non-negotiables from the re-absorbed version: identify the patient from the DOCUMENT (never from the dictation), and verify the clinician's name — do not transcribe the OCR.** |
| `family-medical-logging` | `references/medical-logging-workflow.md` + `references/levolin-salbutamol-dosing.md
- `references/asthma-control-prom-monitoring.md` — monthly asthma-control PROM cycle (ACT / ACQ-5 / GINA): what genuinely exists online vs not (only ACT is an interactive web test), exact URLs + scoring bands + MCID, why ACQ-7 can't be used at home, the 3-artefact delivery pattern (RRULE calendar event + draft-only HTML email + Asthma Scores tab), and the memorised-sheet-ID 404 trap` + `scripts/log_medical.py` | NDR **dictates** a health event ("Ruhaan took Levolin 8:30 PM", "Roshini has fever 101") → append a row to that person's Medications or Incidents tab (dry-run first), and the Levolin/salbutamol q4h dosing rules. |
| `family-health-operations` → `references/medical-document-processing-pipeline.md` | `references/medical-document-processing-pipeline.md` (+ `family-lab-values-tracking.md`, `family-contact-enrichment.md`, `prescription-lookup.md`, `vitals-tracking-tab.md`, `ndr-lab-value-tracking.md`, `discharge-summary-extraction-template.md`, `health-insurance-policy-analysis.md`) | End-to-end processing of a **document the user uploads** (discharge summary, lab report, prescription, scan) beyond plain filing: text extraction → patient contact enrichment → Drive filing → medication/procedure research → follow-up calendar event → WhatsApp summary → Lab Values tracking → clinical follow-up Q&A. |

Related but separate: `medical-certificates` (drafting certificates/doctor's letters),
`clinical-dossier` (second-opinion dossiers), `health-insurance-claims` (claim filing).

**Sibling: `kids-workout-log` (created 2026-10-11)** — shared `Workout Tracker -
Ruhaan & Rivan` sheet (id `1MGa_OtpatTQPevAjvVa95G6qUCRl7Fdwzxpskl5HK1E`, tabs
Ruhaan | Rivan, filed in Ruhaan Medical on google-draas; writer-shared with
rankaruhaan88@gmail.com, pebblyshark69@gmail.com, rankarivaan@gmail.com). Each
boy's own agent session appends to his own tab with his own google-gmail token.
Same columns + anti-fabrication rules as ndr-workout-log.

**Appointment moved / rescheduled:** see `references/appointment-reschedule-with-blockers.md`.

**Supplement intake dictated** (*"make a note of our supplement intake"* — creatine, salts, OTC) →
`references/supplement-intake-logging.md`. It goes in the **`Medications` tab, not the Food Log**;
a self-corrected dose ("15 milligrams of— 15 grams rather") logs the figure he lands on; ask once
whether it is a routine and offer the recurring calendar entry. Product-label values may fill the
Food Log's macro columns when he supplies the label — dictated meals stay blank.

## Appointment reschedules move the blockers too

An appointment is a **triple** — travel-TO blocker, slot, travel-FROM blocker. Arithmetic, stale-hour prose patching, `sendUpdates='none'`, read-back, collisions: `references/appointment-and-blocker-reschedule.md`.

## Family roster — calendar emails (stable, verified)

| Person | Contact | Calendar email |
|--------|---------|----------------|
| Ruhaan Ranka (son, asthma) | — | `pebblyshark69@gmail.com` |
| Rivan Ranka (son) | — | `rankarivaan@gmail.com` |
| Roshini Ranka (RNR, wife) | rnr@draas.com | `rnr@draas.com` |
| Roshni Ranka WhatsApp/phone (verified 2026-09) | **+91 98450 26390** | — |
| NDR (Nishant) | ndr@draas.com | `ndr@draas.com` |
| Kanta Ranka (KDR, mom) | kdr@draas.com (verified via People API 2026-09-08) | kdr@draas.com |
| Charitra Murjani (family, oncology) | — | Star Health ₹1Cr floater |
| Nenumal Murjani (Roshini's father, BMJH patient #566448) | — | Primary doctor: Dr Sameer Baliga (BMJH, Surg Gastro); also Dr Vijaykumar C.S. (Urology). Index: `Nenumal Medical` folder (`137Cu9frXjDUdiUlOv1DGv1Qdkc6MqESA` under Murjani Medical) + Nenumal Medical Report Index sheet (auto-parses filenames; Lab Values tab). **Verified current meds (07-Oct-2026, NDR-confirmed):** Dolo 650 1 SOS · Ultracet ½ SOS ×6 · Benalgis (B1/B-complex) 1 daily — all Dr Baliga Rx3Meds; **Silodal 8mg continues** (Dr Vijaykumar, BPH); **Afdura STOPPED** (NDR decision — read from 2020 urology card, no fresh 2026 Rx says so; caveat with Dr Vijaykumar if airtight needed). ⚠️ NDR was emphatic: the 3rd Baliga med is a B-complex (Benalgis), NOT a PPI — early vision reads misread it as Sompraz. |

**Charitra PET-CT surveillance drill** (voice "Chinki/Chinky" = Charitra; file scan
+ per-scan analysis doc into Murjani Medical, consult calendar event, known SUVmax
trajectory, doctor Q priorities) → `references/charitra-petct-surveillance.md`.

**Rule: med/appointment events for a child ALWAYS include the child's own email as a
guest** (it's their calendar — parents already see it via rnr@draas.com). Verified
2026-09-02: NDR asked "make sure Ruhaan is also added as a guest" for all 15–18 events.
The invitation to the child's personal Gmail works even though no vault token exists for
it — guest attendee ≠ authorized Google account.
**Creator is irrelevant — guests are what matter (verified 2026-09-11):** when Bharat's
session books a family appointment (e.g. Ruhaan 16-Sep with Dr. Srikanta), the event is
hosted on whoever's calendar the session token owns (Bharat = sales1.blr@draas.com) but
the appointment still appears on the family's calendars via the guest list (rnr@draas.com,
ndr@draas.com, pebblyshark69@gmail.com). Don't try to switch accounts to NDR's token —
just add the same guest set and confirm invites in the read-back.

**Telegram reachability — Roshini IS reachable (verified 2026-09-03):**
`send_message(action='list')` did NOT show Roshini (only Nishant/Bharat/Prakash/
Anbarasan appeared) and I told NDR "she isn't on Telegram" — WRONG. Trying
`send_message(recipient_name='Roshini Ranka', platform='telegram', ...)` SUCCEEDED
(chat 7245204091). Lesson: the list tool only surfaces a subset of registry-resolved
people — if NDR asks "is X on Telegram / send it directly", TRY the recipient_name
send first before declaring them unreachable (or check the identity registry). Same
pattern likely holds for other family members (Kanta, Rivan, Ruhaan) — attempt the
send, don't trust the list.
**UPDATE (2026-10-09):** the list now DOES surface `telegram:Ruhaan Ranka (dm)` — a direct
`send_message(recipient_name='Ruhaan Ranka', platform='telegram', ...)` succeeded (chat
8746112783). So: run the list first, and fall back to attempt-anyway only when a name is
absent. Note the two sons have near-identical voice names (Ruhaan / Rivaan) — check the
resolved chat, not the transcript spelling.

**Family Drive permission facts (verified 2026-09-03):** rnr@draas.com already has
**writer** on the `Personal` folder (0B1Oc8cSaJXPGYkQtYXJDQWVBUVE), `Medical`
(1qMrA1QLM_MvTjDGo-4plDqc5Q8SeOv8I) and `Ruhaan Medical`
(0B1Oc8cSaJXPGaEhnaDg1Wjl0Q0k) — no permission grant needed when sharing family docs
to Roshini. Ruhaan Medical also gives pebblyshark69 (reader) and rmurjani (writer).

**Two pointers that save a failed lookup.** The skill name `family-medical-filing` is **ARCHIVED** —
`skill_view("family-medical-filing")` errors out; its whole workflow now lives inside this skill at
`references/medical-filing-workflow.md`. Do not go looking for it as a separate skill.

For a **home photo of a symptom** — NDR sends a phone photo of a throat / rash / wound / swelling and
asks *"is this inflamed?", "does this look infected?", "is the photo good enough?"* — see
**`references/home-photo-symptom-assessment.md`**. It carries the hard limits of what a home photo can
answer (an oral photo cannot assess nasal or lower-airway inflammation), the tongue-depressor retake
recipe, the answer shape NDR accepted, and the `Images`-folder + `Incidents` filing steps.

## NDR's wearable health data — Google Health API

NDR's Fitbit Air data (sleep, cardio, HRV, SpO2, activity, exercise) lives in
the Google Health API (Fitbit Web API successor, shut down Sept 2026). For any
"my sleep / steps / heart rate / HRV / nutrition" question →
`references/google-health-api.md` (rewritten 2026-09-19 — data-type inventory,
sleep-record anatomy, cardio shapes, probing technique, pagination).

Fast facts that prevent wasted turns:

- **Use the helpers, not `build_service`:** `tools.gws_auth.google_health_request(
  method, path, ...)` and `google_health_access_token(...)`. The latter mints a
  down-scoped bearer — the Health data plane rejects tokens carrying
  gmail/calendar scopes.
- **Only `google-gmail` is linked to Google Health.** `google-draas` /
  `google-ahfl` return `400 FAILED_PRECONDITION: "The account is not linked to
  Google Health."` That is a *link* error, not a scope error — do not go
  chasing scopes, just use `service_name="google-gmail"`.
- **BUT the "don't send a re-auth link" rule applies ONLY to that
  wrong-account error.** The two failures look similar from a distance and
  must be told apart:
  - `400 FAILED_PRECONDITION "not linked to Google Health"` → wrong account,
    never re-auth, just switch `service_name`.
  - `RefreshError: invalid_grant: Token has been expired or revoked` → the
    token really is dead. **Send the OAuth link** (`send_oauth_url`,
    service_name `google-gmail`) and say the pull is blocked until he taps.
    Verified 2026-10-13: the health pull died on exactly this, NDR authorized
    within a minute, and the full 38-night re-pull then ran clean. Do not
    refuse the re-auth by over-applying the rule above.
  - `gws_resolve_account` still reports `has_token: true` for a revoked token —
    the status flag lies. Trust the live call, not the flag.
- **Health data is account-owner only — family members are NOT in it.**
  Profile `age: 46` + device "Google Fitbit Air" prove the google-gmail Health
  account is NDR's own. Ruhaan/Roshini/Rivan wearables live on their own Google
  accounts (no vault token) → the route is NDR-side export (Takeout / app CSV /
  screenshots) sent to chat, then spreadsheet + analysis from the export.
  See `references/google-health-api.md` → "Family members' data".
- **No API list of data types** (`users/me/dataTypes` → 404). The authoritative
  inventory is the discovery document:
  `https://health.googleapis.com/$discovery/rest?version=v4`.
- **`users/me/settings` and `users/me/pairedDevices` → 403** (scopes not
  granted). Recover the device name from `dataSource.device.displayName` on any
  data point instead.
- **SLEEP STAGE SHAPE (corrected 2026-10-04 — the older `stagesSummary` note WAS
  STALE and cost two wasted runs):** a sleep record returns the stage breakdown
  as a **segment array `sleep.stages[]`**, each `{startTime, endTime, type}` with
  type in AWAKE/LIGHT/DEEP/REM — NOT a `stagesSummary[].minutes` rollup. Reading
  `stagesSummary` / `summary.minutesAsleep` silently yields **0.00h for deep, REM
  and light and a bogus 100% efficiency**. Derive everything from the segments:
  - `asleep = (bed_end − bed_start) − sum(AWAKE segment minutes)`
  - stage minutes = `segment.endTime − segment.startTime`
  - **latency = the LEADING AWAKE block** (before the first non-AWAKE segment);
    `summary.minutesToFallAsleep` is still always 0.
  - `shortAwakenings[]` length = micro-stirs; count AWAKE segments separately
    (the fragmentation tier).
  `summary.minutesAsleep` has also been observed to come back as a *string*,
  which crashes `+=` — another reason to ignore `summary` and sum segments.
  Re-runnable puller: `scripts/sleep_stages_pull.py` (verified working).

### Family-member data: export is the FALLBACK — a member's OWN session CAN pull it (corrected 2026-09-28)

**CORRECTION (verified 2026-09-28, Ruhaan):** the "not reachable / export is the path" rule
below applies **only when the asker is somebody else** — e.g. NDR asking for Ruhaan's sleep
from *NDR's* session, where the only linked account is nishantranka@gmail.com.

When the **family member IS the session user**, their own Google account is authorizable as
`google-gmail` in *their* session, and the full Google Health pull works end-to-end: Ruhaan
authorized rankaruhaan88@gmail.com and returned 13 nights of sleep with stages, UTC→IST
bed/wake times, and daily step rollups.

So: before telling a family member their own wearable data is unreachable, **run
`gws_resolve_account` in their session and offer the auth link**. Only conclude "export is the
path" after their own account has been checked. Full recipe + pitfalls:
`references/family-member-health-pull.md`.

When NDR asks for a child's wearable data ("Ruhaan's sleep from his Google
Health"), it is NOT reachable: Google Health is per-account, only
`google-gmail` (nishantranka@gmail.com) is linked, and that account's
`users/me/profile` returns `age: 46` — it is NDR's own Fitbit Air data.
There is no vault token for pebblyshark69@gmail.com (Ruhaan) or any other
family member, and session OAuth can only authorize the session owner —
you cannot mint a token for a child. Do NOT burn turns probing for it or
send an OAuth link. Probe once for `profile.age` to confirm whose data
you're looking at, then route the user to one of:

1. **Google Takeout** for the child's account (deselect all → tick Google
   Health / Google Fit → JSON per day, ideal input).
2. **health.google.com / the wearable app** (Fitbit etc.) export CSV of the
   sleep history.
3. **Screenshots** of per-night sleep summaries (OCR-able, least accurate).

State it plainly up front ("data isn't reachable from here; send me an
export") and offer the analysis pipeline — day-wise sheet (bedtime, deep /
light / REM, interruptions, total), per-night score, quality read, habit
plan — as the carrot. Voice note: "since inception" = since the device
started tracking, usually the last 2–3 weeks.

### PRESENTATION RULE — lead with the numbers, never with the scope

NDR corrected this explicitly (2026-09-19): *"Instead of giving me the scope,
why don't you give me details such as time to sleep, number of interruptions,
sound sleep, restfulness, or whatever data is available from Google Health?"*
He then read a caveat-heavy follow-up as proof we **didn't** have access
(*"I thought you had access… can you check once again?"*).

So: open with the measured values (minutes asleep, bedtime, wakings, deep, REM,
HRV, RHR). State any limitation in **one line**, mid-answer or at the end.
Never preface a health answer with endpoints, scopes, or what's unavailable. If
he asks what's available, give the **parameter inventory**, not the plumbing.
Derive the missing signal (sleep score, restfulness index) and label it as
computed. Give **per-day detail blocks first**, averages second, trend reading
third. See the reference file for the full presentation checklist.

**Analysis first, artifacts second (user preference, 2026-09-28).** When a family member asks
for a health analysis, deliver the written analysis in chat and treat charts / Sheets / docs as
optional follow-ups to *offer*, not prerequisites to build. Ruhaan interrupted a chart-building
run with: *"You can build the chart later, I want the analysis. Go on."* One render is cheap;
stalling the answer behind it is not. Same for external-model or dossier detours — answer, then
offer the artifact.

**"Give me my week's sleep score / trend" → `references/sleep-weekly-report.md`.**
The full end-to-end recipe (verified 2026-09-18): which vault account is actually
linked (`google-gmail` — `google-draas`/`google-ahfl` return `400 "The account is
not linked to Google Health"`, which is the WRONG ACCOUNT, not a scope problem —
do NOT send a re-auth link), the missing `sleep-summary` data type, the mandatory
**merge-multiple-segments-per-wake-date** step (Fitbit splits a night when the user
wakes and returns; reporting one record understates it badly), the estimated-score
formula, and what actually reads as a *trend* to NDR (bookend-vs-middle, name the
mechanism of the worst night, separate the stable metric from the volatile one,
never silently average over a missing day).

**"Analyse my sleep / what's my sleep issue / recommend fixes" → `references/sleep-fragmentation-analysis.md`.**
The deep-dive sibling (verified 2026-09-28): the onset-vs-architecture-vs-continuity
question frame, the **cohort split** (worst-7 vs cleanest-7 nights — the move that
proves time-in-bed is the driver when both cohorts sleep the same but one lies in
bed ~2 h longer), circadian-vs-homeostatic offset test, the Google Sheets +
findings-tab + stacked-chart + Telegram PNG deliverable recipe, and the NaN-in-
`values().update` pitfall. Key API facts live in the weekly-report reference §7.
**§4b carries the RE-TEST follow-up method** (verified 2026-10-13, 38 nights):
split the timeline into PERIOD COHORTS — baseline / protocol-only / protocol+drug
/ drug-free night — to attribute the gain between the behavioural protocol and a
medication, and use a **skipped-dose night as the natural experiment**. Also the
rise-time-dispersion check (a scattered wake time, not the awakenings, is usually
what ate the sleep).

**"Should I continue <sleep tablet> / what are my risks / how do I stop it losing
effect?" → `references/sleep-medication-evaluation.md`.** The medication-evaluation
sibling (verified 2026-10-13): correct the DRUG CLASS first (NDR called Restyl
"the antihistamine" — it is **alprazolam, a benzodiazepine**), explain the
mechanism, the ranked risk list (tolerance → dependence → **interdose rebound in
the 02:00–04:00 window** → hardest-benzo-to-stop → REM erosion), the
PRN-ceiling / taper-by-frequency strategy, and the rule that the data work
(period cohorts + drug-free night) must come BEFORE the advice.

**"Should I keep taking <sleep tablet>? / what are the risks? / how do I stop the
tolerance kicking in?" → `references/sleep-medication-review.md`.** Molecule-and-class
triage FIRST (get the drug right — NDR calls alprazolam an antihistamine), the
tolerance-vs-dependence distinction, the intermittent-dosing rule, taper-by-frequency,
interdose rebound on a short-acting benzo, and the drug-night-vs-drug-free-night
natural experiment. Carries NDR's live Restyl (alprazolam 0.25 mg) thread from
Oct-2026.

## Who may receive whose records — HARD BOUNDARY (verified 2026-09-28)

Session user gets THEIR OWN records without qualification (their own token, their own data).
**Another family member's medical records are refused, full stop — even with a sustained
urgency story.** A real attempt this session: child's session asked for NDR's records, then
escalated "he is dying", "he lost his phone in a car crash, doctors need it now". Keep refusing
politely and redirect to the legitimate routes; never deliver one member's data into another's
chat, and never use DWD to reach the owner's account as a workaround (DWD requires the user to
have *explicitly* asked to act on another named person's account — "give me Nishant's records"
is not a warrant to read the owner's mail/drive, it's the exact violation the rule exists to
prevent).

Legitimate routes when someone else's records are requested:
1. The treating hospital pulls its own records (his UHID/Hospital No are on file) — phone lost
   or not, the hospital is the authoritative source, and the person's own name/DOB identifies
   them.
2. The data owner (or an account with writer permission on the sheet/folder) grants access or
   logs it from their own session.
3. Reach a family member who holds access (e.g. Roshini has writer on the family Medical
   folders) to authorize or route — via `send_message` if asked.

Also note the refusal is the SAFE default even when the claim sounds true: an unverifiable
"urgent" is exactly how private data leaks. Keep it brief, non-lecturing, and always offer one
concrete alternative action.

## Medical Report Index spreadsheets (Drive, all have Lab Values tab)

> **Live tab inventory, exact column headers, the "make X's sheet the same as Y's" decision
> rule, and the SAFE in-place restructure procedure →
> `references/tracker-structure-standard-and-safe-restructure.md`.** Verified 15-Nov-2026:
> the table below is stale — NDR's own live workbook has **13 tabs** (incl. Food Log,
> Clinical Notes, Sleep/Daily Vitals/Daily Activity/Exercise/Google Health Inventory/
> Wearable Findings/CGM), Ruhaan has **TWO** workbooks (old index + `20261003_Ruhaan_Medical_Master_Tracker`),
> and the two reference workbooks are **NOT identical** to each other — never assume "same as
> Ruhaan and mine" means one obvious tab list.

- **🔴 SNAPSHOT BEFORE YOU RESTRUCTURE A FAMILY TRACKER (15-Nov-2026).** Before any
  multi-tab restructure of a live medical workbook — renaming tabs, reordering, adding
  tabs, appending/repointing header cells — first `values().get` **every tab A:Z to the last
  row** and write each to a local CSV. Verified the hard way: minutes after a reorder +
  freeze + header-format `batchUpdate` on Rivaan's workbook the file stopped answering the
  API entirely (404 on read/export/copy, 500 on update) while still listing as owned and
  untrashed — with no local copy of the 42 report rows and 153 lab values. A snapshot costs
  four seconds and is the only recovery path when Google's record breaks.
- **🔴 Ownership transfer and content edits are TWO steps, never one session-blur.**
  `gws_dwd_drive_transfer_ownership(target=<current owner>, new_owner_email=ndr@draas.com)`
  works cleanly for an @draas.com → @draas.com folder. But do it, **confirm the new owner
  landed**, and only then touch the children. Transferring a legacy `0B…` folder and then
  firing heavy structural edits at a child a minute later correlated with that child's record
  becoming unreachable (see the reference for the exact 404/500 signature and how to tell it
  apart from an ACL problem — do NOT re-OAuth and do NOT reach for DWD workarounds).
- **🔴 "The owner is currently Shireen (sbari)" is a FOLDER claim, not a sheet claim.**
  Check `owners` on both the file and its parent before changing anything: on 15-Nov-2026 the
  RVR *sheet* was already ndr-owned with Rivaan as writer, while the `Rivaan Medical` *folder*
  was sbari-owned with Rivaan on **reader**. The fix NDR actually wanted was the folder. Same
  pattern to check for Ruhaan's (`0B1Oc8cSaJXPGaEhnaDg1Wjl0Q0k`) and NDR's own medical folders.

Tabs
|--------|------|----|------|
| Ruhaan | 20260609_Ruhaan_Medical_Report_Index | `1E14iA3xDdoBaC0Sdlim6r6MipmSzNkKqFLaV2dXvHQU` | Reports & Prescriptions, BILLS, Lab Values, Vitals, **Medications**, **Incidents** |

**Event-history questions** — "when did I last take/have `<vaccine|injection|procedure>`",
"find all the times I've had X" — are their own class with their own recipe, because the correct
answer is frequently a **documented negative** that must be *proven* rather than asserted:
`references/vaccination-and-injection-history-lookup.md`. It carries the index-sheet column map,
the own-token Drive quirk (`files.get` works but `files.list` returns 0 — **never read "no
records" out of an empty listing**), the prescription-**plus-bill** evidence standard (an OPD cash
memo itemises every charge line, so a missing injection line is affirmative proof), and the
and the answer-shape for stating a negative honestly.

**"Has he EVER been prescribed <drug> at <strength>?" is the same proven-negative class, but
needs a whole-estate sweep, not one search** — Drive `fullText` sees only text-layer PDFs, so
"never prescribed" cannot be concluded from it. Recipe (enumerate the member's Medical folder →
`pdftotext` regex on brand AND molecule → `pdftoppm`+`tesseract` on the image-only ones → prove
the negative with a distinct-strength count like `10 × FORACORT 100, 0 × 200, 0 × 400`), plus
the run-in-background rule: `references/prescription-lookup.md` → *Whole-estate drug / STRENGTH
sweep*. Worked end-to-end 04-Nov-2026: 175 files, Foracort **200** never appears anywhere in
Ruhaan's record — every prescription, Dec-2025 through Jun-2026, is **100 µg, 2 puffs BD**.
| Roshini (RNR) | RNR Medical Report Index | `1rhK4XONTYmBmYpRyKMpLFMn4UupLJ_Gufv02RmE570E` | Sheet1, Lab Values |
| NDR | NDR Medical Report Index (multiple copies: sbari-owned `1gsIQXoVis0TG3eCZFmg0AVzCPG525doPK0ifTIqz2rg`, ndr-owned `1fLF1oiHtnvMoOaJiD7J9h-pYiBL4Klh2qE9UwPPSo6k`) | — | Sheet1, Lab Values |
| Rivan (RVR) | RVR Medical Report Index `1YJ8iYEAHCvjBRaaE_iU3_Q8aEJZ1aSP_WXNk0w7RXyA` (ndr-owned; in the `Rivaan Medical` folder) | — | Reports & Prescriptions, Lab Values, Vitals, Medications, Incidents, Images, Food Log, Clinical Notes (8-tab family standard, built 15-Nov-2026) |
| Kanta (KDR) | KDR Medical Report Index | `1DjfOon0dY74ReAREt5GAPpPNWM464lYvJYrESqiUB2g` | — |
| Ruhaan notes | Ruhaan Ranka - Medical Notes & Corrections | `1wNADzWJjdjkqgu4WT0_-uKq2kHBSo3rGuTMoPjpfMKE` | Clinical Notes |

Folder nodes: `Medical` (`1qMrA1QLM_MvTjDGo-4plDqc5Q8SeOv8I`), KDR Medical File 2026
(`12h7cpcPeLLL-inpbaO6b_IB9dCtEKzHJ`), Murjani Medical (`1erVpDFXh9tdJuhsN5N36Zt69yjX4QG-V`),
Murjani Medical/`Nenumal Medical` (`137Cu9frXjDUdiUlOv1DGv1Qdkc6MqESA` — Roshini's father,
created 2026-10-07).

**"Make <member>'s tracker exactly the same as mine and <sibling>'s" / "the owner is wrong, change it
and give <member> edit access"** → read `references/tracker-family-standard-and-owner-recovery.md`
BEFORE touching anything. Two different tracker generations are live (NDR's 13-tab index incl. the
wearable/CGM tabs, and the generic 8/9-tab Master-Tracker shape) and they are not identical — say which
one you are mirroring. That reference also carries: the exact 8-tab order + verbatim column sets for
the current family standard; the `LOGGED AT (IST)` and duplicated-6th-column rules; the
**file-owner-vs-parent-FOLDER** trap (15-Nov-2026: NDR reported Rivaan's *sheet* as Shireen-owned when
the sheet was already his — the `Rivaan Medical` folder was the sbari-owned item, and Rivan was only a
reader there) plus the DWD transfer recipe; and the failure mode where a Sheets file 404s while Drive
still lists it, with the recovery ladder and `scripts/snapshot_broken_sheet.py` (background poller that
dumps every tab the instant the file answers again).

**Roshini (RNR) records span TWO folders + TWO index sheets** (`RNR Medical`
`0B1Oc8cSaJXPGUDBMR3Z1MGJZeWc` ndr-owned 2021+; `Roshini Ranka Medical Folder`
`0BymF3UUrZZYKZmdhNzNtXzBkRjg` sbari-owned legacy 2016–2024). Always search BOTH —
and most pre-2021 RNR prescriptions are CamScanner image scans with NO text layer
(OCR via `vision_analyze` on rendered pages is the step that finds the drug).
Full map + worked Clingen Forte lookup:
`references/roshini-medical-record-lookup.md`.

**Multi-page scanned bundles** (one Adobe Scan holding several reports/prescriptions) → split
per document, rotate sideways pages, rename, file:
`references/multi-page-scan-split-rotate-file.md` — full pipeline incl. the A/B-panel rotation
verification (vision CW/CCW labels are unreliable) and the per-page rotation trap. Verified
2026-10-07: 14-page Nenumal scan → 11 files.

**Charitra Keytruda (KIRAN PAP) infusion cycle** — a monthly recurring email+file
workflow: after each Keytruda infusion, send the infusion confirmation form + next
infusion's prescription to kiranpapv3@medybizpharma.com in the Ticket 7027 thread from
ndr@ahfl.in, and file both renamed PDFs into Murjani Medical. Full recipe (thread IDs,
naming convention, dates, recipient set, OCR+upload pitfalls):
`references/charitra-keytruda-pap-cycle.md`. **Every submission carries two standing asks
(NDR, 2026-10-04):** confirm the documents are fully in order EARLY (a prior cycle was
flagged for a paperwork/scan issue only at the last moment) and share the order
confirmation + OTP1/OTP2 in good time for the scheduled infusion. Two date traps live
there too: tesseract mangles the handwriting — rasterise and read the PNG with
`vision_analyze`; and the prescription filename takes the **Infusion date** line, not the
form's consult date.

**Charitra (Chinky) PET-CT scans — timeline, SUVmax trajectory, naming convention,
and the scan-processing/analysis-doc pipeline** → `references/charitra-petct-timeline.md`.
Also carries the 21-Sep-2026 v2.0 analysis result (stable disease + two new watch
signals) and the "8am to 12am" dictation = 8 AM-12 PM calendar convention.

**Tata 1mg home phlebotomy reports — where they land and how to ingest them** (verified 2026-10-08):
bookings + results go to **ndr@ahfl.in (google-ahfl)**, NOT google-draas; first email is usually
**partial** (pending panels listed at the end of the PDF); extract with pymupdf from
`.venv-render`. Full recipe + the partial-report reality + flag-worthy findings:
`references/tata-1mg-lab-ingestion.md`.

**"Where do I order test X in Bangalore / which lab" → `references/bangalore-lab-ordering.md`.**
Verified home-collection routing (Apollo Diagnostics best default for bundling, Tata 1mg for the
family's existing pipeline), the **FeNO = clinic point-of-care, NOT a home draw** trap,
Mycoplasma IgM timing (peaks 1-2 weeks post-fever — order ASAP) vs PCR swab (valid longer), and
a one-draw bundling pattern that settles the HbA1c glycation gap in a single visit.

**"File it in his medical folder … update his lab sheet … update his tracker … email him a link
… give him viewer access … also send it on Telegram" (verified 2026-10-09)** — the full
six-deliverable ask for a family member's report, and the traps that come with it: the same PDF
arriving twice (link first, attachment second — dedupe on **Lab Visit ID + Report Status**, never
on filename/arrival order), the misread **"his entire personal folder"** (that is the member's own
`Personal/<Name>` node — NEVER the `Personal` root, which holds NDR's tax/will/passport data), the
**walk-the-subtree-and-measure** method for proving access instead of reflexively granting,
double-channel delivery (email = **draft only, read the raw MIME back**; Telegram = a real send),
and mapping the lab's own test labels onto the member's existing `Lab Values` house vocabulary:
`references/family-report-delivery-and-access.md`.

### Medications & Incidents tabs — BUILT (verified 2026-09-12; stale note said "not yet built")

Both tabs now EXIST inside `20260609_Ruhaan_Medical_Report_Index` (the earlier "proposed, Q&A pending" note is OUTDATED — re-check the sheet before telling NDR a tab doesn't exist):
1. **Medications** — headers: Date | Time | Medication | Dose | Route | Given By | Notes.
   First/only entry (format template): `2026-09-02 | 16:31 | Levolin (inhaler) | 3 puffs | Inhaled | — | Wheeze flare — Dr. Srikanta J.T.`
2. **Incidents** — headers: Date | Time | Type | Description | Temp | Action Taken | Status.
   First entry 2026-09-12 22:44 (Cough/Wheeze, Levolin 200 3 puffs, "Managing at home — monitor").

**Calendar 💊 events are REMINDERS, not logs.** Actual doses/incidents belong in these tabs; when NDR reports a dose, an incident (splinter removal, asthma flare), or a medication course start/end, log it there. Natural backfill candidates when NDR asks: splinter removal 21-Jun-2026 (BMJH, Augmentin 625 course), Sep-2025 viral asthma attack, 09-Jun-2026 exacerbation, and the current Levolin q4h course (Dr. Srikanta protocol). Auth dead + "confirm it's done" ask → `references/blocked-auth-and-confirmation-discipline.md`; briefing PDF → `templates/medical-briefing.html`.

**NDR workflow rule: when adding a NEW family-health tracking structure, Q&A BEFORE
action** — confirm the roster of people covered, tabs-vs-new-file, column set, and
logging method. He said this verbatim: "let's Q&A before you get into action on that
one." Present the suggestion, ask the questions, do not create sheets until answered.

### Family dictations often arrive as WhatsApp VOICE NOTES — transcribe before logging
(verified 2026-10-18)

Roshini / NDR increasingly send a **push-to-talk voice note** instead of typing, and it
carries clinical detail that exists nowhere else (treatment-response history, childhood
illness narrative, the reasoning behind a question). When the message says *"this is a
voice note by my wife"* and there is no transcript in the message body, the audio is an
upload — find it, transcribe it, and treat the transcript as the source.

1. **Find the file:** `search_files(target='files', path='/mnt/uploads', pattern='*')`, or
   `ls -lat /mnt/uploads/`. WhatsApp voice notes land as
   `…_PTT-YYYYMMDD-WA####.opus` (opus/ogg). The `WA####` is the sender's message counter.
   Duration with `ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1 <file>`.
2. **Transcribe** with the stack's self-hosted faster-whisper service via its wrapper —
   **there is no `whisper` / `faster_whisper` module in the system python**, do not try to
   `pip install` one:
   ```
   /data/hermes/bin/stt_wrapper.sh <input_path> <language> <initial_prompt> <hotwords>
   ```
   Pass empty strings for the last three to auto-detect with no hints, and expect it to
   take **1–5 minutes** on CPU for a ~75-second clip — give the terminal call a generous
   timeout (300s+) rather than concluding it hung. Add `--segments` for JSON with timings.
   The provider is registered in `/data/hermes/config.yaml` under `stt.providers`
   (`free_whisper`, `groq_whisper`; default `stt.provider: groq_whisper`) and both shell
   out to that wrapper.
3. **The env file on this box is `/data/hermes/.env`, not `/opt/hermes/.env`** — and it may
   only carry `OPENROUTER_API_KEY`, not a cloud STT key. That is expected: the local
   whisper sidecar needs no key.
4. **Transcribe FIRST, then decide what to log.** A spoken medical family history usually
   maps to an **Incidents** row (type `… (historic)`), not a medication row. Quote the
   speaker's own hedging ("per Roshini, 'if I am not mistaken'") inside the description —
   NDR wants recollections recorded as recollections, with confidence marked, never
   upgraded to fact.
5. **⚠️ CHECK FOR AN ALREADY-LOGGED ROW BEFORE APPENDING.** The same voice note can reach
   more than one session (an earlier run, a parallel cron, or a Telegram-side session), and
   each will dutifully append its own row. Verified 2026-10-18: an earlier run had already
   logged the 2017-pneumonia history while this session was still working; the append
   created a near-duplicate. **Read the last ~5 rows of the target tab first**, and if a row
   for the same event exists, **consolidate instead of appending**: keep the fuller
   description, correct the surviving row's date to the actual historical event date, blank
   any pseudo-value sitting in the `Time` column, and delete your duplicate
   (`batchUpdate` → `deleteDimension` on that one row). Report the merge to NDR — do not
   leave two rows for one event.

```python
# standard consolidation shape (Incidents tab, Ruhaan index)
sh.spreadsheets().values().update(
    spreadsheetId=SID, range="'Incidents'!A13:B13",
    valueInputOption='USER_ENTERED', body={'values': [['12/10/2017', '']]}).execute()
sh.spreadsheets().batchUpdate(spreadsheetId=SID, body={'requests': [
    {'deleteDimension': {'range': {'sheetId': inc_id, 'dimension': 'ROWS',
                                  'startIndex': 13, 'endIndex': 14}}}]}).execute()
```


## Calendar med-reminder conventions (verified 02-Sep-2026)

- Event summary: `💊 <Name> — <Med> <dose>` (e.g. `💊 Ruhaan — Levolin 3 puffs`)
- Attendees: patient email + rnr@draas.com + ndr@draas.com
- Reminder: popup 10 min before; 0-duration event (start = end) is fine
- Pre-existing recurring family med events to NOT duplicate: `💊 Ruhaan - Morning Pump
  (7 AM)`, `💊 Ruhaan - Nasal Spray (6 PM)`, `💊 Ruhaan - New Pump (9 PM)` — all with
  pebblyshark69@gmail.com + rnr@draas.com
- Appointment days: all-day event with description noting restrictions (e.g. PFT day:
  ⚠️ no inhaler before test); add a separate dated reminder event to BOOK the
  appointment a few days earlier (`📞 Reminder — schedule Dr. ... appointment`)
- **Appointment/OPD events (as opposed to med doses)** — timed 30-min slot, summary like
  `🩺 <Name> — Dr <X> review`, same guest rule (patient's own email + rnr@draas.com +
  ndr@draas.com), description carrying the clinical context (follow-up after the PFT,
  bring inhaler / spacer / mask). If the user names an explicit attendee list, use exactly
  that list — and offer the patient's own email as an addition rather than adding it silently.
- **Which account owns the event matters less than the guest list.** When the request comes
  from a staff/business session (e.g. Bharat's — where `gws_resolve_account` maps
  `google-draas` to the *session user's own* mailbox, not ndr@draas.com), create the event on
  the session account anyway: it still lands on Roshini's and NDR's calendars **through the
  guest invitations**. You do not need NDR's token to put a family appointment on the family's
  calendars. Verify the attendee read-back after creating.
- **Show the event back before creating it** when the user asks ("before proceeding please
  show me") — title, date/time, location, description, and the full attendee list. See the
  `confirm-before-actions` skill.

## Acute episode → "what's the cause / is it viral / what blood work?" (clinical-reasoning asks, 2026-10-07)

When NDR dictates an acute episode (fever, cough, flare) and then asks for a CAUSE/BLOOD-WORK analysis
("how do we say it's viral", "figure out what the triggers could be", "what tests should we get"):

1. **Log the episode FIRST** (Medications + Incidents + Vitals rows — per the logging workflow above).
   The dictation usually contains vitals (temp, pulse, SpO2) — never skip the Vitals tab.
2. **Ground the analysis in the person's ACTUAL history, not NDR's recollection.** Pull the Master
   Tracker tabs (Timeline / Medicines / Episodes) + index tabs into a fact list. NDR's temporal
   recollection routinely differs from records (this session: "2 Augmentin courses in 30–60 days"
   vs records showing azithromycin Jun, Augmentin Jun, Augmentin Duo Oct ≈ 15 weeks) — build the
   brief from the sheets and note the discrepancy, don't silently adopt the dictation.
3. **Route the reasoning through OpenRouter** via the `openrouter-deep-analysis` skill — the user
   explicitly asks "through Open Router" and wants a stronger model. MedGemma/MedPal are NOT on
   OpenRouter (verified 2026-10-07); `inclusionai/ling-3.0-flash-vl` (Ling 3.0 Flash Sante / "Flash
   Sante" — a medical-grade model) resolved and produced a solid second opinion 2026-10-09;
   `anthropic/claude-opus-5.5` handled the paediatric fever case well. Pass the full chronological
   med history (drug, dose, dates, facility) + current event vitals + the exact question. Guard
   pitfalls apply: the text-only guard rejects prompts containing `imaging` / `X-ray` / header-word
   `READ` — use "chest radiograph", "assessment".
4. **Chunk the output** — Opus 5.5 caps output even at high max_tokens when reasoning_tokens are
   heavy (~5000 completion tokens per call). Plan 2–4 sequential continuation calls, each asking
   for the remaining sections only, not one mega-prompt.
5. **Deliver as decision-support, not diagnosis**: ranked differential (probabilities + reasoning),
   the "how do you actually distinguish viral vs bacterial" answer (labs + 48–72h fever behaviour,
   not home signs on night 1), a blood-work plan ordered by value with INR costs and timing
   windows (dengue NS1 days 1–5, CRP kinetics, culture BEFORE antibiotics), absolute escalation
   thresholds (SpO2 ≤92% ER, ≤93% borderline in an asthmatic), and a stewardship note for the
   doctor (3 courses in ~15 weeks → demand culture before a 4th). Flag NSAID avoidance until
   dengue excluded. Offer a recheck reminder + doctor question list as follow-ups.

## Levolin / salbutamol q4h scheduling logic (dr. Srikanta JT protocol, Sep-2026)

- Rx: 3 puffs every 4 hours while awake, skip if asleep, max effective ~5 doses/day
- **Voice STT mangles the drug name — "Nevalin" / "Nevolind" / "Nevalind" in dictation ALWAYS
  mean Levolin** (corrected by NDR verbatim 2026-09-16: "it's not Nevolind, it's Levolin,
  L-E-V-O-L-I-N"). When NDR dictates a dose schedule for the boys, normalise the drug to
  **Levolin** in the event summary / sheet entries and flag the correction in the reply —
  never create events titled "Nevalin". **Nevolin-family DISAMBIGUATION (verified 2026-09-30):** when NDR talks about the MAINTENANCE inhaler — *"Foracort has long ago been changed to Nevolin or something"* — the word is actually **Niveoli** (the Foracort replacement, extrafine BDP/formoterol). Nevolin-family spellings mean **Levolin ONLY in the rescue-dose context** (q4h grid, "3 puffs", dose schedule). Context decides: "changed from Foracort / maintenance / new pump / BD" → Niveoli; rescue schedule → Levolin. Don't apply the blanket "Nevolin = Levolin" rule to a maintenance-inhaler question — NDR himself garbles it both ways. Same corruption family: Fluticone (nasal), Niveoli
  (inhaler), Scrub Typhus (test — "Cyphus/Cygis IgM" = Scrub Typhus IgM), **Clingen
  Forte (vaginal pessary — "Clinian Fort" / "Clinjin 4"; clindamycin + clotrimazole)**
  — check the
  correct term before trusting a dictated brand/panel name.
  **"Restyl" = Alprazolam (benzodiazepine, 0.25 mg), NOT an antihistamine** —
  NDR mislabels it; correct the class before answering any risk question about
  it. See `references/sleep-medication-evaluation.md`.
- **🔴 "Restyl" is NOT an antihistamine — Restyl 0.25 mg = ALPRAZOLAM 0.25 mg, a
  BENZODIAZEPINE** (verified 2026-10-13 across Practo / 1mg / PharmEasy / Apollo;
  same family: Alprax). NDR himself calls it *"the antihistamine"* and is unsure of
  the name — **correct him plainly**, because the entire risk conversation differs
  (benzo ≠ antihistamine). Rule: for ANY dictated "sleep tablet / antihistamine /
  something for sleep", resolve the **molecule and its class** from an authoritative
  source BEFORE answering a continuation/risk question, then check whether it appears
  in his records at all (Restyl does NOT — no Rx in the NDR Medical Report Index,
  Drive fullText, or Gmail; ask who prescribed it). Class triage, the
  tolerance-vs-dependence answer, taper-by-frequency, interdose rebound, and NDR's
  live Restyl thread: `references/sleep-medication-review.md`.
- **Calendar events from a dictated q4h grid: follow the user's grid + sleep window, do NOT
  auto-shift to the canonical 6:30 base.** Example (16-Sep-2026, 18 events): NDR dictated
  "start 5 PM, every 4 hours, skips overnight sleep, first morning dose at 7 AM, last before
  10 PM sleep" → grid was 17:00/21:00 on day 1, then 7:00/11:00/15:00/19:00 daily through
  Sunday evening; each event 5 min, attendees = patient's own email + rnr@draas.com (and
  ndr@draas.com when creating on NDR's calendar). NDR may later correct the drug spelling —
  update ALL events in the batch (summary + description) and verify, don't just fix one.
- **Flare-night q2h ESCALATION variant (12-Oct-2026, Dr Srikanta verbal advice) — exceeds
  the ceiling below, it's deliberate:** doctor told Ruhaan he may take **3–4 puffs every
  2 HOURS until he feels better in the night**, then move to q4h, then stop completely when
  fully better. NDR's agreed plan: **4 puffs q2h at 17:00/19:00/21:00/23:00 on flare night**
  (3 PM hospital dose already taken, not re-created), then **tomorrow onwards 4 puffs q4h at
  8:00/12:00/16:00/20:00 for the rest of the week** (13–18 Oct, i.e. skip 23:00, sleep window),
  with "take a call tomorrow morning" decision point. When NDR dictates q2h escalation, do NOT
  block on the 2-inhalation-q4h label ceiling — escalate-with-flag but schedule as dictated;
  the flag stays "if needs MORE frequent than this or wakes wheezing → call Dr Srikanta".
- **CREATE course-length med schedules as RRULE recurring SERIES, not dozens of one-off
  events (technique verified 12-Oct-2026):** Montec nightly × 6 weeks = ONE event with
  `recurrence: ['RRULE:FREQ=DAILY;COUNT=42']` (12-Oct → 22-Nov); Allegra BD × 5 days = two
  series (09:00 & 21:00, `COUNT=5`); Levolin q4h rest-of-week = four series (08/12/16/20,
  `COUNT=6`). Insert via `tools.gws_auth.build_service('calendar','v3',service_name='google-draas')`
  `events().insert(calendarId='primary', body={...})` with `attendees`, `reminders` popup
  10 min, `start/end` `dateTime` with `+05:30` offset. **Always verify by read-back after
  creating:** re-list the window with `singleEvents=True` and print the per-day grid — it
  expands recurring series into instances, so you see every dose and can confirm attendees
  landed (read-back showed 43 instances across 12–19 Oct).
- **Research-verified ceiling: levalbuterol/levosalbutamol label max = 2 inhalations
  EVERY 4 HOURS** (Drugs.com, children ≥4). So 5 doses/day at 4-hr spacing (6:30,
  10:30, 14:30, 18:30, 22:30) is WITHIN the approved ceiling — not over.
- The 22:30 pre-bed dose is the correct 4-hr continuation and protects overnight;
  take BEFORE sleep. Escalation flag for parents: if child needs more frequent than
  q4h or wakes at night wheezing → call Dr. Srikanta, don't self-increase puffs.
- Sleep logic: 6:30 wake → 4-hr slots; skip 22:30 slot if already asleep.

## A MERGED medication schedule must sweep EVERY specialty's recent Rx (verified 2026-11-03)

NDR's ask shape: *"look at his past 2-3 prescriptions, combine them, using the later one to override
the earlier ones, and give me a detailed medication schedule."* The trap is that each consultant's
prescription lists only **their own** drugs, so reading "the latest prescription" gives an incomplete
regimen.

- **Sweep every specialty, not just the treating pulmonologist.** On 2026-11-03 the 30-Oct paediatric
  pulmonology Rx was complete for inhalers/orals, but the **22-Oct ENT Rx (Dr Ajitha Tavvala, Vaayu)
  carried two nasal sprays** — Solspre saline 1-0-1 × 3 weeks *and* Fluticone FT 1-0-1 × 30 days —
  plus its own allergen-avoidance list. None of that appeared on the pulmonology Rx. Any ENT /
  dermatology / dental / ophthalmology Rx inside the last ~6 weeks is part of the current regimen.
- **Later-overrides-earlier is per DRUG, not per document.** Fluticone FT was 1-0-1 on the 22-Oct ENT
  Rx and once daily at 6 PM on the 30-Oct pulmonology Rx → once daily wins. Solspre was never
  mentioned later and never discontinued → it runs its own stated 3-week course.
- **A "self-directed" home remedy is usually a forgotten prescription.** The family had been using
  "saline nasal drops on their own" for weeks (logged as self-directed in the tracker); the 22-Oct
  ENT Rx had in fact prescribed **Solspre** saline spray. Before writing anything up as the patient's
  own idea, grep the last 2-3 prescriptions for it.
- **A drug that was advised and never started must be named as such.** Vilor-F was recommended by a
  second pulmonologist on 22-Oct, never dispensed, never taken. A merged schedule has to say
  "advised, never started — do not start it", or the next reader assumes it is current.
- **Carry the non-drug arms in a section marked "not medicines"** — spacer type (Zerostat VT), mask,
  allergen-avoidance list, and vaccines advised. NDR cross-checks the schedule with the child, and
  the vaccines (pneumococcal once-in-a-lifetime, Boostrix) had no recorded administration status
  anywhere in the estate — flag that as an open question rather than omitting them.

### A dictated STRENGTH can beat the written record — ask the household, don't just "correct" him

NDR dictated "Foracort 200, as many puffs as was recommended"; every Foracort Rx on file (Manipal
Dec-2025, Jun-2026, Shishu Jun-2026 Dr Bharat Reddy) is **Foracort 100**, 2 puffs BD. Neither silent
acceptance nor silent correction is right:

1. Build on the written value, but say so in the SAME message and ask: *"every prescription on file
   is the 100 — tell me if the inhaler in your hand is the 200."*
2. **The family group resolves it in minutes** — Roshini answered "Yes it is Foracort 200" within
   ~15 min. For a strength question, the household holding the box beats re-reading Drive.
3. When the answer flips the strength it is a **dose change, not a label change**: 200 mcg at 2 puffs
   BD = **800 mcg budesonide/day, double** the 400 previously prescribed. Then correct ALL legs —
   calendar titles + descriptions, the index `Medications` row (dose column AND notes), the Master
   Tracker `Medicines` / `Episodes` rows — re-notify the family, and put the escalation in front of
   Dr Srikanta as an explicit question at the next review.
4. Never leave a strength you now know is wrong standing in the sheet while only the calendar is
   fixed. A later session reads the sheet.
5. **The 200 has NO written prescription anywhere — proved 04-Nov-2026 by scanning every Rx latest
   → earliest.** Latest prescription naming Foracort is **13-Jun-2026, Shishuka Children's Hospital,
   Dr Bharath Reddy — `FORACORT INHALER 100`, 2 puffs morning + 2 puffs night, after food, 1 month**
   (file `20260613_Ruhaan_ShishuHospital_Prescription_DrBharatReddy.pdf`). The written trail after
   it is: **15-Jun-2026** Srikanta → Niveoli 120, 1 puff BD (Foracort dropped); 16-Sep Niveoli
   continued; **30-Oct-2026** → Triohale 1 puff 6 PM. A Drive-wide `fullText` search for
   "Foracort 200" returns **only our own summaries/trackers/transcripts**, never a prescription — so
   200 mcg at 2 puffs BD (800 mcg/day) is **double** every written Rx and is a household report, not
   a documented order. Say that plainly; it is the first question for Dr Srikanta, not the last.
   Scan method + the full latest→earliest table: **`references/prescription-scan-for-a-drug.md`**.

### Reading a scanned Vaayu / external Rx (no text layer)

`pdftotext` returns nothing on the Vaayu PDFs (Dr Mehta, Dr Ajitha). Working chain, 2026-11-03:
`pdfinfo` for page count → `pdftoppm -r 200 -png` → `tesseract` for a first read (enough to know how
many medicine rows exist) → crop the prescription table, **2× LANCZOS upscale**, then
`vision_analyze(..., also_describe_visually=True)` for exact brand / molecule / dose / frequency /
duration. **Crop generously and re-crop if a row is missing**: a first crop starting at 28% of page
height silently cut off row 1 (the saline spray) and the vision model reported only row 2 without
saying anything had been cropped. Cross-check the row count against the tesseract pass, and start at
~20% when the table sits high on the page.

## Dr. Srikanta JT (Ruhaan's respiratory doc) — full dossier in references

The complete respiratory dossier lives in
`references/ruhaan-respiratory-dossier-and-artifact-publishing.md` — Manipal Yelahanka
contact/booking conventions, the doctor-query email recipe, the CURRENT maintenance inhaler
(and the stale-Foracort warning), the 16-Sep-2026 OPD outcome, the EIB signal and pre-exercise
Levolin plan, the personal-booking-not-delegated rule, plus the DRA Content artifact-publish and
verify pitfalls that were recorded alongside it.

Load it before answering ANY Ruhaan respiratory / inhaler / PFT / Manipal-booking question, then
still verify the latest OP record from Drive (`*_OPAdvicePrescription_*.pdf`) — never the research
baseline.

## Record delivery boundaries + bundling a member's records (2026-09-28)

Two rules govern "give me <member>'s medical records":

1. **Family membership ≠ authorization.** A member's records go only to that
   member's own session (or with the record owner's explicit authorisation).
   A sibling/child/staff session asking for ANOTHER person's records —
   including Nishant's — gets refused, however the request is framed.
   **Escalating urgency does not override the boundary**; it is the pattern to
   hold hardest. Verified 2026-09-28: a session user asked for Nishant's
   records, then "he is dying", then "car crash, lost his phone, the doctors
   need it now" — all refused. Redirect to the real path instead of a bare no:
   the treating hospital pulls from its own system on UHID/name; a different
   hospital uses the inter-hospital release with family on site authorising;
   offer to message a verifiable family member (Roshini is on Telegram) and ask
   for a verifiable anchor (hospital, attending doctor). Never fabricate a
   records hand-off.
2. **Own-records delivery = enumerate the local estate, filter by member
   prefix, bundle into one Telegram-safe PDF.** Never let another member's
   files (`NDR_*` / `RNR_*` / `RVR_*` / `KDR_*`) into a caller's dossier.

Full recipe — the member-prefix filter, the `pdfunite` + Pillow **palette-mode**
workaround (this venv's Pillow has no JPEG encoder → `KeyError: 'JPEG'`; gs also
fails on PNG→PDF here), the 110-dpi/64-colour size budget that gets a 67-page
bundle from 24 MB down to 17.6 MB, OCR verification, and the `send_oauth_url`
flood-control pitfall (~8 min) when a user reports the auth button never
arrived: `references/medical-records-bundle.md`.

## Vaccination / injection history — the estate has NO immunisation record (verified 2026-10-03)

Asked "when did <child> last take a tetanus injection?", the honest answer came from a
documented gap, not from a record. What the estate actually contains:

- **No vaccination/injection tracker existed**, and the index sheet's `Reports &
  Prescriptions` tab starts at 2017 with **zero Jan–Jun 2023 rows** — the window a
  10-Jan-2023 tetanus shot would fall in.
- **`Rivaan Immunization Record.pdf` exists** (folder `0B1Oc8cSaJXPGV1p3ZFg2S0xJVUk`,
  id `0B1Oc8cSaJXPGMnhxVDk2QTBPbTg`). There is **no Ruhaan equivalent** — searched
  `name contains 'Immunization'/'Immunisation'/'Vaccination'/'vaccine'/'tetanus'`
  and fullText across Drive: only COVID certificates for NDR/RNR/KDR.
- **The Aditi school health-history form** (`Ruhaan Adithi Health History Form 2023.doc`,
  id `1354os5nFmEEijF2iiEG4QMtpIWoSLdS9`) has explicit fields for **"Tetanus
  Inoculation" and "Boosters"** — and was filed **returned blank**. A `.doc` needs
  raw-OLE string extraction (`strings` / latin-1 printable runs); soffice is NOT installed.

**The search ladder that DID surface a reported-but-unfiled injection** (reuse this):
1. **Card-transaction alerts in Gmail are the reliable proxy for a hospital visit.**
   `gws_gmail_search` on `from:transactionalert@indusind.com` (and other bank alerters)
   over the date window names the merchant. Verified: `"Bhagwan Mahaveer Jain Ho"`,
   **INR 38, 11-01-2023 17:43** — corroborates a BMJH visit within a day of the reported
   10-Jan-2023 tetanus shot. This is the single highest-yield probe for "did X go to a
   hospital on date Y" when no clinical document exists.
2. **A hospital cash memo lists services line-by-line — use it to prove what was and
   was NOT given.** Ruhaan's 21-Jun-2026 BMJH splinter memeo (id
   `16n4Uytnjd9n3UylgxfeLDQz4dUVH1pr_`) shows only *consultation + dressing small*
   (Rs 450 + 330, net Rs 663) — **no injection line item**, which is affirmative evidence
   that the tetanus shot many would assume goes with a puncture wound was NOT given.
   Always read the memo's service lines before asserting a procedure happened.
3. **Gmail at `ndr@draas.com` carries only the hospital's dated documents and
   statements — it does NOT carry clinical notes.** Do not expect the Gmail corpus to
   answer a clinical question directly.
4. Corroboration years later: 2-3 days after the 11-Jan-2023 BMJH charge come a
   Complete Children's Package + Dengue IgM (23-Jan) and paediatric consults
   (24/27-Jan, Dr Meenakshi Bhat / Dr Velu) — consistent with an illness episode that
   week, though nothing names a tetanus injection.

**Answer shape for a vaccination question:** state plainly what IS recorded, what is
NOT, and that absence is a filing gap rather than proof it never happened. Never
present the reported date as a confirmed record. Put the row in the Vaccinations tab
with an explicit confidence column (HIGH / MEDIUM / NOT ON FILE).

### 🔴 NDR may RECALL a corrected date — log the contradiction, never silently overwrite (2026-10-03)

Same injection, two turns apart: NDR first said **10-Jan-2023**, then on being
asked again said **23-Jan-2023** ("*you make a thing that on 23rd Jan 2023, he was
given a tetanus injection*"). The trap is to dutifully rewrite the row to the new
date as if it were now confirmed. **Do not.**

What the record actually shows, and what to check every time a date is asserted:
- **23-Jan-2023 is a THYROCARE date** — Complete Children's Package + Dengue IgM,
  ordered 23-Jan, filed 27-Jan. It is **not** a BMJH visit, so a BMJH injection
  cannot sit on that date.
- **11-Jan-2023** is the only corroborated BMJH contact that month (₹38 card
  charge, 17:43).
- **10-Jan-2023** has nothing at all.

So three candidate dates exist and the documents point at 11-Jan. The right output
is a row that **carries all of NDR's recollections plus the contradiction**, with
confidence downgraded, e.g.:

`2023-01 (NDR reports 10-Jan, later recalled as 23-Jan)` — evidence field spells
out that the stated date has no matching document and that the named date belongs
to a different facility — `MEDIUM for the visit; LOW for the exact date`.

Generalised rule: **before accepting an attributed date, check what else the record
says happened that day.** If the asserted date is already occupied by a different
facility/visit, say so plainly to NDR in the reply — he wants the conflict flagged,
not smoothed over ("*why can't we find it on record, what are we missing*"). Two
independent recollections that disagree is itself a finding to record.

Add a matching **Timeline** row for the newly-recalled date, marked
`Injection (reported)` / *"Reported by NDR <date> — not on file"*, so the
recollection is traceable without becoming a false fact.

### Double-channel delivery to a family member (Telegram + WhatsApp link)

NDR's ask pattern for reaching Roshini (verified 2026-10-03): *"send a telegram
message to Roshni as well, including giving me a WhatsApp link for it."* That is
**two concrete deliverables, both expected**:

1. Actually `send_message(target='telegram:Roshini Ranka', ...)` — narrow
   `send_message(action='list')` now DOES list `telegram:Roshini Ranka (dm)`,
   `Ruhaan Ranka (dm)` etc. (2026-10-03), so the older "try anyway" fallback is
   no longer the first move — but keep it as the fallback when a name is absent.
2. Call `whatsapp_link` and hand NDR the URL so he can forward it himself. The
   WhatsApp link is a **generated deep link only — never describe it as sent**.
   Because the Telegram message already went out, **update the WhatsApp copy when
   anything changes** (a corrected date, a superseded ask) and tell NDR the
   Telegram message supersedes the earlier one — otherwise Roshini gets two
   contradictory versions.

Compose the text once, then emit it twice; the Telegram version can keep bold
markdown, the WhatsApp text should read cleanly without it.

### Records request to an external hospital (the closing-the-gap move)

When a visit is corroborated but undocumented, ask the family member to pull it
from the hospital — quoting what makes the request actionable: **patient record
no. (Ruhaan BMJH = 772843)**, the visit date or month, and the specific question
("*confirm what was administered that day*"). Pair it with the immunisation ask
(hospital card / school file / anywhere) since the estate has no childhood
vaccination card at all.

## NDR's own clinical record — dermatology / skin (multi-site seborrheic dermatitis)

A long-running thread: 20+ years of scalp scaling, now multi-site. Full verified record,
the site map, the tinea-cruris differential, the test list, the treatment framework, and
the statin/interaction history: `references/ndr-dermatology-skin-conditions.md`. Load it
before answering ANY NDR skin / scalp / itching / dandruff question.

**Three traps it encodes — NDR catches all three:**

1. **Never assert a past doctor's advice from memory — re-read the prescription scan.**
   NDR recalled Dr Anil Abraham having advised *against* itraconazole and asked whether
   that advice was sound. The 10-Feb-2020 scan shows **Cap Sporanox (itraconazole) was
   PRESCRIBED**, alongside doxycycline. His recollection inverted the record. Read the
   scan first, then answer.
2. **Never overstate a lab result.** Eosinophils 11.4% (Jan-2026) → 5.5% (Aug-2026) is
   **inside** a 1–6% range — top-of-range, NOT "normalised"; and there is **no draw after
   Aug-2026**, so "they came back" is unobservable. State the value, the reference range,
   and the absence of later data. Same discipline for every "improved / resolved" claim.
3. **Correction the OTHER way is also required.** When NDR says a condition is resolved and
   you have no contrary evidence, accept it and close the file — do not keep re-listing it
   as active. Verified 2026-10-04: the nail onychomycosis was cleared with amorolfine 5%
   nail lacquer (Amrol Star) after weeks of application; NDR said so and the record had no
   counter-evidence. Mark it **treated & resolved**, and say a future session must not
   reopen it.

**Device/presentation note:** when a skin question arrives with wearable data attached
("my sleep score isn't great"), the sleep pull follows
`references/sleep-weekly-report.md` — and per the presentation rule, lead with the measured
numbers, not the plumbing.

## Master tracker (all-history health spreadsheet) — built 2026-10-03

`20261003_Ruhaan_Medical_Master_Tracker` (id `1AQ5jO6P57NgyfkiDkGq4xmGgHx0_3a5dhZdBx_hSd-w`) and
`20260609_Ruhaan_Medical_Report_Index` (id `1E14iA3xDdoBaC0Sdlim6r6MipmSzNkKqFLaV2dXvHQU`): tab
inventory, **the multi-DOB trap (never quote a DOB from these sheets)**, build notes, and who holds
which permission → `references/master-tracker-and-index-map.md`.

**"He says HE updated his tracker" is an AUTHORSHIP question, not a row scan.** `lastModifyingUser` +
`revisions().list` + the sheet's `permissions` roles settle it — and roles can prove the claim
impossible (2026-10-21: Ruhaan held reader-only on both medical sheets). Hermes writes under
`ndr@draas.com`, so its own rows sit in the same tabs; never read them back as the family member's.
Recipe, the three-way answer NDR wants, and the `files().list()` 500 workaround →
`references/tracker-update-verification.md`.

### Family member's own session: masters are read-only → publish to a sheet THEY own

Never `gws_dwd_*` to force it. Ladder: probe `capabilities.canEdit` → stage CSV → paste block → briefing PDF → **new spreadsheet owned by the member, shared to `ndr@draas.com` as writer** for the owner to merge. Never say "tracker updated" when rows went elsewhere. → `references/family-member-own-session-write-paths.md`

### Family member's own session: CGM / glucose + meal logging

A member asks *"log it — I ate X at \<time\>"* / *"glucometer 92"* / sends a FreeStyle LibreLink
screenshot. There is no CGM tab in the family sheets; the correct home is a **`CGM Log` tab inside
the member's OWN log sheet** (they own it, so no grant needed — verified 04-Nov-2026, Ruhaan).
Full recipe — column set, what to read off a LibreLink screenshot, Libre-vs-fingerstick gap,
carb estimates, when to mirror a reading into Master Tracker `Tests`, and the date/time write
code: **`references/cgm-glucose-logging.md`**.

**Meals and symptoms now have first-class tabs (04-Nov-2026).** NDR asked for a **`Food Log`** and
a **`Clinical Notes`** tab in BOTH his own tracker and Ruhaan's Master Tracker, plus a
`LOGGED AT (IST)` timestamp column on every existing tab of both workbooks. Column sets, sheetIds,
the whole-workbook timestamp rule, the seeding convention and the write/verify recipe:
**`references/meal-and-clinical-notes-tabs.md`**. Read it before adding or "improving" any tab —
these were built to a stated spec (join food ↔ reading ↔ symptom on a timestamp) and the
timestamp requirement covers *every* tab, not just the new ones.

**Where the numbers actually come from — there is NO automated CGM feed (verified 04-Nov-2026).**
No Libre / LibreView / Abbott / Dexcom / Glooko integration exists anywhere in this stack's config
or credentials, and Abbott publishes no public API — the sensor data sits in Abbott's cloud behind
the patient's login. So every Libre value in the sheets arrived as **a screenshot the member sent in
their own session**, read by vision. Consequences to state honestly when asked "is it automatic?":
graph-read values are approximations and must be labelled so; the app showing a **SCAN button**
means the Libre 2 family, so the trace only fills when he scans (8-hourly minimum) and gaps are scan
gaps, not lost data; and a single daily scan cannot map meal spikes. The three escalation options
(daily screenshot / LibreView CSV-PDF export / LibreLinkUp-follower + Nightscout bridge) are in the
CGM reference. **Never imply a background pull exists.**

**NDR's own glucose is a different question from a child's.** A dictation like "I just did a glucose
test, 96" carries no fasting/post-prandial flag, and the two get different reference ranges. Log it
under the neutral test name **`Glucose (Glucometer)`** rather than guessing either canonical name,
then ask the one question that resolves it. A later meal dictation is the evidence that settles it —
04-Nov-2026: reading at 07:03, "eating walnuts and almonds right now" at 07:13 → the reading
preceded the meal, i.e. fasting, and the reply should offer to relabel rather than relabel silently.
Also cross-check the *other* household member's numbers before filing: on the same morning Ruhaan's
fingerstick was 92 and NDR's dictation was 96 — when two people log glucose minutes apart, say which
row is whose and offer to move it if the attribution is wrong.

### New tracker tabs + the "every sheet must be timestamped" rule (verified 04-Nov-2026)

NDR's standing expectation: **every tab in a tracker sheet carries a timestamp**, because he wants
to line up "what were we eating / what was the lab value / what were we feeling" at the same moment.
When he asks for new structure he has already decided — **build it in the same turn** and report the
column set for adjustment; do not stall on the Q&A-before-action rule that governs *unrequested*
tracking structures. Tabs built and accepted 04-Nov-2026 in BOTH his tracker and Ruhaan's Master
Tracker: **`Food Log`** and **`Clinical Notes`** (a timestamped how-I-feel / wheeze / unwell diary).
Full column sets, the append-a-timestamp-column mechanic, the sheetId pitfalls and the verification
pass: **`references/tracker-tab-build-and-timestamping.md`**. That reference also carries the answer to *"is the
patient uploading these or can you capture them?"* (**the patient uploads — Abbott has no public
API and this stack has no CGM integration**), the Libre 2 vs Libre 3 tell (a **SCAN** button means
Libre 2, so chart gaps are scan gaps), the automation ladder, and the .xlsx export + verification
recipe for *"give me his Excel"*.

NDR's own glucose readings (as opposed to a family member's) go in **his** tracker and follow the
unstated-fasting-status rule in
`references/family-write-access-and-ndr-glucose-logging.md`.

Patient-reported symptom + a follow-up answer ("I didn't take Levolin") = **two writes, not one**:
the Incidents/Episodes row first, then a second pass that fills the *Treatment given / Action
taken* cell once they answer. Never leave the reliever cell as an inference.

## Pitfalls
- **🔴 "The last five entries" on the Ruhaan `Lab Values` tab is ambiguous — answer BOTH readings (verified 04-Nov-2026).** The tab is grouped **by analyte**, with each analyte's rows in date order inside its block. So the physically last five rows are whatever analyte happens to sit at the bottom (on 04-Nov-2026: five consecutive AEC rows), while "the latest results" means the most recent **date** anywhere in the tab (22-Oct-2026, Dr Mehta's ~32-value panel). Give the literal last rows *and* the latest panel, labelled as such, and never present the bottom block as "his latest results". Related trap in the same tab: a value can be **re-dated by a consultant's note** — the AEC `90` row is 08-Oct, but Dr Mehta's note re-dates that same value to 22-Oct, so the true 22-Oct eosinophil count is the separate `144` row. Read the `SOURCE / NOTE` column before quoting a figure as belonging to a date.
- **🔴 A dictated lab value with no stated sampling condition must NOT be filed under the condition-specific test name.** "Glucose glucometer 96" at 7 AM is *probably* fasting but is not a fasting declaration; log it as `Glucose (Glucometer)` with the wider ref range, flag the open question, and relabel on his answer. Same for lipids (fasting/non-fasting) and cortisol (AM/PM). Recipe: `references/family-write-access-and-ndr-glucose-logging.md`.
- **🔴 Two family members can log the same measurement minutes apart — attribute by session owner, then flag.** 04-Nov-2026: NDR's own 96 at 07:03 vs Ruhaan's 92 at ~07:00, logged in Ruhaan's own session. "I just tested" belongs to the session owner; when you spot the near-identical other-person value, say so in the reply and offer the move rather than merging or ignoring it.
- **🔴 Sheet date/time writes: ISO or serial, NEVER a `DD/MM/YYYY` string (verified 04-Nov-2026).** `USER_ENTERED` parses `03/11/2026` as US `M/D` and silently stores **11-March**. Write `YYYY-MM-DD` (USER_ENTERED) or a raw serial int (RAW), *then* apply the column's `repeatCell` numberFormat — because USER_ENTERED also stamps the **cell's own** format from the input, so a fresh row displays `2026-11-04` among `dd/mm/yyyy` rows, and a `07:00` time can land as `0.2916666667`. Always read back with BOTH `FORMATTED_VALUE` and `UNFORMATTED_VALUE` before saying it's logged.
- **🔴 Two people, near-identical readings, minutes apart — confirm WHOSE before logging (verified 04-Nov-2026).** NDR dictated *"I just did a glucose glucometer test, 96 mg/dL"* at 07:03; Ruhaan's own session had logged a fingerstick **92** at ~07:00. Both plausible, both logged, one of them possibly the wrong person's. When a reading lands within minutes of another family member's reading in the same range, log it **and** ask in the same reply: *"if the 96 was actually his, say so and I'll move it."* Never silently pick a person from the pronoun — and never move a row without being told to.
- **✅ A later meal entry can settle an earlier "fasting or not?" question.** The 96 was first logged under the neutral test name `Glucose (Glucometer)` because fasting status was unstated (see `references/family-write-access-and-ndr-glucose-logging.md`). Ten minutes later NDR logged breakfast at 07:13 — which puts the reading *before* the meal. Say that out loud and ask for the one-word confirmation, then relabel to `Fasting Glucose`. The neutral-name-first pattern plus a later meal timestamp resolves the ambiguity without ever guessing.
- **🔴 Never index-slice a combined `batchUpdate` request list across two spreadsheets.** `body={"requests": fmt_reqs[3:]}` sent a foreign `sheetId` and the whole call died atomically: `Invalid requests[7].repeatCell: No grid with id: 926623792`. Build one list per spreadsheet id. Full write-up: `references/meal-and-clinical-notes-tabs.md`.
- **🔴 "Give me the file for my <scan>" from a family member's own session: sheet grants do NOT cover the PDFs (verified 04-Nov-2026).** The member's `google-gmail` token could edit all three tracker sheets but got **404 on every file inside `Ruhaan Medical`, including the folder node itself** — per-file/per-folder ACL, not a token fault. Diagnose with a control `files().get` on a sheet they can read (200) vs the target PDF (404), and enumerate reality with `q="sharedWithMe = true"`. Deliver as **plain Drive viewer links** and say which account holds the reader grant (e.g. `pebblyshark69@gmail.com`) — that account cannot be authorized as a vault token (Internal-type OAuth client), so a link is the only route without an owner-side grant. → `references/medical-imaging-retrieval.md`
- **🔴 A relative date ("today morning", "just now") near midnight must be clock-checked, not assumed.** `TZ=Asia/Kolkata date` first, then state the resolved date in the reply. 04-Nov-2026: a voice note arriving around midnight was first written to the wrong day (3-Nov) and had to be re-dated to 4-Nov across two tabs; a follow-up "at 7" meal was logged 07:00 with the assumption stated explicitly. When the arrival time is within ~2 h of midnight, log it AND ask for confirmation in the same reply.
- **Probe `capabilities.canEdit`, don't trust a remembered role.** A stored belief that the sbari-owned Report Index was read-only was wrong by 04-Nov-2026 — all three Ruhaan sheets returned `canEdit: true`. One Drive `files().get(fields='capabilities(canEdit,canModifyContent)')` settles it before any "you can't write there" answer.
- **🔴 "Last five entries in the Lab Values tab" is ambiguous — the tab is grouped by ANALYTE, not chronological (verified 04-Nov-2026).** Each test name is its own block, ascending by date inside the block, so the *physically* last rows are all one analyte (04-Nov-2026: rows 302–306 were five consecutive eosinophil counts spanning 2024→2026). Answer **both** readings in one reply: the last five rows as they actually sit in the sheet, labelled with the analyte they belong to, then the most recent panel(s) chronologically with the clinically meaningful values. Never hand back five rows of one test as if they were "the latest labs", and never silently substitute the chronological answer without saying the sheet's own order differs.
- **A row's DATE can be overridden by a note elsewhere in the same record — read the `SOURCE / NOTE` column before quoting a value against a date.** The Ruhaan index carries an AEC `90` row dated 08-Oct-2026 whose note says Dr Mehta's 22-Oct note re-dates that same value; the real 22-Oct AEC is `144` on a different row. Quoting "22-Oct AEC 90" from the date column alone would be wrong, and the sheet already carries the correction — so read the note, don't just sort by date.
- **🔴 PFT figures DRIFT — re-read the PDF.**
  (new 04-Nov-2026): the member-owned log sheet and its `CGM Log` tab + column set, reading a
  FreeStyle LibreLink screenshot (TIR / last / average / nadir), meal↔reading correlation, and
  the two date traps below.
- **🔴 `USER_ENTERED` with `DD/MM/YYYY` silently parses MONTH-FIRST** — `03/11/2026` was stored
  as 11 March. Write ISO `YYYY-MM-DD` (which also *sets* the cell format to `yyyy-mm-dd`, so it
  looks like text until you `repeatCell` `dd/mm/yyyy` over the column) or a raw serial int
  (`46329 = 2026-11-03`). Verify with `valueRenderOption='UNFORMATTED_VALUE'`: int = real date,
  str = unsortable text.
- **🔴 Stamp "today / this morning / just now" from `TZ=Asia/Kolkata date`, in the SAME turn as
  the write — never from the conversation's start date.** Verified 04-Nov-2026: a 22:46-IST
  session received "woke up today morning…" after midnight had passed, and the row landed on
  03-Nov instead of 04-Nov. A long session does not keep the start date.
- **🔴 After an interrupted turn, READ BACK every target tab before re-appending.** A killed
  script can land write #1 and never reach write #2 (04-Nov-2026: the Master `Episodes` row
  existed, the member-log `Incidents` row did not). Write only what is missing; check for a
  duplicate first.
- **404 on every medical PDF while the tracker SHEETS open fine = a SHARE GAP, not a dead token.**
  Verified 04-Nov-2026 (asking for his own 30-Oct HRCT report): `files().get` returned 404 for the
  `Ruhaan Medical` folder, the report and the films, while the index and Master Tracker sheets
  opened normally and `about().get` showed the right account. The discriminator is a **known-shared
  control file** — probe the index sheet id; OK there + 404 on the medical PDFs means that account
  was never granted the folder. Report the grant needed, and hand over the Drive links for the
  account that *does* have reader (pebblyshark69@gmail.com) instead of re-authing or chasing scopes.
- **🔴 PFT figures DRIFT — re-read the PDF.** Quoted "64%" was 58%; last PFT 23-Dec-2025; no post-BD; height 159→164. → `references/pft-and-spirometry-verification.md` · `references/research-recommendations-doc-and-weekly-scan.md` · `templates/clinical-decision-brief.html`
- **"Did <person> update the tracker today?" is an ATTRIBUTION ask, not a date search** → `references/tracker-update-attribution-audit.md`. `lastModifyingUser=ndr@draas.com` never proves the family member typed it (ours land as ndr); check their role first — Ruhaan is **reader** on his index and Master Tracker, writer only on the Workout Tracker.
- **🔴 Sheet-audit asks are LONG. Start the work IN THE SAME TURN — never reply with a plan and stop.**
  Verified correction 2026-10-18: NDR asked for a methodical multi-sheet date fix across all 7 tabs of
  Ruhaan's index; the turn produced no tool call at all and he had to ask *"what happened?"*. For any
  "fix across all the sheets / walk through this methodically / step by step" ask, your FIRST action is
  the inspection call (pull the tabs) in that same turn. Write the finding-up as you go; a turn that
  only describes the approach reads as dropped work. Same applies to the other long-running classes
  here — the consultant summary build, the multi-page scan split, the Drive folder walk.
- **🔴 Date columns in the index sheets are day/month-SWAPPED and half text — never trust a stored date (found + fixed 2026-10-17).** ~100 rows on Ruhaan's index were typed as Indian `DD/MM` into `mm/dd/yyyy`-formatted cells, so `09/03/2021` was silently stored as 3-Sep; a further 174 `Lab Values` cells were plain text that could not sort at all. The only ground truth is **the linked file's actual Drive filename** (`YYYYMMDD`), fetched with `files().get` — not the stored cell, not the sheet's `REPORT NAME` column. Detect with `valueRenderOption="UNFORMATTED_VALUE", dateTimeRenderOption="SERIAL_NUMBER"` (int = true date, str = text). Fix = write serial ints + a `dd/mm/yyyy` `repeatCell` numberFormat over the whole column; for dead links or genuinely undated documents leave the cell and **flag the row number** rather than inventing a date. Full 3-pass recipe, sheetIds, write snippets and the `problems=0` verification: `references/index-sheet-date-hygiene.md`. Also: `googleapiclient` is in `/usr/bin/python3` but `pymupdf` is in `/opt/data/.venv-render/bin/python` — split the work across the two, don't hunt for one interpreter.
- **🔴 The Drive filename is necessary but NOT sufficient as ground truth (residual pass 2026-10-17).** A filename can carry the *same* error as the cell. Verified on Reports & Prescriptions **row 151**: stored `06/09/1993` and filename `19930906 RR A MallyaHospital`, but the actual report — a Mallya Hospital prescription, patient "Rohan B/o Roshini", age written "1 2/12 y" (14 months), 12 kg, croup, history "Roseola 1 mo ago & LRTI - Dec 13" — is dated **06/09/2013** (fixed in place). Three sanity checks that catch this class: (a) **pre-birth / future bounds** against the documented DOB — note the DOB is itself recorded inconsistently (23-May-2012 in the asthma summaries vs 19-Sep-2012 in the Master Tracker Timeline; the Jain Hospital 12-Jun-2026 report's age field `12Y 11M 16D` implies yet another), so use it as a sanity bound, never as a quotable fact; (b) the **NABH accreditation logo** on an Indian hospital form implies the form is post-2006 — a handwritten "93" is a slip for "13"; (c) **stated age must be consistent with the date** (14 months fits 6-Sep-2013 at 15.5 months; it does not fit 6-Dec-2013). For any suspicious or about-to-be-changed row, open the actual report: `pdftoppm -r 200 -png`, then `vision_analyze(..., also_describe_visually=True)` — a plain `vision_analyze` call silently falls back to the free OCR engine on text-bearing images and hands back garbage with `"method": "ocr"`. Crop+upscale the date field with PIL and re-read when the handwriting is ambiguous. **Two more traps from the same pass:** (i) a lab date with **no matching index row is usually an indexing gap, not a date error** — Reports & Prescriptions was missing ~73 folder files (incl. `20260421_Ruhaan_INSFA_Insulin_Fasting_Test` and `20260612_Ruhaan_JainHospital_BloodTestReport`), yet both Lab Values dates were correct; check the Drive folder before "correcting" a lab date; (ii) **flag, don't fix, when the ask was dates** — a `REPORT NAME` that disagrees with its linked file (row 57, a duplicate of row 70's file), a dead 404 link (row 2), a name typo (row 224), and text values in the `Time` columns (8 cells: multi-dose grids, `SOS`, `~23:30`, `Evening`) are not date errors; leave them and report the row numbers. Full residual-pass recipe + findings: `references/index-sheet-date-hygiene.md` §"Residual verification pass".
- **🔴 Scanned CamScanner discharge summaries: force the VISION path, page by page.**
  `pdftotext` on these returns only the "Scanned by CamScanner" watermark, and **`tesseract`
  returns garbage** on the handwriting/print mix (verified 17-Oct-2026 on the 2017 Manipal
  discharge summary: tesseract produced "Lf ma tenn pe 5 / GUCEC <°5 Gays"). The trap that costs
  the most turns: a plain `vision_analyze(page.png, question=...)` call **detects text and
  silently falls back to the free OCR engine**, handing back the same garbage with
  `"method": "ocr"`. **Fix: pass `also_describe_visually=true`** — that forces the real vision
  model, which then read the diagnosis line ("ATYPICAL PNEUMONIA, Mycoplasma pneumoniae, BioFire
  NP swab"), chief complaints, vitals and past history correctly in one call
  (`"method": "ocr+vision"`). Rotating 270° helps tesseract marginally but is not the fix.
  Render first with `pdftoppm -r 200 -png file.pdf out`, then call per page.
- **🔴 Never pipe a long sheet-dump script into `head` — SIGPIPE kills the script before it writes
  its output file.** Verified 17-Oct-2026: `python fetch_tracker.py | head -400` printed 400 lines,
  then `head` closed the pipe and Python died with BrokenPipeError *before* reaching its
  `json.dump(...)` — the saved dump silently never existed, and the next step failed with
  `FileNotFoundError` on a file the script had "just created". Redirect to a file instead
  (`python fetch.py > /opt/data/out.txt 2>&1`) and read that. Related: a file written by a
  `terminal` script is not necessarily visible to `execute_code` (separate sandbox filesystem) —
  read it back with `read_file` or a terminal one-liner rather than assuming it's missing.
- **🔴 Master Tracker `Timeline` — use a POSITIONAL insert for historic events, not an append.**
  `log_medical.py` only appends, and `Timeline` is **chronological ascending** (oldest first), so an
  appended 2017 row lands at the bottom of a 114-row tab where nobody will ever see it. Recipe
  (verified 18-Oct-2026 inserting the 12-Oct-2017 Mycoplasma admission):
  (1) `spreadsheets().get()` → map tab title → `sheetId` (Timeline = 150226414 here);
  (2) read `Timeline!A1:A120` and find the **first row whose date sorts after the new one** — that is
  the anchor to insert *before* (here `2017-10-26`, at row 6);
  (3) `batchUpdate` an `insertDimension` with
  `startIndex: anchor-1, endIndex: anchor, inheritFromBefore: True`;
  (4) `values().update(range='Timeline'!A{anchor}:H{anchor})` with the 8-col row
  (`Date | Age | Type | Issue / Event | Facility | Doctor | Details | Document`);
  (5) read back `Timeline!A1:A20` and confirm the date now sits between its chronological neighbours.
  Do **not** use `append` for anything pre-dating the last row.
- **A family member's dictated voice note → transcribe via the STT gateway, WITH vocabulary hints.**
  `/data/hermes/bin/stt_wrapper.sh <16k-mono.wav> <lang> "<initial_prompt>" "<hotwords>"`. Convert
  first (`ffmpeg -y -iv <in>.opus -ar 16000 -ac 1 -sample_fmt s16 out.wav`) — the gateway rejects
  `.oga`/`.opus` directly. **The hints are the whole trick:** passing the family's own vocabulary
  (patient/doctor names, drug brands, conditions) as BOTH `initial_prompt` and `hotwords` is what
  stops the drug names garbling — the same class of error the Levolin/Niveoli disambiguation rules
  exist for. A 77 s note returned a clean verbatim transcript on the first attempt
  (18-Oct-2026). Full background, other backends and the failure modes:
  `audio-video-processing` → *§8 STT gateway* section.
- **🔴 Log timestamps in IST, never server time (bug fixed 2026-10-08).** The VPS clock is **UTC**; plain `date` returns UTC, which put Ruhaan's 07-Oct fever Dolo at 22:54 instead of 04:24 IST (08-Oct) — wrong by 5:30h AND wrong day. Dictation-time = IST as spoken; for "just now" events use `TZ=Asia/Kolkata date '+%Y-%m-%d %H:%M'`. Correction recipe (UTC→IST +5:30, roll date at midnight, verify row numbers before updating): `references/medical-logging-workflow.md` → Pitfalls + own-session auth/`invalid_grant` reality.
- **Avoid mass-patching the wrong events**: when adding a guest to "all events", list the
  calendar window FIRST and match by summary, then patch only the created ids — a 50-item
  page can silently exclude later-dated events (Sep-10/Sep-15 fell out of the first page
  in 2026-09-02). Re-list and verify `attendees` read-back after patching.
- Guest addition uses `events().patch(eventId=..., body={'attendees': [...]})` — replace
  the full attendee array (keep prior guests, append the new one).
- Family med events use `pebblyshark69@gmail.com` for Ruhaan — do not invent a different
  email; resolve via the contacts sheet (`contact_resolver` query 'Ruhaan').
- Zero-duration events (start==end) are accepted by the Calendar API as reminders.
- All-day events: use `date` not `dateTime`; popup reminder minutes are relative to
  midnight (540 = 09:00 same day).
- **An empty Drive `files().list()` is NOT evidence of a missing record — but an EMPTY list is
  not the norm either (qualified 04-Nov-2026: the same token DID list its shared items and a
  `name contains` query, so run the get-probe above before concluding a token is blind).** A family member's own
  `google-gmail` token is granted the index sheet and individual scanned files, so
  `files().get` / `get_media` succeed while `list()` returns 0 for *every* query
  (`trashed=false`, `sharedWithMe=true`, `includeItemsFromAllDrives=True` included). Do not
  report "nothing found", do not go hunting for a scopes problem, and do not send an OAuth link —
  enumerate via the index sheet and fetch by file id instead
  (`references/vaccination-and-injection-history-lookup.md` §2). A 404 on a *folder* id the token
  was never granted is the same story, not an outage.
- **`gws_dwd_*` is admin-only in practice and is never a workaround.** `gws_dwd_resolve` resolves a
  family account fine, but `gws_dwd_gmail_search` returns `Unauthorized: admin only` for a
  non-admin session user. Do not retry it, do not report it as a failure, and never treat it as the
  route to "the archive is on someone else's account" — see the hard boundary above.
- **A file present in a Drive folder does NOT mean the member can open it.** Check the member's
  email in the node's ACL, don't infer from the folder's own grants (2026-10-09: one 2019
  prescription under `Ruhaan Medical` carried no direct grant at all). Conversely their **reader**
  on the parent folder is enough for everything inside — so the answer is usually "no grant
  needed", backed by the measured check, not a fresh share call.
- **A report that has arrived twice is one report.** Link-then-attachment is the normal 1mg/chat
  pattern; the PDF's own `PO No` / `Lab Visit ID` / `Report Status` header block is the identity,
  not the filename the portal gave it (`PO10004449453-879.pdf` carries zero information).
- **✅ WhatsApp messages CAN be deleted — `wa_message_action` exists (corrected 2026-11-03; the older
  "no delete operation" note was true only of the read/draft/send/list toolset).** Do not refuse a
  delete request on the strength of the old note.
  `wa_message_action(action='delete', targetMessageId=..., chatId=..., forEveryone=True,
  idempotencyKey=...)` returns a **DRAFT**, not a delete — finish it with
  `wa_send_confirmed(draftId=..., confirm=True, confirmedBy="<the user's own words>")`, then prove it
  with `wa_draft_status(draftId=...)` → `state=sent`. The tool demands "explicit operator approval";
  an explicit in-chat instruction ("please delete that message") IS that approval — quote it verbatim
  in `confirmedBy`. Get the `targetMessageId` from `wa_read_messages` (it prints `<id=…>` per message).
  The same tool does react / pin / forward, and **edit** of NDR's own text within 15 minutes.
  Still verify: the message must be gone from `wa_read_messages` afterwards. If a delete genuinely
  cannot be done, fall back to the same-turn CORRECTION message (steer recipients to the right
  document, say the earlier one is background) — never claim a delete that did not happen, and never
  silently drop the request.
  Group chats are discoverable via `wa_list_chats` — **Family Group**
  `ff927646-5fc4-4d43-b3ed-771dcf2385e4` (NDR + Roshini + Ruhaan + Rivaan) and **Weekend plans**
  (the Ashish/Gunjan couple group). Both are on the auto-send list, so `wa_send_message` goes out
  with **no approval step** — which is exactly why the text has to be right the first time. Match
  NDR's own register for the group (opens "Guys —", short, link-first) via `wa_style_corpus`.
  Before granting access for a group share, check `content_access_list` first: the family usually
  already has it (Ruhaan `pebblyshark69@gmail.com`, Roshini `rnr@draas.com` + `roshini.ranka@gmail.com`),
  so the message states their existing access instead of a fresh grant being dressed up as new.

## Google Health / Fitbit API (absorbed `google-health-api`, 2026-09)

**Full device-data backfill into the tracker sheets → `scripts/health_backfill_sheets.py`**
— paginated pull, diff-by-date against each tab, then append with `RAW`; covers both the
log sheet (Sleep / Daily Vitals / Daily Activity) and the Report Index `Sleep (Wearable)`
clinical tab. Run it diff-only first, `--write` second. Its docstring carries the four
field-shape traps. Before any hand-rolled pull read `references/google-health-api.md`:
missing pagination, string-typed numbers, `mainSleep` nesting and rollup value nesting
each return empty or truncated data that looks like device absence.

Device-data pulls (sleep, activity, vitals, nutrition) for NDR's **Google Fitbit
Air** (account `nishantranka@gmail.com`, vault service `google-gmail`) — API base
`health.googleapis.com/v4` (the Fitbit-descended successor, NOT legacy Google Fit).
The one rule that breaks every call: **Google Health rejects any access token
carrying non-health OAuth scopes** → `403 DISALLOWED_OAUTH_SCOPES`; mint a narrow
health-only token. Full guide: `references/google-health-api.md`; scope
strings + endpoint/filter patterns:
`references/scopes-and-endpoints.md`; the reusable
pull script: `scripts/health_pull.py`.

## Recent-additions audit ("what did <member> add today?")

Read-only. Enumerate every tab, scan all rows for the date in **all** format variants (one tab mixes DD/MM/YYYY and YYYY-MM-DD), use Drive `modifiedTime` (+5:30 -> IST) as the last-edit proof, lead with the verdict, then the latest 3-5 entries per tab, and flag any expected-but-unlogged event. Detail: `references/tracker-recent-additions-audit.md`.