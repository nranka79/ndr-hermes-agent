# GWS Automation (Docs / Gmail / Contacts / Sheets) — for NDR

All Google access goes through `tools.gws_auth.build_service(api, version, service_name=...)` with the session user's vault token. Never build credentials inline. Resolve accounts with `gws_resolve_account` before guessing a service_name.

## Quick reference
- Python runner: `/opt/hermes/.venv/bin/python3` (execute_code strips env vars → run via terminal for anything needing creds)
- Contacts sheet: `1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g`, tab `NDR DRAAS Google contacts.csv` — email value = col S (19), notes = col O (15)
- Email sending = DRAFT only (drafts().create with base64 MIME); threading needs In-Reply-To + References + threadId

## Google Docs — edits marked in blue (NDR's convention)
NDR wants contract/offer-letter modifications made **in the same online document, with changed text in blue** (foregroundColor RGB 17,85,204 via updateTextStyle). Do NOT create a new version.

Core pattern per edit:
1. `deleteContentRange` (old text) + `insertText` (new text) + `updateTextStyle` (blue) in ONE batchUpdate.
2. **PITFALL — `insertText` with empty text is invalid** ("must specify text to insert"). Pure deletion = `deleteContentRange` alone.
3. **PITFALL — concurrent editing drifts indices.** If a collaborator has writer access (e.g. Roshni on employment docs), sequential read→edit→re-read loops corrupt the doc (duplicated chars `Employee'ss`, `ora` for "or a", merged paragraphs, stray punctuation). Detection: re-read after edits and compare — these artifacts are the signature.
4. **The fix that works:** read the document ONCE, build a char→doc-index map from element `startIndex` + run offsets, compute ALL ranges from that one snapshot, then apply everything as ONE atomic batchUpdate ordered END→START. Verify with a fresh read afterward. (Repair runs use the same technique.)
5. Verify: re-read and probe for expected substrings; confirm blue chars present via textStyle.foregroundColor.

## Gmail — threads & attachments
- Search angles: transcription may mangle names ("Avni" ≠ "Anvi Consultancy" <anvi.cy@gmail.com>). Search multiple angles: subject terms (MOU), generic ('consultancy'), AND quoted variants. Match by CC'd email to confirm identity.
- **PITFALL — `format='full'` does NOT include attachment bytes.** Attachments come back as parts with `body.attachmentId` only. Fetch each with `users().messages().attachments().get(messageId=..., id=attachmentId)` then base64-decode.
- Extract .docx text via zipfile: read `word/document.xml`, regex `<w:p[ >]...?</w:p>`, join `<w:t>` contents.
- Email+attachment review pattern (e.g. MOU claims vs attachment text): list what the email *claims*, then verify each claim against the attachment's actual clauses — flag contradictions between email body and signed document (fee payable "on disbursement" vs "at sanction letter" is the classic).

## Google Contacts (People API) + contacts sheet
- **PITFALL — People API rate limits:** ~90 critical reads/min/user. connections().list and searchContacts both count; a 429 means wait 30–60s, not retry instantly. Keep reads batched.
- Search by phone: format matters — `"98450 71706"` (with space) hits, `"9845071706"` (no space) can miss. Search several variants.
- **PITFALL — updateContact requires the etag** (optimistic concurrency): GET the person first, copy `etag`, send the full updated person + `updatePersonFields` mask.
- Name cleanup: contacts often carry company words in the display name ("Dayakar Reddy Broker") — normalize to givenName/familyName when the user asks.
- ALWAYS mirror changes to BOTH Google Contacts AND the contacts sheet (NDR keeps both). Sheet row = spreadsheet row number; update cells with values().batchUpdate.
- Identity confirmation trick: an email CC'd on a thread IS the person — use it to disambiguate same-name contacts (e.g. Chrysler "Diwakar Reddy" is a DIFFERENT person from "Dayakar H").

## Pitfalls (cross-cutting)
- Verify every write by re-reading (GET after batchUpdate/values().batchUpdate) — never trust the update response alone.
- NDR's contacts sheet is the CRM of record for contacts; memory should hold only the compact cross-reference, not full contact dossiers (memory is 2,200-char capped).
