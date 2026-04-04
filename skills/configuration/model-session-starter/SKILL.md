---
name: model-session-starter
description: |
  Switches the Hermes agent to a different model/provider for the current session.
  From the next message onwards, all LLM calls use the new model configuration.

  Invoke by providing a model keyword as an argument.

  Example usages:
  /model-session-starter MiniMax
  /model-session-starter Gemini
  /model-session-starter Nematron

category: configuration
version: 2.0.0
author: ndr@draas.com
---

# Model Session Starter

Switch the Hermes agent to a different model and provider **in the current session**. The model change takes effect immediately for the next message.

## Model Mappings

| Keyword | Provider | Model |
|---|---|---|
| `MiniMax` | MiniMax | Minimax-M2.7 |
| `Nematron` | OpenRouter | nvidia/nemotron-3-super-120b-a12b:free |
| `Gemini` | OpenRouter | google/gemini-2.5-flash-lite |

## Usage

Invoke with one of the model keywords:

```
/model-session-starter MiniMax
```

or via the hermes skills interface:

```bash
hermes skills run model-session-starter -- gemini
```

## Behavior

When invoked:
1. The skill validates the model keyword against supported options
2. It signals the Hermes agent to switch models
3. Starting with your next message, all LLM calls use the new model
4. The model remains active for the rest of the session

## Notes

- Model switching is **immediate** — from the next message onwards
- The previous model remains in the background for fallback if needed
- You can switch models multiple times in a single session
- Model preference persists until you switch again or end the session
