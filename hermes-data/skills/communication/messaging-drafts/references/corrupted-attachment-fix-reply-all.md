# Corrupted Attachment Fix — Reply-All with Corrected PDF

When a sent email had a corrupted PDF attachment (detected via "Undeliverable" bounce or manual inspection), the fix pattern:

## Detection

- **Bounce notice**: `Undeliverable: Re: <subject>` from Postmaster — the attachment got corrupted during transit or was malformed at source
- **MD5 mismatch**: Compare the attached file's MD5 against the Drive source. A single-byte difference is enough to break a PDF. Download the attachment from the sent email via `gmail.users().messages().attachments().get()`, save to disk, compute `hashlib.md5()`, and compare against the Drive version.

## Fix Workflow

1. **Find the sent email** — search by recipient, subject keywords, CC names. Prefer the latest one that went to the intended recipient (not an auto-generated bounce).

2. **Download the attachment from the sent email** — via `gmail.users().messages().attachments().get(userId='me', messageId=msg_id, id=attachmentId)`. Decode with `base64.urlsafe_b64decode()`. Save to `/tmp/`.

3. **Confirm corruption** — run `pdfinfo` to verify valid PDF structure (1 page, correct page size), and compare MD5 with the Drive source file. Report the difference to the user as evidence.

4. **Find the correct source** — search Drive by name (`name contains 'KDR' and name contains 'cancelled'`) or check the user's Personal/KDR folders. Verify the Drive file with `pdfinfo` and `pdftoppm` + vision check.

5. **Create reply-all draft** with corrected attachment:
   - Get the original message's raw bytes via `gmail.users().messages().get(userId='me', id=msg_id, format='raw')` → `base64.urlsafe_b64decode()`
   - Parse with `email.parser.BytesParser().parsebytes()` to extract `Message-ID` header
   - Build `MIMEMultipart('mixed')` with:
     - `In-Reply-To` = original Message-ID
     - `References` = original Message-ID
     - Same `To`, `Cc` as original
     - Body apologizing for the corruption and explaining the corrected attachment
     - Attachment from Drive source (read local copy with `open(pdf_path, 'rb')`, attach as `MIMEApplication(pdf_data, _subtype='pdf')`)
   - Thread the draft to the original thread: pass `threadId` from the original message in `users().drafts().create()`

6. **Deliver** — return the draft URL: `https://mail.google.com/mail/u/0/#drafts?compose={draft['id']}`

## Pitfalls

- **`format='raw'` is required** for getting the original Message-ID — `format='metadata'` or `'full'` won't return the raw bytes
- **"Undeliverable" bounces have a different thread ID** than the original sent email — do NOT use the bounce's thread for your reply; find the original sent email's thread via subject/recipient search
- **Drive file and Gmail attachment may differ by 1 byte** despite appearing identical — always MD5-compare before assuming they match
- **Folder expiration dates** cannot be set on My Drive folders (`cannotSetExpiration` error) — only grant writer/reader directly without `expirationTime` for folders
- **Large Drive file downloads** (>50MB) may timeout in foreground `terminal()` — use `background=true` with `notify_on_complete=true` and download via `MediaIoBaseDownload` with chunked progress
