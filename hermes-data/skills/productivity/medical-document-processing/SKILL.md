---
name: medical-document-processing
description: |-
  Process medical documents (discharge summaries, lab reports, prescriptions) for family members:
  extract text, identify key medical fields, rename & file on Google Drive with consistent naming,
  research medications/procedures, create follow-up calendar events with family attendees,
  and generate WhatsApp summaries. Full pipeline from raw scan to actionable output.

  Trigger: user uploads a medical document (discharge summary, prescription, lab report, scan)
  and asks to "file it", "file in [name]'s medical folder", "process this", or asks for
  medication info + calendar + WhatsApp in one request.
metadata:
  hermes:
    tags: [medical, documents, discharge-summary, healthcare, drive, calendar, whatsapp, family]
    related_skills: [ocr-and-documents, google-workspace, messaging-links, personal-document-organization]
category: productivity
version: 1.0.0
author: ndr@draas.com
---

# Medical Document Processing Pipeline

## 1. Trigger Conditions

Activate when the user:
- Uploads a medical PDF/scan and says "file it", "file in [name]'s medical folder", "process this"
- Uploads a discharge summary and asks for medication info + follow-up calendar + WhatsApp
- Says any combination of: "rename", "file in medical folder", "what medications", "follow-up date", "calendar event", "WhatsApp summary"

**Common document types:**
- Discharge summary (in-patient procedure/surgery)
- OPD notes / clinic visit summary
- Lab reports (blood work, pathology, radiology)
- Prescription slips
- Pre-operative assessment / clearance

## 2. Stage 1 — Extract Text from the Medical Document

### 2.1 Try pdftotext first (fastest, works for text-based PDFs)

```bash
pdftotext "/path/to/scan.pdf" /tmp/medical_text.txt 2>&1 && cat /tmp/medical_text.txt
```

