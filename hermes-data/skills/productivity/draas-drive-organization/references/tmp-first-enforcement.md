# TMP-first enforcement — never create folders at My Drive root

NDR's standing rule (re-stated emphatically 2026-10-14 after the violation): "All creation only has
to happen in the TMP folder… never in the root drive. Please make sure that they are in the TMP
folder in the root drive."

## Why the rule was violated (2026-10-10→13) and how to prevent it

Three family-admin case folders were created at/above My Drive root across sessions:
- 1LaKbWY26MGq1AS9E2Li2GTofnviYg18H — Kanta Ranka Switzerland Schengen Visa (Nov 2026)
- 1cfRE-dGyQNA08XAbEljl0KHb7RHTHSpi — KYC & Identity Records – Kanta Ranka & Late Dinesh Ranka
- 1wDYrBK4VoA8CX487qAqZ_aQyYyPhXBHa — PassportReissue_KantaRanka_Case_2026

Root cause: creation was ASSUMED to go to the right place, never VERIFIED. The skill said
"TMP first" but no post-create check existed.

## Checklist (do this every time a folder/file is created)

1. ALWAYS pass the TMP folder as parent on create (root TMP id:
   18p74II2uL32sNDzDDwXzmlOUdJJOTmE-, owned ndr@draas.com, directly under My Drive root).
   Never create with no parent (lands at My Drive root). Never create directly in a project
   folder — TMP first, move only on NDR's explicit instruction.
2. AFTER creating OR moving a folder, verify by reading back its `parents` field — same
   verify-by-reading-back discipline as GWS writes. If parents is not the TMP id, move it
   immediately: drive_move add_parents=<TMP>, remove_parents=<old>.
3. When asked to clean up ("these folders are in my root"), move (drive_move) rather than
   recreate — share links and child permissions stay intact; folder id unchanged by a move.
4. On discovery of any historical stray case folder at root, move it under TMP proactively —
   that is NDR's explicit standing instruction; the case folders listed above were all moved
   to TMP on 2026-10-14.

## Notes

- Share links survive the move (the URL still resolves; only the physical parent changes).
- NDR's drive root contains many legitimate pre-existing folders (personal trackers, contacts
  sheet, DRA project packs) — do NOT sweep those; only move folders that HERMES created for
  chat-session work and left at root.