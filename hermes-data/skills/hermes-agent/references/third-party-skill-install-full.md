---
name: third-party-skill-install
description: |
  Evaluate a third-party SKILL.md-format agent skill (from GitHub or anywhere)
  for Hermes installability, then install it. Covers the compatibility checklist
  (frontmatter, references/templates/scripts layout, allowed-tools mapping),
  the install path, and the dependency gate (external CLIs / paid services that
  decide whether the skill is actually usable after install).
  Trigger: "can this skill be installed in Hermes", "install this GitHub skill",
  "does this agent skill work with hermes", "add this skill from <repo>".
metadata:
  hermes:
    tags: [hermes, skills, install, skilmd, github, evaluation]
category: hermes-agent
version: 1.0.0
author: ndr@draas.com
---

# Third-Party Skill Install (SKILL.md evaluation)

When the user asks whether some external agent skill — a GitHub repo, a Claude
Code / Codex plugin, a `SKILL.md`-compatible skill — can be installed in Hermes,
run this evaluation before touching anything.

## What Hermes skills actually are (correct mental model)

- A Hermes skill = **knowledge** (the SKILL.md procedure the agent reads when the
  task matches). A **tool** = **capability** the agent can invoke (terminal,
  read_file, gws_auth, whatsapp_link, browser…). Skills REFER to tools; they do
  not contain them.
- A skill ships as a folder: `SKILL.md` + optional `references/` (templates,
  prompt libraries, research notes), `scripts/` (runnable helpers), `templates/`
  (starter files), `assets/`.
- `references/` files are NOT tools. They are artifacts the agent reads and
  copies from: prompt templates (text pasted into CLIs), copy-paste bash
  recipes, JS/HTML libraries shipped into the deliverable, or Python helpers run
  via terminal. Only occasionally is one a "tool" in the Hermes sense.
- Hermes reads the `name` + `description` YAML frontmatter; other frontmatter
  fields (e.g. Claude Code's `allowed-tools`) are ignored harmlessly.

## Evaluation checklist (worked on oso95/scroll-world, 2026-08-01)

1. **Repo recon** — `curl -s https://api.github.com/repos/<owner>/<repo>` for
   description/fork status, and the recursive tree
   `.../git/trees/main?recursive=1` to see the layout without cloning.
2. **Check the skill folder structure** — does it contain
   `skills/<name>/SKILL.md` + `references/`? That layout is identical to
   Hermes' — good sign. A `.claude-plugin/` dir at root is Claude-Code
   packaging; Hermes ignores it, only the `skills/` tree matters.
3. **Frontmatter** — `name` + `description` present? If yes, Hermes will list
   it. Claude Code `allowed-tools` maps cleanly to Hermes equivalents:
   Bash→terminal, Read/Write/Edit→read_file/write_file/patch, AskUserQuestion→
   clarify, Skill→skill tools.
4. **Dependency gate — the real decision point.** The skill may need external
   CLIs + accounts (e.g. scroll-world needs Monid CLI + API key, Higgsfield CLI,
   ffmpeg; a 6-scene chain ≈ $27). Installation is free and trivial; USABILITY
   depends on these. State this split explicitly to the user: "installs fine,
   but running it bills money / needs X accounts" — and check for the CLIs
   (`which ffmpeg`, auth status) before promising a run.

## Install

```bash
git clone <repo> /tmp/<repo>
mkdir -p /data/hermes/skills/<category>/
cp -R /tmp/<repo>/skills/<name> /data/hermes/skills/<category>/
```

- New skills land in `/data/hermes/skills/` — no plugin registry, no manifest.
- Confirm the folder was actually created with `search_files(target='files')`
  on `/data/hermes/skills/<category>/<name>/` (verify, don't assume).

## Pitfalls

- **Never claim "installed and working" when only the folder copy succeeded.**
  If external CLIs are missing or unauthed, the skill stops at its bootstrap
  step and asks the user for accounts. Report install status and usability
  status separately.
- A skill that generates paid assets (video/image chains) will print cost
  estimates per run — surface that to the user BEFORE they say go, and note
  whether a fallback biller exists (e.g. Higgsfield credits vs Monid pay-per-clip).
- If the user's description of the repo is fuzzy, resolve the ACTUAL repo via
  the GitHub API before evaluating — don't evaluate a guessed repo.
- Overlap note: the bundled `hermes-agent` skill covers configuring Hermes
  itself; this skill is specifically the external-skill evaluation/install path.
