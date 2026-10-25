# Sharing a Drive file with a colleague (role + notification conventions)

Verified 2026-10-13 (Bharat: *"share the signed deed … with Sarthak, that is
admin3.blr at the rate trust.com, so you don't have to take approval and I'll
tell him"*).

## 1. List the file's permissions FIRST, then match the org's existing role

Before granting anything, read who is already on the file:

```
gws_drive_permissions_list(file_id=..., service_name="google-draas")
```

Then **match the role the organisation already uses on that file** rather than
defaulting to reader. On the BHC lease deed every internal DRA collaborator
(admin2.blr, echamundeshwari, ndr@drahomes.in, sbari) was already a **`writer`**,
so the new colleague was granted `writer` too — consistent with the file's own
convention.

**Always state the role you granted, and offer the downgrade.** The reply named
the role, said it matched the other colleagues, and ended with *"say the word if
you'd rather it be view-only — I'll downgrade it in one step."* That keeps an
over-grant cheap to reverse.

## 2. Resolve the colleague's address from mail, not from dictation

Dictated addresses garble ("admin3.blr **at the rate trust.com**" →
`admin3.blr@draas.com`). Confirm with a one-shot mailbox search of the local
part — `gws_gmail_search(query="admin3.blr")` returned the person's real
signature (`Sarthak Sharma <admin3.blr@draas.com>`) and their role in the org.

## 3. "I'll tell him myself" means: do NOT send a notification email

When the requester says they'll inform the colleague, just add the permission.
Don't email, don't draft. Say plainly that no notification was sent.

## 4. A folder you don't own cannot be shared — flag it, don't force it

`permissions().list()` on someone else's folder returns
`403 insufficientFilePermissions`, and the *requester* may not own it either
(the creatives folder belonged to Gowri Singh). In that case you cannot add
recipients to the folder for them. Put the **link** in the email body and tell
the requester the caveat, offering the fallback: copy the assets into a folder
they own and share that instead.

## 5. Verify after granting

The `permissions().create()` response carries the granted `role` and
`emailAddress` — read it back and quote it in the confirmation rather than
assuming the share landed.
