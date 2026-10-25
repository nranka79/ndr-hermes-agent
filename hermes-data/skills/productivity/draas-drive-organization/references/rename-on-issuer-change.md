# Renaming documents when the ISSUER changes (NDR, 2026-09-18)

A document's filename often encodes **who issued it**. When the underlying fact changes
(property sold, lessor replaced, firm renamed), the filename becomes a lie — and NDR treats a
stale issuer name as an error worth interrupting a session to fix. Fix filenames whenever the
issuer changes, in the same turn you learn about the change.

## NDR's instruction, verbatim

> *"Can you please ensure that you rename those documents because it's no longer Prizm
> Developers, it's just Feroz Ahmed or whatever, right? He is giving the NOC. So can you please
> rename the documents appropriately? … So can you please rename them appropriately to reflect
> **my naming convention** along with the fact that it's **Feroz Ahmed giving the NOC to these
> entities**."*

Two rules extracted:

1. **The issuer in the filename must be the CURRENT issuer.** `Prizm_Developers_NOC_*` was
   correct when A.R. Mohammed Abdullah / Prizm Developers was the owner. Once the premises
   transferred to Feroz Ahmed, the same document is *issued by* Feroz Ahmed — the old name
   asserts something false.
2. **The filename must name BOTH ends of the transaction** — issuer AND recipient.

## Convention applied

```
YYYYMMDD <Issuer> <DocType> - <Recipient>.<ext>
```

Worked example — the two Prizm Greystone NOCs re-issued in the new owner's name:

| Before | After |
|---|---|
| `Prizm_Developers_NOC_R3N_1_KAAJ.docx` | `20260918 Feroz Ahmed NOC - REN KAAJ Development Partners.docx` |
| `Prizm_Developers_NOC_DRA_1_KAAJ.docx` | `20260918 Feroz Ahmed NOC - DRA KAAJ Development Partners.docx` |

- **Date = the document's effective date**, i.e. the date now printed in the document body
  (`18.09.2026` in the docs → `20260918` in the filename). Not the upload/edit date.
- **DocType** stays a short uppercase token: `NOC`, `Sale Deed`, `MOU`, `Deed of Reconstitution`.
- Spaces are fine for these human-facing legal docs — the underscore-only
  `YYYYMMDD_Entity_Description` rule (see `scanned-document-*` / `bulk-file-naming-*` references)
  applies to scanned records and bulk-imported files, **not** to these. Match the sibling files
  already in the destination folder before choosing separators.
- **Voice/transcription variants:** NDR says "REN KAJ" and "DRA KAJ"; the canonical firm names
  are **REN KAAJ Development Partners** and **DRA KAAJ Development Partners**. Always write the
  canonical form into the filename even when his dictation garbles it. Note `Ren-Kaj` /
  `REN KAAJ` = the REN entity, while `"Kaj"` alone in speech often means **DRA KAAJ** — two
  different firms.

## In-place rename — never a re-upload

Renaming via `files().update(fileId=..., body={'name': ...})` preserves the **file ID**,
**revision history**, **comments**, and every **existing link** the team already holds. If you
re-upload a copy with a new name you break all of those and pollute the Drive — which NDR
explicitly polices:

> *"I hope the documents are exactly the same original documents, upgraded version, not multiple
> copies of it because it starts polluting the drive. So can you make sure?"*

**Verify there are no duplicate copies** before reporting the rename done:

```python
r = drive.files().list(q="name contains 'Prizm_Developers_NOC' and trashed=false",
    fields="files(id,name,mimeType,parents,owners(emailAddress))",
    supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
```

Expected result after an in-place rename: exactly the two original files. Report the count
explicitly ("Only the two originals exist — no duplicates") because he asks for it.

## Rename the SHORTCUTS too

Shortcuts are separate Drive items with their own `name`. Renaming the target leaves the
shortcut showing the **stale** name in the folder — which is exactly the "old issuer" problem
NDR is trying to kill. Loop over the shortcuts and rename them in the same pass:

```python
# find shortcuts pointing at the doc
sc = drive.files().list(
    q="mimeType='application/vnd.google-apps.shortcut' and trashed=false",
    fields="files(id,name,shortcutDetails)", supportsAllDrives=True,
    includeItemsFromAllDrives=True).execute()
for f in sc.get('files', []):
    if f.get('shortcutDetails', {}).get('targetId') == DOC_ID:
        drive.files().update(fileId=f['id'], body={'name': NEW_NAME},
                             supportsAllDrives=True).execute()
```

`targetId` is only readable **inside `shortcutDetails`** — passing bare `targetId` in a
`fields` mask raises `HttpError 400 "Invalid field selection targetId"`.

## Checklist

1. Confirm the new issuer from source (the document body / the ownership facts), not from a guess.
2. Confirm the document's effective date for the `YYYYMMDD` prefix.
3. Rename the file **in place** (same ID).
4. Rename **every shortcut** targeting it.
5. Sweep for duplicate copies; assert "originals only".
6. Report the before → after name pair to NDR — he reads the mapping to confirm the convention
   is right.
