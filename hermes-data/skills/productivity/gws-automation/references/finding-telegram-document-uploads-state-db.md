# Finding Telegram Document Uploads via state.db

When the user says "I sent those PDFs yesterday around 6:25 PM" and you need to find which session actually received the upload, query the state.db directly. This is the canonical pattern — much faster than scrolling session_search.

## The state.db schema (June 2026)

```
sqlite3 /data/hermes/state.db
.tables
# -> schema_version, sessions, messages, sqlite_sequence, state_meta,
#    messages_fts, messages_fts_data, messages_fts_idx, messages_fts_content,
#    messages_fts_docsize, messages_fts_config, messages_fts_trigram, ...
```

`messages` columns:
- `id` (INTEGER, PK)
- `session_id` (TEXT)
- `role` (TEXT — 'user' | 'assistant' | 'tool' | 'system' | 'session_meta')
- `content` (TEXT — the message body; for Telegram uploads, this is the bracketed metadata: `[The user sent a document: 'filename.pdf'. The file is saved at: /data/hermes/document_cache/doc_<hash>_<filename>.pdf. Ask the user what they'd like you to do with it.]`)
- `timestamp` (REAL — Unix epoch seconds, UTC)
- `tool_call_id`, `tool_calls`, `tool_name`, `token_count`, `finish_reason`, etc.

`sessions` columns:
- `id` (TEXT — `20260605_044253_80914804` style)
- `source` (TEXT — `telegram`, `cron`, etc.)
- `started_at` (REAL — Unix epoch seconds, UTC)
- `last_active`, `message_count`, `title`, `preview`

## Two ways to find document uploads

### 1. Search messages directly (faster, more precise)

```python
import sqlite3
from datetime import datetime

conn = sqlite3.connect('/data/hermes/state.db')
cur = conn.cursor()

# All document uploads in a 6.5 hour window on June 4, 2026 IST (12:00–18:30 UTC)
cur.execute('''
  SELECT session_id, role, timestamp, content
  FROM messages
  WHERE content LIKE '%document_cache%'
  AND role = 'user'
  AND timestamp BETWEEN 1780587600 AND 1780612200  -- 12:00 to 18:30 UTC = 5:30 PM to midnight IST
  ORDER BY timestamp
''')
for r in cur.fetchall():
    ts = datetime.fromtimestamp(r[2]).strftime('%Y-%m-%d %H:%M:%S')
    print(f'[{ts}] {r[0]} -> {r[3][:200]}')
```

### 2. Find sessions first, then look up their messages

```python
# All telegram sessions on a given day
cur.execute('''
  SELECT id, source, started_at, title
  FROM sessions
  WHERE started_at BETWEEN 1780554000 AND 1780630000
  AND source = 'telegram'
  ORDER BY started_at
''')
```

The session-based approach is useful when you want to read the full conversation (not just the upload events).

## Unix epoch to IST mental math

IST is UTC+5:30. Quick conversions:
- 12:00 UTC = 5:30 PM IST
- 12:55 UTC = 6:25 PM IST
- 14:00 UTC = 7:30 PM IST
- 18:30 UTC = midnight IST

For "around 6:25 PM yesterday" with 30-min slop, search `timestamp BETWEEN (17:00 UTC) AND (19:00 UTC)`.

## The cron-session-trap

**Documents uploaded while a cron session is active are silently lost.** The cron session (`source = 'cron'`, scheduled reminders, etc.) has its own session_id and processes emails/inputs internally — uploaded PDFs sit in the doc cache but the cron session doesn't act on them.

