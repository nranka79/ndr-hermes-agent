---
name: youth-athletic-training-programs
description: Design safe, age-appropriate strength and athleticism training programs for NDR's children (currently a 12-year-old soccer goalkeeper) - reconcile parent constraints, construct sessions, source VERIFIED instructional video links per exercise, and deliver a trainer-ready PDF (uploaded to Drive, shared, and emailed to family). Triggers - exercise routine for my child, training program, workout plan, goalkeeper or athlete conditioning, resistance band / bodyweight program for a minor.
version: 1.0.0
author: Hermes Agent
---

# Youth Athletic Training Programs

Design fitness / conditioning programs for NDR's children and deliver them in a
parent-trainer-ready form (PDF + verification videos). The resident athlete pattern is a
12-year-old soccer goalkeeper (Rivaan), training with a paid trainer, at a residence gym that
restricts under-15s from the indoor gym (so sessions run in the outdoor common area with parallel
bars + portable light equipment).

## Who sets the requirements (usually BOTH parents)
- **NDR (father):** tends to push a "resistance training to max capacity, build muscle during
  growth years" bodybuilding philosophy and often specifies gym weights brought outside.
- **Roshini (mother):** typically overrides with the operative constraint sheet — sends the
  category list, and restrictions like "no weights", "band max 5 kg", "on non-football days".
- The final program MUST reconcile to the MOST RESTRICTIVE / most-recent parent instruction.
  When the two conflict (NDR says "bring weights" but Roshini says "without weights, band ≤5kg"),
  follow Roshini's constraint and note the reconciliation to NDR in the reply — don't silently
  pick one.

## Training philosophy to embed (age-appropriate — important)
- At ~12, resistance training builds **strength + neural coordination**, NOT visible muscle
  (hypertrophy needs puberty testosterone). Frame NDR's "max capacity" instinct as: right
  timing to lay the FOUNDATION (movement patterns, tendon/bone strength, neuromuscular
  wiring) that lets him add muscle safely during his growth spurt.
- **Train hard but NOT to failure every set / NOT max load.** Injury risk at this age (growth
  plates, Osgood-Schlatter, apophysitis) lives in max-load grinding and near-failure reps.
  Keep effort "hard but clean form"; stop 2–3 reps before failure when form breaks.
- Typical sets/reps: strength 8–15 controlled reps; plyometrics low reps (3–6), explosive, full
  recovery. Always state this so the trainer doesn't apply adult bodybuilding loading.

## Session structure (40–45 min each)
When a category list is given (e.g. coordination, balance, strength & power incl. plyo,
reaction, speed, posture), build sessions that cover ALL categories every day but ROTATE
exercises between Session A and Session B (variety + broader coverage):
- Warm-up / mobility (5 min) → Coordination / agility ladder (5) → Speed & change-of-direction
  (5) → Strength (squats, glute bridge, band walks, push-ups / lunges, planks, band squats) (12)
  → Power/plyo (jump squats, box jumps / lateral bounds) (6) → Balance (single-leg, eyes-closed) (5)
  → Reaction (GK drill, tennis ball) (5) → Posture / cool-down (4).
- Use the outside parallel bars for bodyweight (feet-elevated push-ups / assisted dips) since the
  indoor gym is off-limits under 15.
- Include a weekly-rhythm note (program on NON-football days, at least 1 rest day) and a
  4–6 week progression section (progress ONE variable at a time, only when form is clean) plus a
  red-flags section (knee/heel/groin pain → physio; Osgood-Schlatter).

## Verified video links (CRITICAL — never fabricate)
Every exercise must carry a real, working YouTube link. **Never guess a video ID.** Use the
`research-web-tools` → `references/youtube-video-link-sourcing.md` technique: browse
`youtube.com/results?search_query=…`, console-extract `a#video-title` hrefs, clean to
`watch?v=<ID>` (strip `&pp=`/`&t=`). For a program with many categories, dispatch PARALLEL
subagents (one per 2 categories) each instructed to extract REAL links via the browser+console
method and return cleaned URLs — never fabricated. Prefer full-length instructional over Shorts;
prefer credible form-demo channels (goalkeeper channels, physio channels, IU-Health/Bupa/NASM/
Bowflex type). Focus on the goalkeeper's needs: agility, coordination, single-leg balance, GK
reaction drills, acceleration/COD, posture (hip flexors, wall slides, thoracic mobility).

## Delivery workflow (trainer-ready)
1. Write the program as clean Markdown (`/data/hermes/projects/<slug>/goalkeeper-program-age12.md`)
   AND a styled HTML version (session blocks, tables, video links, callout boxes for philosophy
   + red flags).
2. Convert HTML → PDF with WeasyPrint (install into a uv venv if not present:
   `uv venv /tmp/weasy_venv && uv pip install --python /tmp/weasy_venv/bin/python weasyprint`).
3. **Upload the PDF to Drive** using the account that matches the audience — for family, that's
   `google-gmail` (nishantranka@gmail.com), NOT work draas. Rename appropriately
   (e.g. "Rivaan Goalkeeper Training Program - Age 12.pdf").
4. **Share editor access** to the family members (e.g. Roshini rnr@draas.com, Rivaan
   rankarivaan@gmail.com).
5. **Draft (never send) a Gmail** to the family explaining setup + WHY + the category list, with
   the Drive PDF link, asking them both to review. Sender = the personal gmail account
   (family mail rule from `email-drafter`). Include the review ask and note it'll be shared with
   the coach once confirmed.

## Pitfalls
- Don't apply "max capacity / to failure" loading to a 12-year-old — encode the age-safe
  philosophy block explicitly; both parents review it.
- Reconcile conflicting parent instructions explicitly in your reply to NDR (state which
  constraint you followed and why).
- Verify YouTube links are REAL and clean; fabricated/guessed IDs will fail in email/PDF delivery.
- Harbor: family emails go from nishantranka@gmail.com; never auto-send (create a DRAFT; tell
  NDR it's in Drafts).
