# GWS: Threaded Draft Creation + Drive Permission Expiry (2026-08-06)

> **Pitfalls discovered same-day (live 400 + silent-OK):**
> 1. `permissions.update` REQUIRES `role` echoed back in the body — passing only
>    `{'expirationTime': ...}` fails with `HttpError 400: "The permission role field is required."`
>    Always send `{'role': p.get('role'), 'expirationTime': expiry}`.
> 2. The update RESPONSE shows `expirationTime: None` even when it succeeded — always
>    re-list permissions (`permissions.list(...)`) to verify the expiry actually set.
> 3. Expiry only works on `type='user'` / `type='group'` permissions, not `anyone` links.

Two proven patterns from a session that needed (a) a polite corporate reminder email
as a threaded Gmail DRAFT and (b) 7-day expiry on a Drive share.

## 1. Threaded Gmail draft via direct API (fallback when skill bridge unavailable)

The `tools.gws_skill_bridge` may be unavailable in the sandbox (e.g. the
google-workspace skill scripts dir is root-owned 700 → `PermissionError` on import).
Draft creation still works via the raw Gmail API and stays 100% compliant with the
email hard rule: **drafts only, NEVER `messages().send()`**.

Steps that worked:

1. **Locate the thread** with a Gmail search query — broaden with OR so you catch
   both the lawyer's two addresses:
   ```python
   svc.users().messages().list(userId='me',
       q='from:krishna@brklaw.in OR to:krishna@brklaw.in OR "brklaw" OR "Pattanshetti"',
       maxResults=10).execute()
   ```
2. **Read the message to reply to** (`format='full'`), walking payload parts for
   `text/plain` body; also fetch `format='metadata'` with
   `metadataHeaders=['Message-ID','References','In-Reply-To']` to build correct
   threading headers. (Krishna B.R. example: replies come from
   `krishna@brklaw.in` via Outlook with a `PN4P287MB...@OUTLOOK.COM` Message-ID,
   while Nishant's outgoing used `krishna_br@pattanshetti.com`.)
3. **Build MIME** with `email.mime.text.MIMEText`; set `To`, `Cc` (keep the same Cc
   as prior mails in the thread), `Subject` (prefixed `Re:`), `In-Reply-To` = the
   replied message's Message-ID, `References` = replied message's References +
   Message-ID, `Date` = `formatdate(localtime=True)`.
4. **Create the draft, threaded:**
   ```python
   raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
   created = svc.users().drafts().create(userId='me',
       body={'message': {'raw': raw, 'threadId': THREAD_ID}}).execute()
   ```
   Returns `draft_id` + `message.id` + `threadId` — report these, never send.

## 2. Drive permission expiry (temporary viewer access)

To give someone **viewer access that auto-expires in N days** (e.g. 7) on a file:

- `permissions.update` **requires the `role` echoed back** — body
  `{'role': existing_role, 'expirationTime': iso8601}`. Passing only
  `expirationTime` → HTTP 400 `"The permission role field is required."`
- **Quirk:** the update *response* may show `expirationTime: None` even though it
  applied. Always verify by re-listing:
  `permissions().list(fileId, fields='permissions(id,emailAddress,role,type,expirationTime)')`
  → confirms `expirationTime: 2026-08-13T12:48:29.000Z` on a `type=user` perm.
- Expiry is only honored for `type=user`/`group` permissions, not `anyone` links.
- Compute expiry in UTC: `(datetime.now(timezone.utc) + timedelta(days=7)).replace(microsecond=0).isoformat().replace('+00:00','Z')`

Both patterns use `tools.gws_auth.build_service('gmail'|'drive', 'v1', service_name=...)`
after `gws_resolve_account`; verify identity with `about().get()` before writes.
