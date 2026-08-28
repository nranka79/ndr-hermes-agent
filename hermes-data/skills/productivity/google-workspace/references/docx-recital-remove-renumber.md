# Removing a recital and renumbering the rest in a .docx sale deed on Drive

Companion to `docx-recital-edit-with-yellow-highlight.md` (that one ADDS a
recital; this one REMOVES one or more and renumbers the survivors). Same DRA
Group title-chain pattern (Bharat / NDR, Ranka Oasis absolute sale deed).

Use case: the user says "recitals (viii) and (ix) are unnecessary documents,
remove the data" — the SPA (Doc.2178/2024) and Other's Deed (Doc.7963/2025)
must drop out and every later recital shifts down (x→viii, xi→ix, xii→x).

## Workflow

1. Download the .docx from Drive via `build_service('drive','v3',service_name='google-draas')`
   → `files().get_media(fileId=...)`, write to /tmp. Drive `files().export(...)`
   to text fails with 403 "Export only supports Docs Editors files" on .docx —
   use `get_media`, not `export`.
2. Enumerate the recital paragraphs by text. Recitals live in a numbered list
   near the top of the title-flow section; the operative covenants have their
   OWN internal (viii)/(ix)/(x) numbering further down — do NOT touch those.
   Identify the title-flow recital block by reading surrounding context
   (they reference On-going vendors/deeds and "same property covered under
   Recital (N) above").
3. **Edit via zipfile + lxml on `word/document.xml`, NOT python-docx.**
   python-docx paragraph run rewrites (empty all runs, set text on run[0])
   frequently DO NOT persist for this operation — the saved file comes back
   byte-identical and the document looks unchanged. The reliable method:
   - read `document.xml` from the zip
   - `etree.fromstring`, find `body`, `body.findall('w:p', ns)`
   - locate the recital `<w:p>` by concatenating `w:t` text
   - `body.remove(p)` to delete (the python-docx index shifts after each
     removal — collect all target elements first, then remove, or re-enumerate)
   - renumber survivors by editing the `w:t` run that holds the `(x)` prefix
     (map `x→viii`, `xi→ix`, `xii→x`)
   - write `document.xml` back into a fresh copy of the zip (`zipfile.ZipFile(...,'w')`
     writing all other entries byte-for-byte)
4. **Fix stale hardcoded cross-references.** After renumbering, grep the body
   for `Recital (N)` mentions that pointed at a now-shifted recital — e.g. a GPA
   recital's closing "the same property covered under Recital (xi) above" must
   become "Recital (ix) above" when xi→ix. Miss this and the deed self-contradicts.
5. Re-upload in place with `service.files().update(fileId=..., media_body=...)`
   to preserve the Drive link. Verify by re-reading the renumber paragraph.

## Pitfalls
- python-docx in-place rewrites don't persist for recital add/remove — go
  straight to lxml on `document.xml` (python-docx is fine for BUILDING docx
  from scratch, not for surgically editing an existing one).
- Two (or more) independent (viii)/(ix)/(x) numbering sequences in one deed
  (title recitals vs. operative covenant clauses) — scope edits to the right
  block or you'll corrupt the covenants.
- Renumbering leaves behind stale `Recital (N)` cross-reference text — always
  grep and fix before re-upload.
- `files().export` 403s on .docx — use `get_media`.