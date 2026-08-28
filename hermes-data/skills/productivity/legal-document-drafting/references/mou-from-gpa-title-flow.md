# MOU Drafted from an Irrevocable GPA / Title-Flow Source Document

**Trigger:** User shares a scanned property document (typically a registered Irrevocable General Power of Attorney, or a chain of agreements) and asks to "generate an MOU draft for the schedule properties with recitals from this document". The MOU party is often NOT the registered owner — it is the GPA holder who has paid full consideration but whose registered sale deed is pending.

Validated Aug 2026: 46-page scanned GPA (Sanchaya Land & Estate Pvt. Ltd. → Pavanchand Nahar), Besthamanahalli Village, Anekal Taluk, 27 schedule items, 8A-37G total. Draft delivered as Google Doc shared with requester.

## Source document receipt (oversized / scanned)
- Telegram rejects files >20MB at upload — no bytes reach the agent. Tell the user to upload to Drive and share the link.
- Download via Drive API: `build_service("drive","v3", service_name="google-draas")` + `files().get_media(fileId=...)` with `MediaIoBaseDownload` (chunked, handles 47MB fine). Verify: `os.path.getsize(out) == meta['size']` from `files().get(fields="size")`.
- The vault in this deployment holds a token only for `google-draas` (ndr@draas.com) even when the requesting session user is psingh@draas.com → docs created land in NDR's Drive; explicitly share with the requester (`drive.permissions().create(type='user', role='writer', emailAddress='psingh@draas.com')`) and deliver the link in a code block (Telegram breaks URLs).
- Scanned source → OCR path (see `ocr-and-documents` skill: pdftoppm render + parallel tesseract). `pdftotext` returning one empty line per page = image-only.

## Recital structure (trace the FULL title flow, one WHEREAS per fact-block)
Drafted in the source document's own voice/sequence:
1. Registered owner's absolute ownership + peaceful possession of the schedule lands (describe village/hobli/taluk/district + aggregate extent).
2. Acquisition chain — registered sale deeds (years, predecessor names, SPA/GPA holders) + conversion Official Memoranda (ALN(A&K) SR nos. + dates).
3. Earlier agreements of sale to a first failed purchaser (registration doc nos, items covered, advance received).
4. That purchaser's failure to complete + agreed refund (with lumpsum interest if stated).
5. Second advance-holder (if any) and their refund agreement.
6. The GPA holder's purchase: total consideration, split — amount paid directly to owner (list RTGS UTR + cheque nos + dates), amounts agreed payable to the failed purchasers at sale-deed execution.
7. Owner's board resolution authorising execution of the GPA.
8. The registered irrevocable GPA itself: doc no + date, summary of powers (develop, approvals, sell/lease/mortgage, litigate, delegate).
9. Failed purchasers signed as consenting witnesses = recorded no-objection.
10. GPA irrevocability (owner received entire consideration) → party's full rights, subject to pending registered sale deed.
11. Party's intent + counterparty's intent (the MOU purpose).

## Party block
- First Party = GPA holder with full particulars (name, father's name, age, address, Aadhaar, PAN) — the GPA's attorney details are exactly what you need.
- Second Party = counterparty; leave as clearly marked placeholder if not stated (`[Name of DRA entity — to be confirmed]`).
- Recitals must say the party "has thereby acquired full, absolute and unfettered rights... subject to execution of the registered sale deed" — never imply registered title that doesn't exist yet.

## Schedule format
- Numbered items (Item 1..N), each: Survey No(s), extent in guntas (or A-G), conversion OM reference + date.
- Item 14-style multi-survey rows: list each survey with its own guntas, then the summed total for the row.
- Compute and show the aggregate: 357 guntas = 8 acres 37 guntas (1 acre = 40 guntas) with a TOTAL row.
- Add a note that full boundary descriptions live in the source GPA schedule pages (don't reproduce all boundaries unless asked).
- Flag non-conversion items (e.g. acquired via Agreement for Sale + registered GPA only) separately.

## Commercial terms
Leave as `[insert ...]` placeholders and list them back to the user at delivery: Second Party identity, purpose (joint development / monetisation / outright sale), consideration + sharing ratio, timeline, dispute resolution. DRA default per `mou-standard-drafting-format.md`: binding mediation under Mediation Act 2023 (NOT arbitration).

## Delivery
- Create Google Doc via Docs API (`documents().create` then `insertText` with the text — strip markdown `**`/table pipes first, keep table rows as ` | `-joined lines), share writer permission with requester, deliver link in a code block + Drive search-by-filename fallback.
- Keep a local .md copy as a second artifact.
