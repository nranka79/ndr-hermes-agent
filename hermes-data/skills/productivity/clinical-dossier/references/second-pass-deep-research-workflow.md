# Second-Pass Deep Research Workflow

**Pattern:** After the initial clinical trials research + deep per-trial analysis is delivered and the user has reviewed it, they may ask for a "second pass" — a deeper, more targeted investigation based on what they learned.

**Trigger phrases:** "based on this, can we do one more detailed research", "I have just updated... now can you research", "what else can be done beyond [current recommendation]"

**This is NOT a do-over.** The user has already validated the first analysis. The second pass asks for exploration beyond what was covered.

---

## When to Use

- User says "based on this" after reading the dossier + trial analysis
- User asks about specific combinations or approaches not covered in the first pass
- User wants social/patient community evidence (Reddit, X/Twitter) in addition to published literature
- User questions the consensus recommendation (e.g., "beyond TKI+ICI, what else?")
- New clinical information (latest scan, new symptoms) arrives and reframes the direction

## Workflow

### Step 1: Read the full current analysis

Before starting new research, read:
- The dossier (Google Doc via Drive API)
- The PET-CT analysis document (if one exists)
- Past session research results

Capture the CURRENT state: what was already recommended, what drugs were already analyzed, what angle was the focus.

### Step 2: Identify the Gap

What is the user asking that was NOT covered? Common gaps after a first pass:

| First Pass Coverage | Second Pass Gap |
|---------------------|-----------------|
| TKI + ICI combos | Local therapies (radiation, debulking, stenting) for obstructing masses |
| FDA-approved trials | Off-label drug import pathways (CDSCO Form 12A, Named Patient Program) |
| Published literature | Patient experiences, doctor commentary on X/Twitter, Reddit discussions |
| Genomic-match trials | Drugs available in-country even without a trial |
| Pembro + Pazopanib | PI3K/AKT/mTOR pathway inhibitors, bispecifics, TIL therapy |
| Single-agent data | Combination therapy sequencing (ICI first, then ICI+TKI, then switch) |

### Step 3: Dispatch Parallel Subagents

Use `delegate_task(tasks=[...])` for independent research angles:

1. **Clinical trials & PubMed** — specific drugs/combos not in the first pass
2. **Social/community** — Reddit r/sarcoma, r/cancer, SmartPatients, SarcomaAlliance (via web search)
3. **X/Twitter** — if xurl is set up, search for sarcoma expert discussions
4. **API setup research** — if the user asks about tools not currently available (LinkedIn, X API, etc.)

### Step 4: Compile and Stack

Find the main dossier's end index via:
```python
doc = docs.documents().get(documentId=DOC_ID).execute()
last_element = doc['body']['content'][-1]
end_index = last_element['endIndex']
```

Append the new findings as the next sequential section (e.g., Section 12 if Section 11 was the first-pass deep analysis):

```python
docs.documents().batchUpdate(
    documentId=DOC_ID,
    body={'requests': [{
        'insertText': {
            'location': {'index': end_index - 1},
            'text': '\n\nSECTION 12 — SECOND-PASS RESEARCH: BEYOND TKI+ICI\n...'
        }
    }]}
).execute()
```

### Step 5: Organize Around Actionability

The second-pass findings should be organized differently from the first pass. The first pass was "what trials exist." The second pass is "what can we DO about this specific problem."

| Priority | Category | Examples |
|----------|----------|----------|
| 1 | Can start NOW | Off-label drugs available in India this week |
| 2 | Can arrange in weeks | Import drugs (Anlotinib, specific TKIs via CDSCO Form 12A) |
| 3 | Local interventions | Radiation to dominant mass, bronchoscopic debulking, stenting |
| 4 | Trial enrollment | Active recruiting trials (global or Asia-regional) |
| 5 | For future progression | Novel agents (bispecifics, oncolytic viruses) in Phase 1/2 |

For each option, include:
- Expected benefit (metabolic reduction? size reduction? symptom relief?)
- Time to effect (weeks vs months)
- Risk profile (bleeding, fistula formation, immune toxicity)
- Availability in patient's location

---

## Pitfalls

- **Don't repeat the first pass.** The user already has that. Focus ONLY on what's new.
- **Don't create a new supplement doc.** Stack at the end of the existing dossier (see `stacking-supplements-convention.md`).
- **Don't recommend something impossible to access.** If a therapy requires travel to another continent, label it as "Long-term / progression-only" — not as an immediate option.
- **Social evidence is low-quality but informative.** A Reddit thread of 5 patients is not a clinical trial, but it shows real-world experiences. Label the evidence level: "Published" vs "Case report" vs "Patient community".
- **X/Twitter search via xurl needs setup.** If `xurl` is not installed/authenticated, use `browser_navigate` to search X.com manually or note to the user that X API setup is needed.
- **Local therapies are outside the user's question scope** — but they should be raised anyway. A patient with airway obstruction needs a local solution even while systemic therapy works.
