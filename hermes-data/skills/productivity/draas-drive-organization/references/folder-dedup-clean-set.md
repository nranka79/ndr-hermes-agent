# Drive Folder Dedup → Clean Set Workflow

Recurring request: "create a new folder with one set of all documents, no duplicate files."
Worked example: Oasis - print (1sG1KlY-higI7vhoafHmyarS_qIWkspEW), 305 PDFs → 291 unique, Aug 2026.

## Steps

1. **Recursive inventory** — walk with `files().list(q=f"'{id}' in parents and trashed=false")`, collect `id, name, mimeType, size, md5Checksum, modifiedTime, parents, shortcutDetails`. `md5Checksum` is available for ALL binary files (PDFs, etc.) — not just some.
2. **Group by md5** to find exact duplicates. Same md5 + same size = byte-identical copy (e.g. `Copy of X.pdf` vs `Copy of Copy of X.pdf`).
3. **Choose canonical per group** with a deterministic score:
   - Penalize `Copy of Copy of` in name
   - Prefer names containing digits (survey/doc numbers = more descriptive)
   - Prefer names with `.pdf` extension and no leading/trailing spaces
   - Tiebreak: shorter name
   - If names disagree on doc type (e.g. "Sale Deed no.1706" vs "Settlement deed No 1706" — same bytes), keep the more standard one; report the drop so the user can rename later.
4. **Create new folder** inside the root via `files().create(body={'name': ..., 'mimeType': 'application/vnd.google-apps.folder', 'parents': [root]})`.
5. **Copy unique files** with `files().copy(fileId=src, body={'name': name, 'parents': [new_folder]})` — copies, never moves; original folder stays intact. 291 copies ≈ 2–4 min; sleep 1s every 20 to stay polite; batch progress print every 50.
6. **Verify**: re-list new folder; assert count == unique count AND zero duplicate md5 groups inside it. Report both numbers.

## Notes

- All files at top level with no subfolders is common for these print-shop folders — walk handles both cases anyway.
- Name-based dedup is NOT enough: same doc can have wildly different filenames (e.g. `EC from 19750101...158/1.pdf` vs `EC from 01011975-03042023.pdf`). md5 is the only safe signal.
- Filenames keep the "Copy of " prefix in the new folder unless the user asks to rename — do not rename during dedup, offer it after.
- Deliver the new folder link in a code block (Telegram breaks plain URLs).
