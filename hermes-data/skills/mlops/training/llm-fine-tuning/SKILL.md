---
name: llm-fine-tuning
description: "LLM fine-tuning methods — choose the right approach: PEFT (LoRA/QLoRA for efficiency), Axolotl (YAML-driven multi-method training), Unsloth (2-5x faster LoRA), or HuggingFace TRL (SFT/DPO/PPO pipeline)."
umbrella: llm-fine-tuning
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Fine-Tuning, LoRA, QLoRA, PEFT, Axolotl, Unsloth, TRL, SFT, DPO, Alignment, Post-Training]
---

# LLM Fine-Tuning — Choosing the Right Method

This umbrella covers all LLM fine-tuning approaches. Select the right tool for your scenario, then use the detailed sub-skill references.

## Decision Tree

```
What is your goal?
├── Quick fine-tuning with minimal compute
│   └── → PEFT/LoRA (references/peft.md)
│         Lightweight adapters, easiest to start.
├── YAML-driven training with many methods (LoRA/DPO/GRPO)
│   └── → Axolotl (references/axolotl.md)
│         Production-ready multi-method fine-tuning.
├── Maximum speed + memory efficiency
│   └── → Unsloth (references/unsloth.md)
│         2-5x faster, 50% less VRAM for LoRA/QLoRA.
└── Full HuggingFace pipeline (SFT → DPO → PPO)
    └── → TRL — content absorbed into this umbrella (see reference table above)
          End-to-end alignment training framework.
```

## Reference Files

| File | Method | Best For |
|------|--------|-----------|
| `references/peft.md` | LoRA / QLoRA / AdaLoRA / DoRA | Efficient adapters, consumer GPUs |
| `references/axolotl.md` | LoRA / DPO / GRPO / ORPO / QLoRA | YAML-driven multi-method training |
| `references/unsloth.md` | LoRA / QLoRA (optimized kernels) | Fastest fine-tuning, minimal VRAM |
- **`trl-fine-tuning`** (absorbed — now part of this umbrella): deeper TRL reference content covering SFT training, DPO variants (IPO, cDPO, RPO), reward modeling, online RL methods (PPO, GRPO, RLOO), and a GRPO production training script. All reference files and templates are now at `references/dpo-variants.md`, `references/grpo-training.md`, `references/online-rl.md`, `references/reward-modeling.md`, `references/sft-training.md`, and `templates/basic_grpo_training.py`. The standalone `trl-fine-tuning` skill is archived.

## Quick Comparison

| Feature | PEFT | Axolotl | Unsloth | TRL |
|---------|------|---------|---------|-----|
| LoRA support | Yes | Yes | Yes (optimized) | Yes |
| QLoRA | Yes | Yes | Yes (optimized) | Yes |
| DPO/Alignment | Via training | Yes | No | Yes |
| GRPO | No | Yes | No | Yes |
| SFT | Via training | Yes | Yes | Yes |
| YAML config | No | Yes | No | No |
| Speed optimization | Basic | Moderate | 2-5x faster | Basic |
| VRAM efficiency | Good | Good | Best | Good |

## Common Patterns

### LoRA Fine-tuning with PEFT
```python
from peft import LoraConfig, get_peft_model
model = get_peft_model(base_model, LoraConfig(r=8, lora_alpha=16, target_modules=all_layers))
```

### Axolotl YAML Config
```yaml
# examples/llama/qlora.yml
base_model: meta-llama/L llama-3-8b
learning_rate: 0.0002
batch_size: 4
epochs: 3
lora_r: 8
lora_alpha: 16
lora_dropout: 0.05
dataset_path: my-data
```

### Unsloth Fast Fine-tuning
```python
from unsloth import FastLanguageModel
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "unsloth/llama-3-8b-bnb-4bit",
    max_seq_length = 2048,
)
model = FastLanguageModel.get_peft_model(model, r=16, lora_alpha=16)
```

---

## Absorbed Sub-Skills

### LLM RL Training (`references/rl/`)

RL-based alignment methods for post-training. Covers GRPO (reasoning models), SIMPO (preference alignment), and SLIME (production-scale GLM). See `references/rl/grpo-training.md`, `references/rl/online-rl.md`, `references/rl/rl-full.md`.

### Distributed Training (`references/`)

Multi-GPU and large-scale training strategies. Covers Accelerate (simple multi-GPU), FSDP (manual sharding), PyTorch Lightning (high-level), and TorchTitan (4D parallelism for 8-512+ GPU pretraining). See `references/distributed-training-full.md`, `references/accelerate.md`, `references/pytorch-fsdp.md`, `references/pytorch-lightning.md`, `references/torchtitan.md`.
