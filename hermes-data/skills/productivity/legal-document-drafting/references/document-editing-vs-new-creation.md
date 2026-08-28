# Document Editing (Redline) vs. New Creation

This skill covers **two distinct workflows** with different — sometimes opposite — formatting conventions. 
Using the wrong one produces incorrect results.

## A. Editing Existing Documents (redline/revision workflow)

**Use when:** the user asks you to edit, modify, revise, or update an existing document (MOU, deed, agreement).

### Rules

| Rule | Value |
|------|-------|
| **Text color** | ALL changes in **RED** (`rgbColor: {red: 1.0, green: 0.0, blue: 0.0}`) |
| **Method** | Replace text directly — no strikethrough, no comments |
| **What to color** | Party name replacements, new clause insertions, clause rewrites, alignment fixes |
| **Recital alignment** | JUSTIFIED, not CENTER |
| **Versioning** | Edit in-place by default. Create `_D2` only when changes are structural (per `gws-automation` → Rule 1 under Nishant's Document Management Conventions) |
| **Delivery pattern** | Iterative rounds — user delivers changes in batches. Apply ONLY the current round and wait for the next |

### Index drift trap

When using `deleteContentRange` + `insertText` in the same `batchUpdate`, subsequent operations' 
indices shift because the insert happens at the deletion point. The new text's range starts at the 
same index as the deletion.

**Safety net:** If indices get mangled, use `replaceAllText` as a fallback to fix garbled fragments.

### Reference implementations

| File | What it covers |
|------|---------------|
| `references/mou-land-aggregation-joint-monetization.md` | Party replacements, RED markup, alignment for MOU |
| `references/reconstitution-and-sec281-pattern.md` (Section 4) | RED Color Markup Convention |
| `gws-automation/references/legal-doc-red-edit-workflow.md` | Full Docs API implementation of RED markup |
| `gws-automation/references/color-coded-doc-updates.md` | Green/blue for incremental reviewer updates |

## B. Creating New Documents (from-scratch workflow)

**Use when:** drafting a new sale deed, partnership deed, agreement, or any document from scratch.

### Rules

| Rule | Value |
|------|-------|
| **Text color** | All pure black (R=0, G=0, B=0) — NEVER use colored fonts |
| **Backgrounds** | No dark backgrounds on body text. Section headings get light gray shading only (`rgbColor: {red: 0.9, green: 0.9, blue: 0.9}`) |
| **Font** | Arial throughout (except section headings which follow the formatting conventions) |
| **Create method** | Drive API (to set parent folder) → populate via Docs API |
| **Formatting** | Per `references/draas-google-doc-formatting-conventions.md` |

### Reference implementation

`references/draas-google-doc-formatting-conventions.md` — the only reference for final-document formatting.

## Why two different rules?

They serve different purposes:

- **RED markup for editing** — makes changes visible for reviewer sign-off. The user needs to see exactly what changed in a draft.
- **Black-only for final** — ensures the executed/printed document is clean and professional. Colored text destroys B&W print readability and looks unprofessional in final deeds.

The `references/draas-google-doc-formatting-conventions.md` reference was updated in June 2026 to carry this disclaimer.
