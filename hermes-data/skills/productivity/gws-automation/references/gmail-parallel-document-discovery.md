# Parallel Gmail Document Discovery (delegate_task Pattern)

When the user asks you to find a specific document or piece of information buried in years of Gmail emails and attachments (e.g., "when did X get shares transferred", "find the board resolution for Y", "search my entire email history for Z"), a single sequential search is too slow and risks missing results hidden in attachment content.

## The Pattern

Use `delegate_task` with parallel subagents, each searching a different query or thread. Each subagent gets its own Gmail API session and searches independently.

### Phase 1: Broad Reconnaissance

First, run a few wide-net Gmail searches to identify the key threads and people involved:

```python
from tools import gws_auth
from googleapiclient.discovery import build

creds = gws_auth.load_credentials('google-draas')
service = build('gmail', 'v1', credentials=creds)

# Run broad queries to identify threads
queries = [
    "BRDPL share transfer",
    "board resolution transfer",
    "Kanta share"
]
for q in queries:
    result = service.users().messages().list(userId='me', q=q, maxResults=10).execute()
    for m in result.get('messages', []):
        msg = service.users().messages().get(userId='me', id=m['id'],
            format='metadata', metadataHeaders=['From','Subject','Date']).execute()
        headers = {h['name'].lower(): h['value'] for h in msg.get('payload',{}).get('headers',[])}
        print(f"{headers.get('date','')[:16]} | {headers.get('subject','')[:70]}")
```

### Phase 2: Identify Threads with Attachments

Check which emails have attachments (these are where the actual documents live):

```python
def has_attachments(msg_id):
    msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
    parts = msg.get('payload', {}).get('parts', [])
    return any(p.get('filename') and p.get('body',{}).get('attachmentId') for p in parts)
```

### Phase 3: Delegate Parallel Subagents

Send parallel subagents to process different threads/queries simultaneously:

```python
from hermes_tools import delegate_task

# DON'T do this in execute_code (sandbox restriction)
# Instead, call delegate_task directly as a tool
```

**IMPORTANT**: `delegate_task` is a Hermes tool, not a Python function you import. Call it directly in your response, not from inside execute_code.

Each subagent should:
1. Search a specific thread or query via the Gmail API (using `tools.gws_auth.build_service`)
2. Download relevant attachments
3. Extract and search content inside attachments (docx, PDFs, xlsx)
4. Return dates and findings

### Phase 4: Example Task Distribution

For finding a shareholder date across 50+ BRDPL emails:

| Task | Query | Goal |
|------|-------|------|
| Agent 1 | "Board minutes" thread | Find share transfer/allotment resolutions |
| Agent 2 | "Share transfer" thread | Find SPA, holding statements, dates |
| Agent 3 | "Minutes summary" Excel/attachments | Find summarized shareholder changes |
| Agent 4 | Broader Gmail search | Check accounts for Kanta mentions |
| Agent 5 | Drive document search | Find share certificates, MGT-7, SH-4 forms |

### Phase 5: Synthesize Results

Collect all subagent outputs and cross-reference dates. The most authoritative source is typically the board meeting minutes (MOBM — Minutes of Board Meetings) which record the exact date of board approval for share transfers/transmissions.

## Pitfalls

- **gws_skill_bridge.gmail_search may return 0 results** even when valid emails exist. Use the direct Gmail API (`gws_auth.build_service('gmail', 'v1')`) instead of the bridge for reliable searches. The bridge's `gmail_search` has intermittent issues where it returns empty arrays.
- **Subagent timeout on large attachments**: A 3.3MB docx with hundreds of pages of board minutes may take 2-3 minutes to process. Set appropriate timeouts. If an agent times out, the findings from other agents may still be sufficient.
- **Sandbox can't use GWS**: `execute_code` sandbox cannot access the vault socket (`gws_fetch_token` import fails). Always run Gmail/Drive Python code in `terminal()` calls (using `<< 'PYEOF'` heredoc syntax) — never inside `execute_code`.
- **"Kanta" may not appear in email bodies**: The name may only be inside attachment content (PDFs, docx). Gmail's fullText search indexes attachments, but the bridge's `gmail_search` may miss these. Use the direct API with `format='full'` and check `payload.parts` for attachment IDs.
- **Attachment download**: Use `service.users().messages().attachments().get(userId='me', messageId=msg_id, id=attachment_id).execute()` to download. The data is base64-encoded in `data` field.
- **Breadth-first search**: Start with broad queries to identify the few key threads, then deep-dive only those threads. Searching every single email sequentially is wasteful.
