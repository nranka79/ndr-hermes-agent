# Reorg Plan HTML Template (TMP-Deliverable)

The user (Jul 2026) requires every reorg plan to be a single self-contained HTML file saved to TMP, using a dark theme so it's "very easy to read" with the current org structure and the proposed reorg side-by-side. This is the template.

**TMP folder id for `ndr@draas.com`:** `18p74II2uL32sNDzDDwXzmlOUdJJOTmE-`

**Why this format:**
- Telegram renders HTML cleanly when uploaded to Drive (just paste the `MEDIA:` link after upload, or send the Drive `webViewLink`)
- Self-contained — single file, no CSS dependencies
- Dark theme matches the user's preferred reading context (Telegram night mode, Hermes TUI)
- Trivial to share / version / archive in TMP

## Structure (mandatory sections, in this order)

1. **Title + meta block** — generated date, Drive account, scope (X source folders, Y files affected)
2. **Correction callout** (only when plan is v2+) — call out what changed from the previous version with a colored "Updated" callout
3. **Bucket structure explanation** — for the user, since they may have forgotten their last instruction
4. **Summary stats grid** — 6-10 colored stat boxes (files per bucket, folders to trash, etc.)
5. **AS-IS tree** — `details/summary` block with a CSS-styled `ul/li` tree showing every source folder and its current contents
6. **TO-BE tree** — same style, showing the proposed destination
7. **Phase-by-phase execution plan** — colored callout boxes (Phase 1, 2, 3...)
8. **File-by-file classification tables** — one `details` block per bucket, with a table of `(from folder, original name)` rows. List every file. Don't summarize.
9. **Decisions table** — 4-6 numbered decisions, with default + answer field. Use the `clarify` tool to get answers.
10. **Footer** — generation date, supersession note (if v2+), reversibility disclaimer

## CSS template (copy this verbatim)

```css
:root {
  --bg: #0f1419;
  --panel: #1a2030;
  --panel2: #232b3d;
  --border: #2d3650;
  --text: #e6e9ef;
  --text-dim: #9aa3b8;
  --accent: #4f8cf7;
  --accent2: #6dd3a4;
  --warn: #f7a14f;
  --danger: #f76e6e;
  --trash: #8a8a8a;
  --keep: #6dd3a4;
  --move: #4f8cf7;
}
* { box-sizing: border-box; }
body {
  background: var(--bg);
  color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  line-height: 1.55;
  margin: 0;
  padding: 32px 20px;
}
.container { max-width: 1300px; margin: 0 auto; }
h1 { color: var(--accent); border-bottom: 2px solid var(--border); padding-bottom: 12px; margin-top: 0; font-size: 26px; }
h2 { color: var(--accent2); margin-top: 40px; border-bottom: 1px solid var(--border); padding-bottom: 8px; font-size: 20px; }
.meta { background: var(--panel); border: 1px solid var(--border); border-radius: 8px; padding: 14px 18px; margin: 16px 0; }
.meta b { color: var(--accent2); }
.summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin: 18px 0; }
.stat { background: var(--panel); border: 1px solid var(--border); border-radius: 8px; padding: 14px; }
.stat .num { font-size: 26px; font-weight: 700; color: var(--accent); }
.stat .lbl { color: var(--text-dim); font-size: 12px; margin-top: 4px; }
.stat.warn .num { color: var(--warn); }
.stat.danger .num { color: var(--danger); }
.stat.keep .num { color: var(--accent2); }
.tree {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 16px 20px;
  font-family: "SF Mono", Consolas, "Courier New", monospace;
  font-size: 12px;
  line-height: 1.7;
  overflow-x: auto;
}
.tree ul { list-style: none; padding-left: 22px; margin: 4px 0; }
.tree li { position: relative; }
.tree li::before { content: ""; position: absolute; left: -16px; top: 0; height: 100%; border-left: 1px dashed var(--border); }
.tree li::after { content: ""; position: absolute; left: -16px; top: 14px; width: 12px; border-top: 1px dashed var(--border); }
.tree li:last-child::before { height: 14px; }
.folder { color: var(--accent); font-weight: 600; }
.folder.highlight { color: var(--accent2); font-weight: 700; }
.file { color: var(--text); }
.file.trashed { color: var(--trash); text-decoration: line-through; }
.root { color: var(--warn); font-weight: 700; font-size: 14px; }
.plan-table { width: 100%; border-collapse: collapse; margin: 16px 0; background: var(--panel); border-radius: 8px; overflow: hidden; font-size: 12px; }
.plan-table th { background: var(--panel2); color: var(--text-dim); text-align: left; padding: 10px 12px; border-bottom: 2px solid var(--border); font-weight: 600; text-transform: uppercase; font-size: 10px; letter-spacing: 0.5px; }
.plan-table td { padding: 8px 12px; border-bottom: 1px solid var(--border); vertical-align: top; }
.plan-table tr:hover td { background: var(--panel2); }
.plan-table .filename { color: var(--text); font-family: "SF Mono", Consolas, monospace; font-size: 11px; word-break: break-all; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
.badge.move { background: rgba(79, 140, 247, 0.18); color: var(--move); }
.badge.create { background: rgba(109, 211, 164, 0.18); color: var(--accent2); }
.badge.trash { background: rgba(247, 110, 110, 0.18); color: var(--danger); }
.badge.keep { background: rgba(109, 211, 164, 0.18); color: var(--keep); }
.callout { background: var(--panel); border-left: 4px solid var(--accent); border-radius: 4px; padding: 14px 18px; margin: 18px 0; }
.callout.warn { border-left-color: var(--warn); }
.callout.danger { border-left-color: var(--danger); }
.callout.success { border-left-color: var(--accent2); }
.callout b { color: var(--accent); }
.callout.warn b { color: var(--warn); }
.callout.danger b { color: var(--danger); }
.callout.success b { color: var(--accent2); }
details { background: var(--panel); border: 1px solid var(--border); border-radius: 8px; padding: 10px 16px; margin: 8px 0; }
details summary { cursor: pointer; color: var(--accent); font-weight: 600; user-select: none; }
details[open] summary { margin-bottom: 8px; }
code { background: var(--panel2); padding: 1px 6px; border-radius: 3px; font-family: "SF Mono", Consolas, monospace; font-size: 11px; color: var(--accent2); }
.footer { color: var(--text-dim); font-size: 12px; text-align: center; margin-top: 60px; padding-top: 20px; border-top: 1px solid var(--border); }
```

