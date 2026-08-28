# Marketing Collateral Lookup — "links shown by <person>" / "anything called posters"

## Trigger
User asks variations of: "share the list of links shown by <person>", "anything called as posters / brochures / flex / hoarding shown by <name>". Typically for the content & marketing head (Gowri Singh — user often says "Gauri", same person, gsingh@draas.com / +91 98454 30607).

## Search ladder (in order)
1. **session_search** for the person's name + aliases (Gauri → Gowri Singh) + "links". This finds the original request/conversation where links were given (e.g. the Ranka Oasis WhatsApp message set, the Serenity Hill View AV feedback links).
2. **Drive search by the file-type noun the user gives** — Drive `name contains` is CASE-INSENSITIVE, so one query suffices:
   ```
   name contains 'poster' and trashed=false
   ```
   A noun query only catches files literally named with that word ("Poster 1.png"). For a full collateral sweep run several nouns: `poster`, `flex`, `hoarding`, `brochure`, `sunpack`, `render`.
3. **Identify the containing folder and list IT** (not just the matched files) — the folder often holds related collateral the user also wants (brochure, video, hoarding). List with:
   ```python
   service.files().list(q=f"'{parent_id}' in parents and trashed=false",
       fields="files(id, name, mimeType, webViewLink, createdTime)", pageSize=200).execute()
   ```
4. **Deliver clean links** `https://drive.google.com/file/d/<ID>/view` (strip `?usp=drivesdk` from webViewLink) + the folder link. Reply with the found set and ask if it's the right project — posters exist per-project, don't assume which one.

## Ranka Udaya marketing folder (verified Aug 2026)
- Folder: `Ranka Udaya` — ID `129WGpGKBCE12ZqobdQj4CCT5Nxdc1Fgc` (sits at Drive ROOT, not under DRA Projects)
- Contents (createdTime Apr–May 2026):
  - Poster 1.png `1CfWTs2L-PpZlnkTTsc_a2YvpD-BLPjlP` … Poster 8.png `1ycz6MLV67ZiAbADoCnPzdoLmAoiCsHx6` (Poster 2 `1-t-JGe-AWMxEUOby9CJxeNE9dljq7BDA`, 3 `1jqHHeHKsWkE0rgRanPWeZ1m2qZd_PnwQ`, 4 `1b8x7kHKurefp2HsT0H0Yij_HAtonS1y0`, 5 `11stk004XbsUg_DEQ-rYFC0uUNMXpANoP`, 6 `1smlhg6zQxs_Id6U9OqaanKhOZjUCWiY1`, 7 `15uW6Wsi55NeJsGH0jtSUmKdqi4uF94OI`)
  - Flex.png `1xRTbKCtGsDKzKA2gwFXIT79IIPmBebXM`
  - Hoarding Board Design.png `15LF3wEPbRomqKRoXXfKsuNXbUy_33Da_` (16 MB)
  - Sunpack.png `1URHEwzGdNQiIL0fmiw8GXER4MqgIMO-P`
  - Ranka Udaya Brochure.pdf `1xdmpYzVtaScg6oG0XA4EuxOeU1VnBu77`
  - Video.mp4 `1NyaZRM2zzv6gRuTEE_trRqUfRZfyp6k-`
- Related: AI-enhanced marketing images (Ranka Udaya 1-12.jpg) live in `1PPCfTmrupoHW4mLzPq0TQmMRKD0NOQb8`; architectural renders in `1KV0fDCalH6VJ_QJudVkUwhbc8LR5nBCk`.

## Pitfall — inline python in terminal() breaks on escaping
`terminal(command=f"... python3 -c {json.dumps(code)}")` mangles newlines/escapes → `SyntaxError: unexpected character after line continuation character`. **Fix: write the .py with write_file to /tmp, then run**:
```
cd /opt/hermes && /opt/hermes/.venv/bin/python3 /tmp/script.py
```
Same for heredocs with nested quotes — write_file is always safer than inline `-c` or heredoc quoting for GWS scripts.