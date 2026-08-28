---
name: comprehensive-research
description: Deep-dive research across multiple dimensions of a complex topic — split into parallel subagent tasks, compile into a single well-formatted HTML report, deliver to Drive TMP folder.
version: 1.0.0
author: Hermes (auto-generated via user session)
platforms: [linux, macos]
metadata:
  hermes:
    tags: [research, delegate_task, html-report, drive-upload, eb5, taxation, trust, immigration]
    homepage: https://hermes-agent.nousresearch.com/docs
---

# Comprehensive Deep-Dive Research

Use this skill when the user asks for **exhaustive, multi-dimensional research** on a complex topic where many subtopics need parallel exploration. The canonical pattern: split the topic into 3+ parallel research tracks → delegate to subagents → compile → format → deliver to Drive.

## When to Use

**Triggers:** "thorough research on X", "analyze all aspects of Y", "deep dive into Z covering A, B, C, D", "create a detailed report on [topic] covering every angle", "examine all possible aspects and risks of [topic]".

This is **not** for simple web searches, single-article lookups, or vendor comparisons. Use it when the research genuinely spans multiple independent dimensions that can be explored in parallel (e.g. process + taxation + legal risks + exit strategy).

## Workflow

### Step 1: Break Down the Topic

Identify 3–4 independent research dimensions. Each must be self-contained enough to be researched by a separate subagent. Examples from the canonical EB-5 session:

| Dimension | Focus |
|-----------|-------|
| Process & Timeline | Application steps, forms, fees, visa bulletin, physical presence |
| Domestic Taxation | Income tax, estate tax, gift tax, reporting (FBAR/FATCA) |
| Trust / Legal Structures | Foreign trust tax treatment, grantor rules, 3520 penalties |
| Exit / Risk Strategy | Failure scenarios, expatriation tax, green card surrender |

**Limit:** Maximum **3 concurrent subagents** (configured by `delegation.max_concurrent_children` in config.yaml). If you have 4 dimensions, run the first 3 in parallel, then the 4th separately.

### Step 2: Write Subagent Task Descriptions

Each `delegate_task` (in a `tasks` array for parallel execution) must include:

- **`context`**: The user's specific situation — their profession, asset profile, family composition, jurisdiction (e.g. Indian HNI with real estate, business ownership, spouse and two kids, considering US immigration). The subagent has NO memory of the conversation, so be comprehensive.
- **`goal`**: A self-contained research brief covering exactly what that dimension needs. Include specific questions, edge cases, and the user's existing understanding to validate/correct.
- **`toolsets`**: `["web"]` for research tasks. Add `["terminal", "file"]` if the subagent needs to write files.

### Step 3: Execute Parallel Research

Use `delegate_task` with the `tasks` array:

```python
delegate_task(tasks=[
    {"goal": "...", "context": "...", "toolsets": ["web"]},
    {"goal": "...", "context": "...", "toolsets": ["web"]},
    {"goal": "...", "context": "...", "toolsets": ["web"]},
])
```

### Step 4: Compile the Report

Build a comprehensive HTML document with:
- **Cover page** with title, date, subject, confidentiality notice
- **Table of contents** linking to all sections
- **One section per research dimension** with clear headings
- **Risk matrix** (if applicable) — severity-rated risks with mitigations
- **Summary tables** for numerical data (timelines, exemptions, costs)
- **Next steps / action plan** section

**CSS requirements:**
- Dark/navy header for the cover (`#1a365d` primary, `#2b6cb0` secondary)
- Card-style sections with rounded corners and subtle borders
- Info/warning/danger/success box styles (colored left borders)
- Responsive tables with alternating row colors
- Timeline component (left-rule with circles) for process flows
- Print-friendly (set `@media print` rules)
- Mobile-friendly (break points at 600px)

### Step 5: Upload to Drive TMP Folder

After writing the local HTML file:

1. Find the TMP folder on Drive: `drive.files().list(q="name = 'TMP' and mimeType = 'application/vnd.google-apps.folder' and trashed = false")`
2. Upload using `MediaFileUpload` with HTML mimetype
3. Capture the file ID and `webViewLink`
4. Report the link to the user

### Step 6: Report to User

Provide:
1. Short summary (2-3 bullets per section)
2. The key actionable findings (critical risks, decisions needed)
3. Link to the Drive document
4. Offer to open it in browser if they want to view immediately

## Pitfalls

- **Subagent web research can return EMPTY:** delegated tasks with `toolsets: ["web"]` may come back with no results at all (toolset/tooling failure, not a content problem). The subagents' `web_search` calls can silently produce nothing while the task "completes". If all three tracks come back empty or stubbed, do NOT re-delegate and do NOT give up — run the research directly in the parent session with the keyless research ladder (Google News RSS for discovery + direct site fetches + x_search). See the `indian-ipo-evaluation` skill for a proven keyless ladder that works from the VPS without Tavily/Apify.
- **3-subagent limit:** `max_concurrent_children` may be 3. Split 4 tasks into 3+1 (parallel then sequential) rather than trying to batch all 4.
- **Subagent summaries are self-reports:** A subagent claiming "file written" may be wrong. For the HTML compilation, always write the file yourself in the parent session rather than trusting a subagent to do it.
- **Context completeness:** Each subagent needs the user's full situation in its `context`. Subagents have zero memory of the conversation. Missing context leads to generic, useless research.
- **HTML over Markdown:** The user asked for "presentable, easy to read" — HTML with CSS is the right choice for complex multi-section reports. Markdown is fine for simpler outputs.
- **Drive delivery:** Always check that the TMP folder exists on Drive before uploading. Use the user's work account (ndr@draas.com for Nishant) unless they specify otherwise.

## Examples of When to Use

- Immigration program research (EB-5, E-2, L-1) covering process + tax + trust + exit
- International business expansion (jurisdiction selection + corporate structure + tax + regulatory)
- Estate planning cross-border (India-US trust + inheritance tax + succession)
- Investment analysis (asset class + tax treatment + jurisdiction + risk)

## Alternative: PubMed Biomedical Research (Single-Dimension)

When the user asks about **scientific/medical/biological literature** — disease diagnostics, biomarkers, drug mechanisms, protein targets, clinical studies — use the **PubMed E-utilities API** directly. This is a single-dimension task that does NOT need subagents or HTML reports.

**Workflow:**
1. `esearch` — get PMIDs matching the query (structured JSON, ~3 req/s limit)
2. `esummary` — quick overview (titles, journals, authors)
3. `efetch` — full abstract XML

See `references/pubmed-eutils.md` for exact curl commands, query patterns, and XML parsing tips.

## Examples of When NOT to Use

- Single-dimension research (use a single `web_search` or `delegate_task` with one goal — or PubMed E-utilities for biomedical topics)
- Fact-checking a specific claim (use `primary-source-tracing` skill)
- Vendor/product evaluation (use `vendor-product-research` skill)
- Quick lookup (use `web_search` directly)
