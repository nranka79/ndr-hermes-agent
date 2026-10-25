# Drive project-alias search + date-prefix renaming of EXISTING files

Verified 2026-09-18, "find everything for Ranka North Star / Allal Sandra".

## 1. The alias problem — one project, many spellings

NDR names a project one way; the Drive has been written to by many people over many years.
For Ranka North Star alone the same project appears as:

- `Ranka North Star`
- `Ranka NorthStar`
- `Northstar`
- `North Star`
- `NORTH STAR`
- `NorthStar`

…plus the **location** alias: he says *"Alal Sandra"* / *"Alala Sundara"* — the village is
**Allalasandra** (also spelled Allalsandra, Allalasandra). Voice renders it variously.

**Rule: never search a single literal string.** Normalise and match:

```python
def norm(s):
    return re.sub(r'[^a-z0-9]', '', s.lower())      # "North Star" == "Northstar" == "north-star"

keys = [norm(k) for k in ("north star", "northstar", "allalasandra", "allalsandra")]
hits = [f for f in all_files if any(k in norm(f['name']) for k in keys)]
```

A search for `"north star"` with a space misses every `Northstar` folder and file, and vice
versa — and the renders are routinely split across those two spellings. Also expect the
project name to be **absent** from some folders (they sit under the location name instead).

## 2. Report shape NDR expects

Group by artifact type, not by folder — he asked for "the entire set of files and folders
with links to each", specifically hunting **images and renders (including renders delivered
as PDF)**:

- Folders (with link)
- Images / renders (JPEG/PNG)
- Render / elevation PDFs
- Presentations (pptx / Slides)
- DWG files
- Key documents (legal, financial)

Give each item its `webViewLink`. **Flag duplicates**: several copies of the same render set
appeared across folders; confirm byte-identity with a checksum before calling them duplicates,
then say so (e.g. "all three are byte-identical — same MD5").

## 3. Date-prefix renaming of EXISTING files (NDR's convention)

NDR's convention is `YYYYMMDD_OriginalName.ext` (see `google-doc-formatting-template` for the
same rule applied to newly-created artifacts). For files that already exist:

1. **Find the earliest real date.** Preference order: the Drive `createdTime`, then the
   earliest `modifiedTime`, then **a date printed inside the document itself** (scan/OCR the
   first page — a sanction drawing or brochure usually carries one).
2. **Rename in place** with `drive.files().update(fileId=..., body={'name': new_name})` — the
   fileId and share links are preserved. Never re-upload to rename.
3. **Do NOT rename a file that already carries a meaningful date or version in its name.**
   `WD_24M_DRA_NORTHSTAR_FINAL_MM_07-05-2026.dwg` already communicates its version — leave it
   and tell NDR you left it deliberately.
4. **Tell NDR which date you used and why** ("created 2015-11-13" / "date on the drawing").
   He asked for exactly this: *"If you can get the date applying my format, please rename them
   appropriately."*

## 4. Binary CAD files cannot be read visually

`.dwg` is binary — no vision pass, no OCR. Date the rename from file metadata, and say plainly
that the contents could not be inspected rather than implying you reviewed the drawing.
