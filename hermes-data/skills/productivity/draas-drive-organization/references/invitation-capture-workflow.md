# Invitation capture: file invite image + calendar event with Drive link

> **Entry point note (2026-09-28):** this file is NOT currently listed in the
> parent SKILL.md's reference index — SKILL.md is at its 100,000-char limit and
> rejects new lines. Reach this file by name; it and
> `references/invitations-tracking-folder.md` are the two invitation references.
> If SKILL.md is ever trimmed, re-add both to the reference list, plus
> `scripts/file_invite_to_drive_and_calendar.py`.

Worked 2026-09-22: NDR sent a birthday-invitation card image (B.K. Das 80th,
IAS Officers Association) with: "make sure the event is in our calendar as well
as the invite itself is hosted in the appropriate invitations folder … and the
link is provided in the description."

## The two deliverables (always BOTH)

1. **Invite filed on Drive** — upload the image into the root **Invitations**
   folder (`1wmXLuD66KOTBtfsDvDQcTWnUjvKEjvt3`, Drive root — NOT Personal's
   `Invitations` `10MgC-_yfF03W3TnPHuI4o1ycKxxkscc1` and NOT `Invites`
   `1KDSqcMagtUYQkE-PDEVwj-a4P8h6jngz`; root `Invitations` is where photo card
   invites go, `Invites` is the general catch-all).
2. **Calendar event created** — Google Calendar (google-draas, primary):
   - Summary: `<Name> <Event>` (e.g. "B.K. Das 80th Birthday Dinner — Vashisth Das")
   - Dates/times from the card; dinner events get 7:30 PM → 10:00 PM unless the
     card says otherwise
   - Location, description = invite Drive link + card details (host, phone)
   - Default reminders

**Runnable:** `scripts/file_invite_to_drive_and_calendar.py` does both deliverables
in one pass — edit the CONFIG block and run with `/opt/hermes/.venv/bin/python3`
(vault env vars are unavailable in `execute_code`). It verifies the upload landed
in the right parent, shares to guests, and carries a double-book guard.

## Confirm the folder is live — the routing question NDR asks

NDR sometimes says *"just reconfirm that skill and confirm that the folder has been
identified in it."* He is asking you to prove the destination folder is the CURRENT
one, not to re-read the note. Satisfy it by **listing the folder's children live**
and reporting what is in it — the response is the evidence, and it catches a stale
ID. Reconfirmed 28-Sep: root `Invitations` held the two photo cards
(`20260606_DinnerDance_KarjulArun.jpg`, `20260924_BKDas_80thBirthday_Invite_IASOfficersAssoc.jpg`),
so the Chandi Homa card was filed there.

Card images uploaded via chat live at `/data/hermes/image_cache/img_<hash>.jpg`;
check that path before asking NDR to re-send them.

## Celebration / party cards (worked 2026-09-28: Kaajal & Arun, Shivani & Aman)

