# WhatsApp Message Drafting — Nishant's Communication Style

---
parent: gws-automation
purpose: "Draft WhatsApp messages in Nishant's personal communication style by analyzing his past chat history with each recipient"
---

## When to Use

Nishant asks you to draft a WhatsApp message for someone (Jitu Sir, Nagaveni, Nilesh, Anbu, etc.) and wants it in his personal tone. He often says "you have my past chat history with them" or "based on these examples."

## The Workflow

1. **Get the past chat history** — Nishant shares WhatsApp screenshots or pastes chat text. This is the ONLY reliable source for his tone with that specific person
2. **Analyze the tone patterns** from the history (see below)
3. **Draft the message** in that exact style
4. **Confirm the draft** with Nishant before generating the WhatsApp link
5. **Generate the link** using the `whatsapp_link` tool with the correct phone number

## Nishant's Style Patterns (Verified Jun 2026)

### Overall Characteristics
- **Respectful but warm** — uses "Sir" for elders/partners, first names for peers
- **🙏 emoji** — used consistently at end of messages as a softener
- **Soft follow-ups** — "Sorry to keep following up", "Gentle reminder", "I didn't want to bother you"
- **Defers to recipient's convenience** — "Whenever it is convenient for you", "Nothing urgent"
- **Short paragraphs** — one idea per paragraph, never dense walls of text
- **No greetings/signoffs** in short messages — just starts with "Good morning Jitu Sir🙏" and ends with "🙏"

### Style by Recipient Type

**Senior/Mediator (e.g., Jitu Virwani):**
- Opens with "Good morning X Sir🙏"
- Always uses "Sir", many 🙏
- Frames request as seeking guidance, not demanding
- "Whenever it is convenient for you, sir🙏"
- Example: "I believe you have spoken to Manish. I would be keen on meeting you to discuss how we can bring this to a conclusion. I have a few ideas and suggestions which I wanted to share with you."

**Peer/Professional (e.g., Nagaveni at Embassy):**
- Opens with "Hi X, I hope all is well🙏"
- Explains WHY they weren't contacted ("I didn't bother you because I knew X was following up")
- Frames as gentle check-in, not demand
- Offers help: "If there's anything you need from me, please let me know🙏"

**Bank/Service Provider (e.g., Nilesh Prasar):**
- Opens with "Dear X,"
- Direct and clear about what's needed
- Uses bold/caps for critical clarifications
- Professional tone, less emoji

**Colleague/Team (e.g., Anbu):**
- Bold headline for context (**Project Name — Topic**)
- Direct name, no "Sir" or "Dear"
- Numbered bullet list for action items
- Expresses urgency frankly

## Multi-Recipient Team Review Request with Drive Links

When Nishant needs to ask internal team members (Gowri, Roshni, Anbu) to review design options by comparing files in Drive:

- **Tone**: Direct and informal — these are colleagues/wife, not external contacts
- **Structure**: Bold headline for context, then bullet or short paragraph per option
- **Links**: Place Drive links inline after file description — one link per variant
- **Call to action**: Explicit preference request at the end
- **Recipients**: Address both by name at the top
- **Optional bonus content**: If there are related reference files, mention they can also browse the folder

Example draft style (WhatsApp markdown):

```
*Project — Document Topic*

Gowri, Ro — looking at both options for the marketing office:

*1. Option Name (Description)*
[link]

*2. Option Name (Alternative Description)*
[link]

There's also the proposed villa renders in the same folder if you want to reference the villa design language:
[link]

Have a look and let me know which one you prefer. Do we go with this or revert to the original white palette?
```

## Handling Multiple Recipients (Group Message Style)

- Use `*bold text*` for WhatsApp bold (headlines)
- Use `_italic_` sparingly for emphasis
- Multiple links can be placed inline with brief descriptions
- End with a clear question that drives feedback
- Note: This is a DRAFT — Nishant copies and sends it himself via WhatsApp

| Don't | Instead |
|-------|---------|
| Long explanatory paragraphs | Short sentences, one idea per line |
| Apologizing for the draft itself | Just present it and ask "does this look good?" |
| Over-explaining context in the message | Let the message stand on its own |
| "I must clarify", "I have to inform" | Softer: "Just wanted to check", "I believe" |

## Drive Document Sharing via WhatsApp

When the user says "send [person] a WhatsApp with the link to [document]" — a compound operation that spans Drive permissions + WhatsApp messaging:

### Full Workflow

1. **Find the document** — search Drive by user's description (name, project, keyword)
2. **Verify it's the right document** — cross-reference with email threads if multiple similar files exist
3. **Check current permissions** on the file before adding new ones:
   ```python
   perms = drive.permissions().list(fileId=pdf_id, fields='permissions(id, type, role, emailAddress)').execute()
   ```
4. **Set view-only access** for the recipient if not already granted:
   ```python
   new_perm = {'type': 'user', 'role': 'reader', 'emailAddress': 'recipient@example.com'}
   drive.permissions().create(fileId=pdf_id, body=new_perm, sendNotificationEmail=False).execute()
   ```
