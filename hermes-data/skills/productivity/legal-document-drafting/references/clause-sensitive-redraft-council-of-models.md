# Clause Redraft — Council-of-Models with Tone-Softening (Jul 2026)

**When to use:** A legal document clause is legally effective but uses harsh/defensive language that could alienate the counterparty (purchaser, partner). The goal is to preserve full legal protection while reframing the language as collaborative and informative.

## The Core Technique: Reframe, Don't Exclude

| ❌ Harsh/Defensive | ✅ Soft/Effective |
|---|---|
| "shall not be covered under Defect Liability Period" | "is not a defect under RERA or the National Building Code" |
| "The Promoter expressly disclaims any liability whatsoever" | "shall be managed as a routine maintenance matter by the Owners Association" |
| "as is where is condition" | "the Owners Association shall endeavor to maintain... based on professional advice" |
| "The Purchaser shall not make any claim" | "such seepage shall not, by itself, be treated as a structural defect" |

**Rule:** Frame the same legal outcome positively. Instead of saying what ISN'T covered, say what the arrangement IS. Instead of disclaiming liability, describe the alternative accountability framework.

## Workflow

### Step 1 — Extract the original clause
Read the Google Doc via Docs API or Drive export. Get the verbatim clause text including sub-clauses.

### Step 2 — Craft a detailed design brief
Capture: legal outcome needed, tone objective (collaborative), specific pain points in existing language, reframing strategy, key terms to include (e.g., "endeavor", "professional advice", "routine maintenance").

### Step 3 — Run parallel model redrafts
Give the exact same brief to multiple models via OpenRouter (GPT 5.5, Claude, Gemini). The council-of-models approach: two models produce independent redrafts, then a third evaluates both and produces a final synthesized version. **Practical shortcut:** User may approve the first good redraft directly.

### Step 4 — Present as HTML/CSS for Word copy-paste
Format as standalone HTML: Times New Roman 12pt, justified, proper clause numbering, sub-clause labels, a "Changes from original" note box. Deliver via `MEDIA:` path.

## Worked Example: Clause 17 — Basement Seepage (Ranka Iris Sale Deed)

**Original issue:** Harsh language ("expressly disclaims any liability", "as is where is", "shall not be deemed a structural defect").

**Reframing strategy:**
- Renamed from "ACKNOWLEDGMENT AND RESPONSIBILITY" to "ACKNOWLEDGMENT AND ROUTINE MAINTENANCE"
- (b): "shall not be treated as a structural defect under RERA or NBC" instead of "shall not be covered under defect liability"
- (c): added "shall endeavor" + professional management framing
- (f): replaced blanket disclaimer with "Promoter responsible for structural defects; routine seepage managed as maintenance"

## Pitfalls
| ❌ Don't | ✅ Do |
| Remove substantive protections | Re-word but preserve legal effect |
| Make it ambiguous | Keep legal outcome as clear |
| Add fluff | Polite ≠ wordy |
| Keep defensive clause titles | Rename to reflect positive framing |
