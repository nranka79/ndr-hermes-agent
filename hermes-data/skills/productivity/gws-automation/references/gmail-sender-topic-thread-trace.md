# Gmail Sender-Topic Thread Trace

**When the user asks:** "Check my emails from [name/advocate/lawyer] regarding [property/project name]. What did they last say? Summarize the last N emails back and forth."

**Why this is different from gmail-specific-thread-audit:**
- The sender name the user says may not match the email From: header (e.g., "Advocate Prasanna Kumar" → actual email from "Prasanna Swaminathan")
- The property name may be spoken phonetically (e.g., "Kathar Nalli" → Katenahalli)
- Goal is a NARROW chronological trace of one specific conversation thread, not a broad scan
- The deliverable is a point-by-point summary of what each side said, not a priority/action table

## Workflow

### Phase 1 — Name and Topic Resolution

The user says a name that may not match the From: header. Always start with MULTIPLE search queries in parallel:

```python
from tools.gws_auth import build_service
service = build_service('gmail', 'v1')

# Try multiple variants — the user may have the name slightly wrong
# or the advocate may have a different email display name
queries = [
    f'{spoken_name_variants} {property_variants}',
    f'from:{email_substring_if_known}',
    f'{property_variant_2}',
    f'{advocate_last_name_only} {property_variant_3}',
]
```

**Name resolution strategy:**
| User says | What to try |
|-----------|-------------|
| "Prasanna Kumar" | `Prasanna` (search all, find the actual name) |
| "Prasanna Kumar Vettokumbak" | each word individually |
| Just "advocate" + last name | The name may be a middle name or part of a compound surname |
| Name of their firm/office | Try `Centre Point`, the firm name, the area |

**Property name resolution:**
| User says | Likely match |
|-----------|-------------|
| "Kathar Nalli" | Katenahalli (Karnataka village name) |
| "Lakshmi Pura" | Laxmipura or Lakkasandra |
| Any spoken Indian village name | Check RTC records, survey numbers, email subjects for similar-sounding names |

### Phase 2 — Identify the Thread

Once you find messages from the correct sender:
1. List all messages from that sender sorted by date
2. Identify which ones are about the target property/project
3. Check if the email is part of a thread (same Subject with Re:)
4. Note which messages are DIRECT (user ↔ advocate) vs THIRD-PARTY (advocate to vendor/consultant, user CC'd)

Key: The last DIRECT exchange may not be the last email overall. The advocate may have sent follow-ups to third parties (e.g., document vendor Sangam) that reference the same project but aren't replies to the user.

### Phase 3 — Read Full Email Bodies

Gmail stores messages as MIME multipart. Use this helper to extract text/plain:

```python
import base64

def extract_text(payload):
    """Recursively extract text/plain from MIME parts."""
    if payload['mimeType'] == 'text/plain' and 'data' in payload.get('body', {}):
        return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
    if 'parts' in payload:
        for part in payload['parts']:
            result = extract_text(part)
            if result:
                return result
    return ''
```

**Important:** `format='full'` in the get() call returns the full MIME tree. `format='raw'` returns the raw RFC822 bytes but is harder to work with. Use `format='full'`.

The body may contain:
- **New content** (the sender's current message) — this is the actual latest communication
- **Quoted text** (lines starting with `>`) — previous messages in the thread
- **Forward boundaries** (`---------- Forwarded message ---------`)

For summary purposes, identify the NEW content (first part before quoted/forwarded text) as the latest communication, then use the downward-quoted text to reconstruct the thread history.

### Phase 4 — Thread Reconstruction

Rules for reconstructing back-and-forth:

1. **Direct reply chain:** Advocate sends → user responds → advocate responds to user's response. This is a true back-and-forth.
2. **Monologue chain:** Advocate sends → user responds → advocate sends to someone else (not user). The thread goes silent on the user side.
3. **Stale thread:** User responds with feedback/requirements → advocate acknowledges and promises revised version → revised version never arrives. This is the most common pattern with Indian legal advocates.

For each email in the back-and-forth, extract:
- **Date** (normalize to IST)
- **Sender → Recipient**
- **Key substantive content** (not pleasantries or attachment references)
- **Promises/commitments** (e.g., "will deliver revised report by Friday")
- **Whether the promise was fulfilled**

### Phase 5 — Structured Summary Format

Present as a chronology table:

```
## [Advocate Name] — [Property Name] Thread

| # | Date | Direction | What Was Said |
|---|---|---|---|
| 1 | Jan 7 | Advocate → You | Sent summary note on title for Sy. 157/1 & 158 |
| 2 | Mar 23 | Advocate → Group | Updated reports for Sy. 157, 158, 114/12 |
| 3 | Mar 24 | You → Advocate | Detailed feedback: needs doc index, Akarband records, want to disprove Grant narrative |
| 4 | Mar 24 | Advocate → You | Acknowledged all points, promised revised reports by Friday |

### Bottom Line
| Question | Answer |
|---|---|
| Last DIRECT exchange? | Date and subject |
| Did promised deliverables arrive? | Yes/No/Partial |
| What's the status now? | One-line summary |
```

The table at the end should answer the user's implied question: "What happened last and what should I do next?"

### Pitfalls

| Pitfall | Fix |
|---------|-----|
| **No results from first query** | Don't give up. Try single words. The name or property may be spelled differently in email than how the user said it. |
| **Email body is empty (shown as empty in output)** | The body was in an attachment or an alternative MIME part. Try the recursive extract_text() above, or check for `text/html` if `text/plain` is empty. |
| **Last email from advocate went to someone else** | Check To/CC headers. The advocate may have emailed Prakash (psingh@draas.com) or Aamir about the same topic while you were on CC or not copied. Expand your search to those recipients' inboxes if accessible. |
| **Thread has dozens of messages** | Focus only on the ones where (a) the user's address is in To/CC, AND (b) the content relates to the specific property. Sangam-vendor emails about document checklists for the same property are context but not "back and forth" with the user. |
| **Advocate name doesn't match from: header** | This is COMMON. The user may know the advocate by their full name (Prasanna Kumar) but the email was set up under a different name (Prasanna Swaminathan). Check the email signature block and reply-to chain for name clues. |
| **Multiple properties in same thread** | The advocate may handle Katenahalli, Gunjur, Laxmipura in parallel. Filter only the property the user asked about. Mention the other threads only if relevant as context. |

### When to use this vs gmail-specific-thread-audit

| Use case | Which reference |
|----------|----------------|
| "Check my last N days and track 3 company threads" | `gmail-specific-thread-audit` |
| "What did Advocate X last say about Property Y?" | `gmail-sender-topic-thread-trace` (this) |
| "Find the email from Kotak Bank about my FD" | `gmail-transaction-search` |
| "Did I reply to X's email about the agreement?" | `email-thread-doc-tracker` |
