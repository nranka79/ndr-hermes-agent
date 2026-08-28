# Ranka Udaya — Client Outreach (WhatsApp)

Project-specific WhatsApp message template for daily client outreach on the **Ranka Udaya** residential project. Part of the `messaging-drafts` umbrella — see `SKILL.md` for the full WhatsApp drafter workflow (wa.me link generation, URL encoding, confirmation flow).

## Trigger

User says: **"Ranka Udaya client [name] [number]"** or similar pattern for daily outreach from Kudiyama (Bharat Hawaldar, DRAAS real estate).

## Standard Message Template

When user names a client and contact number, draft a WhatsApp message with:

**3 Links (always included):**
- 🏠 **Virtual Tour:** https://digitour.housing.com/droneview/ranka_udaya
- 🌐 **Project Details:** https://share.google/Q80Ehv6gG0QX4sEK6
- 📍 **Location Map:** https://maps.app.goo.gl/RTjczx8dPYQXaYQE6

**Message structure:**
```
Hi [Name], thank you for your enquiry on [Source]! 🙏

Please find below the complete details for Ranka Udaya — our premium residential project:

🏠 Virtual Tour: [link]
🌐 Project Details: [link]
📍 Location Map: [link]

Please go through the project details and let me know if you'd like to schedule a site visit or need any more information. Happy to help! 😊
```

## Salutation Rules
- Address client as **"Sir"** or **"Ma'am"** based on gender — ask user if unclear
- Example: "Hi Jai Prakash Sir," or "Hi [Name] Ma'am,"

## Per-Client Customization
- **Housing.com enquiry** → mention "thank you for your enquiry on Housing.com"
- **Referral** → "Thank you for your interest in Ranka Udaya — [Referrer Name] suggested we connect"
- **Direct visit/inquiry** → "Thank you for your interest in Ranka Udaya"
- Adjust tone based on context shared by user

## Sending

Follow the standard WhatsApp drafter flow from `references/whatsapp-drafter-full.md`:
1. Generate wa.me link with URL-encoded message
2. **Ampersand in URLs** — use full-width ampersand ＆ (U+FF06), URL-encoded as `%EF%BD%86`, not `%26`. (This is a per-URL quirk seen in the Google Maps link above; standard wa.me encoder mishandles it.)
3. Present link to user for confirmation before sending

## Related

- `messaging-drafts/references/whatsapp-drafter-full.md` — base WhatsApp drafter (link generation, formatting, context awareness)
- `messaging-drafts/references/whatsapp-url-encoding-research.md` — URL encoding quirks
- `messaging-drafts/references/whatsapp-markdown-codeblock-delivery.md` — markdown delivery for copy-paste
- `real-estate-leads-tracking` — pull portal leads (MagicBricks, Housing.com, 99acres) before outreach
