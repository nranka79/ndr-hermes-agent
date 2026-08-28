# Thread-Level Follow-Up Analysis (3-account, Aug 2026)

Use when the user asks: "analyze my work emails AND personal email", "what do I need to follow up on",
"who am I awaiting a response from", "anything I need to respond to" — i.e. the flat message-level
classification in the main skill is not enough; you must reconstruct conversations.

## Accounts (resolve via gws_resolve_account first)
- google-draas → ndr@draas.com (work primary)
- google-ahfl → ndr@ahfl.in (work secondary)
- google-gmail → nishantranka@gmail.com (personal — ONLY include when the user asks for personal email)

## Fetch strategy
1. For EACH account, query BOTH `in:inbox after:YYYY/MM/DD` AND `in:sent after:YYYY/MM/DD`.
   `in:sent` is mandatory — AWAITING RESPONSE can only be derived from messages the user sent.
2. Split the window into two 7-day queries (`after:X before:mid`, `after:mid`) when max per query
   caps out; dedupe by message `id` across queries afterwards.
3. Use the `fetch()` helper from the main SKILL.md pitfall (JSON-string parsing + "No messages found." handling).
4. Store per-message: id, threadId, from, to, subject, date, snippet, labels, _account.

## Thread reconstruction
- Group by `(account, threadId)` — threads NEVER cross accounts.
- Sort each thread by parsed Date; last message decides the category.
- `'SENT' in last['labels']` → AWAITING RESPONSE (the user sent last; "others" set = who owes him a reply).
- Last message incoming + question/request keywords → NEEDS RESPONSE.
- Incoming + 2+ messages + no ask → INFO_CONVO. Incoming + 1 msg + no ask → FII.

## Classification keywords (subject + snippet)
- NEEDS RESPONSE: please, kindly, could you, can you, request you, let me know, awaiting, needed from you,
  your inputs, your feedback, approval, confirm, review and, ?, would you, are you, do you, have you,
  need your, share the, send me, pls, please revert, at the earliest, escalate
- NEEDS CLARIFICATION: clarify, not sure, please advise, any update, check, discrep

## Noise filtering — second pass needed (Aug 2026 session evidence)
The domain blocklist caught most newsletters, but these still slipped through and needed an EXTRA_NOISE
second filter before presenting:
hrkatha, letsventure, brevistay, kotakbank, mygate, nsdl, ringg, crematrix, worldhrdcongress, chroasia,
quintessentially, netmeds, camsonline, kfintech, fidelity, royalsundaram, canmoney, credai, marriott,
headout, testgorilla, stratechery, usifund, devpost, jamanetwork, anthropic, welcomepickups, bajajlife,
irdai, mediassist, bajajauto, evoting, netflix, amazon
Plus subject markers: 'attendance report', 'daily attendance', 'general file', 'otp',
'one time password', 'dividend', 'annual report', 'agm', 'shareholder', 'coupon'.

**Weekly-run additions (17 Aug 2026, 7-day window):** domains `smarterdharma.com`,
`tcsion.com`, `apify.com`, `ihcltata.com`, `goindigo.in`, `mapmygenome.in`,
`credai.org`, `openrouter.ai` (invoice+statements), `communication.microsoft.com`
(terms updates), `canmoney.in` (IPO blasts), `justdial.com`, `obo-bettermann`,
`blackbox`, `inflow` (Dell), `refcold`/`ishraeconnect.in`, `flamebackcapital.com`
(Meet invites), `liasesforas.com`, `imagesbazaar.com`, `shine.com`, `naukri.com`,
`internshala.com`, `lvxventures.com` / `letsventure.com`, `yatra`, `swiggy.in`;
subject markers `'re-kyc'`, `'periodic kyc'`, `'kyc update'`, `'nominee'`,
`'e-mandate'`, `'fixed deposit'`, `'services suspended'`, `'downtime notification'`,
`'digital general file'`, `'ipo'`, `'account statement'`, `'security alert'`,
`'storage limit'`. Vendor sends to `info@draas.com` (BLACKbox demo, Dell/Inflow
laptops, Justdial listing, OBO Bettermann, REFCOLD awards) still leak into AWAITING
RESPONSE because NDR's own address is in To — filter by recipient address, not just
sender domain. The consolidated weekly lists live in `scripts/weekly_analysis.py`.

## Presentation order (worked well)
1. AWAITING RESPONSE — split by age: "today/this week (chase these)" vs "older (11+ days — nudge)".
   For each: subject, recipient names, days since sent.
2. NEEDS RESPONSE — from/snippet, days old. Flag urgent (RERA final notice, expiry deadlines).
3. Watch list — time-bound informational items (board minutes, portal submissions, internal escalations).
4. End with a "short version": N people owe you this week — names; you owe replies on — items.

## Pitfall — do not infer project names
Base every description solely on the email's From/Subject/Body. Do NOT attach project names the email
doesn't state (same rule as the parent skill).
