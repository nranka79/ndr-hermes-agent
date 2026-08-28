# Treatment Monitoring Protocol — Patient-Facing HTML Email

Class of task: creating a structured **monitoring protocol** for a patient on a specific drug regimen — prescribing tests (what, how often, why) plus an at-home symptom monitoring checklist with detailed what-to-look-for guidance. Delivered as a well-formatted HTML email via Gmail draft.

This is **patient/family-facing** (not a doctor-facing second-opinion dossier). The goal is shared awareness and structured surveillance between the patient, family, and treating physician.

## When to Use

- User asks for a "list of tests to get done" for a patient on a specific medication
- User says "create a monitoring protocol" or "recommended test list with justifications"
- User wants a "complete checklist of symptoms to watch at home" for someone on a drug with known side effects
- User wants this sent as a nice email to family members

## Workflow

### Phase 1 — Research the Drug's Monitoring Requirements

For each drug in the regimen, identify:
1. **Known adverse effects** — cite published sources (FDA label, ASHP, Drugs.com, clinical trials)
2. **Required surveillance tests** — which ones, how often, why
3. **Grading system** — what's Grade 1 vs Grade 2+ (escalation thresholds)
4. **At-home symptoms** — what the patient/caregiver should watch for daily

For combination therapies (e.g., TKI + ICI), identify additive/overlapping toxicities.

**Key sources (in preference order):**
- FDA prescribing information (official label)
- ASHP / Drugs.com drug monographs
- Published clinical trials (Lancet, NEJM, JCO)
- UpToDate (if available)
- NCCN guidelines for supportive care

### Phase 2 — Structure the Email Content

Organise into these sections:

#### 1. Header
- Drug name(s), current dose, planned dose escalation
- Brief context: "Preventive surveillance plan for [Patient]"

#### 2. Blood Investigations
Each test as a card with:
- **Test name** (e.g., Liver Function Test)
- **Frequency** badged prominently (e.g., "Every 1–2 weeks")
- **Why** — what adverse effect it monitors, mechanism, clinical trial incidence rate, why early detection matters

Include: LFT, Thyroid panel, RFT, CBC — customise per drug.

#### 3. Urine Investigations
- Urinalysis, protein/creatinine ratio — for TKIs that cause proteinuria
- Frequency and thresholds for action

#### 4. Cardiopulmonary Monitoring
- Echo/LVEF if relevant
- BP monitoring (daily) — the most common TKI adverse effect
- Target thresholds

#### 5. At-Home Clinical Monitoring Checklist
Each item follows a **three-part structure**:

- **Title** — Symptom name + frequency (e.g., "Blood Pressure — Twice Daily")
- **What to look for** — Specific instructions: how to measure, what's normal vs concerning, what to inspect
- **When to report** — Concrete thresholds: numbers, durations, combinations with other symptoms

Each item must include:
- **Actionable detail** — not "monitor BP" but "sit quietly 5 min before measuring, same arm, same time daily. Report if systolic >140 or diastolic >90 for 3 consecutive readings."
- **Emergency signals** clearly labelled as REPORT IMMEDIATELY
- **Prevention tips** where applicable (moisturising for hand-foot, oral care for mucositis)

Typical items for TKI/ICI regimens:
1. BP (daily) — most common, dose-dependent
2. Weight (weekly) — fluid retention vs wasting
3. Fatigue (daily, scale 1–10) — differentiate anaemia vs hypothyroid vs adrenal vs drug
4. Appetite / Nausea / Bowels (daily) — diarrhoea is a TKI hallmark, immune colitis is more serious
5. Voice changes (daily) — dysphonia ~30% for TKIs
6. Hand-foot skin reaction (daily, inspect) — palmar-plantar erythrodysesthesia
7. Bleeding / bruising (daily) — VEGF impairs endothelial repair
8. Leg swelling / calf pain (daily) — DVT risk
9. Headache / confusion / visual changes (immediate) — RPLS warning
10. Shortness of breath / cough (daily) — differentiate TKI (thromboembolism, HF) vs ICI (pneumonitis)

#### 6. Important Disclaimer Box
- These guidelines are based on published safety data
- Dose modifications only by treating physician
- Any Grade 2+ toxicity must be reported immediately

### Phase 3 — HTML Formatting Guidelines

- **Container**: white card on light grey background, rounded corners, subtle shadow
- **Header**: gradient background with drug name and regimen
- **Test cards**: light grey/blue background, border-left accent colour
- **Section headers**: left border accent, bold, consistent colour per type
- **Frequency badges**: inline pill-style span with coloured background
- **Home checklist**: warm amber/yellow background (patient-facing, not clinical-blue)
- **Warning box**: red-tinted background with bold warning icon
- **Footer**: subtle separator, signature, italic note

