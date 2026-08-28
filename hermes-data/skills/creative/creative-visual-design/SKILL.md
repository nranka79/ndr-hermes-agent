---
name: creative-visual-design
description: "Creative visual design umbrella — architecture diagrams (dark SVG/HTML), Excalidraw hand-drawn diagrams (arch/flow/seq), popular web design systems reference (54 systems as HTML/CSS), and Sketch/Claude Design for HTML mockups."
umbrella: creative-visual-design
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Creative, Visual Design, Architecture Diagrams, Excalidraw, Design Systems, HTML Mockups, Prototyping]
---

# Creative Visual Design — Umbrella

Covers diagram generation, design system references, and HTML prototyping.

## Decision Tree

```
What visual design task?
├── Architecture/cloud/infra diagram (dark-themed SVG)
│   └── → Architecture Diagram (references/architecture-diagram.md)
│         Dark SVG as HTML, cloud/infra layouts.
├── Hand-drawn style diagram (arch, flow, sequence)
│   └── → Excalidraw (references/excalidraw.md)
│         Excalidraw JSON, arch/flow/seq diagrams.
├── Browse 54 real design systems (Stripe, Linear, Vercel...)
│   └── → Popular Web Designs (references/popular-web-designs.md)
│         HTML/CSS reference, 54 systems.
├── Quick HTML mockup / prototype
│   └── → Sketch (references/sketch.md)
│         Throwaway 2-3 design variants.
└── Scrape live website → extract assets + content → build coding agent prompt for design replication
    └── → Website → Agent Prompt Pipeline (references/website-agent-prompt-pipeline.md)
          7-phase: scrape, download, content extract, asset ID, design DNA analysis, prompt build, package.
```

## Sub-Skill Reference

| Skill | When to Use | Output |
|-------|-------------|--------|
| `references/architecture-diagram.md` | Infra/architecture diagrams | Dark SVG/HTML |
| `references/excalidraw.md` | Hand-drawn style diagrams | Excalidraw JSON |
| `references/popular-web-designs.md` | Design system reference | HTML/CSS |
| `references/sketch.md` | Quick mockups | HTML prototypes |
| `references/website-agent-prompt-pipeline.md` | Scrape website → extract assets + content → coding agent prompt | Zip package + HTML prompt |

## Absorbed Skills

- `architecture-diagram` → `references/architecture-diagram.md`
- `excalidraw` → `references/excalidraw.md`
- `popular-web-designs` → `references/popular-web-designs.md`
- `sketch` → `references/sketch.md`

## Resources

- **Excalidraw**: https://excalidraw.com
- **Design Systems**: Stripe, Linear, Vercel, Airbnb, etc.