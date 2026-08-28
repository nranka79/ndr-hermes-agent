# Whitelist Sheet Schema & Rule Parsing

## Sheet metadata
- Spreadsheet ID: `1w8_R0JzfHP1PIdPoCFpqdhDh9TFU0qPqbt3V2vfDyw0`
- Tab: `Whitelist` (rows A:I, header in row 1, data starts row 2)
- Account: google-draas (ndr@draas.com)

## Column mapping (0-indexed)

| Index | Column  | Field             | Python access              |
|-------|---------|-------------------|----------------------------|
| 0     | A       | row_number        | row[0].strip()             |
| 1     | B       | category          | row[1].strip() if len > 1  |
| 2     | C       | value             | row[2].strip() if len > 2  |
| 3     | D       | to_email          | row[3].strip() if len > 3  |
| 4     | E       | subject_keywords  | row[4].strip() if len > 4  |
| 5     | F       | description       | row[5].strip() if len > 5  |
| 6     | G       | rule_type         | row[6].strip() if len > 6  |
| 7     | H       | date_added        | row[7].strip() if len > 7  |
| 8     | I       | notes             | row[8].strip() if len > 8  |

## Critical traps

### 1. No "enabled" column
Column B is `Category` (e.g. "Legal", "Banking - HDFC"), NOT an enabled/disabled flag.
**All listed rules are active.** A rule is valid if it has a value in column A (row #)
and a value in column G (rule type). Do NOT check any "enabled" boolean.

### 2. Rule types and their matching logic

```python
sender_email = ... # extracted from From header ("Name <addr>" → addr)
sender_domain = sender_email.split('@')[1].lower() if '@' in sender_email else ''
subject = ...      # from Subject header

for rule in rules:
    rt = rule['rule_type']   # column G
    val = rule['value'].lower()   # column C

    if rt == 'exact_from':
        if sender_email.lower() == val:
            MATCH

    elif rt == 'domain_from':
        # Strip @ prefix if present (sheet sometimes has @domain.com, sometimes domain.com)
        domain = val.lstrip('@')
        if sender_domain == domain:
            MATCH

    elif rt == 'subject_contains':
        keywords = [kw.strip().lower() for kw in rule['subject_kw'].split(',')]
        for kw in keywords:
            if kw and kw in subject.lower():
                MATCH

    elif rt == 'combined':
        domain_val = val.lstrip('@')
        kw_list = [k.strip().lower() for k in rule['subject_kw'].split(',')]
        if sender_domain == domain_val and any(kw and kw in subject.lower() for kw in kw_list):
            MATCH
```

### 3. Known special rules
- Row 12: `domain_from @draas.com` — catches ALL internal @draas.com emails (marketing, hr, etc.)
- Row 17: `domain_from google.com` — Google platform notifications (Drive, Calendar, etc.)

## Sender email extraction
The `From` header comes in formats like:
```
"Name Surname" <email@domain.com>
email@domain.com
'Name via Channel' <email@domain.com>
```
Always extract with:
```python
sender_email = sender
if '<' in sender and '>' in sender:
    sender_email = sender.split('<')[1].split('>')[0].strip()
```

## Gmail API calls used

### Fetch spam
```python
gmail_svc.users().messages().list(userId='me', q='in:spam', maxResults=200).execute()
```

### Get message details
```python
gmail_svc.users().messages().get(
    userId='me', id=msg_id, format='metadata',
    metadataHeaders=['From', 'Subject', 'To']
).execute()
```

### Move to inbox
```python
gmail_svc.users().messages().modify(
    userId='me', id=msg_id,
    body={'removeLabelIds': ['SPAM'], 'addLabelIds': ['INBOX']}
).execute()
```