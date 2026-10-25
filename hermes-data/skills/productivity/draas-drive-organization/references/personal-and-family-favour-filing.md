# Personal & family-favour documents — where they get filed

Verified 2026-10-16 (Jay Semlani recommendation letter for Chanakya Semlani).

## The routing question, and the answer

Not every DRAAS-letterhead document belongs in a project folder. NDR sometimes asks for a company
document as a **personal favour** — a recommendation letter for a friend's son, a reference for a
relative, a personal undertaking. When he does, the natural instinct is to look for a project
folder (there was none for "Ranka Ankura") or to create one.

**Don't create a project folder for a favour.** NDR's instruction, verbatim:

> *"So this is more a personal favor to family friend Chanakya for his son. So I don't, there's no
> Rangka Ampura, maybe you can leave it in some personal folder, just personal communication
> folder."*

The deciding question is **who the document serves**, not what letterhead it carries. A
recommendation letter uses DRA Realty letterhead and is signed as Director, but it is a personal
communication and gets filed as one.

## The folder that exists

`Personal` — id `0B1Oc8cSaJXPGYkQtYXJDQWVBUVE` — at **My Drive root** on `ndr@draas.com`
(created 2012, 100+ items: Aadhaar/passport scans, wills, family settlement docs, financials,
personal correspondence). This is the correct parent for favours and personal correspondence.

Existing children worth knowing:

| Folder | ID |
|---|---|
| `Personal Communication` (created 2026-10-16 for this filing) | `1O9mfyQDVlStExwfj2XnqaLb1zrj10Sgl` |
| `personal invitation folder` | `1HWAQxiS5hIw_MWvVYKSqRxk5Ky6zsCwA` |
| `Family` | `16NAzSHe0cnYhN1uf43kKlqi_qjNlHVYJ` |
| `Ruhaan` / `Rivaan` / `Ruhan` | `0B1Oc8cSaJXPGbl9VMEZBdE04Z28`, `0B1Oc8cSaJXPGV1p3ZFg2S0xJVUk`, `1MW7FNUVke_9VYpwAn5U-GlHdFcOhofYI` |

**Note:** the TMP-first hard rule has an exception-shaped answer here. TMP is for artifacts whose
destination is not yet named; NDR *named* the destination ("some personal folder / personal
communication folder"), so file straight there rather than staging in TMP and asking again. When
he names a destination, honour it in one pass.

## Naming personal documents

Same `YYYYMMDD_Entity_Description` convention as everything else, but the entity here is the
**subject of the letter plus the signer**, not a project:

```
20261016_NishantRanka_DRA_Recommendation_Letter_JaySemlani_SIGNED.pdf
```

Include `_SIGNED` when the filed copy is the executed one — the unsigned draft and the signed copy
otherwise share a name and become indistinguishable in a folder listing.

## Cleanup that goes with the filing

When filing a signed final, NDR expects the working versions retired in the same pass:

1. Rename the signed PDF, file it, and **verify** (download it back, `sha256` against the local
   original — see `document-comparison/references/verify-pdf-is-signed.md`).
2. Trash the editable Google Doc / `.docx` (`files().update(fileId=..., body={"trashed": True})` —
   recoverable 30 days). Check for a `.docx` companion too; a Google Doc is often the only editable
   copy, but confirm rather than assume.
3. Report the account, the folder **path**, the file name and the sha256 — NDR asks for exactly
   this, and once had to ask because nothing had actually been filed.

## Collaborator identities discovered from permissions

Mirroring permissions off the source document is the reliable way to learn a collaborator's **real
Google address**, since the contact-sheet address often has no Google account at all. In this case
Chanakya Semlani's contact sheet gave `chanakya@semlani.com` (no Google account — Drive refused the
share) while the live identity on the document was `cksemlani@gmail.com`; his son Jay is
`jayksemlani@gmail.com`. Read the permission list, don't guess from contacts.
