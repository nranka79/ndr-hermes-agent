# Medical Report Readouts (NDR/family) — Drive → PDF → image → deep-reasoning Gemini

Class of task: NDR asks for a clinical readout of his or family members' medical
reports (ECG, labs, scans, consultation PDFs) stored on the google-draas Drive.
Example from session: "find ECG in NDR medical folder, take the latest, give me
a readout via Gemini through OpenRouter."

## Hard rules (NDR's medical preferences)
- **Deep-reasoning models ONLY. NEVER Gemini Flash** for medical analysis.
  Even though `google/gemini-3.5-flash` exists on OpenRouter, it is banned for
  medical readouts (user profile rule).
- Confirm WHICH report + its date BEFORE delivering the readout. User asks
  "tell me which ECG, which date — take the latest one."
- Family medical context: KDR = PH (PASP 54), on Keytruda + Axitinib
  (cardiac/arrhythmia risk).

## Workflow (verified in session)
1. Locate folder — Drive search for `Medical` folders: NDR Medical, KDR Medical,
   RNR Medical, Ruhaan Medical, Rivaan Medical. NDR Medical folder id:
   `0B1Oc8cSaJXPGT1JPMVlfajFnTmc`. List contents recursively 2 levels to catch
   scans whose filename doesn't contain "ecg".
2. Find report — query `name contains 'ecg' or name contains 'ekg' or name
   contains 'electro'` (case-insensitive). Naming pattern:
   `YYYYMMDD <NAME> R ECG <Hospital>.pdf` e.g. `20240716 NDR R ECG Nura.pdf`.
3. Pick latest by date in FILENAME / printed on report, NOT modifiedTime —
   a batch re-upload set every mod time to 2026-01-16, so mod time is useless.
4. Download via `svc.files().get_media(fileId=...)`.
5. Render PDF → PNG with PyMuPDF (`fitz`): `page.get_pixmap(dpi=200)`.
   CAUTION: A4 landscape @200dpi = ~9745×6889 px — downscale before any model
   call (PIL, ~1000–1300px wide, JPEG q72–80).
6. Verify date ON the report via `vision_analyze` (free OCR) — patient name,
   study date/time, machine measurements. OCR of ECG waveform pages gives
   garbled lead labels (expected); the measurement page OCRs cleanly.
7. Route the ACTUAL IMAGE to the model — see next section. `call_openrouter_model`
   is TEXT-ONLY: prompt_tokens stays ~600, image_tokens 0, model never sees the
   image. The working path is a direct OpenRouter REST call.
8. Deliver: report identity + date first, then structured readout (rhythm/rate,
   axis, intervals, Q-waves, ST-T, hypertrophy, overall, machine-label check).

## OpenRouter vision routing (the key technique)
`call_openrouter_model` sends `messages[0].content` as a plain STRING
(/opt/hermes/tools/openrouter_tool.py) — markdown data-URL images are not
parsed into image parts. To get vision:
- Build content array: `[{"type":"text","text":...}, {"type":"image_url",
  "image_url":{"url":"data:image/jpeg;base64,<b64>"}}]`
- POST to `https://openrouter.ai/api/v1/chat/completions` with
  `Authorization: Bearer <key>`, model e.g. `google/gemini-3.1-pro-preview`.
- Verified: prompt_tokens jumped 591 → 1659 and the model referenced the
  waveform directly when the image part was included.

## Model availability (checked 2026-08)
- `google/gemini-3.5-pro` does NOT exist on OpenRouter (HTTP 400/404).
- Newest Pro: `google/gemini-3.1-pro-preview`. Also available: 3.5-flash,
  3.5-flash-lite, 2.5-pro, 3-pro-image.
- Check list: `GET https://openrouter.ai/api/v1/models`.

## OpenRouter API key discovery + storage
- NOT in execute_code/terminal env; NOT in /opt/hermes/.env (doesn't exist).
- Lives in the gateway process env: `tr '\0' '\n' < /proc/<pid>/environ |
  grep ^OPENROUTER_API_KEY=` (find pid: `pgrep -f python|gateway`).
- Sanctioned storage: `/data/hermes/.env` (confirm via `hermes config env-path`;
  this deployment's env file is /data/hermes/.env, NOT /opt/hermes/.env).
  Append `OPENROUTER_API_KEY=...`, chmod 600, backup first.
- After storing a NEW key, the RUNNING gateway keeps the OLD key in memory
  until restart — `call_openrouter_model` reads os.environ at call time.
- Validate key: `GET https://openrouter.ai/api/v1/key` with Bearer header →
  usage/limit/free-tier status (free-tier=false + limit null = pay-as-you-go).
- Hygiene: write extracted key to 600-perm temp file, use, DELETE after.
  Never print keys; mask as `sk-or-v1-368...de9`.

## Dead ends (don't repeat)
- `GOOGLE_AI_STUDIO_API_KEY` unusable for vision here: free-tier
  generateContent quota = 0 (429) and project denied (403).
- `vision_analyze` default (gemini-2.0-flash) is fine for OCR/date extraction
  but NOT for the clinical readout (Flash banned + user asked for Pro).
