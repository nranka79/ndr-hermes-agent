# Gmail Draft Threading & Reply-All — Pitfalls and Proven Recipe

Context: preparing draft-only replies/forwards (never auto-send — see SOUL email rule).
Source: Aug 2026 session — ITR reply-all draft to Eshwari, Red Soul refund forward to Roshni/Eshwari.

## PITFALL — `drafts().create()` with raw MIME can land on the WRONG thread

When you build a reply draft as a raw MIME `email.message.EmailMessage` and create it via:

```python
draft = svc.users().drafts().create(
    userId='me',
    body={'message': {'raw': raw}}).execute()
```

Gmail does NOT always consolidate it into the source message's thread, even when you set
`In-Reply-To` / `References` headers correctly. **Observed live:** the draft came back with
`threadId: 1a01de64f31d5b61` while the source email's thread was `1a0193d4df586045` — a
MISMATCH. The reply would have landed in a broken/separate thread, defeating reply-all.

## FIX — pass `threadId` explicitly in the draft body

```python
draft = svc.users().drafts().create(
    userId='me',
    body={'message': {'raw': raw, 'threadId': thread_id}}).execute()
```

where `thread_id = source_msg.get('threadId')` (fetch it from the source message before
building the draft). After creating, ALWAYS re-fetch the draft (`drafts().get(... format='full')`)
and verify `draft['message']['threadId'] == thread_id` and that `In-Reply-To`/`References`
match the source. If mismatched, delete the bad draft and recreate with the threadId.

## Reply-all header construction from a source message

The reply-all recipient set excludes YOUR OWN address from source To/Cc (don't echo yourself).
Rules used live:
- `To` = the source's From (the person you're replying to)
- `Cc` = the source's To/Cc minus your own address(es)
- `Message-ID`: read from source; set reply `In-Reply-To` = source Message-ID, and
  `References` = (source's References if present) + source Message-ID
- `Subject` = `Re: ` + source Subject (only prefix if not already `Re:`)
- Thread into source thread: `{'raw': raw, 'threadId': thread_id}`

## Forward construction

- `To` = destination addresses
- `Subject` = `Fwd: ` + original subject
- Set `In-Reply-To` / `References` to the original Message-ID so Gmail keeps it associated
- Body = your FYI note + the reproduced original ("---------- Forwarded message ----------"
  header block with From/Date/Subject/To/Cc + original text)

## Verify before hand-off

Per the unique-sender rule, verify BEFORE reporting the draft is ready:
1. `drafts().get(id, format='full')` → confirm To/Cc/Subject/In-Reply-To/References/body.
2. Confirm `threadId` matches the source thread (see pitfall above).
3. Confirm identity first with `users().getProfile(userId='me')` → must be the intended account
   (e.g. ndr@draas.com). See google-workspace skill for the identity-mismatch failure mode.
4. Report the draft ID + "review in Drafts, send yourself" — never auto-send.

## Getting the source's threading headers

Fetch source with `format='full'`, walk `payload['headers']` for
`Message-ID`, `References`, `In-Reply-To`, `From`, `To`, `Cc`, `Subject`.
