# Sharing Google Drive Document Links via WhatsApp

## Pattern

When the user asks to send project documents to someone via WhatsApp, the workflow is:

1. **Find the documents on Drive** — search with the project's current name AND legal/alternate names (e.g. "Ranka Udaya" = "Serenity Estates" in legal docs)
2. **Get the public/anyone-with-link share links** from Drive (webViewLink)
3. **Compose a WhatsApp message containing the Drive links** as clickable URLs
4. **User separately downloads the files** and forwards them through other channels — the WhatsApp message is just the notification + links

## Why Links Instead of Attachments

- wa.me URLs have strict length limits — file attachments cannot be embedded
- The user's workflow: "I will download it from the link and send it separately after I send the message"
- The recipient gets the links to preview, and the user sends the actual files through parallel channels (email, Telegram, etc.)

## WhatsApp Message Structure for Document Sharing

### External / Professional Contacts (e.g. ICICI technical team)
```
Hi [Name], as discussed, sharing the documents for [Project]:

1. [Doc Type 1]: [Drive Link]

2. [Doc Type 2]: [Drive Link]

Let me know if you need anything else.
```

### Colleagues (can be more direct)
```
[Name], sharing the [Project] documents you asked for:

1. [Doc Type] → [Drive Link]
2. [Doc Type] → [Drive Link]

Check and confirm.
```

## Drive Search Tips for Project Documents

- **Search with multiple name variants**: A project may have a marketing name (e.g. "Ranka Udaya") and a legal name (e.g. "Serenity Estates"). Search both.
- **Look in structured subfolders**: Many projects have organized folders like:
  - `02_Approvals/` — RERA certificates, HNDT/DTCP approval letters, approved layout plans
  - `04_Sanction_Drawings/` — sanctioned layout plans, building plans
  - `05_Execution_Documents_and_Drawings/`
- **Check document dates**: When multiple versions exist (e.g. two RERA orders dated Apr & May), prefer the most recent one.
- **Use `gws-auth build_service('drive', 'v3')`** for programmatic searching with multiple query patterns.
