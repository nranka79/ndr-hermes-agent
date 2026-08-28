# SLiMe (SGLang + Megatron) — Reference
*Source skill: slime-rl-training (absorbed into llm-rl-training umbrella)*
*Source path: mlops/training/slime/SKILL.md*

## When to Use

- **GLM model training** with tight Megatron-LM integration
- Large-scale production RL with **tensor parallelism + pipeline parallelism**
- Custom data generation workflows
- When you need **SGLang's efficient RL** with Megatron's distributed training
- Multi-node scaling beyond what TRL supports natively

## Architecture Overview

```
SLiMe = SGLang (RL data generation) + Megatron-LM (distributed training)

SGLang: handles batched generation, reward scoring, sample coordination
Megatron: handles tensor parallelism, pipeline parallelism, optimizer sharding
```

## Key Components

### SGLang Router (Data Generation)
```python
from sglang_router import sglang_router

router = sglang_router(
    model_name="glm-4-9b",
    tensor_parallel_size=4,
)
```

### Megatron-LM (Training)
```python
megatron_args = {
    "tensor_model_parallel_size": 4,
    "pipeline_model_parallel_size": 2,
    "num_layers": 28,
    "hidden_size": 4096,
}
```

## When NOT to Use

- Small-scale fine-tuning (use TRL or Axolotl)
- Single-node training (use PEFT or Unsloth)
- Quick experiments (use GRPO/SIMPO via TRL)
