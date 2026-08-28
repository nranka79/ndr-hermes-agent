# Unsloth — Reference
*Source skill: unsloth (absorbed into llm-fine-tuning umbrella)*
*Source path: mlops/training/unsloth/SKILL.md*

## When to Use

- Maximum speed for LoRA/QLoRA fine-tuning
- Training on limited VRAM (6GB for 7B, 8GB for 13B)
- Fast iteration cycles (2–5x faster than standard PEFT)
- All popular open models: Llama 3.1, Mistral, Phi-3, Qwen2.5, Gemma 2

## Key Advantage

| Metric | Standard PEFT | Unsloth |
|--------|--------------|---------|
| Speed | 1x | 2–5x |
| VRAM (7B) | ~14GB | ~6GB |
| Memory savings | — | 50–60% |

## Installation

```bash
pip install unsloth
pip install "unsloth[colab_new]>=2024.11"
```

## Quick Start

```python
from unsloth import FastLanguageModel

# Load 4-bit quantized model
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "unsloth/llama-3.1-8B-bnb-4bit",
    max_seq_length = 2048,
    load_in_4bit = True,
)

# Add LoRA adapters
model = FastLanguageModel.get_peft_model(
    model,
    r = 16,
    lora_alpha = 16,
    lora_dropout = 0,
    target_modules = ["q_proj", "v_proj", "k_proj", "o_proj",
                      "gate_proj", "up_proj", "down_proj"],
)
```

## Training

```python
from unsloth import SFTTrainer
from transformers import TrainingArguments

trainer = SFTTrainer(
    model = model,
    tokenizer = tokenizer,
    train_dataset = dataset,
    dataset_text_field = "text",
    max_seq_length = 2048,
    training_args = TrainingArguments(
        output_dir = "./lora-out",
        num_train_epochs = 3,
        per_device_train_batch_size = 2,
        gradient_accumulation_steps = 4,
        warmup_steps = 10,
        lr_scheduler_type = "linear",
        learning_rate = 2e-4,
    ),
)
trainer.train()
```

## Saving

```python
# Save locally
model.save_pretrained("lora_model")
tokenizer.save_pretrained("lora_model")

# Or merge and save as 16-bit
FastLanguageModel.for_inference(model)  # or .for_training(model)
merged_model = model.merge_and_unload()
merged_model.save_pretrained_merged("merged_model", tokenizer)
```
