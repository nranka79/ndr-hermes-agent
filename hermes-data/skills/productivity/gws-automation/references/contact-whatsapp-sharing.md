# Contact WhatsApp Sharing — Post-Creation Workflow

> ⚠️ **MANDATORY: Read this entire reference before generating any WhatsApp link.**
> Common failures: wrong domain format (wa.me vs api.whatsapp.com/send), `%26` encoding breaking Android, using the `whatsapp_link` tool output without converting the domain.
>
> **NEW (Jul 2026):** The `llm-code-boundary-principle.md` reference codifies Nishant's architecture rule — LLM drafts creative content, code handles data. WhatsApp message text is creative/opinion content (OK for LLM), but any data points (amounts, dates, counts) must be inserted deterministically by code after the LLM step.

After adding a new contact to **Google Contacts** + **NDR DRAAS Google contacts sheet**, Nishant frequently asks to share his contact details with them via WhatsApp.

## Nishant's Contact Details to Share

| Method | Value |
|--------|-------|
| Phone | +919880055634 |
| DRAAS email | ndr@draas.com |
| O3 Infotech email | nishant@o3infotech.com |

## WhatsApp Link Format

Nishant's preference: **`api.whatsapp.com/send`** (NOT wa.me).

Use the `whatsapp_link` tool to generate the link — it produces wa.me URLs. Convert to `api.whatsapp.com/send` by changing the domain (the query parameters stay identical).

**& (ampersand) rule:** Use the word `and` in message text whenever possible. Standard `&` or `%26` in WhatsApp links breaks Android's link parser. If `&` is unavoidable, use Fullwidth `＆` (U+FF06, URL-encoded as `%EF%BC%86`).

## Standard Message Template

```
Hi {name}, here are my contact details for reference:

Nishant Ranka
📞 +919880055634
📧 ndr@draas.com  
📧 nishant@o3infotech.com

Great meeting you today for the {project/product} presentation. Looking forward to staying in touch!
```

Replace `{name}` and `{project/product}` per recipient.

## Full Workflow

1. **Add to Google Contacts** via People API (`people.people().createContact(...)`)
2. **Add to NDR DRAAS contacts sheet** (93-column row, append to sheet)
3. **Read this reference first** — confirm format preferences before generating
4. **Generate WhatsApp link** using the `whatsapp_link` tool (encodes the text properly)
5. **Convert** wa.me → api.whatsapp.com/send (domain swap)
6. **Deliver links** to Nishant in the conversation

### ⚠️ Pitfall: `whatsapp_link` tool outputs wa.me — must convert

The tool outputs `https://wa.me/PHONE?text=MESSAGE`. Nishant prefers `api.whatsapp.com/send`. 
**Conversion:** Swap the domain `wa.me` → `api.whatsapp.com/send` and the path format:
- Tool output: `https://wa.me/919845020921?text=...`
- Converted: `https://api.whatsapp.com/send?phone=919845020921&text=...`

Do NOT skip this step — the wa.me format can break on some Android WhatsApp clients when the message is long.

### ⚠️ Pitfall: `%26` in message text breaks Android WhatsApp

Any `&` character in the message gets URL-encoded as `%26` by the tool. This breaks Android's link parser. 
**Rule:** Replace `&` with the word `"and"` in message text before passing to the tool. If `&` is truly unavoidable, use Fullwidth `＆` (U+FF06, URL-encoded `%EF%BC%86`) instead.
**Check your message text for literal `&` before generating.**
