---
name: youth-athlete-training-program
description: "Design age-appropriate strength/conditioning programs for NDR's children (e.g. Rivaan, a 12-year-old soccer goalkeeper) and youth athletes generally. Covers youth-safe training principles, session structuring, goalkeeper/field-sport positional needs, and the household constraints (no weights under gym age limit, band ≤5kg, sessions on non-sport days)."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [youth training, kids fitness, goalkeeper, soccer, resistance band, program design, athletics]
---

# Youth Athlete Training Program Design

Design strength/conditioning programs for NDR's children and youth athletes. He asks
for structured, deliverable-quality training programs (with optional YouTube video links)
for his kids, who are in competitive sport. Rivaan (12) is a **soccer goalkeeper** in
Bengaluru FC's Young Blues Elite U13 squad; there are other children (e.g. Ruhaan).

## Triggers
- "Design an exercise/workout/training program for [child's name]"
- "[child] plays [sport], coach wants X workouts a week"
- "resistance band / no weights / parallel bars" for an under-age child
- Shared with the child + a parent for review; possibly a coach.

## Household constraints to surface early (Rivaan's case, apply by analogy)
- **Gym age rule:** the apartment gym bars under-15s, so the child trains in the OUTDOOR
  common area (parallel bars are available there).
- **No free weights** (Mum's ruling) — bodyweight + a light **resistance band ≤ 5 kg** only.
- **Sessions on NON-sport days** (rest days from football), not football days.
- **Preferred category set** (from **Roshini Ranka**, the boys' mother — treat as the
  parent-given brief): coordination, balance, strength & power (incl. plyometric),
  reaction, speed, and posture-correction exercises.
- **Session length ~40–45 min**, frequency **2x/week** (per the soccer coach).

## Youth-safe training science (read this before designing — this is the core value)
- **At ~12, resistance training builds STRENGTH + NEURAL COORDINATION, NOT visible muscle.**
  Real hypertrophy needs puberty-level testosterone. So the goal is foundation: clean
  movement patterns, tendon/bone strength, neuromuscular wiring that lets them add muscle
  safely during the growth spurt. Dad's "max capacity / destroy & rebuild" instinct is
  right on TIMING (this is exactly when to build the base) but the loading scheme is wrong
  for a child.
- **Do NOT train to failure every set, and do NOT use max/near-max load at this age.** The
  injury risk lives in growth plates and apophysitis (Osgood-Schlatter — pain below kneecap,
  heel pain, sharp groin/hip pain; all red flags to stop + physio). Keep effort "hard but
  clean form": stop 2–3 reps before failure whenever form breaks. Perfect form > heavy weight.
- **Rep scheme:** most strength sets at **8–15 reps, controlled tempo**. Plyometrics/power
  done FRESH, explosive, LOW reps (3–6) with full recovery. This is the safe sweet spot.

## Session structure (fits the parent brief; each session hits ALL ~6 categories)
Universal warm-up / dynamic mobility (5 min), then rotate exercises across the two days so
each day covers all categories but variety keeps it interesting:
1. Coordination (agility ladder / footwork) — 5 min
2. Speed & change of direction — 5 min
3. Strength (squats, glute bridges, band walks, push-ups, lunges, band squats, planks) — 12 min
4. Power / plyometrics (jump squats, box jumps, lateral bounds) — 6 min
5. Balance (single-leg, eyes-closed) — 5 min
6. Reaction (goalkeeper / hand-eye drills) — 5 min
7. Posture correction / cool-down (hip flexors, wall slides, thoracic mobility) — 4 min

Adjust exercise selection to position: **goalkeeper** → emphasize explosive power,
quick reactions, single-leg balance, agility/coordination, speed off the mark, soft landing.

## Deliverable format
- Full program as a clean, printer/trainer-friendly document: markdown source + an
  **HTML → PDF** (see professional-documents / html-presentations for the WeasyPrint pattern;
  if weasyprint is absent, install it into a throwaway uv venv: `uv venv /tmp/x && uv pip
  install --python /tmp/x/bin/python weasyprint`).
- Include **real YouTube video links** for form/breathing per exercise — use the
  `research-web-tools` → `references/youtube-video-link-sourcing.md` method (browser +
  `a#video-title` console extraction; NEVER fabricate IDs). Prefer full-length instructional
  videos over Shorts; search "for kids"/"for youth athletes"/"for beginners" when age-appropriate.
- Offer to share via Drive: upload the PDF to the appropriate personal account, grant editor
  to the parent + child, and put the Drive link in the email (see email-drafter /
  google-workspace for the upload + permission + draft flow).

## Session-specific detail
- Resolved contacts, household constraints, artifact/Drive/email IDs for the Rivaan run:
  `references/rivaan-goalkeeper-program.md`.

## Email sharing rule
Family emails (to the child + parent) must be drafted from **nishantranka@gmail.com**
(personal), NOT ndr@draas.com — see `email-drafter` skill. The email is always a DRAFT,
never auto-sent. Child + parent both get editor access on the Drive PDF and are asked to
review; once approved it goes to the coach.

## Pitfalls
- Don't blindly apply adult bodybuilding loading to a child — reconcile Dad's "max capacity"
  with youth-safe loading explicitly (explain in the deliverable, don't just silently do one).
- Verify every contact / email address (esp. coaches) via find_contact.py / People API —
  never guess. If a name (e.g. a coach "Keren") isn't in contacts, flag it and ask rather
  than inventing an address.
- Full-length instructional videos beat Shorts for form teaching.
