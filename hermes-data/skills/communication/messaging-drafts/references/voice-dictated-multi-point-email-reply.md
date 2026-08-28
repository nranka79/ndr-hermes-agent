# Voice-Dictated Multi-Point Email Reply

**Trigger:** User says "I am going to give you clarification for each of the points she has made" or "draft a reply keeping each of the points in mind" — followed by a long voice dictation addressing 5-15 distinct points.

This is different from composing an email from scratch: the user has an incoming email with numbered questions, and they dictate their answers point-by-point via voice. Your job is to transform that raw dictation into a coherent, professional email.

## Workflow

### Phase 1: Fetch the Source Email

Before writing anything, retrieve the email the user is responding to. This tells you:
- The exact questions/points raised (so you can match the user's dictation to the right point)
- The recipient's name and email
- The subject line for thread continuity
- Any CC'd parties

```python
# Search for the email
results = service.users().messages().list(userId='me', q='from:sender@email.com keyword').execute()
msg_data = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
```

### Phase 2: Map Voice Points to Email Questions

The user will say "For point 1..." or "With respect to..." — map each voice-dictated clarification to the corresponding point in the original email. Number them so you can verify completeness.

### Phase 3: Compose the Draft

Structure each point clearly:
- Use the **same numbering** as the user's voice dictation (not the original email's numbering, unless they match)
- Bold the topic heading: `**1. Compensation Structure**`
- Follow with clear, well-structured prose — not bullet-point dictation style
- Keep each paragraph to 3-5 sentences max
- Use line breaks between points for readability

### Phase 4: Add Polite Bookends

- Opening: Thank them + apologize if delayed
- Closing: Invite further questions, warm regards

### Phase 5: Present for Confirmation

Show the full draft with:
1. **To** address
2. **CC** addresses
3. **Subject** line
4. Full body

Wait for explicit confirmation before sending.

## Color-Coded Replies (Nishant, Jun 2026)

When the user says "reply in blue" or wants his answers differentiated from the original query:
- Use HTML `<div class="reply" style="color: #1565c0;">` for his answers (blue text)
- Keep the original query in a neutral style (`<div class="query" style="background: #f7f9fc; border-left: 3px solid #1a3a5c;">`)
- Structure each point as: original query → user's answer in blue → Drive links → next point
- Save the formatted HTML as a **Gmail draft** (not sent directly) — the user reviews in Gmail before sending

## Inline Drive Links Per Point

Each item that references a document should include an inline Drive link:
```html
✅ <strong>Already available.</strong><br>
📎 <a href="https://drive.google.com/file/d/.../view">Document Name.pdf</a>
```
- Prefix with ✅ for items already completed
- Prefix with ⚠️ for items needing action
- Prefix with ❌ for items not available
- Use emoji + bold for clarity at a glance
- Never just say "attached" — provide the actual clickable link

## Separate Highlighted Section for Specific CC'd Recipient

When a specific person on CC (e.g., Rahul/Vinod Kumar Das completing a legal opinion) has a distinct action item:
- Add a visually distinct `<div class="note-rahul" style="background: #fff8e1; border-left: 4px solid #f9a825;">` block
- Title it: **SPECIFIC NOTE FOR [NAME]:** in bold with warning color
- List numbered action items inside
- Position it after all the point-by-point replies but before the closing

This is separate from the main point-by-point structure — it's a dedicated call-out that grabs the recipient's attention.

## Auto-Adding Extra CC Participants

When the user mentions someone who needs to provide information or be involved (e.g., "I will mark Kishan as well"), add them to the CC list of the email draft:
- Look up their email from memory, contacts sheet, or past sessions
- Add to both the MIME `Cc` header AND the HTML body header
- Mention their role in the relevant point's reply (e.g., "Kishan CC'd to share his photo")

## TMP Folder Staging + Temporary Permissions Workflow

When the user directs you to stage documents for sharing:

1. **Create or identify the TMP folder** on Drive (typically `TMP` or `Temp` folder)
2. **Copy documents** from their original location to TMP:
   ```python
   copied = s.files().copy(fileId='<original-id>', body={'name': 'Renamed.pdf', 'parents': ['<tmp-folder-id>']}).execute()
   ```
3. **Set temporary editor access** for all recipients (1 week):
   ```python
   for email in recipients:
       s.permissions().create(fileId='<tmp-folder-id>',
           body={'type': 'user', 'role': 'writer', 'emailAddress': email},
           sendNotificationEmail=False).execute()
   ```
4. **Reference each file by its TMP copy link** in the email — not the original Drive location
5. Upload any additional KYC/identity documents the user mentions (copy from original Drive location to TMP)

## Clean Duplicate Drafts

When creating a draft, then updating it (e.g., adding a CC), delete the old draft to avoid clutter:
```python
drafts = gmail.users().drafts().list(userId='me', maxResults=5).execute()
for d in drafts.get('drafts', []):
    msg = gmail.users().drafts().get(userId='me', id=d['id']).execute()
    headers = {h['name']: h['value'] for h in msg['message']['payload']['headers']}
    cc = headers.get('Cc', '')
    if 'newrecipient' not in cc.lower():
        gmail.users().drafts().delete(userId='me', id=d['id']).execute()
```

## Critical Note: Internal Review Gate (Nishant, Jun 2026)

For **sensitive or HR-related emails** (offer letters, compensation clarifications, candidate communications), Nishant may ask you to forward the draft to **Roshni (rnr@draas.com)** for review before sending to the external recipient. CC any relevant stakeholders (e.g. Gowri Singh). Use subject prefix: `FW: [Original Subject] - Draft Reply for Review`.

## Example Workflow (Jun 2026)

- Incoming: Neha (candidate) sent 9 questions about offer letter (compensation, probation, working hours, Saturday policy, leave, courses, secondary responsibilities, KPIs)
- Nishant dictated 9 clarifications via voice covering all points
- Draft was composed and presented with To/CC for confirmation
- At his request, it was forwarded to Roshni + Gowri for internal review instead of sending directly
