# Notes/Comments API Gap — Attachments in Notes Are NOT Exposed (Aug 2026)

## The limitation

The MCP `list_lead_notes` / `list_lead_events` tools return only the note
**title / first line** — NOT the full note body, and NOT any files
attached to the note. Server-side API limitation (escalated to the Kelsa
developer as an enhancement request), not a client bug.

Also: the bearer OAuth token works ONLY for the MCP endpoint
(`https://kelsa.io/mcp`). The web REST API (`kelsa.io/api/...`,
`app.kelsa.io`) requires a browser session login and returns 302 →
`/users/sign_in` for bearer-token calls. There is no REST fallback.

## Workflow when the user says "the InfoMemo / document is attached to the latest comment on the record"

1. `list_lead_notes(lead_id)` will show only titles like "Property
   Details" — the attachment is invisible through the API. Raw
   `model_dump()` confirms `structuredContent: null`; there is no
   hidden payload to extract.
2. Check the record's own attachment **fields** first
   (`cf_land_sketch`, `cf_land_pics`, `cf_revenue_maps_and_documents`,
   `cf_land_legal_set`) — the file may already be attached there and
   retrievable via the S3 signed URL in `get_lead` output. Download the
   S3 URLs and OCR/vision them before concluding the file is lost.
3. If the file genuinely lives only inside the comment, **ask the user
   to share the file directly** (or the location pin) rather than
   trying to extract it. Explain the API gap briefly so they can
   escalate to Kelsa.
4. The web UI at
   `https://kelsa.io/{pipeline_id}/leads?current_item_id={lead_id}`
   DOES render comments with attachments — a browser session is the
   only way to view them, but automated extraction still can't reach
   the S3 URL without the session cookie.

## Enhancement request (forward to Kelsa)

- `list_lead_notes` (or a new `get_note`) should return **full
  note/comment bodies**, not just the title.
- Notes/comments should expose **attachment metadata + signed download
  URL** (same mechanism as `cf_land_sketch` S3 URLs).
- Optionally a structured attachments list per note so clients can
  enumerate/download without parsing HTML.

## Session trace (LG Champions land record, Aug 2026)

- Record: Pipeline 519, Lead 48679748 (Chikkaballapur LG Land 80A,
  attached to LG Champions Layout).
- InfoMemo PDF (sketch + survey numbers/ownership/extent) was attached
  to the latest comment. MCP showed only 2 old notes "Property
  Details"; the InfoMemo was unreachable.
- Searched: `search_leads` "LG"/"Champions"/"InfoMemo"/"Green County",
  both LG Land records' notes/events/tasks, Companies Master 4475,
  Projects Master 4476, Project Location Master 4686, REST API probes
  (all 302). Only the record attachment fields held images (land
  sketch + street-view pic), not the InfoMemo.
- Resolution: prepared an HTML file + WhatsApp link for the user to
  forward to the Kelsa developer (Ashwin) requesting the enhancement.