5. **Clean up** — delete any obsolete drafts, duplicate files, or working versions the user no longer needs
6. **Generate the WhatsApp link** with the document's `webViewLink` or `webContentLink` embedded in the message text
7. **Present the link to the user** as a clickable wa.me URL they can open from their phone

### Message Template for Document Sharing

```
Hi {name}, please find the link to {document description}:

{drive_link}

You have view-only access on Drive.

Regards,
Nishant
```

## Legal Document Procurement Request (Third-Party — Scan/Drive Share)

When asking someone else (colleague, lawyer, vendor) to share scanned documents or a Drive link that they hold:

**Style rules:**
- Direct opening, no pleasantries — "Hi [Name], regarding [project]..."
- Acknowledge what the person's relationship is to the documents ("the legal opinion you prepared", "the original files that were scanned")
- List specific missing documents with registration numbers and dates — be precise so they can find them quickly
- Offer a simple ask: "share your Drive link" or "if you have these scanned, please share"
- Close with "Thanks!"
- No "hope you're well", "how are you", "sorry to bother" — Nishant's stated preference (confirmed Jul 2026)

**Template:**

```
Hi [Name],

Regarding the [Project Name] ([Survey Number], [Village]) legal due diligence — I'm trying to locate a few specific documents from the scanned set. Could you check if these are available on your end?

1. [Doc type] dated [Date] (Reg No. [Number]) — [brief description of parties]
2. [Doc type] for the period [dates] — [notes]
3. [Doc type] — [notes]

If you have these scanned or a Drive link to the full set, please share. Thanks!
```

**Recipient-specific variations:**
- **Conveyancing lawyer who wrote the opinion** — "You would have reviewed all these for the opinion you prepared on [property] — do you have them in scanned form?"
- **Colleague who scanned the originals** — "I remember the original files were scanned but I can't find [specific items] on Drive. Can you share whatever digitized docs you have?"
- **Vendor's team** — "Can you check if your records include [specific items]?"

## Common Variations

- **"Send [person] the WhatsApp"** — assume standard Drive document sharing unless told otherwise
- **"Share it and send them [person] a WhatsApp"** — set permissions + share link
- **"Give them access and message them"** — same compound operation

### Pitfalls

- **Do NOT share sensitive documents publicly** — use user-level permissions (`type: 'user'`), not `type: 'anyone'`
- **Set `sendNotificationEmail=False`** — the WhatsApp message IS the notification; sending both is redundant and annoying
- **Check existing permissions first** — if the person already has access, don't add a duplicate permission entry
- **Verify the recipient's email domain** — @draas.com for internal staff, personal/Gmail for external consultants. Use People API or Gmail search to confirm before adding
- **Delete obsolete drafts BEFORE sharing** — the user doesn't want the recipient to see draft/working versions alongside the final document

### WhatsApp Link Generation (No Dedicated Tool)

There is no `whatsapp_link` tool available. Generate wa.me URLs manually:

```
https://wa.me/91{phone_digits}?text={url_encoded_message}
```

Steps:
1. Strip country code prefix (e.g. `+91`) — just digits after `91`
2. URL-encode the message text
3. Assemble the full URL

### WhatsApp Link — & (ampersand) Encoding Breaks Links

URL-encode the message text manually. The `&` character becomes `%26` in the URL. On several platforms (Telegram, mobile browsers, desktop WhatsApp), the `%26` in the wa.me redirect chain causes the link to fail — the URL breaks before the message is sent.

**Fix:** Replace `&` with `and` (or the word for the ampersand) in the message text before URL-encoding:

```
# DON'T — & encoded as %26, link breaks on some platforms
https://wa.me/9198xxxxxxx?text=Need%20A%20%26%20B%20details

# DO — write out 'and' instead of '&'
https://wa.me/9198xxxxxxx?text=Need%20A%20and%20B%20details
```

This applies to ALL characters that URL-encode as `%XX` — but `&` is the most common offender because it's an HTML/URL parameter separator and interferes with the redirect chain. Other safe alternatives: spell out symbols, avoid the character entirely, or use a simple dash/comma where possible.

## Phone Number Resolution Order

When generating the WhatsApp link, follow the contact-phone-lookup skill (this is the authoritative source):

1. People API (Google Contacts — "My Contacts" only)
2. NDR DRAAS Google contacts sheet (`1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g`)
3. Old contacts sheet (`1KQe9CQyfpLXR16hYFLWNwwJ0NPEsv2q0PQwL4sEy8vU`) — fallback
4. Memory
5. Session history (check for previous WhatsApp message threads)
6. Ask user directly — only after all above exhausted

**CRITICAL:** The user will express frustration ("What happened??") if you ask for the number without first exhaustively searching all sources. Do steps 1-5 every time before going to step 6.

If user says the number is wrong, show raw search results from each source (source name + query + returned data) and ask which source they trust or if they can share the correct number.
