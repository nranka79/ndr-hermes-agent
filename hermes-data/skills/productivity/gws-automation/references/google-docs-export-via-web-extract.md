# Reading Google Doc Text via web_extract Export URL

When vault access is unavailable (sandbox limitations, session-ID mismatch, stale token), you can still **read** Google Doc content by exporting to plain text via the direct export URL.

## Pattern

```python
from hermes_tools import web_extract

doc_id = "1abcDEF123..."
url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"
result = web_extract(urls=[url])
text = result["results"][0]["content"]  # plain text of the document
```

## Limitations

- **Read-only** — Cannot update docs through this path
- **Public/shared access required** — The doc must be accessible to the viewer. If the doc is not shared, the export returns a Google login page, not the content
- **Plain text only** — No formatting, tables, or images are preserved
- **Best for inspection** — Use this to check what `[To be filled]` markers exist, verify content before updating, or extract data

## When to Use

1. **Vault offline** — Terminal vault access also fails
2. **Execute_code sandbox** — `gws_fetch_token` stub is missing (tool not in enabled_tools)
3. **Quick inspection** — You just need to read the content, not modify it

## When NOT to Use

- **Need to update the doc** — Use the Docs API via vault-authenticated terminal script
- **Doc has complex formatting** — Tables, lists, images won't come through. Use Docs API instead
- **Doc is not shared** — The export URL requires view access

## Verified Example (Jul 2026)

Reading all 9 SBI pre-approval documents to find `[To be filled]` markers:

```python
docs_to_check = [
    "1OyjSC4MY6VylLnWH7iM_ZjjVhSbrMc8hiNV2Fx6zZ9M",  # CA Cert - Amber
    "1_ParqgsHR2sNuAjbu8Mj4IXRpGno3lI01iOzg_ZnHOM",  # Req Letter - Amber
    "1ToeGXdYOp1MQMWO-26bycsVDrfujom5d32TmxgUq0jE",  # Builder Profile - Amber
    # ... etc
]
for doc_id in docs_to_check:
    url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"
    result = web_extract(urls=[url])
    text = result["results"][0]["content"]
    tbf_count = text.count("[To be filled]")
    print(f"Doc {doc_id}: {tbf_count} placeholders")
```
