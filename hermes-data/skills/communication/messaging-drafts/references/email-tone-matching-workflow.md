# Email Tone-Matching Workflow — Drafting to Match Past Correspondence

## When to Use

**Trigger:** User says "write an email to [name], use the same tone I use with them — check my past emails first" or any variant asking you to match their established communication style with a specific recipient.

The user wants the tone, salutation, sign-off, word choice, and sentence structure to mirror what they've used historically — not a generic corporate email.

## Workflow

### Step 1 — Search for past correspondence

Search the user's Gmail for emails TO and FROM the recipient:

```python
from tools.gws_auth import build_service
gmail = build_service("gmail", "v1")

# Search both directions
results = gmail.users().messages().list(
    userId='me',
    q='from:recipient@email.com OR to:recipient@email.com',
    maxResults=10
).execute()
```

### Step 2 — Extract tone markers from BOTH directions

Read the raw email bodies and identify:

| Marker | What to Look For | Example |
|--------|-----------------|---------|
| **Salutation** | How does the user address them? | "Hi Jeejaji" — familial |
| **Sign-off** | "Regards", "Warmly", "Nishant", "Thanks" | "Regards,\nNishant" |
| **Formality level** | Formal vs casual, contractions, sentence length | Contracted = casual |
| **Sentence structure** | Short vs long, bullets vs paragraphs | Clear sections, bullet lists |
| **Vocabulary** | Specific phrases used repeatedly | "bringing you up to speed", "on board" |
| **Personal touch** | Family references, shared context | "Jeejaji" for brother-in-law |

### Step 3 — The user's sent emails are PRIMARY

The user's own sent messages to this recipient are the main source. The recipient's replies show what they expect, but replicate the USER'S writing style from those threads.

### Step 4 — Present tone analysis + draft, then confirm

Before sending:
1. Tone summary — "You address him as [X], sign off as [Y], tone is [Z]"
2. Full draft
3. Ask for confirmation — "Does the tone match?"

### Step 5 — Only send after explicit "yes"

The user requires: confirm the tone → confirm the draft → then send.

## Real Example (Nishant → Ranjeeth Rathod, Jun 2026)

**Tone extracted:**
- Salutation: "Hi Jeejaji" (familial, respectful)
- Tone: Warm, direct, collaborative
- Language: "I wanted to share", "I think", "Let me know"
- Formatting: Plain text, short paragraphs, `*bold*` for emphasis
- Sign-off: "Regards,\nNishant"

## Attaching PPTX Decks to These Emails

Business opportunity emails often include a .pptx deck from Drive:

- The file is often a native .pptx (not Google Slides)
- Drive `export` with mimeType `application/pdf` raises `fileNotExportable` for .pptx files
- **Fix:** Download the original via `drive.files().get_media()` and attach directly:
  ```python
  from email.mime.base import MIMEBase
  from email import encoders
  part = MIMEBase('application', 'vnd.openxmlformats-officedocument.presentationml.presentation')
  part.set_payload(pptx_bytes)
  encoders.encode_base64(part)
  part.add_header('Content-Disposition', 'attachment; filename="filename.pptx"')
  msg.attach(part)
  ```
- Also include the Drive webViewLink in the email body as a fallback

## Pitfalls

1. **Don't assume generic corporate tone** — The user may use a very different style with family vs vendors. Always check actual emails.
2. **Recipient's style is secondary** — Focus on how the USER writes to them, not vice versa.
3. **Voice-mangled names** — If the recipient name was said in voice, it may not match Gmail records. Cross-check Cc headers in found threads first.
4. **"Send this link as an attachment"** — means attach the FILE, not just include the URL. Download and attach.