If the PDF already has embedded text (e.g. hospital's digital discharge summary), pdftotext returns clean text immediately.

### 2.2 Fallback to pymupdf (if pdftotext returns garbled or incomplete text)

```bash
/opt/hermes/.venv/bin/python3 -c "
import pymupdf
doc = pymupdf.open('/path/to/scan.pdf')
for page in doc:
    print(page.get_text())
"
```

### 2.3 Fallback to OCR (tesseract/ocrmypdf for scanned documents)

```bash
ocrmypdf --sidecar /tmp/medical_text.txt "/path/to/scan.pdf" /tmp/ocr_output.pdf --force-ocr 2>&1
```

### 2.4 Fallback to Vision Analysis (when OCR tools fail)

If all text extraction methods produce unusable output, convert PDF pages to JPEGs and use `vision_analyze`:

```bash
# JPEG at 150 DPI, NOT png at 200+ — high-DPI PNGs come out 6000x10000+ px
# and the vision provider rejects them with a generic 400 "Provided image is not valid"
pdftoppm -jpeg -r 150 "/path/to/scan.pdf" /tmp/page
```

**ALWAYS downscale before vision_analyze** — providers reject oversized images with an opaque 400
("Provided image is not valid" / "Unable to process input image"). Thumbnail to ≤1600px on the
longest side with PIL first:

```python
from PIL import Image
im = Image.open('/tmp/page-1.jpg')
im.thumbnail((1600, 1600))
im.save('/tmp/page_small.jpg', 'JPEG', quality=90)
```

Then pass the resized image to `vision_analyze` with a specific extraction question.

**Handwritten prescriptions (OPD slips, Rx pads):** full-page OCR comes back garbled for cursive
handwriting. The working pattern is:
1. Render at 150 DPI JPEG, then crop **horizontal bands** (e.g. 25–55%, 45–75%, 65–95% of height)
   and zoom each band independently (`c.thumbnail((1800,1800))` then save as JPEG).
2. Ask the same extraction question per band, explicitly requesting character-by-character reads of
   drug names/dosages/frequency (`0-0-1` = morning/noon/night; `✓-✓-✓` = thrice daily).
3. Cross-check two band passes; ambiguous brand names (e.g. a cough syrup read as "RESWAS" vs
   "RESUNAS") should be flagged as unconfirmed rather than guessed.

**pdftoppm pitfalls:** at `-r 250`+ the render can exceed 180s and get killed mid-write, leaving a
**truncated PNG** that PIL refuses to open ("image file is truncated"). Use `-jpeg -r 150` and
delete the bad render before retrying at lower DPI.

### 2.5 Identify key fields from the extracted text

Extract these fields (common in Indian discharge summaries):

| Field | How to find |
|-------|-------------|
| **Patient name** | "Patient Name :" or header |
| **Date of birth / Age** | "D.O.D." / "Date of Birth:" / "Age/Sex:" |
| **Date of admission** | "Date of Admission :" |
| **Date of discharge** | Top-right date or "Date of Discharge:" |
| **Hospital name** | Header letterhead or "Hospital" watermark |
| **IP/Reg/ UHID No** | Unique hospital ID |
| **Primary consultant** | "Primary Dr." or "Consultant:" |
| **Diagnosis / Final Diagnosis** | "Final Diagnosis :" |
| **Procedure performed** | "Operative Procedure:" or "Procedure:" section |
| **Treatment given** | "Treatment Given:" / IV medications |
| **Discharge medications** | "Discharge Medication" table/list |
| **Follow-up** | "Followup Details:" / "Review after X days" |
| **Restrictions / advice** | Post-operative instructions |
| **Emergency contact** | Hospital emergency number |
| **Bill/claim info** | Sponsor/insurance details |

> **IMPORTANT**: The user's Google Workspace account (`ndr@draas.com`) was set up with a Gmail scope that may expire or become stale. If `build_service('drive', 'v3', ...)` or `build_service('calendar', 'v3', ...)` raises `RefreshError: invalid_scope` while People/Sheets/Docs continue working, the google-draas OAuth token needs re-auth. This typically happens after a Google Workspace admin policy change. Surface: "The Gmail/Drive scope on your ndr@draas.com token has expired — you need to re-authorize. Click the button I'm sending to re-approve." The user should still be able to use `build_service('people', 'v1', ...)` and `build_service('sheets', 'v4', ...)` in the interim since those scopes are separate.

## 3. Stage 2 — Enrich the Patient's Google Contact

After filing the document but before researching medications, enrich the patient's Google Contact if it exists under a simple family label (e.g. "Mom", "Dad", "Amma", etc.) rather than a proper name. This ensures the contact has:
- Correct first/last name → used in Calendar attendee resolution
- Email address → used for event invitations
- Phone number → used for WhatsApp summaries
- Nickname field → preserves the original searchable label

### 3.1 Search for the contact by family label

Use Google Contacts `searchContacts` with the likely family label (the user refers to family members by these labels in conversation):

```python
from tools.gws_auth import build_service
people = build_service('people', 'v1', service_name='google-draas')

results = people.people().searchContacts(
    query='Mom',  # or 'Dad', 'Amma', 'Mummy', etc.
    readMask='names,phoneNumbers,emailAddresses,userDefined'
).execute()
```

### 3.2 Identify the matching contact

Filter results to the one with no family name or a givenName matching the label. Typical pattern for label-only contacts:
- `displayName` = `'Mom'`, `givenName` = `'Mom'`, no `familyName`
- Has phone numbers but no email address
- No `userDefined` fields

### 3.3 Update the contact with proper name + email + nickname

```python
# GET current state first (required for etag)
contact = people.people().get(
    resourceName='people/...',
    personFields='names,phoneNumbers,emailAddresses,userDefined'
).execute()

# UPDATE with proper first/last name and email
updated = people.people().updateContact(
    resourceName=contact['resourceName'],
    updatePersonFields='names,emailAddresses,userDefined',
    body={
        'etag': contact['etag'],
        'names': [{
            'givenName': 'Kanta',
            'familyName': 'Ranka',
            'displayName': 'Kanta Ranka',
        }],
        'phoneNumbers': contact.get('phoneNumbers', []),  # preserve existing
        'emailAddresses': [{
            'value': 'kdr@draas.com',  # patient's Google Workspace email
            'formattedType': 'Home',
            'type': 'home',
        }],
        'userDefined': [{
            'key': 'nickname',
            'value': 'Mom',  # the original searchable label
        }],
    }
).execute()
```

> **IMPORTANT:** The `etag` is mandatory on `updateContact`. Always GET first, then PATCH with the fresh etag. If the update fails with a 400/FailedPrecondition, re-GET and retry — another writer may have changed the contact.

### 3.4 Verify the update

```python
# Quick check that the contact now has the right fields
check = people.people().get(
    resourceName=updated['resourceName'],
    personFields='names,emailAddresses,userDefined,phoneNumbers'
).execute()
```

### 3.5 Known family labels

| Label | Proper Name | Email (Calendar + Drive) | Primary Phone |
|-------|-------------|------------------------|---------------|
| Mom | Kanta Ranka | kdr@draas.com | +91 99001 33634 |
| Roshini | Roshini Ranka | rnr@draas.com | +91 98450 26390 |

For family members not in this table, search Google Contacts by their label, then ask the user for the missing details (email / full name).

### 3.6 Why this matters

The enriched contact feeds THREE downstream steps:
1. **Calendar event** — `kdr@draas.com` and `rnr@draas.com` as attendees work because they're Google Workspace domain users (email resolves even if not in contacts)
2. **WhatsApp summary** — the phone number from the contact is passed to `whatsapp_link`
3. **Future searches** — searching "Kanta Ranka" will now find the contact, and searching "Mom" still works via the nickname field

> **Caveat:** The People API `userDefined` field is a general-purpose key-value store, not a dedicated "nickname" field. The Google Contacts UI shows it under "Custom" fields with the key name visible. This is the only way to preserve the original searchable label via API — there is no dedicated `nickname` property on the Google Contacts v3 People API.

## 4. Stage 3 — Determine Filing Location on Google Drive

### 3.1 Find the person's Medical folder

```python
from tools.gws_auth import build_service

drive = build_service('drive', 'v3', service_name='google-draas')
results = drive.files().list(
    q="name contains 'KDR' and name contains 'Medical' and mimeType='application/vnd.google-apps.folder'",
    spaces='drive',
    includeItemsFromAllDrives=True,
    supportsAllDrives=True,
    fields='files(id,name,parents)'
).execute()
```

For family members, known Drive folders:
- **KDR Medical** (Kanta D. Ranka) — id=0B1Oc8cSaJXPGUUtVbTJHb0Y3V2s, parent=KDR Docs
  - Contains subfolder: **Invoices** (id=1jNhEYEe1i2bEdcvQ2Lg9GG2XH4b9mpnu)
- **Murjani Medical** (Charitra Murjani) — id=1erVpDFXh9tdJuhsN5N36Zt69yjX4QG-V
  - Contains subfolder: **Murjani Medical Invoices** (id=1l4YOlo4HCxFAWkoVMMxT1JYloPUDq79R)
  - Can contain **per-person subfolders** for family sub-members (e.g. **Kishan/** inside Murjani Medical). Create these when the user says "under [Name]'s folder" or a document belongs to a specific family sub-member who doesn't have their own top-level medical folder. The subfolder name is just the person's first name (or as the user says it).
  - Convention: `YYYYMMDD Charitra {DocType} {Hospital}.pdf`
    (e.g. `20260701 Charitra Pembrolizumab Prescription St Johns.pdf`, `20260722 Charitra Cough Prescription St Johns.pdf`)
  - Charitra's oncology care is at St John's Medical College Hospital (Dr Annie K. Baa, Dept of Medical
    Oncology, Doc ID 2002) + AIIMS via Dr Rastogi; treatment pembrolizumab (Keytruda) + axitinib for ASPS.
    A **new/persistent cough in a patient on checkpoint inhibitors should flag possible immune-related
    pneumonitis**, not just infection — say so when reviewing such prescriptions.
- **NDR Medical** (Nishant D. Ranka — the user himself) — id=0B1Oc8cSaJXPGT1JPMVlfajFnTmc
  - NDR calls this his "MyMedicalRecords" folder. Contains the **NDR Medical Report Index** spreadsheet
    (id=1gsIQXoVis0TG3eCZFmg0AVzCPG525doPK0ifTIqz2rg) with two tabs:
    - `Sheet1` — report index: SL.NO, TYPE (REPORT/PRESCRIPTION/LETTER/IMAGE/INVOICE...), DATE, REPORT NAME, LINK
    - `Lab Values` — parameter tracking: DATE, TEST NAME, CATEGORY, VALUE, UNIT, REF LOW, REF HIGH (one row per measured parameter per test date)
  - Naming convention: `YYYYMMDD NDR R {Package} {Lab}.pdf`
    (e.g. `20260421 NDR R INSFA Wellness 360 Thyrocare.pdf`, `20260115 NDR Aarogyam Package Thyrocare.pdf`,
    `20260816 NDR R Healthy 2026 Package + INSFA + Homocysteine + Testosterone.pdf`)
- **NDR Medical** (Nishant D. Ranka) — id=0B1Oc8cSaJXPGT1JPMVlfajFnTmc
  - Contains subfolder: **Invoices** (id=1vy22sktwa1aD4bYDRpCad38lxM5P3RGT)
  - NDR Medical Report Index spreadsheet (with Lab Values tab) lives here — see Stage 3.5
- **RNR Medical** (Roshini Ranka) — id=0B1Oc8cSaJXPGUDBMR3Z1MGJZeWc
- **RVR Medical** (Rivaan Ranka) — id=0BymF3UUrZZYKVFY2UzkxUEI0UlU
- **Ruhaan Medical** — id=0B1Oc8cSaJXPGaEhnaDg1Wjl0Q0k
- Other family members: search by name + "Medical" or broad search

### 3.2 Follow existing naming convention

Study the 10 most recent files in the target folder to determine the convention, then match it.

**Known conventions:**
- **KDR Medical**: `YYYYMMDD_KDR_Description_Details.pdf`
  - Example: `20260716_KDR_DischargeSummary_Stapedotomy_Trustwell_DrHaldipur.pdf`
  - Example: `20260711_Manipal_MillersRoad_KantaRanka_OPDNotes_DrVasunethraKasargod_ReviewVisit_MildRiskDisclosure.pdf`
  - Example: `20230613_KDR_DischargeSummary_Stapedotomy_Trustwell_DrHaldipur.pdf` (2023 left-ear procedure)
  - Pattern: `YYYYMMDD_KDR_{DocType}_{Hospital/Clinic}_{DoctorIfRelevant}[_Details].pdf`
- **NDR Medical**: `YYYYMMDD NDR R {Test/Package} {Lab}.pdf`
  - Example: `20260816 NDR R Healthy 2026 Package + INSFA + Homocysteine + Testosterone.pdf`
  - Example: `20260816 NDR R Cortisol.pdf`
- **RVR Medical**: `YYYYMMDD RVR R {Test} {Lab}.pdf`
  - Example: `20260816 RVR R Healthy 2026 Package.pdf`
- **RNR Medical**: `YYYYMMDD RNR R {Test} {Lab}.pdf`

### 3.3 Upload the renamed file

```python
from googleapiclient.http import MediaFileUpload

file_metadata = {
    'name': 'YYYYMMDD_KDR_Description.pdf',
    'parents': [KDR_MEDICAL_FOLDER_ID]
}
media = MediaFileUpload('/path/to/original.pdf', mimetype='application/pdf')
uploaded = drive.files().create(
    body=file_metadata, media_body=media,
    supportsAllDrives=True,
    fields='id,name,webViewLink'
).execute()
```

### 3.4 Verify the upload landed correctly

```python
# List recent files in the folder to confirm it's there
recent = drive.files().list(
    q=f"'{parent_id}' in parents",
    spaces='drive',
    includeItemsFromAllDrives=True,
    supportsAllDrives=True,
    fields='files(id,name,modifiedTime)',
    orderBy='modifiedTime desc',
    pageSize=5
).execute()
```

### 3.5 Lab reports: push every parameter into the Lab Values tracking tab

When the document is a **lab report** (blood work, urine, health-check package), the user wants
more than filing: every measured parameter gets logged into the family member's tracking
spreadsheet so trends can be computed over time. This is a standing DRAAS workflow ("track all
of this data… a spreadsheet online").

1. **Identify the tracking spreadsheet.** Each family member with a Medical folder has a
   `<NAME> Medical Report Index` spreadsheet. NDR's is at `1gsIQXoVis0TG3eCZFmg0AVzCPG525doPK0ifTIqz2rg`
   (tabs: `Sheet1` = report index, `Lab Values` = parameter log). Check `gws_resolve_account` /
   list the Medical folder to find the member's sheet rather than guessing.
2. **Append one row to Sheet1** (report index): next SL.NO (max existing + 1), TYPE=REPORT,
   DATE (ISO `YYYY-MM-DD`), REPORT NAME (the uploaded filename), LINK (the Drive webViewLink).
3. **Extract and cross-validate every parameter** — see Step 3.6b for the dual cross-validation
   pipeline (OCR text extraction + vision image extraction, both via Gemini 2.5 Flash, only
   accept values where both methods agree). This is a standing requirement for ALL lab report
   extractions, not just historical backfills.
4. **Append rows to `Lab Values`**: columns are DATE | TEST NAME | CATEGORY | VALUE | UNIT |
   REF LOW | REF HIGH. One row per parameter. Use the sheet's existing TEST NAME vocabulary
   (e.g. `Fasting Glucose`, `HbA1c`, `HDL Cholesterol`, `LDL Cholesterol`, `Lipoprotein (a)`,
   `hs-CRP`, `Vitamin D`, `Vitamin B12`, `Folate`, `Ferritin`, `Zinc`, `Copper`, `TSH`,
   `Testosterone`, `Homocysteine`, `eGFR`) — do NOT introduce the lab's verbose header names
   (`FASTING BLOOD SUGAR(GLUCOSE)`, `HIGH SENSITIVITY C-REACTIVE PROTEIN (HS-CRP)`, etc.) as
   new test names, or trends will fragment. Categories seen in the sheet: Diabetes, Lipid,
   Cardiac Risk, CBC, Iron Studies, Kidney, Liver, Thyroid, Vitamins, Minerals, Hormones,
   Bone, Urine, Pancreas, Electrolytes.
5. **Urine panel**: only pH and specific gravity are numeric/outlier-prone; the rest are
   qualitative (ABSENT/normal) — log pH + SG, skip the qualitative rows.
6. **Verify** by re-reading the tail of both tabs after append.

### 3.6 Trend comparison & diagnosis across past reports

The user asks for: compare this report against the previous 1–3, flag what's good/bad, note
what looks off *for the entire family*, and say whether retesting is warranted.

**Deliverable format (NDR's explicit ask — follow it exactly):** when he says "review and
analyze it for all parameters… what is improving or going wrong… suggestions", produce ONE
message per family member with these exact sections:
1. **Improving ✅** — in-range + improving vs history (with numbers)
2. **Going wrong ⚠️** — out-of-range or wrong-direction trends (with numbers + ref)
3. **What to test next** — named tests with reason + horizon (e.g. "repeat homocysteine with B12/folate/B6 in same draw")
4. **Suggestions** — split into: 🥗 Food / 💊 Supplements / 🏃 Exercise / 💊 Medication (each concrete, dose-level where sensible)
Then a **family-wide comparison table** (same metric across all members, e.g. HbA1c / Lp(a) / Vitamin D / Ferritin) + a **pending labs** line for reports still "Processing" (e.g. DHEA-S, HDM allergy panel). Close with a disclaimer that this is family awareness, not medical advice — review with their doctors.

## 3.6c Enhanced "clinical-profile-aware" diagnosis — the master deliverable (recurring)

NDR's richer ask (recurring Aug 2026): not just trend comparison but a **per-person clinical diagnosis** document that:
- Uses the FULL Lab Values data (all 600–800 rows: date, unit, actual value) for each of the four members (**NDR, RNR/Roshini, Ruhaan, RVR/Rivaan**)
- Folds in each person's **clinical background** — known conditions, past doctor visits (e.g. NDR: CCTA/MPI 2019, cardiology advisories Dr Sunil Dwivedi / Dr Priya Chinnappa, seborrhoeic dermatitis, mentioned supplements; Roshini perimenopause; Ruhaan/Rivaan atopy/asthma) and the user's own risk framing
- Produces, per member: **Latest-report diagnosis → Risk assessment → Improving ✅ → Deteriorating ⚠️ → Interventions (Food/Supplements/Exercise/Medical) → Longevity / latest-research framing**
- Grounds interventions in LATEST research/trials + credible longevity/biohacker consensus (Attia: apoB as causal ASCVD particle, Lp(a) fixed/genetic → screen early + manage everything else, CGM for glycemia, diabetes-as-insulin-resistance; Patrick: homocysteine/B-vitamin-vascular-cognitive link, VitD/K2/protein/resistance for bone, zinc/copper; Sinclair: sugar/micronutrient/lifelong-CV levers; Norton: evidence-based diet on refined carbs/resistance/post-meal movement; RNA Lp(a) therapies pelacarsen/apo(a)-siRNA in late trials; perimenopause HRT as shared decision, not self-started)

**⛔ CRITICAL — always check for an existing deliverable BEFORE generating.** These documents are large, expensive to produce, and are often ALREADY prepared in a prior session (often the same day, following the same 2026-08-16 report batch). Before running any subagents or writing a new markdown, **run `search_files(pattern='*', target='files', path='/data/hermes/projects/medical')`** and read the latest master file. Known recurring artifacts (Aug 2026), all under `/data/hermes/projects/medical/`:
- `Medical-Analysis-Enhanced-2026-08.md` — **THE master enhanced doc** (all 4 members, clinical-profile + longevity framing). Primary deliverable.
- `Medical-Trend-Analysis-2026-08.md` — trend-data foundation the enhanced doc builds on.
- `NDR-Diagnosis-2026-08.md`, `Ruhaan-Diagnosis-2026-08.md` — prior per-member deep-dives.
**Do NOT regenerate duplicates** — this session wasted ~4 subagent runs creating `diagnosis-*.md` files that duplicated the master until caught and deleted. If asked "where is the analysis" and the file exists, answer "it's prepared at <path>" and deliver it rather than re-creating. Only prepare fresh if the master is genuinely absent or the user wants a materially different structure.

1. **Pull history**: read the full `Lab Values` tab once, group rows by TEST NAME in Python,
   sort by date. This gives per-parameter time series spanning years (NDR's sheet has data back
   to 2014).
2. **Normalize test names when grouping** — the sheet has drift (e.g. `WBC` vs
   `TOTAL LEUCOCYTE COUNT (WBC)`, `Platelets` vs `Platelet Count`, `HDL CHOLESTEROL - DIRECT`
   vs `HDL Cholesterol`, `LDL CHOLESTEROL - DIRECT` vs `LDL Cholesterol`). Group with a
   lowercase/stripped key or an alias map, else trends silently miss rows.
3. **Watch for junk historical rows** — earlier manual entries can contain garbage (e.g.
   `Urine pH = 45.23` in the 2025-01-06 batch, Apolipoprotein columns swapped to `68`/`0.5`).
   Sanity-check outliers against the actual report before quoting them in a trend.
4. **Flag structure**: what's GOOD (in-range + improving), what's OFF (out of range or
   trending the wrong way), plus a retest recommendation with a horizon per flagged parameter.
   Family-wide comparison is limited: KDR/RNR/RVR/Ruhaan sheets are report indexes only (no
   Lab Values tabs) — only NDR's sheet tracks numeric parameters, so family comparisons rely
   on scanning the index sheets for blood-test report names or opening individual PDFs.
5. **Medical context for common Indian-package flags** (Healthy 2026 / Aarogyam / INSFA):
   - HbA1c: <5.7 normal, 5.7–6.4 prediabetic, ≥6.5 diabetic (ADA). A reading of 5.9 with a
     rising fasting glucose (85→90→94→96.5) is a retest-in-3-months signal, not panic.
   - Lp(a): largely genetic and stable across years (NDR ~82–100 mg/dL vs ref <30) — don't
     suggest frequent retests; it's a one-time risk stratification marker.
   - Eosinophils: NDR had 8–14% for 2 years (ref 1–6) — family history of atopy (Ruhaan
     asthma); a normal reading is notable improvement.
   - Zinc/Copper/Vitamin D insufficiency are common recurring themes; pair with supplementation
     advice and a 3-month recheck.
   - TSH creeping to the upper edge of range (2.9→4.18) while T3/T4 stay normal = recheck in
     3–6 months, not urgent.
   - Homocysteine >15 after years at 11–14: check B12/folate/B6 in the same draw before
     supplementing — don't guess the cause.
   - Prolactin ~2× upper limit (Roshini 40.5 vs ref 4.79–23.3): lab recommends recheck 3
     specimens 20–30 min apart + macroprolactin assay before any diagnosis — say so verbatim.
   - FSH/LH/E2 consistent with perimenopause at ~46 is expected, not pathology.

### 3.6b ALL-parameter historical backfill — when a member's Lab Values tab has only one date

When the user asks for trajectory analysis and a member's Lab Values tab contains only the
latest report (one date — happens when a sheet was created in the Aug 2026 batch but older
reports were never backfilled), **backfill EVERY parameter from every historical report**,
not just a curated subset. The user explicitly corrected (Aug 2026): "each report has over
107 parameters... why did we add only 32 rows?" — the expectation is ~80 rows per report
date, matching the full parameter set of the latest report.

**Pipeline (validated Aug 2026, 16 reports, 967 total params, 0 mismatches):**

1. **List the member's Medical folder** for older lab-report PDFs (blood/urine/hormone panels;
   skip prescriptions, OPD notes, X-rays, receipts).

2. **Extract via Gemini 2.5 Flash (text-based):** Send the full extracted text (pdftotext or
   pymupdf output) to `call_openrouter_model` with model `google/gemini-2.5-flash` and a
   prompt requesting ALL test results as a JSON array. The model normalizes test names
   automatically. Include the full text (up to ~60K chars) — Gemini handles it easily.

3. **Cross-validate via Gemini 2.5 Flash (vision-based):** For each report, render each
   data-page to a PNG image (pymupdf `page.get_pixmap(dpi=200)`, base64-encode), send to
   Gemini 2.5 Flash vision via OpenRouter's multimodal API, extract parameters from the page
   image. **Key rule: target the same section of the report as the text extraction** — render
   the specific page or crop that contains the matching test block, not the whole report at
   once (the user's explicit instruction: "running only that particular snapshot of that
   section through again vision model"). Compare the vision-extracted values with the
   text-extracted values. **Accept only parameters where both methods agree on the value.**
   Mismatches are flagged for review with both values shown.

4. **Append cross-validated rows** to the member's Lab Values tab using the SAME normalized
   TEST NAME + category vocabulary as the existing rows. Use the member's existing sheet
   IDs (see `references/family-lab-values-tracking.md`).

5. **Result:** per member, every historical report contributes ~80 rows to the Lab Values tab,
   making the tracking sheet genuinely longitudinal. Worked example (Aug 2026): RNR backfilled
   700 rows across 9 dates (2018–2026), Ruhaan 174 rows across 7 dates, RVR 152 rows across
   3 dates — all cross-validated with 0 mismatches.

**Thyrocare/RLS backward-parser quirk:** in these PDFs' extracted text, the VALUE line
precedes the TEST NAME line (layout: `METHOD\nVALUE\nUNIT\nTESTNAME`), the opposite of most
report formats — a forward-looking parser silently drops everything. The working pattern is a
**backward-looking scan**: for each line that looks like a TEST NAME (all-caps, len>4, not
ending ':'), look back 1–2 lines for a numeric VALUE and capture the unit/ref that follow.
Also strip non-parameter noise (lipid category labels like `NORMAL: <150`, method names like
`PHOTOMETRY: 92.2`) — they collide with real test names. Verify key readings against the
"Tests Outside Reference Range" summary page rather than trusting parse output blindly.

**However, the Gemini 2.5 Flash extraction method (step 2) handles this automatically and
is far more reliable than a hand-written parser** — prefer it for all new extractions. The
backward-parser note is only relevant if you need to extract without an OpenRouter-capable
model.

**Cross-validation script pattern:** see `references/family-lab-values-tracking.md` for the
full Gemini extraction + vision cross-validation workflow, including the OpenRouter API call
formats for both text and vision modes, the comparison logic, and the batch processing
pattern.

### 3.7 Report interpretation framing

Lead with the answer, then the evidence. For action confirmations (filed/tracked), state what
was done with concrete IDs (SL.NO, row counts, file link). For the assessment, group into
GOOD / OFF / RETEST sections — no tables in Telegram, use labeled bullets.

## 3.5 Stage 3.5 — Family Lab Values Tracking System (report → Lab Values pipeline)

NDR tracks every family member's lab parameters over time in per-member Google Sheets. Each member has a **Report Index** spreadsheet with:
- **Index tab** (`Sheet1` or `Reports & Prescriptions`): `SL.NO | TYPE | DATE | REPORT NAME | LINK` (TYPE ∈ REPORT / PRESCRIPTION / INVOICE / LETTER / DICF / DRF / IMAGE)
- **Lab Values tab**: `DATE | TEST NAME | CATEGORY | VALUE | UNIT | REF LOW | REF HIGH` (header frozen + bold, 1000-row grid)

Canonical per-member spreadsheets (all have Lab Values tab since Aug 2026):
- **NDR** `1gsIQXoVis0TG3eCZFmg0AVzCPG525doPK0ifTIqz2rg` (tabs: Sheet1, Lab Values)
- **KDR** `1DjfOon0dY74ReAREt5GAPpPNWM464lYvJYrESqiUB2g` (Sheet1, Lab Values)
- **RNR** `1rhK4XONTYmBmYpRyKMpLFMn4UupLJ_Gufv02RmE570E` (Sheet1, Lab Values)
- **RVR (Rivaan)** `1YJ8iYEAHCVjBRaaE_iU3_Q8aEJZ1aSP_WXNk0w7RXyA` (Sheet1, Lab Values)
- **Ruhaan** `1E14iA3xDdoBaC0Sdlim6r6MipmSzNkKqFLaV2dXvHQU` (tabs: Reports & Prescriptions, BILLS, Lab Values)

Per-report pipeline (NDR's explicit workflow — ONE report at a time):
1. **Rename** per member convention (see 3.2)
2. **Upload** PDF to the member's Medical folder
3. **Index**: append row to the member's index tab — next SL.NO (max existing + 1), TYPE=REPORT, DATE `YYYY-MM-DD`, REPORT NAME, LINK
4. **Extract** every parameter (RLS/Thyrocare PDFs are text-based → `pdftotext -layout` works, no OCR needed)
5. **Lab Values**: append rows with canonical TEST NAME forms (see `references/family-lab-values-tracking.md` for the full mapping + worked values) — use the SAME test name every time or trend queries break

**Receipts**: multi-member payment receipts (e.g. one Thyrocare receipt covering NDR + Rivaan + Roshni) → file in **NDR Medical > Invoices** (payer's folder), TYPE=INVOICE in NDR's index. Name like `20260816_NDR_Thyrocare_Receipt_VL4052F0_NDR_Rivaan_Roshni_6186.pdf`, and put a `description` on the Drive file listing which patient/tests each covers.

Full worked example, canonical test-name list, category set, and the exact append script pattern: `references/family-lab-values-tracking.md`.

## 4.5 — Family Lab Values Tracking System (lab report pipeline)

For DRAAS family **lab reports** (Thyrocare/RLS "Healthy 2026" style, cortisol, etc.), NDR runs a per-member tracking system: each member has a **Medical Report Index spreadsheet** (report inventory) with a **Lab Values tab** (long-format parameter history: `DATE | TEST NAME | CATEGORY | VALUE | UNIT | REF LOW | REF HIGH`). Every new lab report goes through the full pipeline:
**Pipeline per report (NDR's explicit order):**
1. **Rename** with family convention `YYYYMMDD <Initials> R <Test> <Lab>.pdf` (e.g. `20260816 RVR R Healthy 2026 Package.pdf`, `20260816 NDR R Cortisol.pdf`)
2. **Upload** to the member's Medical folder (IDs in `references/family-lab-values-tracking.md`)
3. **Index** in their Report Index sheet (Sheet1 / 'Reports & Prescriptions' tab), TYPE=REPORT, next SL.NO
4. **Extract and cross-validate** every parameter — see the dual cross-validation pipeline in section 3.6b (text + vision, both via Gemini 2.5 Flash, accept only where both agree). Standing requirement for ALL extractions.
5. **Append** rows to their Lab Values tab using the **normalized test names** listed in the reference file so trends line up across reports

Payment receipts → **NDR Medical > Invoices** (payer = NDR), TYPE=INVOICE in NDR's index, description lists every patient/test covered. Interim reports (some tests "Processing") still get filed + tracked for the Ready parameters, with the pending tests flagged in the summary.

**Family-wide comparison section** (see 3.6) — cross-member metrics comparison.

## 3.6 Stage 3.6 — Genetic / Polygenic Risk Score (PRS) Test Report Analysis

When the document is a **genetic screening test report** — e.g. MedGenome Kardiogen, 23andMe Health, or any polygenic risk score (PRS) report for heart disease, diabetes, cancer, etc. — it requires a fundamentally different analysis than a lab report or discharge summary. These are **screening** tests, not diagnostic tests, and the output is a statistical risk score, not a measured parameter.

### 3.6.1 Identify the test type

Key signals in the report text:
- "Polygenic Risk Score" / "PRS" / "KRS" / "Kardiogen Risk Score"
- "Genetic screening test" / "NOT a diagnostic test"
- "Genome-wide" / "whole genome genotyping"
- "Odds ratio" / "decile" / "risk category"
- Company: MedGenome, Genessense, 23andMe, Myriad, Color, etc.

### 3.6.2 Key fields to extract

| Field | What to look for | Example |
|-------|-----------------|---------|
| **Test name** | Header or title | KARDIOGEN — Genetic Risk Assessment for Heart Health |
| **Company / Lab** | Footer or lab info | MedGenome Labs Ltd., Genessense |
| **Patient** | Personal info section | Kishan Murjani Nair, 37, Male |
| **Risk Score (KRS/PRS)** | Numerical score | -0.789 |
| **Risk Category** | Average / Moderate / High | Average |
| **Odds Ratio** | Multiplier vs general population | ≤1.0 |
| **Decile Bin** | 1–10 ranking | 4th decile |
| **Validation cohort** | Study population size | 2,963 South Asian individuals |
| **Scientific publication** | Model source | Nature Medicine Jul 2023 (Patel/Khera), JACC 2020 (Wang et al.) |
| **Lab accreditation** | CAP / CLIA / NABL | CAP (College of American Pathologists) |

### 3.6.3 How to interpret the results for the user

Structure the analysis as a **"What it is → What it means → What it doesn't tell you → Verdict"** narrative:

1. **What the test is** — A polygenic risk score reads 1M+ genetic markers across the genome and compresses them into a single score. It's like a "credit score for your heart genetics" — a statistical estimate of inherited predisposition, NOT a diagnosis of current disease.

2. **What the result means** — explain the three-tier system:
   - **Average risk** (KRS < 0.123, odds ratio ≤ 1.0): genetic risk is at or below population average. This is the best category. The person's genes do NOT put them at elevated risk.
   - **Moderate risk** (KRS 0.123–0.840, odds ratio 1.42–1.92): modestly elevated genetic risk.
   - **High risk** (KRS ≥ 0.840, odds ratio 3.08): 3× more likely to develop CAD. 76% of people in this zone had CAD in the validation study.

3. **What it does NOT tell you** — critically important to flag:
   - It does NOT diagnose current disease (not a stress test, ECG, or angiogram)
   - Lifestyle factors (diet, exercise, smoking, cholesterol, BP, blood sugar) are equally or more important
   - A low-risk result is NOT a free pass to ignore lifestyle
   - A high-risk result is NOT a guarantee of disease — healthy lifestyle reduced events by 46% even in high-genetic-risk groups (Harvard study cited in the report)

4. **Validation & scientific credibility** — assess the lab's claims:
   - **Published model?** Nature Medicine / JACC publication = strong. Lab-internal model = weak.
   - **South Asian validation?** Critical for Indian patients. Models built on European populations don't transfer well. MedGenome validated on 2,963 South Asians.
   - **Lab accreditation?** CAP/CLIA/NABL = gold standard.
   - **Marker count?** 1.29M markers is comprehensive (consumer tests use 600K–700K).

5. **Practical value verdict** — give a balanced take:
   - "This is valid science, worth keeping in the medical file."
   - "Combine with regular clinical checks (lipid profile, BP, HbA1c, family history)."
   - "Genetic risk is stable across a lifetime — no need to retest."
   - "The lifestyle recommendations in the report (diet, exercise, sleep, no smoking) are identical to general heart-health guidelines."

### 3.6.4 Naming convention for genetic test reports

Format: `YYYYMMDD {FirstName} Kardiogen {FullTestName} {Company}.pdf`
- Example: `20260823 Kishan Kardiogen Genetic Risk Assessment Heart Health MedGenome.pdf`

### 3.6.5 Filing location

- If the person has their own medical folder → file directly inside it
- If the person is a family sub-member without their own folder → create a subfolder inside the family medical folder (e.g. "Kishan" inside "Murjani Medical") — see Stage 3.1 for subfolder creation pattern
- If the person is a new family member → ask the user where to file it

### 3.6.6 No lab values tracking needed

Genetic tests produce a **single stable risk score** that does not change over time — unlike blood parameters that need trend tracking. Do NOT attempt to add rows to the Lab Values tab. The report is filed as-is and the analysis is communicated verbally to the user.

## 4. Stage 4 — Research Medications

When the discharge summary lists medications, explain each one's purpose. Use this reference guide for common post-operative ear surgery medications (from a known real discharge summary):

| Medication | Common Name | Purpose |
|------------|-------------|---------|
| **Diamox** 250 mg | Acetazolamide | Carbonic anhydrase inhibitor — reduces CSF pressure to prevent perilymphatic fistula/gusher post-stapedotomy. Also helps with post-op dizziness. |
| **Sumo** | Aceclofenac + Paracetamol (most common) | Anti-inflammatory + analgesic — manages post-operative pain and inflammation. Some brands may contain serratiopeptidase for added anti-swelling effect. |
| **Stugeron** 25 mg | Cinnarizine | Vestibular suppressant / calcium channel blocker — controls vertigo, dizziness, and nausea common after inner ear surgery. |
| **Pantop-D** | Pantoprazole + Domperidone | Gastric protection — pantoprazole reduces stomach acid; domperidone prevents nausea/vomiting caused by other post-op medications (steroids, NSAIDs). Taken before food. |

When web_search is unavailable (FIRECRAWL_API_KEY not configured), use your own pharmacological knowledge. If unsure about a specific brand or medication, say so honestly — don't fabricate.

### Research fallback when web is unavailable

1. Use `call_openrouter_model` with a prompt like "What is [Medication] [Dosage] used for in the context of [Procedure/surgery] post-operative care?"
2. Cross-reference with known Indian brand names (many are available in the Drug Today / 1mg databases)
3. If still unsure, group by apparent function: painkillers (analgesics), anti-vertigo/dizziness, stomach protection, antibiotics, anti-inflammatory

## 4b. Finding an EXISTING Prescription / Medication Record (lookup, not processing)

When NDR asks "find the `<medicine>` prescription for `<family member>`" (voice often garbles
the drug: "Azitro Maisan" → Azithromycin) — this is a lookup over the family medical Drive
estate, NOT the file-a-new-document pipeline.

**Search ladder (fastest → definitive):** session_search → `/data/hermes/projects/medical/`
(analysis docs only) → Drive `fullText contains '<drug>'` (**misses scanned PDFs — Drive
doesn't index image-based PDFs**) → **walk the member's Medical folder listing and pick
`*_Prescription_<Doctor>.pdf` candidates by date-range + doctor** → download + `pdftoppm
-r 150` + `vision_analyze` to confirm the actual drug (brands vary: AZEE = Azithromycin).

Full worked example (Ruhaan's Azithromycin, Dr Bharath Reddy at Shishuka Children's Specialty
Hospital, 13-Jun-2026), family folder walk, brand→drug mappings, and voice glossary:
`references/prescription-lookup.md`.

## 6. Stage 5 — Create Follow-up Calendar Event

### 5.1 Extract follow-up timing

Look for phrases like:
- "Review after X days with Dr. [Name]"
- "Follow-up in [department] OPD with prior appointment"
- "Next visit: [date]"

Calculate the actual date:
- Discharge date = 16 July 2026 (for reference)
- "Review after 10 days" + discharge date → 26 July 2026
- The summary may also show a suggested date range in parentheses: `(25|26)`

### 5.2 Create the event

```python
from tools.gws_auth import build_service
calendar = build_service('calendar', 'v3', service_name='google-draas')

event = {
    'summary': 'KDR - Follow-up with Dr. [Name] ([Specialty]) - [Hospital]',
    'description': '''Follow-up after [Procedure] done on [Date] at [Hospital].
    
Discharged: [Date]
Surgeon: Dr. [Name]
Hospital: [Hospital], [Address]

Notes: Prior appointment required. Call [Hospital] [Department] OPD to confirm slot.
Emergency Contact: [Hospital Phone]

Restrictions still active: [list relevant restrictions].''',
    'start': {
        'dateTime': '2026-07-26T10:00:00',
        'timeZone': 'Asia/Kolkata',
    },
    'end': {
        'dateTime': '2026-07-26T11:00:00',
        'timeZone': 'Asia/Kolkata',
    },
    'attendees': [
        {'email': 'kdr@draas.com'},    # Patient
        {'email': 'rnr@draas.com'},    # Family member / caregiver
    ],
    'reminders': {
        'useDefault': False,
        'overrides': [
            {'method': 'email', 'minutes': 1440},   # 1 day before
            {'method': 'popup', 'minutes': 120},     # 2 hours before
        ],
    },
}

created = calendar.events().insert(
    calendarId='primary', body=event, sendUpdates='all'
).execute()
```

**Known attendees for KDR medical events:**
- Kanta Ranka (patient): `kdr@draas.com`
- Roshini Ranka (family caregiver): `rnr@draas.com`

For other family members, find their Google Workspace email from:
1. Google Contacts search
2. NDR DRAAS Contact Sheet (Sheet ID `1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g`)
3. If not found in contacts, the user may need to provide the email

### 5.3 Verify the event

```bash
# Check it's on the calendar, confirm attendees
```

## 7. Stage 6 — Generate WhatsApp Summary for the Patient/Family

Compose a concise WhatsApp message summarizing:
1. Key medications and their purpose (simple explanation)
2. Follow-up date and doctor
3. Important restrictions (what NOT to do)
4. Emergency contact number
5. A comforting closing line

**Example message structure:**

> [Name] — your discharge summary is filed. Quick recap:
>
> 1. **Medications** — [Drug name] (purpose), [Drug name] (purpose), etc. Take as prescribed.
>
> 2. **Follow-up** with Dr. [Name] on ~[Date] — [Family member] will accompany you.
>
> 3. **Restrictions:** [Most important 2-3 restrictions]
>
> 4. **Emergency:** [Hospital] — [phone]
>
> Rest well. Love you.

Use the `whatsapp_link` tool to generate the link. The phone number comes from the patient's enriched Google Contact (Stage 3 / section 4) — specifically the canonical phone field. If the patient has multiple numbers, use the primary one (first in the array, which has `metadata.primary: true`).

Common restriction phrasing (post-ear surgery):
- No coughing, sneezing, nose blowing
- No heavy lifting / sudden head movements
- No outstation travel for 10 days
- No air travel for 2 months

## 8. Post-Processing Q&A — Answering Clinical Follow-Up Questions

After the initial pipeline (extraction → filing → medications → calendar → WhatsApp), the user often follows up with specific clinical questions about what the document says or doesn't say. This happens most frequently with discharge summaries after surgery.

### 8.1 Identify the question domain

The user's follow-up questions typically fall into these categories:

| Category | Example questions |
|----------|-----------------|
| **Follow-up timing** | "Is it 25th or 26th?" "When exactly is the review?" |
| **Restrictions** | "Does it say no nose blowing?" "Heavy lifting?" "Air travel?" |
| **Ear/incision care** | "Cotton replacement?" "How often?" "When to remove packing?" |
| **Bathing / hygiene** | "Head bath allowed?" "Water in ear?" "Shower restrictions?" |
| **Activity resumption** | "When can she go outstation?" "Exercise?" "Driving?" |
| **Medication clarification** | "Is this for pain or dizziness?" "Before/after food?" |

### 8.2 How to answer — three-layer approach

**Layer 1: Read the document.** Re-extract text from the original PDF and search for the specific term (e.g., "bath", "cotton", "packing", "water", "shower", "sponge", "clean", "change"). Most discharge summaries are short enough to re-read completely.

**Layer 2: Note the gap.** If the term doesn't appear, say so explicitly: "Not mentioned in the discharge summary." Do NOT fabricate instructions or guess common medical practice as fact. Frame the absence as something to clarify with the doctor.

**Layer 3: Only contextualize with general knowledge when clearly flagged as such.** If you know a common post-surgical standard (e.g., "keep ear dry after ear surgery to prevent infection"), present it as general knowledge, not as something from the document. Use phrases like:
- "The discharge summary doesn't address this. For [procedure type], the general standard is usually [X], but this should be confirmed with the surgeon."
- "This would typically be covered in a separate post-op care sheet from the nursing staff, not in the discharge summary itself."

### 8.3 Common post-stapedotomy questions and what discharge summaries typically say (or don't)

| Question | In this discharge summary? | Common general guidance (flag as NOT from document) |
|----------|--------------------------|-----------------------------------------------------|
| Nose blowing? | ✅ Usually listed explicitly | Can cause pressure changes that disrupt the stapes prosthesis |
| Cotton/packing replacement? | ❌ NOT in summary | Packing typically removed by surgeon at follow-up, not by patient. Ask at appointment. |
| Head bath / water in ear? | ❌ NOT in summary | Keep ear dry until follow-up. Use Vaseline-coated cotton ball in outer ear when bathing. |
| Air travel? | ✅ Usually listed (2 months) | Pressure changes during flight can disrupt healing |
| Heavy lifting? | ✅ Usually listed (2 months) | Similar pressure/straining concern |
| Outstation travel? | ✅ Usually listed (10 days) | Staying near the hospital in case of complications |

### 8.4 When the document is ambiguous

Discharge summaries sometimes show conflicting or ambiguous dates. The user flagged a case where the summary said `(25\|26)` — both dates listed. In this case:
1. The summary says "Review after 10 days" → discharged 16 July + 10 days = 26 July
2. But the parentheses show `(25|26)` — the doctor indicated either is acceptable
3. Let the user decide, confirming which date works best with their schedule

### 8.5 Present clearly with source attribution

Format: "The discharge summary says [X]. It does NOT mention [Y] — you'll need to confirm with [Dr./hospital] at the follow-up."

This is more useful than fabricating an answer or saying "I don't know."

## 9. Pitfalls

### P1. Family contacts may be stored under a simple label, not a proper name

Family members (Kanta "Mom", Roshini, etc.) are often stored in Google Contacts under a simple label — `givenName: 'Mom'`, no `familyName`, no `emailAddresses`. This makes them invisible to name-only searches like "Kanta Ranka". They **do** show up when searched by their label:

```python
# DON'T: this returns nothing for label-only contacts
people.people().searchContacts(query='Kanta Ranka', ...)

# DO: search by the likely family label
people.people().searchContacts(query='Mom', ...)
```

When you can't find a patient's contact by their full name, try these labels (in order of likelihood based on Indian family conventions):
1. `Mom` / `Mummy` / `Amma` / `Mother`
2. `Dad` / `Papa` / `Appa`
3. The family member's first name alone (e.g. just "Roshini")

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `searchContacts('Kanta Ranka')` returns nothing | Contact stored as `givenName: 'Mom'` | Search by family label, See Stage 3 (section 4) above |
| `searchContacts('Mom')` finds a contact with no family name | Label-only contact | Run Stage 2.5 enrichment to add proper name + email + nickname |
| Contact has phone numbers but no email | Email was never added | Add `kdr@draas.com` (domain email resolves for Calendar even if not in contacts) |

**Important:** Even without the contact enrichment, `kdr@draas.com` works as a Calendar attendee because it's a Google Workspace domain user. The enrichment is for WhatsApp phone number discovery and for proper contact hygiene.

### P2. Venv activation for gws_auth
The `tools.gws_auth` module requires the Hermes venv at `/opt/hermes/.venv/`. Always run Python scripts using:
```bash
/opt/hermes/.venv/bin/python3 script.py
```
Not the system Python (which lacks `googleapiclient`).

### P3. pdftotext may return garbled text for scanned PDFs
If `pdftotext` produces unreadable output, the PDF is a scan (image-based). Fall back to ocrmypdf (`--force-ocr`) or convert to images for vision analysis.

### P4. Calendar event description should be comprehensive
The event description should include enough medical context that any family member opening the event can understand what it's about. Include: procedure name, date, surgeon, hospital, restrictions still active, and emergency contact.

### P5. Gmail scope may be stale while drive/calendar/people are fine
This is documented in MEMORY and USER PROFILE. If `build_service('drive', 'v3', ...)` throws `RefreshError: invalid_scope` for `google-draas`, the Gsuite OAuth scope was lost during re-auth. People/Sheets/Docs/Drive may still work. Don't assume the whole vault is broken — re-auth only the failing scopes via `send_oauth_url`.

### P6. Adding a "Lab Values" tab: batchUpdate with `sheetId: None` fails
When creating the Lab Values tab, the `addSheet` request succeeds, but a follow-up `batchUpdate` that references the new sheet via `sheetId: None` fails with `Invalid requests[0].updateSheetProperties: No sheet with id: 0` (the sheet ids are not 0-based / the new tab got a random id). Fix: after `addSheet`, re-fetch spreadsheet metadata (`spreadsheets().get()`), find the new tab's actual `properties.sheetId`, and use that in `updateSheetProperties`/`repeatCell` requests. Verified Aug 2026 on Ruhaan's sheet (new tab id was 123181047).

### P7. Duplicate family index spreadsheets exist — use the canonical one
Search results for family index sheets return duplicates (e.g. `NDR Medical Report Index` exists at `1gsIQXoVis...` inside the NDR Medical folder AND at `1fLF1oiHtnvMoOaJiD7J9h-pYiBL4Klh2qE9UwPPSo6k` in root). Use the one whose `parents` is the member's Medical folder, and prefer the most recently modified. Same for RNR (two sheets exist: `1rhK4XONT...` in RNR Medical folder vs `1VB6FsfTAOi...` root) and KDR. When in doubt, check `modifiedTime` and which folder parents point to.

### P8. Paediatric reference ranges differ from adult ranges
Child reports (Rivaan, Ruhaan) use age-specific ranges — e.g. Rivaan 13Y: ALP 127–403 U/L, TSH 0.72–5.77 µIU/mL, MPV 7.5–8.3 fL, creatinine low-normal 0.55 mg/dL (kids run lower than adult 0.72–1.18). Do NOT flag paediatric values against adult ranges; use the report's own Bio. Ref. Interval column.

### P9. WhatsApp Medical-folder share: keep short, drop resourcekey, verify recipient is already editor (hit 2026-08-20)
When NDR asks to WhatsApp a family member (e.g. Roshini, rnr@draas.com, +91 98450 26390) the family medical Drive folder links: the 4 canonical folders are NDR Medical `0B1Oc8cSaJXPGT1JPMVlfajFnTmc`, Ruhaan Medical `0B1Oc8cSaJXPGaEhnaDg1Wjl0Q0k`, RNR Medical `0B1Oc8cSaJXPGUDBMR3Z1MGJZeWc`, Rivaan Medical `0BymF3UUrZZYKVFY2UzkxUEI0UlU` — and **rnr@draas.com is already an editor on all four** (verify with `permissions().list()` before assuming a share is needed; usually no permission change is required). Omit the `?resourcekey=0-...` suffix when sharing with an existing editor — they don't need it, and 3-4 full resourcekey URLs make the WhatsApp message too long so Telegram cuts it off mid-list (NDR reported exactly this: "it just cuts off at folders"). Send plain `https://drive.google.com/drive/folders/<id>` links, one per line, keep the whole message under the single-message limit.

## 10. Family Lab Values Tracking (per-member parameter sheets)

NDR keeps, per family member, a **medical report index spreadsheet** (report list) AND a **Lab Values tab** (every lab parameter from every report — one row per parameter per date) so trends can be compared across reports and across family members. Standing directive (Aug 2026): process **ONE report at a time, ONE family member at a time** — never batch all reports together.

**Pipeline per report (NDR's explicit order):**
1. **Rename** PDF with family convention: `YYYYMMDD {Initials} R {Package} {Lab}.pdf` (e.g. `20260816 NDR R Healthy 2026 Package + INSFA + Homocysteine + Testosterone.pdf`)
2. **File** into that member's Medical folder on Drive (folder IDs in `references/family-lab-values-tracking.md`)
3. **Index** — append row to the member's Report Index sheet (tab Sheet1 / Reports & Prescriptions): `SL.NO = max+1, TYPE, DATE, REPORT NAME, LINK`
4. **Extract and cross-validate** every parameter — see the dual cross-validation pipeline in section 3.6b (text + vision, both via Gemini 2.5 Flash, accept only where both agree). Standing requirement for ALL extractions.
5. **Lab Values** — append one row per parameter to the member's Lab Values tab: `DATE, TEST NAME, CATEGORY, VALUE, UNIT, REF LOW, REF HIGH`

**Test-name normalization:** reuse the exact TEST NAME strings already in the member's Lab Values tab (`Fasting Glucose`, `HbA1c`, `Total Cholesterol`, `HDL Cholesterol`, `LDL Cholesterol`, `Triglycerides`, `Lipoprotein (a)`, `hs-CRP`, `Vitamin D`, `Vitamin B12`, `Folate`, `Zinc`, `Copper`, `TSH`, `Testosterone`, `Homocysteine`, `eGFR`, `Neutrophils`, `Eosinophils`…) so trend rows line up. Categories used: Diabetes, Lipid, Cardiac Risk, CBC, Iron Studies, Kidney, Liver, Thyroid, Vitamins, Minerals, Hormones, Urine, Bone. Append with `values().append(..., valueInputOption='USER_ENTERED', insertDataOption='INSERT_ROWS')`.

**Updated report replaces old ("newer version, delete earlier one"):** When the user uploads a report saying it's an updated/complete version of one already tracked, follow this comparison workflow:
1. **Confirm this is a later version** — same date? same lab? same package? If yes (same date, same patient, superseding the earlier upload), proceed.
2. **Extract ALL parameters** from the new report (pdftotext + backward-scan for RLS/Thyrocare format — VALUE often precedes TEST NAME).
3. **Map to canonical sheet names** — normalize report headers to the Lab Values tab's existing TEST NAME vocabulary (your `sheet_params` key set). Imperfect matches still go through the canonical name.
4. **Compare**: build the set of params in the new report vs the set already in the sheet for that date. Three outputs:
   - **New params** (in report, not in sheet) — will be appended.
   - **Matched params** (in both) — values should match; if they differ, flag for user review.
   - **Orphan params** (in sheet, not in report) — these existed from the earlier partial upload but aren't in the complete version. **Ask the user** before deleting them — they may come from a separate test (e.g. standalone Cortisol) that the main package doesn't cover, and losing them silently is worse than keeping a stale value.
5. **Decision fork**:
   - User says "delete all and re-insert" → wipe rows for that date, insert fresh from new report + re-add orphans if user confirmed.
   - User says "just add the missing ones" → append only new params, leave orphans untouched.
   - If user doesn't respond: **prefer appending new params + keeping orphans** (less destructive). Tell the user what you found and what you did.
6. **Verify**: re-read the last rows of Lab Values tab to confirm new params landed, and that row count makes sense (old count + new count - deleted count).
7. **Ruhaan/Roshni specific**: in Healthy 2026 packages, derived ratios (TC/HDL, LDL/HDL, ApoB/ApoA1, SGOT/SGPT, A/G) are rarely printed on the report — they're already in the sheet from a prior pass. Don't flag them as "orphans" unless the user asks. Focus on raw measured parameters.

**Payment receipts (family tests):** file in **NDR Medical > Invoices** even when the receipt covers several members (payer = NDR; his mobile is on the receipt). Name `YYYYMMDD_{Initials}_Thyrocare_Receipt_{ReceiptNo}_{Members}_{Amount}.pdf`, index as TYPE=INVOICE, put receipt no / txn id / covered members in the Drive `description` field.

**Pitfalls:**
- **Adding a Lab Values tab:** `batchUpdate` with `sheetId: None` fails with `No sheet with id: 0` on spreadsheets whose first sheet's id isn't 0 (verified on Ruhaan's index — new tab id was 123181047). After `addSheet`, GET the spreadsheet, read the new tab's real `sheetId`, then apply freeze-row-1 + bold header using that id.
- **Duplicate index sheets** exist for KDR and RNR. Canonical = the one living inside that member's Medical folder (check via `drive.files().get(fileId, fields='parents')`); the duplicates (with Bills tabs) are stale.
- Report `webViewLink` arrives with `?usp=drivesdk` — strip it before storing in the index.

Full sheet/folder IDs, header format, and index TYPE values: `references/family-lab-values-tracking.md`.

## 11. Related Skills

- **`ocr-and-documents`** — text extraction from PDFs (the first stage of this pipeline)
- **`google-workspace`** — Drive uploads, Calendar events via raw API
- **`messaging-links`** — WhatsApp link generation for the patient summary
- **`personal-document-organization`** — local filesystem filing of personal financial/tax docs (complementary: that skill covers local filing, this skill covers Drive filing of medical docs)

## Reference Files

- `references/family-medical-drive-and-docs.md` — the four family Medical Drive folder IDs + Roshini-already-editor status, and the `/data/hermes/projects/medical/` analysis-doc home (master `Medical-Analysis-Enhanced-2026-08.md` etc.). Check this before creating any new family trend/diagnosis document.
- `references/discharge-summary-extraction-template.md` — template for extracting fields from Indian discharge summaries, with worked example and medication reference table
- `references/ndr-lab-value-tracking.md` — NDR's lab-report tracking setup: folder/sheet IDs, canonical TEST NAME vocabulary for the Lab Values tab, worked example (16 Aug 2026 Healthy 2026 package), trend-grouping pitfalls, append code pattern
- `references/family-contact-enrichment.md` — full worked example of enriching a label-only family contact (e.g. "Mom") to a proper named contact with email + nickname, including People API calls, pitfalls, and downstream usage
- `references/health-insurance-policy-analysis.md` — workflow for analyzing a health insurance policy PDF: extracting key fields, researching claim procedures (including OpenRouter fallback when web tools unavailable), and compiling a structured Google Doc reference file. Use this when the user asks about an insurance policy's contact info, claim process, or dispute procedures.
- `references/family-lab-values-tracking.md` — the family-wide Lab Values tracking system: per-member spreadsheet IDs, canonical TEST NAME + CATEGORY mapping, index-append and lab-append script patterns, Lab Values tab creation (with the sheetId pitfall), and RLS/Thyrocare extraction notes. Use this for every lab report filed since Aug 2026.
- `references/prescription-lookup.md` — "find the `<medicine>` prescription for `<family member>`" lookup ladder (session → local analysis docs → Drive fullText misses scanned PDFs → walk member's Medical folder → OCR-verify), Ruhaan Azithromycin worked example (Dr Bharath Reddy, Shishuka Children's Specialty Hospital, AZEE = Azithromycin), and common brand→drug mappings.
