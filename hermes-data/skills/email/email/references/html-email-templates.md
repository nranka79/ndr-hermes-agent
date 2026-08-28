# HTML Email Templates — NDR's Preferences

For **important / commercial / family emails** (property transactions, legal agreements, partnership terms, family consent emails), the user prefers clean HTML+CSS formatting over plain text.

## Core CSS Skeleton

```html
<style>
  body { font-family: 'Segoe UI', Arial, sans-serif; font-size: 14px; line-height: 1.6; color: #333; }
  .container { max-width: 640px; margin: 0 auto; padding: 20px; }
  h2 { color: #1a1a2e; font-size: 18px; margin-top: 24px; margin-bottom: 10px; border-bottom: 1px solid #e0e0e0; padding-bottom: 6px; }
  .highlight { background: #fef9e7; border-left: 4px solid #f0ad4e; padding: 12px 16px; margin: 16px 0; }
  .key-term { font-weight: 600; color: #1a5276; }
  .consent-box { background: #eaf2f8; border: 1px solid #aed6f1; border-radius: 6px; padding: 14px 18px; margin: 18px 0; }
  .quote { font-family: 'Courier New', monospace; background: #f5f5f5; padding: 8px 12px; border-radius: 4px; font-size: 13px; }
  .footer { margin-top: 28px; padding-top: 14px; border-top: 1px solid #ddd; font-size: 13px; color: #666; }
  strong { color: #1a1a2e; }
  ul { margin: 8px 0; padding-left: 20px; }
  li { margin: 6px 0; }
</style>
```

## Section Patterns

### Section header
```html
<h2>Section Title</h2>
```
Use h2 for sections only (not h1). The bottom border automatically separates sections.

### Key commercial term (highlight box)
```html
<div class="highlight">
<p><strong>Key Point:</strong> Important condition or constraint that needs emphasis.</p>
</div>
```
Use for: sale nature ("As Is, Where Is"), critical legal requirements, timeline constraints.

### Consent / confirmation box
```html
<div class="consent-box">
<p style="font-weight: 600; margin-bottom: 8px;">Requested Confirmation:</p>
<p class="quote">"Yes, we are agreeable to joining the Sale Agreement and/or Sale Deed as vendors."</p>
</div>
```
Use for: explicit confirmation requests, signature blocks, approval requests.

### Inline key term
```html
<span class="key-term">right of first refusal</span>
```
Use for: defined legal/commercial terms on first mention.

## Tone Rules

- **To:** First-name salutation ("Hi All," / "Hi Guys," for family; "Dear [Name]," for professional)
- **Sign-off:** "Warmly," for family; "Regards," or "Best regards," for professional
- Use "we" / "us" / "our" for the group, not "I" unless recording personal consent
- Keep sentences short — each thought on its own line is fine
- **No filler**: don't explain why you're emailing beyond the subject line

## Implementation

```python
from tools.gws_skill_bridge import call
call("draft_create",
     service_name="google-draas",
     to="recipient1@domain.com, recipient2@domain.com",
     cc="ndr@draas.com",
     subject="Subject Line — Key Context",
     body=html_body,
     html=True)
```

The `html=True` parameter tells the bridge to use MIMEText with `html` subtype instead of `plain`. The HTML body should be a complete, self-contained document with all styles in a `<style>` block.
