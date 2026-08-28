# Gmail Draft Formatting Pitfalls

## Draft Creation — Use the Bridge, Not Raw API

**Lesson (Jul 2026, Skylark Zenith reply):** Gmail drafts created via the raw API (`users().drafts().create()` with a `raw` MIME message + `threadId`) often do NOT appear inline in the Gmail thread view. The draft shows in the Drafts folder but when the user opens the email thread, it's invisible.

**Fix:** Always use `draft_reply_create` from `tools.gws_skill_bridge.call()` — it properly nests the draft in the Gmail thread with the `DRAFT` label.

```python
from tools.gws_skill_bridge import call
call('draft_reply_create', service_name='google-draas',
     thread_id='<threadId>', message_id='<messageId>',
     body='Your reply text', body_type='plain')
```

## HTML Rendering — Keep It Minimal

**Lesson (Jul 2026, Skylark Zenith reply):** Complex HTML with CSS colors, spans, nested divs, and `style` attributes does NOT render well in Gmail drafts created via the API. The HTML tags may show as raw text in the compose window.

**The user's preference (Nishant Ranka, Jul 2026):**
- Plain text format (body_type='plain' or minimal HTML)
- Simple bold tags `<b>` for emphasizing response content — no colors, no CSS
- The user explicitly rejected blue-font styling and complex HTML

**What works:**
```
# Use plain text with section markers:
call('draft_reply_create', ..., body='''Hi X,

--- Question 1 ---
Your bolded response here.

--- Question 2 ---
Your bolded response here.
''', body_type='plain')

# OR minimal HTML with ONLY <b> tags:
call('draft_reply_create', ..., body='''<b>Your bolded response here.</b>''', body_type='html')
```

**What to avoid:**
- `<span style="color:#...">` — rendered HTML tags as visible text
- Nested `<div>` with CSS — broke the compose view
- `<hr>`, styled elements — can cause rendering issues
