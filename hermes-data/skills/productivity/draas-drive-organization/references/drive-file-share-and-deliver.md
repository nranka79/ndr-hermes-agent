# Drive File Find → Verify → Share → Deliver (Telegram/WhatsApp)

Worked 2026-09-28: NDR dictated "find me the Embassy Habitat 1503 survey drawing, give Roshini access, send her a Telegram message with the link."

## 1. Find it

- `gws_drive_list` with `query="name contains '<fragment>'"` — broad first ("Embassy Habitat"), then narrow (`1503`, `survey`, `dwg`/`mimeType='application/acad'`).
- The `name contains '<unit>'` search (`1503`) surfaces a *folder* named after the unit as well as files — inspect the folder before assuming a file is missing.
- Multiple copies exist across accounts (ndr@draas.com, sales1.blr@draas.com, admin2.blr@draas.com) — pick the file whose **owner is ndr@draas.com** and whose parent chain matches the project folder.
- If the ask is "survey drawing of the whole layout" but only a DWG exists, say so plainly: no PDF twin exists, the DWG is the only copy. (In the worked case the folder ALSO had GF/FF *floor plans* — PDFs, but they are not the survey.)

## 2. Verify DWG content — know what you CAN'T do

Native AutoCAD DWG (magic `AC1021` = AutoCAD 2007+ binary, compressed) is **not readable as text**:
- `strings` on the file yields only binary noise (`$$$C`, `&&&C` …) — no layer names, no text entities. DWG of this version stores text compressed; nothing is greppable.
- `ezdxf` reads **DXF only** — `ezdxf.readfile('x.dwg')` raises `OSError: File is not a DXF file`. Native DWG needs an ODA File Converter / LibreDWG (`dwgread`); neither is installed on the box.
- `file`/`xxd` may also be missing from PATH.
- Conclusion: **do not burn time trying to render/verify DWG content locally.** Verify by (a) filename self-description (`..._SurveyDrawing_...`), (b) sibling files in the same folder (same surveyor/date batch), (c) `gws_drive_get` modified/created times. Then deliver, and OFFER the user a PDF/image conversion (needs the ODA converter installed, or a surveyor-side export) rather than silently failing.

## 3. Grant access

```python
# via gws_drive_permissions_add (native tool):
# email = rnr@draas.com (Roshini's registered DRAAS identity)
gws_drive_permissions_add(file_id="<FILE_ID>", email="<EMAIL>", role="reader", service_name="google-draas")
```
- Default role **reader**. Only escalate to writer/commenter if the user asks (deliverable is viewing/using the drawing).
- Use the person's canonical email from the contacts sheet/People (Roshini → `rnr@draas.com`), not a guessed gmail.

## 4. Deliver the link

- Share link form: `https://drive.google.com/file/d/<FILE_ID>/view` — plain link, not a code block.
- **Telegram**: `send_message(recipient_name="Roshini Ranka", platform="telegram", message="...link...")`. Recipient must exist in the identity registry (check with `send_message(action='list')` if unsure — Telegram targets include `Roshini Ranka (dm)`).
- In the message, say who it's from (NDR asked), what it is, and offer the conversion if the format is niche (DWG needs CAD software to open).
- Nothing to "send" on the user's side — this is an outbound Telegram message, actually delivered (verify the `success: true` + `message_id` in the response).