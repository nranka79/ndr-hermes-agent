---
name: model-session-starter
description: |
  Generates a command to start a new Hermès session with a specified model and provider configuration.
  Invoke by providing a model keyword as an argument.

  Example usages:
  hermes skills run model-session-starter -- MiniMax
  hermes skills run model-session-starter -- Gemini
  hermes skills run model-session-starter -- Nematron

category: configuration
version: 1.0.0
author: ndr@draas.com
---

# Model Session Starter

Quickly generate the command to start a new Hermès session with your preferred model and provider.

## Model Mappings

| Keyword | Provider | Model |
|---|---|---|
| `MiniMax` | MiniMax | Minimax-M2.7 |
| `Nematron` | OpenRouter | nvidia/nemotron-3-super-120b-a12b:free |
| `Gemini` | OpenRouter | google/gemini-2.5-flash-lite |

## Usage

```bash
hermes skills run model-session-starter -- <model_keyword>
```

Replace `<model_keyword>` with one of: `MiniMax`, `Gemini`, `Nematron`.

The script outputs the `hermes` command to copy and run for a new session with the desired configuration.

**Note:** This skill does not change the current active model — it generates the command for starting a *new* session.
