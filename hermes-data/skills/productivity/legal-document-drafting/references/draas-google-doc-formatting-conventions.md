# DRAAS Google Doc Formatting Conventions

All DRAAS legal documents **output as final documents** to Google Docs must follow these standards. This applies to **newly created documents** only — see note below for the separate editing workflow.

## ⚠️ Important: This covers FINAL documents, not EDITING

This reference applies when **creating a new document from scratch** (sale deed, partnership deed, agreement). When the user asks you to **edit or revise an existing document**, a different convention applies:
- **ALL changes in RED** (RGB 1.0, 0.0, 0.0) — every modification is colored to show what changed
- See the main SKILL.md section "Document Editing (Redline) vs. New Creation"
- See also `gws-automation/references/legal-doc-red-edit-workflow.md` for the Docs API implementation
- See `references/reconstitution-and-sec281-pattern.md` Section 4 for RED markup convention
- See `references/mou-land-aggregation-joint-monetization.md` → RED Markup section

The two workflows are opposites: **black-only for final documents** preserves B&W printability; **RED markup for editing** makes changes visible for review. The contradiction is intentional — they serve different purposes.

## Quick Reference Table

| Element | Font | Size | Bold | Background |
|---|---|---|---|---|
| Document title | Arial | 22pt | Yes | White |
| Subtitle (location) | Arial | 13pt | Yes | White |
| Section headings (1-9) | Arial | 12pt | Yes | Light gray (R=0.9) |
| Sub-headings | Arial | 11pt | Yes | White |
| Bullet content | Arial | 10pt | Normal | White |
| Sub-list items | Arial | 10pt | Normal | White |
| Table headers (left col) | Arial | 10pt | Yes | Per sheet |
| Table values (right col) | Arial | 10pt | Normal | Per sheet |
| Closing / witness text | Arial | 10pt | Normal | White |

## Critical Rules

1. **All text pure black** (R=0, G=0, B=0). Never use colored fonts — they destroy B&W print readability. The user has explicitly rejected colored fonts in legal documents.

2. **No dark backgrounds on body text** — only section headings get light gray shading (`rgbColor: {red: 0.9, green: 0.9, blue: 0.9}`). Content blocks, tables, bullet lists must have white/transparent background for B&W printing.

3. **Consistent spacing:**
   - Title: 6pt above / 4pt below
   - Section headings: 10pt above / 4pt below
   - Sub-headings: 8pt above / 4pt below
   - Bullet items: 3pt above / 3pt below
   - Sub-list items: 1pt above / 1pt below
   - Table cell content: 1pt above / 1pt below

4. **Apply base formatting first** — set entire document to Arial 10pt normal black, then override specific ranges.

5. **Text inserted via Docs API has no inherited formatting** — always follow `insertText` with explicit `updateTextStyle` calls.

## Implementation

Use `gws-automation/references/docs-api-formatting.md` for detailed Docs API batch operation patterns (deleteContentRange constraints, index shifting, replaceAllText, table cell iteration).

### Formatting sequence for new documents:
```python
# 1. Create via Drive API (supports parent folder)
# 2. Insert text at index 1
# 3. Set entire doc to Arial 10pt normal black
# 4. Override specific ranges: title (22pt bold), headings (12pt bold), etc.
# 5. Set paragraph spacing by category
# 6. Set paragraph shading for section headings
```

### Formatting sequence for editing existing documents:
```python
# 1. Copy the document via Drive API
# 2. Make text changes (replaceAllText for simple, delete+insert for complex)
# 3. Set entire doc to Arial 10pt normal black
# 4. Override heading sizes/bold
# 5. Remove stray background shading from body content
# 6. Set consistent paragraph spacing
```
