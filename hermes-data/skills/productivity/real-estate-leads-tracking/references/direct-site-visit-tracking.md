# Direct Site Visit Tracking

When a lead walks in directly to a project site (not through a portal), log them in a lightweight tracking sheet.

## Sheet Structure

| Column | Header | Type | Notes |
|--------|--------|------|-------|
| A | # | Auto-number | Sequential |
| B | Visit Date & Time | Free text | e.g. "06 Jun 2026" |
| C | Name | Free text | Lead's name |
| D | Contact Number | Phone | wa.me hyperlink for WhatsApp |
| E | Remarks | Free text | "Direct site visit. Looking for 2 plots." |

## Creation Pattern

1. Create xlsx with openpyxl
2. Upload to Drive root with mimeType conversion → Google Sheets
3. Share the link in Telegram

## User Preference

- Bharat (sales1.blr@draas.com): upload to **Drive root**, not project folders
- Phone numbers get clickable WhatsApp links: `https://wa.me/91{phone}`
- Add date/time column — the user always wants to know *when* the visit happened
