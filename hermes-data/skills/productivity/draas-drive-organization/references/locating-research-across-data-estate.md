# Locating research / artifacts across the DRAAS data estate

Use when the user asks "find the research we did on X", "did I email Y about Z", "is there a survey/RTC/EC/zoning record for this land?" — the answer may live in any of several stores, and concluding "not found" after checking ONE store is wrong.

## Search ladder (fastest → slowest, in this order)

1. **Session history** — `session_search(query="<project> <owner> <place>")`. Include colloquial AND spelling variants in one OR query.
2. **Gmail (ndr@draas.com only)** — NDR uses ONLY ndr@draas.com as his work account (stated 2026-08-17). Do NOT search ahfl.in for work mail, do NOT ask him to re-auth it. Search sent + inbox + drafts with ALL spelling variants:
   - `svc.users().messages().list(q='<term>', maxResults=10)` then metadata headers for Subject/From/Date.
   - Place-name garble: "Siddhapura" returned 0 hits while "Siddapura" returned hits. Always run the variants list (Siddhapura/Siddapura/Sidhapura, Glenmore/Greenmore/Green More, Jainagar/Jayanagar/Jai Nagar).
   - A DRAFT is a legit "I wrote it" artifact — check `in:drafts` too.
3. **Drive fullText sweep** — `files().list(q=f"fullText contains '{term}' and trashed=false")` for every variant; also `name contains '<term>'` for filenames that fullText misses. This found the PrestigeGreenMore topo survey when Gmail/Kelsa/sessions had nothing. Walk parent chains (files().get parents 2–4 levels) to identify the containing project folder (e.g. `PSCP > PrestigeGreenMore`).
4. **Kelsa** — pipelined per-account. See kelsa-read skill → "DRAAS account/pipeline map": DRA account ID 5, DRA Land Proposal 519 (property offers), DRA Sales Leads 10, DRA R&D 2000. Owner names inside a parcel's notes/attachments are NOT searchable — 0 results for a known owner (Alok/Puttaraju/nursery) is normal. Survey numbers as query terms are noise.
5. **gbrain** — `GBRAIN_HOME=/data/hermes/users/<slug>/.gbrain-writable gbrain search "<terms>" --json`. NOTE: ndr's, vkdas's and psingh's brain.pglite are corrupt (human_only) — plain-text notes dirs may be empty too. Don't burn time here if the PGLite error appears; move on.

## Interpretation rules

- **"Email from me to colleague X does not exist" → assignment was verbal.** Do not stop at "not found". Collect the artifacts found in other stores, then draft the follow-up email (To the colleague, CC the user-named others) restating the task, what's missing, and asking for status/ETA. Recipients must be verified via `find_contact.py` before drafting.
- **A topographic/survey PDF on Drive is the highest-value artifact** for a land parcel — OCR/vision it to extract survey numbers, owner labels, village, block, nursery/landmark names. These feed the follow-up email's "identify survey numbers offered" ask.
- Keep the user informed about WHERE you searched and what each store returned — they remember differently ("I use only draas.com") and correct the scope early.

## Worked example — Siddhapura / Prestige GreenMore (2026-08-17)

User asked: "pull up my email to Rahul Vinod Kumar Das re Siddhapura land in Jainagar behind Prestige Glenmore; Prakash was cc'd; asked Rahul to check how Prestige Glenmore/GreenMore changed park zone → yellow zone at BBMP, and identify the survey numbers offered by one Mr. Alok."

Result:
- No such email anywhere in draas.com (checked all variants). Assignment verbal.
- Drive: `PSCP` folder → `PrestigeGreenMore` folder → `20231015_PrestigeGreenMore_TopographicSurvey_3rdBlockJayanagar_LaraTech.pdf` (id 1QdBu8HVWeVeXbRKn31t6V9WnzbmUbLfv). Vision/OCR of the survey revealed: Siddapura, 3rd Block Jayanagar, **Sy No 27/2 + 27/3**, owner labels ALOK + PUTTARAJU, **Sri Ranganatha Nursery** on site, area 7027.46 sqm / 1A 29.45G, LaraTech survey #863, 15-Oct-2023.
- Kelsa: 0 for Alok / Puttaraju / nursery / Greenmore in Land Proposal 519.
- gbrain: corrupt PGLite, empty notes.
- Drafted follow-up to Rahul (vkdas@draas.com) cc Prakash (psingh@draas.com) asking for: BBMP park→yellow order, whether it covers ALL wrongly-classified survey numbers or just Prestige's, status/effort/ETA, full survey-number list; Prakash to pull RTCs + ECs + zoning map + Google the BBMP order. Draft ID r-8216796519665669248.
- Note: the `pscp-kingfisher-towers-context.md` reference in this skill already maps the PSCP folder contents (Hermitage, Golfshire, PrestigeGreenMore, KFT) — link that context when a PSCP search hits.