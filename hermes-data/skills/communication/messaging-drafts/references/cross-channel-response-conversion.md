# Cross-Channel Response Conversion — WhatsApp → Email

**Trigger:** User says "I already responded to [person] in the WhatsApp group / via WhatsApp. Now he's sent an email with the same queries. Draft an email response based on what I already said."

## Workflow

### Phase 1 — Find the previous response

The user has already responded to the same person/queries via another channel (typically WhatsApp group). You need to find that response to reuse the content.

**Search order:**

1. **session_search** — Search past sessions for the person's name + "WhatsApp" or the project/context name:
   ```python
   results = session_search(query="Raghu Ranka Amber WhatsApp response", limit=5)
   ```
   Look for the assistant's response that contains the full WhatsApp message text.

2. **Current session scroll** — If the WhatsApp response was from an earlier turn in the same session, scroll back through the session history using `session_search` with the person's name and topic.

3. **Check for saved files** — The previous response may have been saved as an HTML file, text file, or similar under `/data/hermes/document_cache/` or `/data/hermes/drafts/`.

### Phase 2 — Understand the email

1. **Find the email** — Search Gmail for the sender's email address. Voice transcriptions mangle email addresses (e.g., "RMIVAR" → `rmiyer@bitanz.com`). Try multiple queries:
   - `q="Raghu Iyer OR oz.iyer@gmail.com OR rmiyer OR RMIVAR"`
   - If name search fails, search recent emails (`newer_than:2d`) and look for the person's name in From: headers.

2. **Extract the full email body** — Use `format='raw'` + base64 decode + `email.message_from_bytes()` to get the full plain text body.

3. **Parse the points** — The email typically lists numbered queries/concerns. Count them, understand each one.

### Phase 3 — Reconcile & draft

The WhatsApp response may have covered only some of the points in the email. The email may include NEW points not addressed in the WhatsApp chat.

**Reconciliation approach:**

| WhatsApp covered | Email point | Action |
|---|---|---|
| ✅ Addressed | Same point repeated | Reuse WhatsApp content in email format |
| ✅ Addressed but partially | Same point with new sub-questions | Extend WhatsApp response with new answers |
| ❌ Not addressed | New point | Draft fresh response |
| ❌ Not addressed | Timing/process question (e.g., "execute after RERA") | Acknowledge and confirm |

**Draft rules:**

1. **Lead with the most important point** — not chronological order of the email. If the user's WhatsApp response was structured around 6 key themes, keep that structure and add new points after.
2. **Use the same tone** — The WhatsApp response had a specific tone (constructive, partnership-oriented, never defensive). Carry that tone into the email.
3. **Separator lines** — Use `━━` (U+2501 U+2501) dividers between point sections for readability, same as the WhatsApp format.
4. **Sign off professionally** — Full name, title, company. The WhatsApp response may have omitted a signature; the email should include one.
5. **Confirm before sending** — Show the full draft to the user on Telegram before calling `gmail.send()`. Let them review and modify.

### Phase 3a — Opening Brief Pattern

When the user has already responded via WhatsApp/Telegram before seeing the email, add an **opening brief** acknowledging this:

> Dear [Name],
>
> I didn't realise you had emailed — I had already responded to your points yesterday on our [WhatsApp group/Telegram]. I just happened to see this email now, so I'm providing the same response here for ease of reference.
>
> You can read it on either platform, depending on your convenience. Trying to keep it as brief as possible so it's a quick read for you. I've also included a note clarifying [topic] with clause references.
>
> And as always, if there are still pending doubts after this, better to get on a call and clarify so we can move ahead.

**When to include:** Always, when the user says "I already responded on [other channel]" about the same topic.

### Phase 3b — Clause Reference Notation

When the email involves legal/commercial agreements (JDA, SSA, FAR, RERA), the user expects **explicit clause references** to be called out:

- **Mention the specific clause number and document:** e.g., "Clause 5.6 of our Principal JDA (16-Aug-2025)"
- **Quote the clause provisions** verbatim or paraphrased in bullet points
- **State clearly whether the clause applies or doesn't apply** to the current situation, with reasoning
- **Separate the clause analysis** as its own numbered point with a heading like `━━ 7. [Topic] (Clause X of Document Y) ━━`

