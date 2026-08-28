# Email Extraction → WhatsApp Message

**Trigger:** User says "get the [details] from the email I sent to [person] about [topic] and send a WhatsApp message to [recipient]."

**Workflow (validated June 2026):**

1. **Find the email** — Search Gmail via `gmail.users().messages().list()` with query:
   - `from:ndr@draas.com to:[recipient] [topic keyword]` (for sent emails)
   - `from:[sender] [topic keyword]` (for received emails)
   - Order by date (most recent first is default)

2. **Extract body text** — Get the email, extract `text/plain` or `text/html` part from payload parts tree. Strip HTML tags for clean text.

3. **Parse structured data** — Extract the specific details the user asked for (table data, list items, numbers). Present in a clean format.

4. **Create WhatsApp message** — Follow standard WhatsApp drafting workflow in `references/whatsapp-drafter-full.md`:
   - Use `api.whatsapp.com/send?phone=...&text=...` format
   - Apply full-width ampersand fix (`%26` → `＆` U+FF06)
   - For multi-item data, use a simple bullet list or table format

5. **Deliver** — Send HTML file via MEDIA + clickable WhatsApp link to the user's Telegram.

**Example (June 2026):** User asked for Century Regalia apartment details from an email to Manohar Singh. Extracted 5 units (Aspra 206, Brilla 004, Brilla 206, Crissa 401, Crissa 404) with sizes and types from the email body, then created a WhatsApp message for Dharmesh Ranka.

**Key nuance:** The email body usually contains the most accurate structured data — the PDF attachments are floor plans/images, not text-extractable. Prefer reading the body text over PDF attachments for data extraction.
