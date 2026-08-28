# Reading AI Studio Prompt Files from Drive

AI Studio prompt files (Google AI Studio chats saved to Drive) have mimeType `application/vnd.google-makersuite.prompt`. They cannot be exported or opened as standard documents — they must be read via `drive.files().get_media()` and parsed as JSON.

## When to use this

- User says "find files under Google AI Studio folder" or "read the AI Studio prompts"
- User refers to "chats" or "prompts" saved from Google AI Studio about a specific project/transaction
- User asks you to understand context that was developed in AI Studio conversations

## Structure

The file is JSON with this structure:

```json
{
  "runSettings": {
    "model": "models/gemini-2.5-pro",
    "temperature": 1.0,
    "maxOutputTokens": 65536,
    "thinkingBudget": -1
  },
  "chunkedPrompt": {
    "chunks": [
      {
        "driveDocument": {
          "id": "<google-doc-id>",
          "tokenCount": 7741
        },
        "role": "user"
      },
      {
        "text": "Actual user prompt or AI response text...",
        "role": "user",
        "tokenCount": 829
      }
    ]
  }
}
```

Each chunk in `chunkedPrompt.chunks[]` is either:
- **`driveDocument`** — a reference to a Google Doc that was uploaded as context. You need to read this separately via `drive.files().export(fileId, mimeType='text/plain')`.
- **`text`** — inline content. This is the actual user prompt or AI response text. Multiple chunks form an alternating conversation (user → AI → user → AI...).

## Reading workflow

```python
import json
from tools.gws_auth import build_service

drive = build_service("drive", "v3")

# 1. Get the raw JSON
content = drive.files().get_media(fileId="<prompt-file-id>").execute()
data = json.loads(content.decode("utf-8"))

# 2. Extract chunks
chunks = data.get("chunkedPrompt", {}).get("chunks", [])

# 3. Process each chunk
for i, chunk in enumerate(chunks):
    if "driveDocument" in chunk:
        doc_id = chunk["driveDocument"]["id"]
        tokens = chunk["driveDocument"].get("tokenCount", "?")
        print(f"Chunk {i}: References Drive Doc {doc_id} ({tokens} tokens)")
        
        # Read the referenced doc
        doc_text = drive.files().export(fileId=doc_id, mimeType="text/plain").execute()
        text = doc_text.decode("utf-8")
        print(text)
        
    elif "text" in chunk:
        txt = chunk["text"]
        print(f"Chunk {i}: Text ({len(txt)} chars)")
        print(txt)
```

## Key pitfalls

- **Huge files**: Some AI Studio prompt files can be 1.3+ MB (1.3M chars) with 100+ chunks. Read selectively — extract chunks that reference Drive docs (those contain uploaded agreements) or chunks with substantive analysis near the end.
- **Truncated output**: When printing in terminal, the output will be truncated. Use `print(text[:5000])` for preview, or write to a file.
- **Referenced Drive docs may also need reading**: The real content (agreements, SHA, amendments) is often in the referenced Google Docs, not inline.
- **model field is not always present**: Older prompts may not have `runSettings.model`. Newer ones (Jun 2026+) use `gemini-2.5-pro` or `gemini-3.1-pro-preview`.

## Common use case: multi-source transaction analysis

When a user asks to understand a complex transaction documented across multiple AI Studio prompts:

1. Find all prompt files in the Google AI Studio folder via `drive.files().list(q=f"'{folder_id}' in parents")`
2. Read each prompt file via `get_media()` + JSON parse
3. Identify all referenced Drive docs (agreements, SHA, amendments)
4. Read those separately (export as text)
5. Cross-reference with email threads (Gmail search)
6. Compile clause-by-clause analysis

This was validated in June 2026 for the BuxRanka/BRDPL/Godrej transaction where 4 AI Studio prompts referenced the SPSSHA, First Amendment, Second Amendment, Board Resolutions, and a 50KB email thread about Premium FAR vs TDR.
