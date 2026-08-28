# LLM + Code Boundary Principle (Nishant's Architecture)

## Core Principle

LLMs should be used to **generate code infrastructure** (templates, merge scripts, pipeline orchestration), not to generate the final output that contains data.

**The division:**

| What LLM does | What code does |
|---|---|
| Generate templates with placeholders | Deterministically merge JSON data into templates |
| Architect the workflow/pipeline | Execute the data transform and merge |
| Orchestrate when to run which job | Format, validate, and deliver the output |
| Generate creative content (copy, images) | — |

**Why:** An LLM takes a probabilistic approach for the next token. When generating a report containing specific data points (amounts, names, dates, addresses), there is ALWAYS a risk that the generative process alters a data point. This is unacceptable for any output where data integrity matters.

**The pattern:**
1. LLM designs the template structure (with placeholders)
2. Code extracts data from source (API call, database, file read)
3. Code merges data into template (deterministic, no generative step)
4. LLM orchestrates when to run the pipeline (scheduling, conditional triggers)
5. Result: data integrity is maintained because no generative step touches the values

## Application to This Environment

### WhatsApp message generation
- LLM: draft the message content, decide what to say
- Tool (`whatsapp_link`): encode the URL correctly (deterministic)
- The message itself is creative/opinion content — LLM-generated text is appropriate here because it's the user's *thoughts*, not published data

### Report/email generation
- LLM: draft the text, structure, tone
- Code: insert specific data points (amounts, dates, names) — these must come from deterministic extraction, not from the LLM's generated text
- **NEVER** ask the LLM to generate "the report with the data" — that's a probabilistic step over data

### Kelsa pipelines
- Templates define the data structure
- Automations run deterministic rules (data_entry prerequisites, field calculations, stage jumps)
- LLM orchestrates the workflow design and the scheduling
- Perfect example of the principle in practice

## Pitfalls

- **"Just generate the report"**: Asking an LLM to generate a report containing specific numbers from a data source is wrong. The LLM will produce plausible-looking but possibly wrong numbers.
- **"Write the email and include the invoice amount"**: The LLM should write the email with a placeholder; code inserts the actual invoice amount after the generative step.
## Session Examples (Jul 2026)

### Example 1: WhatsApp Philosophy Message (creative content — LLM direct generation OK)

Nishant dictated a WhatsApp message sharing his philosophy on LLM usage. This was creative/opinion content — the message was his *thoughts*, not published data. Direct LLM generation was appropriate because there were no data points (amounts, dates, names) that could be corrupted.

Contrast with: if he had asked me to send Kishan a summary of share transaction details (amounts, share counts, dates), that would need the template+merge pattern.

### Example 2: Kannada Document Translation (LLM generates template, code produces output — CORRECT)

Nishant sent a Kannada PDF (Serenity Hill View land conversion cancellation letter from DC office). The workflow:

| Step | What | Why |
|------|------|-----|
| 1. Translation | LLM (Gemini 2.5 Flash) translates the Kannada text directly from the image | Translation is inherently generative — there is no deterministic source-to-target mapping |
| 2. HTML template | LLM designs the HTML+CSS that mimics the original letter's layout, spacing, margin, indent structure | Layout design is creative/structural — LLM's strength is generating the right markup |
| 3. Data merge | The translated text is *inserted into the HTML template* by code (string formatting, not generation) | Critical boundary: the translated text from step 1 is treated as a completed data blob, not re-processed |
| 4. PDF generation | `playwright` or `weasyprint` converts the deterministic HTML to PDF | Pure code — no generative step touches the final output |
| 5. Drive filing | Upload to correct project folder + rename per convention | Pure code — deterministic |

**Where the boundary was respected:** The Gemini model received the image and produced a single translation. That translation was then treated as an opaque data blob — it was inserted into the HTML via Python string operations, never re-generated or modified by any LLM. The HTML template structure was LLM-designed, but the data within it was not.

**Where it would go wrong:** Asking Gemini to "also format this as an HTML page" in one shot — the model would re-generate the translation within its response, creating a second opportunity for hallucination. Always separate translation from template rendering.
