---
name: llm-code-boundary
description: "Define the boundary between LLM (template/code generation, orchestration) and deterministic code (data merge, execution) — never use the generative model to produce reports containing structured data."
version: 1.0
author: Hermes Agent
license: MIT
---

# LLM ↔ Code Boundary — Data Integrity Principle

## Core Philosophy (Nishant, Jul 2026)

> *"These are exactly the cases where LLM or AI is only to be used to generate the code infrastructure because this is pure code. You are putting in data and you have a template and you push it into the template or you need to tell the LLM — suppose you want templates auto generated — you generate a template with placeholders for name and all the other data and then you ask it to use merge code to merge JSON data into the template. But it should never be asked to generate the report with the data because by virtue of it being generative there is a chance that one of the data point is changed because that's generative — it takes a probabilistic approach for the next token."*

> *"When it's about publishing data that can't be so — you need to use a clever use of LLM plus code always and you need to be very clear what is an LLM use case and what is a code use case. LLM to generate code to execute repetitive tasks is the way to go."*

## The Principle

| Role | What to Do | Examples |
|------|-----------|----------|
| **LLM** | Generate **template structure** with placeholders, generate **code/infrastructure** that merges data, **orchestrate** the workflow | Template: "Hi {{name}}, your plot {{plot_no}} at {{project}} is ready." Code: Python/JS merge script, Kelsa automation rule, cron job |
| **Deterministic Code** | Slot structured **data** into templates, **execute** repetitive tasks, perform **calculations** | String.format(), Jinja render, JSON merge, Python dict substitution, Kelsa field formulas |

## Anti-Patterns (Never Do These)

| ❌ Wrong (LLM generates data report) | ✅ Right (LLM generates template, code merges) |
|--------------------------------------|-----------------------------------------------|
| "Generate a WhatsApp message with Kishan's phone number +91 98450 20921 and email kishan@flamebackcapital.com" | "Generate a template with {{name}}, {{phone}}, {{email}} placeholders. Then run a merge script with the JSON payload." |
| "Write an email to Prakash with the list of 5 properties and their rates" | "Generate the email template with {{recipient}} and a table row {{#properties}}{{name}} — {{rate}}{{/properties}}. Let a Python script populate it from the sheet." |
| "Draft a letter with all the survey numbers and areas" (data values inside the prompt) | "Generate a letter template with placeholders for survey data. Load the data from the sheet and merge programmatically." |
| Any task where the user provides structured data and asks the LLM to *present* it verbatim | LLM generates the container/structure; code fills in the data values |

## Why This Matters

1. **Data integrity** — A probabilistic model can alter, omit, or hallucinate data values during generation. A single changed digit in a phone number, survey number, or cost figure causes real-world harm (wrong WhatsApp recipient, wrong legal document).
2. **Reproducibility** — Code+template gives the same output every time for the same input. LLM generation gives a different result each time.
3. **Auditability** — When data is merged by code, you can trace exactly which input produced which output. LLM-generated text is opaque.
4. **Token cost** — Feeding data through the LLM costs tokens. Template+merge costs zero tokens for the data portion.

## When the User Provides Data + Asks for Output

**The correct flow for ANY task where structured data needs to be presented in a message/document:**

1. **LLM step:** Determine the output format (template structure, placeholders, layout, styling)
2. **Code step:** Read/collect the data from source (sheet, API, file, user-provided JSON)
3. **Code step:** Merge data into template using deterministic string operations
4. **Code step:** Deliver the final output (WhatsApp link, HTML file, Drive doc, email)

### Practical DRAAS Examples

| Task | LLM Does | Code Does |
|------|---------|-----------|
| WhatsApp message with contact info | Creates template: "Hi {{name}}, please connect with {{contact_name}} at {{phone}}. Context: {{context}}" | Reads name/phone from contacts sheet → substitutes into template → generates wa.me link |
| Kelsa automation | Generates the automation rule logic (trigger + action + field mapping) | Executes via Kelsa MCP tools |
| Cron job for weekly reports | Generates the cron job prompt with placeholders for data | Reads data from sheet/API → merges → delivers |
| Legal document with client data | Drafts the legal clause structure with {{clients}}, {{property}}, {{amount}} placeholders | Reads client data from sheet → populates → generates final document |
| Email with table of values | Creates the HTML email template with {{table_rows}} placeholder | Reads data from sheet/API → builds table rows → substitutes into template → sends |

