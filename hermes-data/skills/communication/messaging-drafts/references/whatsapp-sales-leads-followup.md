# WhatsApp — Sales Agent/Broker Follow-Up on Leads with Exclusivity Concern

**Trigger:** User says "send a WhatsApp to [broker/agent]" asking for updates on sales/rental leads across multiple properties, where exclusivity was committed and the user needs pipeline visibility to justify continuing it.

## Pattern Overview

The user has committed exclusivity to a broker for selling/renting multiple properties. Time has passed with limited visible progress. The message needs to:

1. Ask for specific updates per property
2. Request pipeline visibility (leads, visits, conversion potential)
3. Gently remind about exclusivity commitment
4. Express need for data to convince internal stakeholders
5. Offer the broker a chance to provide evidence before exclusivity is reconsidered

## Structure

```
[Per-property update asks]

[General process/timeline ask]

[Exclusivity context — committed to you, but internal pressure]
[Ask for advice/data to make case internally]
```

## Per-Property Updates

Each property should have its own paragraph with:
- Property name
- Type of inquiry (sale / rental / both)
- Specific ask (leads count, pipeline, visits, conversion)

Example:
> **Ranka Iris (sale)** — where do we stand? How many leads have come in, what's the pipeline looking like?

> **Prestige Hermitage** — we're looking for both sale and rental inquiries. Any leads on either front?

## Exclusivity Section — Key Elements

The exclusivity concern must be framed as **collaborative, not confrontational**:

| Element | How to phrase |
|---------|---------------|
| Acknowledge commitment | "we've kept this exclusively with you as I committed" |
| Respect the agreement | "I want to respect that" |
| Explain pressure | "there's pressure internally to get these residual units moving" |
| Gentle consequence | "if it's not working out, I'll have to start talking to others" |
| Ask for help | "what's your advice? Any data you can share that I can use to convince the team?" |
| Buy time | "if I can show some concrete activity, I can make the case internally" |

**Tone:** Collaborative. The message says "help me help you" — not "you're failing."

## Complete Template

```
Sunny, just following up on a few things:

[Property 1] ([sale/rental]) — where do we stand? How many leads have come in, what's the pipeline looking like?

[Property 2] — we're looking for both sale and rental inquiries. Any leads on either front? What's the progress?

[Property 3] ([sale/rental]) — same. Any updates, leads, conversion potential?

It's been some time now, so could you give me a sense of the process and where things stand on each?

[Name], the reason I'm checking in — we've kept this exclusively with you as I committed, and I want to respect that. But there's pressure internally to get these residual units moving. If for whatever reason it's not working out, I'll have to start talking to others.

So I'm asking — what's your advice? Any data or leads you can share that I can use to convince the team to give it another month? If I can show some concrete activity, I can make the case internally.
```

## Delivery

- Generate as a clickable wa.me deep link (phone number from Google Contacts search)
- If phone number not found: search People API, then contacts sheet, then ask user
- Use `api.whatsapp.com/send?phone=...&text=...` format for reliability
- Present the link in plain Telegram text (not in a code block)

## Pitfall — Voice Transcription Correcting Property Details

In one session, the user initially said "Ranka Iris rental inquiry" but corrected to **"Ranka Iris is a sale inquiry"** on review. Always confirm the property's purpose (sale vs rental) with the user before finalizing, especially when derived from voice transcription.

## Pitfall — Multiple Properties Per Message

When a broker handles multiple properties (e.g., Ranka Iris + Prestige Hermitage + Century Regalia), list each as its own bullet/paragraph. Do NOT merge them into one sentence. The user needs per-property visibility.
