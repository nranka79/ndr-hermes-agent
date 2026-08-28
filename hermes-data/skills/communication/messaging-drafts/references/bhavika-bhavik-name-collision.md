# Bhavika vs Bhavik — Name Collision (June 2026)

## The Problem

User said "Bhavika Ranka" in a voice message. The contacts sheet returned `bhavika@deciphergroup.com` — which IS a real person named Bhavika Ranka. But the user actually meant **Bhavik Ranka** (no final 'a'), a completely different person.

## Root Cause

Both names exist simultaneously in:
- **People API** — two separate entries with different emails/phones:
  - Bhavika Ranka — bhavika@deciphergroup.com
  - Bhavik Ranka — bhavik@draas.com, bhavik.92@gmail.com
- **Contacts Sheet** — Row 622 (Bhavik) vs Row 623 (Bhavika)
- **Gmail** — Bhavik was CC'd on Ranka Iris OC emails as bhavik@draas.com

## Resolution

Cross-referenced by searching Gmail for "Bhavik Ranka Iris" — found him CC'd on the **Ranka Iris Occupancy Certificate** email thread using `bhavik@draas.com`. This confirmed that `bhavik@draas.com` is the correct work contact for project-related matters.

## Lesson

When a name differs by a single letter (especially final vowels: Bhavik vs Bhavika, Rohit vs Rohita), **do not assume it's a spelling variant of the same person**. Treat it as a potential name collision and:
1. Check if BOTH names exist in the sheet as separate entries
2. Cross-reference with Gmail in the specific project context
3. Present both to the user for confirmation
