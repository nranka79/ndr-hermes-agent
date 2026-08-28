---
name: creative-ai-tools
description: "Creative AI tool umbrella — p5.js generative art (shaders, interactive, 3D), Manim CE math animations (3Blue1Brown style), ComfyUI image/video/audio generation, and text humanization (strip AI-isms)."
umbrella: creative-ai-tools
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Creative, p5.js, Manim, ComfyUI, Humanizer, Generative Art, Animations]
---

# Creative AI Tools — Umbrella

Covers generative art, math animations, image generation, and text humanization.

## Decision Tree

```
What creative AI tool?
├── Generative art, shaders, interactive / 3D
│   └── → p5.js (references/p5js.md)
│         Sketches, GLSL shaders, interactive, 3D WebGL.
├── Math/science animations (3Blue1Brown style)
│   └── → Manim CE (references/manim-video.md)
│         Manim CE, mathematical visualizations.
├── Image/video/audio generation
│   └── → ComfyUI (references/comfyui.md)
│         Stable Diffusion, video, audio via ComfyUI.
├── Strip AI-isms from text / add human voice
│   └── → Humanizer (references/humanizer.md)
│         Remove filler, hedge words, add personality.
└── Control TouchDesigner via MCP
    └── → TouchDesigner MCP (references/touchdesigner-mcp.md)
          twozero MCP server, real-time visuals.
```

## Sub-Skill Reference

| Skill | When to Use | Key Tool |
|-------|-------------|----------|
| `references/p5js.md` | Generative art, shaders | p5.js, GLSL |
| `references/manim-video.md` | Math animations | Manim CE |
| `references/comfyui.md` | Image/video/audio gen | ComfyUI |
| `references/humanizer.md` | Text humanization | NLP transformation |
| `references/touchdesigner-mcp.md` | Real-time visuals | TouchDesigner + MCP |

## Absorbed Skills

- `p5js` → `references/p5js.md`
- `manim-video` → `references/manim-video.md`
- `comfyui` → `references/comfyui.md`
- `humanizer` → `references/humanizer.md`
- `touchdesigner-mcp` → `references/touchdesigner-mcp.md`
- `claude-design` → `references/claude-design.md`
- `songwriting-and-ai-music` → `references/songwriting-and-ai-music.md`

## Quick Reference

### p5.js
```javascript
function setup() {
  createCanvas(400, 400);
}
function draw() {
  background(220);
  ellipse(200, 200, 50, 50);
}
```

### Manim
```bash
manim -qh scene.py SquareToCircle
```

### ComfyUI
```bash
# Install
pip install ComfyUI
# Launch
python main.py
```

## Resources

- **p5.js**: https://p5js.org
- **Manim CE**: https://github.com/ManimCommunity/manim
- **ComfyUI**: https://github.com/comfyanonymous/ComfyUI