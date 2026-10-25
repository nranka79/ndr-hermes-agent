# SIR2026 / ECI voter notice filing convention (verified 2026-09-14; RECALL added 2026-09-21)

> **Load triggers:** filing a SIR/ECI voter notice (paired Kannada+English), AND the later-recall
> case — "what was that voter notice", "where was I supposed to go on Friday", "what was the
> telephone number on that notice", "did I go to the electoral roll appearance?". The RECALL
> section at the bottom is the part that answers those; read it before searching Drive blind.

ECI annual revision (SIR-2026, running as SSR) voter notices arrive as Kannada scans (Adobe Scan, garbled OCR). DRAAS files a PAIR per person, one Kannada + one English, with an established pattern:

- `20260910 SIR2026 Voter Notice - Roshini Ranka (Kannada Original).pdf`
- `20260910 SIR2026 Voter Notice - Roshini Ranka (English Translation).pdf`
- This session: `20260914 SIR2026 Voter Notice - Nazeer Ahamad (Kannada Original|English Translation).pdf`

## Rules
- **Name pattern:** `YYYYMMDD SIR2026 Voter Notice - <Full Name> (Kannada Original|English Translation).pdf` — this is the paired-space style (NOT the underscore YYYYMMDD_Entity_Description rule); match the existing pair's style so siblings sort together.
- **Date prefix = scan/receipt date** (the day the paper notice arrived), not the hearing/appearance date on the notice.
- **Location:** the `Personal` folder (id `0B1Oc8cSaJXPGYkQtYXJDQWVBUVE`) at root OR in the per-person subfolder (RNR = Roshini Ranka, DDR, Ruhan, Ruhaan, Rivaan, Murjani...). If no per-person folder exists for the notice's subject, file at Personal root and offer to create one.
- **Flag the named voter:** the notice may name someone other than the manager (e.g. NAZEER AHAMAD handled by NDR). State the voter's name in the reply; identity documents carried to the hearing must match the VOTER's name/address, not the manager's.
- **English version is made from a faithful Gemini 2.5 translation** — pipeline in `ocr-and-documents` → `references/kannada-gemini-openrouter-translation.md`.

## Related calendar pattern
The notice usually carries a hearing ("appear before the undersigned ... at <school/venue>") — create BOTH a pre-visit reminder (user's chosen evening time) AND a calendar entry for the actual appearance window, with all voter details + notice contact (BLO mobile) in the description, no guests for the named voter unless the manager confirms.

## MISSED the appearance date — delegate to office staff (added 2026-09-21)

The appearance window is short (a 2-hour slot, ~4 days after the notice arrives) and it
DOES get missed. When NDR says *"I didn't do this today itself because I already missed
the 18th September date"*, the work becomes a **follow-up-to-reschedule**, not a filing.

**Do not assume the date already passed just because the user says "Friday" or "today".**
Work out which date they mean against the notice, then say plainly that it is in the past.
Verified case: NDR said *"go somewhere on Friday"*; the notice's Friday was **18-Sep** (3
days past), and the coming Friday **25-Sep** had no event at all. Saying so — and asking
which he meant — was the correct move. Confirm from the calendar + inbox before drafting:
no newer SIR notice had arrived across ndr@draas.com / ndr@ahfl.in / nishantranka@gmail.com
(45-day sweep).

**Delegation template — send the office boy (Ravi, Office Boy, DRA Realty):**
Ask him to (1) phone the BLO, (2) attend in person with a PRINTED copy of the notice, and
(3) try to have it handled on NDR's behalf. If the officer insists on NDR personally, Ravi
must come back with **where, what time, and which ORIGINAL documents** — NDR will reach
within 35 minutes — and may put NDR on a **video/phone call** from the venue.

Carry-over flags to include in the message:
- The notice is in the **voter's** name, not NDR's (e.g. NAZEER AHAMAD). The BLO cannot trace
  the file without that name — offer to add an identifying line.
- Attach/send BOTH versions (English + Kannada original) for printing.
- Contact number on the notice is the **BLO's**, not the voter's — that is the number to dial.

**The notice-number/venue/BLO details live in the tracker row** (P-145 Roshini Ranka,
P-160 Nazeer Ahamad) and in the calendar event description — read those before re-deriving
anything, and keep the reply's facts consistent with what was filed.

## RECALL — "that voter notice I was supposed to go to" (verified 2026-09-21)

NDR asks this months later, from memory, with a detail or two wrong. Do NOT guess and do NOT
re-run the whole pipeline. Recovery recipe:

1. **Tracker first, not Drive.** `personal-task-tracker` rows P-145 (Roshini Ranka) and P-160
   (Nazeer Ahamad) hold the COMPLETE record — notice number, EPIC, booth, venue, BLO mobile,
   the appearance window, AND the Drive file links in the Proof-of-Completion columns. One
   read of the `All Tasks` tab answers most of the question. Grep the tab for
   `sir-2026` / `electoral-roll` / `nazeer` / `roshini` (lowercased), not just "voter".
2. **Then confirm the notice text** by downloading the filed English PDF from Drive
   (`files().get_media`, then `pymupdf` → `page.get_text()`). The English translation has a real
   text layer, so **pymupdf extracts it cleanly — no OCR or vision needed**. This is the fast
   path; only fall back to vision pools if the PDF is image-only.
3. **Then check the calendar is still right** — `q="Voter"` on `events().list` over a wide window
   returns the pre-visit + appearance pair in one call.
4. **State the BLO number.** "The telephone number on the notice" = the **BLO** (Booth Level
   Officer), e.g. K. Sridhar Babu 98452 44731. It is the ONLY number the notice carries; there is
   no number for the named voter.

**Pitfall — do not silently accept the user's stated day/date.** NDR asked about "Friday" when the
notice's Friday had already passed (18-Sep-2026, asked on 21-Sep). Two errors in one:
saying "Confirmed" would have been wrong, and *assuming* a future Friday would be when he meant
nothing. **Verify the date against today's date, say plainly that that instance is past, and
report what the calendar actually holds.** Then give him the fork: already attended → close it
out; still pending → draft a WhatsApp to the BLO's mobile asking for the rescheduled window and
put the new slot on the calendar.

**Before concluding "no newer notice exists",** sweep all three accounts
(google-draas / google-ahfl / google-gmail) with `newer_than:45d` for voter/electoral/SIR terms,
and check recent Drive uploads. Absence is only reportable after that sweep — it is a real answer
once verified, not a reason to shrug.