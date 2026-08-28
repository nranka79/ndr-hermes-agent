---
name: content-team-briefing-html
description: "Build A4-print-ready HTML briefing notes for content teams / external vendors. Light-themed, page-breaked, with concrete day-to-day examples embedded. For DRAAS content briefs and similar internal/external team briefs."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [briefing, content-team, HTML, A4-print, examples, real-estate]
---

# Content Team Briefing — A4 HTML

Build A4-print-ready HTML briefing notes for content/marketing teams. **Light theme, structured, with concrete day-to-day examples** — not a framework document. The user will open the HTML in a browser and `Ctrl+P → Save as PDF` for distribution.

## Trigger

User asks for a "briefing note", "scope document", "content brief", or "scope of work" for an internal team or external vendor/agency. Especially when:
- The brief needs to be shared as a PDF
- The product being briefed has multiple funnel stages (ToFu / MoFu / BoFu)
- The work involves **day-to-day** content production (not one-off campaigns)

---

## User-confirmed preferences (June 2026 DRAAS Content Team Brief)

1. **A4 page breaks mandatory** — user said: "remember when preparing HTML file I might convert it into PDFs or around the content which fits in an A4, you can send it HTML page breaks when I put it in the HTML pages."
2. **Frameworks alone are insufficient** — user feedback: "structurally it is correct it's covered the key areas but it's not covered the examples of the kite [type] of day to day work." A briefing without concrete day-to-day examples is **incomplete** and will be sent back for revision.
3. **Hero product / flagship context first** — the briefing should name the specific product/business being marketed, not stay abstract. (DRAAS brief: "Weekend Home / Estate Living".)
4. **Funnel-structured** — Top / Middle / Bottom + Daily Engagement is the preferred organization. Single "core pillars" lists are too thin.
5. **Table-of-content-examples** — include a content calendar snapshot table (channel × content type × example × funnel stage) so the team can see a full week of work in one glance.

---

## Document Structure

### Required sections (in order)

1. **Mission / scope header** — name the product being marketed, state the production scale target (e.g. 10x-20x), name the approach (AI-first, lean, etc.)
2. **Content Funnel Strategy** — broken into 3-4 sub-sections (ToFu / MoFu / BoFu / Daily Engagement), each with:
   - Purpose sentence
   - `.example-box` (highlighted) containing 3-5 **concrete** content types with named examples (article titles, post topics, ad copy angles, tool names)
3. **Execution Workflow** — daily cadence, multi-format loop, social interaction
4. **Content Calendar Snapshot** — `<table>` with 5-7 example rows showing what a week of work looks like
5. **KPIs** — 4-6 specific, measurable metrics tied to the funnel stages
6. **Footer** — implementation note + contact for tooling

### Page breaks

Sections 1, 2, 3, 4, 5 should each be a separate A4 page. Use `<div class="page-break"></div>` between sections.

Inside Section 2 (funnel), wrap each sub-section in `<div class="no-break">` so a funnel block doesn't get split across pages.

### CSS template (light theme, A4-ready)

```css
/* Screen */
body {
    font-family: 'Segoe UI', Arial, sans-serif;
    line-height: 1.6; color: #333;
    max-width: 800px; margin: auto; padding: 40px;
}
h1 { color: #2c3e50; border-bottom: 2px solid #2c3e50; padding-bottom: 10px; }
h2 { color: #34495e; margin-top: 30px; }
h3 { color: #2c3e50; margin-top: 20px; }
.highlight { background-color: #f8f9fa; border-left: 5px solid #007bff; padding: 15px; margin: 20px 0; }
.example-box { background-color: #fff3e0; border-left: 5px solid #ff9800; padding: 15px; margin: 15px 0; }
table { width: 100%; border-collapse: collapse; margin: 15px 0; }
table th, table td { border: 1px solid #ddd; padding: 10px; text-align: left; }
table th { background-color: #34495e; color: white; }

/* Print / PDF (A4) */
@page { size: A4; margin: 20mm 18mm; }

@media print {
    body { max-width: 100%; padding: 0; font-size: 11pt; line-height: 1.5; color: #000; }
    h1 { font-size: 18pt; margin-top: 0; }
    h2 { font-size: 14pt; }
    h3 { font-size: 12pt; }
    .highlight, .example-box {
        background: none !important; border-left-width: 3px; padding: 10px;
        -webkit-print-color-adjust: exact; print-color-adjust: exact;
    }
    table th {
        background-color: #34495e !important;
        -webkit-print-color-adjust: exact; print-color-adjust: exact;
    }
    .page-break { page-break-after: always; display: block; }
    .no-break { page-break-inside: avoid; }
    h2, h3 { page-break-after: avoid; }
    table { page-break-inside: avoid; }
}
```

### Concrete example — the DRAAS Content Team Briefing

Built for the DRA Content Engine with Weekend Home / Estate Living as the flagship product. The original version was a 3-section framework; the user sent it back saying "this does not cover all the examples I gave... the type of content." The updated version added:

- ToFu examples: paid articles in publications, blog/Substack/Medium ("Why have a weekend home?", "High achiever weekend lifestyle"), Instagram Reels (farm sunrise, relaxation), Facebook community seeding in wellness/longevity groups
- MoFu examples: Facebook promoted ads for "Weekend Homes Lifestyle Club", interactive quizzes ("Which weekend home style suits you?"), "Are you weekend-ready?" calculator, polls/votes
- Daily engagement examples: 1+ post per day, commenting in Facebook/LinkedIn/Instagram communities, tagging in trending news
- A 7-row content calendar table mapping each content type to a channel, example, and funnel stage

The full file is at `/data/hermes/users/ndr/Content_Team_Briefing.html` (A4-ready, 5 pages, light theme, example-box highlights preserved on print).

---

## Workflow

1. **Receive the briefing ask** — user describes what needs to be briefed
2. **Identify the product / scope** — name it explicitly in the mission section
3. **Lay out funnel sub-sections** — get user to confirm or supply the **concrete day-to-day examples** for each funnel stage before drafting
4. **Draft the HTML** — use the CSS template above, with `<div class="page-break">` between major sections and `<div class="no-break">` inside funnel sub-sections
5. **Show the user the file path** — and offer to send via Telegram as a `MEDIA:` attachment (user often can't reach the filesystem directly — see messaging-drafts/SKILL.md "Delivery of file artifacts")
6. **User converts to PDF** — opens in browser, `Ctrl+P → Save as PDF`. A4 page size is already set in `@page`.

## Pitfalls

- **Generic framework without examples = rejection** — always push for specific day-to-day examples. Ask the user to enumerate before drafting if needed.
- **Forgetting `print-color-adjust: exact`** — without this, the highlighted `.example-box` backgrounds and table-header colours disappear in the PDF.
- **Page breaks inside a funnel block** — wrap each funnel sub-section in `<div class="no-break">` to keep ToFu / MoFu / BoFu together.
- **Heading orphans** — `h2, h3 { page-break-after: avoid; }` keeps a heading from being separated from its following content.
- **Tables split across pages** — `table { page-break-inside: avoid; }` is essential for the content calendar snapshot to stay on one page.

## Related

- `productivity-workflows/SKILL.md` — umbrella
- `references/investment-document-creation-full.md` — different pattern: dark theme, Q&A, 2-page DRAAS investor deck (not this — same umbrella, different workflow)
- `messaging-drafts/SKILL.md` — for sending the HTML file to the user via Telegram
