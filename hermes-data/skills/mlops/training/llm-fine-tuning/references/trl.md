# HuggingFace TRL — Reference
*Source skill: trl-fine-tuning (absorbed into llm-fine-tuning umbrella)*
*Source path: mlops/training/trl-fine-tuning/SKILL.md*

## When to Use

- Full alignment pipeline via HuggingFace TRL
- SFT (Supervised Fine-Tuning) for instruction tuning
- DPO (Direct Preference Optimization) for preference alignment
- PPO/GRPO for RL-based reward optimization
- Reward model training for RLHF

## Installation

```bash
pip install trl[peft,dev]
```

## SFT — Supervised Fine-Tuning

```python
from trl import SFTTrainer
from transformers import TrainingArguments

trainer = SFTTrainer(
    model = model,
    train_dataset = dataset,
    tokenizer = tokenizer,
    dataset_text_field = "text",
    max_seq_length = 512,
    args = TrainingArguments(
        output_dir = "./sft-out",
        num_train_epochs = 3,
        per_device_train_batch_size = 4,
    ),
)
trainer.train()
```

## DPO — Direct Preference Optimization

```python
from trl import DPOTrainer
import torch

dpo_trainer = DPOTrainer(
    model = model,
    ref_model = ref_model,
    train_dataset = preference_dataset,  # has chosen/rejected columns
    tokenizer = tokenizer,
    args = TrainingArguments(
        output_dir = "./dpo-out",
        beta = 0.1,          # regularization strength
        per_device_train_batch_size = 2,
    ),
)
dpo_trainer.train()
```

## GRPO — Group Relative Policy Optimization

```python
from trl import GRPOTrainer, GGQRTrainer
from trl.models import make_discrete_reward_model

grpo_trainer = GRPOTrainer(
    model = model,
    reward_functions = [reward_fn],  # list of reward functions
    args = TrainingArguments(
        output_dir = "./grpo-out",
        num_iterations = 512,     # number of generation steps
        num_batch_generations = 4,
    ),
)
```

## Reward Model

```python
from trl import RewardTrainer
from transformers import RewardConfig

trainer = RewardTrainer(
    model = reward_model,
    train_dataset = dataset,  # with chosen/rejected columns
    tokenizer = tokenizer,
    args = RewardConfig(
        output_dir = "./reward-model",
        per_device_train_batch_size = 4,
    ),
)
trainer.train()
```