Three cards were filed+calendared in one sitting (Chandi Homa; "Drinks, Dinner &
Dancing"; Diwali Get Together). What the party cards added:

- **"Just calendar it for me and Roshini" / "Calendar this one as well" does NOT mean
  skip the filing.** NDR is naming the artefact he wants to see on his phone (the
  event). The standing two-deliverable rule still applies: file the card in root
  `Invitations` **and** create the calendar event, then surface **both** links. He
  confirmed the pattern implicitly by not objecting to either.
- **"<time> onwards" party cards → start at the stated time, 3-hour block.** Observed:
  "8:00 PM onwards" → 20:00–23:00, twice. This is distinct from the 7:30–10:00 PM
  dinner default above — a drinks/dinner/dancing or Diwali card is an evening party,
  not a dinner sitting. Do not apply the dinner default to it.
- **Host names come from the card's closing signature**, not the header: "Kaajal &
  Arun", "SHIVANI & AMAN", "With love, Narang's". Use those for the event title and
  the Drive filename (`YYYYMMDD_<Event>_<HostOrVenue>.jpg`).
- **"me and Roshini" = Roshini is the only attendee added.** NDR owns the primary
  calendar (organiser); adding him as an attendee too is a self-invite quirk. Keep
  `rnr@draas.com`, `guestsCanSeeOtherGuests: False`, `sendUpdates: 'all'`.
- **After creating the event, offer to add the host family to contacts** — party hosts
  are usually not yet in the sheet. Offer; never add silently.
- **Cross-reference hosts against open reminders.** "Kaajal & Arun" matched an open
  Arun Ahuja birthday-reminder item where the spouse had been captured only as
  "Kajal" — naming the hosts on a card is often the missing key to an older note.

## Reusing the shipped script (fastest path, used 3× on 2026-09-28)

`scripts/file_invite_to_drive_and_calendar.py` does both deliverables in one pass.
Practically: copy its CONFIG block into a small file under `/tmp`, point `SRC` at the
card in `/data/hermes/image_cache/`, run with `/opt/hermes/.venv/bin/python3` (vault
env vars are NOT available in `execute_code`). The script's own stdout — folder
contents, parents verification, guest list, `htmlLink` — is the evidence to quote back
to NDR.

**Ordering pitfall — guard the UPLOAD, not just the event.** The script uploads the
card FIRST and only then runs its calendar double-book guard, so a re-run after a
partial failure leaves a **second Drive copy of the card** while the script still exits
cleanly on the event guard. The duplicate is therefore invisible in the script's own
output. Check the folder listing for the exact target filename BEFORE uploading and
reuse the existing file id; print the folder listing in the run so the count is visible
and an accidental second upload is obvious.

## Image-card specifics (Chandi Homa case, 2026-09-28)

- Religious/ceremony cards carry a **sequence of timings** (puja start, a mid-morning
  ritual, the concluding rite, then lunch). Block the calendar event from the FIRST
  listed time to the end of the last item — do not use the default 2–3 h block.
  Worked: 8:30 AM puja start → Purna Ahuti 12:15–12:30 PM → prasad lunch = 8:30 AM–2:00 PM.
- Keep each named ritual on its own line in the description; NDR reads these off the event.
- Signature line on the card ("With love, Narang's") gives the host family name for the
  event title and location.

## Evening social events (drinks / dinner / party) — block length

The `8:00 PM onwards` style card (worked: Kaajal & Arun, Embassy Habitat Clubhouse,
9-Oct-2026) is an **open-ended** invitation. Block it **20:00 → 23:00** — a 3-hour
window, not the 7:30–22:00 dinner default, and not an all-night block. Rule of thumb:
- **"onwards"** on the card → 3 h from the stated start
- **fixed dinner** (no "onwards") → 7:30 PM → 10:00 PM per the default above
- **ceremony card with a sequence of rituals** → first listed time → end of the last
  named item (see the Chandi Homa specifics above); never the social-event window

Also: the hosts line on these cards is a **couple** ("Kaajal & Arun"). Put it in the
event title AND the description, and cross-check it against open birthday/anniversary
reminders — the same people often appear in both (Kaajal & Arun ↔ the pending
Arun Ahuja birthday reminder, "Kajal" = Kaajal). Flag the match to NDR rather than
silently merging the records.

## Naming convention for invite files

`YYYYMMDD_<Event>_<HostOrVenue>.jpg` — matches existing entries
(`20260606_DinnerDance_KarjulArun.jpg`, `20260917_Parna_Invitation_QueensCorner.jpg`,
`20261009_DrinksDinnerDancing_KaajalArun_EmbassyHabitat.jpg`).
Use `.jpg` even when the source has no extension — upload with
`mimeType="image/jpeg"`.

## Calendar description template

```
Invite: <drive link>

<card headline> — <full event line>.
<time line>.
Venue: <venue>.
Host: <name> — <phone>
```

Return BOTH the event link (`htmlLink`) and the Drive link to the user.

## Contact resolution (optional value-add)

Resolve the host via contact_resolver — NDR's contacts often have the host
(Vasisth Das → vashisth@gmail.com, +91 98450 22273 matching the invite). Offer
to add the host as a guest; don't add silently.