Use inline `<style>` in `<head>` — Gmail strips external CSS. Google Workspace Gmail supports class-based CSS from `<style>` in the head.

**CSS classes to define:**
- `.container` — max 640px, white bg, rounded, shadow
- `.header` — gradient, white text, padding 32px 36px
- `.body-content` — padding 32px 36px
- `.section` — margin-bottom 28px
- `.section-title` — border-left accent, bold
- `.test-card` — light bg, border, rounded, padding
- `.test-meta` — pill badge with blue bg
- `.home-checklist` — amber/yellow bg
- `.checklist-item` — padding, bottom border
- `.item-title` — bold, brown colour
- `.item-detail` — lighter brown
- `.item-when` — inline badge with yellow bg
- `.warning-box` — red-tinted bg
- `.footer` — subtle top border, grey text

Responsive: include `@media only screen and (max-width: 500px)` rule reducing padding.

### Phase 4 — Draft Creation

Use gws_skill_bridge:

```python
from tools.gws_skill_bridge import call
resp = call('draft_create',
    service_name='google-draas',
    to='patient@email.com',
    cc='family@email.com',
    subject='Drug — Monitoring Protocol for Patient',
    body=html_body
)
```

The HTML body goes directly into the draft — the bridge handles MIME wrapping.

**For revisions after draft creation:**
The bridge has no update/trash operation. Delete old draft via Gmail API then create new:

```python
from tools.gws_auth import build_service
svc = build_service('gmail', 'v1', service_name='google-draas')
svc.users().drafts().delete(userId='me', draft_id='OLD_ID').execute()
# Then call draft_create again
```

Run the script via `/opt/hermes/.venv/bin/python` (the system python lacks googleapiclient).

### Phase 5 — User Review & Approval

1. Present a summary of what's in the email (by section)
2. Confirm recipient emails
3. Let the user review in Gmail Drafts
4. User sends it themselves from Drafts folder (never send autonomously per the hard rule)

## User Preference (Nishant, DRAAS)

When the user says "explain each symptom in detail" / "what to look for" / "give details":
- **Each checklist item needs a three-part breakdown**: what it is, how to monitor specifically (the action), and when it becomes concerning (the threshold)
- Example for fatigue: don't say "monitor fatigue." Say "Rate on scale 1–10 at same time daily. 1 = fully energetic, 10 = unable to get out of bed. Report if score increases 3+ points in a week, or fatigue is accompanied by shortness of breath on minimal exertion, or you feel unusually cold and sluggish (could be hypothyroidism)."
- **Urgency tiers**: mark as "report if" (monitor), "report" (sooner), and "report IMMEDIATELY" (emergency — RPLS, PE, GI bleeding)
- **Prevention**: include actionable prevention tips (urea cream for hand-foot, oral hydration for diarrhoea, same arm for BP consistency)
- **Consent**: always present a summary of what's in the email and confirm with the user before creating the draft

## Pitfalls

- **Draft revisions**: Must delete-old then create-new. Keep the draft_id from the first creation.
- **Gmail rendering**: Class-based CSS in `<style>` works in Google Workspace Gmail. Provide complete `<!DOCTYPE html>` document.
- **HTML body length**: Keep under ~50KB — very long bodies cause mobile rendering issues.
- **Medical accuracy**: Every "why" justification must cite actual clinical trial incidence rates. Use web_search to verify if uncertain.
- **Voice-to-text drug names**: Always confirm via web_search before committing (e.g., "azitinib" → "axitinib").
- **Deep reasoning for medical content**: Use `call_openrouter_model` with claude-opus-4.8 or deepseek-r1 for drug-side-effect research. Flash models not acceptable for clinical reasoning.
- **Resolve service_name first**: Always call `gws_resolve_account` before creating the draft.
- **Confirm recipient emails**: Check memory and user profile before creating. Never guess.
- **Use the hermes venv**: Run via `/opt/hermes/.venv/bin/python` — system python lacks googleapiclient.

## Related Skills & References

- `clinical-dossier` — Doctor-facing second-opinion dossier (complementary: different audience)
- `medical-certificates` — Parent skill; covers patient medical docs, prescription scheduling
- `references/new-medication-research-from-prescription.md` — Drug identification from user clues (e.g., Axitinib)
- `references/comprehensive-medical-brief.md` — A4 printable HTML brief for specialist visits