Example (from June 2026 Raghu Iyer email):
```
━━ 7. Premium FAR Costs (Clause 5.6 of Principal JDA dated 16-Aug-2025) ━━

I recognise that Clause 5.6 of our Principal JDA (16-Aug-2025) provides for 
Premium FAR differently. That clause states:
• The Landowner has the sole right to procure Premium FAR / TDR rights at their own cost
• Any additional SBUA created is shared 50:50
• The Developer bears approval and construction costs of the additional area

However — that clause addresses a scenario where Premium FAR rights are purchased 
from the government. That's not what happened here. Our 1.97 was achieved through 
design optimisation within existing provisions — no Premium FAR rights were procured. 
So Clause 5.6 is simply not triggered in this case.
```

### Phase 4 — Send (Reply All)

**CRITICAL:** Check the original email's To: and Cc: fields. The user expects **Reply All** so that everyone CC'd on the original email also receives the response. Use `mime_msg['Cc']` to include all original CC recipients.

```python
from email.message import EmailMessage
import base64

msg = EmailMessage()
msg["From"] = "Nishant Ranka <ndr@draas.com>"
msg["To"] = "rmiyer@bitanz.com"
msg["Cc"] = "Manohar Singh <msingh@redsoul.co.in>"  # Include ALL original CC recipients
msg["Subject"] = "Re: Original Subject"
msg["In-Reply-To"] = "<original-message-id>"
msg["References"] = "<original-references>"
msg.set_content(body_text)

raw_b64 = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8').replace('+','-').replace('/','_').replace('=','')
gmail.users().messages().send(userId='me', body={'raw': raw_b64, 'threadId': '<thread-id>'}).execute()
```

**How to get CC recipients from the original email:**
```python
# Get the original email's metadata
orig_msg = gmail.users().messages().get(userId='me', id='<orig-id>', format='metadata',
    metadataHeaders=['From','To','Cc','Subject','Date']).execute()
headers = {h['name']: h['value'] for h in orig_msg['payload']['headers']}
cc_recipients = headers.get('Cc', '')
# Use this in the reply's Cc header
```

**Subject line:** Use `"Re: Original Subject"` — matching the original email's subject line so Gmail threads them correctly. The subject may include a prefix like "Subject: Subject: ..." which is a Gmail quirk from IMAP — preserve it as-is.

## Real Example (June 2026)

- **User** sent WhatsApp response in Ranka Amber group addressing 6 points from Raghu Iyer
- **Raghu then sent** email with 10 numbered points (6 from WhatsApp + 4 new: Premium FAR costs, stilt plan version, parking count, RERA timing)
- **Workflow:** session_search → found WhatsApp text → extracted Raghu's email from Gmail → reconciled 6+4 = 10 point response → drafted email → confirmed with user
- **User then provided corrections/enhancements** to points 6-10 via chat — these were incorporated into the email before sending (the WhatsApp content was the foundation, but the user refined several points in the draft)
- **Sent via Reply All** — original email had Manohar Singh on CC

## Pitfalls

- **Voice transcription mangling email addresses:** "RMIVAR" = `rmiyer@bitanz.com`. Always search by partial and try domain variations (`bitanz.com`, `gmail.com`, etc.).
- **WhatsApp response may have been in a DIFFERENT session:** The original WhatsApp drafting may be in a session from days ago. Use `session_search` with date range if needed.
- **The user may have iterated on the WhatsApp content:** The actual sent message might differ from the first draft. Look for the final version the user confirmed, not the initial proposed draft. In some cases, the user will provide **additional refinements** to the WhatsApp content when converting to email — watch for this in follow-up messages.
- **Email may be a Reply to an earlier mail:** Check threadId and In-Reply-To headers. Use the correct thread when sending the reply.
- **Don't forget Reply All:** Check if the original email had CC recipients. The user expects you to include them.
- **User may correct specific points in the draft** — especially for legal/commercial content (clause interpretations, FAR calculations, parking counts). Present the draft, let the user refine, then send the final version. Do not send the first draft without user approval.
