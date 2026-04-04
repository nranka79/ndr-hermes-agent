---
name: model-changer
description: |
  Switches the Hermes agent to a different LLM model mid-session.
  Use this skill whenever the user asks to change, switch, or use a different model/AI
  (e.g. "switch to Qwen", "use Gemini", "change model to MiniMax", "try Nematron").
  From the next message onwards, all LLM calls use the new model.

  Supported keywords: MiniMax, Gemini, Nematron, Qwen
metadata:
  hermes:
    tags: [model, switch, llm, provider, qwen, gemini, minimax, nematron, configuration]
category: configuration
version: 2.2.0
author: ndr@draas.com
---

# Model Changer

Switch the Hermes agent to a different LLM model **mid-session**. The change takes effect from the next message onwards.

**Trigger phrases:** "switch to Qwen", "use Gemini", "change model to MiniMax", "try Nematron", "/model-changer <keyword>"

## Supported Models

| Keyword | Provider | Model ID |
|---------|----------|----------|
| `MiniMax` | MiniMax | Minimax-M2.7 |
| `Nematron` | OpenRouter | nvidia/nemotron-3-super-120b-a12b:free |
| `Gemini` | OpenRouter | google/gemini-2.5-flash-lite |
| `Qwen` | OpenRouter | qwen/qwen3.6-plus:free |

## Agent Workflow

When the user asks to change/switch models, use the `switch_model` tool directly:

```
switch_model(model="qwen")
switch_model(model="gemini")
switch_model(model="minimax")
switch_model(model="nematron")
```

Then confirm to the user which model was activated and that it takes effect from the next message.

## Notes

- If the keyword is not recognised, list the supported options and ask the user to pick one.
- You can switch models multiple times in a single session.
- The model remains active until switched again or the session ends.
