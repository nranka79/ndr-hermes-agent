# Forensic Email-Thread Lookup — "who was marked on that email?"

Class of request: NDR (or a stakeholder) refers back to a SPECIFIC past email from a
partial/fuzzy/voice description and wants the recipient list (To/Cc) — or wants to know
whether a particular person/group was marked on it. Often phrased as:
"we sent an email to Sarthak about the ₹25L refund from [some collective] account — who all
were marked on it?", "did that same email also go to Roshni and Eshwari for ITR?"

## Why this is a distinct workflow

Finding a *specific* past email is different from triage (scan the last N hours) or drafting.
You are reconstructing an email you may not have sent from memory, from a voice-memo
description whose proper nouns and amounts are frequently mis-transcribed. The danger is
locking onto the verbatim spoken words and searching for something that never existed.

## Step 1 — Do NOT trust the verbatim transcription of proper nouns / amounts

Voice messages butcher entity names, group names, person names, and figures. Examples seen:
- User said "**Reformers Collective**" / "regsorformers collective" → the real entity is
  "**Red Soul Farmers Collective**" (also appears as "Redsol Farmers Collective", "Red Sol
  Farmers Collective" in the threads).
- The amount spoken as "25 lakh" was "₹25,00,000" — fine — but still try both digit and
  word forms ("25 lakh", "2500000", "₹25,00,000").

Treat every spoken name/amount as a *hypothesis*, not a search term. Resolve it against what
the emails actually contain, then correct the user's naming in your reply.

## Step 2 — Multi-query triangulation (converge on the thread)

Run several independent Gmail `q=` searches so you don't depend on any single (possibly
wrong) term. The dimensions that uniquely pin a thread:
1. **Entity-name variants** — try phonetic/substring variants ("reformers", "farmers",
   "red soul", "redsol", "red sol") and the domain of the related counterparty
   (e.g. "redsoul.co.in" surfaced the bank-account email).
2. **The person involved** (e.g. "nishant prakash" — gave this thread plus a separate
   partnership-deed email).
3. **The amount** ("25 lakh", "₹25,00,000").
4. **The recipient** named by the user ("sarthak").
5. **Subject-entity combos** ("red soul", "farmers collective").

Whichever dimension overlaps is the thread. In the ₹25L case, "sarthak" + "refund" +
"nishant prakash" + "red soul" all landed on the same subject line
"Red Soul Farmers Collective — Refund of ₹25,00,000".

## Step 3 — Pull exact To/Cc for EVERY variant of the email

This is the part that matters and the part that trips people up: the recipient list of the
**original**, any **forward**, and any **reply** inside the same thread are all DIFFERENT, and
the user's follow-up ("did that same email go to Roshni and Eshwari?") depends on that
distinction. Answer only after checking each relevant variant:

- **Original** (NDR → Sarthak, Cc Nishant Prakash): `To` = the addressee, `Cc` = who was copied.
- **Forward to a third party** (e.g. NDR → Manohar): frequently `Cc: None` even though the
  original body carries the original To/Cc inside it. Do not infer the forward's recipients
  from the embedded headers in the body — read the forward message's OWN top-level headers.
