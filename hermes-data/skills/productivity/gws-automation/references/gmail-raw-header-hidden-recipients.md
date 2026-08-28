# Gmail Raw Header Parsing — Hidden CC/BCC Recipients

When an email's `To` and `Cc` headers from Gmail's metadata API don't show a person you know is on the thread, they may be hidden in **raw MIME headers** (listed in a RFC 2822 continuation line in the CC field, or added via BCC).

The standard Gmail API metadata request does NOT always return all CC recipients:

```python
# This may MISS recipients — only shows parsed CC list
msg = service.users().messages().get(
    userId='me', id=MSG_ID,
    format='metadata',
    metadataHeaders=['To', 'Cc', 'Subject']
).execute()
headers = {h['name']: h['value'] for h in msg['payload']['headers']}
print(headers.get('Cc'))  # May be truncated
```

## Fix: Use raw format and parse MIME headers

```python
import base64

msg = service.users().messages().get(
    userId='me', id=MSG_ID,
    format='raw'  # Returns full RFC 2822 message
).execute()

raw_bytes = base64.urlsafe_b64decode(msg['raw'].encode('utf-8'))
raw_text = raw_bytes.decode('utf-8', errors='replace')

# Scan all lines for hidden recipients
for line in raw_text.split('\n'):
    lower = line.lower()
    if 'to:' in lower or 'cc:' in lower or 'bcc:' in lower:
        print(line)
```

## Why this happens

Gmail's API metadata parser sometimes splits CC headers across multiple MIME continuation lines (indented with whitespace + tab on subsequent lines). The `metadataHeaders` response only captures the first line of the header. The full raw message preserves all continuation lines.

## Example from Jun 2026

A Viraj Majithia email showed:
- `metadataHeaders['Cc']` → `Satish Jadhav <satish.jadhav@godrejventure.com>, Amit Saraf`
- Raw headers revealed a continuation line: `\tSaurabh Vashishth <saurabh.vashishth@godrejventure.com>`

## When to use this

- You cross-reference a name mentioned in the email body ("Looping in Saurabh") but can't find their email in the standard CC list
- A previous email in the thread says "++ Saurabh" or "adding X to this thread"
- The user says "make sure X is marked" but X doesn't appear in any parsed header
