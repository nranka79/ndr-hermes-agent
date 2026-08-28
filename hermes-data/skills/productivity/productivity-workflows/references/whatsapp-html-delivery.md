# WhatsApp HTML Delivery for Long Messages

When a WhatsApp message exceeds the `wa.me` URL character limit (~2048 chars), it gets truncated when sent as a single deep-link URL. The solution is to create an HTML file with a styled preview + WhatsApp button.

## Trigger

- The user asks for a WhatsApp message and you generate a link
- The link's URL-encoded text parameter is very long (approaching or exceeding 1000 characters pre-encoding)
- The message arrives split across multiple Telegram messages because the link was too long
- User says: "The message is splitting, make it as a HTML file with a send WhatsApp button"

## Workflow

### 1. Build the HTML file

Create a single-page HTML with:
- **Styled preview** of the message (WhatsApp chat-bubble style: green `#dcf8c6` background on white card)
- **Clear recipient info** at top (name, phone number)
- **WhatsApp button** — large green (`#25d366`) styled anchor tag
- Message content formatted for easy scanning (numbered lists, bold headings)

```html
<style>
  body { font-family: -apple-system, sans-serif; background: #f0f2f5; padding: 16px; }
  .card { background: #fff; border-radius: 16px; padding: 20px; margin-bottom: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
  .btn-wa {
    display: flex; align-items: center; justify-content: center; gap: 10px;
    width: 100%; padding: 16px; background: #25d366; color: #fff;
    border: none; border-radius: 50px; font-size: 17px; font-weight: 600;
    cursor: pointer; text-decoration: none;
  }
  .btn-wa:hover { background: #20bd5a; }
  .btn-wa svg { width: 22px; height: 22px; fill: #fff; }
  .message-preview { background: #dcf8c6; border-radius: 12px; padding: 16px; font-size: 13px; line-height: 1.5; }
</style>
```

### 2. Generate WhatsApp link with `whatsapp_link` tool

```python
from tools import whatsapp_link
result = whatsapp_link(phone='+9198XXXXXXXX', text='Your long message here...')
# result.url is the wa.me link — embed it in the href
```

**Important:** For very long messages (1000+ chars of text), `whatsapp_link` will produce a link where the text may be silently truncated by WhatsApp's URL limit when opened on mobile. The HTML file is still the right approach — it gives the user a clean preview and the best-effort link.

### 3. Save and deliver

```python
write_file(path='/opt/data/whatsapp_recipient_name.html', content=html_content)
send_message(message='MEDIA:/opt/data/whatsapp_recipient_name.html', target='telegram')
```

### 4. Share the file

The HTML file arrives as a native file attachment in Telegram. The user opens it on their phone, taps the WhatsApp button, and the message opens in WhatsApp pre-filled.

## When to use HTML vs direct link

| Message length | Delivery method |
|---|---|
| Short (<500 chars text, <1500 chars encoded URL) | Direct `whatsapp_link` — send the link in Telegram |
| Long (>500 chars text, approaching URL limit) | **HTML file with button** — always |
| Multiple separate messages to different recipients | HTML file for each, sent separately |

## Template structure

```html
<div class="card header">
  <h1>📋 Title</h1>
  <p>Tap the button below to send</p>
</div>

<div class="card">
  <div class="recipient">
    <div class="label">To</div>
    <div class="name">Recipient Name</div>
    <div class="phone">+91 XXXXXXXXXX</div>
  </div>
  
  <a class="btn-wa" href="https://wa.me/91XXXXXXXXXX?text=..." target="_blank">
    <svg>...WhatsApp icon...</svg>
    Send to [Name] on WhatsApp
  </a>
  
  <div class="message-preview">
    Message content formatted for reading...
  </div>
</div>
```

## Pitfalls

- **WhatsApp URL silently truncates long text.** There's no error — the message just stops. Keep the HTML preview as the reference and note to the user that very long parts may get cut off in the actual WhatsApp app.
- **SVG WhatsApp icon.** Use the standard WhatsApp SVG path for the button icon:
  `<path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967..."/>`
- **Phone number format.** Use `91XXXXXXXXXX` (no +, no spaces) in the wa.me link, but use `+91XXXXXXXXXX` for display.
- **HTML file opens in browser on mobile.** The user taps the button → opens WhatsApp app → message is pre-filled.
