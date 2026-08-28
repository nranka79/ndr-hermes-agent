# TorchTitan — Reference
*Source skill: distributed-llm-pretraining-torchtitan (absorbed into distributed-training umbrella)*
*Source path: mlops/training/torchtitan/SKILL.md*

## When to Use

- Pretraining LLMs (Llama 3.1, DeepSeek V3, or custom) at 8–512+ GPUs
- 4D parallelism: FSDP2 + Tensor Parallel + Pipeline Parallel + Context Parallel
- Float8 training on H100 GPUs
- Distributed checkpointing for large models
- torch.compile integration for performance

## Quick Start

**Installation:**
```bash
# Stable from PyPI
pip install torchtitan

# Latest from source
git clone https://github.com/pytorch/torchtitan
cd torchtitan
pip install -r requirements.txt
```

**Download tokenizer:**
```bash
python scripts/download_hf_assets.py \
  --repo_id meta-llama/Llama-3.1-8B \
  --assets tokenizer --hf_token=YOUR_TOKEN
```

**Start training on 8 GPUs:**
```bash
CONFIG_FILE="./torchtitan/models/llama3/train_configs/llama3_8b.toml" ./run_train.sh
```

## Key 4D Parallelism Concepts

TorchTitan composes four parallelism dimensions:

1. **FSDP2** — Parameter sharding across data parallel ranks
2. **Tensor Parallel (TP)** — Weight matrix splitting across GPUs within a node
3. **Pipeline Parallel (PP)** — Layer staging across nodes
4. **Context Parallel (CP)** — Attention context sharding across GPUs

## Example Training Config (TOML)

```toml
[model]
model_name = "llama3_8b"

[training]
batch_size = 1
max_steps = 100000

[compute]
tensor_parallel_degree = 4
pipeline_parallel_degree = 2
context_parallel_degree = 2
use_float8 = true
```

## Key Features

- **65%+ speedup** over baseline on H100 GPUs
- **Float8 (FP8)** training support with per-tensor scaling
- **Distributed checkpoints** via `torch.distributed.checkpoint`
- **torch.compile** integration for speed
- **Built-in training configs** for Llama 3.1 (8B/70B/405B)
- **Mixed precision** (BF16 + FP8)
