# Medical Report Analysis (ECG readouts, lab PDFs) — NDR/KDR family

Proven workflow for reading/analyzing/comparing/sharing medical reports from the Drive medical folders.
Use when the user asks to read an ECG, compare reports across dates, or share a report with a doctor/contact.

## Hard rules (medical)
- **Never Gemini Flash for medical readouts.** Deep-reasoning Pro only: `google/gemini-3.1-pro-preview` on OpenRouter (`gemini-3.5-pro` does NOT exist there).
- **`call_openrouter_model` tool CANNOT attach images** — prompt is a plain string (image_tokens 0). Vision requires a DIRECT OpenRouter chat/completions call (curl/urllib) with a base64 `data:image/...` URL part.
- **max_tokens ≥ 3000** for reasoning models — Gemini 3.1 Pro burns ~1150 tokens reasoning; at max_tokens 1200 it returns `finish_reason: length` with an empty/truncated readout. Ask for "compact bullet list, minimal reasoning".
- Medical output is private to the user; never send to a third party without direction.

## Locating reports on Drive
- NDR Medical folder on **google-draas** (ndr@draas.com): `0B1Oc8cSaJXPGT1JPMVlfajFnTmc`. KDR Medical: `0B1Oc8cSaJXPGUUtVbTJHb0Y3V2s`.
- Filename convention `YYYYMMDD NDR/KDR R ECG <Hospital>.pdf`; search `name contains 'ECG' and trashed=false`.
- `gws_resolve_account` FIRST — tokens go stale (google-ahfl expired 2026-08). Verify about() owner pre-write.

## Pipeline (proven Aug 2026)
1. Drive API `files().get_media` to download.
2. `pdfinfo` page count → `pdftoppm -png -r 200` render.
3. Compress: PIL thumbnail ~1400px, JPEG q85 → ~300 KB (full-res PNG ~3.4 MB too big).
4. OCR (`vision_analyze`) garbles ECG trace labels — useless for intervals; always use the real vision model for ECG content.
5. Direct OpenRouter call: base64 data URL in content array + structured prompt (rhythm/HR, axis, PR/QRS/QT/QTc, ST/T, hypertrophy/ischemia, machine interpretation, one-line impression). Load key via `load_hermes_dotenv(hermes_home=Path('/data/hermes'), project_env=Path('/opt/hermes/.env'))`.
6. Save full JSON response to file — terminal tail truncates long readouts.

## Comparison + output shape (user preference)
Lead with the answer; per-report bullets → **Key comparison points** → **Bottom line**. State what's normal, what changed, whether alarming (e.g. BER visible only at slower HR is rate-dependent, not new disease).

## Sharing with a third party
- Viewer: Drive `permissions().create(fileId, {type:'user', role:'reader', emailAddress}), sendNotificationEmail=False`, then VERIFY with `permissions().list`.
- WhatsApp: ALWAYS `whatsapp_link` tool (never hand-build wa.me). Individual → include phone (user rule). `platform='telegram'` for MarkdownV2-safe display link.

## Contact lookup fallback chain
1. People API `searchContacts` (partial names OK).
2. NDR DRAAS Google contacts sheet `1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g` (scan all tabs).
3. Gmail `messages().list(q=...)` across draas + gmail accounts.
4. `session_search` past chats / calendar invites — e.g. Sadeq Ali found via 28-Jul-2026 event: mali@accurkardia.com, mali@archimydes.com, +44 7704 135902.

## Pitfalls
- Medical Report Index sheet `1gsIQXoVis0TG3eCZFmg0AVzCPG525doPK0ifTIqz2rg` may 403 for sheets API — fall back to direct folder listing.
- Don't send notification emails when granting permissions unless asked.