- **Reply** (Sarthak's confirmation): To/Cc usually mirror the original but not always.

Use `format='full'` and parse `payload.headers` for `From`/`To`/`Cc` of each message id.
Report them separately, e.g. "Original: To Sarthak, Cc Nishant Prakash. Forward to Manohar:
To Manohar only, Cc None — no Roshni/Eshwari."

## Sender-centric sweep — you know the SENDER/domain, not the recipient

Variant of the lookup where the user names a likely sender ("emails from drahomes.in,
Compliance / Ravi / Prabhakar") but the recipient/To is unknown. Recipient-oriented Gmail
queries (`"Lalit Kumar" "Vishwas"`) come up empty because the missing link is a party name,
not a party on the envelope. Instead:

1. **Inventory the sender's whole outbox with pageToken pagination** (up to ~300+ msgs):
   `q='from:ravi.v@drahomes.in'`, loop `nextPageToken` until exhausted.
2. **Keyword-match To + Cc + Subject per message** (case-insensitive): the hit list beats
   any single-query guess. In the Aug 2026 TIDCO/RLDA hunt, scanning
   `from:prabhakar.s@draas.com` (192 msgs), `from:ravi.v@drahomes.in` (35),
   `from:admin2.blr@drahomes.in` (353), `from:compliance@drahomes.in` (54) surfaced the
   whole CPPL/RLDA thread family in one pass.
3. **Cross-party queries** still help once you have a name: `"Lalit Kumar" "Vishwas"`,
   `"Lalit" "Chennai" "shares"` find threads where BOTH parties appear even if the spoken
   name is mangled ("Lalit" ↔ "Lalith").
4. **Financial-artifact tracing**: people who never email directly often appear in bank
   artifacts inside other threads. Search the RTGS/UTR remitter name (`"LALIT KUMAR"` in an
   RTGS row), share folio numbers, certificate numbers, "Mr. X @49%" shareholding workings.
   This is how "Mr. Lalith" resolved to the 49% investor behind Chennai Premium Projects.

## threads.get 404 fallback — use messages().get instead

Some message IDs returned by `users().messages().list()` fail
`threads().get(id=...)` with `HttpError 404 "Requested entity was not found"` — most often
for older/archived threads or list results crossing mailbox states. Do NOT declare the email
gone; fall back to `users().messages().get(userId='me', id=..., format='full')` which returns
the same headers/body for a single message. Thread-view aggregation is lost, but the To/Cc
evidence you need is intact. (Seen in the Aug 2026 Mundhara & Co folio lookup: 8 of 10
`threads().get` calls 404'd while `messages().get` worked.)

## Missing-account gate — re-auth before concluding "not in email"

After exhausting all term variants on the primary account, if the personal account
(`google-gmail`, nishantranka@gmail.com) shows an expired token (`invalid_grant`), THAT is
the unsearched surface — especially when compliance/secretarial senders write to personal
gmails directly (DRA compliance addresses dranjeeth@gmail.com / nishantranka@gmail.com).
Send ONE `send_oauth_url` (Google-only tool) and offer to resume the sweep after the user
taps the button. Also flag any mailbox you cannot reach at all (e.g. a partner's personal
Gmail) so the user can search it themselves.

## Working code pattern

Search (list) then fetch full headers per message:

```python
import os
os.environ.setdefault("HERMES_SESSION_USER_ID", "ndr")
from tools.gws_auth import build_service
svc = build_service('gmail', 'v1', service_name='google-draas')  # google-draas, NOT 'google'
profile = svc.users().getProfile(userId='me').execute()
print("MAILBOX:", profile.get('emailAddress'))   # confirm = ndr@draas.com

res = svc.users().messages().list(userId='me', q=query, maxResults=10).execute()
for m in res.get('messages', []):
    full = svc.users().messages().get(userId='me', id=m['id'], format='full').execute()
    hdrs = {h['name']: h['value'] for h in full['payload']['headers']}
    print(hdrs.get('Date'), '|', hdrs.get('From'), '|', hdrs.get('To'), '|',
          'Cc:', hdrs.get('Cc'), '|', hdrs.get('Subject'))
```

Notes:
- Run via `terminal()`, prefix `HERMES_SESSION_USER_ID=ndr` (see google-workspace skill on the
  wrong-session-user trap), and pass `service_name='google-draas'` explicitly.
- Iterate: loop the query over the variant list in Step 2.

## Related matters that surface in the same lookup

When answering "who was marked," the same entity often appears in OTHER threads that are
related but distinct. Flag them rather than merging:
- A *bank-account-details* email ("Bank Account Details – Redsol Farmers Collective",
  Sarthak → Manohar, Cc NDR) is separate from the *refund instruction* email.
- A *partnership-deed* email (NDR → Nishant Prakash, Cc Bharat) is separate again.
- An *ITR* thread for land partners (Prakash → Eshwari, Cc Roshini, Bharat, NDR) belongs to a
  different matter — do not let "did they get CC'd on the ITR" merge with "who was on the
  refund email." Report the correct thread and clearly delimit the others.
