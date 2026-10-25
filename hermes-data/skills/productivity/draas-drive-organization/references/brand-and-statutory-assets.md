# DRA Brand & Statutory Assets — Locations (verified 2026-10-09)

Where to find frequently-requested DRA Group brand/statutory files so future
sessions don't re-hunt Drive. Verify with `gws_resolve_account` first; Bharat's
session = `service_name='google-draas'`.

## DRA logo — TAGLINE DISAMBIGUATION (critical)

There are multiple "DRA logo" files in Drive with DIFFERENT taglines. When the
user says "the DRA logo", always confirm WHICH tagline before attaching:

| File | Tagline | Use |
|---|---|---|
| `/data/hermes/cache/analysis/dra_logo/dra-logo.png` (transparent RGBA, 800x544) | **HOME OF PRIDE** (gold/black) | Official DRA Realty letterhead logo — DEFAULT answer to "DRA logo" |
| `/data/hermes/cache/analysis/dra_logo/dra-logo.svg` (4918 B) | none (mark only) | vector source |
| Drive `DRA LOGO.pdf` (0BxYJXvUewWijTWgzYVJKMjVISExjM2RZMUdDVGxLMm43RGRV) | **EXPERIENCE NICE** | older brand variant — NOT the letterhead logo |
| Drive `DRA-logo.jpg` (1wS7T7CkjiC5gekVQeQmvwUkAkXhVksMZ) | "BY DRA" | old/different variant — NOT the letterhead logo |
| Drive `DRA logo.svg` (1myxLGQUwfXmZgbwOq0TmuHPZUwe4OH6E) | mark only | My Drive root |

The HOME OF PRIDE PNG was originally pulled from a user-uploaded image
(June 2026 session) and embedded into every DRA Realty letterhead — it is the
one used on official docs. **Verify any candidate with vision_analyze before
sending** (`question: does it contain the HOME OF PRIDE tagline?`).

## DRA Thindlu GST certificate

- GSTIN: **29AAXFD2296G1ZS** — legal name **DRA THINDLU LAND PARTNERS**, Form
  GST REG-06, Queens Corner, 3rd Floor 302A, Queens Road, Bengaluru 560001
  (Partnership).
- Canonical file: `DRA THINDLU GST CERTIFICATE (1).pdf`
  (Drive id 1UQkKtCni05Rqvq93ZnT-dCHjq1ldvKW5, owner ndr@draas.com,
  modified 2026-10-07; copies also in the shared team folder
  `1_54EM5JuJzp3GZKNAXI7MsULx2jtvzX7`, e.g. 1jZcqo_cSigyEk9UjBYAZNIc0LWSWEdKh).
- Related: DRA REALTY PRIVATE LIMITED is a SEPARATE GST entity (GSTIN
  29AALCD9962L1ZW per letterhead) — pick the certificate matching the entity
  the vendor is invoicing (land partners entity for Ranka Udaya plot bookings).
- Bank (booking payments, Ranka Udaya): "Dra Thindlu Land Partners" — Kotak
  Mahindra, IFSC KKBK0008059, Infantry Road, Current A/c 0051732561.

## Sibling entities — GST certs seen in Drive

DRA REALTY PVT LTD, Ranka Holdings, Sevaganapalli Land Partners,
Ranka Amber Realty — all have certs under `name contains 'GST'` searches;
verify entity name + GSTIN before attaching.

## Workflow tips

- Drive search: `fullText contains '<phrase>'` indexes PDF/image OCR — handy to
  find which asset actually contains a tagline ("Home of Pride" surfaced
  Flex.png etc.). But image OCR is unreliable for picking THE logo — rely on
  the local cache + vision check.
- Download binary Drive files (PDF/PNG) via
  `build_service('drive','v3', service_name=...)` +
  `files().get_media()` + `MediaIoBaseDownload` (no native tool for binaries).
- Voice-dictated project/venue names should be cross-checked against Drive
  folder names — this session "Sukruti" (dictated) was actually the
  "Sukriti Cultural Association (SCA), opp. TISB" folder in Bharat's My Drive.
- `pdftotext` on the GST cert gives GSTIN/legal name — quick verification
  before attaching to an email.