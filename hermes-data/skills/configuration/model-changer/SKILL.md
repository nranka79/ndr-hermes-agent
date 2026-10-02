---
name: model-changer
description: |
  Switches the Hermes agent to a different LLM model mid-session.
  Use this skill whenever the user asks to change, switch, or use a different model/AI
  (e.g. "switch to Qwen", "use Gemini", "change model to MiniMax", "give me a deep
  thinking model", "use the latest Opus", "switch to the cheapest Gemini flash model").
  From the next message onwards, all LLM calls use the new model.

  Supported: MiniMax, Nematron, Gemini2, Gemini3, Qwen (instant shortcuts) PLUS any
  free-text vendor/tier/capability/version ask ("deep thinking", "claude opus 4.6",
  "cheapest gemini flash", "deepseek r1") -- resolved live against OpenRouter's model
  catalog.
metadata:
  hermes:
    tags: [model, switch, llm, provider, qwen, gemini, minimax, nematron, openrouter, reasoning, configuration]
category: configuration
version: 3.0.0
author: ndr@draas.com
---

# Model Changer

Switch the Hermes agent to a different LLM model **mid-session**. The change takes effect from the next message onwards.

**Trigger phrases:** "switch to Qwen", "use Gemini2", "use Gemini3", "change model to MiniMax", "try Nematron", "give me a deep thinking model", "use the latest Opus", "switch to the cheapest Gemini flash model", "/model-changer <keyword-or-free-text>"

## How it actually works (read this before touching the code)

This is a **script**, not a callable LLM tool. There is no `switch_model(...)` function the
agent can invoke directly — older versions of this file claimed there was; that tool never
existed, which is why switching silently did nothing for a long time (the script wrote a
handoff file that nothing consumed). Both halves are wired up now:

1. Agent runs the script via the `terminal` tool (a subprocess — it cannot touch the live
   gateway's in-memory state directly).
2. The script resolves the keyword, then writes a small JSON request file keyed by this
   session's `HERMES_SESSION_KEY` (exported into the subprocess env by `tools/terminal_tool.py`).
3. `gateway/run.py`'s `_consume_pending_skill_model_switch()` checks for that file at the
   start of the **next** incoming message for this session, applies the real switch (same
   code path `/model` uses), and deletes the file.

If `HERMES_SESSION_KEY` is empty (bare CLI/cron run, no live chat session), the script
refuses with a clear error instead of silently writing somewhere nobody will read it.

## Agent Workflow

Run the script via `terminal`, from the Hermes install root:

```
python3 /data/hermes/skills/configuration/model-changer/scripts/main.py -- qwen
python3 /data/hermes/skills/configuration/model-changer/scripts/main.py -- "deep thinking opus"
python3 /data/hermes/skills/configuration/model-changer/scripts/main.py -- "cheapest gemini flash"
python3 /data/hermes/skills/configuration/model-changer/scripts/main.py -- "claude opus 4.6"
```

(Adjust the path if `skill_view`/`skills_list` reports a different on-disk location for this
skill — always use the path those tools report, the above is the layout as of 2026-10-02.)

**Keyword shortcuts** (instant, no network call): `minimax`, `nematron`, `gemini2`, `gemini3`, `qwen`.

**Anything else** is free text passed straight to `tools.model_resolver.resolve_openrouter_model`,
which matches vendor (gemini/claude/opus/gpt/deepseek/qwen/kimi/llama/mistral/grok/...), tier
(opus/flash/pro/mini/lite/r1/...), reasoning capability ("deep thinking"/"reasoning"/"smartest"),
explicit version ("4.6"), and "cheapest"/"free" against OpenRouter's live catalog — it does NOT
require one of a fixed brand-name list, and it refuses (with candidate suggestions) rather than
silently guessing when nothing in the ask is recognizable.

Then read the script's stdout and relay it to the user:
- Success: confirm which model was activated, that it takes effect from the next message.
- Failure: relay the error + any candidate model ids the resolver suggested, or list the 5
  keyword shortcuts, and ask the user to clarify or name a vendor/tier.

## Notes

- **Inspecting the current model/provider:** `hermes config get model` / `hermes config get provider` silently return empty on the DRAAS box. Read `/data/hermes/config.yaml` directly instead (e.g. `grep -iE "model|provider" /data/hermes/config.yaml`). Do NOT look in `/opt/hermes/config.yaml` — that path is the Hermes code repo, not the live config.
- **Writing config:** file tools (`patch` / `write_file`) are REFUSED on `/data/hermes/config.yaml` by design. Use the CLI — `hermes` is not on PATH, so invoke the absolute binary: `HERMES_HOME=/data/hermes /opt/hermes/.venv/bin/hermes config set <key> <value>`. Full procedure in the `hermes-provider-routing` skill. (This is for the global default model; it is unrelated to the mid-session switch above, which only needs the `terminal` call shown.)
- **This skill only switches the MAIN model.** Auxiliary subsystems — `vision`, `web_extract`, `compression`, `image_gen`, TTS/STT — have their own independent `provider`/`model` config and are NOT changed by this script. To diagnose or repoint those, load `hermes-provider-routing`.
- The switch only takes effect for the **next** message, never the one that triggered it (the script runs mid-turn, inside this turn's own tool call; the file is only read when the *following* message comes in).
- If the ask is not recognised and the resolver has no confident match, list the 5 keyword shortcuts and the resolver's candidate suggestions, and ask the user to pick one or name a vendor/tier.
- You can switch models multiple times in a single session.
- The model remains active until switched again or the session ends.
