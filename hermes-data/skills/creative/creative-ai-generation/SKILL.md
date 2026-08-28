---
name: creative-ai-generation
description: "Creative AI generation umbrella — ASCII art (pyfiglet, cowsay, boxes), ASCII video (video/audio to colored ASCII MP4/GIF), and pixel art with era palettes (NES, Game Boy, PICO-8)."
umbrella: creative-ai-generation
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Creative, ASCII Art, ASCII Video, Pixel Art, Retro Gaming, Image Conversion]
---

# Creative AI Generation — Umbrella

Covers ASCII art, ASCII video, and pixel art generation.

## Decision Tree

```
What creative generation task?
├── ASCII art from text (banners, boxes, cowsay)
│   └── → ASCII Art (references/ascii-art.md)
│         pyfiglet, cowsay, boxes, image-to-ascii.
├── Convert video/audio to colored ASCII MP4/GIF
│   └── → ASCII Video (references/ascii-video.md)
│         aalibi, image conversion, colored ASCII.
└── Pixel art with era-specific palettes
    └── → Pixel Art (references/pixel-art.md)
          NES (6-color), Game Boy (4-tone), PICO-8 (16-color).
```

## Sub-Skill Reference

| Skill | When to Use | Key Tool |
|-------|-------------|----------|
| `references/ascii-art.md` | ASCII text art | pyfiglet, cowsay, boxes |
| `references/ascii-video.md` | Video → ASCII | aalibi, image conversion |
| `references/pixel-art.md` | Retro pixel art | Palette-based generation |

## Absorbed Skills

- `ascii-art` → `references/ascii-art.md`
- `ascii-video` → `references/ascii-video.md`
- `pixel-art` → `references/pixel-art.md`

## Quick Reference

### ASCII Art
```bash
cowsay "Hello World"
figlet "Hello"
boxes -d dog "Hello"
```

### Pixel Art Palettes
- **NES**: 6 colors per tile, limited palette
- **Game Boy**: 4-tone green (#0f380f, #306230, #8bac0f, #9bbc0f)
- **PICO-8**: 16-color palette, 128x128 sprites

## Resources

- **pyfiglet**: https://github.com/pwaller/pyfiglet
- **aalibi**: https://github.com/jwieting/aalibi
- **PICO-8**: https://www.lexaloffle.com/pico-8.php