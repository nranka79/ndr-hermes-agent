# DRA Realty office address & attendee resolution for calendar invites (2026-08-25)

## DRA Realty Pvt Ltd office address (canonical, from NDR DRAAS contacts sheet)

**L 149/A, 3rd floor, Liss Arcade, 5th Main, 6th Sector, HSR Layout, Bangalore – 560 102**

- Where it lives in the NDR DRAAS contacts sheet (`1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g`):
  the office address is stored in the **Address 1 columns (39–47)** of the rows
  for DRA Realty employees (e.g. row 57: col 39 `Work`, col 40 formatted
  address, col 42 city, col 46 country IN, col 47 extended "6th Sector, HSR
  Layout"). Scan range `A:BF` and filter for `Address 1 - Street` /
  `Address 1 - Formatted` to find it.
- The address is NOT in the Notes/Organization columns; you must read the
  address columns (39+, NOT `A:AM` which stops at 38).

## Balaji (DRA Homes) — two different people, one common trap

| Person | Email | Role |
|---|---|---|
| **Balaji Natarajan** | `balaji.n@drahomes.in` | EVP – CEO Office, DRA Homes. The one who schedules meetings with consultants (Deloitte tax structuring, etc.) |
| **Balaji G** | `balaji@drahomes.in` | DGM – Marketing, DRA Homes. Different person — do NOT mix emails |

- Neither was found via `contact_resolver` (session had no gws_service configured) or
  People API `searchContacts('Balaji')` in any of the 3 accounts (only Balaji
  Pasumarthy/Golden Square etc. surfaced).
- **The reliable resolution path was Gmail `from:` header search:**
  `users().messages().list(q='from:(balaji) dra homes')` on google-draas
  returned him immediately with self-describing signatures ("Balaji Natarajan
  (Executive Vice President - CEO Office / DRA Homes) <balaji.n@drahomes.in>").
- Lesson: when a person is identified only by first name + company ("Balaji N
  DRA homes"), and contacts sheet + People API come up empty, search Gmail
  threads with `from:(firstname) company` — signatures carry the full name,
  exact title and email. Verified addresses from actual thread headers are
  exactly what NDR expects for invite recipients (matches his standing rule).

## Calendar invite pattern that works (no guest email needed)

- User asks "create calendar invite for me at DRA Realty office" based on a
  WhatsApp thread (meeting fixed by Balaji: Tue 11 AM).
- Create on ndr's calendar via
  `build_service('calendar','v3', service_name='google-draas')`; ALWAYS verify
  `calendars().get(calendarId='primary')` owner == ndr@draas.com before insert
  (wrong-owner pitfall is real).
- Pass IST offset `+05:30`; location = the office address above.
- When the key guest (e.g. Deloitte's Amit) has no email on file, invite the
  resolveable organizer (Balaji) + NDR only, and tell NDR to share the guest's
  address to add them — do not guess a deloitte.com address.
- Never auto-send the invite without NDR's explicit "create invite" instruction;
  creating on his calendar with sendUpdates='all' is the sanctioned action when
  he asks.