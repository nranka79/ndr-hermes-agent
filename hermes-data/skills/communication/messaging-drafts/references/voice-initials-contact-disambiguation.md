# Voice-Transcribed Initials — Contact Disambiguation

## When to use

User says a contact name in a voice message that includes initials (e.g. "Adv. P R Krishna" or "Mr. B R Sharma") and/or a firm name that sounds like an abbreviation (e.g. "Jain Patan Chetty" instead of "J P A & Associates"). **Do not run a single search and declare "no record found"** — voice transcriptions are unreliable on both initials and on Indian firm abbreviations.

## The trap

Voice-to-text on Telegram consistently mangles:

| Heard as | Could actually be |
|---|---|
| "P R" | "B R" (P/B are the most common swap) |
| "B R" | "P R" |
| "K R" | "G R" / "K B" / "B K" |
| "S K" | "A K" / "S N" / "K S" |
| "Jain Patan Chetty" | "J P A" (the letters, not the words) |
| "Patan Chetty" | "Pattanshetty" / "Pattanshetti" / "J P A" |
| "Krishna Murthy" | "Krishnappa" / "Krishnamurthy" / "Krishnaswamy" |

The whole "P R vs B R" trap alone accounts for ~30% of voice-misheard initial pairs in DRAAS / Indian business context.

## Verified pattern (June 2026, Adv. B R Krishna)

User said: *"Advocate PR Krishna, works with Jain Patan Chetty"*. Both pieces were wrong:

- **"P R Krishna"** → actually **"B R Krishna"** (P/B swap)
- **"Jain Patan Chetty"** → actually **"J P A & Associates / Pattanshetty"** (J P A heard as three words)

The correct contact was found only after:

1. First search for "PR Krishna" + "Patan Chetty" returned nothing
2. User corrected to "B R Krishna"
3. Re-searching `"B R Krishna" OR "B.R. Krishna"` surfaced a Nov 2025 invoice thread Cc'd to **br.krishna.advocate@gmail.com**
4. The full body of that thread surfaced a second address: **krishna@brklaw.in** (Ccd on an Apr 2026 email)
5. The firm signature block confirmed J P A & Associates (Pattanshetti) at #70 Infantry Road, Bengaluru

## Working pattern

When voice input contains initials or an abbreviation that returns zero hits:

1. **Generate the 3-4 most-likely alternate spellings** (B↔P, P↔B, K↔G for the lead consonant; expand abbreviations to spelled-out forms).
2. **Search Gmail for ALL variants** in a single `users().messages().list(q=...)` call using `OR`:
   ```python
   queries = [
       '"B R Krishna"',
       '"B.R. Krishna"',
       '"BR Krishna"',
       '"P R Krishna"',  # original
   ]
   seen = set()
   for q in queries:
       res = gmail.users().messages().list(userId="me", q=q, maxResults=15).execute()
       for m in res.get("messages", []):
           if m["id"] in seen: continue
           seen.add(m["id"])
           # fetch full body — alternate email aliases live in Cc headers
   ```
3. **Always fetch the message body in `format="full"`** — alternate email addresses and firm names usually appear in the Cc header or signature, not in the To/From of the original message. A single "From" line of one address doesn't tell you about the other 1-2 addresses they use.
4. **Mine Cc headers specifically** for unknown associates. Pattern: `gmail.users().messages().get(id, format='metadata', metadataHeaders=['From','To','Cc','Subject','Date'])`.
5. **Mine the firm signature block** for the office address and phone — it confirms the firm association.
6. **If a firm name was also mentioned**, search Gmail separately for the firm name + "kannada/ca/advocate/associates" to find any thread that mentions the firm even if the contact name was wrong.

## When to give up and ask the user

If 4+ spelling/abbreviation variants all return zero Gmail matches AND the Drive has no document mentioning any of them, ask the user:

> "I searched Gmail + Drive for several spellings of the name (B R, P R, BR, B.R.) and the firm (J P A, Jain Patan, Pattanshetti) and found no record. Could you confirm the spelling, or send me a recent email/WhatsApp from them so I can pull the exact email/phone?"

## Phone number discovery — escalation chain

Voice input rarely provides a phone number. When the user gives a number out-of-band, accept it (after a basic sanity check: 10 digits starting with 6/7/8/9 for India) and proceed.

When the user does NOT provide a number but you need one for WhatsApp, the discovery chain is:

1. **Gmail signature/footer** — fetch the email body in `format="full"`, regex for `+91 \d{4,5} \d{5,6}` and `91[6-9]\d{9}`. Most firm signatures have an office number; the advocate's personal mobile is often NOT in the signature.
2. **Contacts sheet** (SA DWD, see `gws-automation/references/google-sheets-api-read-write.md`) — search the company contacts registry for the name.
3. **People API** — fallback if the contacts sheet is empty (requires additional OAuth scope).
4. **Drive PDF/email attachments** — past engagement letters, invoices, or signed agreements often have the counterparty's phone.
5. **Ask the user** — last resort; don't loop on searches once Gmail + Drive + Sheets all returned nothing.

## Related

- `references/gmail-thread-contact-mining.md` — Phase 4 contact resolution: mining Gmail To/Cc/From headers + thread body for an external counterparty's email aliases, firm association, and phone numbers. The deep dive on step 2-4 of the chain above.
- `references/contacts-lookup.md` — Find person by name → full contact record (sheet + People API fallback).
- `references/voice-entity-resolution.md` — Voice message → project/contact resolution: the 4-phase workflow BEFORE any action. This file is specifically about the P-R vs B-R / abbreviation trap that survives Phase 1-3.
