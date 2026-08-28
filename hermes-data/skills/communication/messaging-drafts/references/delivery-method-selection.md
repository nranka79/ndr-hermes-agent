# Delivery Method Selection — WhatsApp First, Email Only When Explicit

## Decision Rule

**When the user says "create a message for [contact]" with no delivery method specified, default to WhatsApp link. Only create a Gmail draft when the user explicitly says "email" or "send an email."**

Confirmed from user correction (Nishant Ranka, Jul 2026):
- User asked me to "create a message for Rahul/Vinod" about Form 43J findings
- I created a Gmail draft → user immediately corrected: "Not email, I got a whatsapp message for him"

## Rationale

For external contacts (vendors, lawyers, partners, consultants), WhatsApp is the primary communication channel. Email drafts are reserved for:
- Formal document delivery with attachments
- Multi-party thread communication where threading matters
- Cases where the contact specifically uses email (bank officers, regulatory bodies, government officials)
- When the user explicitly says "draft an email" / "send an email"

## Workflow

1. **Look up the contact's phone number** — Use `contact-phone-lookup` skill or search the NDR DRAAS Google contacts sheet. Check the verified phone table.
2. **Check if alternative channels exist** — If the contact has both a phone and email, prefer WhatsApp unless the user said "email"
3. **Compose the message** per the tone rules (see `references/whatsapp-text-formatting.md`)
4. **Generate wa.me link** and deliver to user as a clickable Telegram link
5. **Only fall back to Gmail draft** if the user corrects you or explicitly says "email"

## Pitfalls

- **Don't auto-create email drafts** — When the user says "message" or "send this to [name]" without specifying, WhatsApp is the default
- **Don't ask "email or WhatsApp?"** — Just default to WhatsApp. The user will correct you if they want email
- **But DO create email drafts when told "email"** — The rule is WhatsApp-first, not WhatsApp-only. If the user says "draft an email," create the draft.
- **Document delivery exceptions** — If the message includes file attachments that can't be sent via WhatsApp link text, email may be necessary even if not specified. In this case, say: "I'll create an email draft since this needs document attachments — sending via WhatsApp link won't work for attachments."
