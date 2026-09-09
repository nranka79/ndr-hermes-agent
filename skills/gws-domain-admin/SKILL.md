---
name: gws-domain-admin
version: 0.1.0
description: >-
  Act on ANY user in the Google Workspace domain as the admin (NDR) via
  domain-wide delegation. Use when the admin says things like "check <name>'s
  account", "search <name>'s mail/drive", "read <name>'s inbox", "send mail as
  <name>", "list <name>'s drive files", "transfer ownership of <doc> to
  <name>", "create a doc/drive file for <name>", or asks about a specific
  person's Gmail, Drive, Docs, or Contacts. Resolves the person through the
  gws-vault, obtains credentials via get_gws_credentials, and drives the
  Google APIs through tools/gws_admin.py.
---

# GWS Domain Admin (domain-wide delegation)

You are operating as the Hermes domain admin. Through the gws-vault you can
act on ANY user in the Google Workspace domain using a service-account key
with domain-wide delegation (DWD). Only the admin identity may do this.

## Trigger phrases

When the user (the admin, NDR) says any of these, use this skill:

- "check <name>'s account" / "look at <name>'s mail/drive/contacts"
- "search <name>'s mail" / "what's in <name>'s inbox" / "find emails from X in <name>'s mail"
- "send as <name>" / "email as <name>"
- "list <name>'s drive files" / "transfer ownership of <file> to <name>"
- "create a doc for <name>" / "add a contact for <name>"
- anything referencing acting on another person's Google account

## DWD SAFETY RULES (non-negotiable)

1. **Admin-only.** The vault's `get_gws_credentials` op enforces this
   (fail-closed: session_uid must be `role=="admin"` or
   `permissions.vault_admin`). You must NEVER call it with a non-admin
   session identity, and never pass the DWD key onward.
2. **The key stays in the vault.** The service-account key is fetched by
   `tools/gws_admin.py` into process memory only. NEVER write it to disk,
   NEVER paste it into chat, logs, or tool output. If you ever need to
   display anything about it, mask it (e.g. `…abcd`).
3. **Audited.** Every dwd-mode grant is logged server-side by the vault
   (peer_uid, requester, target). Behave accordingly — every action you take
   as another user is recorded.
4. **User mode vs dwd mode.** When the target is the admin themselves, the
   vault returns "user" mode (their own refresh token, no subject). For
   anyone else it returns "dwd" mode and you impersonate via
   `subject=<target email>`. Never set a subject in user mode.
5. **Never leak.** Never log `token_json` or the SA `private_key`. The
   library masks these automatically; don't undo that.

## Workflow

1. **Resolve the person** (who is it? canonical email?):
   ```bash
   python3 tools/gws_admin.py resolve "<name or email>"
   ```
   If ambiguous, ask the admin to be more specific. The vault is the single
   source of truth for identity; do not guess emails.

2. **Pick the operation** — use `tools/gws_admin.py`'s classes:
   - `GWSDWActor(session_uid=<admin email>)` then `.gmail(t)`, `.drive(t)`,
     `.docs(t)`, `.contacts(t)` for the per-service clients, or
     `.get_credentials(t)` / `.resolve_target(t)` directly.
   - The session identity defaults to `GWS_VAULT_SYSTEM_ADMIN`
     (default `ndr@nishantranka.com`).

3. **Run the API call** for the requested operation:

   | Ask | Call |
   |---|---|
   | search mail | `GmailService.search_messages(q)` |
   | send as <name> | `GmailService.send_message(to, subject, body, cc, bcc, attachments)` |
   | draft | `GmailService.create_draft(...)` |
   | trash a message | `GmailService.delete_message(message_id)` |
   | list labels | `GmailService.list_labels()` |
   | list drive files | `DriveService.list_files(query)` |
   | file metadata | `DriveService.get_file_metadata(file_id)` |
   | create drive file/folder | `DriveService.create_file(name, mime_type, content, folder_id)` |
   | update drive file | `DriveService.update_file(file_id, name, content, mime_type, folder_id)` |
   | delete drive file | `DriveService.delete_file(file_id)` |
   | permissions | `DriveService.list_permissions(file_id)` |
   | transfer ownership | `DriveService.transfer_ownership(file_id, new_owner_email)` (two-step `permissions.update` + `transferOwnership=true`) |
   | create a doc | `DocsService.create_document(title, content_html)` |
   | list contacts | `ContactsService.list_contacts()` |
   | get/update/delete contact | `ContactsService.get_contact`, `update_contact`, `delete_contact` (gdata m8 feeds, NOT the People API) |
   | export contacts | `ContactsService.export_contacts("vcard3")` |

4. **Report back** concisely: who was acted on, what mode was used
   (user vs dwd), and the outcome. Never include credential material.

## Example (send as another user)

```python
from tools.gws_admin import GWSDWActor
actor = GWSDWActor(session_uid="ndr@nishantranka.com")
gmail = actor.gmail("alice@nishantranka.com")   # or a name: actor.gmail("alice")
result = gmail.send_message(
    to="vendor@example.com", subject="Re: invoice",
    body="Hi, please see attached.", attachments=[{"filename": "inv.pdf", "data": "…base64…", "mime_type": "application/pdf"}],
)
```

The vault returns `needs_auth` if the person has no personal token yet —
report that they need to authorize once via the normal OAuth flow.

## Troubleshooting

- "Ambiguous target" → more than one identity matches; use a full email or a
  more specific name.
- "DWD credential not provisioned" → the `google-dwd` key is not uploaded;
  upload it on the admin panel at `admin.ahfl.in/vault/dwd`.
- "Unauthorized: admin only" → the session identity is not a vault admin; do
  not attempt to bypass this.