## Generation pattern (Python)

```python
# After building classification into /tmp/reorg/classification_FINAL.json:
# 1. Write the template with placeholders for each bucket table
# 2. For each bucket, generate HTML rows
# 3. Substitute placeholders
# 4. Upload to TMP

with open("/tmp/reorg/plan_template.html") as fh:
    html = fh.read()

# Bucket rows helper
def bucket_rows(items):
    rows = []
    for c in items:
        src = shorten_path(c.get('parent_path', '?'))
        name = c['name'].replace('|', '\\|')
        rows.append(f"<tr><td class='source'>{src}</td><td class='filename'>{name}</td></tr>")
    return "\n".join(rows)

for bucket_name, placeholder in [("01_Title_and_Legal_Opinions", "__BUCKET_01__"), ...]:
    items = [c for c in classified if c["bucket_name"] == bucket_name]
    html = html.replace(placeholder, bucket_rows(items))

# Save and upload
write_file("/tmp/reorg/plan.html", html)
upload_to_drive("/tmp/reorg/plan.html", TMP_ID, name="YYYYMMDD <Project> - Reorg Plan.html")
```

## Versioning pattern

When the user corrects the plan, **trash the previous version** before uploading v2. Pattern:
```python
# Find and trash prior version
prior = service.files().list(
    q=f"name contains 'Reorg Plan' and '{TMP_ID}' in parents and trashed = false",
    pageSize=5, fields="files(id)"
).execute()
for f in prior.get("files", []):
    service.files().update(fileId=f["id"], body={"trashed": True}, supportsAllDrives=True).execute()

# Upload new
service.files().create(body={...}, media_body=MediaFileUpload(...)).execute()
```

The new HTML's "Correction callout" section at the top should explicitly call out what changed from the prior version. User will often iterate v1 → v2 → v3 — make the changes clear each time.

## Common mistakes

- **Don't summarize file lists.** "57 files going to bucket 01" is useless; show all 57 rows in a `details` block.
- **Don't skip the AS-IS tree.** The user explicitly said: *"showing me the current org structure, the current different folders, where do they lie, what is the root, what is the entire tree under which these folders lie, right?"* — show the full tree, with file IDs inline.
- **Don't propose to My Drive root.** The user has been burned by this; v2 of one plan had to be redone. The TO-BE tree always shows the canonical home.
- **Don't forget reversibility.** Footer MUST say "All operations reversible from Drive Trash for 30 days."
- **Don't use light mode.** The user is on Telegram dark mode + Hermes TUI; the dark theme CSS is mandatory.
- **Don't include charts/graphs.** HTML file size should stay under 100KB. Tables + tree + callouts only.
