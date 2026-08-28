# Gmail Sent-Email Investigation

**Pattern:** User asks "did I send X to Y? Was link Z in that email? Follow up if needed."

## Steps

1. **Identify the user's Gmail account** — usually `ndr@draas.com` (primary) or `ndr@drahomes.in` (alias). Search both.

2. **Search strategies** (in order of specificity):
   ```
   to:<recipient> after:<date> <subject keyword>
   from:<sender> to:<recipient> <keyword>
   ```
   - Start with specific recipient + subject keyword
   - Broaden if no results (drop date, drop recipient, try partial names)
   - Search both `to:` (primary) and body mentions

3. **Get full message body** — use `format='full'` to get the complete email including links:
   ```python
   m = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
   ```
   Extract plain-text body from parts, handling multipart MIME nesting.

4. **Verify link presence** — search the decoded body for the specific URL or document ID.

5. **Report** — tell the user:
   - Which email you found (date, subject, to)
   - Whether the link WAS or WAS NOT in it
   - If not there, where it was sent instead (to whom)

6. **If follow-up is requested** — draft and send the update email with the link explicitly highlighted.

## Common Search Query Patterns

| Pattern | Example |
|---|---|
| By recipient + date | `to:psingh@draas.com after:2026/06/15` |
| By recipient + keyword | `to:psingh@draas.com "sharing agreement"` |
| By content link | `1EnY77qQ-UXeMV7Pr49l6kiK_RTITK_jQ09gvljTthWI` (doc ID) |
| From + alias | `from:ndr@drahomes.in to:prakash` |
| Forward detection | `Fwd to:prakash SSA` |
| Date-ranged sent | `from:ndr@draas.com after:2026/06/14` |

## Handling Voice-Transcribed Name Variations

The user often sends voice messages, so recipient names you hear may differ from the actual Gmail spelling:

- **Try multiple spellings** — e.g., user says "Shinchana" → search `Sinchana`, `Shinchana`, `Sincena` — the actual name may be `Sinchana` (sgowda@draas.com) or a personal email (sinchanalgowda16@gmail.com)
- **Check both work and personal emails** — the same person may appear as `sgowda@draas.com` (work) and `sinchal*@gmail.com` (personal)
- **Iterate queries** — if a specific `to:<name>@draas.com <keyword>` query returns 0, try dropping the keyword, then dropping the domain, then searching just the keyword
- **Use `from:` scope** when the user says "I sent" — `from:ndr@draas.com after:<date>` to list all sent emails in range, then scan subjects

## Thread Status Investigation (checking for replies)

**Pattern:** User asks "check if X replied to our email thread" — find the latest reply from a specific party on a thread.

Unlike "did I send?" (sent email search), this is a **thread investigation** — find all messages on a known thread and identify the latest external reply.

### Steps

1. **Find the thread** — search by exact subject or participant:
   ```python
   results = service.users().messages().list(
       userId='me',
       q='subject:"BuxRanka Hudson Project" godrej OR godrejventure',
       maxResults=5
   ).execute()
   ```

2. **Get the full thread** — use `threads().get()` to fetch all messages at once:
   ```python
   thread = service.users().threads().get(userId='me', id=thread_id).execute()
   for msg in thread['messages']:
       headers = {h['name']: h['value'] for h in msg['payload']['headers']
                  if h['name'] in ['From', 'Date', 'Subject']}
       print(f'[{headers["Date"]}] {headers["From"]}')
       print(f'  {msg["snippet"][:200]}')
   ```

3. **Check for replies after a known date** — narrow search to surface new replies:
   ```python
   # After you know the last-message date, check for anything newer
   results = service.users().messages().list(
       userId='me',
       q='after:2026/06/23 godrej OR godrejventure OR smithakshi'
   ).execute()
   ```

4. **Report the timeline** — present the last N messages chronologically so the user can see who said what and when.

### Common thread-investigation queries

| Goal | Query |
|---|---|
| Find a specific thread | `subject:"Project Name" godrej` |
| Check for recent replies | `after:YYYY/MM/DD godrej OR godrejventure` |
| From a specific person | `from:smithakshi@godrejventure.com after:YYYY/MM/DD` |
| Full thread snapshot | Use `threads().get()` on the threadId |

### Pitfall — Gmail search may cap at 100 results
If a thread has many messages, `messages().list()` may only return 100 max. Use `threads().get()` (which returns all messages in a thread) for comprehensive thread investigation instead of relying on `messages().list()` alone.

---

## Pre-Follow-up: Verify Document Access

**Before sending a follow-up email with a document link**, check that the recipient actually has access to it. If they don't, grant access first.

### 1. Check current permissions on the linked document

```python
drive = build_service("drive", "v3")
perms = drive.permissions().list(
    fileId=DOC_ID,
    fields="permissions(id, emailAddress, role, type, expirationTime)"
).execute()
for p in perms.get('permissions', []):
    print(f"  {p.get('emailAddress','?')} -> {p['role']} (expires: {p.get('expirationTime','no expiry')})")
```

### 2. Add editor access with expiry if recipient is missing

```python
from datetime import datetime, timezone, timedelta

expiry = datetime.now(timezone.utc) + timedelta(days=7)
drive.permissions().create(
    fileId=DOC_ID,
    body={
        'type': 'user',
        'role': 'writer',       # Editor access
        'emailAddress': 'psingh@draas.com',
        'expirationTime': expiry.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    },
    sendNotificationEmail=False  # Don't spam them before your email
).execute()
```

### 3. Sequence matters — grant access BEFORE sending the follow-up

```
1. Check current permissions on linked doc
2. If recipient missing → grant Editor with 7-day expiry
3. THEN send follow-up email highlighting the link
```

## Pitfalls

- **Recipient in CC doesn't show in `to:` search** — use `cc:` prefix or search without recipient field
- **Multiple aliases** — Nishant sends from both `ndr@draas.com` and `ndr@drahomes.in`. Check both.
- **Gmail full-text search is case-insensitive** but stem-aware
- **Encoded email bodies** — plain text parts (`text/plain`) are base64-encoded. Use `base64.urlsafe_b64decode()`.
- **Gmail truncates large results** — use `maxResults` and pagination for comprehensive searches
- **Voice-transcribed names won't match Gmail** — iterate through phonetic variations before concluding email doesn't exist
- **Don't send follow-up without verifying access** — the link is useless if the recipient can't open it

## Sending Follow-up Email

When user says "if link was there, send update highlighting it":

```python
message = MIMEText(body_text)
message['To'] = ', '.join(recipients)
message['Subject'] = subject
raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
service.users().messages().send(userId='me', body={'raw': raw}).execute()
```

### Follow-up email structure

Keep the email targeted — the user specifically wants the recipient to see the link:
- **Subject:** Direct and descriptive (e.g., "Project X — Specific Document Name")
- **Body:** Lead with the link, highlight what it is, note access has been granted
- **To:** Include all original recipients + anyone the user explicitly adds
