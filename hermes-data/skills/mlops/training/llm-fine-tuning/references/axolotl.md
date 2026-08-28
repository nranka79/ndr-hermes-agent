# Axolotl — Reference
*Source skill: axolotl (absorbed into llm-fine-tuning umbrella)*
*Source path: mlops/training/axolotl/SKILL.md*

## When to Use

- Declarative YAML-driven training (no Python coding needed)
- Running multiple fine-tuning methods (LoRA, DPO, GRPO, ORPO, QLoRA) from same codebase
- Quick switching between training methods via config changes
- Pretraining + SFT + RLHF in one pipeline

## Installation

```bash
pip install axolotl
```

## Example QLoRA YAML Config

```yaml
# examples/llama3/qlora.yml
base_model: meta-llama/Meta-Llama-3-8B
model_type: LlamaForCausalLM

load_in_4bit: true
bf16: true
train_dataset_paths:
  - data/my-data.jsonl

output_dir: ./qlora-out
num_epochs: 3
batch_size: 4
gradient_accumulation_steps: 4
learning_rate: 0.0002
lora_r: 8
lora_alpha: 16
lora_dropout: 0.05
lora_target_modules:
  - q_proj
  - v_proj
  - k_proj
  - o_proj
```

## Key Config Options

```yaml
# Dataset format
dataset_preproc_num_proc: 4
max_seq_length: 2048

# Training method
# (specify ONE of these)
sft: {}                    # Supervised Fine-Tuning
dpo: {}                    # Direct Preference Optimization
grpo: {}                   # Group Relative Policy Optimization
orpo: {}                   # Odds Ratio Preference Optimization

# LoRA
lora_r: 8
lora_alpha: 16
lora_target_modules: [q_proj, v_proj]
lora_dropout: 0.05

# DeepSpeed
deepspeed:
  stage: 2
  offload_optimizer: true
```

## Running Training

```bash
axolotl train examples/llama3/qlora.yml
```

## Supported Models

- Llama 1/2/3/3.1 (all sizes)
- Mistral / Mistral-Nemo
- Phi-3
- Qwen2 / Qwen2.5
- Gemma 1 / Gemma 2
- And 100+ others via HuggingFace AutoModel
