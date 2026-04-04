---
name: model-changer
description: |
  Switches the Hermes agent to a different model/provider mid-session.
  From the next message onwards, all LLM calls use the new model configuration.

  Invoke by providing a model keyword as an argument.

  Example usages:
  /model-changer MiniMax
  /model-changer Gemini
  /model-changer Nematron
  /model-changer Qwen

category: configuration
version: 2.1.0
author: ndr@draas.com
---

# Model Changer

Switch the Hermes agent to a different model and provider **mid-session**. The model change takes effect immediately for the next message.

## Model Mappings

| Keyword | Provider | Model |
|---|---|---|
| `MiniMax` | MiniMax | Minimax-M2.7 |
| `Nematron` | OpenRouter | nvidia/nemotron-3-super-120b-a12b:free |
| `Gemini` | OpenRouter | google/gemini-2.5-flash-lite |
| `Qwen` | OpenRouter | qwen/qwen3.6-plus:free |

## Usage

Invoke with one of the model keywords:

```
/model-changer MiniMax
```

or via the hermes skills interface:

```bash
hermes skills run model-changer -- gemini
```

## Behavior

When invoked:
1. The skill validates the model keyword against supported options
2. It signals the Hermes agent to switch models
3. Starting with your next message, all LLM calls use the new model
4. The model remains active for the rest of the session

## Notes

- Model switching is **immediate** — from the next message onwards
- You can switch models multiple times in a single session
- Model preference persists until you switch again or end the session
