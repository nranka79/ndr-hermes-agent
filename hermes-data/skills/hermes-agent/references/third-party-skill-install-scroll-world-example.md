# Worked example — scroll-world (oso95/scroll-world)

Assessed 2026-08-01 for NDR. Repo: "A skill that turn any brand into a scrollable 3D world" — builds scroll-scrubbed "fly through the world" landing pages (Apple-style scroll cinematics).

## Repo structure (from git tree API)

```
.claude-plugin/            ← marketplace metadata (IRRELEVANT for Hermes)
  marketplace.json
  plugin.json
LICENSE (MIT)
README.md
skills/scroll-world/
  SKILL.md                  (49.5 KB — the procedure; name+description frontmatter)
  references/
    prompts.md              (10 KB — fill-in-the-slots prompt templates for image/video gen CLIs)
    pipeline.md             (16 KB — copy-paste bash batch scripts: generate → frames → connectors → encode)
    scrub-engine.js         (29 KB — the DELIVERABLE: vanilla-JS scroll-scrub video engine, shipped into user's page)
    index-template.html     (2.7 KB — minimal page that mounts the engine)
    knockout.py             (2.9 KB — the ONLY runnable helper: PIL background-removal script, agent runs via terminal)
```

## Compatibility verdict — INSTALLABLE (standard SKILL.md)

- Frontmatter `name` + `description` → Hermes reads both directly.
- `allowed-tools: Bash, Read, Write, Edit, AskUserQuestion, Skill` → maps 1:1 to Hermes terminal/read_file/write_file/patch/clarify/skill tools.
- References map cleanly onto Hermes references/scripts/templates conventions (repo just uses references/ for everything).

## The real blocker — external paid CLIs

- **Monid CLI** (monid.ai) — default video-chain backend (Seedance 2.0, pay-per-clip, ~$27 per 6-scene 1080p chain). Needs API key + balance.
- **Higgsfield CLI** (higgsfield.ai) — renders scene stills (gpt_image_2) + fallback video (kling3_0). Needs auth + credits.
- **ffmpeg / ffprobe** — frame extraction/encoding.
- **Python + Pillow** — knockout + mobile canvases.
- **Optional: Codex CLI** — alternate stills source via ChatGPT subscription.

## Explanation given to NDR (mental-model correction)

User believed: "a skill = MD instructions + tool files, and tools = Python files."
Correction: Hermes skills = knowledge (SKILL.md); tools = capabilities (terminal, read_file, gws_auth...). The reference files here are NOT tools:
- prompts.md / pipeline.md → text the agent reads and copies from (reference material / recipes).
- scrub-engine.js / index-template.html → code that goes INTO the deliverable (the product, not the process).
- knockout.py → the one file matching the "Python tool" mental model (runnable helper).
- Actual "tools" = external CLIs (higgsfield, monid, ffmpeg) driven through Hermes's terminal tool.

## Decision for NDR

Installation trivial (copy folder); running it bills real money and needs Monid + Higgsfield accounts set up first. Asked before installing; treated as nice-to-have unless he sets up the accounts.
