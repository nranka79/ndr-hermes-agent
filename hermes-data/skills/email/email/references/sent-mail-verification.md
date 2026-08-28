# Sent Mail Verification

Verify whether an email with a specific attachment was sent to named recipients. Useful when the user says "did I send X to Y with the PDF?" from a voice description.

## Trigger

User asks: "did I send [attachment/PDF] to [person]", "check my sent mail and confirm I sent it to [name]", "was [person] included on that email", "find the email with [description] that went out"

## Core Flow

### 1. Resolve the account

```python
from tools.gws_auth import build_service
gws_resolve_account(account="ndr@draas.com")
service = build_service('gmail', 'v1', service_name='google-draas')
```

### 2. Search sent mail with precise operators

```python
results = service.users().messages().list(
    userId='me',
    q='in:sent after:YYYY/MM/DD (keyword1 OR keyword2)',
    maxResults=20
).execute()
```

Key Gmail search operators:
- `in:sent` — only sent items
- `after:YYYY/MM/DD` / `before:YYYY/MM/DD` — date range
- Keywords in parens `(word1 OR word2)` — match any
- Use `subject:` prefix to scope to subject line

### 3. Check attachment filenames

Gmail API returns attachments in nested parts. Walk the tree:

```python
def find_attachments(parts_list):
    for p in parts_list:
        fn = p.get('filename', '')
        if fn:
            attachments.append(fn)
        find_attachments(p.get('parts', []))
```

### 4. Verify each recipient was individually addressed

Sent emails to different people are SEPARATE messages (not CC), even when sent at similar times. Check each message's `To` header independently.

### 5. Cross-reference across all accounts

If not found on the primary account, check all available ones via `gws_resolve_account()`. Search `google-ahfl` (ndr@ahfl.in) and `google-gmail` (nishantranka@gmail.com) independently.

## Pitfalls

- **Voice-mangled names** — "Riyaga" / "Gawri" may not match actual spellings. Search phonetic variants, check the contact directory, or ask for clarification.
- **Separate messages, not CC** — individual sends at the same time, not a mass CC. Don't look for a single email with multiple To addresses.
- **Nested attachment parts** — forwards may embed the original as a MIME part; walk the full tree with recursion.
- **Date format** — Gmail uses `YYYY/MM/DD`. Widen the range if no results.
- **Results pagination** — `messages().list()` may return only the first page. Check `nextPageToken` for more.
- **`prevPageToken` from LM memory is stale** — pageTokens expire after ~10 minutes. Always request fresh with `maxResults`.
- **Verify `labelIds`** — use `'SENT' in m.get('labelIds', [])` to confirm it's a sent message (not inbox/draft) when ambiguity exists.