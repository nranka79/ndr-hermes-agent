---
name: distributed-training
description: "Distributed LLM training — choose the right strategy for your scale: HuggingFace Accelerate (simplest), PyTorch FSDP (manual sharding), or PyTorch Lightning (automatic high-level). TorchTitan covers 4D parallelism pretraining at 8–512+ GPUs."
umbrella: distributed-training
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Distributed Training, FSDP, Accelerate, PyTorch Lightning, TorchTitan, DDP, 4D Parallelism, Pretraining]
---

# Distributed Training — Choosing the Right Strategy

Use this umbrella skill to select the best distributed training approach for your workload, then drill into the specific reference files for implementation details.

## Decision Tree

```
What is your training scenario?
├── Quick multi-GPU support for existing PyTorch code
│   └── → HuggingFace Accelerate (references/accelerate.md)
│         Minimal code changes, works with any model.
├── Large-model sharding with fine-grained control
│   └── → PyTorch FSDP (references/pytorch-fsdp.md)
│         Manual sharding decisions, maximum flexibility.
├── Clean training loops with built-in best practices
│   └── → PyTorch Lightning (references/pytorch-lightning.md)
│         Trainer handles distributed details for you.
└── Pretraining at 8–512+ GPUs with FSDP2/TP/PP/CP
    └── → TorchTitan (references/torchtitan.md)
          PyTorch-native 4D parallelism for Llama/DeepSeek pretraining.
```

## Reference Files

| File | When to Use |
|------|-------------|
| `references/accelerate.md` | 4-line distributed upgrade to any PyTorch script |
| `references/pytorch-fsdp.md` | Fully Sharded Data Parallel with manual control |
| `references/pytorch-lightning.md` | High-level Trainer class, auto-distributed |
| `references/torchtitan.md` | 4D parallelism pretraining at scale (FSDP2+TP+PP+CP) |

## Quick Comparison

| Feature | Accelerate | PyTorch FSDP | PyTorch Lightning | TorchTitan |
|---------|-----------|-------------|-------------------|------------|
| Code changes | 4 lines | Significant | Moderate | Significant |
| Sharding control | Basic | Full | Partial | Full (4D) |
| Pretraining support | Yes | Yes | Yes | Expert-level |
| Learning curve | Low | High | Low | High |
| Handles checkpoints | Via FSDP | Manual | Auto | Auto |
| TP/PP/CP support | No | FSDP2 only | Via DeepSpeed | Full 4D |

## Common Patterns

### Adding Multi-GPU to Existing Script → Accelerate
```python
from accelerate import Accelerator
accelerator = Accelerator()
model, optimizer, dataloader = accelerator.prepare(model, optimizer, dataloader)
# Run with: accelerate launch train.py
```

### Large Model with Custom Sharding → FSDP
```python
from torch.distributed.fsdp import FullyShardedDataParallel as FSDP
model = FSDP(model, sharding_strategy=ShardingStrategy.FULL_SHARD)
```

### Clean, Maintainable Code → Lightning
```python
class LitModel(L.LightningModule):
    def training_step(self, batch, batch_idx):
        loss = self.model(batch)
        return loss
trainer = L.Trainer(max_epochs=10, accelerator='gpu', devices=2)
trainer.fit(LitModel(), train_loader)
```

### Pretraining at Scale → TorchTitan
```bash
CONFIG_FILE="./torchtitan/models/llama3/train_configs/llama3_8b.toml" ./run_train.sh
```
