# Repurposing a Prior Email Chain to a New Recipient (same briefing + same attachments)

Class of task: "we sent this chain to advocate X — now send the same content/briefing/attachments to advocate Y" (common for estate/succession matters with multiple counsel, regulatory follow-ups, vendor re-engagements).

Session-validated Aug 2026: succession-certificate matter briefed to Rahul → Advocate Malliah (Aug 2026 thread) → repurposed for Sanjay Sethia. The draft petition docx lived on the Malliah email; death certificate, family tree, and 4 Aadhaar cards lived on the *earlier* Hitesh Solanki thread (2025). Both threads had to be mined.

## Workflow

1. **Find the chain(s) with subject-keyword Gmail search** — run several queries, dedupe by message id:
   - `subject:("succession certificate" OR "succession")`
   - `"<topic>" in:anywhere`
   - `from:<prev-advocate> OR to:<prev-advocate>` (catches the advocate's name even when subject varies)
   - Note the THREAD ids — one matter often spans multiple threads (main thread + earlier thread with different counsel).

2. **Read every message body in each thread** (`format='full'`) and extract:
   - the briefing facts (assets, deed dates, family structure)
   - the numbered asks made to previous counsel
   - the user's explicit constraints — e.g. *"Family Settlement Deed to be filed only as an annexure; details NOT disclosed in the petition body"* — these must be carried verbatim into the new draft.
   - the last counsel's response (fee quotes, blockers) as context; do NOT include unless the user asks.

3. **Collect attachments across ALL messages, not just the latest**:
   - Scan each message payload recursively for parts with `filename` + `body.attachmentId`.
   - Download via `messages().attachments().get(userId='me', messageId=<id>, id=<attachmentId>)`, base64-decode, save to a staging dir (`/tmp/<recipient>_attachments/`).
   - Attachments for "the same attachments as before" are frequently spread across different threads/dates — never assume they're all on the most recent message.

4. **Build the new draft with raw Gmail API** (the gws bridge `draft_create` does NOT support attachments):
   - `MIMEMultipart('mixed')` + `MIMEText(body, 'plain', 'utf-8')` + one `MIMEBase` part per file (`set_payload` → `encoders.encode_base64` → `Content-Disposition: attachment; filename="<fn>"`).
   - Sanitise filenames for the attachment header (spaces/parens are OK; avoid quotes).
   - `service.users().drafts().create(userId='me', body={'message': {'raw': <urlsafe-b64>}})`.

5. **Verify authoritatively**:
   - `drafts().list()` — draft resource present (the reliable "is it a draft" check).
   - `drafts().get(id=...)` — confirm To, Subject, and attachment count (`payload.parts` with `attachmentId`).

## Notes

- Match the user's own prior emails' tone: `Dear Sir / Dear Mr. <Surname>,` → Background → numbered asks → `Warm regards, Nishant Ranka`. Plain text is fine and mirrors the existing chain.
- If the user withheld a private document from previous counsel until engagement (e.g. FSA deed), DO NOT attach it to the new draft either — mirror prior practice and say so in the report.
- Default account `ndr@draas.com` unless the original chain lives elsewhere (older chains may be from `ndr@drahomes.in` — new drafts still go to the work account per user rule).
- The new draft is a NEW thread (no `threadId`, no In-Reply-To) unless the user explicitly asks to keep threading.
