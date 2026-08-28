# Gmail HTML Email Draft — Inline CSS Pattern

Gmail **strips `<style>` tags from the `<head>`** of HTML emails. All CSS must be inlined on individual HTML elements. This applies to both drafts saved via the Gmail API and sent emails.

## The Pattern

```python
import sys
sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

gmail = build_service('gmail', 'v1')

html_body = """<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="font-family: 'Segoe UI', Arial, sans-serif; background: #f5f5f0; margin: 0; padding: 20px;">
  <!-- Everything uses inline style because Gmail strips <style> tags -->
  <table width="600" cellpadding="0" cellspacing="0" style="background: #ffffff; border-radius: 8px;">
    <tr>
      <td style="background: #1a3c34; padding: 28px 32px; color: #f5f0e8;">
        <h1 style="margin: 0; font-size: 22px;">Title</h1>
      </td>
    </tr>
    <tr>
      <td style="padding: 32px; font-size: 15px; line-height: 1.6; color: #333;">
        <p>Body text here.</p>
      </td>
    </tr>
  </table>
</body>
</html>"""

plain_text = """Plain text fallback version."""

# MIMEMultipart with both alternatives
message = MIMEMultipart('alternative')
message['To'] = 'recipient@example.com'
message['Cc'] = 'cc@example.com'
message['Subject'] = 'Subject Line'

part1 = MIMEText(plain_text, 'plain')
part2 = MIMEText(html_body, 'html')
message.attach(part1)
message.attach(part2)

# Save as draft
raw = base64.urlsafe_b64encode(message.as_bytes()).decode().rstrip('=')
draft = gmail.users().drafts().create(userId='me', body={'message': {'raw': raw}}).execute()
print(f"Draft ID: {draft.get('id')}")
print(f"Open: https://mail.google.com/mail/u/0/#drafts")

# To send directly instead of saving as draft:
# sent = gmail.users().messages().send(userId='me', body={'raw': raw}).execute()
```

## Critical Rules

### 1. Inline CSS — No `<style>` tag
Gmail's HTML sanitizer **removes** `<style>` blocks from `<head>`. Put all styles as `style="..."` attributes on the actual HTML elements.

```html
<!-- ❌ WON'T WORK in Gmail -->
<style>
  .header { background: blue; }
</style>

<!-- ✅ WORKS -->
<td style="background: blue; padding: 20px;">
```

### 2. Table-based layout
Gmail renders in a limited CSS environment. Use `<table>` layout (not flexbox/grid) for reliable rendering across Gmail clients (web, iOS, Android).

### 3. Always include a plain text alternative
`MIMEMultipart('alternative')` with `MIMEText(text, 'plain')` first, then `MIMEText(html, 'html')`. The email client shows whichever it supports. Without the plain text part, spam filters may penalize the email.

### 4. Colored badges / status indicators
Use inline-styled `<span>` elements for tags/badges:
```html
<span style="background: #f8d7da; color: #721c24; padding: 2px 8px; border-radius: 3px; font-size: 11px; font-weight: 700;">MISSING</span>
<span style="background: #d4edda; color: #155724; padding: 2px 8px; border-radius: 3px; font-size: 11px; font-weight: 700;">DONE</span>
<span style="background: #fff3cd; color: #856404; padding: 2px 8px; border-radius: 3px; font-size: 11px; font-weight: 700;">PENDING</span>
```

### 5. Numbered checklists with visual hierarchy
Structure long checklists with section headings and priority badges:
```html
<tr>
  <td style="padding: 6px 0;" colspan="2">
    <span style="background: #f8d7da; color: #721c24; ...">HIGH PRIORITY</span>
  </td>
</tr>
<tr>
  <td style="padding: 8px 0; border-bottom: 1px solid #eee; width: 30px; vertical-align: top; color: #a02c2c;">1.</td>
  <td style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>Item name</strong> — description</td>
</tr>
```

## When to use this pattern

Use this pattern when the user says:
- "Draft an email using HTML CSS so it's clear"
- "Create a nice readable presentable email"
- "Format it with HTML"
- "Keep it short and sweet but nicely formatted"

For **simple text-only emails** (no formatting needed), use a plain `MIMEText` — HTML is unnecessary overhead.

## Nishant's preference (DRAAS)

Nishant explicitly asks for **HTML/CSS formatted emails** for multi-item structured updates (checklists, reports, pending items). Keep the email **short and sweet** — the HTML formatting handles visual hierarchy (color-coded priorities, tables, section headers). Do not make it lengthy; the formatting should make the content scannable, not padded.

### Layout recipe (for checklists/pending items emails):
1. **Header** — dark background (gn: #1a3c34), white text, project title
2. **Body** — white card, grey background (#f5f5f0) for contrast
3. **Section headers** — colored badge spans (red = high priority, amber = medium, green = done, blue = action)
4. **Numbered items** — subtle table with left number, right content, light borders
5. **Footer** — muted grey, centered
