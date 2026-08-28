---
name: third-party-skill-installation
description: Evaluate and install third-party agent skills (SKILL.md-format repos from GitHub, e.g. Claude Code / Codex / Vercel-skills ecosystems) into Hermes. Use when the user says "can this skill be installed in Hermes", "install this skill from GitHub", or shares a repo that turns out to be an agent skill. Covers repo inspection (README, file tree, SKILL.md frontmatter), Hermes compatibility mapping (references/scripts/templates, allowed-tools), the install procedure (copy into /data/hermes/skills/), and the real blocker — external paid CLIs the skill shells out to.
version: 1.0.0
platforms: [linux, macos]
metadata:
  hermes:
    tags: [skills, install, github, skllmd, compatibility, hermes-config]
---

# Third-Party Skill Installation (SKILL.md repos → Hermes)

Use when NDR asks whether / how a GitHub skill repo can be installed in Hermes, or hands over a repo that is an agent skill. The skill ecosystem is converging on the `SKILL.md` format (Claude Code plugins, Codex skills, Vercel `npx skills`), and Hermes uses the SAME format — so most such repos install cleanly. The work is: verify it's really a SKILL.md skill, map its structure to Hermes conventions, check what external tools it needs, then copy it in.

## Skills vs Tools — the correct mental model

- A Hermes skill = **knowledge** (the SKILL.md procedure the agent reads when the task matches). A **tool** = **capability** the agent can invoke (terminal, read_file, gws_auth, whatsapp_link, browser…). Skills REFER to tools; they do not contain them.
- A skill ships as a folder: `SKILL.md` + optional `references/` (templates, prompt libraries, research notes), `scripts/` (runnable helpers), `templates/` (starter files), `assets/`.
- `references/` files are NOT tools — they are artifacts the agent reads and copies from: prompt templates (text pasted into CLIs), copy-paste bash recipes, JS/HTML libraries shipped into the deliverable, or Python helpers run via terminal.
- Hermes reads the `name` + `description` YAML frontmatter; other frontmatter fields (e.g. Claude Code's `allowed-tools`) are ignored harmlessly.

## Workflow

1. **Get repo metadata + README** via the GitHub API (web_extract often fails on GitHub without credits):
   - `curl -s https://api.github.com/repos/<owner>/<repo>` — confirm `description` (often says "a skill for Claude Code, Codex...").
   - `curl -s https://raw.githubusercontent.com/<owner>/<repo>/main/README.md` — install section + requirements.
   - Full tree: `curl -s "https://api.github.com/repos/<owner>/<repo>/git/trees/main?recursive=1"` and list paths.
2. **Confirm it's a SKILL.md skill** — look for `skills/<skill-name>/SKILL.md` in the tree. The repo may ALSO ship `.claude-plugin/` marketplace metadata; that's irrelevant for Hermes — the skill folder is what matters.
3. **Read the SKILL.md frontmatter + first ~80 lines** (`raw.githubusercontent.com/.../skills/<name>/SKILL.md`). Hermes reads `name` + `description` — if those exist, it's installable. Note the `allowed-tools` field (Claude Code convention); Hermes ignores it but it tells you what the skill expects to call.
4. **Map tools + structure to Hermes** (tell the user this explicitly — it reassures and corrects the mental model):
   - `allowed-tools` map: Bash → `terminal`; Read → `read_file`; Write → `write_file`; Edit → `patch`; AskUserQuestion → `clarify`; Skill → skill tools.
   - `references/*.md` → Hermes references/ (prompt templates, pipeline recipes the agent reads).
   - `references/*.js` / `*.html` → likely DELIVERABLE code (goes into the user's output page), not something Hermes runs.
   - `references/*.py` or `scripts/*.py` → runnable helper scripts (agent runs via terminal/python).
   - Clarify the user's common misconception: a skill is NOT "MD file + Python tool files". A skill = instructions + reference material; the "tools" it uses are Hermes's own tools + external CLIs it shells out to via terminal.
5. **Check the REAL blocker — external dependencies**. Most generative skills shell out to paid CLIs (e.g. scroll-world needs Monid CLI + API key and Higgsfield CLI + credits; ffmpeg; optional Codex CLI). Without those authed/installed, the skill stops at its bootstrap step. State this plainly: installation is free, running it bills real money.
6. **Install**:
   - `git clone --depth 1 https://github.com/<owner>/<repo> /tmp/<repo>`
   - `mkdir -p /data/hermes/skills/<category>/` then `cp -R /tmp/<repo>/skills/<skill-name> /data/hermes/skills/<category>/`
   - If the repo has no `skills/` wrapper (SKILL.md at root), copy the folder containing SKILL.md itself.
   - Verify with `skills_list` / `skill_view(name)`.
7. **Report**: verdict (yes/no + why), the structure map (which files are read vs run vs shipped), the external deps + rough cost if known, and ask before installing (NDR may treat it as "nice-to-have later").

## Pitfalls

- **web_extract/web_search may be out of credits** — the GitHub API + raw.githubusercontent.com via curl are the reliable path; use them first.
- **Don't over-promise on cost** — quote per-run estimates from the README only; exact billing comes from the CLI's own balance output.
- **Don't try to "port" the skill** — if the SKILL.md format is standard, a straight folder copy works; no need to convert prompts or rewrite the engine.
- **`main` may not be the default branch** — check the API's `default_branch` if the raw fetch 404s.
- **Hermes category is optional** — a bare `cp -R ... /data/hermes/skills/` also works; use a category only when it helps organization.
- **Never claim "installed and working" when only the folder copy succeeded** — if external CLIs are missing or unauthed, the skill stops at its bootstrap step and asks the user for accounts. Report install status and usability status separately.
- **A skill that generates paid assets (video/image chains) prints cost estimates per run** — surface that to the user BEFORE they say go, and note whether a fallback biller exists (e.g. Higgsfield credits vs Monid pay-per-clip).
- **Resolve the ACTUAL repo before evaluating** — if the user's description of the repo is fuzzy, confirm via the GitHub API; don't evaluate a guessed repo.

## Reference files
- `third-party-skill-install-scroll-world-example.md` — worked example: the scroll-world repo (oso95/scroll-world) assessment — structure, dependency/cost notes (Monid/Higgsfield), and the answer given to NDR.
- `third-party-skill-install-full.md` — full content of the former `third-party-skill-install` skill (absorbed 2026-08-09): mental model, evaluation checklist, install steps, pitfalls.
