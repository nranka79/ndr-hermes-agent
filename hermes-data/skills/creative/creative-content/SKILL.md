---
name: creative-content
description: "Creative content generation umbrella — knowledge comics (baoyu-comic), infographics (baoyu-infographic: 21 layouts x 21 styles), design-md token spec files, creative ideation via constraints, and browser demos with pretext."
umbrella: creative-content
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Creative, Content Generation, Comics, Infographics, Ideation, Design, Browser Demos]
---

# Creative Content — Umbrella

Covers content generation, ideation, and creative formats.

## Decision Tree

```
What creative content task?
├── Educational/biography/tutorial comics
│   └── → Baoyu Comic (references/baoyu-comic.md)
│         Knowledge comics in Chinese/English.
├── Data visualization infographics
│   └── → Baoyu Infographic (references/baoyu-infographic.md)
│         21 layouts x 21 styles, data viz.
├── Author/validate DESIGN.md token spec files
│   └── → Design MD (references/design-md.md)
│         Google DESIGN.md format.
├── Generate project ideas via constraints
│   └── → Creative Ideation (references/creative-ideation.md)
│         Creative constraints for brainstorming.
└── Build creative browser demos
    └── → Pretext (references/pretext.md)
          @chenglou/pretext React demos.
```

## Sub-Skill Reference

| Skill | When to Use | Output |
|-------|-------------|--------|
| `references/baoyu-comic.md` | Knowledge comics | Illustrated tutorials |
| `references/baoyu-infographic.md` | Infographics | 21x21 layout/style grid |
| `references/design-md.md` | Token spec files | DESIGN.md |
| `references/creative-ideation.md` | Project ideas | Brainstorming with constraints |
| `references/pretext.md` | Browser demos | React/pretext demos |
| `references/architectural-ai-render-prompts.md` | AI image prompts for architectural renders | Structured material + branding prompts |

## Absorbed Skills

- `baoyu-comic` → `references/baoyu-comic.md`
- `baoyu-infographic` → `references/baoyu-infographic.md`
- `design-md` → `references/design-md.md`
- `creative-ideation` → `references/creative-ideation.md`
- `pretext` → `references/pretext.md`