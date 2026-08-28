# HuggingFace Accelerate — Reference
*Source skill: huggingface-accelerate (absorbed into distributed-training umbrella)*
*Source path: mlops/training/accelerate/SKILL.md*

## When to Use

- Adding multi-GPU (DDP/FSDP) support to an existing PyTorch script with minimal changes
- Quick experiments across different hardware (CPU, single GPU, multi-GPU, TPU)
- When you want a single code path that works on laptop and supercomputer
- HuggingFace model fine-tuning with distributed support

## Quick Start

**Installation:**
```bash
pip install accelerate
```

**Convert PyTorch script (4 lines):**
```python
import torch
+ from accelerate import Accelerator

+ accelerator = Accelerator()

  model = torch.nn.Transformer()
  optimizer = torch.optim.Adam(model.parameters())
  dataloader = torch.utils.data.DataLoader(dataset)

+ model, optimizer, dataloader = accelerator.prepare(model, optimizer, dataloader)

  for batch in dataloader:
      optimizer.zero_grad()
      loss = model(batch)
-     loss.backward()
+     accelerator.backward(loss)
      optimizer.step()
```

**Run:**
```bash
accelerate launch train.py
```

## Key Commands

```bash
# Launch on multi-GPU
accelerate launch --multi_gpu train.py

# Launch with FSDP
accelerate launch --fsdp "full_shard" train.py

# Launch with DeepSpeed
accelerate launch --deepspeed train.py

# Interactive config
accelerate config
```

## Key Features

- **Unified API** across CPU, single GPU, multi-GPU, TPU
- **DeepSpeed integration** for ZeRO stages 0/1/2/3
- **FSDP integration** for parameter sharding
- **Gradient checkpointing** support
- **Mixed precision** (FP16/BF16)
- **TPU support** via xla
