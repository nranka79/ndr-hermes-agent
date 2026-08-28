# Email-attachment → Drive filing (deliver a doc the user needs to print/sign)

Use when the user says "give me that Word document from the email with <advocate> re <matter>" / "pull the attachment, file it, give me the link" — the deliverable is the file ON DRIVE (renamed + filed in the matter folder) plus the link, often with a MEDIA: copy so they can print immediately.

## Pipeline (validated 2026-08-17, ITAT giving-effect-order letter)

1. **Locate the thread by case number / person, not date.** Search `q='<case-no> <matter-keyword>'` (e.g. `ITA 2786`). The thread may be a side-thread with a DIFFERENT subject ("Draft of letter to be submitted") from the main matter thread ("Re: ITA 2786/...") — collect both. Match on the person's name (Arunkumar M.S. / arunkumarms1158@gmail.com) if needed.
2. **Walk message parts for the attachment** — attachments may be nested (multipart/alternative > parts). Dump the parts tree of each message in the thread; record filename, mimeType, attachmentId, size:
   ```python
   def dump_parts(parts, indent=4):
       for p in parts:
           fn = p.get("filename",""); body = p.get("body",{})
           print(f"{' '*indent} {p.get('mimeType','')} | fn='{fn}' | attId='{body.get('attachmentId','')}' | sz={body.get('size',0)}")
           if "parts" in p: dump_parts(p["parts"], indent+4)
   ```
3. **Download via `messages().attachments().get(messageId, id=attachmentId)`** → `base64.urlsafe_b64decode(data)`. Save to `/tmp/<descriptive>.docx`.
4. **Verify content BEFORE delivering** — for docx: `zipfile.ZipFile(path).read('word/document.xml')` + strip tags + html.unescape, print first ~2500 chars. Confirms it's the right letter (parties, PAN, case no, dates) and not a stale/corrupt copy. This also surfaces the content summary the user expects ("it's the Giving Effect Order letter re ITA 2786...").
5. **Check Drive for existing versions BEFORE uploading** — `name contains '<matter keyword>'` (e.g. 'Giving Effect Order Letter'). A signed PDF and a FILLED.docx may already sit in My Drive root from when the user previously prepared the document. Tell the user these exist and ask which they want for the print/sign use-case — the FILLED version is usually the better print target even though they asked for the "original" from the advocate.
6. **Upload with a descriptive name** — `Dinesh Ranka - Giving Effect Order Letter - Original Word Doc from Arunkumar M.S - 7 Jul 2026.docx` style (matter + person + source + date). Keep the native docx mimeType (`application/vnd.openxmlformats-officedocument.wordprocessingml.document`) so the user gets a real .docx they can edit/print.
7. **File in the matter folder, not root** — find the right home (see matter-folder map below) and move via `files().update(addParents=..., removeParents=...)`. Verify parent after move.
8. **Deliver** — Drive link (`webViewLink` or `webContentLink`) + MEDIA:/tmp/path.docx so it's printable immediately from Telegram.

## Matter-folder map (Dinesh Ranka ITAT / tax matters)

- **DR ITAT** folder `1fRsJMML15vYuVKmV_Gprr6TF1gSFll9m` — home for Dinesh Ranka ITAT AY 2011-12 docs: set-aside notices, Order.pdf, NFAC appeal, indemnity/legal-heir docs (240713 Indemnity Agreement Legal Heirs_NDR.docx), and the giving-effect-order letter family.
- Related docs NOT yet consolidated there (2026-08-17): `Dinesh Ranka - Giving Effect Order Letter - 30 July 2026 - FILLED.docx` (`1ylV1N8PWGGkLZvz2b0UZsE0_mRLsEpvA`) and `... - SIGNED.pdf` (`17jLh1uPEMZUFTQbDvIawx5okdmUs8uVu`) sit in My Drive root. Offer to move them into DR ITAT so the whole matter sits together.

## Thread reference (worked example)

Thread `19f3b09fb55511df` "Draft of letter to be submitted":
- 7 Jul 2026, Arunkumar M.S. → NDR: original `New Microsoft Word Document (3).docx` (12,498 bytes) — the advocate's letter template.
- 30 Jul 2026, NDR → Arunkumar: `Dinesh Ranka - Giving Effect Order Letter - 30 July 2026 - SIGNED.pdf` (40,009 bytes) — the filled+signed+scanned return.

## Pitfalls

- **vision_analyze rejects PDFs outright** (`Only real image files are supported for vision analysis`) — if you need to read a scanned attachment, convert with `pdftoppm -png -r 150 file.pdf /tmp/page` first, then vision_analyze the PNG. For docx, the zipfile text extraction is instant and better than any vision route.
- The `gmail messages list` search `q='subject:"..." from:arunkumar'` may return the wrong thread (side-thread with different subject). Expand to the case-number query and walk the whole thread.
- Draft scripts printing JSON need `import json` — a NameError on `print(json.dumps(res))` means the draft_create itself already succeeded; verify via `drafts().list()` and move on, don't re-create.
