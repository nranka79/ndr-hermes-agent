# Scientific Research Deep-Dive

## When to use this reference
- User asks to elaborate on a scientific/health/medical claim from a video, article, or podcast
- User asks "what does the study actually say" or "explain the mechanisms behind X"
- User wants source study identification, evidence quality assessment, or practical translation of research findings
- Trigger pattern: initial summary → user pushes for deeper mechanism explanation and source tracing

## Workflow

### Phase 1: Initial request handling
- Provide a concise structured summary FIRST (findings, source, key quotes)
- Structure: Core Premise → Key Findings (with numbers) → Mechanisms → Actionable Takeaways
- Cite the specific study name, journal, authors, and publication year
- If the source is a video, extract its title, channel, and interviewee

### Phase 2: Deep-dive (when user asks for elaboration)
Do NOT re-summarize at the same level. Go deeper on:

#### A. Source study identification
- Find the actual peer-reviewed paper(s) being referenced
- Search for: study title, corresponding authors, journal, PMID/DOI
- Extract: cohort size, study design (RCT vs prospective cohort vs cross-sectional vs meta-analysis vs mouse model), follow-up duration
- For human studies: note important confounders and adjustments

#### B. Evidence quality assessment
Be explicit about what type of evidence supports each claim:

| Evidence type | Strength | Example from this session |
|---|---|---|
| Meta-analysis of RCTs | Strongest | — |
| Prospective cohort (20k-200k+) | Strong | Malik 2016, 206k participants, 24yr follow-up |
| Cross-sectional analysis | Moderate-suggestive | "Double diabetes prevalence" finding — correlation, not causation |
| Mouse model (genetically diverse, mid-life intervention) | Mechanistic | LDMM mouse study — Het-3 strain, gold standard for aging |
| Single-arm / uncontrolled | Weak | — |
| In vitro / cell culture | Mechanistic only | — |

Always distinguish: **mouse ≠ human**, **cross-sectional ≠ longitudinal**, **prevalence ≠ incidence**.

#### C. Mechanism explanation (the "why")
This is what differentiates a good deep-dive from a superficial one. For each finding:

1. **Identify the biological pathway** (e.g., methionine → mTOR → IGF-1/FGF21)
2. **Explain the direction of effect** — what goes up, what goes down, and why that matters
3. **Name the specific molecules/hormones** (e.g., GLP-1, FGF21, IGF-1, growth hormone)
4. **Distinguish correlation from causation** — what's a mediator vs confounder vs direct effect
5. **Use analogy** when helpful (e.g., "GLP-1 is the same pathway Ozempic targets")

#### D. Category differentiation
When a study makes a broad claim about a category ("animal protein", "red meat", "dietary fat"), ALWAYS break it down:

- **Within "animal protein"**: Red meat ≠ poultry ≠ fish ≠ dairy ≠ eggs. They have different methionine content, different fat profiles, different heme iron, different epidemiological associations.
- **Within "plant protein"**: Legumes ≠ nuts ≠ grains ≠ soy. Different amino acid profiles, different fiber content, different co-nutrients.
- **Within "fish"**: Fatty fish (salmon, mackerel) have omega-3s that may offset risks; white fish (tilapia) has different profile.
- **Always explain the distinctions and why they matter mechanistically.**

### Phase 3: Practical translation
Give the user something they can actually use:

- **Concrete numbers** (e.g., "3% of calories from red meat → nuts = 20% risk reduction")
- **Food-level guidance** (e.g., "a 6oz chicken breast has 195% of daily methionine — one serving already exceeds the Goldilocks zone")
- **Comparison to common reference points** (e.g., "Ozempic targets GLP-1; this diet increases GLP-1 naturally")
- **What to do more of AND less of** — don't just say "eat less X", say what to replace it with

### Phase 4: Verification by source divergence
- If the user pushes further, verify claims across MULTIPLE independent sources:
  - The study itself (PubMed/DOI)
  - News/press releases from the institution (USC, Harvard)
  - Independent science journalism (MedicalXpress, Nature News)
  - Cross-reference with meta-analyses or systematic reviews on the same topic
- Note where sources agree and disagree

## User-specific communication preferences
- When asked to elaborate, go deep on MECHANISMS (pathways, molecules, direction of effects) — this is what distinguishes a satisfying answer from a superficial one
- Always distinguish between categories within a label — "animal protein" is not one thing; break it down
- Cite specific study details (authors, journal, cohort size, follow-up years, exact hazard ratios with confidence intervals)
- Explain evidence quality: mouse vs human, cross-sectional vs longitudinal, prevalence vs incidence
- End with practical, food-level or action-level takeaways
- Source the actual papers — don't just repeat media claims about the papers

## Pitfalls
- **Don't conflate evidence types**: Cross-sectional "prevalence doubled" is not the same as prospective "risk increased 13%." Be precise about which is which.
- **Don't flatten categories**: The user will push back on "animal protein = bad" if fish is included. Pre-empt that by distinguishing within categories proactively.
- **Don't stop at "what" — explain "why"**: The mechanism is what the user wants when they ask for elaboration. If you only give more numbers, they'll ask again.
- **Don't invent mechanisms**: If the video/study didn't explain why, search for the mechanism separately. Use web_search for the specific pathway + mechanism question.
- **Don't oversimplify the Goldilocks zone**: It's not "less is better" or "more is better" — it's context-dependent. State both sides of the U-shaped curve.
- **Mouse model caveats**: Always note when the primary data is from mice. The mechanism may be conserved, but the diet composition and dosages don't translate 1:1.
- **Check for conflicts of interest**: Valter Longo holds equity in L-Nutra (FMD products). Mention this when relevant — it doesn't invalidate the science but is important context.
