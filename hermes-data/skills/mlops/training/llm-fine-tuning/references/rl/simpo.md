# SIMPO (Simple Preference Optimization) — Reference
*Source skill: simpo-training (absorbed into llm-rl-training umbrella)*
*Source path: mlops/training/simpo/SKILL.md*

## When to Use

- Preference alignment with **simple, no-RL** approach
- When you want DPO-like results but **without a reference model**
- **Reference-free** alignment (more memory-efficient)
- **+6.4 points** on AlpacaEval 2.0 vs DPO in the paper

## Key Innovation

DPO requires a **reference model** (KL divergence term). SIMPO eliminates it by using a **ranking-based contrastive loss** — the chosen response is closer to the rejected response than a margin.

Loss: `L = -log σ(log π(y_c) - log π(y_r) + β)`

Where β is the margin controlling separation between chosen/rejected.

## Advantages over DPO

| Feature | DPO | SIMPO |
|---------|-----|-------|
| Reference model | Required | Not needed |
| Memory footprint | 2x model | 1x model |
| Training speed | Slower | Faster |
| AlpacaEval 2.0 | Baseline | +6.4 pts |

## TRL Implementation

```python
from trl import SimPOConfig, SimPOTrainer

trainer = SimPOTrainer(
    model=model,
    train_dataset=preference_dataset,  # needs 'chosen' and 'rejected'
    tokenizer=tokenizer,
    args=SimPOConfig(
        output_dir="./simpo-out",
        beta=0.1,              # Margin parameter (higher = more separation)
        num_train_epochs=3,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        learning_rate=1e-6,
    ),
)
trainer.train()
```

## Key Hyperparameters

- **beta** (margin): 0.1–0.3. Higher values push chosen/rejected further apart.
- **label_smoothing**: 0.0–0.1. Can help with noisy preference data.
- **learning_rate**: Typically lower than SFT — 1e-6 to 5e-6.

## When to Choose SIMPO over GRPO

- **SIMPO**: When you have static preference pairs (chosen/rejected) and want a simple, reference-free method.
- **GRPO**: When you can generate samples per question and need self-contained RL without reward annotation.
