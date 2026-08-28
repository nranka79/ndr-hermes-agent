# WhatsApp Option Comparison Draft — "Which Option Do You Prefer?"

**Trigger:** User wants a WhatsApp message asking one or more recipients to compare two (or more) design/plan options and give feedback (e.g., "original render vs. GPT-enhanced earthy render" for a marketing office).

## Workflow

### Phase 1 — Resolve Each File to a Drive Link

Ensure all files being compared are on Google Drive with stable, shareable links:
- Original file from architect/vendor
- Variation/GPT-enhanced version
- Any supporting renders for context (e.g., villa renders to show the overall design language)

### Phase 2 — Gather Recipient Info

- Names: Confirm correct spelling (Gowri, NOT Gauri; Roshni/Ro, NOT Roshini/Rochney)
- Emails: Needed for Drive permission setting (editor access)
- Phone numbers: Needed for WhatsApp link

### Phase 3 — Set Drive Permissions Before Sharing Links

Send links that WORK when the recipient taps them. Set editor (writer) permission BEFORE generating the message:

```python
for email in [recipient1_email, recipient2_email]:
    drive.permissions().create(
        fileId=FOLDER_ID,
        body={'type': 'user', 'role': 'writer', 'emailAddress': email},
        sendNotificationEmail=False
    ).execute()
```

Set on the PARENT folder so all subfolders and files are accessible.

### Phase 4 — Draft the Message

Structure:
1. **Greeting + ask:** "Could you please look at both options and let me know which you prefer?"
2. **Option 1 (Original):** Brief description + Drive link
3. **Option 2 (Variation):** Brief description + how it was created + Drive link
4. **Your opinion:** State your preference caveat (e.g., "I'm not sure about the earthy color — we can go back to white which is what the villas will be")
5. **Additional reference:** Link to the full folder so they can browse related renders
6. **Call to action:** "Let me know your feedback on which direction works better"

### Phase 5 — Delivery Format

Present the message in a **markdown code block** (triple backticks, no language tag) for the user to copy-paste into WhatsApp. Do NOT generate a deep link — the user typically wants to:
- Review the message before sending
- Possibly add their own framing/context
- Send to multiple people individually

### Message Template

```
Roshni and Gowri — could you please look at both options for the [Project] [Asset] renders and let me know which one you prefer?

Option 1 (Original by [Architect Name]):
[Drive Link]

Option 2 ([Description of Variation]):
[Drive Link]

The [variation] was an alternate I asked [tool/method] to create from [Architect]'s original to explore a different look. But I'm not completely sold on the [specific feature] — we can go back to the [original direction] which is what our [other reference assets] will be.

Also take a look at the [related renders] we already have, they're in the same folder:
[Drive Folder Link]

Let me know your feedback on which direction works better for [Project].
```

### When to Use This Pattern

- Design option comparison (building renders, villa designs, entrance concepts)
- Marketing collateral review (brochure layouts, logo options, branding)
- Any "Option A vs Option B" decision where you want feedback from specific stakeholders

### When NOT to Use

- **Single option review** — use a direct message pattern instead
- **User wants to send directly** — generate a deep link instead of code block
- **More than 3 options** — consider an HTML card with all options listed

### Pitfall — Recipient Has Multiple Emails/Names

Gowri Singh (gsingh@draas.com) — NOT "Gauri". Corrected in session (Jun 2026). Always verify name spelling. Roshni Ranka (rnr@draas.com) — addressed as "Ro" by Nishant. Misspellings: Roshini, Rochney.

### Pitfall — Verify Uploaded File Before Sharing Links (Jun 2026)

**Problem:** Two rounds of wrong links were sent because the agent uploaded a file that was NOT the user's image — it was a different cached image from the session. The user had to correct twice.

**Root cause:** User-uploaded images (temporary files in /tmp) are cleaned up between session turns. When the agent tried to process and convert the image, the temp file was gone and a stale cached image was used instead.

**Fix — always verify the file you're about to share:**

1. **Confirm the filename matches the content** — Before sharing a Drive link, state what you're about to share and how you derived it from the user's input. "I'll upload the GPT-enhanced image you shared as `{filename}` — confirming this is the file you shared above."
2. **For user-uploaded images** — Process the image IMMEDIATELY when the user shares it (same turn). Do not defer conversion/upload to a later response. Temp files are not guaranteed to persist between responses.
3. **If the temp file is already gone** — Ask the user to re-upload. Do NOT guess or substitute a different file.
4. **After upload, confirm the link works** — Tap or open the Drive link yourself (via browser_use_cloud if needed) to verify it shows the expected content before sending to the user.
5. **Deliver links one at a time** — When the user corrected a link, share only the corrected link + ask if it looks right, rather than sending a full batch of links again. Fewer links = fewer failure points.

**Key lesson:** An uploaded image may look correct in vision analysis but the temp file path may belong to a different file by the time you act on it. Handle image processing in the same response turn.
