# Editing Existing MOU / Legal Documents in Google Docs

When a user asks you to add, modify, or remove clauses from an existing MOU
or legal document that lives in Google Docs, use this workflow.

> **Party restructure / title-flow recitals:** For removing or reassigning
> parties, single-party consolidation, Schedule re-mapping, or folding a
> scanned legal-opinion title chain into recitals + condition precedents, see
> `references/mou-party-restructure-title-flow-recitals.md` (validated on the
> Doddasane Dev-Cum-Sale MOU, Jul 2026).

## Workflow

### 1. Read the document and map its structure

Use `terminal()` + `gws_auth.build_service` (not `execute_code` — the sandbox
strips vault env vars).

```python
import sys
sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service

service = build_service("docs", "v1", service_name="google-draas")
doc = service.documents().get(documentId="DOCUMENT_ID").execute()
content = doc.get("body", {}).get("content", [])

# Print each paragraph with its startIndex and endIndex
for elem in content:
    para = elem.get("paragraph")
    if para:
        text = "".join([
            e.get("textRun", {}).get("content", "")
            for e in para.get("elements", [])
            if e.get("textRun")
        ])
        if text.strip():
            print(f"[{elem['startIndex']}-{elem['endIndex']}] {text[:200]}")
```

This gives you the exact character indices of every heading and clause — the
map you need to compute insertion points.

### 2. Find insertion points

Look for the **last element before your target section** and the **first
element of the next section**. Insert your new clause text at the exact
`startIndex` of the next section's heading.

Example: to insert a new Clause 4.2 between Clause 4 and Clause 5, find
where `5. ESCROW ACCOUNT` heading starts (e.g., `12338`) and insert there.

### 3. Insert text with batchUpdate

**Critical: when inserting multiple blocks, insert from highest index first
(innermost to outermost).** Each insert shifts all subsequent indices.

```python
# Insert profit clarification AFTER Tier 3 (higher index first)
requests = [{
    "insertText": {
        "location": {"index": TIER_3_END_INDEX},
        "text": "\n\n5.2. [clause text...]\n"
    }
}]
service.documents().batchUpdate(
    documentId=doc_id,
    body={"requests": requests}
).execute()

# Then insert road access clause BEFORE Clause 5 (lower index — unaffected
# by the first insert since it was BEFORE this position)
doc = service.documents().get(documentId=doc_id).execute()
# re-find the Clause 5 heading index
requests2 = [{
    "insertText": {
        "location": {"index": CLAUSE_5_START},
        "text": "\n\n4.2. [clause text...]\n"
    }
}]
service.documents().batchUpdate(
    documentId=doc_id,
    body={"requests": requests2}
).execute()
```

### 4. Verify

Rerun the structure dump and spot-check that:
- The new clause heading appears at the expected position
- The formatting is consistent (same heading style as neighboring clauses)
- No existing content was overwritten or corrupted

## Pitfalls

- **Index shifting**: After the first `insertText`, all indices after the
  insertion point increase by exactly `len(inserted_text)`. Either (a) insert
  from highest index first, or (b) re-fetch the document to recompute indices
  between inserts.

- **Wrong service_name**: Always pass `service_name="google-draas"` (or
  the correct vault key). Plain `build_service("docs", "v1")` defaults to
  `"google"` which doesn't match any vault key. Resolve with
  `gws_resolve_account` or check memory for the user's known service.

- **403 "caller does not have permission" = wrong session identity, not doc
  permissions**: The docs call works only when `HERMES_SESSION_USER_ID`
  matches the real session id (check `echo $HERMES_SESSION_USER_ID`, e.g.
  `ndr-[REDACTED-TID]`). Guessing a slug like `sales1_blr` yields 403 even on
  docs the user owns. The vault's "canonical_uid ... using raw id as fallback"
  warning is informational, not the cause.

- **Stale vault socket path**: If `gws_resolve_account` reports the vault
  socket unreachable, locate the live socket with `find / -name vault.sock`
  (this deployment: `/run/gws-vault/vault.sock` — the env var may point to a
  dead path like `/opt/data/gws-vault/run/vault.sock`). Prefix every command:
  `GWS_VAULT_SOCKET=/run/gws-vault/vault.sock HERMES_SESSION_USER_ID=<real-id>
  python3 ...`. Don't conclude the vault daemon is down.

- **terminal() vs execute_code**: The vault socket env var is stripped in
  `execute_code()` sandboxes. Always use `terminal()` with a Python heredoc
  for Docs API work. See `gws-automation/references/terminal-gws-access-venv-path.md`.

- **Re-fetch between inserts**: After `batchUpdate`, the in-memory `content`
  array is stale. You must `documents().get()` again to get correct indices
  for the next operation. This is mandatory, not optional.

- **Newlines before inserts**: Insert `\n\n` before the clause text to
  ensure proper paragraph breaks between the preceding clause and the new one.

- **Document ownership**: The edited document is owned by the authenticated
  Google account (e.g., `psingh@draas.com` or `ndr@draas.com`). If the user
  can't see changes, share the doc or check which account was used to edit.

- **Vault socket + session identity in terminal()**: When calling
  `build_service` via `terminal()`, set BOTH env vars explicitly or the call
  can fail with misleading errors:
  - `GWS_VAULT_SOCKET` may point at a stale path (e.g.
    `/opt/data/gws-vault/run/vault.sock`). Find the live socket with
    `find / -name vault.sock 2>/dev/null` (commonly `/run/gws-vault/vault.sock`)
    and export it. Otherwise you get `Vault socket unreachable ... No such file
    or directory` from `gws_resolve_account`/`build_service`.
  - `HERMES_SESSION_USER_ID` must be the CURRENT session's id (check
    `echo $HERMES_SESSION_USER_ID`, e.g. `ndr-[REDACTED-TID]`) — a stale id (e.g.
    from another session like `sales1_blr`) fetches the WRONG user's token,
    producing HTTP 403 `The caller does not have permission` on
    `documents().get()`. That 403 is a session-identity problem, NOT a
    missing-auth problem — do not send an OAuth URL. The
    `canonical_uid: vault has no identity mapping ... using raw id as fallback key`
    warning is benign; proceed.
- **Deletions in one batch: highest index first** — for `deleteContentRange`
  lists, sort ranges descending by startIndex so earlier deletions don't shift
  later anchors. Verify each range's boundary text before applying.