## Implementation Patterns

### Pattern 1: Template String + JSON Merge (simple)

```python
# LLM generates this template:
template = "Hi {name}, please connect with {contact}. Their number is {phone}."

# Code loads data and merges:
data = {"name": "Anbu", "contact": "Amit Pujari", "phone": "+91 87479 31502"}
message = template.format(**data)
```

### Pattern 2: HTML Template + JavaScript (for interactive cards)

```python
# LLM generates the HTML template:
html = """
<div class="card">
  <h2>Instructions for {{name}}</h2>
  <ul>
  {% for step in steps %}
    <li>{{step}}</li>
  {% endfor %}
  </ul>
</div>
"""

# Code loads data and renders:
from jinja2 import Template
t = Template(html)
output = t.render(name="Anbu", steps=["Contact Amit", "Visit site", "Report back"])
```

### Pattern 3: Python Script Generator (for repetitive tasks)

```python
# LLM generates a Python script with placeholders:
script_code = """
contacts = {{contacts_json}}
template = {{template_json}}
for c in contacts:
    msg = template.replace('{name}', c['name'])
    send_whatsapp(c['phone'], msg)
"""

# Code serializes the data and executes:
import json
contacts = [{"name": "Anbu", "phone": "918150029900"}]
template = "Hi {name}, please connect..."
final_script = script_code.replace("{{contacts_json}}", json.dumps(contacts))
exec(final_script)
```

### Pattern 4: Cron + Kelsa Automation (for recurring tasks)

```python
# LLM generates the cron job + template:
cron_prompt = f"""
When this cron runs:
1. Load data from [source]
2. Apply {template} to each row
3. Deliver to [recipient]
"""

# The cron infrastructure reads data, merges, delivers — LLM only touches template design, never individual data values.
```

## Verification — Did You Follow the Principle?

Checklist before executing any task involving structured data + output:
- [ ] Did I separate the template design (LLM) from the data merge (code)?
- [ ] Is the data loaded programmatically from its source (sheet, API, file), not from my own prompt?
- [ ] Are placeholder names used in the template, not actual data values?
- [ ] Would a different run with the same data produce the identical output?
- [ ] If the data changes, does only the merge step need to re-run (not the LLM)?

## Edge Cases

### User Provides Data Verbatim in Their Instruction

When the user dictates the complete message with data values in their voice/text instruction, **it is safe to use those values directly** — the user is acting as the data source, and you are acting as the merge executor. The data came from the user, not from the LLM's probabilistic generation.

**Example:** User says *"Send to Anbu: Hi Anbu, please connect with Amit Pujari at +91 87479 31502"* → The user provided both the template AND the data values. Execute directly.

**When to still use the pattern:** If the user's dictated message follows a recurring structure (same format, different values each time), suggest creating a template + script so future runs don't need re-dictation.

### User Corrects Data Values

When the user corrects a phone number, name, or other data point:
1. **Immediate fix:** Just update the value in the generated output (fast path)
2. **For recurring tasks:** Use this as a signal that the data source (sheet, memory) was stale — update the source AND create a template+merge workflow so the issue doesn't recur

## Related Skills
- messaging-drafts — umbrella for email/WhatsApp drafting; apply this principle when creating drafts
- confirm-before-actions — always confirm data values before acting; this principle ensures values aren't accidentally altered by generation
- contact-phone-lookup — sources for contact data; applies Pattern 1 (template + merge) for WhatsApp links
- gbrain-ops — personal knowledge brain; structured data retrieval falls under code, not LLM

## Consolidation Note

This skill absorbed the former `llm-data-boundary` skill, which covered the identical principle. The key insight from that skill is highlighted in its Kelsa integration note: Kelsa pipelines are a natural home for the template+merge pattern, where LLM sets up pipeline structure and Kelsa handles data flow deterministically. Full original text archived at `~/.hermes/skills/.archive/llm-data-boundary/SKILL.md`.
