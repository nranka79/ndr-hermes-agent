# PyTorch Lightning — Reference
*Source skill: pytorch-lightning (absorbed into distributed-training umbrella)*
*Source path: mlops/training/pytorch-lightning/SKILL.md*

## When to Use

- Clean training loops with minimal boilerplate
- Want built-in best practices (checkpointing, logging, early stopping)
- Scaling from laptop to supercomputer with same code
- Production training pipelines needing callbacks and monitoring
- Multi-GPU/TPU training without distributed code

## Quick Start

**Installation:**
```bash
pip install lightning
```

**Convert PyTorch to Lightning (3 steps):**
```python
import lightning as L
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

# Step 1: Define LightningModule
class LitModel(L.LightningModule):
    def __init__(self, hidden_size=128):
        super().__init__()
        self.model = nn.Sequential(
            nn.Linear(28 * 28, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, 10)
        )

    def training_step(self, batch, batch_idx):
        x, y = batch
        y_hat = self.model(x)
        loss = nn.functional.cross_entropy(y_hat, y)
        self.log('train_loss', loss)
        return loss

    def configure_optimizers(self):
        return torch.optim.Adam(self.parameters(), lr=1e-3)

# Step 2: Create data
train_loader = DataLoader(train_dataset, batch_size=32)

# Step 3: Train with Trainer
trainer = L.Trainer(max_epochs=10, accelerator='gpu', devices=2)
model = LitModel()
trainer.fit(model, train_loader)
```

**Trainer handles automatically:**
- GPU/TPU/CPU switching
- Distributed training (DDP, FSDP, DeepSpeed)
- Mixed precision (FP16, BF16)
- Gradient accumulation
- Checkpointing
- Logging
- Progress bars

## Key Trainer Flags

```python
trainer = L.Trainer(
    max_epochs=10,
    accelerator='gpu',          # 'cpu', 'gpu', 'tpu', 'mps', 'auto'
    devices=2,                  # Number of devices, or 'auto'
    strategy='ddp',            # 'auto', 'ddp', 'fsdp', 'deepspeed'
    precision=16,              # 32, 16, 'bf16'
    accumulate_grad_batches=4,
    enable_checkpointing=True,
    logger=True,
    callbacks=[EarlyStopping(), ModelCheckpoint()],
)
```

## Lightning Fabric (for custom control)

```python
from lightning import Fabric

fabric = Fabric(accelerator="cuda", devices=4, strategy="ddp")
fabric.launch()

model, optimizer = fabric.setup(model, optimizer)
```
