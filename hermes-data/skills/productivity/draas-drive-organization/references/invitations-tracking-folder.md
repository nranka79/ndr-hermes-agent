# Invitation Media — Tracker Folder, Video Analysis, Calendar Invite & Reply

Class of task: NDR receives a personal invitation (text paste + media link, a WhatsApp message, or an
image he drops in chat). He wants, in some order:
(1) media filed into the EXISTING invitations tracking folder (never a new folder),
(2) a calendar invite with named attendees + reminders, the file link in the description,
(3) extra details from the media read off the card/video,
(4) the invitation forwarded to a family member (often his mother, Kanta Ranka) on WhatsApp.

## Canonical tracking folder
- **"Invitations"** root folder id `1wmXLuD66KOTBtfsDvDQcTWnUjvKEjvt3` — **photo/reception cards go here.**
- Naming: `YYYYMMDD_Event_HostOrVenue.jpg` (e.g. `20261116_Wedding_NikhilHarshitha.jpg`,
  `20261026_ChandiHoma_NarangResidence_KumaraPark.jpg`, `20260924_BKDas_80thBirthday_Invite_IASOfficersAssoc.jpg`).
- Upload with `mimeType: image/jpeg`.

## Duplicate-name pitfall (2026-09-06; routing re-CONFIRMED 2026-09-28 and 2026-10-19)
Drive has (at least) THREE folders matching "invitation" — disambiguate by CONTENTS (list children),
never by name alone:
- `1wmXLuD66KOTBtfsDvDQcTWnUjvKEjvt3` — root "Invitations" (My Drive root) ← **photo-card invites (current convention)**
- `10MgC-_yfF03W3TnPHuI4o1ycKxxkscc1` — "Invitations" (Personal/Temp parent) — OLDER mixed family media (video invites, baby shower, prayer meeting). Do NOT send new photo cards here.
- `1HWAQxiS5hIw_MWvVYKSqRxk5Ky6zsCwA` — "personal invitation folder" — Heer's 5th Birthday Invite

Check with `files().list(q="'<fid>' in parents and trashed=false")` before filing.

## Sharing convention for filed cards — READ THIS BEFORE PROMISING A LINK
Every card in the root folder is shared **reader → rnr@draas.com only**, owner ndr@draas.com.
There is **no "anyone with the link"** permission on any of them.
Consequence: a Drive link to a card will NOT open for anyone outside NDR + Roshni — including his mother,
siblings, or a WhatsApp recipient without a Workspace account. Never paste a card link into a family
WhatsApp message assuming it will open. If a non-Google recipient must see the card, either
(a) NDR forwards the image from his own phone, or (b) you explicitly ask to switch the file to
`type: anyone, role: reader` and say you will revert it afterwards.

## Calendar event — house pattern (verified 2026-10-19)
`build_service("calendar", "v3", service_name="google-draas")`, `calendarId="primary"`:
- `summary`: `"Reception — Nikhil & Harshitha (Pirgal family)"` — event type, couple/host, family in brackets.
- `location`: exactly as printed on the card (`Chamara Vajra - Markata Lawns, Jaymahal Main Road, Bengaluru`).
- `start/end`: `dateTime` WITH `+05:30` **and** `timeZone: "Asia/Kolkata"`. "7 PM onwards + dinner" → 19:00–22:00.
- `attendees`: resolve via `contact_resolver` (Roshni → `rnr@draas.com`); `guestsCanSeeOtherGuests: False`.
- `reminders`: `useDefault: False`, overrides `popup` at **5 days / 3 days / 1 day** plus `email` at 1 day —
  this is NDR's standing ask for wedding/social invitations. (Doctor/service appointments instead use
  2 hr + 45 min + email-a-day-before.)
- `description`: the FULL card text (date, time, venue, programme notes) + `Drive card: <link>` +
  the original sender's WhatsApp message in quotes. This makes the event self-contained when the card is lost.
- `sendUpdates: "none"` — create the event, do NOT let Google email the attendees. Then tell NDR
  "created with sendUpdates=none, say the word and I'll push the notification". Pushing invite email is
  his call, never automatic.
