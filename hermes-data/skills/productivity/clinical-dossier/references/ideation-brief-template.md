# Ideation Brief Template

Send this to GPT-5.5 and Opus 4.8 via OpenRouter in Phase 3.

## Structure

```
You are an expert at presenting a complex [respiratory/general] case to a busy specialist for a second opinion.

## The Patient
{patient_name}, {age}yo {gender}, diagnosed with {diagnosis} ({date}). Current episode since {onset_date} triggered by {trigger}.

## The Core Problem
{chief complaint}. **{key clinical discriminator}** — this is a key feature.

## Current Treatment Course (current episode)
- {medication}: {dose} — {status}
- ...

Cough NOT under control despite {therapy}. ER visit {date} at {hospital}.

## Key Objective Findings

**Latest ({date} — {hospital} / {doctor}):**
- {test}: {value}
- ...

**Historical Trend:**
| Date | {parameter1} | {parameter2} | ... |
| ... | ... | ... | ... |

**Other normal findings:**
- {finding}

## What's Normal / Ruled Out
- ✅ ...

## The Two Competing Views (present neutrally)
**View A — {dx_name}**
- {supporting observation}
- ...

**View B — {dx_name}**
- {supporting observation}
- ...

## Tests NOT Done
- ❌ {test} — never performed
- ⏳ {test} — result awaited

## The Clinical Asks
Q1. ...
Q2. ...
...

---

Propose the optimal structure, ordering, and framing so a specialist grasps the case in under 5 minutes and can answer the asks. Specifically:
(a) what belongs on the first page vs. linked appendix
(b) how to present the competing views neutrally
(c) which 4–8 objective data points to surface up front and how
(d) how to phrase the asks so they're answerable
(e) what, if anything, is still missing for a strong second opinion

Do NOT diagnose. Return a concrete presentation blueprint.
```

## Output spec — final dossier sections

1. Title + one-line patient/context line (age, key comorbidities, date prepared)
2. THE SITUATION (≤120 words): current episode, persistent symptom, current treatment
3. WHAT WE'RE ASKING YOU (the doctor): 4-6 specific clinical questions
4. KEY OBJECTIVE FINDINGS: compact table — each row linked to source
5. WHAT'S NORMAL / RULED OUT: short bullet list
6. THE TWO COMPETING VIEWS: side-by-side or parallel sections, stated neutrally
7. TESTS NOT DONE / PENDING: table with clinical rationale
8. TREATMENT COURSE: day-by-day or period-by-period table
9. COMPLETE TIMELINE: all relevant clinical events in order
10. REPORT INDEX: every source file as clickable link, grouped by type

## Delivery format

- **Google Doc**: Created via HTML import (see `gws-automation` reference `html-to-google-doc-import`)
- **Email draft**: Gmail draft with opening note → full dossier as HTML body → PDF attachment (PDF exported from Google Doc)
- **Medical Facts Sheet**: Separate Google Sheet for "absolute facts that overrule prescriptions"