How to detect this:
1. Find which session_id received the upload (using pattern #1 above)
2. Check `sessions.source` for that session_id
3. If `source = 'cron'`, the upload was ignored — you need to surface this to the user

Workaround: tell the user to re-send the PDFs in a normal session (not while a cron is firing). The user can usually tell by looking at which Telegram chat was active at the time.

## The phantom-attachment trap: user says "attached" but no file was cached

The user says "Attached is a judgment" — but you find nothing in document_cache and no `[The user sent a document: ...]` record in state.db. This happens when the Telegram gateway received the message but the file wasn't cached, typically in two scenarios:

**Scenario A: Internal API pipeline consumed the message first.**
The message was passed to an internal pipeline task (e.g. search-query generation, follow-up suggestion) as plain text inside `<chat_history>`. The pipeline task receives only the text — the file attachment is stripped. By the time the real agent processes the message, there is no file to work with.

**Scenario B: File upload genuinely failed at the Telegram gateway.**
The gateway log (`/data/hermes/logs/agent.log`) shows no `Cached user document at ...` entry for the message. The file was never downloaded.

### How to detect a phantom attachment

```python
import sqlite3, re
from datetime import datetime, timezone

conn = sqlite3.connect('/data/hermes/state.db')
cur = conn.cursor()

now = datetime.now(timezone.utc).timestamp()
recent = now - 600  # last 10 minutes

# 1. Find messages where user said "attach" or "upload" near text about a document
cur.execute("""
  SELECT id, session_id, timestamp, substr(content,1,300)
  FROM messages
  WHERE role = 'user'
    AND (content LIKE '%attach%' OR content LIKE '%upload%' OR content LIKE '%document%' OR content LIKE '%pdf%')
    AND content NOT LIKE '%The user sent%'  -- exclude actual cached uploads
    AND timestamp > ?
  ORDER BY timestamp DESC
  LIMIT 10
""", (recent,))

for r in cur.fetchall():
    ts = datetime.fromtimestamp(r[2]).strftime('%H:%M:%S')
    print(f'[{ts}] msg#{r[0]} session={r[1]}')
    print(f'  text: {r[3][:150]}')

# 2. Cross-check against actual document uploads in same window
cur.execute("""
  SELECT COUNT(*) FROM messages
  WHERE content LIKE '%The user sent a document%'
    AND timestamp > ?
""", (recent,))
cached_count = cur.fetchone()[0]
print(f'\nActual documents cached in this window: {cached_count}')
```

### What to tell the user

Be direct: "I checked the system — the file wasn't received. Your message came through as text only. Could you please resend the file?"

Do NOT say "I can't find the file" — this implies the file exists but you lost it. Say "it wasn't received/cached." This sets accurate expectations about the Telegram gateway's behavior, not your search skills.

### Preventing phantom attachments

- Ask the user to upload the file **in a fresh message by itself**, then send the analysis request in a follow-up message. Sending both in one message risks pipeline processing.
- If the user says "I already sent it" and you can confirm the file exists in document_cache (Scenario A from above), search for the document_cache path and use it directly — the file IS there, it just wasn't attached to the working session.

## Full filename extraction

The state.db stores the bracketed metadata, not the file content. To get the actual filenames, regex them out:

```python
import re
m = re.search(r"doc_[a-f0-9]+_([^\\\\.]+\\.pdf)", content)
filename = m.group(1) if m else '?'
```

Files live at `/data/hermes/document_cache/doc_<hash>_<filename>.pdf`. The hash is stable per file content — same file uploaded twice gets the same hash. The filename is the user-visible name with a timestamp prefix from telegram's `file.date` (e.g. `202606041800.pdf` = uploaded June 4 2026 at 18:00).

## Alternate upload path: `/opt/data/` direct saves

Not all Telegram file uploads go through `document_cache`. Some land directly at `/opt/data/<filename>` as a bare file on disk with no entry in document_cache. This happens for certain phone-gallery attachments and PDFs sent from mobile document apps.

**Detection:**

```bash
find /opt/data -maxdepth 3 -type f \( -iname "*.pdf" -o -iname "*.jpg" -o -iname "*.png" -o -iname "*.jpeg" -o -iname "*.zip" \) -newer /opt/data/ 2>/dev/null | head -10
```

If the user says "I shared it earlier in this session" and you find nothing in document_cache, run the above command immediately before searching Drive or state.db.

## Why not just use session_search?

session_search is FTS5 over message content — it's great for "find sessions where the user mentioned X" but slow for "find all PDF uploads in a 6-hour window on a specific day". Direct state.db SQL is the right tool for time-bounded structural queries.

## Reference: state.db is a 426 MB file

`/data/hermes/state.db` is large (426 MB on June 5 2026, growing). Direct `sqlite3 state.db` from a Python script is fine — just don't copy the file. Use `from datetime import datetime` to format the `timestamp` (REAL, epoch seconds) — don't try to format from inside SQL.
