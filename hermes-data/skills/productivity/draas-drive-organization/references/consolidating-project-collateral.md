# Consolidating a user's own collateral into one folder per project (verified 2026-10-05)

Recipe for the ask: *"put all the sales & marketing related data to one folder in my Drive prepared by
me — one of <project A> and one of <project B> — add PS as suffix to the folder name, only final /
last versions."*

## The four decisions that matter

1. **MOVE, do not COPY.** Drive storage is genuinely constrained at DRAAS (NDR has raised running out
   of storage), so duplicating a few hundred MB of PDFs/renders across folders is unacceptable. A
   move keeps the file ID, so **every existing share link, permission and embed stays valid** —
   nothing breaks. Copying creates a second object with a new ID and doubles the bytes.
2. **Only final / last versions go in.** Exclude v1/v2/v3 intermediates, superseded drafts and
   duplicated `Copy of …` objects — but **leave them where they are**. Do not delete or trash without
   asking; the cleanup story is "the new folder holds finals, the old folders hold leftovers".
3. **Scope to what the user actually authored.** "Prepared by me" excludes files they merely
   forwarded, and excludes a different department's material. Legal / RERA / banking documents
   (APF forms, RERA filings, sale deeds, board resolutions) are a **different class** from sales &
   marketing collateral — leave them out and say so explicitly so the omission reads as deliberate.
4. **Do not decompose existing well-formed subfolders.** If a project already has a tidy
   `X (PS) - Marketing Collaterals` folder containing `Brochures & Specs` / `Floor Plans` / `Renders`,
   move the *subfolders* in whole. Flattening 23 renders into one flat list is a worse outcome than
   carrying the grouping across.

## Finding the finals — the ordering pass

Pull everything by name, then classify. Reading only the filenames is not enough; you need
`modifiedTime` and the owner:

```python
r = svc.files().list(q=f"name contains '{term}' and trashed=false", pageSize=100,
        fields='files(id,name,mimeType,modifiedTime,owners(emailAddress),parents)').execute()['files']
```

Sort each document family by `modifiedTime` and keep the newest per family. Where a family has an
explicit version in the name (`…_v4.2_30Sep2026.pdf` vs an unversioned sibling), the **versioned,
later-timestamped** one is the final — verify with the timestamp, don't trust the name alone.

Also pull the children of the obvious PS-owned folders before choosing; the final often already lives
inside one (`Ranka Udaya Marketing and Content`, `RANKA Amber (PS) - Marketing Collaterals`,
`Lead Outreach Materials — Updated Oct 2026`).

## Executing the moves

```python
def move(fid, newp):
    f = svc.files().get(fileId=fid, fields='parents').execute()
    old = ','.join(f.get('parents', []))
    svc.files().update(fileId=fid, addParents=newp, removeParents=old, fields='id,parents').execute()

def mk(name, parent=None):
    body = {'name': name, 'mimeType': 'application/vnd.google-apps.folder'}
    if parent: body['parents'] = [parent]
    return svc.files().create(body=body, fields='id,webViewLink').execute()
```

Move items **one at a time and log failures** — a loop that swallows exceptions reports "all moved"
when some silently did not. Print `moved N/M` and re-list the destination folder afterwards as proof.

Where a source folder is then left holding only superseded files, **say so and offer to clean it** —
do not tidy it unilaterally.

## Traps hit

- **`terminal` rejects a heredoc containing `&`.** The literal string `Sales & Marketing` inside a
  folder name made the tool refuse with *"Foreground command uses '&' backgrounding. Use
  terminal(background=true)…"* — which is a false positive, not a real backgrounding attempt. Fix:
  `write_file` the script to `/data/hermes/tmp/<name>.py`, then run
  `/opt/hermes/.venv/bin/python3 /data/hermes/tmp/<name>.py`. Do this for any Drive script that
  mentions an ampersand-named folder.
- **Flag genuine duplicates rather than silently including them.** A `Copy of <same cost sheet>`
  sitting beside the original is not a "version" — name it in the reply and offer to bin it.
- **Deliver final-version counts per folder** ("31 items / 14 items — 11 files + 3 subfolders") so the
  user can eyeball completeness in the reply without opening Drive.
- **This is an explicit exception to the TMP-first rule.** Normal chat-session artifacts are born in
  TMP; a consolidation the user explicitly asks for lands directly in the folders they named.