- Verify by reading the event back: summary, start/end, location, attendees, reminder overrides,
  and `link in description` — all four before reporting success.

## The media-forwarding leg — plan for it up front
NDR's usual third ask is *"and forward the invitation to my mum"*. The WhatsApp bridge API that Hermes
exposes is a **text surface**: read/search/style-corpus/draft/confirm/send of text only. There is no media
download call and no media send call on it (the tool source states there is no filesystem access to media,
and `wa.ahfl.in` answers 401 to anything outside the documented text endpoints). Broadcast-list messages
are worse: the media key is not released to a linked device, so the card often never even lands in the
bridge record while NDR can see it perfectly on his phone.

So: **never promise "I'll forward the image"**. State the split plainly and give the two routes:
1. **NDR forwards the card from his phone** — 2 taps, image intact, zero exposure. Recommend this first.
2. **Link route** — switch the Drive file to anyone-with-link viewer, send a one-line follow-up text with
   the link (needs his explicit yes; draft it and show the text first), revert sharing later.
Either way the **text** message carrying every detail off the card (date, time, venue, "followed by dinner")
IS sendable and is usually enough for the parent to diarise it.

Hint for the wording: NDR's register with his mother is short, factual, bulleted — date/time/venue lines,
no flourishes, prefixed "Mom,". Draft it that way (call `wa_style_corpus` on her chat first), show it
verbatim, and only then `wa_send_confirmed`.

## Workflow (end to end)
1. Get the card. If it arrives as a chat attachment it is at `/data/hermes/image_cache/img_*.jpg` —
   `vision_analyze` it and read ALL text (date line, time, venue line 1 + line 2, programme notes).
   Cross-check the weekday — a wrong weekday on a hand-set date is a silent error.
2. Upload to the canonical folder with the naming convention; share reader with Roshni; keep the id + link.
3. Create the calendar event as above; read it back.
4. Draft the WhatsApp text (style corpus first) → show verbatim → `wa_send_confirmed` → `wa_draft_status`
   to confirm `state=sent`.
5. Update the tracker row (P-xxx) with Delivery Link(s) = Drive link + calendar htmlLink, and record the
   media leg as the only open item if the image could not be forwarded.
6. Invite VIDEO instead of a photo card → see the frame-grab recipe below.

## Invite video analysis recipe (portrait 576x1024, ~47s worked)
1. `ffprobe -v error -show_entries format=duration -show_entries stream=codec_type,codec_name,width,height`.
2. Frame-grab every ~5s: `for t in 1 5 10 15 ... 45; do ffmpeg -v error -ss $t -i invite.mp4 -frames:v 1 -q:v 3 f_$t.jpg; done`
3. `vision_analyze` EACH frame asking "Read and extract ALL text" — the details card usually appears mid-video
   (~25s), family names ~30s, closing line ~45s. Take all frames, not just the first.
4. Audio is typically music-only — skip transcription unless a voiceover is expected.
5. OCR on decorative/script fonts is garbled — cross-check against the text NDR pasted; treat the video as
   authoritative for ADDITIONS (worked: invite text said "Royal Senate, Gate 6" → video added "Palace Grounds").

## Reply-to-sender variant
When NDR also wants a reply to the host family: Hinglish, warm, confirms attendance
("hum 20th ko ... zaroor aayenge. Aap se us din milte hain"), recipient resolved via `contact_resolver`,
and the clickable link produced ONLY through the `whatsapp_link` tool (never hand-encoded).

## Pitfalls
- Sender-name drift: NDR may say "Suresh Shah S-H-A" while the broadcast comes from "Suresh Pirgal" on a
  **+1 US number** and the saved contact is "Suresh Sha Lalchand Pirgal" (+91 98440 32032). Two chats, same
  person. Flag the discrepancy before any outbound message rather than silently picking one.
- "two three invites" from NDR does not mean three cards arrived — count what is actually in WhatsApp and
  say how many you got before building anything on the assumption.
- Do not net the card's Drive link into a WhatsApp text for a non-Google recipient (see sharing convention).
