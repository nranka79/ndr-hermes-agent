# Share Own Contact Details via WhatsApp

**Trigger:** User meets someone (at a meeting, RLDA office, etc.) and didn't have a visiting card. Asks to send the person a WhatsApp message containing their own contact details.

## Workflow

1. **Who is the recipient?** Resolve name + phone number from visiting card photo, contacts sheet, People API, or memory
2. **What details to share?** The user typically provides these verbally — if uncertain, ask
3. **Draft the message** — keep it natural and brief:

```
Hi [Recipient Name],

Pleasure meeting you today at [location]! I didn't have my card on me, but here are my details:

[Full Name]
[Company Name]
[Office Address]
📧 [email]
📱 [phone number]

Looking forward to staying in touch. Do let me know if there's anything further from our side on [topic discussed].

Warm regards,
[Name]
```

4. **Resolve the user's own phone number** — check `contact-phone-lookup` skill, memory, or ask the user directly. Do NOT assume you have it.
5. **Generate WhatsApp deep link** — use `api.whatsapp.com/send?phone=...&text=...` format
6. **Deliver as clickable link** in plain Telegram text, not code block

## Key Details to Collect

| Detail | Source |
|--------|--------|
| Recipient name | User's voice / visiting card |
| Recipient phone | Visiting card OCR / contacts |
| User's name | Known (Nishant Ranka) |
| User's company | Known (DRA Realty Private Limited) |
| User's office address | User stated verbally; verify if uncertain |
| User's email | Known (ndr@draas.com) |
| User's phone | Check memory/contacts skill; ask if unavailable |

## Pitfall — User's Own Phone Number May Not Be Stored

The user may not have themselves saved as a contact in Google Contacts or the contacts sheet. If you cannot find their number:
- Check `contact-phone-lookup` skill (memory table often has it)
- Check past session transcripts
- Ask the user directly — they know their own number

## Worked Example (Jun 2026 — Shravan Mahipal K, Bagmane Group)

Nishant met Shravan at the RLDA office. Shravan had identified the Bangalore RLDA plot. Nishant didn't have his card. Details shared:
- Nishant Ranka, DRA Realty Private Limited
- Prism Towers, Kalinga Road, Bangalore
- ndr@draas.com
- Phone number (from contact-phone-lookup skill memory)
