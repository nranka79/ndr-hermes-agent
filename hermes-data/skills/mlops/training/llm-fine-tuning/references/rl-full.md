---
name: llm-rl-training
description: "LLM alignment via reinforcement learning — GRPO (group relative policy optimization for reasoning), SIMPO (simple preference optimization), or SLIME (Megatron+SGLang for production RL scaling)."
umbrella: llm-rl-training
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [RL Training, Alignment, GRPO, SIMPO, PPO, DPO, RLHF, Preference Optimization, Megatron, SGLang, Post-Training]
---

# LLM Alignment via Reinforcement Learning

This umbrella covers RL-based alignment methods for LLMs. Each approach serves a different scale and use case.

## Decision Tree

```
What is your RL alignment need?
├── Reasoning model optimization (Math/Code/General)
│   └── → GRPO (references/grpo.md)
│         Group-relative advantages, no reward model needed.
├── Simple preference alignment without RL complexity
│   └── → SIMPO (references/simpo.md)
│         Ranking-based, straightforward and effective.
├── Production-scale RL with Megatron + SGLang
│   └── → SLIME (references/slime.md)
│         Best for GLM models and large-scale RL scaling.
└── Full RLHF pipeline (SFT → Reward → PPO → DPO)
    └── → Use TRL (llm-fine-tuning/references/trl.md)
```

## Reference Files

| File | Approach | When to Use |
|------|----------|-------------|
| `references/grpo.md` | Group Relative Policy Optimization | Reasoning models (Math, Code), no reward model |
| `references/simpo.md` | Simple Preference Optimization | Quick preference alignment, ranking-based |
| `references/slime.md` | Megatron + SGLang framework | Production GLM training, large-scale RL |

## Quick Comparison

| Feature | GRPO | SIMPO | SLIME |
|---------|------|-------|-------|
| Reward model needed | No | No | Optional |
| Complexity | Medium | Low | High |
| Scale | Medium-Large | Medium | Large-Production |
| Target use case | Reasoning (Math/Code) | General alignment | GLM production |
| Framework | HuggingFace TRL | HuggingFace TRL | Megatron + SGLang |

## Key Concepts

**GRPO (Group Relative Policy Optimization):**
- Groups samples by question, computes relative advantage
- No critic/reward model needed — self-contained
- Best for reasoning tasks (Math, Code)
- Reference: `grpo-rl-training` skill

**SIMPO (Simple Preference Optimization):**
- Ranking-based without the complexity of PPO
- Uses a contrastive loss over ranked candidates
- Simple implementation, strong results
- Reference: `simpo-training` skill

**SLIME (SGLang + Megatron):**
- Megatron for distributed tensor parallelism
- SGLang for efficient RL data generation
- Reference: `slime-rl-training` skill
