# GRPO (Group Relative Policy Optimization) — Reference
*Source skill: grpo-rl-training (absorbed into llm-rl-training umbrella)*
*Source path: mlops/training/grpo-rl-training/SKILL.md*

## When to Use

- **Reasoning models** (Math, Code, Logic) — primary use case
- Self-rewarding mechanisms without a separate reward model
- Efficient RL where reward annotation is expensive
- Best when you can generate many samples per question

## Key Concept

GRPO divides samples by question, computes group-relative advantages (no critic needed), and applies policy gradient updates. This eliminates the need for a separate reward/critic model.

## Core Algorithm

1. For each question Q, generate G samples: `[answer_1, answer_2, ..., answer_g]`
2. Compute reward for each answer using a reward function
3. Compute group-relative advantage: `adv_i = r_i - mean(all_r)`
4. Policy gradient update using `adv_i` to reinforce better answers

## TRL Implementation

```python
from trl import GRPOTrainer, GRPOConfig
from datasets import Dataset

def reward_fn(prompts, responses, **kwargs):
    # Simple accuracy reward
    rewards = []
    for prompt, response in zip(prompts, responses):
        # Your reward logic here
        score = 1.0 if correct(response) else 0.0
        rewards.append(score)
    return rewards

trainer = GRPOTrainer(
    model=model,
    reward_functions=[reward_fn],
    args=GRPOConfig(
        output_dir="./grpo-output",
        num_iterations=8,        # PPO-style inner loop steps
        num_batch_generations=4, # Samples per prompt
        gradient_accumulation_steps=2,
    ),
)
trainer.train()
```

## Advantages over PPO

| Aspect | PPO | GRPO |
|--------|-----|------|
| Reward model | Required | Not needed |
| Critic network | Required | Not needed |
| Memory | 2x models | 1x model |
| Sample efficiency | Lower | Higher |
| Best for | General RL | Reasoning tasks |

## Best Practices

- Generate **8–16 samples per question** for good group statistics
- Use **reward shaping** — raw accuracy is sparse; consider intermediate rewards
- **Reference model** (KL penalty) prevents reward hacking
- Works best with **structured outputs** (boxed answers, code blocks)
