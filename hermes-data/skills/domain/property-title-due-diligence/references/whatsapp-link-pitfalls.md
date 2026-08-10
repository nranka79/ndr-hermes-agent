# WhatsApp Link Generation — Pitfalls

## THE NUMBER TRANSPOSITION BUG (2026-08-07, Sundar Padmanabhan case)

User caught that a wa.me link pointed to the wrong number even though the
displayed contact number was correct. Root cause: **I transposed two digits
when typing the `phone` parameter** — registry had `98204 35939` (digits
9820435939) but I passed `+919820439359` (9820439359). The whatsapp_link tool
encodes exactly what it receives; it does NOT reorder or validate digits.

**Rule: before generating a WhatsApp link for a named person, ALWAYS:**
1. Look up the contact from the registry (People API + contacts sheets).
2. Show the user the number(s) found and CONFIRM which one to use — the
   registry can hold multiple numbers per contact (Mobile / Home / Wapp) and
   the "Wapp" label is not proof the number is current.
3. Copy the digits verbatim from the lookup result into the `phone` param.
   Do not retype from memory or from a previously-rendered URL.
4. Verify the URL's `wa.me/<digits>` segment equals the registry digits
   (strip +91, compare the full 10-digit string) before delivering.

## Verification pattern
- expected:  9820435939   (+91 98204 35939)
- passed:    9820439359   (+91 98204 39359)  ← WRONG, transposed
- Check `phone` echoed in tool output equals what the registry shows.

## Long messages split into parts
Messages > ~4096 chars are returned as `parts[]` with `split: true`. Deliver
EACH part as its OWN separate Telegram message (send_message per part) —
never combine parts, Telegram's own splitter will cut the link.

## Group vs individual links (DRA convention)
- Individual: include `phone` so the link opens the right chat.
- Group (e.g. DRA Realty Group): OMIT phone — link opens WhatsApp for the
  user to pick the group, text pre-filled.
