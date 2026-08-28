# Multi-Model Google Doc Rewrite Pipeline

When you need to substantially rewrite a Google Doc based on new strategic context, use this three-stage pipeline: independent deep-thinking models + synthesis model + Docs API bulk update.

## When to use

- The document is a discussion note, risk analysis, or governance doc that needs re-drafting because of a structural change (new ownership ratio, entity type change, strategic pivot)
- The changes are too extensive for line-by-line patching — you're replacing most sections
- The user wants multiple independent analyses before a final version

## The three-stage pipeline

### Stage 1: Read the source document

Read the Google Doc as plain text via Drive API export:

```python
import sys
sys.path.insert(0, '/opt/hermes')
import os
# User ID from context (check skill SKILL.md for known mappings)
os.environ['HERMES_SESSION_USER_ID'] = 'ndr'  # Nishant
from tools.gws_auth import build_service

# Export as text
drive = build_service('drive', 'v3')
doc_id = '1Wz...'  # from the Google Doc URL
content = drive.files().export(fileId=doc_id, mimeType='text/plain').execute()
if isinstance(content, bytes):
    content = content.decode('utf-8')
```

Use `/opt/hermes/.venv/bin/python3` (not system `python3`) — it has googleapiclient installed.

### Stage 2: Call two (or more) independent deep-thinking models via OpenRouter

Use `call_openrouter_model` for each model independently — they run in parallel in the same turn. Each gets the full document text plus the new context/instructions.

**Model selection by use case:**

| Use case | Deep-thinking model | Synthesis model |
|----------|-------------------|-----------------|
| Legal/commercial doc rewrite | `openai/o3-mini` + `google/gemini-3.5-flash` | `anthropic/claude-opus-4` |
| Technical analysis | `openai/o3-mini` + `google/gemini-2.5-pro` | `anthropic/claude-opus-4` |
| Creative/editorial | `openai/o3-mini` + `google/gemini-3.5-flash` | `anthropic/claude-sonnet-4` |

**Prompt structure for deep-thinking models:**

Each deep-thinking model prompt must contain:
1. The **full document** (paste verbatim between backtick fences)
2. The **new context** — what changed and why
3. A numbered **task list** with explicit instructions

Important: Set `max_tokens` high enough (12000-16000) since each model's output is a complete revised document.

The `user_trigger_phrase` parameter must include the model family name (gpt, gemini, claude, deepseek, qwen, etc.). Examples:
- `"Use GPT via OpenRouter to analyze..."` → works for o3-mini, GPT-4, etc.
- `"Use Gemini via OpenRouter to analyze..."` → works for all Gemini models
- `"Use Claude Opus via OpenRouter to synthesize..."` → works for Claude models

Call the deep-thinking models first (in parallel, same turn), then call the synthesis model in a later turn after both results are back.

### Stage 3: Synthesize with a third model

After receiving both deep-thinking analyses, call a synthesis model (preferably Claude Opus or Sonnet) with:
1. A brief summary of the new context
2. Key recommendations from Model A
3. Key recommendations from Model B
4. The document structure to follow
5. Instructions to produce ONE clean final document

The synthesis prompt should be structured to guide the model toward producing a complete document ready for insertion, not an editorial commentary.

### Stage 4: Apply to the Google Doc via Docs API

Use the `docs.documents().batchUpdate()` API with two requests in one call:

1. `deleteContentRange` — delete from index 1 to (end_index - 1)
2. `insertText` — insert the new content at index 1

```python
docs_service = build_service('docs', 'v1')
doc = docs_service.documents().get(documentId=doc_id).execute()
body = doc.get('body', {})
content = body.get('content', [])
end_index = content[-1]['endIndex'] if content else 1

# Bulk replace
requests = [
    {
        'deleteContentRange': {
            'range': {
                'startIndex': 1,
                'endIndex': end_index - 1
            }
        }
    },
    {
        'insertText': {
            'location': {'index': 1},
            'text': new_content  # synthesized document text
        }
    }
]
docs_service.documents().batchUpdate(
    documentId=doc_id,
    body={'requests': requests}
).execute()
```

This is faster and cleaner than line-by-line editing for major rewrites.

### Stage 5: Rename to indicate new version

```python
drive = build_service('drive', 'v3')
drive.files().update(
    fileId=doc_id,
    body={'name': 'YYYYMMDD_Project_DocType_V3'}
).execute()
```

## Pitfalls

- **Document too large for model context window.** The full V2 document in the example was ~22K chars — within most model limits. If the doc is larger, truncate or summarize the least relevant sections before sending.
- **Google Docs export removes some formatting.** The plain text export loses bullet styling, tables, colors, and fonts. The bulk-replace method replaces ALL content, so any formatting will be lost. For documents that need rich formatting preserved, use line-by-line Docs API editing instead.
- **HERMES_SESSION_USER_ID must be set correctly.** Check the SKILL.md header for the user-ID mapping for common users. Terminal subprocesses don't inherit this env var — set it explicitly.
- **The synthesis model may restructure the document.** Claude Opus tends to reorganize content into what it considers a better structure. If the original structure must be preserved, explicitly say "preserve the original document's structure and section headings" in the synthesis prompt.
- **Document length may change.** After bulk replacement, the document may be longer or shorter. The `end_index` is recalculated from the live doc — always fetch it fresh before the batchUpdate call, don't cache it.
