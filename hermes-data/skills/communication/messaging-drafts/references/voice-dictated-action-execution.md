# Voice-Dictated Action Execution Workflow

**Trigger:** User sends a voice message containing a sequence of instructions to execute — not just a reply to an email, but a series of independent actions (upload files, share documents, send notifications, create emails).

This is distinct from `voice-dictated-multi-point-email-reply.md` (which is specifically about replying to a numbered email) and `voice-entity-resolution.md` (which resolves contact names). This workflow handles "do these N things" instructions from a single voice message.

## Workflow

### Phase 1: Transcribe

Use whisper (transformers pipeline as fallback — see mlops/models/whisper skill for CPU-only setup) to get text from the `.ogg` file.

The audio file is at `/data/hermes/audio_cache/` — find the most recent file.

```python
from transformers import pipeline
pipe = pipeline("automatic-speech-recognition", model="openai/whisper-base", dtype=torch.float32, device=-1)
result = pipe("/data/hermes/audio_cache/audio_XXXX.ogg", return_timestamps=True)
transcript = result["text"]
```

> **Pitfall:** Audio > 30 seconds requires `return_timestamps=True` — otherwise the pipeline raises `ValueError` about "more than 3000 mel input features."

### Phase 2: Parse Into Action Items

Voice dictation is lossy. Common artifacts:
- **Name mangling:** "Rochney" → Roshni, "redsole" → redsoul.co.in, "Gundelpaint" → Gundalpet
- **Email address typos:** Always cross-reference against Gmail contacts/People API before acting
- **Number confusion:** "redsole.co.in" from voice may actually be "redsoul.co.in" — verify against email thread headers before granting access
- **Project names:** Voice creates spelling variants (Shoolagiri/Shulagiri, Bili/Bidadi, Gundalpet/Gundlupet) — verify against Drive folder names and prior conversations

Parse the transcript into discrete, numbered action items. Present them to the user for confirmation before execution.

### Phase 3: Sequential Execution

Voice instructions often have dependency chains. Execute in order:

1. **Drive operations first** (upload, rename, delete duplicates) — establishes the documents before sharing
2. **Permissions/Sharing** — grant access to the uploaded documents
3. **Email notifications** — send after permissions are set so recipients can access links immediately
4. **WhatsApp message** — deliver as code block for copy-paste (last, since user needs to copy and send)

### Dual-Channel Variant: WhatsApp + Email for Record

When the user says "send a WhatsApp message AND an email to put this on record" (NOT a dependency chain — both channels carry the SAME info simultaneously):

1. **WhatsApp and email are PEER actions, not sequential** — create the WhatsApp deep link AND the email draft in parallel
2. **Email MUST be a threaded reply on an existing relevant thread** (see `references/proactive-dual-channel-record.md`), never a new email
3. **WhatsApp = immediate notification; Email = permanent record** — same content, different purpose
4. Deliver both results together: WhatsApp deep link + email draft location + CC list

### Phase 4: Validate & Confirm

Before sending the final output:
- **Verify all documents were found** — check Drive search results; if a document the user references isn't found, ask
- **Verify email addresses** — cross-check against the Gmail thread headers (From/To/Cc) rather than relying solely on voice transcription
- **Present a summary** of what was done before delivering the WhatsApp draft

## Workflow Diagram

```
Voice .ogg → Transcribe (whisper) → Parse actions → 
  ├─ 1. Drive ops (upload, rename, delete dupes)
  ├─ 2. Permissions (viewer/editor for specific emails)
  ├─ 3. Email (send with links)
  └─ 4. WhatsApp (code block for copy-paste)
→ Present summary → Deliver final output
```

## Pitfalls

1. **Disk space:** whisper + torch + CUDA needs ~3-4GB. On constrained systems, use CPU-only torch with `--index-url https://download.pytorch.org/whl/cpu` and keep only the most recent audio files. Clean `/data/hermes/audio_cache/` regularly (keep last 10 files max).

2. **Audio cache cleanup:** `rm -f /data/hermes/audio_cache/*.ogg` to free space. The audio file won't auto-redownload if deleted — ask user to resend if needed.

3. **Duplicate Drive files:** Users often upload the same file twice (same name, same content). Check for duplicates before/after upload. Delete older copies.

4. **Email addresses from voice:** Always verify against the actual email thread headers. Voice will mangle "msingh@redsoul.co.in" as "redsole.co.in" or other variants.

5. **Document naming:** Follow the project's existing naming convention. For DRAAS documents, the pattern is `YYYYMMDD_ProjectName_Description_FROM.xxx` — check the target Drive folder for existing filenames to match the convention.

6. **Google Drive permission changes are immediate:** Once you grant `reader` or `writer` access, the recipient gets an email notification by default. Set `sendNotificationEmail=False` unless the user explicitly wants the recipient notified.
