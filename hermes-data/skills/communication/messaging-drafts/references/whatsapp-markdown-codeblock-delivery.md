# WhatsApp Markdown — Code Block Delivery Pattern

## Trigger

User asks you to draft a WhatsApp message. Before delivering, always check: does the message use WhatsApp markdown (`*bold*`, `_italic_`, `~strikethrough~`, ````code````)?

If yes, deliver in a **markdown code block** (triple backticks with no language tag) so that when the user copies and pastes into WhatsApp, the markdown formatting auto-renders.

## Why

WhatsApp supports markdown, but if you deliver the message as plain Telegram text, the markdown syntax may render incorrectly or not at all when pasted. A code block preserves the raw markdown syntax so the user can copy-paste directly into the WhatsApp chat window and see bold/italic/strikethrough applied automatically.

## Template

```
```
*🎉 HEADLINE — ALL CAPS, EMOJI*

Dear [Audience],

Body paragraph with *bold* emphasis on key words.

• Bullet point with *key term*
• Another point

Closing line with 🙏

Warm regards,
[Name]
```

## Do NOT
- Use Telegram markdown (e.g. `**bold**`) — WhatsApp uses single `*` for bold
- Deliver without a code block — the markdown will be eaten by Telegram's rendering
- Send as a file or HTML card — this is for plain text messages the user copies

## When to use
- WhatsApp group announcements (OC celebrated, project updates, etc.)
- One-to-one WhatsApp messages with formatting
- Any message where the user will copy-paste into WhatsApp and expects formatting to survive

## Multi-message delivery (2+ messages)

When the user asks for **more than one separate WhatsApp message** (e.g. a main response + a follow-up on a specific topic), **do NOT send them as separate code blocks in Telegram** — Telegram splits them across messages, and the user can't easily copy both.

Instead, create an **HTML file** with both messages as copy-able code blocks:

1. Create an HTML file with one card per message, each containing a `<pre>` block with the message text and a JavaScript Copy button (`navigator.clipboard.writeText()`)
2. Send the file via Telegram: `send_message(message="MEDIA:/path/to/file.html")`
3. The user opens the HTML in their browser and clicks Copy for each message

**Fallback if MEDIA delivery is blocked:** If `media_delivery_allow_dirs: []` prevents MEDIA from working, present each message as a standalone code block in Telegram with a clear label. The formatting survives copy-paste either way.

## Multi-point structured responses

For business partner / landowner messages covering 5-15 points (e.g. SSA review, JDA clarifications), see `references/whatsapp-multi-point-response.md` for the full format — point-by-point structure with `━━` separators, bold headings, and calibrated tone.