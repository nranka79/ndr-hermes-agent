# Blue-marked docx edits — "make the correction in blue, same link, run it by the advocate again"

NDR workflow for correcting a legal petition/docx that advocates sent:
*"make the correction in the petition, make the correction in blue so I
know exactly what is corrected, and I'll use the same link"* (worked
example: Dinesh Ranka P&SC succession petition, 2026-08-31).

## When to use
User wants edits to an existing .docx (from email attachment or Drive)
marked so **every change is visually obvious** (blue = added/changed text),
then wants the SAME Drive link to keep working (no new file, no copy).

## Workflow

1. **Get the latest .docx** — either the Drive file (download via
   `files().get_media`) or the original email attachment
   (`messages().attachments().get` → base64.urlsafe_b64decode). Check Drive
   ownership — if the doc lives in ndr's drive, edit THAT copy.
2. **Edit with python-docx** (terminal, `/opt/hermes/.venv/bin/python3`,
   `HERMES_SESSION_USER_ID=ndr`):
   - For each change, locate the run(s) in the paragraph that need editing.
   - **Change the run text AND set `run.font.color.rgb = RGBColor(0x00,0x00,0xFF)`**
     so the changed text renders blue.
   - For blank placeholders ("Date: ___", "GPA dated ______"), fill the
     value into the same paragraph — add a new run with blue text or put
     blue text right after the label, matching the doc's existing format.
   - Keep unchanged text untouched (black) so the diff is obvious at a glance.
3. **Verify runs are actually blue** before uploading — re-open with
   python-docx and assert `run.font.color.rgb == RGBColor(0x00,0x00,0xFF)`
   on every intended change (this catches pale/gray defaults: LibreOffice
   writes `auto` color which python-docx may not flag as blue).
4. **Upload back to the SAME Drive file id** —
   `MediaFileUpload(path, mimetype='...document')` +
   `drive.files().update(fileId=<SAME id>, media_body=media)`. This
   REPLACES the file content in place → link unchanged → user can forward
   it to the advocate for re-confirmation.
5. **Verify from Drive**: download the file back with `get_media`, re-run
   the blue-run assertion + text checks (each intended change present).
6. Deliver the SAME webViewLink + a bullet list of what changed and why
   (e.g. "prayer reverted to joint 5-heirs grant per FSD 06.08.2025",
   "GPA reference date filled", "execution date 05.09.2026").

## Pitfalls
- `files().update()` with media_body REPLACES content but preserves id,
  name, parents, permissions — do not pass a name unless renaming too.
- Re-uploading a docx as Google Docs conversion requires
  `application/vnd.openxmlformats-officedocument.wordprocessingml.document`
  mimetype; if the original Drive file is a native Google Doc, first
  download the docx export (or export to docx then edit) — but prefer
  editing the native docx copy if present.
- Blue intent: NDR reviews-by-eye — do NOT hide a change in a merged run
  where the whole paragraph was rewritten black. Every corrected string
  must itself be blue.
- If a date has two places (petition signature date AND verification
  date), update BOTH — he counts them (verified 2 of 2 in the worked
  example).
- The user runs the corrected doc by the advocate again ("I will just run
  it by Sanjay Sethia again asking him to reconfirm") — phrase the
  deliverable to support that: same link + explicit list of what changed.